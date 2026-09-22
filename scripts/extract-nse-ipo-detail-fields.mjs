import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const NSE_HOME = "https://www.nseindia.com/market-data/all-upcoming-issues-ipo";
const API_BASE = "https://www.nseindia.com/api/ipo-detail";
const USER_AGENT =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

function normalizeText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function normalizeTitle(value) {
  return normalizeText(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function parseEquityShareQuantity(value) {
  const text = normalizeText(value).replace(/^"|"$/g, "");
  const match = text.match(/^([0-9][0-9,]*)\s+Equity\s+Shares\b/i);
  if (!match) return null;
  const quantity = Number(match[1].replace(/,/g, ""));
  return Number.isInteger(quantity) && quantity > 0 ? quantity : null;
}

export function listingDateCandidatesFromIpoDetail(payload) {
  const meta = payload?.metaInfo;
  if (!meta || typeof meta !== "object" || Array.isArray(meta)) return [];

  const candidates = [];
  for (const [key, value] of Object.entries(meta)) {
    const normalized = key.replace(/[^a-z0-9]/gi, "").toLowerCase();
    if (normalized === "listingdate" || normalized === "dateoflisting") {
      candidates.push({ key, value });
    }
  }
  return candidates;
}

function parseStrictIsoDate(value) {
  const raw = normalizeText(value).replace(/^"|"$/g, "");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) return null;
  const parsed = new Date(raw + "T00:00:00Z");
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString().slice(0, 10) === raw ? raw : null;
}

export function parseListingDateFromIpoDetail(payload) {
  const rawValue = payload?.metaInfo?.listingDate;
  if (rawValue === null || rawValue === undefined || normalizeText(rawValue) === "") {
    return { value: null, reason: "term_absent", source_value: null };
  }

  const sourceValue = normalizeText(rawValue).replace(/^"|"$/g, "");
  const value = parseStrictIsoDate(sourceValue);
  if (!value) {
    return { value: null, reason: "unparseable_listing_date", source_value: sourceValue };
  }

  return {
    value,
    reason: null,
    source_value: sourceValue,
    source_key: "listingDate"
  };
}

export function priceBandCandidatesFromIpoDetail(payload) {
  const list = payload?.issueInfo?.dataList;
  if (!Array.isArray(list)) return [];
  return list
    .filter((item) => {
      const title = normalizeTitle(item?.title);
      return title === "price range" || title === "price band";
    })
    .map((item) => ({
      title: normalizeText(item?.title),
      value: normalizeText(item?.value).replace(/^"|"$/g, "")
    }));
}

function parseRupeeBand(value) {
  const text = normalizeText(value).replace(/^"|"$/g, "");
  const currency = "(?:₹|Rs\\.?|INR)";
  const amount = "([0-9][0-9,]*(?:\\.[0-9]{1,2})?)";
  const pattern = new RegExp(
    "^\\s*" + currency + "\\s*" + amount + "\\s*(?:\\/\\-)?\\s*" +
    "(?:to|[-–—])\\s*" + currency + "\\s*" + amount + "\\s*(?:\\/\\-)?\\s*" +
    "per\\s+(?:Equity\\s+)?Share\\b",
    "i"
  );
  const match = text.match(pattern);
  if (!match) return null;

  const min = Number(match[1].replace(/,/g, ""));
  const max = Number(match[2].replace(/,/g, ""));
  if (!Number.isFinite(min) || !Number.isFinite(max) || min <= 0 || max <= 0 || min > max) {
    return null;
  }
  return { min, max };
}

export function parsePriceBandFromIpoDetail(payload) {
  const candidates = priceBandCandidatesFromIpoDetail(payload);
  const parsed = [];

  for (const item of candidates) {
    const band = parseRupeeBand(item.value);
    if (band) parsed.push({ ...item, ...band });
  }

  if (parsed.length === 0) {
    return {
      value: null,
      reason: candidates.length > 0 ? "placeholder_or_unparseable" : "term_absent",
      evidence_items: candidates
    };
  }

  const unique = new Map(
    parsed.map((item) => [item.min + "|" + item.max, item])
  );
  if (unique.size !== 1) {
    return {
      value: null,
      reason: "official_term_conflict",
      evidence_items: candidates
    };
  }

  const item = [...unique.values()][0];
  return {
    value: { min: item.min, max: item.max },
    reason: null,
    source_value: item.value,
    source_title: item.title,
    evidence_items: candidates
  };
}

function stripParentheticalText(value) {
  const text = String(value ?? "");
  let depth = 0;
  let out = "";
  for (const ch of text) {
    if (ch === "(") {
      depth += 1;
      continue;
    }
    if (ch === ")") {
      if (depth > 0) depth -= 1;
      continue;
    }
    if (depth === 0) out += ch;
  }
  return normalizeText(out);
}

function parseInrAmountWithUnit(value) {
  const text = normalizeText(value);
  const match = text.match(
    /(?:₹|Rs\.?|INR)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(crores?|millions?|lakhs?|lacs?)\b/i
  );
  if (!match) return null;

  const number = Number(match[1].replace(/,/g, ""));
  if (!Number.isFinite(number) || number <= 0) return null;

  const unit = match[2].toLowerCase().replace(/s$/, "");
  const multiplier = unit === "crore"
    ? 1e7
    : unit === "million"
      ? 1e6
      : 1e5;

  return {
    value: number * multiplier,
    source_amount: match[0]
  };
}

export function parseIssueSizeInrFromIpoDetail(payload) {
  const candidates = issueSizeCandidatesFromIpoDetail(payload);
  if (candidates.length === 0) {
    return { value: null, reason: "term_absent", evidence_items: [] };
  }

  const parsed = [];
  for (const candidate of candidates) {
    const text = stripParentheticalText(candidate.value);
    const hasFresh = /\bfresh\s+(?:issue|offer)\b/i.test(text);
    const hasOfs = /\boffer\s+for\s+sale\b|\bOFS\b/i.test(text);

    // Never combine multiple offer legs here. Mixed offers require arithmetic
    // or a separately stated overall total, neither of which this parser does.
    if (hasFresh && hasOfs) continue;

    // A sole explicitly stated Fresh Issue or OFS leg is the entire offer;
    // accepting its INR aggregate requires no arithmetic.
    if (hasFresh || hasOfs) {
      const amount = parseInrAmountWithUnit(text);
      if (!amount) continue;
      parsed.push({
        ...candidate,
        value_inr: amount.value,
        source_amount: amount.source_amount
      });
      continue;
    }

    // Without a single-leg statement, do not reinterpret share counts or
    // generic prose as an INR total.
  }

  if (parsed.length === 0) {
    return {
      value: null,
      reason: "no_safe_overall_inr_total",
      evidence_items: candidates
    };
  }

  const unique = new Map(
    parsed.map((item) => [String(item.value_inr), item])
  );
  if (unique.size !== 1) {
    return {
      value: null,
      reason: "official_term_conflict",
      evidence_items: candidates
    };
  }

  const item = [...unique.values()][0];
  return {
    value: item.value_inr,
    reason: null,
    source_value: item.value,
    source_title: item.title,
    source_amount: item.source_amount,
    evidence_items: candidates
  };
}

export function issueSizeCandidatesFromIpoDetail(payload) {
  const list = payload?.issueInfo?.dataList;
  if (!Array.isArray(list)) return [];

  return list
    .filter((item) => {
      const title = normalizeTitle(item?.title);
      return title === "issue size" || title === "total issue size" || title === "offer size";
    })
    .map((item) => ({
      title: normalizeText(item?.title),
      value: normalizeText(item?.value).replace(/^"|"$/g, "")
    }));
}

export function issuePriceCandidatesFromIpoDetail(payload) {
  const list = payload?.issueInfo?.dataList;
  const candidates = [];

  if (Array.isArray(list)) {
    for (const item of list) {
      const title = normalizeTitle(item?.title);
      if (title === "issue price" || title === "final issue price" || title === "offer price") {
        candidates.push({
          source: "issueInfo.dataList",
          title: normalizeText(item?.title),
          value: normalizeText(item?.value).replace(/^"|"$/g, "")
        });
      }
    }
  }

  const meta = payload?.metaInfo;
  if (meta && typeof meta === "object" && !Array.isArray(meta)) {
    for (const [key, value] of Object.entries(meta)) {
      const normalized = key.replace(/[^a-z0-9]/gi, "").toLowerCase();
      if (normalized === "issueprice" || normalized === "finalissueprice" || normalized === "offerprice") {
        candidates.push({
          source: "metaInfo",
          title: key,
          value: normalizeText(value).replace(/^"|"$/g, "")
        });
      }
    }
  }

  return candidates;
}

export function marketLotCandidatesFromIpoDetail(payload) {
  const list = payload?.issueInfo?.dataList;
  if (!Array.isArray(list)) return [];

  return list
    .filter((item) => {
      const title = normalizeTitle(item?.title);
      return title === "market lot" || title === "lot size";
    })
    .map((item) => ({
      title: normalizeText(item?.title),
      value: normalizeText(item?.value).replace(/^"|"$/g, "")
    }));
}

export function parseMarketLotFromIpoDetail(payload) {
  const candidates = marketLotCandidatesFromIpoDetail(payload);
  const parsed = [];

  for (const item of candidates) {
    const quantity = parseEquityShareQuantity(item.value);
    if (quantity !== null) {
      parsed.push({ ...item, quantity });
    }
  }

  if (parsed.length === 0) {
    return {
      value: null,
      reason: candidates.length > 0 ? "placeholder_or_unparseable" : "term_absent",
      evidence_items: candidates
    };
  }

  const unique = [...new Set(parsed.map((item) => item.quantity))];
  if (unique.length !== 1) {
    return {
      value: null,
      reason: "official_term_conflict",
      evidence_items: candidates
    };
  }

  const preferred =
    parsed.find((item) => normalizeTitle(item.title) === "market lot") ||
    parsed.find((item) => normalizeTitle(item.title) === "lot size");

  return {
    value: unique[0],
    reason: null,
    source_value: preferred.value,
    source_title: preferred.title,
    evidence_items: candidates
  };
}

export function minimumApplicationCandidatesFromIpoDetail(payload) {
  const list = payload?.issueInfo?.dataList;
  if (!Array.isArray(list)) return [];

  return list
    .filter((item) => {
      const title = normalizeTitle(item?.title);
      const hasMinimum = title.includes("minimum");
      const hasApplication = title.includes("application");
      const hasInvestment = title.includes("investment");
      return hasMinimum && (hasApplication || hasInvestment);
    })
    .map((item) => ({
      title: normalizeText(item?.title),
      value: normalizeText(item?.value).replace(/^"|"$/g, "")
    }));
}

export function parseMinimumBidFromIpoDetail(payload) {
  const list = payload?.issueInfo?.dataList;
  if (!Array.isArray(list)) {
    return { value: null, reason: "missing_issue_info", evidence_items: [] };
  }

  const values = [];
  const evidenceItems = [];

  for (const item of list) {
    const title = normalizeTitle(item?.title);
    if (title !== "minimum order quantity" && title !== "bid lot") continue;

    const rawValue = normalizeText(item?.value).replace(/^"|"$/g, "");
    evidenceItems.push({
      title: normalizeText(item?.title),
      value: rawValue
    });

    const quantity = parseEquityShareQuantity(rawValue);
    if (quantity !== null) {
      values.push({ title, quantity, rawValue });
    }
  }

  if (values.length === 0) {
    return {
      value: null,
      reason: evidenceItems.length > 0 ? "placeholder_or_unparseable" : "term_absent",
      evidence_items: evidenceItems
    };
  }

  const unique = [...new Set(values.map((item) => item.quantity))];
  if (unique.length !== 1) {
    return {
      value: null,
      reason: "official_term_conflict",
      evidence_items: evidenceItems
    };
  }

  const preferred =
    values.find((item) => item.title === "minimum order quantity") ||
    values.find((item) => item.title === "bid lot");

  return {
    value: unique[0],
    reason: null,
    source_value: preferred.rawValue,
    source_title: preferred.title === "minimum order quantity"
      ? "Minimum Order Quantity"
      : "Bid Lot",
    evidence_items: evidenceItems
  };
}

export function resolveNseIdentity(record) {
  const directSymbol = normalizeText(record?.nse_symbol).toUpperCase();
  const directSeries = normalizeText(record?.nse_series).toUpperCase();
  if (directSymbol && directSeries) {
    return { symbol: directSymbol, series: directSeries, source: "retained_fields" };
  }

  const candidates = [
    record?.nse_source?.url,
    ...(record?.documents || [])
      .filter((doc) =>
        doc.type === "NSE Issue Information" ||
        doc.type === "NSE Issue Information API"
      )
      .map((doc) => doc.url)
  ].filter(Boolean);

  for (const rawUrl of candidates) {
    try {
      const url = new URL(rawUrl);
      if (url.protocol !== "https:" || !["www.nseindia.com", "nseindia.com"].includes(url.hostname)) {
        continue;
      }
      const symbol = normalizeText(url.searchParams.get("symbol")).toUpperCase();
      const series = normalizeText(url.searchParams.get("series")).toUpperCase();
      if (!symbol || !["EQ", "SME"].includes(series)) continue;
      return { symbol, series, source: "retained_official_url" };
    } catch {
      // Ignore malformed legacy URLs; keep the record unresolved.
    }
  }

  return null;
}

function recoveryFiles() {
  if (!fs.existsSync(RECOVERY_ROOT)) return [];
  return fs.readdirSync(RECOVERY_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .flatMap((entry) => {
      const file = path.join(RECOVERY_ROOT, entry.name, "nse-issue-information.json");
      return fs.existsSync(file) ? [file] : [];
    })
    .sort();
}

function candidateRecords() {
  return recoveryFiles().flatMap((file) => {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    return (recovery.records || [])
      .filter((record) =>
        resolveNseIdentity(record) &&
        (record.terms?.minimum_bid_quantity === null || record.terms?.minimum_bid_quantity === undefined) &&
        (record.minimum_bid_quantity?.value === null || record.minimum_bid_quantity?.value === undefined)
      )
      .map((record) => ({ file, recovery, record }));
  });
}

function marketLotCandidateRecords() {
  return recoveryFiles().flatMap((file) => {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    return (recovery.records || [])
      .filter((record) =>
        resolveNseIdentity(record) &&
        (record.terms?.market_lot === null || record.terms?.market_lot === undefined) &&
        (record.market_lot?.value === null || record.market_lot?.value === undefined)
      )
      .map((record) => ({ file, recovery, record }));
  });
}

function issueSizeCandidateRecords() {
  return recoveryFiles().flatMap((file) => {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    return (recovery.records || [])
      .filter((record) =>
        resolveNseIdentity(record) &&
        (record.issue_size_inr?.value === null || record.issue_size_inr?.value === undefined)
      )
      .map((record) => ({ file, recovery, record }));
  });
}

function priceBandCandidateRecords() {
  return recoveryFiles().flatMap((file) => {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    return (recovery.records || [])
      .filter((record) =>
        resolveNseIdentity(record) &&
        !record.terms?.price_band &&
        (record.price_band?.value === null || record.price_band?.value === undefined)
      )
      .map((record) => ({ file, recovery, record }));
  });
}

function listingDateCandidateRecords() {
  return recoveryFiles().flatMap((file) => {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    return (recovery.records || [])
      .filter((record) =>
        resolveNseIdentity(record) &&
        (record.listing_date?.value === null || record.listing_date?.value === undefined)
      )
      .map((record) => ({ file, recovery, record }));
  });
}

function cookieHeader(headers) {
  const values = typeof headers.getSetCookie === "function"
    ? headers.getSetCookie()
    : [headers.get("set-cookie")].filter(Boolean);
  return values.map((value) => value.split(";")[0]).filter(Boolean).join("; ");
}

async function fetchWithRetry(url, options, attempts = 3, timeoutMs = 15000) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(url, {
        ...options,
        signal: AbortSignal.timeout(timeoutMs)
      });
      if (response.ok) return response;
      lastError = new Error("HTTP " + response.status + " for " + url);
    } catch (error) {
      lastError = error;
    }
    if (attempt < attempts) {
      await new Promise((resolve) => setTimeout(resolve, attempt * 1200));
    }
  }
  throw lastError;
}

