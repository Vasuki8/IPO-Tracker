import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const ALLOWED_HOSTS = new Set(["www.sebi.gov.in", "sebi.gov.in"]);
const USER_AGENT =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

function fail(message) {
  throw new Error(`Abridged Prospectus field extraction failed: ${message}`);
}

function normalizeText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function officialPdfUrl(url) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }
  if (parsed.protocol !== "https:" || !ALLOWED_HOSTS.has(parsed.hostname)) return null;
  if (!/\.pdf(?:$|\?)/i.test(parsed.href)) return null;
  return parsed.href;
}

function headerBoundary(lines, headerIndex, start) {
  let end = null;
  for (let i = Math.max(0, headerIndex - 2); i <= Math.min(lines.length - 1, headerIndex + 3); i += 1) {
    const index = lines[i].toUpperCase().indexOf("ELIGIBILITY");
    if (index > start && (end === null || index < end)) end = index;
  }
  return end ?? start + 34;
}

export function parseExplicitTotalIssueSize(layoutText) {
  const lines = String(layoutText ?? "").replace(/\t/g, "    ").split(/\r?\n/);

  for (let i = 0; i < Math.min(lines.length, 80); i += 1) {
    const upper = lines[i].toUpperCase();
    const match = upper.match(/TOTAL\s+(?:OFFER|ISSUE)/);
    if (!match) continue;

    const start = match.index;
    const end = headerBoundary(lines, i, start);
    const slices = [];

    for (let row = i + 1; row < Math.min(lines.length, i + 24); row += 1) {
      const rowUpper = lines[row].toUpperCase();
      if (/RISKS?\s+IN\s+RELATION|GENERAL\s+RISK|ISSUER.?S?\s+ABSOLUTE/.test(rowUpper)) break;
      slices.push(lines[row].slice(Math.max(0, start - 2), end + 2));
    }

    const columnText = normalizeText(slices.join(" "));
    const amount = columnText.match(
      /(?:₹|RS\.?|INR)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*MILLION\b/i
    );
    if (!amount) return null;

    const millions = Number(amount[1].replace(/,/g, ""));
    if (!Number.isFinite(millions) || millions <= 0) return null;

    return {
      value: Math.round(millions * 1_000_000),
      source_value: `₹${amount[1]} million`,
      page: 1
    };
  }

  return null;
}

export function candidateAbridgedDocument(record) {
  if (record.issue_size_inr?.value !== null && record.issue_size_inr?.value !== undefined) return null;
  return (record.documents || []).find((doc) =>
    doc.type === "SEBI Abridged Prospectus" && officialPdfUrl(doc.url)
  ) || null;
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
          throw new Error(`unexpected content-type ${contentType || "(missing)"}`);
        }
        return Buffer.from(await response.arrayBuffer());
      }
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    if (attempt < attempts) {
      await new Promise((resolve) => setTimeout(resolve, attempt * 1000));
    }
  }
  throw lastError;
}

function firstPageLayout(pdfBytes) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ipo-ap-"));
  const file = path.join(dir, "document.pdf");
  try {
    fs.writeFileSync(file, pdfBytes);
    return execFileSync(
      "pdftotext",
      ["-f", "1", "-l", "1", "-layout", "-enc", "UTF-8", file, "-"],
      { encoding: "utf8", maxBuffer: 8 * 1024 * 1024 }
    );
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

async function run() {
  ensurePdfTextTool();
  const now = new Date().toISOString();
  const stats = {
    candidates: 0,
    downloaded: 0,
    extracted: 0,
    placeholders_or_missing: 0,
    fetch_errors: 0
  };

  for (const file of recoveryFiles()) {
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    let changed = false;

    for (const record of recovery.records || []) {
      const document = candidateAbridgedDocument(record);
      if (!document) continue;
      stats.candidates += 1;

      let layout;
      try {
        layout = firstPageLayout(await fetchPdf(document.url));
        stats.downloaded += 1;
      } catch (error) {
        stats.fetch_errors += 1;
        console.warn(`Abridged Prospectus unavailable for ${record.issuer_name}: ${error.message}`);
        continue;
      }

      const extraction = parseExplicitTotalIssueSize(layout);
      if (!extraction) {
        stats.placeholders_or_missing += 1;
        continue;
      }

      if (applyIssueSizeExtraction(record, document, extraction, now)) {
        stats.extracted += 1;
        changed = true;
        console.log(
          `Extracted issue size for ${record.issuer_name}: ${extraction.source_value} (page ${extraction.page})`
        );
      }
    }

    if (changed) {
      recovery.generated_at = now;
      fs.writeFileSync(file, `${JSON.stringify(recovery, null, 2)}\n`);
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
