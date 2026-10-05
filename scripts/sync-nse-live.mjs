import { liveIssueIneligibility, normalizeSeries } from "./ipo-instrument-policy.mjs";
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
    if (liveIssueIneligibility(item)) return;
    const symbol = normalizeText(item.symbol).toUpperCase();
    const series = normalizeText(item.series).toUpperCase();
    const companyName = normalizeText(item.companyName);
    if (!symbol || !series || !companyName) return;
    const key = `${series}:${symbol}`;
    const previous = merged.get(key) || {};
    if (previous.companyName && canonicalName(previous.companyName) !== canonicalName(companyName)) {
      fail("issuer_identity_conflict_between_feeds: " + JSON.stringify({previous, incoming:{...item,__source_url:sourceUrl}}));
    }

    const combined = { ...previous };
    combined.__field_sources = { ...(previous.__field_sources || {}) };
    combined.__field_observations = Object.fromEntries(
      Object.entries(previous.__field_observations || {}).map(([name, items]) => [name, [...items]])
    );
    combined.__field_conflicts = Object.fromEntries(
      Object.entries(previous.__field_conflicts || {}).map(([name, items]) => [name, [...items]])
    );
    combined.__source_urls = [...(previous.__source_urls || [])];
    if (!combined.__source_urls.includes(sourceUrl)) combined.__source_urls.push(sourceUrl);

    for (const [name, value] of Object.entries(item)) {
      if (value === null || value === undefined || value === "") continue;
      const priorValue = combined[name];
      const priorSource = combined.__field_sources[name];
      const observations = combined.__field_observations[name] || [];
      if (!observations.some((entry) => entry.source_url === sourceUrl && JSON.stringify(entry.value) === JSON.stringify(value))) {
        observations.push({ value, source_url: sourceUrl });
      }
      combined.__field_observations[name] = observations;

      if (priorSource && priorSource !== sourceUrl &&
          priorValue !== null && priorValue !== undefined && priorValue !== "" &&
          JSON.stringify(priorValue) !== JSON.stringify(value)) {
        const conflicts = combined.__field_conflicts[name] || [];
        for (const entry of [
          { value: priorValue, source_url: priorSource },
          { value, source_url: sourceUrl }
        ]) {
          if (!conflicts.some((other) => other.source_url === entry.source_url &&
              JSON.stringify(other.value) === JSON.stringify(entry.value))) conflicts.push(entry);
        }
        combined.__field_conflicts[name] = conflicts;
      }

      combined[name] = value;
      combined.__field_sources[name] = sourceUrl;
    }

    // Current-issue observations are absorbed after upcoming observations, so
    // the record-level pointer follows the endpoint that supplied the winning
    // merged values. Per-field provenance is retained separately above.
    combined.__source_url = sourceUrl;
    merged.set(key, combined);
  }

  for (const item of upcoming || []) absorb(item, UPCOMING_URL);
  for (const item of current || []) absorb(item, CURRENT_URL);

  return [...merged.values()];
}

function sourceUrlForField(issue, fieldName = null) {
  if (fieldName && issue.__field_sources?.[fieldName]) return issue.__field_sources[fieldName];
  return issue.__source_url || UPCOMING_URL;
}

function sourceEvidence(issue, now, fieldName = null, sourceUrl = null) {
  const symbol = normalizeText(issue.symbol).toUpperCase();
  return {
    url: sourceUrl || sourceUrlForField(issue, fieldName),
    document_type: "NSE IPO Live Feed",
    document_identity: `NSE IPO Live Feed — ${symbol}`,
    publication_date: null,
    page: null,
    collected_at: now
  };
}

function sourceDocument(issue, now, sourceUrl = null) {
  const evidence = sourceEvidence(issue, now, null, sourceUrl);
  return {
    type: evidence.document_type,
    identity: evidence.document_identity,
    url: evidence.url,
    publication_date: null,
    collected_at: now
  };
}

function sourceDocuments(issue, now) {
  const urls = [...(issue.__source_urls || [])];
  if (urls.length === 0) urls.push(sourceUrlForField(issue));
  return urls.map((url) => sourceDocument(issue, now, url));
}

function retainedField(value, sourceValue, issue, now, {
  fieldName = null,
  sourceUrl = null,
  status = "verified",
  corrections = [],
  additionalSources = []
} = {}) {
  if (value === null || value === undefined) return undefined;
  const evidence = sourceEvidence(issue, now, fieldName, sourceUrl);
  const field = {
    value,
    source_value: sourceValue,
    page: null,
    status,
    source: {
      url: evidence.url,
      document_type: evidence.document_type,
      document_identity: evidence.document_identity,
      publication_date: null,
      collected_at: now
    },
    corrections
  };
  if (additionalSources.length) field.additional_sources = additionalSources;
  return field;
}

