import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  applyIssuePriceExtraction,
  applyIssueSizeExtraction,
  applyMinimumBidExtraction
} from "./extract-prospectus-fields.mjs";
import { historicalPdfKey } from "./backfill-historical-pdf-fields.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const STATE_PATH = path.join(ROOT, "ops", "sebi-historical-pdf-fields.json");

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

export function mergeHistoricalPdfFieldProposal(groups, currentState, proposalState) {
  const index = new Map();
  for (const group of groups) {
    for (const record of group.recovery.records || []) {
      index.set(historicalPdfKey(record), { group, record });
    }
  }

  currentState ||= { schema_version: "1.0.0", issuers: {} };
  currentState.issuers ||= {};

  const stats = {
    proposal_entries: 0,
    cursor_updates: 0,
    matched_records: 0,
    extracted_records: 0,
    extracted_fields: 0,
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
    const document = incoming.document || {
      type: "SEBI Prospectus PDF",
      identity: null,
      url: incoming.source_url,
      publication_date: null
    };
    const extractions = incoming.extractions || {};
    const changed = [];

    if (extractions.issue_price &&
        applyIssuePriceExtraction(record, document, extractions.issue_price, incoming.last_attempted_at)) {
      changed.push("issue_price");
    }
    if (extractions.issue_size_inr &&
        applyIssueSizeExtraction(record, document, extractions.issue_size_inr, incoming.last_attempted_at)) {
      changed.push("issue_size_inr");
    }
    if (extractions.minimum_bid_quantity &&
        applyMinimumBidExtraction(record, document, extractions.minimum_bid_quantity, incoming.last_attempted_at)) {
      changed.push("minimum_bid_quantity");
    }

    if (changed.length > 0) {
      group.changed = true;
      stats.extracted_records += 1;
      stats.extracted_fields += changed.length;
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
  const stats = mergeHistoricalPdfFieldProposal(groups, currentState, proposal);
  const now = new Date().toISOString();

  for (const group of groups) {
    if (!group.changed) continue;
    group.recovery.generated_at = now;
    fs.writeFileSync(group.file, JSON.stringify(group.recovery, null, 2) + "\n");
  }

  if (stats.cursor_updates > 0) {
    fs.mkdirSync(path.dirname(STATE_PATH), { recursive: true });
    fs.writeFileSync(STATE_PATH, JSON.stringify(currentState, null, 2) + "\n");
  }

  console.log(JSON.stringify({ historical_pdf_field_semantic_merge: stats }, null, 2));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => { console.error(error); process.exit(1); });
