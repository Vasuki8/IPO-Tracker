import fs from "node:fs";
import path from "node:path";
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

export function parseBseSmeAdditionNoticeHtml(html) {
  const body = stripTags(html);
  const rows = [];
  const pattern =
    /With reference to Notice No\.?\s*([0-9]{8}-[0-9]+)\s*,?\s*(.+?)\s*\(Exchange ticker\s*-\s*([0-9]{6})\)\s*,?\s*is(?: being)? listed on BSE,?\s*effective\s+(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*,?\s*)?([A-Za-z]+\s+\d{1,2},\s*\d{4})/gi;

  for (const match of body.matchAll(pattern)) {
    rows.push({
      listing_notice_no: match[1],
      issuer_name: normalizeText(match[2]),
      bse_scrip_code: match[3],
      listing_date: isoDate(match[4]),
      listing_date_raw: normalizeText(match[4])
    });
  }

  return rows.filter((row) =>
    /^\d{8}-\d+$/.test(row.listing_notice_no) &&
    /^\d{6}$/.test(row.bse_scrip_code) &&
    row.issuer_name &&
    row.listing_date
  );
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

function noticeSortValue(row) {
  const value = Date.parse(row?.Notice_Date ?? row?.dt_tm ?? "");
  return Number.isFinite(value) ? value : 0;
}

export async function auditLatestBseSmeAdditionNotices(batchSize = NOTICE_BATCH_SIZE) {
  const catalog = await fetchJson(BSE_INDEX_NOTICE_LIST_URL);
  const all = Array.isArray(catalog?.Table) ? catalog.Table : [];
  const eligible = all
    .filter(isBseSmeAdditionNotice)
    .filter((row) => {
      const year = new Date(row?.Notice_Date ?? row?.dt_tm ?? "").getUTCFullYear();
      return Number.isInteger(year) && year >= 2020 && year <= 2026;
    })
    .sort((a, b) => noticeSortValue(b) - noticeSortValue(a));

  const selected = eligible.slice(0, Math.max(0, Number(batchSize) || 0));
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
    already_retained_sources: 0,
    parse_failures: 0,
    fetch_errors: 0
  };
  const candidates = [];
  const failures = [];

  for (const notice of selected) {
    const noticeNo = String(notice?.notice_no ?? notice?.Notice_no ?? "").trim();
    if (!/^\d{8}-\d+$/.test(noticeNo)) {
      stats.parse_failures += 1;
      failures.push({ notice_no: noticeNo || null, reason: "invalid_notice_number" });
      continue;
    }

    try {
      const detail = await fetchJson(BSE_INDEX_NOTICE_DETAIL_URL + encodeURIComponent(noticeNo));
      stats.fetched_notices += 1;
      const parsed = parseBseSmeAdditionNoticeHtml(detail?.Data);
      if (parsed.length === 0) {
        stats.parse_failures += 1;
        failures.push({ notice_no: noticeNo, reason: "no_parseable_listing_reference" });
        continue;
      }

      for (const row of parsed) {
        stats.parsed_entries += 1;
        const sourceUrl = listingNoticeUrl(row.listing_notice_no);
        const match = matchIndexCompany(row.issuer_name, recoveryRecords);
        if (match.match_type === "exact") stats.exact_matches += 1;
        else if (match.match_type === "prefix") stats.prefix_matches += 1;
        else if (match.match_type === "none") stats.unmatched_candidates += 1;

        const retained = retainedUrls.has(sourceUrl);
        if (retained) stats.already_retained_sources += 1;

        candidates.push({
          index_notice_no: noticeNo,
          index_notice_date: isoDate(notice?.Notice_Date ?? notice?.dt_tm),
          index_notice_subject: normalizeText(notice?.Subject ?? notice?.subject),
          ...row,
          listing_notice_url: sourceUrl,
          source_already_retained: retained,
          match_type: match.match_type,
          matched_issuer: match.match?.record?.issuer_name ?? null,
          matched_year: match.match?.year ?? null
        });
      }
    } catch (error) {
      stats.fetch_errors += 1;
      failures.push({
        notice_no: noticeNo,
        reason: "detail_fetch_error",
        error: String(error?.message || error)
      });
    }

    await new Promise((resolve) => setTimeout(resolve, 150));
  }

  return { stats, candidates, failures };
}

async function run() {
  const batchArg = process.argv.find((arg) => arg.startsWith("--batch="));
  const batchSize = batchArg ? Number(batchArg.slice("--batch=".length)) : NOTICE_BATCH_SIZE;
  const result = await auditLatestBseSmeAdditionNotices(batchSize);
  console.log(JSON.stringify({ bse_sme_addition_notice_audit: result }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => {
  console.error(error);
  process.exit(1);
});
