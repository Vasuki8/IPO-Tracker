import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const NSE_HOME = "https://www.nseindia.com/market-data/all-upcoming-issues-ipo";
const UPCOMING_URL = "https://www.nseindia.com/api/all-upcoming-issues?category=ipo";
const CURRENT_URL = "https://www.nseindia.com/api/ipo-current-issue";
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function fail(message) {
  throw new Error(`NSE live sync failed: ${message}`);
}

function normalizeText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function canonicalName(value) {
  return normalizeText(value)
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function slugify(value) {
  return canonicalName(value).replace(/\s+/g, "-");
}

function numeric(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(String(value).replace(/,/g, "").trim());
  return Number.isFinite(parsed) ? parsed : null;
}

export function parseNseDate(value) {
  const text = normalizeText(value);
  if (!text) return null;
  const match = text.match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/);
  if (!match) return null;
  const months = {
    jan: "01", feb: "02", mar: "03", apr: "04", may: "05", jun: "06",
    jul: "07", aug: "08", sep: "09", oct: "10", nov: "11", dec: "12"
  };
  const month = months[match[2].toLowerCase()];
  if (!month) return null;
  return `${match[3]}-${month}-${String(match[1]).padStart(2, "0")}`;
}

export function parseIssuePrice(value) {
  const text = normalizeText(value);
  if (!text) return { kind: "missing", value: null, raw: null };

  const numberPattern = "([0-9][0-9,]*(?:\\.[0-9]+)?)";
  const range = text.match(new RegExp(`(?:Rs\\.?|₹)?\\s*${numberPattern}\\s*(?:to|[-–—])\\s*(?:Rs\\.?|₹)?\\s*${numberPattern}`, "i"));
  if (range) {
    const min = numeric(range[1]);
    const max = numeric(range[2]);
    if (min !== null && max !== null) {
      return { kind: "band", value: { min, max }, raw: text };
    }
  }

  const single = text.match(new RegExp(`(?:Rs\\.?|₹)?\\s*${numberPattern}`, "i"));
  if (single) {
    const price = numeric(single[1]);
    if (price !== null) return { kind: "fixed", value: price, raw: text };
  }

  return { kind: "missing", value: null, raw: text };
}

export function mapNseStatus(value) {
  const status = normalizeText(value).toLowerCase();
  if (status === "active") return "open";
  if (status === "forthcoming" || status === "upcoming") return "upcoming";
  if (status === "closed" || status === "past") return "closed";
  return null;
}

export function mapBoard(series) {
  const normalized = normalizeText(series).toUpperCase();
  if (normalized === "SME") return "SME";
  if (normalized === "EQ") return "Mainboard";
  return null;
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
      lastError = new Error(`HTTP ${response.status} for ${url}`);
    } catch (error) {
      lastError = error;
    }
    if (attempt < attempts) await sleep(attempt * 1200);
  }
  throw lastError;
}

async function fetchNseJson(url, cookie) {
  const response = await fetchWithRetry(url, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "application/json,text/plain,*/*",
      "accept-language": "en-US,en;q=0.9",
      "referer": NSE_HOME,
      "cookie": cookie
    }
  });
  const payload = await response.json();
  if (!Array.isArray(payload)) fail(`${url} did not return an array`);
  return payload;
}

async function fetchLiveFeeds() {
  const landing = await fetchWithRetry(NSE_HOME, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9"
    }
  });
  const cookie = cookieHeader(landing.headers);
  const [upcoming, current] = await Promise.all([
    fetchNseJson(UPCOMING_URL, cookie),
    fetchNseJson(CURRENT_URL, cookie)
  ]);
  return { upcoming, current };
}

export function mergeFeeds(upcoming, current) {
  const merged = new Map();

  function absorb(item, sourceUrl) {
    const symbol = normalizeText(item.symbol).toUpperCase();
    const series = normalizeText(item.series).toUpperCase();
    const companyName = normalizeText(item.companyName);
    if (!symbol || !series || !companyName) return;
    const key = `${series}:${symbol}`;
    const previous = merged.get(key) || {};
    const combined = { ...previous };
    for (const [name, value] of Object.entries(item)) {
      if (value !== null && value !== undefined && value !== "") combined[name] = value;
    }
    combined.__source_url = previous.__source_url || sourceUrl;
    merged.set(key, combined);
  }

  for (const item of upcoming || []) absorb(item, UPCOMING_URL);
  for (const item of current || []) absorb(item, CURRENT_URL);

  return [...merged.values()];
}

function sourceEvidence(issue, now) {
  const symbol = normalizeText(issue.symbol).toUpperCase();
  return {
    url: issue.__source_url || UPCOMING_URL,
    document_type: "NSE IPO Live Feed",
    document_identity: `NSE IPO Live Feed — ${symbol}`,
    publication_date: null,
    page: null,
    collected_at: now
  };
}

function sourceDocument(issue, now) {
  const evidence = sourceEvidence(issue, now);
  return {
    type: evidence.document_type,
    identity: evidence.document_identity,
    url: evidence.url,
    publication_date: null,
    collected_at: now
  };
}

