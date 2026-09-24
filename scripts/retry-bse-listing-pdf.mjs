import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { pathToFileURL } from "node:url";
import { validateBatch, listingUrl, verifyListingHtml, noticeText, sha256 } from "./verify-bse-listing-candidates.mjs";

export function archiveProbeUrl(noticeNo) {
  listingUrl(noticeNo); // The archive path is a retrieval probe, never evidence by itself.
  return `https://www.bseindia.com/downloads/UploadDocs/Notices/${noticeNo}/${noticeNo}.pdf`;
}

const ATTACHMENT_PATH = "/markets/MarketInfo/DownloadAttach.aspx";
const ATTACHMENT_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function isOfficialListingPdfUrl(value, noticeNo) {
  listingUrl(noticeNo);
  if (value === archiveProbeUrl(noticeNo)) return true;
  try {
    const url = new URL(String(value));
    const keys = [...url.searchParams.keys()].sort();
    return url.protocol === "https:" && url.hostname === "www.bseindia.com" &&
      url.pathname === ATTACHMENT_PATH &&
      keys.length === 2 && keys[0] === "attachedId" && keys[1] === "id" &&
      url.searchParams.get("id") === noticeNo &&
      ATTACHMENT_ID.test(url.searchParams.get("attachedId") || "");
  } catch {
    return false;
  }
}

