import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const ALLOWED_HOSTS = new Set(["www.sebi.gov.in", "sebi.gov.in"]);
const MAX_PAGES = 20;
const DIAGNOSTIC_MAX_PAGES = 80;
const MINIMUM_BID_DIAGNOSTIC_MAX_PAGES = 650;
const NII_MINIMUM_APPLICATION_MAX_PAGES = 140;
const NEW_ISSUE_SIZE_EVIDENCE = new Map([
  ["Moneyview Limited", "SEBI RHP PDF"],
  ["Qualiance International Limited", "SEBI Other Document PDF"]
]);
const USER_AGENT =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

function fail(message) {
  throw new Error("Prospectus field extraction failed: " + message);
}

function normalizeText(value) {
  return String(value ?? "")
    .replace(/\u00a0/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function officialProspectusPdfUrl(url) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }
  if (parsed.protocol !== "https:" || !ALLOWED_HOSTS.has(parsed.hostname)) return null;
  if (!/^\/sebi_data\/attachdocs\//i.test(parsed.pathname)) return null;
  if (!/\.pdf$/i.test(parsed.pathname)) return null;
  return parsed.href;
}

export function parseExplicitIssuePrice(pageText, page = 1) {
  const text = normalizeText(pageText);
  if (!text) return null;

  const patterns = [
    /\b(?:the\s+)?(?:offer|issue)\s+price\s*(?:(?:is|of)|has\s+been\s+determined\s+at)?\s*[:\-–—]?\s*(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)(?:\s*\/\-)?\s*[*#^†‡]?\s*(?:per\s+(?:equity\s+)?share|\/\s*(?:equity\s+)?share)\b/i,
    /\b(?:offer|issue)\s+price\s+(?:has\s+been\s+fixed|has\s+been\s+determined)\s+(?:at\s+)?(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)(?:\s*\/\-)?\s*[*#^†‡]?\s*(?:per\s+(?:equity\s+)?share|\/\s*(?:equity\s+)?share)\b/i,
    /\b(?:at\s+)?a\s+price\s+of\s*(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*[*#^†‡]?\s*(?:\/\-)?\s*per\s+(?:equity\s+)?share\b.{0,180}?\(\s*[“"'‘’]?\s*(?:offer|issue)\s+price\s*[”"'‘’]?\s*\)/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (!match) continue;
    const numeric = Number(match[1].replace(/,/g, ""));
    if (!Number.isFinite(numeric) || numeric <= 0) continue;
    return {
      value: numeric,
      source_value: "₹" + match[1] + " per Equity Share",
      page
    };
  }

  return null;
}

export function parseExplicitIssuePriceFromPages(pages) {
  for (let index = 0; index < (pages || []).length; index += 1) {
    const extraction = parseExplicitIssuePrice(pages[index], index + 1);
    if (extraction) return extraction;
  }
  return null;
}

export function findIssuePriceMentions(pageText, page = 1) {
  const text = normalizeText(pageText);
  const mentions = [];
  const pattern = /\b(?:offer|issue)\s+price\b/ig;
  for (const match of text.matchAll(pattern)) {
    const start = Math.max(0, match.index - 90);
    const end = Math.min(text.length, match.index + 220);
    mentions.push({
      page,
      context: text.slice(start, end)
    });
    if (mentions.length >= 6) break;
  }
  return mentions;
}

export function candidateProspectusDocument(record) {
  if (record.issue_price?.value !== null && record.issue_price?.value !== undefined) return null;
  return (record.documents || []).find((doc) =>
    doc.type === "SEBI Prospectus PDF" && officialProspectusPdfUrl(doc.url)
  ) || null;
}

export function candidateProspectusIssueSizeDocument(record) {
  if (record.issue_size_inr?.value !== null && record.issue_size_inr?.value !== undefined) return null;
  return (record.documents || []).find((doc) =>
    doc.type === "SEBI Prospectus PDF" && officialProspectusPdfUrl(doc.url)
  ) || null;
}

export function candidateNewIssueSizeEvidenceDocument(record) {
  if (record.issue_size_inr?.value !== null && record.issue_size_inr?.value !== undefined) return null;
  const expectedType = NEW_ISSUE_SIZE_EVIDENCE.get(record.issuer_name);
  if (!expectedType) return null;
  return (record.documents || []).find((doc) =>
    doc.type === expectedType && officialProspectusPdfUrl(doc.url)
  ) || null;
}

export function candidateRhpIssueSizeDocument(record) {
  if (record.issue_size_inr?.value !== null && record.issue_size_inr?.value !== undefined) return null;
  return (record.documents || []).find((doc) =>
    doc.type === "SEBI RHP PDF" && officialProspectusPdfUrl(doc.url)
  ) || null;
}

export function candidateRhpMinimumBidDocument(record) {
  if (record.minimum_bid_quantity?.value !== null && record.minimum_bid_quantity?.value !== undefined) return null;
  if (record.terms?.minimum_bid_quantity !== null && record.terms?.minimum_bid_quantity !== undefined) return null;
  return (record.documents || []).find((doc) =>
    doc.type === "SEBI RHP PDF" && officialProspectusPdfUrl(doc.url)
  ) || null;
}

export function candidateRhpMinimumApplicationDocument(record) {
  if (
    record.minimum_application_amount_inr?.value !== null &&
    record.minimum_application_amount_inr?.value !== undefined
  ) return null;
  return (record.documents || []).find((doc) =>
    doc.type === "SEBI RHP PDF" && officialProspectusPdfUrl(doc.url)
  ) || null;
}

export function candidateRhpNiiMinimumApplicationDocument(record) {
  const existing = record.application_requirements?.non_institutional?.minimum_application_amount_inr?.value;
  if (existing !== null && existing !== undefined) return null;
  return (record.documents || []).find((doc) =>
    doc.type === "SEBI RHP PDF" && officialProspectusPdfUrl(doc.url)
  ) || null;
}

export function candidateRhpNiiMinimumBidDocument(record) {
  const existing = record.application_requirements?.non_institutional?.minimum_bid_quantity?.value;
  if (existing !== null && existing !== undefined) return null;
  return (record.documents || []).find((doc) =>
    doc.type === "SEBI RHP PDF" && officialProspectusPdfUrl(doc.url)
  ) || null;
}

export function candidateProspectusRetailMinimumApplicationDocument(record) {
  const existing = record.application_requirements?.retail?.minimum_application_amount_inr?.value;
  if (existing !== null && existing !== undefined) return null;
  return (record.documents || []).find((doc) =>
    doc.type === "SEBI Prospectus PDF" && officialProspectusPdfUrl(doc.url)
  ) || null;
}

export function candidateProspectusMinimumBidDocument(record) {
  if (record.minimum_bid_quantity?.value !== null && record.minimum_bid_quantity?.value !== undefined) return null;
  if (record.terms?.minimum_bid_quantity !== null && record.terms?.minimum_bid_quantity !== undefined) return null;
  return (record.documents || []).find((doc) =>
    doc.type === "SEBI Prospectus PDF" && officialProspectusPdfUrl(doc.url)
  ) || null;
}

export function parseExplicitMinimumBidQuantity(pageText, page = 1) {
  const text = normalizeText(pageText);
  if (!text) return null;

  const patterns = [
    /\bbid\s+lot\s*[:\-–—]?\s*([0-9][0-9,]*)\s+equity\s+shares\b/i,
    /\bminimum\s+bid\s*[:\-–—]?\s*([0-9][0-9,]*)\s+equity\s+shares\b/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (!match) continue;
    const value = Number(match[1].replace(/,/g, ""));
    if (!Number.isInteger(value) || value <= 0) continue;
    return {
      value,
      source_value: match[0],
      page
    };
  }

  return null;
}

export function parseExplicitMinimumBidQuantityFromPages(pages) {
  for (let index = 0; index < (pages || []).length; index += 1) {
    const extraction = parseExplicitMinimumBidQuantity(pages[index], index + 1);
    if (extraction) return extraction;
  }
  return null;
}

export function findMinimumBidMentionsInPages(pages) {
  const mentions = [];
  const patterns = [
    /\bminimum\s+bid(?:ding)?(?:\s+(?:lot|quantity))?\b/ig,
    /\bbid\s+lot\b/ig,
    /\bminimum\s+of\s+[0-9][0-9,]*\s+equity\s+shares\b/ig,
    /\bin\s+multiples\s+of\s+[0-9][0-9,]*\s+equity\s+shares\b/ig
  ];

  for (let pageIndex = 0; pageIndex < (pages || []).length; pageIndex += 1) {
    const text = normalizeText(pages[pageIndex]);
    for (const pattern of patterns) {
      pattern.lastIndex = 0;
      for (const match of text.matchAll(pattern)) {
        const start = Math.max(0, match.index - 160);
        const end = Math.min(text.length, match.index + 420);
        mentions.push({
          page: pageIndex + 1,
          context: text.slice(start, end)
        });
        if (mentions.length >= 18) return mentions;
      }
    }
  }
  return mentions;
}

export function findMinimumApplicationAmountMentionsInPages(pages) {
  const mentions = [];
  const labelPatterns = [
    /\bminimum\s+(?:application|investment)(?:\s+(?:amount|size))?\b/ig,
    /\bminimum\s+amount\s+(?:of|for)\s+(?:the\s+|an?\s+)?application\b/ig,
    /\bapplication\s+(?:amount|size)\s*[:\-–—]?\s*minimum\b/ig
  ];
  const explicitInr = /(?:₹|rs\.?|inr)\s*[0-9][0-9,]*(?:\.[0-9]+)?\b/i;

  for (let pageIndex = 0; pageIndex < (pages || []).length; pageIndex += 1) {
    const text = normalizeText(pages[pageIndex]);
    for (const pattern of labelPatterns) {
      pattern.lastIndex = 0;
      for (const match of text.matchAll(pattern)) {
        const start = Math.max(0, match.index - 220);
        const end = Math.min(text.length, match.index + 520);
        const context = text.slice(start, end);
        if (!explicitInr.test(context)) continue;
        mentions.push({
          page: pageIndex + 1,
          label: match[0],
          context
        });
        if (mentions.length >= 24) return mentions;
      }
    }
  }
  return mentions;
}

function applicationAmountToInr(rawAmount, rawUnit) {
  const amount = Number(String(rawAmount).replace(/,/g, ""));
  if (!Number.isFinite(amount) || amount <= 0) return null;

  const unit = String(rawUnit ?? "").toLowerCase();
  const multiplier = !unit
    ? 1
    : unit.startsWith("million")
      ? 1_000_000
      : unit.startsWith("lakh") || unit.startsWith("lac")
        ? 100_000
        : unit.startsWith("crore")
          ? 10_000_000
          : null;
  if (!multiplier) return null;
  return Math.round(amount * multiplier);
}

export function findExplicitNiiMinimumApplicationAmounts(pageText, page = 1) {
  const text = normalizeText(pageText);
  if (!text) return [];

  const results = [];
  const pattern = /\bminimum\s+application(?:\s+(?:amount|size))?\s*(?:viz\.?|of|is|shall\s+be)?\s*[:\-–—]?\s*(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(million|lakhs?|lacs?|crores?)?\b/ig;

  for (const match of text.matchAll(pattern)) {
    const contextStart = Math.max(0, match.index - 320);
    const contextEnd = Math.min(text.length, match.index + 420);
    const categoryContext = text.slice(contextStart, contextEnd);
    if (!/\bnon[\s-]*institutional(?:\s+(?:investor|bidder|portion|investors|bidders))?\b/i.test(categoryContext)) {
      continue;
    }

    const value = applicationAmountToInr(match[1], match[2]);
    if (!value) continue;

    results.push({
      value,
      source_value: match[0],
      page,
      context: categoryContext
    });
  }
  return results;
}

export function findExplicitNiiMinimumApplicationAmountsInPages(pages) {
  return (pages || []).flatMap((pageText, index) =>
    findExplicitNiiMinimumApplicationAmounts(pageText, index + 1)
  );
}

export function findExplicitRetailMinimumApplicationAmounts(pageText, page = 1) {
  const text = normalizeText(pageText);
  if (!text) return [];

  const results = [];
  const patterns = [
    /\bminimum\s+application(?:\s+(?:amount|size))?\s*(?:viz\.?|of|is|shall\s+be)?\s*[:\-–—]?\s*(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(million|lakhs?|lacs?|crores?)?\b/ig,
    /\bminimum\s+amount\s+(?:of|for)\s+(?:the\s+|an?\s+)?application\s*[:\-–—]?\s*(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(million|lakhs?|lacs?|crores?)?\b/ig
  ];
  const retailPattern = /\bretail\s+individual\s+(?:bidder|bidders|investor|investors)\b/i;

  for (const pattern of patterns) {
    pattern.lastIndex = 0;
    for (const match of text.matchAll(pattern)) {
      const contextStart = Math.max(0, match.index - 360);
      const contextEnd = Math.min(text.length, match.index + 460);
      const context = text.slice(contextStart, contextEnd);
      if (!retailPattern.test(context)) continue;

      const value = applicationAmountToInr(match[1], match[2]);
      if (!value) continue;

      results.push({
        value,
        source_value: match[0],
        page,
        context
      });
      if (results.length >= 12) return results;
    }
  }

  return results;
}

export function findExplicitRetailMinimumApplicationAmountsInPages(pages) {
  return (pages || []).flatMap((pageText, index) =>
    findExplicitRetailMinimumApplicationAmounts(pageText, index + 1)
  );
}

export function findExplicitNiiMinimumBidQuantities(pageText, page = 1) {
  const text = normalizeText(pageText);
  if (!text) return [];

  const results = [];
  const patterns = [
    /\bminimum\s+bid(?:ding)?(?:\s+(?:lot|quantity|size))?\s*(?:of|is|shall\s+be)?\s*[:\-–—]?\s*([0-9][0-9,]*)\s+(?:equity\s+)?shares\b/ig,
    /\bminimum\s+(?:application|bid)\s+size\s*(?:of|is|shall\s+be)?\s*[:\-–—]?\s*([0-9][0-9,]*)\s+(?:equity\s+)?shares\b/ig,
    /\bminimum\s+of\s+([0-9][0-9,]*)\s+(?:equity\s+)?shares\b/ig
  ];
  const niiPattern = /\bnon[\s-]*institutional(?:\s+(?:investor|bidder|portion|investors|bidders))?\b/i;

  for (const pattern of patterns) {
    pattern.lastIndex = 0;
    for (const match of text.matchAll(pattern)) {
      const contextStart = Math.max(0, match.index - 260);
      const contextEnd = Math.min(text.length, match.index + 360);
      const context = text.slice(contextStart, contextEnd);
      if (!niiPattern.test(context)) continue;

      const value = Number(match[1].replace(/,/g, ""));
      if (!Number.isInteger(value) || value <= 0) continue;

      results.push({
        value,
        source_value: match[0],
        page,
        context
      });
      if (results.length >= 12) return results;
    }
  }
  return results;
}

export function findExplicitNiiMinimumBidQuantitiesInPages(pages) {
  return (pages || []).flatMap((pageText, index) =>
    findExplicitNiiMinimumBidQuantities(pageText, index + 1)
  );
}

export function findAggregateIssueSizeMentions(pageText, page = 1) {
  const text = normalizeText(pageText);
  const mentions = [];
  const patterns = [
    /\baggregating\s+(?:to|up\s+to)\s+(?:₹|rs\.?|inr)\s*[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:million|lakhs?|crores?)?\b/ig,
    /\btotal\s+(?:offer|issue)\s+size\b/ig
  ];

  for (const pattern of patterns) {
    for (const match of text.matchAll(pattern)) {
      const start = Math.max(0, match.index - 140);
      const end = Math.min(text.length, match.index + 300);
      mentions.push({ page, context: text.slice(start, end) });
      if (mentions.length >= 8) return mentions;
    }
  }
  return mentions;
}

function aggregateAmountToInr(rawAmount, rawUnit) {
  const amount = Number(String(rawAmount).replace(/,/g, ""));
  if (!Number.isFinite(amount) || amount <= 0) return null;

  const unit = String(rawUnit).toLowerCase();
  const multiplier = unit.startsWith("million")
    ? 1_000_000
    : unit.startsWith("lakh")
      ? 100_000
      : unit.startsWith("crore")
        ? 10_000_000
        : null;

  if (!multiplier) return null;
  return Math.round(amount * multiplier);
}

export function parseExplicitAggregateIssueSize(pageText, page = 1) {
  const text = normalizeText(pageText);
  if (!text) return null;

  const amount = "([0-9][0-9,]*(?:\\.[0-9]+)?)";
  const marker = "[*#^†‡]{0,4}";
  const unit = "(million|lakhs?|crores?)";
  const currency = "(?:₹|rs\\.?|inr)";
  const aggregate = "aggregating\\s+(?:to|up\\s+to)";
  const overallLabel = "\\(\\s*[“\\\"'‘’]?\\s*(?:the\\s+)?(?:offer|issue)\\s*[”\\\"'‘’]?\\s*\\)";
  const priceLabel = "\\(\\s*(?:the\\s+)?[“\\\"'‘’]?\\s*(?:offer|issue)\\s+price\\s*[”\\\"'‘’]?\\s*\\)";

  const patterns = [
    new RegExp(
      priceLabel + "\\s*" + aggregate + "\\s*" + currency + "\\s*" +
      amount + "\\s*" + marker + "\\s*" + unit + "\\s*" + marker,
      "i"
    ),
    new RegExp(
      "\\b" + aggregate + "\\s*" + currency + "\\s*" +
      amount + "\\s*" + marker + "\\s*" + unit + "\\s*" + marker +
      "\\s*" + overallLabel,
      "i"
    ),
    new RegExp(
      "\\btotal\\s+(?:offer|issue)\\s+size\\s*[:\\-–—]?\\s*" +
      currency + "\\s*" + amount + "\\s*" + marker + "\\s*" + unit + "\\s*" + marker,
      "i"
    )
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (!match) continue;

    const rawAmount = match[1];
    const rawUnit = match[2];
    const value = aggregateAmountToInr(rawAmount, rawUnit);
    if (!value) continue;

    return {
      value,
      source_value: "₹" + rawAmount + " " + rawUnit,
      page
    };
  }

  return null;
}

export function parseExplicitAggregateIssueSizeFromPages(pages) {
  for (let index = 0; index < (pages || []).length; index += 1) {
    const extraction = parseExplicitAggregateIssueSize(pages[index], index + 1);
    if (extraction) return extraction;
  }
  return null;
}

export function applyIssuePriceExtraction(record, document, extraction, collectedAt) {
  if (!document || !extraction) return false;
  if (record.issue_price?.value !== null && record.issue_price?.value !== undefined) return false;

  record.issue_price = {
    value: extraction.value,
    source_value: extraction.source_value,
    page: extraction.page,
    source: {
      url: document.url,
      document_type: document.type,
      document_identity: document.identity ?? null,
      publication_date: document.publication_date ?? null,
      collected_at: collectedAt
    }
  };
  record.last_collected_at = collectedAt;
  return true;
}

export function applyMinimumBidExtraction(record, document, extraction, collectedAt) {
  if (!document || !extraction) return false;
  if (record.minimum_bid_quantity?.value !== null && record.minimum_bid_quantity?.value !== undefined) return false;
  if (record.terms?.minimum_bid_quantity !== null && record.terms?.minimum_bid_quantity !== undefined) return false;

  record.minimum_bid_quantity = {
    value: extraction.value,
    source_value: extraction.source_value,
    page: extraction.page,
    status: "verified",
    source: {
      url: document.url,
      document_type: document.type,
      document_identity: document.identity ?? null,
      publication_date: document.publication_date ?? null,
      collected_at: collectedAt
    }
  };
  record.last_collected_at = collectedAt;
  return true;
}

export function applyNiiMinimumApplicationExtraction(record, document, extraction, collectedAt) {
  if (!document || !extraction) return false;

  const existing = record.application_requirements?.non_institutional?.minimum_application_amount_inr?.value;
  if (existing !== null && existing !== undefined) return false;

  record.application_requirements ??= {};
  record.application_requirements.non_institutional ??= {};
  record.application_requirements.non_institutional.minimum_application_amount_inr = {
    value: extraction.value,
    source_value: extraction.source_value,
    page: extraction.page,
    status: "verified",
    source: {
      url: document.url,
      document_type: document.type,
      document_identity: document.identity ?? null,
      publication_date: document.publication_date ?? null,
      collected_at: collectedAt
    }
  };
  record.last_collected_at = collectedAt;
  return true;
}

export function applyIssueSizeExtraction(record, document, extraction, collectedAt) {
  if (!document || !extraction) return false;
  if (record.issue_size_inr?.value !== null && record.issue_size_inr?.value !== undefined) return false;

  record.issue_size_inr = {
    value: extraction.value,
    source_value: extraction.source_value,
    page: extraction.page,
    source: {
      url: document.url,
      document_type: document.type,
      document_identity: document.identity ?? null,
      publication_date: document.publication_date ?? null,
      collected_at: collectedAt
    }
  };
  record.last_collected_at = collectedAt;
  return true;
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

function ensurePdfTextTool() {
  try {
    execFileSync("pdftotext", ["-v"], { stdio: "ignore" });
  } catch {
    fail("pdftotext is required but is not available on this runner");
  }
}

async function fetchPdf(url, attempts = 3) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(url, {
        headers: {
          "user-agent": USER_AGENT,
          "accept": "application/pdf,*/*",
          "referer": "https://www.sebi.gov.in/"
        }
      });
      if (response.ok) {
        const contentType = response.headers.get("content-type") || "";
        if (!/application\/pdf/i.test(contentType)) {
          throw new Error("unexpected content-type " + (contentType || "(missing)"));
        }
        return Buffer.from(await response.arrayBuffer());
      }
      lastError = new Error("HTTP " + response.status);
    } catch (error) {
      lastError = error;
    }
    if (attempt < attempts) {
      await new Promise((resolve) => setTimeout(resolve, attempt * 1000));
    }
  }
  throw lastError;
}

function pagesLayout(pdfBytes, maxPages = MAX_PAGES) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ipo-prospectus-"));
  const file = path.join(dir, "document.pdf");
  try {
    fs.writeFileSync(file, pdfBytes);
    const text = execFileSync(
      "pdftotext",
      ["-f", "1", "-l", String(maxPages), "-layout", "-enc", "UTF-8", file, "-"],
      { encoding: "utf8", maxBuffer: 16 * 1024 * 1024 }
    );
    return text.split("\f").slice(0, maxPages);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function fullPagesLayout(pdfBytes) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ipo-prospectus-full-"));
  const file = path.join(dir, "document.pdf");
  try {
    fs.writeFileSync(file, pdfBytes);
    const text = execFileSync(
      "pdftotext",
      ["-layout", "-enc", "UTF-8", file, "-"],
      { encoding: "utf8", maxBuffer: 32 * 1024 * 1024 }
    );
    const pages = text.split("\f");
    if (pages.length > 0 && pages[pages.length - 1].trim() === "") pages.pop();
    return pages;
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

async function diagnose() {
  ensurePdfTextTool();
  const stats = {
    candidates: 0,
    downloaded: 0,
    mentions: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      const document = candidateProspectusDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = pagesLayout(await fetchPdf(document.url), DIAGNOSTIC_MAX_PAGES);
        stats.downloaded += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn("Prospectus diagnostic unavailable for " + record.issuer_name + ": " + error.message);
        continue;
      }

      const mentions = pages.flatMap((pageText, index) =>
        findIssuePriceMentions(pageText, index + 1)
      ).slice(0, 12);
      stats.mentions += mentions.length;

      console.log(JSON.stringify({
        issuer_name: record.issuer_name,
        document: document.identity ?? document.type,
        pages_scanned: pages.length,
        mentions
      }, null, 2));
    }
  }

  console.log(JSON.stringify({ diagnostic_stats: stats }, null, 2));
}

async function diagnoseIssueSize() {
  ensurePdfTextTool();
  const stats = {
    candidates: 0,
    downloaded: 0,
    mentions: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      const document = candidateProspectusIssueSizeDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = pagesLayout(await fetchPdf(document.url), MAX_PAGES);
        stats.downloaded += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn("Prospectus size diagnostic unavailable for " + record.issuer_name + ": " + error.message);
        continue;
      }

      const mentions = pages.flatMap((pageText, index) =>
        findAggregateIssueSizeMentions(pageText, index + 1)
      ).slice(0, 18);
      stats.mentions += mentions.length;

      console.log(JSON.stringify({
        issuer_name: record.issuer_name,
        document: document.identity ?? document.type,
        pages_scanned: pages.length,
        mentions
      }, null, 2));
    }
  }

  console.log(JSON.stringify({ issue_size_diagnostic_stats: stats }, null, 2));
}

async function diagnoseNewIssueSizeEvidence() {
  ensurePdfTextTool();
  const stats = {
    candidates: 0,
    downloaded: 0,
    parseable_overall_totals: 0,
    mentions: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      const document = candidateNewIssueSizeEvidenceDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = pagesLayout(await fetchPdf(document.url), MAX_PAGES);
        stats.downloaded += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "New issue-size evidence unavailable for " +
          record.issuer_name + ": " + error.message
        );
        continue;
      }

      const extraction = parseExplicitAggregateIssueSizeFromPages(pages);
      if (extraction) stats.parseable_overall_totals += 1;
      const mentions = pages.flatMap((pageText, index) =>
        findAggregateIssueSizeMentions(pageText, index + 1)
      ).slice(0, 18);
      stats.mentions += mentions.length;

      console.log(JSON.stringify({
        issuer_name: record.issuer_name,
        document_type: document.type,
        document: document.identity ?? document.type,
        url: document.url,
        pages_scanned: pages.length,
        parsed_overall_total: extraction,
        mentions
      }, null, 2));
    }
  }

  console.log(JSON.stringify({ new_issue_size_evidence_stats: stats }, null, 2));
}

async function diagnoseRhpIssueSize() {
  ensurePdfTextTool();
  const stats = {
    candidates: 0,
    downloaded: 0,
    parseable_overall_totals: 0,
    mentions: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      const document = candidateRhpIssueSizeDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = pagesLayout(await fetchPdf(document.url), MAX_PAGES);
        stats.downloaded += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn("RHP size diagnostic unavailable for " + record.issuer_name + ": " + error.message);
        continue;
      }

      const extraction = parseExplicitAggregateIssueSizeFromPages(pages);
      if (extraction) stats.parseable_overall_totals += 1;
      const mentions = pages.flatMap((pageText, index) =>
        findAggregateIssueSizeMentions(pageText, index + 1)
      ).slice(0, 18);
      stats.mentions += mentions.length;

      console.log(JSON.stringify({
        issuer_name: record.issuer_name,
        document: document.identity ?? document.type,
        pages_scanned: pages.length,
        parsed_overall_total: extraction,
        mentions
      }, null, 2));
    }
  }

  console.log(JSON.stringify({ rhp_issue_size_diagnostic_stats: stats }, null, 2));
}