function retainedFieldEvidence(field, fallbackSource = null) {
  const source = field?.source || fallbackSource;
  if (!source?.url) return [];
  return [{
    url: source.url,
    document_type: source.document_type ?? "NSE IPO Live Feed",
    document_identity: source.document_identity ?? null,
    publication_date: source.publication_date ?? null,
    page: field?.page ?? null,
    collected_at: source.collected_at ?? null
  }];
}

function addAdditionalSourceOnce(field, evidence) {
  const existing = Array.isArray(field.additional_sources) ? field.additional_sources : [];
  if (existing.some((item) => item.url === evidence.url &&
      item.document_identity === evidence.document_identity &&
      item.document_type === evidence.document_type)) return false;
  field.additional_sources = [...existing, evidence];
  return true;
}

function liveFieldConflict(issue, fieldName, parser, preferredValue, now) {
  const observations = issue.__field_conflicts?.[fieldName] || [];
  if (observations.length < 2) return null;
  const parsed = observations.map((entry) => ({
    value: parser(entry.value),
    source_url: entry.source_url
  })).filter((entry) => entry.value !== null && entry.value !== undefined);
  const competing = parsed.filter((entry) => JSON.stringify(entry.value) !== JSON.stringify(preferredValue));
  if (competing.length === 0) return null;
  const preferredSource = sourceUrlForField(issue, fieldName);
  return {
    status: "conflict",
    additionalSources: competing.map((entry) => sourceEvidence(issue, now, fieldName, entry.source_url)),
    correction: {
      kind: "official_live_feed_disagreement",
      status: "unresolved",
      note: "Official NSE live endpoints reported different values in the same collection; the current merged candidate is retained for review.",
      preferred_candidate: { value: preferredValue },
      competing_observations: competing.map((entry) => ({ value: entry.value }))
    },
    preferredSource
  };
}

function liveRetainedField(value, sourceValue, issue, now, fieldName, parser) {
  const conflict = liveFieldConflict(issue, fieldName, parser, value, now);
  return retainedField(value, sourceValue, issue, now, {
    fieldName,
    sourceUrl: conflict?.preferredSource || null,
    status: conflict?.status || "verified",
    corrections: conflict ? [conflict.correction] : [],
    additionalSources: conflict?.additionalSources || []
  });
}

function fieldUsesLiveSource(record, fieldName) {
  if (Object.hasOwn(record, fieldName)) {
    return record[fieldName]?.source?.document_type === "NSE IPO Live Feed";
  }
  return usesLiveFeedAsTermSource(record);
}

function updateLiveTerm(record, {
  fieldName,
  termName,
  value,
  sourceValue,
  issue,
  now,
  sourceFieldName,
  parser
}) {
  if (value === null || value === undefined || !fieldUsesLiveSource(record, fieldName)) return false;
  record.terms ||= {};
  const existingField = Object.hasOwn(record, fieldName) ? record[fieldName] : null;
  const currentValue = existingField?.value ?? (termName ? record.terms?.[termName] : null) ?? null;
  const nextField = liveRetainedField(value, sourceValue, issue, now, sourceFieldName, parser);

  if (currentValue === null || currentValue === undefined) {
    record[fieldName] = nextField;
    if (termName) record.terms[termName] = value;
    return true;
  }

  if (JSON.stringify(currentValue) === JSON.stringify(value)) {
    if (!existingField) {
      record[fieldName] = nextField;
      if (termName) record.terms[termName] = value;
      return true;
    }
    const incomingEvidence = sourceEvidence(issue, now, sourceFieldName);
    return addAdditionalSourceOnce(existingField, incomingEvidence);
  }

  const previousEvidence = retainedFieldEvidence(existingField, record.nse_source);
  const previousCorrections = Array.isArray(existingField?.corrections) ? existingField.corrections : [];
  nextField.corrections = [
    ...previousCorrections,
    {
      corrected_at: now,
      previous_value: currentValue,
      previous_status: existingField?.status ?? "verified",
      reason: "Later official NSE live-feed observation changed this field; the previous observation is retained.",
      replacement_value: value,
      previous_evidence: previousEvidence,
      evidence: [sourceEvidence(issue, now, sourceFieldName)]
    },
    ...(nextField.corrections || [])
  ];
  for (const evidence of previousEvidence) addAdditionalSourceOnce(nextField, evidence);
  record[fieldName] = nextField;
  if (termName) record.terms[termName] = value;
  return true;
}

