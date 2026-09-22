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
    /\b(?:offer|issue)\s+price\s+(?:has\s+been\s+fixed|has\s+been\s+determined)\s+(?:at\s+)?(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)(?:\s*\/\-)?\s*[*#^†‡]?\s*(?:per\s+(?:equity\s+)?share|\/\s*(?:equity\s+)?share)\b/i
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
  const action = process.argv.includes("--diagnose") ? diagnose : run;
  action().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
