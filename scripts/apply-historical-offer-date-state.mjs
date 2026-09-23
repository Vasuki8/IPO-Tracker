import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { applyOfferDates, HISTORICAL_OFFER_DATE_PARSER_VERSION, offerDateExtractionPassesCurrentRules, offerDateKey } from "./backfill-historical-offer-dates.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const STATE_PATH = path.join(ROOT, "ops", "sebi-historical-offer-dates.json");

function recoveryFiles() {
  if (!fs.existsSync(RECOVERY_ROOT)) return [];
  return fs.readdirSync(RECOVERY_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^20\d{2}$/.test(entry.name))
    .map((entry) => path.join(RECOVERY_ROOT, entry.name, "nse-issue-information.json"))
    .filter((file) => fs.existsSync(file))
    .sort();
}

function readJson(file, fallback) {
  return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, "utf8")) : fallback;
}

function newerOrEqual(incoming, current) {
  const a = Date.parse(incoming?.last_attempted_at || "");
  const b = Date.parse(current?.last_attempted_at || "");
  if (!Number.isFinite(b)) return true;
  if (!Number.isFinite(a)) return false;
  return a >= b;
}

function addDocumentOnce(record, source, collectedAt) {
  record.documents ||= [];
  if (record.documents.some((doc) => doc.url === source.url)) return;
  record.documents.push({
    type: source.document_type,
    identity: source.document_identity ?? null,
    url: source.url,
    publication_date: source.publication_date ?? null,
    collected_at: collectedAt
  });
}

function correctionHistoryEntry(field, incoming) {
  if (!field?.value) return null;
  return {
    corrected_at: incoming.corrected_at ?? incoming.last_attempted_at ?? null,
    reason: incoming.correction_reason ?? "Historical offer-date correction",
    previous_value: field.value,
    previous_status: field.status ?? null,
    previous_source_value: field.source_value ?? null,
    previous_evidence: field.source ? [{
      url: field.source.url,
      document_type: field.source.document_type,
      document_identity: field.source.document_identity ?? null,
      publication_date: field.source.publication_date ?? null,
      page: field.page ?? null,
      collected_at: field.source.collected_at ?? null
    }] : []
  };
}

function applyCorrectedDateField(record, fieldName, correctionSpec, incoming) {
  if (!correctionSpec?.replacement_value) return { changed: false, conflict: false };

  const directField = record[fieldName];
  const directValue = directField?.value ?? null;
  const termValue = record.terms?.[fieldName] ?? null;
  const currentValue = directValue ?? termValue;
  const replacement = correctionSpec.replacement_value;
  const previous = correctionSpec.previous_value ?? null;

  if (currentValue === replacement) return { changed: false, conflict: false, already: true };

  // Never overwrite a different value that appeared concurrently from another
  // source. Known parser-v1 corrections may replace only their exact legacy
  // value, or fill a field that is still missing.
  if (currentValue !== null && currentValue !== previous) {
    return { changed: false, conflict: true };
  }

  const source = incoming.correction?.source;
  if (!source?.url || !source?.document_type) return { changed: false, conflict: true };

  const priorCorrections = Array.isArray(directField?.corrections) ? directField.corrections : [];
  const history = directValue === previous && previous !== null
    ? correctionHistoryEntry(directField, incoming)
    : null;

  record[fieldName] = {
    value: replacement,
    source_value: incoming.correction?.source_value ?? null,
    page: source.page ?? null,
    status: "verified",
    source: {
      url: source.url,
      document_type: source.document_type,
      document_identity: source.document_identity ?? null,
      publication_date: source.publication_date ?? null,
      collected_at: incoming.corrected_at ?? incoming.last_attempted_at ?? new Date().toISOString()
    },
    corrections: history ? [...priorCorrections, history] : priorCorrections
  };

  addDocumentOnce(
    record,
    source,
    incoming.corrected_at ?? incoming.last_attempted_at ?? new Date().toISOString()
  );
  record.last_collected_at = incoming.corrected_at ?? incoming.last_attempted_at ?? record.last_collected_at;
  return { changed: true, conflict: false };
}

