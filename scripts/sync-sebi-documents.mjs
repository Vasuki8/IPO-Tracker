import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const HISTORICAL_SEARCH_STATE_PATH = path.join(ROOT, "ops", "sebi-historical-search.json");

export const SEBI_RHP_LIST_URL =
  "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=11&ssid=15";
export const SEBI_FINAL_LIST_URL =
  "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=12&ssid=15";
export const SEBI_ALL_FILINGS_URL =
  "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes&sid=3";
export const SEBI_PUBLIC_ISSUES_URL =
  "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=15";
export const SEBI_SEARCH_URL =
  "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes";
export const MAX_TARGETED_SEARCHES = 12;
export const MAX_HISTORICAL_TARGETED_SEARCHES = 12;

const USER_AGENT =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function fail(message) {
  throw new Error(`SEBI document sync failed: ${message}`);
}

function decodeHtml(value) {
  return String(value ?? "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&#x2F;/gi, "/")
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)));
}

function stripTags(value) {
  return decodeHtml(String(value ?? "").replace(/<[^>]*>/g, " "))
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

export function canonicalIssuer(value) {
  return normalizeText(value)
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/\bltd\.?\b/g, " limited ")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\blimited\s*$/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function issuerVariants(value) {
  const original = normalizeText(value);
  const variants = new Set([canonicalIssuer(original)]);
  if (/\(\s*india\s*\)/i.test(original)) {
    variants.add(canonicalIssuer(original.replace(/\(\s*india\s*\)/gi, " ")));
  }
  return [...variants].filter(Boolean);
}

export function parseSebiDate(value) {
  const text = normalizeText(value);
  const match = text.match(
    /\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(\d{4})\b/i
  );
  if (!match) return null;
  const months = {
    jan: "01", feb: "02", mar: "03", apr: "04", may: "05", jun: "06",
    jul: "07", aug: "08", sep: "09", oct: "10", nov: "11", dec: "12"
  };
  return `${match[3]}-${months[match[1].toLowerCase()]}-${String(match[2]).padStart(2, "0")}`;
}

export function cacheBustedListingUrl(url, token) {
  const parsed = new URL(url);
  parsed.searchParams.set("_fresh", String(token));
  return parsed.href;
}

function absoluteUrl(href, baseUrl) {
  try {
    return new URL(decodeHtml(href), baseUrl).href;
  } catch {
    return null;
  }
}

function classifyListingTitle(title) {
  const value = normalizeText(title);
  if (!value) return null;
  if (/\b(?:DRHP|UDRHP)\b|addendum|corrigendum/i.test(value)) return null;
  if (/\bRHP\b|red herring prospectus/i.test(value)) return "rhp";
  if (/\bprospectus\b/i.test(value) && !/abridged/i.test(value)) return "final";
  return null;
}

export function issuerFromListingTitle(title, kind) {
  const value = normalizeText(title).replace(/[–—]/g, "-");
  if (kind === "rhp") {
    return value
      .replace(/\s*-\s*RHP\b[\s\S]*$/i, "")
      .replace(/\s*-\s*Red Herring Prospectus\b[\s\S]*$/i, "")
      .trim();
  }
  if (kind === "final") {
    return value
      .replace(/\s*-\s*(?:Final\s+)?Prospectus\b[\s\S]*$/i, "")
      .trim();
  }
  return value;
}

function nearestDateBefore(html, index) {
  const window = html.slice(Math.max(0, index - 1400), index);
  const matches = [
    ...window.matchAll(
      /\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b/gi
    )
  ];
  return matches.length ? parseSebiDate(matches.at(-1)[0]) : null;
}

function filingUrlFromAnchorAttributes(attributes, baseUrl) {
  const hrefMatch = attributes.match(/\bhref\s*=\s*(["'])([^"']+)\1/i);
  if (hrefMatch) {
    const href = absoluteUrl(hrefMatch[2], baseUrl);
    if (href && /sebi\.gov\.in\/filings\/public-issues\//i.test(href)) return href;
  }

  const embedded = attributes.match(
    /(?:https?:\\?\/\\?\/www\.sebi\.gov\.in)?\\?\/filings\\?\/public-issues\\?\/[^"'<>\s)]+\.html/i
  );
  if (!embedded) return null;
  return absoluteUrl(embedded[0].replace(/\\\//g, "/"), baseUrl);
}

function kindFromFilingUrl(url) {
  const path = decodeURIComponent(new URL(url).pathname).toLowerCase();
  if (/\b(?:drhp|udrhp)\b|addendum|corrigendum/.test(path)) return null;
  if (/-rhp_\d+\.html$/.test(path)) return "rhp";
  if (/-prospectus_\d+\.html$/.test(path)) return "final";
  return null;
}

export function issuerFromFilingUrl(url, kind) {
  const pathname = decodeURIComponent(new URL(url).pathname);
  const file = pathname.split("/").at(-1) || "";
  let slug = file.replace(/_\d+\.html$/i, "");
  if (kind === "rhp") slug = slug.replace(/-rhp$/i, "");
  if (kind === "final") slug = slug.replace(/-prospectus$/i, "");
  return slug.replace(/-/g, " ").replace(/\s+/g, " ").trim();
}

function pushListingEntry(entries, seen, html, index, href, title, kind) {
  if (!href || !kind) return;
  const issuerName = title ? issuerFromListingTitle(title, kind) : issuerFromFilingUrl(href, kind);
  if (!issuerName) return;
  const key = `${kind}|${href}`;
  if (seen.has(key)) return;
  seen.add(key);
  entries.push({
    kind,
    issuer_name: issuerName,
    title: title || `SEBI ${kind === "rhp" ? "RHP filing" : "Prospectus filing"} — ${issuerName}`,
    url: href,
    publication_date: nearestDateBefore(html, index)
  });
}

export function parseSebiListingHtml(html, expectedKind, baseUrl) {
  const entries = [];
  const seen = new Set();
  const anchorPattern = /<a\b([^>]*)>([\s\S]*?)<\/a>/gi;

  for (const match of html.matchAll(anchorPattern)) {
    const attributes = match[1] || "";
    const href = filingUrlFromAnchorAttributes(attributes, baseUrl);
    if (!href) continue;

    const title = stripTags(match[2]);
    const titleKind = classifyListingTitle(title);
    const urlKind = kindFromFilingUrl(href);
    const kind = titleKind || urlKind;
    if (!kind || (expectedKind && kind !== expectedKind)) continue;

    // SEBI's live RHP list can emit malformed/nested markup where an RHP
    // filing URL is paired with the adjacent Abridged Prospectus anchor text.
    // In that case the visible title is not safe for issuer identity. Trust
    // the filing URL slug instead; deterministic record matching remains
    // unchanged.
    const identityTitle = titleKind === kind ? title : "";
    pushListingEntry(entries, seen, html, match.index ?? 0, href, identityTitle, kind);
  }

  const rawFilingPattern =
    /(?:https?:\\?\/\\?\/www\.sebi\.gov\.in)?\\?\/filings\\?\/public-issues\\?\/[^"'<>\s)]+\.html/gi;

  for (const match of html.matchAll(rawFilingPattern)) {
    const href = absoluteUrl(match[0].replace(/\\\//g, "/"), baseUrl);
    if (!href || !/sebi\.gov\.in\/filings\/public-issues\//i.test(href)) continue;
    const kind = kindFromFilingUrl(href);
    if (!kind || (expectedKind && kind !== expectedKind)) continue;

    // Raw-URL fallback intentionally derives issuer identity from the official
    // filing URL slug. Nearby table text can include titles from adjacent rows
    // and is therefore not safe for identity reconstruction.
    pushListingEntry(entries, seen, html, match.index ?? 0, href, "", kind);
  }

  return entries;
}

export function directSebiProspectusPdf(value, baseUrl) {
  if (!value) return null;

  const decoded = decodeHtml(String(value)).replace(/\\\//g, "/");
  const candidates = [decoded];

  try {
    const outer = new URL(decoded, baseUrl);
    const file = outer.searchParams.get("file");
    if (file) candidates.push(file);
    candidates.push(outer.href);
  } catch {
    // Keep trying encoded/raw candidates below.
  }

  for (const candidateValue of [...candidates]) {
    try {
      const once = decodeURIComponent(candidateValue);
      if (once !== candidateValue) candidates.push(once);
    } catch {
      // Ignore malformed percent-encoding.
    }
  }

  for (const candidate of candidates) {
    let parsed;
    try {
      parsed = new URL(candidate, baseUrl);
    } catch {
      continue;
    }

    if (parsed.protocol !== "https:") continue;
    if (!/^(?:www\.)?sebi\.gov\.in$/i.test(parsed.hostname)) continue;
    if (!/^\/sebi_data\/attachdocs\//i.test(parsed.pathname)) continue;
    if (!/\.pdf$/i.test(parsed.pathname)) continue;
    return parsed.href;
  }

  return null;
}

export function parseProspectusPdfLinks(html, baseUrl) {
  const docs = [];
  const seen = new Set();

  const add = (candidate) => {
    const url = directSebiProspectusPdf(candidate, baseUrl);
    if (!url || seen.has(url)) return;
    seen.add(url);
    docs.push({
      type: "SEBI Prospectus PDF",
      identity: "SEBI Prospectus PDF",
      url
    });
  };

  for (const match of html.matchAll(/\bhref\s*=\s*(["'])([^"']+)\1/gi)) {
    add(match[2]);
  }

  for (const match of html.matchAll(
    /(?:https?:\/\/www\.sebi\.gov\.in\/web\/\?file=)?https?%3A%2F%2Fwww\.sebi\.gov\.in%2Fsebi_data%2Fattachdocs%2F[^"'<>\s]+?\.pdf/gi
  )) {
    add(match[0]);
  }

  for (const match of html.matchAll(
    /(?:https?:\/\/www\.sebi\.gov\.in)?\/sebi_data\/attachdocs\/[^"'<>\s]+?\.pdf/gi
  )) {
    add(match[0]);
  }

  return docs;
}

export function parseOtherDocumentPdfLinks(html, baseUrl, identity = "SEBI Other Document") {
  return parseProspectusPdfLinks(html, baseUrl).map((doc) => ({
    ...doc,
    type: "SEBI Other Document PDF",
    identity: `${identity} — PDF`
  }));
}

export function parseAbridgedProspectusLinks(html, baseUrl) {
  const docs = [];
  const seen = new Set();
  const anchorPattern =
    /<a\b[^>]*href\s*=\s*(["'])([^"']+)\1[^>]*>([\s\S]*?)<\/a>/gi;

  for (const match of html.matchAll(anchorPattern)) {
    const title = stripTags(match[3]);
    if (!/abridged prospectus/i.test(title)) continue;
    const href = absoluteUrl(match[2], baseUrl);
    if (!href || !/sebi\.gov\.in\/sebi_data\/commondocs\//i.test(href)) continue;
    if (seen.has(href)) continue;
    seen.add(href);
    docs.push({
      type: "SEBI Abridged Prospectus",
      identity: title,
      url: href
    });
  }
  return docs;
}

export function matchIssuerRecord(records, issuerName) {
  const sourceVariants = new Set(issuerVariants(issuerName));
  const matches = records.filter(({ record }) =>
    issuerVariants(record.issuer_name).some((variant) => sourceVariants.has(variant))
  );
  return matches.length === 1 ? matches[0] : null;
}

export function hasSebiDocument(record) {
  return (record.documents || []).some((doc) =>
    /^SEBI\s/i.test(normalizeText(doc.type)) ||
    /sebi\.gov\.in/i.test(String(doc.url || ""))
  );
}

export function isLiveFeedRecord(record) {
  return record?.nse_source?.document_type === "NSE IPO Live Feed" ||
    /\/api\/(?:all-upcoming-issues|ipo-current-issue)/i.test(String(record?.nse_source?.url || ""));
}

export function targetedSearchCandidates(records, maxSearches = MAX_TARGETED_SEARCHES) {
  return records
    .filter(({ record }) => isLiveFeedRecord(record) && !hasSebiDocument(record))
    .sort((a, b) => String(b.record.first_observed_at || "").localeCompare(String(a.record.first_observed_at || "")))
    .slice(0, maxSearches);
}

export function historicalSearchKey(record) {
  const year = String(record?.listing_date?.value || "").slice(0, 4);
  return `${year || "unknown"}|${record?.id || canonicalIssuer(record?.issuer_name)}`;
}

function retryDelayMs(status) {
  return status === "error" ? 24 * 60 * 60 * 1000 : 30 * 24 * 60 * 60 * 1000;
}

export function historicalSearchCandidates(
  records,
  state = { issuers: {} },
  now = new Date().toISOString(),
  maxSearches = MAX_HISTORICAL_TARGETED_SEARCHES
) {
  const nowMs = Date.parse(now);
  return records
    .filter(({ record }) => {
      if (isLiveFeedRecord(record) || hasSebiDocument(record)) return false;
      if (!/^20\d{2}-\d{2}-\d{2}$/.test(String(record?.listing_date?.value || ""))) return false;
      const item = state?.issuers?.[historicalSearchKey(record)];
      if (!item?.last_attempted_at) return true;
      if (item.status === "matched") return false;
      const attemptedMs = Date.parse(item.last_attempted_at);
      if (!Number.isFinite(nowMs) || !Number.isFinite(attemptedMs)) return true;
      return nowMs - attemptedMs >= retryDelayMs(item.status);
    })
    .sort((a, b) => {
      const dateOrder = String(b.record.listing_date?.value || "").localeCompare(String(a.record.listing_date?.value || ""));
      return dateOrder || a.record.issuer_name.localeCompare(b.record.issuer_name);
    })
    .slice(0, maxSearches);
}

function readHistoricalSearchState() {
  if (!fs.existsSync(HISTORICAL_SEARCH_STATE_PATH)) {
    return { schema_version: "1.0.0", issuers: {}, changed: false };
  }
  const state = JSON.parse(fs.readFileSync(HISTORICAL_SEARCH_STATE_PATH, "utf8"));
  state.issuers ||= {};
  state.changed = false;
  return state;
}

function writeHistoricalSearchState(state) {
  if (!state.changed) return;
  const output = { schema_version: "1.0.0", issuers: state.issuers };
  fs.mkdirSync(path.dirname(HISTORICAL_SEARCH_STATE_PATH), { recursive: true });
  fs.writeFileSync(HISTORICAL_SEARCH_STATE_PATH, JSON.stringify(output, null, 2) + "\n");
}

export function searchTermForIssuer(issuerName) {
  const words = canonicalIssuer(issuerName).split(" ").filter(Boolean);
  const stopwords = new Set([
    "limited", "ltd", "india", "and", "of", "the",
    "industries", "industry", "international", "services", "solutions",
    "engineering", "developers", "logistics", "consulting"
  ]);
  const candidates = words.filter((word) => !stopwords.has(word) && word.length >= 4);
  if (candidates.length === 0) return words[0] || "";
  return candidates.sort((a, b) => b.length - a.length || words.indexOf(a) - words.indexOf(b))[0];
}

export function buildSebiSearchUrl(issuerName) {
  const url = new URL(SEBI_SEARCH_URL);
  const searchTerm = searchTermForIssuer(issuerName);
  url.searchParams.set("search", searchTerm || normalizeText(issuerName));
  return url.href;
}

function sameDocument(a, b) {
  return a.url === b.url || (
    normalizeText(a.identity).toLowerCase() === normalizeText(b.identity).toLowerCase() &&
    a.type === b.type
  );
}

export function appendDocument(record, document) {
  record.documents ||= [];
  if (record.documents.some((existing) => sameDocument(existing, document))) return false;
  record.documents.push(document);
  return true;
}

export function applySebiEntry(match, entry, now, abridgedDocs = []) {
  const { record } = match;
  const type = entry.kind === "rhp" ? "SEBI RHP filing" : "SEBI Prospectus filing";
  let changed = appendDocument(record, {
    type,
    identity: entry.title,
    url: entry.url,
    publication_date: entry.publication_date,
    collected_at: now
  });

  for (const doc of abridgedDocs) {
    changed = appendDocument(record, {
      ...doc,
      publication_date: entry.publication_date,
      collected_at: now
    }) || changed;
  }

  if (changed) record.last_collected_at = now;
  return changed;
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

function loadRecoveries() {
  return recoveryFiles().map((file) => ({
    file,
    data: JSON.parse(fs.readFileSync(file, "utf8")),
    changed: false
  }));
}

async function fetchText(url, attempts = 3, timeoutMs = 15000) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(url, {
        headers: {
          "user-agent": USER_AGENT,
          "accept": "text/html,application/xhtml+xml",
          "accept-language": "en-US,en;q=0.9",
          "cache-control": "no-cache",
          "pragma": "no-cache",
          "referer": "https://www.sebi.gov.in/"
        },
        signal: AbortSignal.timeout(timeoutMs)
      });
      if (response.ok) return await response.text();
      lastError = new Error(`HTTP ${response.status} for ${url}`);
    } catch (error) {
      lastError = error;
    }
    if (attempt < attempts) await sleep(attempt * 1200);
  }
  throw lastError;
}

async function discoverListing(url, kind, cacheToken) {
  const requestUrl = cacheBustedListingUrl(url, cacheToken);
  const html = await fetchText(requestUrl);
  const entries = parseSebiListingHtml(html, kind, url);
  if (entries.length === 0) {
    const filingRefs = (html.match(/filings[\\/]+public-issues/gi) || []).length;
    const pageText = stripTags(html).slice(0, 500);
    const label = kind || "general filings";
    fail(
      `${label} listing returned no parseable filing entries ` +
      `(bytes=${html.length}, filing_refs=${filingRefs}, page_head=${JSON.stringify(pageText)})`
    );
  }
  return entries;
}

async function detailDocumentsForEntry(entry, detailCache) {
  let detailHtml = detailCache.get(entry.url);
  if (detailHtml === undefined) {
    try {
      detailHtml = await fetchText(entry.url);
    } catch {
      detailHtml = null;
    }
    detailCache.set(entry.url, detailHtml);
  }
  if (!detailHtml) return [];

  if (entry.kind === "rhp") {
    const abridged = parseAbridgedProspectusLinks(detailHtml, entry.url);
    const rhpPdfs = parseProspectusPdfLinks(detailHtml, entry.url).map((doc) => ({
      ...doc,
      type: "SEBI RHP PDF",
      identity: `${entry.title} — PDF`
    }));
    return [...abridged, ...rhpPdfs];
  }

  if (entry.kind === "final") {
    return parseProspectusPdfLinks(detailHtml, entry.url).map((doc) => ({
      ...doc,
      identity: `${entry.title} — PDF`
    }));
  }

  return [];
}

async function applyEntry(match, entry, now, detailCache, stats, changedRecords) {
  const attachedDocs = await detailDocumentsForEntry(entry, detailCache);
  const before = match.record.documents?.length || 0;
  if (!applySebiEntry(match, entry, now, attachedDocs)) return false;

  match.recovery.changed = true;
  changedRecords.add(match.record.id);
  stats.added_documents += (match.record.documents?.length || 0) - before;
  stats.resolved_rhp_pdfs += attachedDocs.filter((doc) => doc.type === "SEBI RHP PDF").length;
  stats.resolved_prospectus_pdfs += attachedDocs.filter((doc) => doc.type === "SEBI Prospectus PDF").length;
  return true;
}

async function resolveOtherDocumentPdfs(records, now, detailCache, stats, changedRecords) {
  for (const match of records) {
    const filings = (match.record.documents || []).filter((doc) => doc.type === "SEBI Other Document");
    for (const filing of filings) {
      stats.other_document_pdf_candidates += 1;

      let html = detailCache.get(filing.url);
      if (html === undefined) {
        try {
          html = await fetchText(filing.url);
        } catch (error) {
          stats.other_document_pdf_errors += 1;
          console.warn(
            "SEBI Other Document PDF resolution failed for " +
            match.record.issuer_name + ": " + error.message
          );
          detailCache.set(filing.url, null);
          continue;
        }
        detailCache.set(filing.url, html);
      }
      if (!html) continue;

      const docs = parseOtherDocumentPdfLinks(html, filing.url, filing.identity);
      let added = 0;
      for (const doc of docs) {
        if (appendDocument(match.record, {
          ...doc,
          publication_date: filing.publication_date ?? null,
          collected_at: now
        })) {
          added += 1;
        }
      }

      if (added > 0) {
        match.record.last_collected_at = now;
        match.recovery.changed = true;
        changedRecords.add(match.record.id);
        stats.resolved_other_document_pdfs += added;
        stats.added_documents += added;
      }
    }
  }
}

async function targetedSearch(records, now, detailCache, stats, changedRecords, historicalState) {
  const liveCandidates = targetedSearchCandidates(records)
    .map((match) => ({ ...match, search_scope: "live" }));
  const historicalCandidates = historicalSearchCandidates(records, historicalState, now)
    .map((match) => ({ ...match, search_scope: "historical" }));
  const candidates = [...liveCandidates, ...historicalCandidates];

  stats.targeted_candidates = candidates.length;
  stats.targeted_live_candidates = liveCandidates.length;
  stats.targeted_historical_candidates = historicalCandidates.length;

  for (const match of candidates) {
    stats.targeted_searches += 1;
    const url = buildSebiSearchUrl(match.record.issuer_name);
    let html;
    try {
      html = await fetchText(url, 2, 10000);
    } catch (error) {
      stats.targeted_errors += 1;
      console.warn(`SEBI targeted search failed for ${match.record.issuer_name}: ${error.message}`);
      if (match.search_scope === "historical") {
        historicalState.issuers[historicalSearchKey(match.record)] = {
          issuer_name: match.record.issuer_name,
          listing_date: match.record.listing_date?.value ?? null,
          last_attempted_at: now,
          status: "error",
          search_url: url,
          parsed_entries: 0,
          matched_entries: 0
        };
        historicalState.changed = true;
      }
      continue;
    }

    const parsedEntries = parseSebiListingHtml(html, null, url);
    stats.targeted_parsed_entries += parsedEntries.length;
    const entries = parsedEntries.filter((entry) => matchIssuerRecord([match], entry.issuer_name));

    if (match.search_scope === "historical") {
      historicalState.issuers[historicalSearchKey(match.record)] = {
        issuer_name: match.record.issuer_name,
        listing_date: match.record.listing_date?.value ?? null,
        last_attempted_at: now,
        status: entries.length > 0 ? "matched" : "no_match",
        search_url: url,
        parsed_entries: parsedEntries.length,
        matched_entries: entries.length
      };
      historicalState.changed = true;
    }

    if (entries.length === 0) continue;

    const uniqueKinds = new Set();
    for (const entry of entries) {
      const uniqueKey = `${entry.kind}|${entry.url}`;
      if (uniqueKinds.has(uniqueKey)) continue;
      uniqueKinds.add(uniqueKey);
      stats.targeted_matches += 1;
      await applyEntry(match, entry, now, detailCache, stats, changedRecords);
    }
  }
}

async function run() {
  const now = new Date().toISOString();
  const recoveries = loadRecoveries();
  if (recoveries.length === 0) fail("no recovery manifests found");
  const historicalSearchState = readHistoricalSearchState();

  const records = recoveries.flatMap((recovery) =>
    (recovery.data.records || []).map((record) => ({ recovery, record }))
  );

  const cacheToken = now.replace(/\D/g, "");
  const [rhpEntries, finalEntries, allFilingsEntries, publicIssuesEntries] = await Promise.all([
    discoverListing(SEBI_RHP_LIST_URL, "rhp", cacheToken),
    discoverListing(SEBI_FINAL_LIST_URL, "final", cacheToken),
    discoverListing(SEBI_ALL_FILINGS_URL, null, cacheToken),
    discoverListing(SEBI_PUBLIC_ISSUES_URL, null, cacheToken)
  ]);

  console.log(
    "SEBI RHP listing head: " +
    rhpEntries.slice(0, 8).map((entry) => `${entry.publication_date || "undated"}|${entry.issuer_name}`).join(" ; ")
  );

  const primaryEntries = [];
  const primarySeen = new Set();
  for (const entry of [...rhpEntries, ...finalEntries, ...allFilingsEntries, ...publicIssuesEntries]) {
    const key = `${entry.kind}|${entry.url}`;
    if (primarySeen.has(key)) continue;
    primarySeen.add(key);
    primaryEntries.push(entry);
  }

  const detailCache = new Map();
  const stats = {
    listing_entries: primaryEntries.length,
    matched: 0,
    unmatched: 0,
    changed_records: 0,
    added_documents: 0,
    targeted_candidates: 0,
    targeted_live_candidates: 0,
    targeted_historical_candidates: 0,
    targeted_searches: 0,
    targeted_matches: 0,
    targeted_parsed_entries: 0,
    targeted_errors: 0,
    resolved_rhp_pdfs: 0,
    resolved_prospectus_pdfs: 0,
    other_document_pdf_candidates: 0,
    resolved_other_document_pdfs: 0,
    other_document_pdf_errors: 0
  };
  const changedRecords = new Set();

  for (const entry of primaryEntries) {
    const match = matchIssuerRecord(records, entry.issuer_name);
    if (!match) {
      stats.unmatched += 1;
      continue;
    }
    stats.matched += 1;
    await applyEntry(match, entry, now, detailCache, stats, changedRecords);
  }

  await targetedSearch(records, now, detailCache, stats, changedRecords, historicalSearchState);
  await resolveOtherDocumentPdfs(records, now, detailCache, stats, changedRecords);
  stats.changed_records = changedRecords.size;
  writeHistoricalSearchState(historicalSearchState);

  for (const recovery of recoveries) {
    if (!recovery.changed) continue;
    recovery.data.generated_at = now;
    fs.writeFileSync(recovery.file, `${JSON.stringify(recovery.data, null, 2)}\n`);
  }

  console.log(
    `SEBI document sync: ${stats.matched} matched latest-list entries, ` +
    `${stats.unmatched} unmatched; targeted ${stats.targeted_searches}/${stats.targeted_candidates} ` +
    `record(s) (live=${stats.targeted_live_candidates}, historical=${stats.targeted_historical_candidates}), ${stats.targeted_parsed_entries} targeted result filing(s), ` +
    `${stats.targeted_matches} targeted filing match(es), ${stats.targeted_errors} targeted error(s); ` +
    `${stats.resolved_rhp_pdfs} RHP PDF(s), ${stats.resolved_prospectus_pdfs} Prospectus PDF(s), ` +
    `${stats.resolved_other_document_pdfs} Other Document PDF(s) resolved ` +
    `from ${stats.other_document_pdf_candidates} candidate filing(s) ` +
    `(${stats.other_document_pdf_errors} error(s)); ` +
    `${stats.changed_records} changed record(s), ` +
    `${stats.added_documents} document(s) added.`
  );
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;

if (isMain) {
  run().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
