import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { resolveNseIdentity } from "./extract-nse-ipo-detail-fields.mjs";
import { parseNseDate } from "./sync-nse-live.mjs";

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
  if (!text || /\[●\]|^(?:na|n\/a|-)$/i.test(text)) return null;

  const range = text.match(/(?:₹|Rs\.?|INR)?\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?\s*(?:to|[-–—])\s*(?:₹|Rs\.?|INR)?\s*[0-9]/i);
  if (range) return null;

  const match = text.match(/^(?:₹|Rs\.?|INR)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(?:\/\-)?(?:\s*per\s+(?:Equity\s+)?Share)?$/i);
  if (!match) return null;

  const parsed = Number(match[1].replace(/,/g, ""));
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

export function selectPastIssueRow(record, rows) {
  const identity = resolveNseIdentity(record);
  if (!identity) return { row: null, reason: "missing_identity" };

  const matches = (rows || []).filter((row) =>
    normalizeText(row?.symbol).toUpperCase() === identity.symbol
  );
  if (matches.length !== 1) {
    return {
      row: null,
      reason: matches.length === 0 ? "no_symbol_match" : "ambiguous_symbol_match"
    };
  }

  const row = matches[0];
  const rowSeries = normalizeText(row?.securityType ?? row?.series).toUpperCase();
  if (rowSeries && rowSeries !== identity.series) {
    return { row: null, reason: "series_mismatch" };
  }

  const rowListingDate = parseNseDate(row?.listingDate);
  if (record.listing_date?.value && rowListingDate && record.listing_date.value !== rowListingDate) {
    return { row: null, reason: "listing_date_mismatch" };
  }

  return { row, reason: null };
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

function addDocumentOnce(record, document) {
  record.documents ||= [];
  if (record.documents.some((item) => item.url === document.url && item.identity === document.identity)) {
    return false;
  }
  record.documents.push(document);
  return true;
}

export function applyPastIssuePrice(record, row, collectedAt) {
  if (record.issue_price?.value !== null && record.issue_price?.value !== undefined) return false;

  const selection = selectPastIssueRow(record, [row]);
  if (!selection.row) return false;

  const price = parsePastIssuePrice(row.issuePrice);
  if (price === null) return false;

  const identity = resolveNseIdentity(record);
  if (!identity) return false;

  record.issue_price = {
    value: price,
    source_value: normalizeText(row.issuePrice),
    status: "verified",
    page: null,
    source: {
      url: PAST_URL,
      document_type: "NSE Public Past Issues",
      document_identity: "NSE Public Past Issues — " + identity.symbol,
      publication_date: null,
      collected_at: collectedAt
    }
  };

  addDocumentOnce(record, {
    type: "NSE Public Past Issues",
    identity: "NSE Public Past Issues — " + identity.symbol,
    url: PAST_URL,
    publication_date: null,
    collected_at: collectedAt
  });

  record.last_collected_at = collectedAt;
  return true;
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

  const rows = await response.json();
  if (!Array.isArray(rows)) {
    throw new Error("NSE public-past-issues did not return an array");
  }

  const groups = new Map();
  for (const candidate of candidateRecords()) {
    if (!groups.has(candidate.file)) {
      groups.set(candidate.file, { recovery: candidate.recovery, candidates: [] });
    }
    groups.get(candidate.file).candidates.push(candidate.record);
  }

  const stats = {
    past_rows: rows.length,
    candidates: 0,
    exact_matches: 0,
    extracted: 0,
    missing_or_unparseable: 0,
    rejected_matches: 0
  };

  for (const [file, group] of groups) {
    let changed = false;

    for (const record of group.candidates) {
      stats.candidates += 1;
      const selection = selectPastIssueRow(record, rows);

      if (!selection.row) {
        stats.rejected_matches += 1;
        console.warn(
          "NSE past-issue row rejected for " + record.issuer_name + ": " + selection.reason
        );
        continue;
      }

      stats.exact_matches += 1;
      const price = parsePastIssuePrice(selection.row.issuePrice);
      if (price === null) {
        stats.missing_or_unparseable += 1;
        continue;
      }

      if (applyPastIssuePrice(record, selection.row, now)) {
        stats.extracted += 1;
        changed = true;
        console.log(
          "Extracted NSE final issue price for " + record.issuer_name + ": ₹" + price
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

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;

if (isMain) {
  run().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