function apiUrl(record) {
  const identity = resolveNseIdentity(record);
  if (!identity) return null;
  const url = new URL(API_BASE);
  url.searchParams.set("symbol", identity.symbol);
  url.searchParams.set("series", identity.series);
  return url.href;
}

function addDocumentOnce(record, document) {
  record.documents ||= [];
  if (record.documents.some((item) => item.url === document.url && item.identity === document.identity)) {
    return false;
  }
  record.documents.push(document);
  return true;
}

export function applyMarketLot(record, extraction, sourceUrl, collectedAt) {
  if (!extraction?.value) return false;
  if (record.terms?.market_lot !== null && record.terms?.market_lot !== undefined) return false;
  if (record.market_lot?.value !== null && record.market_lot?.value !== undefined) return false;

  const identity = resolveNseIdentity(record);
  if (!identity) return false;
  const symbol = identity.symbol;

  if (!record.nse_symbol) record.nse_symbol = identity.symbol;
  if (!record.nse_series) record.nse_series = identity.series;

  record.market_lot = {
    value: extraction.value,
    source_value: extraction.source_value,
    status: "verified",
    page: null,
    source: {
      url: sourceUrl,
      document_type: "NSE Issue Information API",
      document_identity: "NSE Issue Information — " + symbol,
      publication_date: null,
      collected_at: collectedAt
    }
  };

  addDocumentOnce(record, {
    type: "NSE Issue Information API",
    identity: "NSE Issue Information — " + symbol,
    url: sourceUrl,
    publication_date: null,
    collected_at: collectedAt
  });

  record.last_collected_at = collectedAt;
  return true;
}