function retainedField(value, sourceValue, issue, now) {
  if (value === null || value === undefined) return undefined;
  const evidence = sourceEvidence(issue, now);
  return {
    value,
    source_value: sourceValue,
    page: null,
    source: {
      url: evidence.url,
      document_type: evidence.document_type,
      document_identity: evidence.document_identity,
      publication_date: null,
      collected_at: now
    }
  };
}

export function buildNewRecoveryRecord(issue, now) {
  const issuerName = normalizeText(issue.companyName);
  const symbol = normalizeText(issue.symbol).toUpperCase();
  const series = normalizeText(issue.series).toUpperCase();
  const board = mapBoard(series);
  const status = mapNseStatus(issue.status);
  const openDate = parseNseDate(issue.issueStartDate);
  const closeDate = parseNseDate(issue.issueEndDate);
  const parsedPrice = parseIssuePrice(issue.priceBand || issue.issuePrice);
  const marketLot = numeric(issue.lotSize);
  const evidence = sourceEvidence(issue, now);

  const record = {
    id: slugify(issuerName),
    issuer_name: issuerName,
    board,
    sector: null,
    status,
    nse_symbol: symbol,
    nse_series: series,
    nse_source: {
      url: evidence.url,
      document_type: evidence.document_type,
      document_identity: evidence.document_identity,
      publication_date: null,
      collected_at: now
    },
    terms: {
      price_band: parsedPrice.kind === "band" ? parsedPrice.value : null,
      market_lot: marketLot,
      minimum_bid_quantity: null,
      open_date: openDate,
      close_date: closeDate
    },
    documents: [sourceDocument(issue, now)],
    first_observed_at: now,
    last_collected_at: now,
    board_evidence: board ? [evidence] : [],
    status_evidence: status ? [evidence] : []
  };

  if (parsedPrice.kind === "fixed") {
    record.issue_price = retainedField(parsedPrice.value, parsedPrice.raw, issue, now);
  }

  return record;
}

function extractExistingSymbol(record) {
  if (record.nse_symbol) return normalizeText(record.nse_symbol).toUpperCase();
  try {
    const url = new URL(record.nse_source?.url);
    const symbol = url.searchParams.get("symbol");
    if (symbol) return symbol.toUpperCase();
  } catch {
    // Keep fallback matching below.
  }
  const identity = normalizeText(record.nse_source?.document_identity);
  const match = identity.match(/[—-]\s*([A-Z0-9&]+)$/);
  return match ? match[1].toUpperCase() : null;
}

function samePriceBand(a, b) {
  return a && b && Number(a.min) === Number(b.min) && Number(a.max) === Number(b.max);
}

function addEvidenceOnce(array, evidence) {
  if (!Array.isArray(array)) return [evidence];
  const exists = array.some((item) =>
    item.url === evidence.url &&
    item.document_identity === evidence.document_identity &&
    item.document_type === evidence.document_type &&
    item.collected_at === evidence.collected_at
  );
  return exists ? array : [...array, evidence];
}

function usesLiveFeedAsTermSource(record) {
  return record.nse_source?.document_type === "NSE IPO Live Feed";
}

function addDocumentOnce(array, document) {
  if (!Array.isArray(array)) return [document];
  const exists = array.some((item) => item.url === document.url && item.identity === document.identity);
  return exists ? array : [...array, document];
}

function enrichExistingRecord(record, issue, now) {
  let changed = false;
  const evidence = sourceEvidence(issue, now);
  const document = sourceDocument(issue, now);
  const liveBoard = mapBoard(issue.series);
  const liveStatus = mapNseStatus(issue.status);
  const parsedPrice = parseIssuePrice(issue.priceBand || issue.issuePrice);
  const liveLot = numeric(issue.lotSize);
  const openDate = parseNseDate(issue.issueStartDate);
  const closeDate = parseNseDate(issue.issueEndDate);

  if (!record.nse_symbol) {
    record.nse_symbol = normalizeText(issue.symbol).toUpperCase();
    changed = true;
  }
  if (!record.nse_series) {
    record.nse_series = normalizeText(issue.series).toUpperCase();
    changed = true;
  }

  if (!record.board && liveBoard) {
    record.board = liveBoard;
    record.board_evidence = addEvidenceOnce(record.board_evidence, evidence);
    changed = true;
  }

  if (liveStatus && record.status !== liveStatus) {
    record.status = liveStatus;
    record.status_evidence = addEvidenceOnce(record.status_evidence, evidence);
    changed = true;
  }

  record.terms ||= {};
  const canFillLiveTerms = usesLiveFeedAsTermSource(record);

  if (canFillLiveTerms && !record.terms.price_band && parsedPrice.kind === "band") {
    record.terms.price_band = parsedPrice.value;
    changed = true;
  } else if (record.terms.price_band && parsedPrice.kind === "band" && !samePriceBand(record.terms.price_band, parsedPrice.value)) {
    console.warn(`Price-band mismatch retained without overwrite for ${record.issuer_name}: recovery=${JSON.stringify(record.terms.price_band)} live=${JSON.stringify(parsedPrice.value)}`);
  }

  if (canFillLiveTerms && (record.terms.market_lot === null || record.terms.market_lot === undefined) && liveLot !== null) {
    record.terms.market_lot = liveLot;
    changed = true;
  }
  if (canFillLiveTerms && !record.terms.open_date && openDate) {
    record.terms.open_date = openDate;
    changed = true;
  }
  if (canFillLiveTerms && !record.terms.close_date && closeDate) {
    record.terms.close_date = closeDate;
    changed = true;
  }
  if (!record.issue_price && parsedPrice.kind === "fixed") {
    record.issue_price = retainedField(parsedPrice.value, parsedPrice.raw, issue, now);
    changed = true;
  }

  const nextDocuments = addDocumentOnce(record.documents, document);
  if (nextDocuments !== record.documents) {
    record.documents = nextDocuments;
    changed = true;
  }

  if (changed) record.last_collected_at = now;
  return changed;
}

