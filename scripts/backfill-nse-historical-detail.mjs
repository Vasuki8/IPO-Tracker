import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { selectBalancedByListingYear } from "./historical-batch-selection.mjs";
import {
  applyIssuePrice,
  applyIssueSize,
  applyMarketLot,
  applyMinimumBid,
  applyPriceBand,
  parseIssuePriceFromIpoDetail,
  parseIssueSizeInrFromIpoDetail,
  parseMarketLotFromIpoDetail,
  parseMinimumBidFromIpoDetail,
  parsePriceBandFromIpoDetail,
  resolveNseIdentity
} from "./extract-nse-ipo-detail-fields.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const STATE_PATH = path.join(ROOT, "ops", "nse-historical-detail.json");
const NSE_HOME = "https://www.nseindia.com/market-data/all-upcoming-issues-ipo";
const API_BASE = "https://www.nseindia.com/api/ipo-detail";
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
export const HISTORICAL_DETAIL_BATCH_SIZE = 48;
export const HISTORICAL_DETAIL_PARSER_VERSION = "1.0.0";

function normalizeText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function recoveryFiles() {
  if (!fs.existsSync(RECOVERY_ROOT)) return [];
  return fs.readdirSync(RECOVERY_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^20\d{2}$/.test(entry.name))
    .map((entry) => path.join(RECOVERY_ROOT, entry.name, "nse-issue-information.json"))
    .filter((file) => fs.existsSync(file))
    .sort();
}

export function historicalDetailKey(record) {
  const year = String(record?.listing_date?.value || "").slice(0, 4);
  return `${year || "unknown"}|${record?.id || normalizeText(record?.issuer_name).toLowerCase()}`;
}

export function missingHistoricalDetailFields(record) {
  const fields = [];
  if (record.issue_price?.value == null) fields.push("issue_price");
  if (!record.terms?.price_band && record.price_band?.value == null) fields.push("price_band");
  if (record.terms?.market_lot == null && record.market_lot?.value == null) fields.push("market_lot");
  if (record.terms?.minimum_bid_quantity == null && record.minimum_bid_quantity?.value == null) fields.push("minimum_bid_quantity");
  if (record.issue_size_inr?.value == null) fields.push("issue_size_inr");
  return fields;
}

export function historicalDetailCandidates(
  records,
  state = { issuers: {} },
  currentYear = new Date().getUTCFullYear(),
  max = HISTORICAL_DETAIL_BATCH_SIZE
) {
  const eligible = records.filter(({ record }) => {
    const identity = resolveNseIdentity(record);
    if (!identity) return false;
    const listingYear = Number(String(record?.listing_date?.value || "").slice(0, 4));
    if (!Number.isInteger(listingYear) || listingYear >= currentYear) return false;
    if (missingHistoricalDetailFields(record).length === 0) return false;
    const item = state?.issuers?.[historicalDetailKey(record)];
    if (!item) return true;
    if (item.parser_version !== HISTORICAL_DETAIL_PARSER_VERSION) return true;
    if (item.status === "error") {
      const attempted = Date.parse(item.last_attempted_at || "");
      return !Number.isFinite(attempted) || Date.now() - attempted >= 24 * 60 * 60 * 1000;
    }
    return false;
  });
  return selectBalancedByListingYear(eligible, max);
}

export function applyHistoricalDetailPayload(record, payload, sourceUrl, collectedAt) {
  const before = missingHistoricalDetailFields(record);
  const extractions = {
    issue_price: parseIssuePriceFromIpoDetail(payload),
    price_band: parsePriceBandFromIpoDetail(payload),
    market_lot: parseMarketLotFromIpoDetail(payload),
    minimum_bid_quantity: parseMinimumBidFromIpoDetail(payload),
    issue_size_inr: parseIssueSizeInrFromIpoDetail(payload)
  };
  const changed = [];
  if (extractions.issue_price?.value != null && applyIssuePrice(record, extractions.issue_price, sourceUrl, collectedAt)) changed.push("issue_price");
  if (extractions.price_band?.value != null && applyPriceBand(record, extractions.price_band, sourceUrl, collectedAt)) changed.push("price_band");
  if (extractions.market_lot?.value != null && applyMarketLot(record, extractions.market_lot, sourceUrl, collectedAt)) changed.push("market_lot");
  if (extractions.minimum_bid_quantity?.value != null && applyMinimumBid(record, extractions.minimum_bid_quantity, sourceUrl, collectedAt)) changed.push("minimum_bid_quantity");
  if (extractions.issue_size_inr?.value != null && applyIssueSize(record, extractions.issue_size_inr, sourceUrl, collectedAt)) changed.push("issue_size_inr");
  return {
    before,
    changed,
    remaining: missingHistoricalDetailFields(record),
    reasons: Object.fromEntries(Object.entries(extractions).map(([key, value]) => [key, value?.reason ?? null]))
  };
}