export function applyIssueSize(record, extraction, sourceUrl, collectedAt) {
  if (!extraction?.value) return false;
  if (record.issue_size_inr?.value !== null && record.issue_size_inr?.value !== undefined) return false;

  const identity = resolveNseIdentity(record);
  if (!identity) return false;
  const symbol = identity.symbol;

  if (!record.nse_symbol) record.nse_symbol = identity.symbol;
  if (!record.nse_series) record.nse_series = identity.series;

  record.issue_size_inr = {
    value: extraction.value,
    source_value: extraction.source_value,
    status: "verified",
    page: null,
    source: {
      url: sourceUrl,
      document_type: "NSE Issue Information API",
      document_identity: "NSE Issue Information — " + symbol,
      publication_date: null,
      collected_at: collectedAt
    }
  };

  addDocumentOnce(record, {
    type: "NSE Issue Information API",
    identity: "NSE Issue Information — " + symbol,
    url: sourceUrl,
    publication_date: null,
    collected_at: collectedAt
  });

  record.last_collected_at = collectedAt;
  return true;
}

export function applyPriceBand(record, extraction, sourceUrl, collectedAt) {
  if (!extraction?.value) return false;
  if (record.terms?.price_band) return false;
  if (record.price_band?.value !== null && record.price_band?.value !== undefined) return false;

  const identity = resolveNseIdentity(record);
  if (!identity) return false;
  const symbol = identity.symbol;

  if (!record.nse_symbol) record.nse_symbol = identity.symbol;
  if (!record.nse_series) record.nse_series = identity.series;

  record.price_band = {
    value: extraction.value,
    source_value: extraction.source_value,
    status: "verified",
    page: null,
    source: {
      url: sourceUrl,
      document_type: "NSE Issue Information API",
      document_identity: "NSE Issue Information — " + symbol,
      publication_date: null,
      collected_at: collectedAt
    }
  };

  addDocumentOnce(record, {
    type: "NSE Issue Information API",
    identity: "NSE Issue Information — " + symbol,
    url: sourceUrl,
    publication_date: null,
    collected_at: collectedAt
  });

  record.last_collected_at = collectedAt;
  return true;
}

