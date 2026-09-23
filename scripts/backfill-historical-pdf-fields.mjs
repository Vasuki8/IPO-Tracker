import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { selectBalancedByListingYear } from "./historical-batch-selection.mjs";
import {
  applyIssuePriceExtraction,
  applyIssueSizeExtraction,
  applyMinimumBidExtraction,
  parseExplicitAggregateIssueSizeFromPages,
  parseExplicitIssuePriceFromPages,
  parseExplicitMinimumBidQuantityFromPages
} from "./extract-prospectus-fields.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const STATE_PATH = path.join(ROOT, "ops", "sebi-historical-pdf-fields.json");
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
export const HISTORICAL_PDF_FIELD_BATCH_SIZE = 8;
export const HISTORICAL_PDF_FIELD_PARSER_VERSION = "1.0.0";
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

export function historicalPdfKey(record) {
  const year = String(record?.listing_date?.value || "").slice(0, 4);
  return `${year || "unknown"}|${record?.id || normalizeText(record?.issuer_name).toLowerCase()}`;
}

export function missingHistoricalPdfFields(record) {
  const fields = [];
  if (record.issue_price?.value == null) fields.push("issue_price");
  if (record.issue_size_inr?.value == null) fields.push("issue_size_inr");
  if (record.minimum_bid_quantity?.value == null && record.terms?.minimum_bid_quantity == null) fields.push("minimum_bid_quantity");
  return fields;
}

export function candidateHistoricalPdf(record, currentYear = new Date().getUTCFullYear()) {
  const listingYear = Number(String(record?.listing_date?.value || "").slice(0, 4));
  if (!Number.isInteger(listingYear) || listingYear >= currentYear) return null;
  if (missingHistoricalPdfFields(record).length === 0) return null;
  const docs = record.documents || [];
  return docs.find((doc) => doc.type === "SEBI Prospectus PDF" && officialSebiPdf(doc.url)) ||
    docs.find((doc) => doc.type === "SEBI RHP PDF" && officialSebiPdf(doc.url)) ||
    null;
}

export function historicalPdfCandidates(
  records,
  state = { issuers: {} },
  currentYear = new Date().getUTCFullYear(),
  max = HISTORICAL_PDF_FIELD_BATCH_SIZE
) {
  const eligible = records.filter(({ record }) => {
    if (!candidateHistoricalPdf(record, currentYear)) return false;
    const item = state?.issuers?.[historicalPdfKey(record)];
    if (!item) return true;
    if (item.parser_version !== HISTORICAL_PDF_FIELD_PARSER_VERSION) return true;
    if (item.status !== "error") return false;
    const attempted = Date.parse(item.last_attempted_at || "");
    return !Number.isFinite(attempted) || Date.now() - attempted >= 24 * 60 * 60 * 1000;
  });
  return selectBalancedByListingYear(eligible, max);
}

export function applyHistoricalPdfFields(record, document, pages, collectedAt) {
  const before = missingHistoricalPdfFields(record);
  const changed = [];
  const extractions = {
    issue_price: null,
    issue_size_inr: null,
    minimum_bid_quantity: null
  };

  if (before.includes("issue_price")) {
    const extraction = parseExplicitIssuePriceFromPages(pages);
    extractions.issue_price = extraction ?? null;
    if (extraction && applyIssuePriceExtraction(record, document, extraction, collectedAt)) changed.push("issue_price");
  }
  if (before.includes("issue_size_inr")) {
    const extraction = parseExplicitAggregateIssueSizeFromPages(pages);
    extractions.issue_size_inr = extraction ?? null;
    if (extraction && applyIssueSizeExtraction(record, document, extraction, collectedAt)) changed.push("issue_size_inr");
  }
  if (before.includes("minimum_bid_quantity")) {
    const extraction = parseExplicitMinimumBidQuantityFromPages(pages);
    extractions.minimum_bid_quantity = extraction ?? null;
    if (extraction && applyMinimumBidExtraction(record, document, extraction, collectedAt)) changed.push("minimum_bid_quantity");
  }

  return { before, changed, remaining: missingHistoricalPdfFields(record), extractions };
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
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ipo-historical-pdf-"));
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
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ipo-historical-pdf-text-"));
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
  const candidates = historicalPdfCandidates(records, state);
  const now = new Date().toISOString();
  const stats = { candidates: candidates.length, attempted: 0, downloaded: 0, extracted_records: 0, extracted_fields: 0, no_fields: 0, fetch_errors: 0 };

  for (const { group, record } of candidates) {
    const key = historicalPdfKey(record);
    const document = candidateHistoricalPdf(record);
    stats.attempted += 1;
    try {
      const pages = firstPages(fetchPdf(document.url));
      stats.downloaded += 1;
      const result = applyHistoricalPdfFields(record, document, pages, now);
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
        parser_version: HISTORICAL_PDF_FIELD_PARSER_VERSION,
        status: result.changed.length ? "extracted" : "no_fields",
        extracted_fields: result.changed,
        remaining_fields: result.remaining,
        extractions: result.extractions,
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
        parser_version: HISTORICAL_PDF_FIELD_PARSER_VERSION,
        status: "error",
        error: error.message,
        source_url: document.url
      };
      console.warn("Historical SEBI PDF unavailable for " + record.issuer_name + ": " + error.message);
    }
  }

  for (const group of groups) {
    if (!group.changed) continue;
    group.recovery.generated_at = now;
    fs.writeFileSync(group.file, JSON.stringify(group.recovery, null, 2) + "\n");
  }
  if (candidates.length > 0) writeState(state);
  console.log(JSON.stringify({ historical_pdf_fields: stats }, null, 2));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => { console.error(error); process.exit(1); });
