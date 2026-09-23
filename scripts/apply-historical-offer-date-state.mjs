import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { applyOfferDates, offerDateKey } from "./backfill-historical-offer-dates.mjs";

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
    missing_records: 0
  };

  for (const [key, incoming] of Object.entries(proposalState?.issuers || {})) {
    stats.proposal_entries += 1;
    const current = currentState.issuers[key];
    if (newerOrEqual(incoming, current)) {
      currentState.issuers[key] = incoming;
      stats.cursor_updates += 1;
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
    const parsed = {
      open_date: incoming.open_extraction ?? null,
      close_date: incoming.close_extraction ?? null
    };

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