export function applyListingDate(record, extraction, sourceUrl, collectedAt) {
  if (!extraction?.value) return false;
  if (record.listing_date?.value !== null && record.listing_date?.value !== undefined) return false;

  const identity = resolveNseIdentity(record);
  if (!identity) return false;
  const symbol = identity.symbol;

  if (!record.nse_symbol) record.nse_symbol = identity.symbol;
  if (!record.nse_series) record.nse_series = identity.series;

  record.listing_date = {
    value: extraction.value,
    source_value: extraction.source_value,
    status: "verified",
    page: null,
    source: {
      url: sourceUrl,
      document_type: "NSE Issue Information API",
      document_identity: "NSE Issue Information — " + symbol,
      publication_date: null,
      collected_at: collectedAt
    }
  };

  addDocumentOnce(record, {
    type: "NSE Issue Information API",
    identity: "NSE Issue Information — " + symbol,
    url: sourceUrl,
    publication_date: null,
    collected_at: collectedAt
  });

  record.last_collected_at = collectedAt;
  return true;
}

export function applyMinimumBid(record, extraction, sourceUrl, collectedAt) {
  if (!extraction?.value) return false;
  if (record.minimum_bid_quantity?.value !== null && record.minimum_bid_quantity?.value !== undefined) return false;
  if (record.terms?.minimum_bid_quantity !== null && record.terms?.minimum_bid_quantity !== undefined) return false;

  const identity = resolveNseIdentity(record);
  if (!identity) return false;
  const symbol = identity.symbol;

  if (!record.nse_symbol) record.nse_symbol = identity.symbol;
  if (!record.nse_series) record.nse_series = identity.series;

  record.minimum_bid_quantity = {
    value: extraction.value,
    source_value: extraction.source_value,
    status: "verified",
    page: null,
    source: {
      url: sourceUrl,
      document_type: "NSE Issue Information API",
      document_identity: "NSE Issue Information — " + symbol,
      publication_date: null,
      collected_at: collectedAt
    }
  };

  addDocumentOnce(record, {
    type: "NSE Issue Information API",
    identity: "NSE Issue Information — " + symbol,
    url: sourceUrl,
    publication_date: null,
    collected_at: collectedAt
  });

  record.last_collected_at = collectedAt;
  return true;
}