function apiUrl(record) {
  const identity = resolveNseIdentity(record);
  if (!identity) return null;
  const url = new URL(API_BASE);
  url.searchParams.set("symbol", identity.symbol);
  url.searchParams.set("series", identity.series);
  return url.href;
}

function readState() {
  if (!fs.existsSync(STATE_PATH)) return { schema_version: "1.0.0", issuers: {} };
  const state = JSON.parse(fs.readFileSync(STATE_PATH, "utf8"));
  state.issuers ||= {};
  return state;
}

function writeState(state) {
  fs.mkdirSync(path.dirname(STATE_PATH), { recursive: true });
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2) + "\n");
}

function cookieHeader(headers) {
  const values = typeof headers.getSetCookie === "function"
    ? headers.getSetCookie()
    : [headers.get("set-cookie")].filter(Boolean);
  return values.map((value) => value.split(";")[0]).filter(Boolean).join("; ");
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 10000) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(timeoutMs) });
  if (!response.ok) throw new Error("HTTP " + response.status + " for " + url);
  return response;
}

async function run() {
  const groups = recoveryFiles().map((file) => ({
    file,
    recovery: JSON.parse(fs.readFileSync(file, "utf8")),
    changed: false
  }));
  const records = groups.flatMap((group) =>
    (group.recovery.records || []).map((record) => ({ group, record }))
  );
  const state = readState();
  const candidates = historicalDetailCandidates(records, state);
  const now = new Date().toISOString();

  if (candidates.length === 0) {
    console.log(JSON.stringify({ historical_nse_detail: { candidates: 0, attempted: 0, extracted_records: 0, fetch_errors: 0 } }, null, 2));
    return;
  }

  const landing = await fetchWithTimeout(NSE_HOME, {
    headers: { "user-agent": USER_AGENT, "accept": "text/html,application/xhtml+xml", "accept-language": "en-US,en;q=0.9" }
  }, 10000);
  const cookie = cookieHeader(landing.headers);

  const stats = { candidates: candidates.length, attempted: 0, api_success: 0, extracted_records: 0, extracted_fields: 0, no_fields: 0, fetch_errors: 0 };

  for (const { group, record } of candidates) {
    const key = historicalDetailKey(record);
    const url = apiUrl(record);
    stats.attempted += 1;
    try {
      const response = await fetchWithTimeout(url, {
        headers: {
          "user-agent": USER_AGENT,
          "accept": "application/json,text/plain,*/*",
          "accept-language": "en-US,en;q=0.9",
          "referer": NSE_HOME,
          "cookie": cookie,
          "cache-control": "no-cache",
          "pragma": "no-cache"
        }
      }, 10000);
      const payload = await response.json();
      stats.api_success += 1;
      const result = applyHistoricalDetailPayload(record, payload, url, now);
      if (result.changed.length) {
        group.changed = true;
        stats.extracted_records += 1;
        stats.extracted_fields += result.changed.length;
      } else {
        stats.no_fields += 1;
      }
      state.issuers[key] = {
        issuer_name: record.issuer_name,
        listing_date: record.listing_date?.value ?? null,
        last_attempted_at: now,
        parser_version: HISTORICAL_DETAIL_PARSER_VERSION,
        status: result.changed.length ? "extracted" : "no_fields",
        extracted_fields: result.changed,
        remaining_fields: result.remaining,
        source_url: url
      };
    } catch (error) {
      stats.fetch_errors += 1;
      state.issuers[key] = {
        issuer_name: record.issuer_name,
        listing_date: record.listing_date?.value ?? null,
        last_attempted_at: now,
        parser_version: HISTORICAL_DETAIL_PARSER_VERSION,
        status: "error",
        error: error.message,
        source_url: url
      };
      console.warn("Historical NSE ipo-detail unavailable for " + record.issuer_name + ": " + error.message);
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }

  for (const group of groups) {
    if (!group.changed) continue;
    group.recovery.generated_at = now;
    fs.writeFileSync(group.file, JSON.stringify(group.recovery, null, 2) + "\n");
  }
  writeState(state);
  console.log(JSON.stringify({ historical_nse_detail: stats }, null, 2));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => { console.error(error); process.exit(1); });