async function diagnoseProspectusMinimumBid() {
  ensurePdfTextTool();
  const stats = {
    candidates: 0,
    downloaded: 0,
    mentions: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      const document = candidateProspectusMinimumBidDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = pagesLayout(await fetchPdf(document.url), MINIMUM_BID_DIAGNOSTIC_MAX_PAGES);
        stats.downloaded += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn("Prospectus minimum-bid diagnostic unavailable for " + record.issuer_name + ": " + error.message);
        continue;
      }

      const mentions = findMinimumBidMentionsInPages(pages);
      stats.mentions += mentions.length;

      console.log(JSON.stringify({
        issuer_name: record.issuer_name,
        document: document.identity ?? document.type,
        pages_scanned: pages.length,
        mentions
      }, null, 2));
    }
  }

  console.log(JSON.stringify({ prospectus_minimum_bid_diagnostic_stats: stats }, null, 2));
}

async function diagnoseProspectusRetailMinimumApplication() {
  ensurePdfTextTool();
  const stats = {
    candidates: 0,
    downloaded: 0,
    documents_with_explicit_retail_inr_amount: 0,
    mentions: 0,
    pages_scanned: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      const document = candidateProspectusRetailMinimumApplicationDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = fullPagesLayout(await fetchPdf(document.url));
        stats.downloaded += 1;
        stats.pages_scanned += pages.length;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "Prospectus retail minimum-application diagnostic unavailable for " +
          record.issuer_name + ": " + error.message
        );
        continue;
      }

      const mentions = findExplicitRetailMinimumApplicationAmountsInPages(pages);
      if (mentions.length > 0) stats.documents_with_explicit_retail_inr_amount += 1;
      stats.mentions += mentions.length;

      console.log(JSON.stringify({
        issuer_name: record.issuer_name,
        document: document.identity ?? document.type,
        url: document.url,
        pages_scanned: pages.length,
        retail_minimum_application_mentions: mentions
      }, null, 2));
    }
  }

  console.log(JSON.stringify({ prospectus_retail_minimum_application_diagnostic_stats: stats }, null, 2));
}