async function diagnosePriceBand() {
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const stats = {
    candidates: 0,
    api_success: 0,
    responses_with_price_band_terms: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      if (record.terms?.price_band || record.price_band?.value) continue;
      const identity = resolveNseIdentity(record);
      if (!identity) continue;
      stats.candidates += 1;

      const url = apiUrl(record);
      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "application/json,text/plain,*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const payload = await response.json();
        stats.api_success += 1;
        const candidates = priceBandCandidatesFromIpoDetail(payload);
        if (candidates.length > 0) stats.responses_with_price_band_terms += 1;

        console.log(JSON.stringify({
          issuer_name: record.issuer_name,
          symbol: identity.symbol,
          series: identity.series,
          url,
          price_band_candidates: candidates
        }, null, 2));
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn("NSE price-band diagnostic unavailable for " + record.issuer_name + ": " + error.message);
      }
    }
  }

  console.log(JSON.stringify({ nse_price_band_diagnostic_stats: stats }, null, 2));
}

async function diagnoseIssueSize() {
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const stats = {
    candidates: 0,
    api_success: 0,
    responses_with_issue_size_terms: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      if (record.issue_size_inr?.value !== null && record.issue_size_inr?.value !== undefined) continue;
      const identity = resolveNseIdentity(record);
      if (!identity) continue;

      stats.candidates += 1;
      const url = apiUrl(record);

      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "application/json,text/plain,*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const payload = await response.json();
        stats.api_success += 1;
        const candidates = issueSizeCandidatesFromIpoDetail(payload);
        if (candidates.length > 0) stats.responses_with_issue_size_terms += 1;

        console.log(JSON.stringify({
          issuer_name: record.issuer_name,
          symbol: identity.symbol,
          series: identity.series,
          url,
          issue_size_candidates: candidates
        }, null, 2));
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn("NSE issue-size diagnostic unavailable for " + record.issuer_name + ": " + error.message);
      }

      await new Promise((resolve) => setTimeout(resolve, 650));
    }
  }

  console.log(JSON.stringify({ nse_issue_size_diagnostic_stats: stats }, null, 2));
}