export function buildNewRecoveryRecord(issue, now) {
  const reason = liveIssueIneligibility(issue);
  if (reason) fail("ineligible IPO instrument: " + reason);
  const issuerName = normalizeText(issue.companyName);
  const symbol = normalizeText(issue.symbol).toUpperCase();
  const series = normalizeText(issue.series).toUpperCase();
  const board = mapBoard(series);
  const status = mapNseStatus(issue.status);
  const openDate = parseNseDate(issue.issueStartDate);
  const closeDate = parseNseDate(issue.issueEndDate);
  const priceFieldName = normalizeText(issue.priceBand) ? "priceBand" : "issuePrice";
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
    documents: sourceDocuments(issue, now),
    first_observed_at: now,
    last_collected_at: now,
    board_evidence: board ? [sourceEvidence(issue, now, "series")] : [],
    status_evidence: status ? [sourceEvidence(issue, now, "status")] : []
  };

  if (parsedPrice.kind === "band") {
    record.price_band = liveRetainedField(
      parsedPrice.value, parsedPrice.raw, issue, now, priceFieldName,
      (raw) => {
        const parsed = parseIssuePrice(raw);
        return parsed.kind === "band" ? parsed.value : null;
      }
    );
  }
  if (marketLot !== null) {
    record.market_lot = liveRetainedField(marketLot, issue.lotSize, issue, now, "lotSize", numeric);
  }
  if (openDate) {
    record.open_date = liveRetainedField(openDate, issue.issueStartDate, issue, now, "issueStartDate", parseNseDate);
  }
  if (closeDate) {
    record.close_date = liveRetainedField(closeDate, issue.issueEndDate, issue, now, "issueEndDate", parseNseDate);
  }
  if (parsedPrice.kind === "fixed") {
    record.issue_price = liveRetainedField(
      parsedPrice.value, parsedPrice.raw, issue, now, priceFieldName,
      (raw) => {
        const parsed = parseIssuePrice(raw);
        return parsed.kind === "fixed" ? parsed.value : null;
      }
    );
  }

  return record;
}

function retainedIdentity(record) {
  const symbols = new Set([normalizeText(record.nse_symbol).toUpperCase()].filter(Boolean));
  const series = new Set([normalizeSeries(record.nse_series)].filter(Boolean));
  try {
    const url = new URL(record.nse_source?.url);
    if (["www.nseindia.com", "nseindia.com"].includes(url.hostname)) {
      const symbol = normalizeText(url.searchParams.get("symbol")).toUpperCase();
      const sourceSeries = normalizeSeries(url.searchParams.get("series"));
      if (symbol) symbols.add(symbol);
      if (sourceSeries) series.add(sourceSeries);
    }
  } catch { /* Missing source identifiers are not invented. */ }
  const identity = normalizeText(record.nse_source?.document_identity);
  const match = identity.match(/^NSE (?:IPO Live Feed|Issue Information(?: API)?|Public Past Issues) [—-] ([A-Z0-9&-]+)$/);
  if (match) symbols.add(match[1]);
  return {symbols:[...symbols],series:[...series]};
}