async function diagnoseRhpMinimumApplication() {
  ensurePdfTextTool();
  const stats = {
    candidates: 0,
    downloaded: 0,
    documents_with_explicit_inr_mentions: 0,
    mentions: 0,
    pages_scanned: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      const document = candidateRhpMinimumApplicationDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = fullPagesLayout(await fetchPdf(document.url));
        stats.downloaded += 1;
        stats.pages_scanned += pages.length;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "RHP minimum-application diagnostic unavailable for " +
          record.issuer_name + ": " + error.message
        );
        continue;
      }

      const mentions = findMinimumApplicationAmountMentionsInPages(pages);
      if (mentions.length > 0) stats.documents_with_explicit_inr_mentions += 1;
      stats.mentions += mentions.length;

      console.log(JSON.stringify({
        issuer_name: record.issuer_name,
        document: document.identity ?? document.type,
        url: document.url,
        pages_scanned: pages.length,
        minimum_application_mentions: mentions
      }, null, 2));
    }
  }

  console.log(JSON.stringify({ rhp_minimum_application_diagnostic_stats: stats }, null, 2));
}

async function diagnoseRhpMinimumBid() {
  ensurePdfTextTool();
  const stats = {
    candidates: 0,
    downloaded: 0,
    mentions: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      const document = candidateRhpMinimumBidDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = pagesLayout(await fetchPdf(document.url), MINIMUM_BID_DIAGNOSTIC_MAX_PAGES);
        stats.downloaded += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn("RHP minimum-bid diagnostic unavailable for " + record.issuer_name + ": " + error.message);
        continue;
      }

      const mentions = findMinimumBidMentionsInPages(pages);
      stats.mentions += mentions.length;

      console.log(JSON.stringify({
        issuer_name: record.issuer_name,
        document: document.identity ?? document.type,
        pages_scanned: pages.length,
        mentions
      }, null, 2));
    }
  }

  console.log(JSON.stringify({ rhp_minimum_bid_diagnostic_stats: stats }, null, 2));
}