async function diagnoseIssuePrice() {
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const stats = {
    candidates: 0,
    api_success: 0,
    responses_with_issue_price_terms: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      if (record.issue_price?.value !== null && record.issue_price?.value !== undefined) continue;
      if (record.listing_date?.value === null || record.listing_date?.value === undefined) continue;
      const identity = resolveNseIdentity(record);
      if (!identity) continue;

      stats.candidates += 1;
      const url = apiUrl(record);

      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "application/json,text/plain,*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const payload = await response.json();
        stats.api_success += 1;
        const candidates = issuePriceCandidatesFromIpoDetail(payload);
        if (candidates.length > 0) stats.responses_with_issue_price_terms += 1;

        console.log(JSON.stringify({
          issuer_name: record.issuer_name,
          symbol: identity.symbol,
          series: identity.series,
          listing_date: record.listing_date.value,
          url,
          issue_price_candidates: candidates
        }, null, 2));
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn("NSE issue-price diagnostic unavailable for " + record.issuer_name + ": " + error.message);
      }

      await new Promise((resolve) => setTimeout(resolve, 650));
    }
  }

  console.log(JSON.stringify({ nse_issue_price_diagnostic_stats: stats }, null, 2));
}

async function diagnoseMinimumApplicationAmount() {
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const stats = {
    candidates: 0,
    api_success: 0,
    responses_with_application_terms: 0,
    fetch_errors: 0
  };

  const seen = new Set();

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      const identity = resolveNseIdentity(record);
      if (!identity) continue;
      const key = identity.symbol + "|" + identity.series;
      if (seen.has(key)) continue;
      seen.add(key);
      stats.candidates += 1;

      const url = apiUrl(record);
      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "application/json,text/plain,*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const payload = await response.json();
        stats.api_success += 1;
        const candidates = minimumApplicationCandidatesFromIpoDetail(payload);
        if (candidates.length > 0) stats.responses_with_application_terms += 1;

        console.log(JSON.stringify({
          issuer_name: record.issuer_name,
          symbol: identity.symbol,
          series: identity.series,
          url,
          minimum_application_candidates: candidates
        }, null, 2));
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "NSE minimum-application diagnostic unavailable for " +
          record.issuer_name + ": " + error.message
        );
      }

      await new Promise((resolve) => setTimeout(resolve, 650));
    }
  }

  console.log(JSON.stringify({ nse_minimum_application_diagnostic_stats: stats }, null, 2));
}

async function diagnoseMarketLot() {
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const stats = {
    candidates: 0,
    api_success: 0,
    responses_with_market_lot_terms: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      if (record.terms?.market_lot !== null && record.terms?.market_lot !== undefined) continue;
      if (record.market_lot?.value !== null && record.market_lot?.value !== undefined) continue;

      const identity = resolveNseIdentity(record);
      if (!identity) continue;
      stats.candidates += 1;

      const url = apiUrl(record);
      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "application/json,text/plain,*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const payload = await response.json();
        stats.api_success += 1;

        const candidates = marketLotCandidatesFromIpoDetail(payload);
        if (candidates.length > 0) stats.responses_with_market_lot_terms += 1;

        console.log(JSON.stringify({
          issuer_name: record.issuer_name,
          symbol: identity.symbol,
          series: identity.series,
          url,
          market_lot_candidates: candidates
        }, null, 2));
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "NSE market-lot diagnostic unavailable for " + record.issuer_name + ": " + error.message
        );
      }

      await new Promise((resolve) => setTimeout(resolve, 650));
    }
  }

  console.log(JSON.stringify({ nse_market_lot_diagnostic_stats: stats }, null, 2));
}

async function runMarketLot() {
  const now = new Date().toISOString();
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const groups = new Map();
  for (const candidate of marketLotCandidateRecords()) {
    if (!groups.has(candidate.file)) {
      groups.set(candidate.file, { recovery: candidate.recovery, candidates: [] });
    }
    groups.get(candidate.file).candidates.push(candidate.record);
  }

  const stats = {
    candidates: 0,
    api_success: 0,
    extracted: 0,
    missing_or_placeholder: 0,
    conflicts: 0,
    fetch_errors: 0
  };

  for (const [file, group] of groups) {
    let changed = false;

    for (const record of group.candidates) {
      stats.candidates += 1;
      const url = apiUrl(record);

      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "application/json,text/plain,*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const payload = await response.json();
        stats.api_success += 1;

        const extraction = parseMarketLotFromIpoDetail(payload);
        if (extraction.reason === "official_term_conflict") {
          stats.conflicts += 1;
          console.warn(
            "NSE market-lot conflict retained as null for " + record.issuer_name + ": " +
            JSON.stringify(extraction.evidence_items)
          );
        } else if (extraction.value === null) {
          stats.missing_or_placeholder += 1;
        } else if (applyMarketLot(record, extraction, url, now)) {
          stats.extracted += 1;
          changed = true;
          console.log(
            "Extracted NSE market lot for " + record.issuer_name + ": " +
            extraction.value + " Equity Shares (" + extraction.source_title + ")"
          );
        }
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "NSE ipo-detail unavailable for market-lot extraction for " +
          record.issuer_name + ": " + error.message
        );
      }

      await new Promise((resolve) => setTimeout(resolve, 650));
    }

    if (changed) {
      group.recovery.generated_at = now;
      fs.writeFileSync(file, JSON.stringify(group.recovery, null, 2) + "\n");
    }
  }

  console.log(JSON.stringify(stats, null, 2));
}