export function attachmentProbeUrlsFromHtml(html, noticeNo) {
  listingUrl(noticeNo);
  const matches = String(html ?? "").matchAll(/href\s*=\s*["']?(https:\/\/www\.bseindia\.com\/markets\/MarketInfo\/DownloadAttach\.aspx\?[^"'\s>]+)/gi);
  const urls = [];
  for (const match of matches) {
    const value = match[1].replace(/&amp;/gi, "&");
    if (isOfficialListingPdfUrl(value, noticeNo) && !urls.includes(value)) urls.push(value);
  }
  return urls.slice(0, 4);
}

export function verifyListingPdfText(extracted, candidate, asOf) {
  const checked = verifyListingHtml(extracted, candidate, asOf);
  if (checked.status !== "verified") return checked;
  const pages = extracted.split("\f").map(noticeText);
  for (const fact of Object.values(checked.facts)) {
    const page = pages.findIndex((text) => text.includes(fact.source_value));
    if (page < 0) throw new Error("field_page_evidence_missing");
    fact.page = page + 1;
  }
  checked.identity_pages = {
    notice: pages.findIndex((text) => text.includes("Notice No. " + candidate.listing_notice_no)) + 1,
    board: pages.findIndex((text) => /\bSegment SME\b/.test(text)) + 1
  };
  return checked;
}

export function applyPdfVerificationResult(result, checked, { url, attempt, bytesLength, evidenceFile }) {
  if (!result.html_attempt && String(result.evidence_file || "").endsWith(".html")) {
    result.html_attempt = {
      source_url: result.source_url,
      response_sha256: result.response_sha256,
      collected_at: result.collected_at,
      evidence_file: result.evidence_file,
      reasons: result.reasons
    };
  }
  Object.assign(result, checked, {
    source_url: url,
    source_kind: "BSE Listing Notice PDF",
    response_sha256: attempt.response_sha256,
    response_bytes: bytesLength,
    http_status: attempt.http_status,
    content_type: attempt.content_type,
    collected_at: attempt.collected_at,
    evidence_file: evidenceFile,
    scanned_pdf_pages: "1-3"
  });
  return result;
}

async function fetchPdfAttempt(url, candidate, evidenceDir, evidenceFile, retrievalMethod, fetchImpl) {
  const attempt = { source_url: url, retrieval_method: retrievalMethod, collected_at: null };
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "bse-listing-pdf-"));
  try {
    const response = await fetchImpl(url, {
      headers: { "user-agent": "Mozilla/5.0", accept: "application/pdf", referer: candidate.listing_notice_url },
      signal: AbortSignal.timeout(20000),
      redirect: "error"
    });
    attempt.http_status = response.status;
    attempt.content_type = response.headers.get("content-type");
    if (!response.ok) { await response.body?.cancel(); throw new Error("http_" + response.status); }
    const chunks = []; let size = 0;
    for await (const chunk of response.body) {
      size += chunk.length;
      if (size > 2 * 1024 * 1024) throw new Error("response_size_limit");
      chunks.push(Buffer.from(chunk));
    }
    const bytes = Buffer.concat(chunks);
    attempt.collected_at = new Date().toISOString();
    attempt.response_bytes = bytes.length;
    attempt.response_sha256 = sha256(bytes);
    if (bytes.subarray(0, 5).toString("ascii") !== "%PDF-") throw new Error("not_a_pdf");
    fs.writeFileSync(path.join(evidenceDir, evidenceFile), bytes);
    fs.writeFileSync(path.join(dir, "notice.pdf"), bytes);
    execFileSync("pdftotext", ["-f", "1", "-l", "3", "-layout", path.join(dir, "notice.pdf"), path.join(dir, "notice.txt")], { timeout: 20000, stdio: "ignore" });
    const extracted = fs.readFileSync(path.join(dir, "notice.txt"), "utf8");
    attempt.extracted_text_sha256 = sha256(extracted);
    const checked = verifyListingPdfText(extracted, candidate, attempt.collected_at);
    attempt.status = checked.status;
    attempt.reasons = checked.reasons;
    attempt.response_text = checked.response_text;
    return { attempt, checked, bytesLength: bytes.length, evidenceFile };
  } catch (error) {
    attempt.error = String(error?.message || error);
    return { attempt, checked: null, bytesLength: null, evidenceFile };
  } finally {
    attempt.collected_at ||= new Date().toISOString();
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

export async function retryPdf(report, evidenceDir, fetchImpl = fetch, { upgradeVerifiedHtml = false } = {}) {
  validateBatch({ schema_version: report.schema_version, candidates: report.results.map((r) => r.candidate) });
  fs.mkdirSync(evidenceDir, { recursive: true });
  for (const result of report.results) {
    const verifiedPdf = result.status === "verified" && result.source_kind === "BSE Listing Notice PDF";
    const verifiedHtml = result.status === "verified" && !verifiedPdf;
    if (verifiedPdf || (verifiedHtml && !upgradeVerifiedHtml)) continue;

    const candidate = result.candidate;
    const original = structuredClone(result);
    let rejected = null;
    let html = "";
    if (typeof original.evidence_file === "string" && path.basename(original.evidence_file) === original.evidence_file &&
        original.evidence_file.endsWith(".html")) {
      const htmlPath = path.join(evidenceDir, original.evidence_file);
      if (fs.existsSync(htmlPath)) html = fs.readFileSync(htmlPath, "utf8");
    }
    const attachmentUrls = attachmentProbeUrlsFromHtml(html, candidate.listing_notice_no);

    const archiveUrl = archiveProbeUrl(candidate.listing_notice_no);
    const archive = await fetchPdfAttempt(
      archiveUrl, candidate, evidenceDir, candidate.listing_notice_no + ".pdf",
      "official_archive_path_probe", fetchImpl
    );
    result.pdf_archive_attempt = archive.attempt;
    if (archive.checked?.status === "verified") {
      applyPdfVerificationResult(result, archive.checked, {
        url: archiveUrl, attempt: archive.attempt, bytesLength: archive.bytesLength, evidenceFile: archive.evidenceFile
      });
      continue;
    }
    if (archive.checked?.status === "rejected") rejected = { ...archive, url: archiveUrl };

    result.pdf_attachment_attempts = [];
    let attachmentVerified = false;
    for (let i = 0; i < attachmentUrls.length; i++) {
      const url = attachmentUrls[i];
      const attemptResult = await fetchPdfAttempt(
        url, candidate, evidenceDir, `${candidate.listing_notice_no}-attachment-${i + 1}.pdf`,
        "official_notice_attachment", fetchImpl
      );
      result.pdf_attachment_attempts.push(attemptResult.attempt);
      if (attemptResult.checked?.status === "verified") {
        applyPdfVerificationResult(result, attemptResult.checked, {
          url, attempt: attemptResult.attempt, bytesLength: attemptResult.bytesLength, evidenceFile: attemptResult.evidenceFile
        });
        attachmentVerified = true;
        break;
      }
      if (attemptResult.checked?.status === "rejected" && !rejected) rejected = { ...attemptResult, url };
    }
    if (attachmentVerified) continue;

    if (original.status === "verified") {
      Object.assign(result, original, {
        pdf_archive_attempt: archive.attempt,
        pdf_attachment_attempts: result.pdf_attachment_attempts
      });
    } else if (rejected) {
      applyPdfVerificationResult(result, rejected.checked, {
        url: rejected.url, attempt: rejected.attempt, bytesLength: rejected.bytesLength, evidenceFile: rejected.evidenceFile
      });
      result.pdf_archive_attempt = archive.attempt;
      result.pdf_attachment_attempts ||= [];
    }
  }
  report.stats = { attempted: report.results.length, verified: 0, rejected: 0, unavailable: 0 };
  for (const result of report.results) report.stats[result.status] += 1;
  report.status = report.stats.verified === report.stats.attempted ? "complete" : report.stats.verified ? "partial" : "failed";
  report.generated_at = new Date().toISOString();
  return report;
}

async function run() {
  const args = Object.fromEntries(process.argv.slice(2).map((a) => { const i = a.indexOf("="); return [a.slice(0, i), a.slice(i + 1)]; }));
  if (!args["--report"] || !args["--evidence-dir"]) throw new Error("--report and --evidence-dir required");
  const upgradeVerifiedHtml = args["--upgrade-verified-html"] === "true";
  if (args["--upgrade-verified-html"] != null && !["true", "false"].includes(args["--upgrade-verified-html"])) {
    throw new Error("--upgrade-verified-html must be true or false");
  }
  const report = JSON.parse(fs.readFileSync(args["--report"], "utf8"));
  const updated = await retryPdf(report, args["--evidence-dir"], fetch, { upgradeVerifiedHtml });
  fs.writeFileSync(args["--report"], JSON.stringify(updated, null, 2) + "\n");
  console.log(JSON.stringify({ bse_listing_verification_with_pdf: updated.stats, status: updated.status }));
  if (updated.status !== "complete") process.exitCode = 1;
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) run().catch((e) => { console.error(e); process.exitCode = 1; });