async function diagnoseRhpNiiMinimumBid() {
  ensurePdfTextTool();
  const stats = {
    candidates: 0,
    downloaded: 0,
    documents_with_explicit_nii_share_quantity: 0,
    mentions: 0,
    pages_scanned: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const record of recovery.records || []) {
      const document = candidateRhpNiiMinimumBidDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = pagesLayout(await fetchPdf(document.url), MINIMUM_BID_DIAGNOSTIC_MAX_PAGES);
        stats.downloaded += 1;
        stats.pages_scanned += pages.length;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "RHP NII minimum-bid diagnostic unavailable for " +
          record.issuer_name + ": " + error.message
        );
        continue;
      }

      const mentions = findExplicitNiiMinimumBidQuantitiesInPages(pages);
      if (mentions.length > 0) stats.documents_with_explicit_nii_share_quantity += 1;
      stats.mentions += mentions.length;

      console.log(JSON.stringify({
        issuer_name: record.issuer_name,
        document: document.identity ?? document.type,
        url: document.url,
        pages_scanned: pages.length,
        nii_minimum_bid_quantity_mentions: mentions
      }, null, 2));
    }
  }

  console.log(JSON.stringify({ rhp_nii_minimum_bid_diagnostic_stats: stats }, null, 2));
}

async function runNiiMinimumApplication() {
  ensurePdfTextTool();
  const now = new Date().toISOString();
  const stats = {
    candidates: 0,
    downloaded: 0,
    extracted: 0,
    explicit_nii_amount_missing: 0,
    conflicts: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    let changed = false;

    for (const record of recovery.records || []) {
      const document = candidateRhpNiiMinimumApplicationDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = pagesLayout(await fetchPdf(document.url), NII_MINIMUM_APPLICATION_MAX_PAGES);
        stats.downloaded += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(
          "RHP unavailable for NII minimum-application extraction for " +
          record.issuer_name + ": " + error.message
        );
        continue;
      }

      const matches = findExplicitNiiMinimumApplicationAmountsInPages(pages);
      const uniqueValues = [...new Set(matches.map((match) => match.value))];
      if (uniqueValues.length === 0) {
        stats.explicit_nii_amount_missing += 1;
        continue;
      }
      if (uniqueValues.length > 1) {
        stats.conflicts += 1;
        console.warn(
          "Conflicting NII minimum-application amounts for " + record.issuer_name +
          ": " + uniqueValues.join(", ")
        );
        continue;
      }

      const extraction = matches.find((match) => match.value === uniqueValues[0]);
      if (applyNiiMinimumApplicationExtraction(record, document, extraction, now)) {
        stats.extracted += 1;
        changed = true;
        console.log(
          "Extracted NII minimum application amount for " + record.issuer_name + ": ₹" +
          extraction.value + " (PDF page " + extraction.page + ")"
        );
      }
    }

    if (changed) {
      recovery.generated_at = now;
      fs.writeFileSync(file, JSON.stringify(recovery, null, 2) + "\n");
    }
  }

  console.log(JSON.stringify(stats, null, 2));
}