async function runIssueSize() {
  const now = new Date().toISOString();
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const groups = new Map();
  for (const candidate of issueSizeCandidateRecords()) {
    if (!groups.has(candidate.file)) {
      groups.set(candidate.file, { recovery: candidate.recovery, candidates: [] });
    }
    groups.get(candidate.file).candidates.push(candidate.record);
  }

  const stats = {
    candidates: 0,
    api_success: 0,
    extracted: 0,
    unsupported_or_share_count: 0,
    conflicts: 0,
    fetch_errors: 0
  };

  for (const [file, group] of groups) {
    let changed = false;

    for (const record of group.candidates) {
      stats.candidates += 1;
      const url = apiUrl(record);

      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "application/json,text/plain,*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const payload = await response.json();
        stats.api_success += 1;

        const extraction = parseIssueSizeInrFromIpoDetail(payload);
        if (extraction.reason === "official_term_conflict") {
          stats.conflicts += 1;
          console.warn(
            "NSE issue-size conflict retained as null for " + record.issuer_name + ": " +
            JSON.stringify(extraction.evidence_items)
          );
        } else if (extraction.value === null) {
          stats.unsupported_or_share_count += 1;
        } else if (applyIssueSize(record, extraction, url, now)) {
          stats.extracted += 1;
          changed = true;
          console.log(
            "Extracted NSE issue size for " + record.issuer_name + ": INR " + extraction.value
          );
        }
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "NSE ipo-detail unavailable for issue-size extraction for " +
          record.issuer_name + ": " + error.message
        );
      }

      await new Promise((resolve) => setTimeout(resolve, 650));
    }

    if (changed) {
      group.recovery.generated_at = now;
      fs.writeFileSync(file, JSON.stringify(group.recovery, null, 2) + "\n");
    }
  }

  console.log(JSON.stringify(stats, null, 2));
}

async function runPriceBand() {
  const now = new Date().toISOString();
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const groups = new Map();
  for (const candidate of priceBandCandidateRecords()) {
    if (!groups.has(candidate.file)) {
      groups.set(candidate.file, { recovery: candidate.recovery, candidates: [] });
    }
    groups.get(candidate.file).candidates.push(candidate.record);
  }

  const stats = {
    candidates: 0,
    api_success: 0,
    extracted: 0,
    missing_or_placeholder: 0,
    conflicts: 0,
    fetch_errors: 0
  };

  for (const [file, group] of groups) {
    let changed = false;

    for (const record of group.candidates) {
      stats.candidates += 1;
      const url = apiUrl(record);

      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "application/json,text/plain,*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const payload = await response.json();
        stats.api_success += 1;

        const extraction = parsePriceBandFromIpoDetail(payload);
        if (extraction.reason === "official_term_conflict") {
          stats.conflicts += 1;
          console.warn(
            "NSE price-band conflict retained as null for " + record.issuer_name + ": " +
            JSON.stringify(extraction.evidence_items)
          );
        } else if (extraction.value === null) {
          stats.missing_or_placeholder += 1;
        } else if (applyPriceBand(record, extraction, url, now)) {
          stats.extracted += 1;
          changed = true;
          console.log(
            "Extracted NSE price band for " + record.issuer_name + ": " +
            extraction.value.min + " to " + extraction.value.max
          );
        }
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "NSE ipo-detail unavailable for price-band extraction for " +
          record.issuer_name + ": " + error.message
        );
      }
    }

    if (changed) {
      group.recovery.generated_at = now;
      fs.writeFileSync(file, JSON.stringify(group.recovery, null, 2) + "\n");
    }
  }

  console.log(JSON.stringify(stats, null, 2));
}

async function runListingDate() {
  const now = new Date().toISOString();
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const groups = new Map();
  for (const candidate of listingDateCandidateRecords()) {
    if (!groups.has(candidate.file)) {
      groups.set(candidate.file, { recovery: candidate.recovery, candidates: [] });
    }
    groups.get(candidate.file).candidates.push(candidate.record);
  }

  const stats = {
    candidates: 0,
    api_success: 0,
    extracted: 0,
    missing: 0,
    unparseable: 0,
    fetch_errors: 0
  };

  for (const [file, group] of groups) {
    let changed = false;

    for (const record of group.candidates) {
      stats.candidates += 1;
      const url = apiUrl(record);

      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "application/json,text/plain,*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const payload = await response.json();
        stats.api_success += 1;

        const extraction = parseListingDateFromIpoDetail(payload);
        if (extraction.reason === "unparseable_listing_date") {
          stats.unparseable += 1;
          console.warn(
            "NSE listing date unparseable for " + record.issuer_name + ": " + extraction.source_value
          );
        } else if (extraction.value === null) {
          stats.missing += 1;
        } else if (applyListingDate(record, extraction, url, now)) {
          stats.extracted += 1;
          changed = true;
          console.log(
            "Extracted NSE listing date for " + record.issuer_name + ": " + extraction.value
          );
        }
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "NSE ipo-detail unavailable for listing-date extraction for " +
          record.issuer_name + ": " + error.message
        );
      }

      await new Promise((resolve) => setTimeout(resolve, 650));
    }

    if (changed) {
      group.recovery.generated_at = now;
      fs.writeFileSync(file, JSON.stringify(group.recovery, null, 2) + "\n");
    }
  }

  console.log(JSON.stringify(stats, null, 2));
}

