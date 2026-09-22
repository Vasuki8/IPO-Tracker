import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { resolveNseIdentity } from "./extract-nse-ipo-detail-fields.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const NSE_HOME = "https://www.nseindia.com/market-data/all-upcoming-issues-ipo";
const PAST_URL = "https://www.nseindia.com/api/public-past-issues";
const USER_AGENT =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

function normalizeText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

export function parsePastIssuePrice(value) {
  if (value === null || value === undefined) return null;
  const text = normalizeText(value).replace(/^"|"$/g, "");
  if (!text || /\[●\]|\b(?:na|n\/a|-)\b/i.test(text)) return null;

  if (/\b(?:to|[-–—])\b/.test(text.replace(/\d-\d/g, ""))) return null;

  const match = text.match(/^(?:₹|Rs\.?|INR)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(?:\/\-)?(?:\s*per\s+(?:Equity\s+)?Share)?$/i);
  if (!match) return null;
  const number = Number(match[1].replace(/,/g, ""));
  return Number.isFinite(number) && number > 0 ? number : null;
}

export function indexPastIssues(rows) {
  const bySymbol = new Map();
  for (const row of rows || []) {
    const symbol = normalizeText(row?.symbol).toUpperCase();
    if (!symbol) continue;
    if (!bySymbol.has(symbol)) bySymbol.set(symbol, []);
    bySymbol.get(symbol).push(row);
  }
  return bySymbol;
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
        (record.issue_price?.value === null || record.issue_price?.value === undefined) &&
        (record.listing_date?.value !== null && record.listing_date?.value !== undefined)
      )
      .map((record) => ({ file, record }));
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

async function run() {
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);

  const response = await fetchWithRetry(PAST_URL, {
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
  if (!Array.isArray(payload)) {
    throw new Error("NSE public-past-issues did not return an array");
  }

  const bySymbol = indexPastIssues(payload);
  const stats = {
    past_rows: payload.length,
    candidates: 0,
    exact_symbol_matches: 0,
    rows_with_parseable_issue_price: 0,
    ambiguous_symbol_matches: 0
  };

  for (const { record } of candidateRecords()) {
    const identity = resolveNseIdentity(record);
    stats.candidates += 1;
    const matches = bySymbol.get(identity.symbol) || [];
    if (matches.length > 1) {
      stats.ambiguous_symbol_matches += 1;
    }
    if (matches.length === 1) stats.exact_symbol_matches += 1;

    const rows = matches.map((row) => ({
      symbol: row.symbol ?? null,
      company: row.company ?? row.companyName ?? null,
      securityType: row.securityType ?? row.series ?? null,
      listingDate: row.listingDate ?? null,
      issuePrice: row.issuePrice ?? null,
      parsed_issue_price: parsePastIssuePrice(row.issuePrice)
    }));
    if (rows.some((row) => row.parsed_issue_price !== null)) {
      stats.rows_with_parseable_issue_price += 1;
    }

    console.log(JSON.stringify({
      issuer_name: record.issuer_name,
      symbol: identity.symbol,
      series: identity.series,
      retained_listing_date: record.listing_date.value,
      matches: rows
    }, null, 2));
  }

  console.log(JSON.stringify({ nse_past_issue_price_diagnostic_stats: stats }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;

if (isMain) {
  run().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
