import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { matchIndexCompany } from "./audit-bse-sme-ipo-index.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const SOURCE_MANIFEST = path.join(ROOT, "data", "bse-ipo-sources.json");

export const BSE_INDEX_NOTICE_LIST_URL =
  "https://www.bseindices.com/AsiaIndexAPI/api/GetNoticesadvancesearch_newcomb/w";
export const BSE_INDEX_NOTICE_DETAIL_URL =
  "https://www.bseindices.com/AsiaIndexAPI/api/DisplayNoticecircular/w?NoticeId=";
export const NOTICE_BATCH_SIZE = 20;
export const NOTICE_PARSER_VERSION = "1.1.0";

const USER_AGENT =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function normalizeText(value) {
  return String(value ?? "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&rsquo;|&lsquo;/gi, "'")
    .replace(/&ndash;|&mdash;/gi, "-")
    .replace(/&#10;|&#13;/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function stripTags(value) {
  return normalizeText(
    String(value ?? "")
      .replace(/<script[\s\S]*?<\/script>/gi, " ")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<[^>]+>/g, " ")
  );
}

function isoDate(raw) {
  const parsed = Date.parse(String(raw ?? ""));
  if (!Number.isFinite(parsed)) return null;
  return new Date(parsed).toISOString().slice(0, 10);
}

function listingNoticeUrl(noticeNo) {
  return "https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=" + noticeNo;
}

export function isBseSmeAdditionNotice(row) {
  const subject = normalizeText(row?.Subject ?? row?.subject);
  return /^Additions?\s+to\s+the\s+BSE\s+SME\s+IPO\s+INDEX$/i.test(subject);
}

export function officialNoticePdfUrl(row) {
  const raw = normalizeText(row?.FileName ?? row?.file_name ?? "");
  if (!raw) return null;
  try {
    const url = new URL(raw);
    const host = url.hostname.toLowerCase();
    if (url.protocol !== "https:" || url.username || url.password) return null;
    if (!(host === "bseindia.com" || host.endsWith(".bseindia.com"))) return null;
    if (!/\.pdf$/i.test(url.pathname)) return null;
    return url.href;
  } catch {
    return null;
  }
}

export function summarizeBseNoticeDataShape(value, depth = 0) {
  if (depth > 2) return typeof value;
  if (value === null) return null;
  if (Array.isArray(value)) {
    return {
      type: "array",
      length: value.length,
      sample: value.slice(0, 2).map((item) => summarizeBseNoticeDataShape(item, depth + 1))
    };
  }
  if (typeof value === "object") {
    return {
      type: "object",
      keys: Object.keys(value).slice(0, 20),
      fields: Object.fromEntries(
        Object.entries(value).slice(0, 12).map(([key, item]) => [
          key,
          typeof item === "string"
            ? { type: "string", length: item.length, prefix: item.slice(0, 180).replace(/\s+/g, " ") }
            : summarizeBseNoticeDataShape(item, depth + 1)
        ])
      )
    };
  }
  return { type: typeof value, value: String(value).slice(0, 180) };
}

function firstStringValue(value, depth = 0) {
  if (depth > 3 || value == null) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = firstStringValue(item, depth + 1);
      if (found) return found;
    }
    return "";
  }
  if (typeof value === "object") {
    for (const item of Object.values(value)) {
      const found = firstStringValue(item, depth + 1);
      if (found) return found;
    }
  }
  return "";
}

export function summarizeBseNoticeParseFailure(value, limit = 700) {
  const html = firstStringValue(value);
  const body = stripTags(html);
  const normalizedLimit = Math.max(120, Math.min(1000, Number(limit) || 700));
  const markers = ["With reference", "BSE SME IPO", "Exchange ticker", "Exchange Ticker"];
  const positions = markers
    .map((marker) => body.toLowerCase().indexOf(marker.toLowerCase()))
    .filter((value) => value >= 0);
  const start = positions.length > 0 ? Math.max(0, Math.min(...positions) - 80) : 0;
  return body.slice(start, start + normalizedLimit);
}