async function runMinimumBid() {
  ensurePdfTextTool();
  const now = new Date().toISOString();
  const stats = {
    candidates: 0,
    downloaded: 0,
    extracted: 0,
    explicit_minimum_bid_missing: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    let changed = false;

    for (const record of recovery.records || []) {
      const document = candidateProspectusMinimumBidDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = pagesLayout(await fetchPdf(document.url), MAX_PAGES);
        stats.downloaded += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn("Prospectus unavailable for minimum-bid extraction for " + record.issuer_name + ": " + error.message);
        continue;
      }

      const extraction = parseExplicitMinimumBidQuantityFromPages(pages);
      if (!extraction) {
        stats.explicit_minimum_bid_missing += 1;
        continue;
      }

      if (applyMinimumBidExtraction(record, document, extraction, now)) {
        stats.extracted += 1;
        changed = true;
        console.log(
          "Extracted minimum bid quantity for " + record.issuer_name + ": " +
          extraction.value + " Equity Shares (PDF page " + extraction.page + ")"
        );
      }
    }

    if (changed) {
      recovery.generated_at = now;
      fs.writeFileSync(file, JSON.stringify(recovery, null, 2) + "\n");
    }
  }

  console.log(JSON.stringify(stats, null, 2));
}

async function runIssueSize() {
  ensurePdfTextTool();
  const now = new Date().toISOString();
  const stats = {
    candidates: 0,
    downloaded: 0,
    extracted: 0,
    explicit_size_missing: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    let changed = false;

    for (const record of recovery.records || []) {
      const document = candidateProspectusIssueSizeDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = pagesLayout(await fetchPdf(document.url), MAX_PAGES);
        stats.downloaded += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn("Prospectus unavailable for issue-size extraction for " + record.issuer_name + ": " + error.message);
        continue;
      }

      const extraction = parseExplicitAggregateIssueSizeFromPages(pages);
      if (!extraction) {
        stats.explicit_size_missing += 1;
        continue;
      }

      if (applyIssueSizeExtraction(record, document, extraction, now)) {
        stats.extracted += 1;
        changed = true;
        console.log(
          "Extracted issue size for " + record.issuer_name + ": " +
          extraction.source_value + " (PDF page " + extraction.page + ")"
        );
      }
    }

    if (changed) {
      recovery.generated_at = now;
      fs.writeFileSync(file, JSON.stringify(recovery, null, 2) + "\n");
    }
  }

  console.log(JSON.stringify(stats, null, 2));
}

