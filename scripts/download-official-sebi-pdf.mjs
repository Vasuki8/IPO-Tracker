import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";

export const DEFAULT_SEBI_PDF_DOWNLOAD_ATTEMPTS = 4;
export const MAX_SEBI_PDF_BYTES = 80 * 1024 * 1024;

export function isOfficialSebiAttachmentPdf(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" &&
      /^(?:www\.)?sebi\.gov\.in$/i.test(parsed.hostname) &&
      /^\/sebi_data\/attachdocs\//i.test(parsed.pathname) &&
      /\.pdf$/i.test(parsed.pathname) &&
      !parsed.username && !parsed.password;
  } catch {
    return false;
  }
}

function errorText(error) {
  return [error?.message, error?.stderr?.toString?.(), error?.stdout?.toString?.()]
    .filter(Boolean).join("\n");
}

function resumeUnsupported(error) {
  return /does not seem to support byte ranges|cannot resume|requested range not satisfiable|range error/i.test(errorText(error));
}

export function downloadOfficialSebiPdf(url, {
  userAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
  referer = "https://www.sebi.gov.in/",
  maxSeconds = 75,
  attempts = DEFAULT_SEBI_PDF_DOWNLOAD_ATTEMPTS,
  maxBytes = MAX_SEBI_PDF_BYTES,
  tempPrefix = "ipo-sebi-pdf-",
  execImpl = execFileSync
} = {}) {
  if (!isOfficialSebiAttachmentPdf(url)) throw new Error("unsafe_sebi_pdf_url");
  if (!Number.isInteger(maxSeconds) || maxSeconds < 15 || maxSeconds > 180) throw new Error("invalid_sebi_pdf_max_seconds");
  if (!Number.isInteger(attempts) || attempts < 1 || attempts > 6) throw new Error("invalid_sebi_pdf_attempts");
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 1024 || maxBytes > 200 * 1024 * 1024) throw new Error("invalid_sebi_pdf_max_bytes");

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), tempPrefix));
  const file = path.join(dir, "document.pdf");
  let resumed = false;
  const failures = [];
  try {
    for (let attempt = 1; attempt <= attempts; attempt += 1) {
      const existing = fs.existsSync(file) ? fs.statSync(file).size : 0;
      if (existing > maxBytes) throw new Error("sebi_pdf_partial_exceeds_size_bound");
      const args = [
        "--fail", "--location", "--silent", "--show-error",
        "--connect-timeout", "10", "--max-time", String(maxSeconds),
        "--max-filesize", String(maxBytes),
        "--user-agent", userAgent,
        "--referer", referer
      ];
      if (existing > 0) {
        args.push("--continue-at", "-");
        resumed = true;
      }
      args.push("--output", file, url);

      try {
        execImpl("curl", args, { stdio: ["ignore", "ignore", "pipe"], maxBuffer: 1024 * 1024 });
      } catch (error) {
        failures.push({ attempt, existing_bytes: existing, error: errorText(error).slice(0, 1200) });
        if (existing > 0 && resumeUnsupported(error)) fs.rmSync(file, { force: true });
        if (attempt < attempts) continue;
        const retained = fs.existsSync(file) ? fs.statSync(file).size : 0;
        throw new Error("sebi_pdf_download_failed_after_" + attempts + "_attempts retained_bytes=" + retained +
          " last_error=" + failures.at(-1).error);
      }

      const bytes = fs.readFileSync(file);
      if (bytes.length > maxBytes) throw new Error("sebi_pdf_exceeds_size_bound");
      if (bytes.length < 5 || bytes.subarray(0, 5).toString("ascii") !== "%PDF-") {
        failures.push({ attempt, existing_bytes: existing, error: "response was not PDF" });
        fs.rmSync(file, { force: true });
        if (attempt < attempts) continue;
        throw new Error("response was not PDF");
      }
      return { bytes, attempts_used: attempt, resumed, failures };
    }
    throw new Error("sebi_pdf_download_exhausted");
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}
