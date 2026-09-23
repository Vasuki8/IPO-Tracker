import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { selectBalancedByListingYear } from "./historical-batch-selection.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const STATE_PATH = path.join(ROOT, "ops", "sebi-historical-offer-dates.json");
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
export const HISTORICAL_OFFER_DATE_BATCH_SIZE = 12;
export const HISTORICAL_OFFER_DATE_PARSER_VERSION = "2.0.0";
const MAX_PAGES = 35;

function normalizeText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function officialSebiPdf(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" &&
      /^(?:www\.)?sebi\.gov\.in$/i.test(parsed.hostname) &&
      /^\/sebi_data\/attachdocs\//i.test(parsed.pathname) &&
      /\.pdf$/i.test(parsed.pathname);
  } catch {
    return false;
  }
}

function monthNumber(name) {
  const months = {
    jan:"01", january:"01", feb:"02", february:"02", mar:"03", march:"03",
    apr:"04", april:"04", may:"05", jun:"06", june:"06", jul:"07", july:"07",
    aug:"08", august:"08", sep:"09", sept:"09", september:"09", oct:"10", october:"10",
    nov:"11", november:"11", dec:"12", december:"12"
  };
  return months[String(name || "").toLowerCase()] ?? null;
}

function validIsoDate(year, month, day) {
  const y = Number(year), m = Number(month), d = Number(day);
  if (!Number.isInteger(y) || !Number.isInteger(m) || !Number.isInteger(d)) return null;
  const date = new Date(Date.UTC(y, m - 1, d));
  if (date.getUTCFullYear() !== y || date.getUTCMonth() !== m - 1 || date.getUTCDate() !== d) return null;
  return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

export function parseExplicitOfferDate(value) {
  const text = normalizeText(value).replace(/[.]/g, "");
  let match = text.match(/\b(January|February|March|April|May|June|July|August|September|Sept|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s+(20\d{2})\b/i);
  if (match) {
    const month = monthNumber(match[1]);
    if (month) return validIsoDate(match[3], month, match[2]);
  }
  match = text.match(/\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|Sept|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*,?\s+(20\d{2})\b/i);
  if (match) {
    const month = monthNumber(match[2]);
    if (month) return validIsoDate(match[3], month, match[1]);
  }
  return null;
}

function firstExplicitDateMatch(value) {
  const text = String(value ?? "");
  const patterns = [
    /\b(January|February|March|April|May|June|July|August|September|Sept|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s+(20\d{2})\b/i,
    /\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|Sept|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*,?\s+(20\d{2})\b/i
  ];
  let best = null;
  for (const pattern of patterns) {
    const match = pattern.exec(text);
    if (!match) continue;
    const parsed = parseExplicitOfferDate(match[0]);
    if (!parsed) continue;
    if (!best || match.index < best.index) {
      best = { value: parsed, raw: match[0], index: match.index };
    }
  }
  return best;
}

function stripAllowedBridgeToken(value, pattern) {
  const match = value.match(pattern);
  return match ? value.slice(match[0].length) : value;
}

function allowedLabelDateBridge(rawBridge) {
  let bridge = String(rawBridge ?? "").trim();

  // Ordinary punctuation can separate a label from its value. A full stop is
  // intentionally excluded so prose like "Offer Closing Date. F&S has..."
  // cannot donate an unrelated later date.
  bridge = bridge.replace(/^[,:;\-–—\s]+/, "");

  bridge = stripAllowedBridgeToken(
    bridge,
    /^except\s+in\s+relation\s+to\s+any\s+bids?\s+received\s+from\s+the\s+anchor\s+investors?,?/i
  );
  bridge = bridge.replace(/^[,:;\-–—\s]+/, "");

  bridge = stripAllowedBridgeToken(bridge, /^i\.?\s*e\.?/i);
  bridge = bridge.replace(/^[,:;\-–—\s]+/, "");

  bridge = stripAllowedBridgeToken(bridge, /^being\b/i);
  bridge = bridge.replace(/^[,:;\-–—\s]+/, "");

  bridge = stripAllowedBridgeToken(
    bridge,
    /^(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b/i
  );
  bridge = bridge.replace(/^[,:;\-–—\s]+/, "");

  return bridge.trim() === "";
}

function anchorSpecificDateContext(text, labelIndex, labelLength, afterLabel, dateMatch) {
  const before = text.slice(Math.max(0, labelIndex - 55), labelIndex);
  if (/anchor\s+investor/i.test(before)) return true;

  const tailStart = dateMatch.index + dateMatch.raw.length;
  const tail = afterLabel.slice(tailStart, tailStart + 150);
  return (
    /\bbids?\s+by\s+anchor\s+investors?\s+were\s+submitted\b/i.test(tail) ||
    /\ballocation\s+to\s+anchor\s+investors?\b/i.test(tail) ||
    /\banchor\s+investor\s+allocation\b/i.test(tail)
  );
}

function dateMentions(pageText, page, kind) {
  const text = normalizeText(pageText);
  if (!text) return [];
  const labels = kind === "open"
    ? [
        /\b(?:bid\s*\/\s*issue|bid|issue|offer)\s+opening\s+date\b/ig,
        /\b(?:bid\s*\/\s*issue|bid|issue|offer)\s+(?:opens?|opened)\s+on\b/ig
      ]
    : [
        /\b(?:bid\s*\/\s*issue|bid|issue|offer)\s+closing\s+date\b/ig,
        /\b(?:bid\s*\/\s*issue|bid|issue|offer)\s+(?:closes?|closed)\s+on\b/ig
      ];
  const mentions = [];
  for (const pattern of labels) {
    pattern.lastIndex = 0;
    for (const match of text.matchAll(pattern)) {
      const labelIndex = match.index ?? 0;
      const labelEnd = labelIndex + match[0].length;
      const afterLabel = text.slice(labelEnd, Math.min(text.length, labelEnd + 180));
      const dateMatch = firstExplicitDateMatch(afterLabel);
      if (!dateMatch) continue;

      const bridge = afterLabel.slice(0, dateMatch.index);
      if (!allowedLabelDateBridge(bridge)) continue;
      if (anchorSpecificDateContext(text, labelIndex, match[0].length, afterLabel, dateMatch)) continue;

      const sourceEnd = labelEnd + dateMatch.index + dateMatch.raw.length;
      mentions.push({
        value: dateMatch.value,
        source_value: text.slice(labelIndex, sourceEnd),
        page
      });
    }
  }
  return mentions;
}

function uniqueDate(mentions) {
  const byValue = new Map();
  for (const item of mentions) if (!byValue.has(item.value)) byValue.set(item.value, item);
  if (byValue.size !== 1) return { extraction: null, conflict: byValue.size > 1 };
  return { extraction: [...byValue.values()][0], conflict: false };
}

export function parseExplicitOfferDatesFromPages(pages, listingDate = null) {
  const openMentions = [];
  const closeMentions = [];
  for (let index = 0; index < (pages || []).length; index += 1) {
    openMentions.push(...dateMentions(pages[index], index + 1, "open"));
    closeMentions.push(...dateMentions(pages[index], index + 1, "close"));
  }
  const open = uniqueDate(openMentions);
  const close = uniqueDate(closeMentions);
  if (open.conflict || close.conflict) {
    return { open_date: null, close_date: null, reason: "official_date_conflict", open_mentions: openMentions, close_mentions: closeMentions };
  }

  const openDate = open.extraction?.value ?? null;
  const closeDate = close.extraction?.value ?? null;
  if (openDate && closeDate && openDate > closeDate) {
    return { open_date: null, close_date: null, reason: "invalid_offer_chronology", open_mentions: openMentions, close_mentions: closeMentions };
  }
  if (listingDate && closeDate && closeDate > listingDate) {
    return { open_date: null, close_date: null, reason: "closing_after_listing", open_mentions: openMentions, close_mentions: closeMentions };
  }
  return {
    open_date: open.extraction ?? null,
    close_date: close.extraction ?? null,
    reason: openDate || closeDate ? null : "explicit_dates_absent",
    open_mentions: openMentions,
    close_mentions: closeMentions
  };
}

export function offerDateExtractionPassesCurrentRules(extraction, kind, listingDate = null) {
  if (!extraction?.value || !extraction?.source_value) return false;
  const parsed = parseExplicitOfferDatesFromPages([extraction.source_value], listingDate);
  const candidate = kind === "open" ? parsed.open_date : parsed.close_date;
  return candidate?.value === extraction.value;
}

export function candidateOfferDateDocument(record, currentYear = new Date().getUTCFullYear()) {
  const listingYear = Number(String(record?.listing_date?.value || "").slice(0, 4));
  if (!Number.isInteger(listingYear) || listingYear >= currentYear) return null;
  const openMissing = record.open_date?.value == null && record.terms?.open_date == null;
  const closeMissing = record.close_date?.value == null && record.terms?.close_date == null;
  if (!openMissing && !closeMissing) return null;
  const docs = record.documents || [];
  return docs.find((doc) => doc.type === "SEBI Prospectus PDF" && officialSebiPdf(doc.url)) ||
    docs.find((doc) => doc.type === "SEBI RHP PDF" && officialSebiPdf(doc.url)) ||
    null;
}

export function offerDateKey(record) {
  const year = String(record?.listing_date?.value || "").slice(0, 4);
  return `${year || "unknown"}|${record?.id || normalizeText(record?.issuer_name).toLowerCase()}`;
}

export function offerDateCandidates(
  records,
  state = { issuers: {} },
  currentYear = new Date().getUTCFullYear(),
  max = HISTORICAL_OFFER_DATE_BATCH_SIZE
) {
  const eligible = records.filter(({ record }) => {
    if (!candidateOfferDateDocument(record, currentYear)) return false;
    const item = state?.issuers?.[offerDateKey(record)];
    if (!item) return true;
    if (item.parser_version !== HISTORICAL_OFFER_DATE_PARSER_VERSION) return true;
    if (item.status !== "error") return false;
    const attempted = Date.parse(item.last_attempted_at || "");
    return !Number.isFinite(attempted) || Date.now() - attempted >= 24 * 60 * 60 * 1000;
  });
  return selectBalancedByListingYear(eligible, max);
}

function fieldSource(document, collectedAt) {
  return {
    url: document.url,
    document_type: document.type,
    document_identity: document.identity ?? null,
    publication_date: document.publication_date ?? null,
    collected_at: collectedAt
  };
}

export function applyOfferDates(record, document, parsed, collectedAt) {
  let changed = false;
  if (parsed?.open_date && record.open_date?.value == null && record.terms?.open_date == null) {
    record.open_date = {
      value: parsed.open_date.value,
      source_value: parsed.open_date.source_value,
      page: parsed.open_date.page,
      status: "verified",
      source: fieldSource(document, collectedAt)
    };
    changed = true;
  }
  if (parsed?.close_date && record.close_date?.value == null && record.terms?.close_date == null) {
    record.close_date = {
      value: parsed.close_date.value,
      source_value: parsed.close_date.source_value,
      page: parsed.close_date.page,
      status: "verified",
      source: fieldSource(document, collectedAt)
    };
    changed = true;
  }
  if (changed) record.last_collected_at = collectedAt;
  return changed;
}

function recoveryFiles() {
  if (!fs.existsSync(RECOVERY_ROOT)) return [];
  return fs.readdirSync(RECOVERY_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^20\d{2}$/.test(entry.name))
    .map((entry) => path.join(RECOVERY_ROOT, entry.name, "nse-issue-information.json"))
    .filter((file) => fs.existsSync(file))
    .sort();
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

function fetchPdf(url) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ipo-offer-dates-"));
  const file = path.join(dir, "document.pdf");
  try {
    execFileSync("curl", [
      "--fail", "--location", "--silent", "--show-error",
      "--retry", "1", "--retry-all-errors",
      "--connect-timeout", "10", "--max-time", "45",
      "--user-agent", USER_AGENT,
      "--referer", "https://www.sebi.gov.in/",
      "--output", file, url
    ], { stdio: ["ignore", "ignore", "pipe"], maxBuffer: 1024 * 1024 });
    const bytes = fs.readFileSync(file);
    if (bytes.length < 5 || bytes.subarray(0, 5).toString("ascii") !== "%PDF-") throw new Error("response was not PDF");
    return bytes;
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function firstPages(pdfBytes) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ipo-offer-date-text-"));
  const file = path.join(dir, "document.pdf");
  try {
    fs.writeFileSync(file, pdfBytes);
    const output = execFileSync("pdftotext", [
      "-f", "1", "-l", String(MAX_PAGES), "-layout", "-enc", "UTF-8", file, "-"
    ], { encoding: "utf8", maxBuffer: 16 * 1024 * 1024, timeout: 30000 });
    return output.split("\f").slice(0, MAX_PAGES);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

async function run() {
  try {
    execFileSync("pdftotext", ["-v"], { stdio: "ignore" });
  } catch {
    throw new Error("pdftotext is required");
  }

  const groups = recoveryFiles().map((file) => ({
    file,
    recovery: JSON.parse(fs.readFileSync(file, "utf8")),
    changed: false
  }));
  const records = groups.flatMap((group) =>
    (group.recovery.records || []).map((record) => ({ group, record }))
  );
  const state = readState();
  const candidates = offerDateCandidates(records, state);
  const now = new Date().toISOString();
  const stats = { candidates: candidates.length, attempted: 0, downloaded: 0, extracted_records: 0, open_dates: 0, close_dates: 0, no_fields: 0, conflicts: 0, fetch_errors: 0 };

  for (const { group, record } of candidates) {
    const key = offerDateKey(record);
    const document = candidateOfferDateDocument(record);
    stats.attempted += 1;
    try {
      const pages = firstPages(fetchPdf(document.url));
      stats.downloaded += 1;
      const parsed = parseExplicitOfferDatesFromPages(pages, record.listing_date?.value ?? null);
      if (parsed.reason === "official_date_conflict" || parsed.reason === "invalid_offer_chronology" || parsed.reason === "closing_after_listing") {
        stats.conflicts += 1;
      }
      const beforeOpen = record.open_date?.value ?? record.terms?.open_date ?? null;
      const beforeClose = record.close_date?.value ?? record.terms?.close_date ?? null;
      const changed = applyOfferDates(record, document, parsed, now);
      const afterOpen = record.open_date?.value ?? record.terms?.open_date ?? null;
      const afterClose = record.close_date?.value ?? record.terms?.close_date ?? null;
      if (changed) {
        group.changed = true;
        stats.extracted_records += 1;
        if (!beforeOpen && afterOpen) stats.open_dates += 1;
        if (!beforeClose && afterClose) stats.close_dates += 1;
      } else {
        stats.no_fields += 1;
      }
      state.issuers[key] = {
        issuer_name: record.issuer_name,
        listing_date: record.listing_date?.value ?? null,
        last_attempted_at: now,
        parser_version: HISTORICAL_OFFER_DATE_PARSER_VERSION,
        status: changed ? "extracted" : (parsed.reason || "no_fields"),
        open_date: afterOpen,
        close_date: afterClose,
        open_extraction: parsed.open_date ?? null,
        close_extraction: parsed.close_date ?? null,
        document: {
          type: document.type,
          identity: document.identity ?? null,
          url: document.url,
          publication_date: document.publication_date ?? null
        },
        source_url: document.url
      };
    } catch (error) {
      stats.fetch_errors += 1;
      state.issuers[key] = {
        issuer_name: record.issuer_name,
        listing_date: record.listing_date?.value ?? null,
        last_attempted_at: now,
        parser_version: HISTORICAL_OFFER_DATE_PARSER_VERSION,
        status: "error",
        error: error.message,
        source_url: document.url
      };
      console.warn("Historical SEBI offer-date PDF unavailable for " + record.issuer_name + ": " + error.message);
    }
  }

  for (const group of groups) {
    if (!group.changed) continue;
    group.recovery.generated_at = now;
    fs.writeFileSync(group.file, JSON.stringify(group.recovery, null, 2) + "\n");
  }
  if (candidates.length > 0) writeState(state);
  console.log(JSON.stringify({ historical_offer_dates: stats }, null, 2));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => { console.error(error); process.exit(1); });