export function mergeOfferDateProposal(groups, currentState, proposalState) {
  const index = new Map();
  for (const group of groups) {
    for (const record of group.recovery.records || []) {
      index.set(offerDateKey(record), { group, record });
    }
  }

  currentState ||= { schema_version: "1.0.0", issuers: {} };
  currentState.issuers ||= {};
  const stats = {
    proposal_entries: 0,
    cursor_updates: 0,
    matched_records: 0,
    extracted_records: 0,
    open_dates: 0,
    close_dates: 0,
    already_present: 0,
    missing_records: 0,
    stale_parser_entries: 0,
    invalid_extractions: 0,
    corrected_records: 0,
    corrected_open_dates: 0,
    corrected_close_dates: 0,
    correction_conflicts: 0
  };

  for (const [key, incoming] of Object.entries(proposalState?.issuers || {})) {
    stats.proposal_entries += 1;

    if (incoming?.parser_version !== HISTORICAL_OFFER_DATE_PARSER_VERSION) {
      stats.stale_parser_entries += 1;
      continue;
    }

    const current = currentState.issuers[key];
    if (newerOrEqual(incoming, current)) {
      currentState.issuers[key] = incoming;
      stats.cursor_updates += 1;
    }

    if (incoming?.status === "corrected_official_nse") {
      const match = index.get(key);
      if (!match) {
        stats.missing_records += 1;
        continue;
      }
      stats.matched_records += 1;

      const { group, record } = match;
      const openResult = applyCorrectedDateField(record, "open_date", incoming.correction?.open_date, incoming);
      const closeResult = applyCorrectedDateField(record, "close_date", incoming.correction?.close_date, incoming);

      if (openResult.conflict) stats.correction_conflicts += 1;
      if (closeResult.conflict) stats.correction_conflicts += 1;

      if (openResult.changed || closeResult.changed) {
        group.changed = true;
        stats.corrected_records += 1;
        if (openResult.changed) stats.corrected_open_dates += 1;
        if (closeResult.changed) stats.corrected_close_dates += 1;
      }
      continue;
    }

    if (incoming?.status !== "extracted") continue;
    const match = index.get(key);
    if (!match) {
      stats.missing_records += 1;
      continue;
    }
    stats.matched_records += 1;

    const { group, record } = match;
    const beforeOpen = record.open_date?.value ?? record.terms?.open_date ?? null;
    const beforeClose = record.close_date?.value ?? record.terms?.close_date ?? null;
    const document = incoming.document || {
      type: "SEBI Prospectus PDF",
      identity: null,
      url: incoming.source_url,
      publication_date: null
    };
    const openValid = incoming.open_extraction
      ? offerDateExtractionPassesCurrentRules(incoming.open_extraction, "open", incoming.listing_date ?? null)
      : true;
    const closeValid = incoming.close_extraction
      ? offerDateExtractionPassesCurrentRules(incoming.close_extraction, "close", incoming.listing_date ?? null)
      : true;

    if (!openValid) stats.invalid_extractions += 1;
    if (!closeValid) stats.invalid_extractions += 1;

    const parsed = {
      open_date: openValid ? (incoming.open_extraction ?? null) : null,
      close_date: closeValid ? (incoming.close_extraction ?? null) : null
    };

    if (!parsed.open_date && !parsed.close_date) continue;

    const changed = applyOfferDates(
      record,
      document,
      parsed,
      incoming.last_attempted_at || new Date().toISOString()
    );
    const afterOpen = record.open_date?.value ?? record.terms?.open_date ?? null;
    const afterClose = record.close_date?.value ?? record.terms?.close_date ?? null;

    if (changed) {
      group.changed = true;
      stats.extracted_records += 1;
      if (!beforeOpen && afterOpen) stats.open_dates += 1;
      if (!beforeClose && afterClose) stats.close_dates += 1;
    } else {
      stats.already_present += 1;
    }
  }

  return stats;
}

async function run() {
  const inputArg = process.argv.find((arg) => arg.startsWith("--input="));
  if (!inputArg) throw new Error("--input=<proposal-state.json> is required");
  const input = inputArg.slice("--input=".length);
  const proposal = readJson(input, { schema_version: "1.0.0", issuers: {} });
  const groups = recoveryFiles().map((file) => ({
    file,
    recovery: JSON.parse(fs.readFileSync(file, "utf8")),
    changed: false
  }));
  const currentState = readJson(STATE_PATH, { schema_version: "1.0.0", issuers: {} });
  const stats = mergeOfferDateProposal(groups, currentState, proposal);

  for (const group of groups) {
    if (!group.changed) continue;
    group.recovery.generated_at = new Date().toISOString();
    fs.writeFileSync(group.file, JSON.stringify(group.recovery, null, 2) + "\n");
  }

  if (stats.cursor_updates > 0) {
    fs.mkdirSync(path.dirname(STATE_PATH), { recursive: true });
    fs.writeFileSync(STATE_PATH, JSON.stringify(currentState, null, 2) + "\n");
  }

  console.log(JSON.stringify({ historical_offer_date_semantic_merge: stats }, null, 2));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => { console.error(error); process.exit(1); });