async function run() {
  ensurePdfTextTool();
  const now = new Date().toISOString();
  const stats = {
    candidates: 0,
    downloaded: 0,
    extracted: 0,
    explicit_price_missing: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    let changed = false;

    for (const record of recovery.records || []) {
      const document = candidateProspectusDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let pages;
      try {
        pages = pagesLayout(await fetchPdf(document.url), MAX_PAGES);
        stats.downloaded += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn("Prospectus unavailable for " + record.issuer_name + ": " + error.message);
        continue;
      }

      const extraction = parseExplicitIssuePriceFromPages(pages);
      if (!extraction) {
        stats.explicit_price_missing += 1;
        continue;
      }

      if (applyIssuePriceExtraction(record, document, extraction, now)) {
        stats.extracted += 1;
        changed = true;
        console.log(
          "Extracted issue price for " + record.issuer_name + ": " +
          extraction.source_value + " (PDF page " + extraction.page + ")"
        );
      }
    }

    if (changed) {
      recovery.generated_at = now;
      fs.writeFileSync(file, JSON.stringify(recovery, null, 2) + "\n");
    }
  }

  console.log(JSON.stringify(stats, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;

if (isMain) {
  const action = process.argv.includes("--diagnose-new-size-evidence")
    ? diagnoseNewIssueSizeEvidence
    : process.argv.includes("--diagnose-prospectus-retail-min-application")
      ? diagnoseProspectusRetailMinimumApplication
    : process.argv.includes("--diagnose-rhp-nii-min-bid")
      ? diagnoseRhpNiiMinimumBid
    : process.argv.includes("--nii-minimum-application")
      ? runNiiMinimumApplication
    : process.argv.includes("--diagnose-rhp-min-application")
      ? diagnoseRhpMinimumApplication
    : process.argv.includes("--minimum-bid")
      ? runMinimumBid
    : process.argv.includes("--diagnose-prospectus-min-bid")
      ? diagnoseProspectusMinimumBid
    : process.argv.includes("--diagnose-rhp-min-bid")
      ? diagnoseRhpMinimumBid
      : process.argv.includes("--diagnose-rhp-size")
      ? diagnoseRhpIssueSize
      : process.argv.includes("--issue-size")
      ? runIssueSize
    : process.argv.includes("--diagnose-size")
      ? diagnoseIssueSize
      : process.argv.includes("--diagnose")
        ? diagnose
        : run;
  action().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}