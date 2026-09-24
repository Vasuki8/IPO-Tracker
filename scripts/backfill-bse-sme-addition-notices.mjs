import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  BSE_INDEX_NOTICE_LIST_URL,
  BSE_INDEX_NOTICE_DETAIL_URL,
  NOTICE_BATCH_SIZE,
  NOTICE_PARSER_VERSION,
  isBseSmeAdditionNotice,
  officialNoticePdfUrl,
  parseBseSmeAdditionNoticeHtml,
  validateNoticeBatchSize
} from "./audit-bse-sme-addition-notices.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const BSE_NOTICE_STATE_PATH = path.join(ROOT, "ops", "bse-sme-addition-notices.json");
export const BSE_NOTICE_RETRY_COOLDOWN_MS = 24 * 60 * 60 * 1000;
const USER_AGENT =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function normalizeText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function noticeNo(row) {
  return String(row?.notice_no ?? row?.Notice_no ?? "").trim();
}

function noticeSortValue(row) {
  const value = Date.parse(row?.Notice_Date ?? row?.dt_tm ?? "");
  return Number.isFinite(value) ? value : 0;
}

function isoDate(value) {
  const parsed = Date.parse(String(value ?? ""));
  return Number.isFinite(parsed) ? new Date(parsed).toISOString().slice(0, 10) : null;
}

function listingNoticeUrl(value) {
  return "https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=" + value;
}

export function emptyBseNoticeState() {
  return {
    schema_version: "1.0.0",
    parser_version: NOTICE_PARSER_VERSION,
    updated_at: null,
    bootstrap: null,
    catalog: null,
    notices: {}
  };
}

export function eligibleBseSmeAdditionNotices(catalog) {
  if (!Array.isArray(catalog?.Table)) throw new Error("BSE notice catalog has no Table array");
  return catalog.Table
    .filter(isBseSmeAdditionNotice)
    .filter((row) => {
      const year = new Date(row?.Notice_Date ?? row?.dt_tm ?? "").getUTCFullYear();
      return Number.isInteger(year) && year >= 2020 && year <= 2026;
    })
    .sort((a, b) => noticeSortValue(b) - noticeSortValue(a) || noticeNo(b).localeCompare(noticeNo(a)));
}

const COMPATIBLE_PARSED_PARSER_VERSIONS = new Set(["1.1.0"]);

function currentParserEntry(state, row) {
  const entry = state?.notices?.[noticeNo(row)];
  if (!entry) return null;
  if (entry.parser_version === NOTICE_PARSER_VERSION) return entry;
  if (entry.status === "parsed" && COMPATIBLE_PARSED_PARSER_VERSIONS.has(entry.parser_version)) return entry;
  return null;
}

function parserChangedFailure(state, row) {
  const entry = state?.notices?.[noticeNo(row)];
  return entry &&
    entry.status !== "parsed" &&
    entry.parser_version !== NOTICE_PARSER_VERSION
    ? entry
    : null;
}

export function selectBseNoticeBackfillBatch(
  eligible,
  state,
  batchSize = NOTICE_BATCH_SIZE,
  nowMs = Date.now()
) {
  validateNoticeBatchSize(batchSize);
  const repairedFailures = eligible
    .filter((row) => parserChangedFailure(state, row))
    .slice(0, batchSize)
    .map((row) => ({ row, reason: "parser_changed_failure" }));
  if (repairedFailures.length > 0) return repairedFailures;

  const unseen = eligible.filter((row) => !state?.notices?.[noticeNo(row)] && !currentParserEntry(state, row));
  const selected = unseen.slice(0, batchSize).map((row) => ({ row, reason: "unseen_or_parser_changed" }));

  if (selected.length >= batchSize || unseen.length > 0) return selected;

  const retries = eligible
    .map((row) => ({ row, entry: currentParserEntry(state, row) }))
    .filter(({ entry }) => entry && entry.status !== "parsed")
    .filter(({ entry }) => {
      const attempted = Date.parse(entry.last_attempted_at || "");
      return !Number.isFinite(attempted) || nowMs - attempted >= BSE_NOTICE_RETRY_COOLDOWN_MS;
    })
    .sort((a, b) => {
      const left = Date.parse(a.entry.last_attempted_at || "") || 0;
      const right = Date.parse(b.entry.last_attempted_at || "") || 0;
      return left - right || noticeSortValue(b.row) - noticeSortValue(a.row);
    })
    .slice(0, batchSize);

  return retries.map(({ row }) => ({ row, reason: "retry_failed_notice" }));
}