async function diagnoseListingDate() {
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const stats = {
    candidates: 0,
    api_success: 0,
    responses_with_listing_date: 0,
    fetch_errors: 0
  };

  const seen = new Set();
  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      if (record.listing_date?.value !== null && record.listing_date?.value !== undefined) continue;
      const identity = resolveNseIdentity(record);
      if (!identity) continue;
      const key = identity.symbol + "|" + identity.series;
      if (seen.has(key)) continue;
      seen.add(key);
      stats.candidates += 1;

      const url = apiUrl(record);
      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "application/json,text/plain,*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const payload = await response.json();
        stats.api_success += 1;
        const candidates = listingDateCandidatesFromIpoDetail(payload);
        if (candidates.length > 0) stats.responses_with_listing_date += 1;

        console.log(JSON.stringify({
          issuer_name: record.issuer_name,
          symbol: identity.symbol,
          series: identity.series,
          url,
          meta_info_keys: payload?.metaInfo && typeof payload.metaInfo === "object"
            ? Object.keys(payload.metaInfo)
            : [],
          listing_date_candidates: candidates
        }, null, 2));
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "NSE listing-date diagnostic unavailable for " + record.issuer_name + ": " + error.message
        );
      }

      await new Promise((resolve) => setTimeout(resolve, 650));
    }
  }

  console.log(JSON.stringify({ nse_listing_date_diagnostic_stats: stats }, null, 2));
}

async function run() {
  const now = new Date().toISOString();
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const groups = new Map();
  for (const candidate of candidateRecords()) {
    if (!groups.has(candidate.file)) {
      groups.set(candidate.file, { recovery: candidate.recovery, candidates: [] });
    }
    groups.get(candidate.file).candidates.push(candidate.record);
  }

  const stats = {
    candidates: 0,
    api_success: 0,
    extracted: 0,
    missing_or_placeholder: 0,
    conflicts: 0,
    fetch_errors: 0
  };

  for (const [file, group] of groups) {
    let changed = false;

    for (const record of group.candidates) {
      stats.candidates += 1;
      const url = apiUrl(record);

      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "application/json,text/plain,*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const payload = await response.json();
        stats.api_success += 1;

        const extraction = parseMinimumBidFromIpoDetail(payload);
        if (extraction.reason === "official_term_conflict") {
          stats.conflicts += 1;
          console.warn(
            "NSE minimum-bid conflict retained as null for " + record.issuer_name + ": " +
            JSON.stringify(extraction.evidence_items)
          );
        } else if (extraction.value === null) {
          stats.missing_or_placeholder += 1;
        } else if (applyMinimumBid(record, extraction, url, now)) {
          stats.extracted += 1;
          changed = true;
          console.log(
            "Extracted NSE minimum bid for " + record.issuer_name + ": " +
            extraction.value + " Equity Shares (" + extraction.source_title + ")"
          );
        }
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "NSE ipo-detail unavailable for " + record.issuer_name + ": " + error.message
        );
      }

      await new Promise((resolve) => setTimeout(resolve, 650));
    }

    if (changed) {
      group.recovery.generated_at = now;
      fs.writeFileSync(file, JSON.stringify(group.recovery, null, 2) + "\n");
    }
  }

  console.log(JSON.stringify(stats, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;

if (isMain) {
  const action = process.argv.includes("--diagnose-minimum-application")
    ? diagnoseMinimumApplicationAmount
    : process.argv.includes("--market-lot")
      ? runMarketLot
    : process.argv.includes("--diagnose-market-lot")
      ? diagnoseMarketLot
      : process.argv.includes("--issue-size")
        ? runIssueSize
    : process.argv.includes("--diagnose-issue-size")
      ? diagnoseIssueSize
    : process.argv.includes("--diagnose-issue-price")
      ? diagnoseIssuePrice
    : process.argv.includes("--price-band")
      ? runPriceBand
    : process.argv.includes("--diagnose-price-band")
      ? diagnosePriceBand
      : process.argv.includes("--listing-date")
        ? runListingDate
      : process.argv.includes("--diagnose-listing-date")
        ? diagnoseListingDate
        : run;
  action().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