// Unlike Date.parse, reject calendar rollover (e.g. February 30 -> March 2).
function strictListingDate(raw) {
  const match = String(raw).match(/^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$/);
  if (!match) return null;
  const months = ["january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"];
  const month = months.indexOf(match[1].toLowerCase());
  const day = Number(match[2]);
  const year = Number(match[3]);
  if (month < 0 || day < 1 || year < 1900 || year > 2100) return null;
  const date = new Date(Date.UTC(year, month, day));
  if (date.getUTCMonth() !== month || date.getUTCDate() !== day) return null;
  return date.toISOString().slice(0, 10);
}

export function parseBseSmeAdditionNoticeHtml(html) {
  const body = stripTags(html);
  const rows = [];
  // The same punctuation grammar must delimit a clause AND parse its entries.
  const entryStart = /With reference to\s+Notice No\.?\s*:?\s*[0-9]{8}-[0-9]+/gi;
  const starts = [...body.matchAll(entryStart)];

  for (let index = 0; index < starts.length; index += 1) {
    const from = starts[index].index;
    const to = Math.min(starts[index + 1]?.index ?? body.length, from + 1800);
    const clause = body.slice(from, to);
    // Index admission's later "Effective at the open" date is NOT a listing date.
    const listingStatement = clause.match(
      /\b(?:is being|are being|will be|is|are)\s+listed\s+on\s+(?:SME\s+platform\s+of\s+)?BSE\b[\s,]*effective\s+(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*,?\s*)?([A-Za-z]+\s+\d{1,2},\s*\d{4})/i
    );
    if (!listingStatement) continue;
    const listingTerms = clause.slice(0, listingStatement.index);
    const effectiveRaw = normalizeText(listingStatement[1]);
    const listingDate = strictListingDate(effectiveRaw);
    if (!listingDate) continue;

    const entryPattern =
      /(?:With reference to\s+)?Notice No\.?\s*:?\s*([0-9]{8}-[0-9]+)\s*,?\s*(.{1,220}?)\s*\(Exchange ticker\s*[–—-]\s*([0-9]{6})\s*\)/gi;
    const entries = [...listingTerms.matchAll(entryPattern)];
    if (!entries.length) continue;
    // All issuer references before the shared listing statement must be explicit.
    // Do not bridge missing tickers or unrelated prose to a later issuer's date.
    const separators = listingTerms.replace(entryPattern, " ");
    if (!/^(?:\s|,|&|\band\b)*$/i.test(separators)) continue;
    if (entries.some((entry) => /\bNotice\s+No\b/i.test(entry[2]))) continue;

    for (const entry of entries) {
      rows.push({
        listing_notice_no: entry[1],
        issuer_name: normalizeText(entry[2]),
        bse_scrip_code: entry[3],
        listing_date: listingDate,
        listing_date_raw: effectiveRaw
      });
    }
  }

  // Repeated evidence is idempotent; conflicting names/dates never use last-wins.
  const byKey = new Map();
  const conflicts = new Set();
  for (const row of rows) {
    const key = row.listing_notice_no + "|" + row.bse_scrip_code;
    const previous = byKey.get(key);
    if (previous && (previous.issuer_name !== row.issuer_name ||
        previous.listing_date !== row.listing_date)) conflicts.add(key);
    else if (!previous) byKey.set(key, row);
  }
  return [...byKey].filter(([key]) => !conflicts.has(key)).map(([, row]) => row);
}

export function validateNoticeBatchSize(value) {
  if (!Number.isInteger(value) || value < 1 || value > NOTICE_BATCH_SIZE) {
    throw new Error("Notice batch size must be an integer between 1 and " + NOTICE_BATCH_SIZE);
  }
  return value;
}

export function classifyAdditionNoticeAudit(result) {
  const stats = result?.stats;
  if (!stats || stats.catalog_rows === 0) return "failed";
  if (stats.eligible_sme_addition_notices === 0) return "no_eligible_notices";
  if (stats.attempted_notices === 0 || stats.parsed_entries === 0) return "failed";
  if (stats.parse_failures > 0 || stats.fetch_errors > 0 || result.failures?.length > 0) {
    return "partial";
  }
  return "complete";
}

