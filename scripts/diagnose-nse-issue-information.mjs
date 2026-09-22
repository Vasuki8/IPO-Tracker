import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const NSE_HOME = "https://www.nseindia.com/market-data/issue-information";
const USER_AGENT =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";
const TARGET_ISSUERS = new Set([
  "Adroit Industries (India) Limited",
  "National Stock Exchange of India Limited",
  "Swastika Infra Limited"
]);

function normalizeText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function stripTags(value) {
  return normalizeText(
    String(value ?? "")
      .replace(/<script\b[\s\S]*?<\/script>/gi, " ")
      .replace(/<style\b[\s\S]*?<\/style>/gi, " ")
      .replace(/<[^>]*>/g, " ")
      .replace(/&nbsp;/gi, " ")
      .replace(/&amp;/gi, "&")
      .replace(/&quot;/gi, '"')
      .replace(/&#39;|&apos;/gi, "'")
  );
}

export function parseIssueInformationBidTerms(html) {
  const text = stripTags(html);
  const bidLot = text.match(
    /\bBid\s+Lot\s*[:\-]?\s*([0-9][0-9,]*)\s+Equity\s+Shares\b/i
  );
  const minimumOrder = text.match(
    /\bMinimum\s+Order\s+Quantity\s*[:\-]?\s*([0-9][0-9,]*)\s+Equity\s+Shares\b/i
  );

  return {
    bid_lot: bidLot ? Number(bidLot[1].replace(/,/g, "")) : null,
    minimum_order_quantity: minimumOrder ? Number(minimumOrder[1].replace(/,/g, "")) : null,
    contexts: [
      ...text.matchAll(/\b(?:Bid\s+Lot|Minimum\s+Order\s+Quantity)\b/ig)
    ].slice(0, 6).map((match) => {
      const start = Math.max(0, match.index - 100);
      const end = Math.min(text.length, match.index + 260);
      return text.slice(start, end);
    })
  };
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
        TARGET_ISSUERS.has(record.issuer_name) &&
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

async function fetchWithRetry(url, options, attempts = 3) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(url, options);
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

function issueInfoUrl(record, type) {
  const url = new URL(NSE_HOME);
  url.searchParams.set("series", record.nse_series);
  url.searchParams.set("symbol", record.nse_symbol);
  url.searchParams.set("type", type);
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
    pages_fetched: 0,
    pages_with_terms: 0,
    fetch_errors: 0
  };

  for (const { record } of candidateRecords()) {
    stats.candidates += 1;
    const attempts = [];

    for (const type of ["Active", "Forthcoming", "Past"]) {
      const url = issueInfoUrl(record, type);
      try {
        const response = await fetchWithRetry(url, {
          headers: {
            "user-agent": USER_AGENT,
            "accept": "text/html,application/xhtml+xml",
            "accept-language": "en-US,en;q=0.9",
            "referer": NSE_HOME,
            "cookie": cookie,
            "cache-control": "no-cache",
            "pragma": "no-cache"
          }
        });
        const html = await response.text();
        stats.pages_fetched += 1;
        const parsed = parseIssueInformationBidTerms(html);
        if (parsed.bid_lot !== null || parsed.minimum_order_quantity !== null) {
          stats.pages_with_terms += 1;
        }
        attempts.push({
          type,
          url,
          bytes: html.length,
          bid_lot: parsed.bid_lot,
          minimum_order_quantity: parsed.minimum_order_quantity,
          contexts: parsed.contexts
        });
        if (parsed.minimum_order_quantity !== null) break;
      } catch (error) {
        stats.fetch_errors += 1;
        attempts.push({ type, url, error: error.message });
      }
    }

    console.log(JSON.stringify({
      issuer_name: record.issuer_name,
      symbol: record.nse_symbol,
      series: record.nse_series,
      attempts
    }, null, 2));
  }

  console.log(JSON.stringify({ nse_issue_information_diagnostic_stats: stats }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;

if (isMain) {
  run().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