function assertCompatibleIdentity(record, issue) {
  const retained = retainedIdentity(record);
  const symbol = normalizeText(issue.symbol).toUpperCase();
  const series = normalizeSeries(issue.series);
  if (!canonicalName(record.issuer_name) || canonicalName(record.issuer_name) !== canonicalName(issue.companyName) ||
      retained.symbols.some(value => value !== symbol) || retained.series.some(value => value !== series) ||
      (record.board && record.board !== mapBoard(series))) {
    fail("issuer_identity_conflict: " + JSON.stringify({
      existing:{id:record.id,issuer_name:record.issuer_name,board:record.board,...retained,source:record.nse_source}, incoming:issue
    }));
  }
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

export function enrichExistingRecord(record, issue, now) {
  const reason = liveIssueIneligibility(issue);
  if (reason) fail("ineligible IPO instrument: " + reason);
  assertCompatibleIdentity(record, issue);
  let changed = false;
  const evidence = sourceEvidence(issue, now);
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
    if (record.status !== "listed") {
      record.status = liveStatus;
      changed = true;
    }
    const nextStatusEvidence = addEvidenceOnce(record.status_evidence, evidence);
    if (nextStatusEvidence !== record.status_evidence) {
      record.status_evidence = nextStatusEvidence;
      changed = true;
    }
  }

  record.terms ||= {};
  const priceFieldName = normalizeText(issue.priceBand) ? "priceBand" : "issuePrice";

  if (parsedPrice.kind === "band" && updateLiveTerm(record, {
    fieldName: "price_band",
    termName: "price_band",
    value: parsedPrice.value,
    sourceValue: parsedPrice.raw,
    issue,
    now,
    sourceFieldName: priceFieldName,
    parser: (raw) => {
      const parsed = parseIssuePrice(raw);
      return parsed.kind === "band" ? parsed.value : null;
    }
  })) changed = true;

  if (liveLot !== null && updateLiveTerm(record, {
    fieldName: "market_lot",
    termName: "market_lot",
    value: liveLot,
    sourceValue: issue.lotSize,
    issue,
    now,
    sourceFieldName: "lotSize",
    parser: numeric
  })) changed = true;

  if (openDate && updateLiveTerm(record, {
    fieldName: "open_date",
    termName: "open_date",
    value: openDate,
    sourceValue: issue.issueStartDate,
    issue,
    now,
    sourceFieldName: "issueStartDate",
    parser: parseNseDate
  })) changed = true;

  if (closeDate && updateLiveTerm(record, {
    fieldName: "close_date",
    termName: "close_date",
    value: closeDate,
    sourceValue: issue.issueEndDate,
    issue,
    now,
    sourceFieldName: "issueEndDate",
    parser: parseNseDate
  })) changed = true;

  if (parsedPrice.kind === "fixed" && updateLiveTerm(record, {
    fieldName: "issue_price",
    termName: null,
    value: parsedPrice.value,
    sourceValue: parsedPrice.raw,
    issue,
    now,
    sourceFieldName: priceFieldName,
    parser: (raw) => {
      const parsed = parseIssuePrice(raw);
      return parsed.kind === "fixed" ? parsed.value : null;
    }
  })) changed = true;

  for (const nextDocument of sourceDocuments(issue, now)) {
    const nextDocuments = addDocumentOnce(record.documents, nextDocument);
    if (nextDocuments !== record.documents) {
      record.documents = nextDocuments;
      changed = true;
    }
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
  const excluded = [
    ...feeds.upcoming.map(issue => ({issue,url:UPCOMING_URL})),
    ...feeds.current.map(issue => ({issue,url:CURRENT_URL}))
  ].filter(item => liveIssueIneligibility(item.issue)).map(item => ({
    ...item, reason:liveIssueIneligibility(item.issue), collected_at:now
  }));
  const issues = mergeFeeds(feeds.upcoming, feeds.current);
  if (issues.length === 0 && excluded.length === 0) fail("official NSE feeds returned zero IPO issues");

  // Preflight every identity before changing any manifest. Both name and symbol
  // must agree; lookup precedence or Map overwrites may not resolve a conflict.
  const manifests = new Map();
  const registry = [];
  const register = (year, record) => registry.push({year,record});
  if (fs.existsSync(RECOVERY_ROOT)) {
    for (const dir of fs.readdirSync(RECOVERY_ROOT,{withFileTypes:true})) {
      if (!dir.isDirectory() || !/^20\d{2}$/.test(dir.name)) continue;
      const year = Number(dir.name), entry = readOrCreateManifest(year,now);
      if (!entry.existed) continue;
      if (!Array.isArray(entry.manifest.records)) fail(`${entry.file}: records must be an array`);
      manifests.set(year,entry);
      for (const record of entry.manifest.records) register(year,record);
    }
  }
  const plans = [];
  for (const issue of issues) {
    const year = issueYear(issue), symbol = normalizeText(issue.symbol).toUpperCase(), name = canonicalName(issue.companyName);
    const hits = registry.filter(({record}) => retainedIdentity(record).symbols.includes(symbol) || canonicalName(record.issuer_name) === name);
    if (hits.length > 1) fail("ambiguous_issuer_identity: " + JSON.stringify({incoming:issue, candidates:hits.map(({year,record})=>({year,id:record.id,issuer_name:record.issuer_name}))}));
    if (hits.length === 1) {
      assertCompatibleIdentity(hits[0].record,issue);
      if (hits[0].year !== year) fail("cross_year_identity_requires_review: " + JSON.stringify({incoming:issue,existing_year:hits[0].year,id:hits[0].record.id}));
      plans.push({year,issue,existing:hits[0].record});
    } else {
      const created = buildNewRecoveryRecord(issue,now);
      plans.push({year,issue,created});
      register(year,created);
    }
  }

  const summary = {discovered:issues.length,added:0,enriched:0,excluded,years:[]};
  const changedYears = new Set();
  for (const {year,issue,existing,created} of plans) {
    if (!manifests.has(year)) manifests.set(year,readOrCreateManifest(year,now));
    const {manifest} = manifests.get(year);
    if (existing) {
      if (enrichExistingRecord(existing,issue,now)) {changedYears.add(year);summary.enriched += 1;}
    } else {
      manifest.records.push(created);
      changedYears.add(year);summary.added += 1;
    }
  }
  for (const year of [...new Set(plans.map(plan=>plan.year))].sort((a,b)=>a-b)) {
    const {file,manifest} = manifests.get(year), changed = changedYears.has(year);
    if (changed) {
      manifest.generated_at = now;
      manifest.records.sort((a,b)=>a.issuer_name.localeCompare(b.issuer_name));
      if (!dryRun) {
        fs.mkdirSync(path.dirname(file),{recursive:true});
        fs.writeFileSync(file,`${JSON.stringify(manifest,null,2)}\n`);
      }
    }
    summary.years.push({year,issues:plans.filter(plan=>plan.year===year).length,changed});
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