function loadRecoveryRecords() {
  if (!fs.existsSync(RECOVERY_ROOT)) return [];
  const result = [];
  for (const entry of fs.readdirSync(RECOVERY_ROOT, { withFileTypes: true })) {
    if (!entry.isDirectory() || !/^20\d{2}$/.test(entry.name)) continue;
    const file = path.join(RECOVERY_ROOT, entry.name, "nse-issue-information.json");
    if (!fs.existsSync(file)) continue;
    const data = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of data.records || []) {
      result.push({ year: Number(entry.name), record });
    }
  }
  return result;
}

function retainedListingUrls() {
  if (!fs.existsSync(SOURCE_MANIFEST)) return new Set();
  const manifest = JSON.parse(fs.readFileSync(SOURCE_MANIFEST, "utf8"));
  return new Set(
    (manifest.sources || [])
      .filter((source) => source.kind === "listing_notice")
      .map((source) => source.url)
      .filter(Boolean)
  );
}

async function fetchJson(url) {
  const response = await fetch(url, {
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

async function fetchPdfText(url) {
  const response = await fetch(url, {
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

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "bse-sme-notice-"));
  const pdfPath = path.join(dir, "notice.pdf");
  const textPath = path.join(dir, "notice.txt");
  try {
    fs.writeFileSync(pdfPath, bytes);
    execFileSync(
      "pdftotext",
      ["-f", "1", "-l", "3", "-layout", pdfPath, textPath],
      { stdio: "ignore", timeout: 20000 }
    );
    return fs.readFileSync(textPath, "utf8");
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function noticeSortValue(row) {
  const value = Date.parse(row?.Notice_Date ?? row?.dt_tm ?? "");
  return Number.isFinite(value) ? value : 0;
}

export async function auditLatestBseSmeAdditionNotices(batchSize = NOTICE_BATCH_SIZE) {
  validateNoticeBatchSize(batchSize);
  const catalog = await fetchJson(BSE_INDEX_NOTICE_LIST_URL);
  if (!Array.isArray(catalog?.Table)) throw new Error("BSE notice catalog has no Table array");
  const all = catalog.Table;
  const eligible = all
    .filter(isBseSmeAdditionNotice)
    .filter((row) => {
      const year = new Date(row?.Notice_Date ?? row?.dt_tm ?? "").getUTCFullYear();
      return Number.isInteger(year) && year >= 2020 && year <= 2026;
    })
    .sort((a, b) => noticeSortValue(b) - noticeSortValue(a));

  const selected = eligible.slice(0, batchSize);
  const recoveryRecords = loadRecoveryRecords();
  const retainedUrls = retainedListingUrls();

  const stats = {
    catalog_rows: all.length,
    eligible_sme_addition_notices: eligible.length,
    attempted_notices: selected.length,
    fetched_notices: 0,
    parsed_entries: 0,
    exact_matches: 0,
    prefix_matches: 0,
    unmatched_candidates: 0,
    ambiguous_matches: 0,
    already_retained_sources: 0,
    pdf_notice_downloads: 0,
    detail_api_fallbacks: 0,
    parse_failures: 0,
    fetch_errors: 0
  };
  const candidates = [];
  const failures = [];

  for (const [noticeIndex, notice] of selected.entries()) {
    if (noticeIndex > 0) await new Promise((resolve) => setTimeout(resolve, 150));
    const noticeNo = String(notice?.notice_no ?? notice?.Notice_no ?? "").trim();
    if (!/^\d{8}-\d+$/.test(noticeNo)) {
      stats.parse_failures += 1;
      failures.push({ notice_no: noticeNo || null, reason: "invalid_notice_number" });
      continue;
    }

    const indexNoticePdfUrl = officialNoticePdfUrl(notice);
    let noticeText = "";
    let sourceKind = null;
    let pdfError = null;

    if (indexNoticePdfUrl) {
      try {
        noticeText = await fetchPdfText(indexNoticePdfUrl);
        sourceKind = "bse_index_notice_pdf";
        stats.pdf_notice_downloads += 1;
      } catch (error) {
        pdfError = String(error?.message || error);
      }
    }

    if (!noticeText) {
      try {
        const detail = await fetchJson(BSE_INDEX_NOTICE_DETAIL_URL + encodeURIComponent(noticeNo));
        noticeText = typeof detail?.Data === "string" ? detail.Data : "";
        sourceKind = "bse_index_notice_detail_api";
        stats.detail_api_fallbacks += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        failures.push({
          notice_no: noticeNo,
          reason: "notice_source_fetch_error",
          pdf_url: indexNoticePdfUrl,
          pdf_error: pdfError,
          detail_error: String(error?.message || error)
        });
        continue;
      }
    }

    stats.fetched_notices += 1;
    const parsed = parseBseSmeAdditionNoticeHtml(noticeText);
    if (parsed.length === 0) {
      stats.parse_failures += 1;
      failures.push({
        notice_no: noticeNo,
        reason: "no_parseable_listing_reference",
        source_kind: sourceKind,
        index_notice_pdf_url: indexNoticePdfUrl,
        pdf_error: pdfError,
        ...(failures.length < 3
          ? { excerpt: summarizeBseNoticeParseFailure(noticeText) }
          : {})
      });
      continue;
    }

    for (const row of parsed) {
      stats.parsed_entries += 1;
      const sourceUrl = listingNoticeUrl(row.listing_notice_no);
      const match = matchIndexCompany(row.issuer_name, recoveryRecords);
      if (match.match_type === "exact") stats.exact_matches += 1;
      else if (match.match_type === "prefix") stats.prefix_matches += 1;
      else if (match.match_type === "none") stats.unmatched_candidates += 1;
      else stats.ambiguous_matches += 1;

      const retained = retainedUrls.has(sourceUrl);
      if (retained) stats.already_retained_sources += 1;

      candidates.push({
        index_notice_no: noticeNo,
        index_notice_date: isoDate(notice?.Notice_Date ?? notice?.dt_tm),
        index_notice_subject: normalizeText(notice?.Subject ?? notice?.subject),
        index_notice_pdf_url: indexNoticePdfUrl,
        index_notice_source_kind: sourceKind,
        index_notice_source_url: sourceKind === "bse_index_notice_pdf"
          ? indexNoticePdfUrl
          : BSE_INDEX_NOTICE_DETAIL_URL + encodeURIComponent(noticeNo),
        extracted_text_sha256: createHash("sha256").update(noticeText, "utf8").digest("hex"),
        collected_at: new Date().toISOString(),
        ...row,
        listing_notice_url: sourceUrl,
        source_already_retained: retained,
        match_type: match.match_type,
        matched_issuer: match.match?.record?.issuer_name ?? null,
        matched_year: match.match?.year ?? null
      });
    }

  }

  return { stats, candidates, failures };
}

async function run() {
  const batchArg = process.argv.find((arg) => arg.startsWith("--batch="));
  const batchSize = validateNoticeBatchSize(batchArg ? Number(batchArg.slice("--batch=".length)) : NOTICE_BATCH_SIZE);
  const outputArg = process.argv.find((arg) => arg.startsWith("--output="));
  let result;
  try {
    result = await auditLatestBseSmeAdditionNotices(batchSize);
  } catch (error) {
    result = { stats: null, candidates: [], failures: [{
      reason: "audit_collection_error", error: String(error?.message || error)
    }] };
  }
  const report = {
    schema_version: "1.0.0",
    parser_version: NOTICE_PARSER_VERSION,
    generated_at: new Date().toISOString(),
    run_id: process.env.GITHUB_RUN_ID || null,
    commit_sha: process.env.GITHUB_SHA || null,
    batch_limit: batchSize,
    status: classifyAdditionNoticeAudit(result),
    ...result,
    scope_note: "Discovery candidates only. Index admission dates are not listing dates. " +
      "Verify issuer-specific official BSE listing notices before materialization."
  };
  const json = JSON.stringify({ bse_sme_addition_notice_audit: report }, null, 2) + "\n";
  if (outputArg) {
    const output = path.resolve(outputArg.slice("--output=".length));
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.writeFileSync(output, json);
  }
  console.log(json.trimEnd());
  if (["failed", "partial"].includes(report.status)) process.exitCode = 1;
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
