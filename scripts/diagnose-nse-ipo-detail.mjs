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

export function collectBidLotFields(value, pathParts = [], out = []) {
  if (Array.isArray(value)) {
    value.forEach((item, index) => collectBidLotFields(item, [...pathParts, String(index)], out));
    return out;
  }
  if (!value || typeof value !== "object") return out;

  for (const [key, item] of Object.entries(value)) {
    const nextPath = [...pathParts, key];
    const normalizedKey = key.replace(/[^a-z0-9]/gi, "").toLowerCase();
    const relevant =
      /bid/.test(normalizedKey) ||
      /lot/.test(normalizedKey) ||
      /minimum/.test(normalizedKey) ||
      /minorder/.test(normalizedKey) ||
      /quantity/.test(normalizedKey);

    if (relevant && (item === null || ["string","number","boolean"].includes(typeof item))) {
      out.push({ path: nextPath.join("."), key, value: item });
    }

    if (item && typeof item === "object") {
      collectBidLotFields(item, nextPath, out);
    }
  }
  return out;
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
        record.nse_symbol &&
        record.nse_series &&
        (record.terms?.minimum_bid_quantity === null || record.terms?.minimum_bid_quantity === undefined) &&
        (record.minimum_bid_quantity?.value === null || record.minimum_bid_quantity?.value === undefined)
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

function apiUrl(record) {
  const url = new URL(API_BASE);
  url.searchParams.set("symbol", normalizeText(record.nse_symbol).toUpperCase());
  url.searchParams.set("series", normalizeText(record.nse_series).toUpperCase());
  return url.href;
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
  const stats = {
    candidates: 0,
    api_success: 0,
    responses_with_bid_fields: 0,
    fetch_errors: 0
  };

  for (const { record } of candidateRecords()) {
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
      const fields = collectBidLotFields(payload).slice(0, 80);
      if (fields.length > 0) stats.responses_with_bid_fields += 1;

      console.log(JSON.stringify({
        issuer_name: record.issuer_name,
        symbol: record.nse_symbol,
        series: record.nse_series,
        url,
        top_level_type: Array.isArray(payload) ? "array" : typeof payload,
        top_level_keys: payload && !Array.isArray(payload) && typeof payload === "object"
          ? Object.keys(payload).slice(0, 80)
          : [],
        array_length: Array.isArray(payload) ? payload.length : null,
        bid_lot_fields: fields
      }, null, 2));
    } catch (error) {
      stats.fetch_errors += 1;
      console.warn(JSON.stringify({
        issuer_name: record.issuer_name,
        symbol: record.nse_symbol,
        series: record.nse_series,
        url,
        error: error.message
      }));
    }

    await new Promise((resolve) => setTimeout(resolve, 650));
  }

  console.log(JSON.stringify({ nse_ipo_detail_diagnostic_stats: stats }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;

if (isMain) {
  run().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