export function bseNoticeProgress(eligible, state) {
  let parsed = 0;
  let failed = 0;
  let unseen = 0;
  let staleParser = 0;
  let nextUnseenNoticeNo = null;

  for (const row of eligible) {
    const key = noticeNo(row);
    const entry = state?.notices?.[key];
    if (!entry) {
      unseen += 1;
      nextUnseenNoticeNo ||= key;
      continue;
    }
    const current = currentParserEntry(state, row);
    if (!current) {
      staleParser += 1;
      unseen += 1;
      nextUnseenNoticeNo ||= key;
      continue;
    }
    if (current.status === "parsed") parsed += 1;
    else failed += 1;
  }

  return {
    eligible_notices: eligible.length,
    parsed_current_parser: parsed,
    failed_current_parser: failed,
    unseen_or_parser_changed: unseen,
    stale_parser_entries: staleParser,
    next_unseen_notice_no: nextUnseenNoticeNo,
    complete: unseen === 0 && failed === 0
  };
}

export function validateBseNoticeState(state) {
  if (!state || state.schema_version !== "1.0.0" || typeof state.notices !== "object" || Array.isArray(state.notices)) {
    throw new Error("invalid_bse_notice_state");
  }
  for (const [key, entry] of Object.entries(state.notices)) {
    if (!/^\d{8}-\d+$/.test(key) || entry?.notice_no !== key ||
        typeof entry.parser_version !== "string" || !["parsed", "fetch_error", "unparseable"].includes(entry.status) ||
        !Number.isSafeInteger(entry.attempts) || entry.attempts < 1 ||
        !Number.isFinite(Date.parse(entry.first_attempted_at || "")) ||
        !Number.isFinite(Date.parse(entry.last_attempted_at || "")) ||
        !Number.isSafeInteger(entry.parsed_entry_count) || entry.parsed_entry_count < 0) {
      throw new Error("invalid_bse_notice_state_entry");
    }
    if (entry.status === "parsed" && entry.parsed_entry_count < 1) {
      throw new Error("parsed_bse_notice_without_entries");
    }
    if (entry.extracted_text_sha256 != null && !/^[a-f0-9]{64}$/.test(entry.extracted_text_sha256)) {
      throw new Error("invalid_bse_notice_text_hash");
    }
    if (entry.parsed_entries != null && !Array.isArray(entry.parsed_entries)) {
      throw new Error("invalid_bse_notice_parsed_entries");
    }
  }
  return state;
}

async function fetchJson(url, fetchImpl = fetch) {
  const response = await fetchImpl(url, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "application/json,*/*",
      "accept-language": "en-US,en;q=0.9",
      "referer": "https://www.bseindices.com/notices"
    },
    signal: AbortSignal.timeout(20000)
  });
  if (!response.ok) throw new Error("HTTP " + response.status + " " + url);
  return response.json();
}

