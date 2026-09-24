import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  BSE_NOTICE_STATE_PATH,
  emptyBseNoticeState,
  validateBseNoticeState
} from "./backfill-bse-sme-addition-notices.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function timestamp(value) {
  const parsed = Date.parse(value || "");
  return Number.isFinite(parsed) ? parsed : 0;
}

export function mergeBseNoticeStates(current, proposal) {
  validateBseNoticeState(current);
  validateBseNoticeState(proposal);
  const merged = structuredClone(current);
  merged.schema_version = "1.0.0";
  merged.parser_version = proposal.parser_version;
  merged.bootstrap ||= structuredClone(proposal.bootstrap ?? null);

  for (const [noticeNo, incoming] of Object.entries(proposal.notices || {})) {
    const existing = merged.notices[noticeNo];
    if (!existing ||
        existing.parser_version !== proposal.parser_version ||
        timestamp(incoming.last_attempted_at) > timestamp(existing.last_attempted_at) ||
        (timestamp(incoming.last_attempted_at) === timestamp(existing.last_attempted_at) &&
          incoming.attempts > existing.attempts)) {
      merged.notices[noticeNo] = structuredClone(incoming);
    }
  }

  if (!merged.catalog || timestamp(proposal.catalog?.observed_at) >= timestamp(merged.catalog?.observed_at)) {
    merged.catalog = structuredClone(proposal.catalog ?? merged.catalog);
  }
  if (timestamp(proposal.updated_at) >= timestamp(merged.updated_at)) {
    merged.updated_at = proposal.updated_at;
  }
  return validateBseNoticeState(merged);
}

function readCurrent() {
  if (!fs.existsSync(BSE_NOTICE_STATE_PATH)) return emptyBseNoticeState();
  return validateBseNoticeState(JSON.parse(fs.readFileSync(BSE_NOTICE_STATE_PATH, "utf8")));
}

function run() {
  const args = process.argv.slice(2);
  if (args.length === 1 && args[0] === "--check") {
    const current = readCurrent();
    console.log(JSON.stringify({
      bse_notice_state_valid: true,
      parser_version: current.parser_version,
      notices: Object.keys(current.notices).length
    }));
    return;
  }
  if (args.length !== 1 || !args[0].startsWith("--input=")) {
    throw new Error("use --input=<state.json> or --check");
  }

  const input = path.resolve(ROOT, args[0].slice("--input=".length));
  const proposal = validateBseNoticeState(JSON.parse(fs.readFileSync(input, "utf8")));
  const merged = mergeBseNoticeStates(readCurrent(), proposal);
  fs.mkdirSync(path.dirname(BSE_NOTICE_STATE_PATH), { recursive: true });
  fs.writeFileSync(BSE_NOTICE_STATE_PATH, JSON.stringify(merged, null, 2) + "\n");
  console.log(JSON.stringify({
    bse_notice_state_merge: {
      parser_version: merged.parser_version,
      notices: Object.keys(merged.notices).length,
      updated_at: merged.updated_at
    }
  }));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) {
  try { run(); }
  catch (error) { console.error(error); process.exit(1); }
}