function recoveryFileForYear(year) {
  return path.join(RECOVERY_ROOT, String(year), "nse-issue-information.json");
}

function readOrCreateManifest(year, now) {
  const file = recoveryFileForYear(year);
  if (fs.existsSync(file)) {
    return { file, manifest: JSON.parse(fs.readFileSync(file, "utf8")), existed: true };
  }
  return {
    file,
    existed: false,
    manifest: {
      source_family: "Official NSE / SEBI / issuer offer-document evidence",
      collection_started_at: now,
      generated_at: now,
      records: []
    }
  };
}

function issueYear(issue) {
  const parsed = parseNseDate(issue.issueStartDate);
  if (parsed) return Number(parsed.slice(0, 4));
  return new Date().getUTCFullYear();
}

function readFixture(fixturePath) {
  const payload = JSON.parse(fs.readFileSync(path.resolve(fixturePath), "utf8"));
  return {
    upcoming: Array.isArray(payload.upcoming) ? payload.upcoming : [],
    current: Array.isArray(payload.current) ? payload.current : []
  };
}

export async function runSync({ fixturePath = null, dryRun = false, now = new Date().toISOString() } = {}) {
  const feeds = fixturePath ? readFixture(fixturePath) : await fetchLiveFeeds();
  const issues = mergeFeeds(feeds.upcoming, feeds.current);
  if (issues.length === 0) fail("official NSE feeds returned zero IPO issues");

  const grouped = new Map();
  for (const issue of issues) {
    const year = issueYear(issue);
    if (!grouped.has(year)) grouped.set(year, []);
    grouped.get(year).push(issue);
  }

  const summary = { discovered: issues.length, added: 0, enriched: 0, years: [] };

  for (const [year, yearIssues] of [...grouped.entries()].sort(([a], [b]) => a - b)) {
    const { file, manifest, existed } = readOrCreateManifest(year, now);
    if (!Array.isArray(manifest.records)) fail(`${file}: records must be an array`);

    const bySymbol = new Map();
    const byName = new Map();
    for (const record of manifest.records) {
      const symbol = extractExistingSymbol(record);
      if (symbol) bySymbol.set(symbol, record);
      byName.set(canonicalName(record.issuer_name), record);
    }

    let manifestChanged = false;
    for (const issue of yearIssues) {
      const symbol = normalizeText(issue.symbol).toUpperCase();
      const nameKey = canonicalName(issue.companyName);
      const existing = bySymbol.get(symbol) || byName.get(nameKey);

      if (existing) {
        if (enrichExistingRecord(existing, issue, now)) {
          manifestChanged = true;
          summary.enriched += 1;
        }
        continue;
      }

      const record = buildNewRecoveryRecord(issue, now);
      manifest.records.push(record);
      bySymbol.set(symbol, record);
      byName.set(nameKey, record);
      manifestChanged = true;
      summary.added += 1;
    }

    if (manifestChanged || !existed) {
      manifest.generated_at = now;
      manifest.records.sort((a, b) => a.issuer_name.localeCompare(b.issuer_name));
      if (!dryRun) {
        fs.mkdirSync(path.dirname(file), { recursive: true });
        fs.writeFileSync(file, `${JSON.stringify(manifest, null, 2)}\n`);
      }
    }

    summary.years.push({ year, issues: yearIssues.length, changed: manifestChanged || !existed });
  }

  return summary;
}

async function main() {
  const fixtureArg = process.argv.find((arg) => arg.startsWith("--fixture="));
  const fixturePath = fixtureArg ? fixtureArg.slice("--fixture=".length) : null;
  const dryRun = process.argv.includes("--dry-run");
  const summary = await runSync({ fixturePath, dryRun });
  console.log(JSON.stringify(summary, null, 2));
}

const invokedPath = process.argv[1] ? pathToFileURL(path.resolve(process.argv[1])).href : null;
if (invokedPath === import.meta.url) {
  main().catch((error) => {
    console.error(error.stack || error.message || error);
    process.exit(1);
  });
}