async function fetchPdfText(url, fetchImpl = fetch) {
  const response = await fetchImpl(url, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "application/pdf,*/*;q=0.5",
      "accept-language": "en-US,en;q=0.9",
      "referer": "https://www.bseindices.com/notices"
    },
    signal: AbortSignal.timeout(30000)
  });
  if (!response.ok) throw new Error("HTTP " + response.status + " " + url);
  const bytes = Buffer.from(await response.arrayBuffer());
  if (bytes.length < 5 || bytes.subarray(0, 5).toString("ascii") !== "%PDF-") {
    throw new Error("BSE notice source is not a PDF: " + url);
  }

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "bse-sme-history-"));
  const pdfPath = path.join(dir, "notice.pdf");
  const textPath = path.join(dir, "notice.txt");
  try {
    fs.writeFileSync(pdfPath, bytes);
    execFileSync("pdftotext", ["-f", "1", "-l", "3", "-layout", pdfPath, textPath], {
      stdio: "ignore",
      timeout: 20000
    });
    return fs.readFileSync(textPath, "utf8");
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function sourceEntry(row, text, sourceKind, sourceUrl, previous, now, status, error = null) {
  const parsed = status === "parsed" ? parseBseSmeAdditionNoticeHtml(text) : [];
  return {
    notice_no: noticeNo(row),
    notice_date: isoDate(row?.Notice_Date ?? row?.dt_tm),
    subject: normalizeText(row?.Subject ?? row?.subject),
    parser_version: NOTICE_PARSER_VERSION,
    status,
    attempts: previous?.parser_version === NOTICE_PARSER_VERSION ? previous.attempts + 1 : 1,
    first_attempted_at: previous?.parser_version === NOTICE_PARSER_VERSION
      ? previous.first_attempted_at
      : now,
    last_attempted_at: now,
    source_kind: sourceKind,
    source_url: sourceUrl,
    pdf_url: officialNoticePdfUrl(row),
    extracted_text_sha256: text
      ? createHash("sha256").update(text, "utf8").digest("hex")
      : null,
    parsed_entry_count: parsed.length,
    parsed_entries: parsed.map((item) => ({
      ...item,
      listing_notice_url: listingNoticeUrl(item.listing_notice_no)
    })),
    error
  };
}

async function processNotice(row, previous, now, fetchImpl = fetch) {
  const key = noticeNo(row);
  if (!/^\d{8}-\d+$/.test(key)) {
    return sourceEntry(row, "", null, null, previous, now, "unparseable", "invalid_notice_number");
  }

  const pdfUrl = officialNoticePdfUrl(row);
  let text = "";
  let sourceKind = null;
  let sourceUrl = null;
  let pdfError = null;

  if (pdfUrl) {
    try {
      text = await fetchPdfText(pdfUrl, fetchImpl);
      sourceKind = "bse_index_notice_pdf";
      sourceUrl = pdfUrl;
    } catch (error) {
      pdfError = String(error?.message || error);
    }
  }

  if (!text) {
    const detailUrl = BSE_INDEX_NOTICE_DETAIL_URL + encodeURIComponent(key);
    try {
      const detail = await fetchJson(detailUrl, fetchImpl);
      text = typeof detail?.Data === "string" ? detail.Data : "";
      sourceKind = "bse_index_notice_detail_api";
      sourceUrl = detailUrl;
    } catch (error) {
      return sourceEntry(
        row, "", sourceKind, sourceUrl ?? pdfUrl, previous, now, "fetch_error",
        JSON.stringify({ pdf_error: pdfError, detail_error: String(error?.message || error) })
      );
    }
  }

  const parsed = parseBseSmeAdditionNoticeHtml(text);
  if (!parsed.length) {
    return sourceEntry(
      row, text, sourceKind, sourceUrl, previous, now, "unparseable",
      pdfError ? "pdf_error_before_fallback: " + pdfError : "no_parseable_listing_reference"
    );
  }
  return sourceEntry(row, text, sourceKind, sourceUrl, previous, now, "parsed");
}

function readState(statePath = BSE_NOTICE_STATE_PATH) {
  if (!fs.existsSync(statePath)) return emptyBseNoticeState();
  return validateBseNoticeState(JSON.parse(fs.readFileSync(statePath, "utf8")));
}

function writeState(state, statePath = BSE_NOTICE_STATE_PATH) {
  validateBseNoticeState(state);
  fs.mkdirSync(path.dirname(statePath), { recursive: true });
  fs.writeFileSync(statePath, JSON.stringify(state, null, 2) + "\n");
}

export async function backfillBseSmeAdditionNotices({
  batchSize = NOTICE_BATCH_SIZE,
  state = null,
  fetchImpl = fetch,
  now = () => new Date().toISOString(),
  sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
} = {}) {
  validateNoticeBatchSize(batchSize);
  const working = structuredClone(state ?? emptyBseNoticeState());
  validateBseNoticeState(working);
  const catalog = await fetchJson(BSE_INDEX_NOTICE_LIST_URL, fetchImpl);
  const eligible = eligibleBseSmeAdditionNotices(catalog);
  const before = bseNoticeProgress(eligible, working);
  const selected = selectBseNoticeBackfillBatch(eligible, working, batchSize, Date.parse(now()));
  const attemptAt = now();
  const stats = {
    selected: selected.length,
    parsed: 0,
    fetch_errors: 0,
    unparseable: 0,
    discovered_entries: 0
  };
  const failures = [];
  const candidates = [];

  for (const [index, selection] of selected.entries()) {
    if (index > 0) await sleep(150);
    const row = selection.row;
    const key = noticeNo(row);
    const entry = await processNotice(row, working.notices[key], attemptAt, fetchImpl);
    working.notices[key] = entry;
    if (entry.status === "parsed") {
      stats.parsed += 1;
      stats.discovered_entries += entry.parsed_entry_count;
      for (const parsed of entry.parsed_entries || []) {
        candidates.push({
          index_notice_no: key,
          index_notice_date: entry.notice_date,
          index_notice_subject: entry.subject,
          index_notice_source_url: entry.source_url,
          index_notice_source_kind: entry.source_kind,
          extracted_text_sha256: entry.extracted_text_sha256,
          selection_reason: selection.reason,
          ...parsed
        });
      }
    } else {
      if (entry.status === "fetch_error") stats.fetch_errors += 1;
      else stats.unparseable += 1;
      failures.push({
        notice_no: key,
        status: entry.status,
        error: entry.error,
        attempts: entry.attempts,
        retry_after: new Date(Date.parse(entry.last_attempted_at) + BSE_NOTICE_RETRY_COOLDOWN_MS).toISOString()
      });
    }
  }

  if (selected.length) {
    working.schema_version = "1.0.0";
    working.parser_version = NOTICE_PARSER_VERSION;
    working.updated_at = attemptAt;
    working.catalog = {
      catalog_rows: catalog.Table.length,
      eligible_count: eligible.length,
      newest_notice_no: eligible[0] ? noticeNo(eligible[0]) : null,
      oldest_notice_no: eligible.at(-1) ? noticeNo(eligible.at(-1)) : null,
      observed_at: attemptAt
    };
  }

  const after = bseNoticeProgress(eligible, working);
  return {
    state: working,
    report: {
      schema_version: "1.0.0",
      parser_version: NOTICE_PARSER_VERSION,
      generated_at: attemptAt,
      run_id: process.env.GITHUB_RUN_ID || null,
      commit_sha: process.env.GITHUB_SHA || null,
      batch_limit: batchSize,
      selected_notice_nos: selected.map(({ row, reason }) => ({ notice_no: noticeNo(row), reason })),
      stats,
      progress_before: before,
      progress_after: after,
      candidates,
      failures,
      status: failures.length ? "partial" : selected.length ? "complete" : "no_work",
      scope_note:
        "Historical discovery cursor only. Parsed index notices never materialize IPOs; issuer-specific official listing evidence remains required."
    }
  };
}

async function run() {
  const allowed = new Set(["--batch", "--output"]);
  const args = {};
  for (const raw of process.argv.slice(2)) {
    const at = raw.indexOf("=");
    if (at < 0) throw new Error("arguments_require_equals");
    const key = raw.slice(0, at);
    if (!allowed.has(key)) throw new Error("unknown_argument_" + key);
    args[key] = raw.slice(at + 1);
  }
  const batchSize = args["--batch"] ? Number(args["--batch"]) : NOTICE_BATCH_SIZE;
  const current = readState();
  const result = await backfillBseSmeAdditionNotices({ batchSize, state: current });
  if (result.report.stats.selected > 0) writeState(result.state);
  if (args["--output"]) {
    const output = path.resolve(args["--output"]);
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.writeFileSync(output, JSON.stringify(result.report, null, 2) + "\n");
  }
  console.log(JSON.stringify({ bse_sme_notice_backfill: result.report }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => {
  console.error(error);
  process.exit(1);
});
