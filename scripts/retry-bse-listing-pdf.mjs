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
  result.html_attempt = {
    source_url: result.source_url,
    response_sha256: result.response_sha256,
    collected_at: result.collected_at,
    evidence_file: result.evidence_file,
    reasons: result.reasons
  };
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

export async function retryPdf(report, evidenceDir, fetchImpl = fetch, { upgradeVerifiedHtml = false } = {}) {
  validateBatch({ schema_version: report.schema_version, candidates: report.results.map((r) => r.candidate) });
  fs.mkdirSync(evidenceDir, { recursive: true });
  for (const result of report.results) {
    const verifiedPdf = result.status === "verified" && result.source_kind === "BSE Listing Notice PDF";
    const verifiedHtml = result.status === "verified" && !verifiedPdf;
    if (verifiedPdf || (verifiedHtml && !upgradeVerifiedHtml)) continue;
    const candidate = result.candidate;
    const url = archiveProbeUrl(candidate.listing_notice_no);
    const attempt = { source_url: url, retrieval_method: "official_archive_path_probe", collected_at: null };
    result.pdf_archive_attempt = attempt;
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "bse-listing-pdf-"));
    try {
      const response = await fetchImpl(url, { headers: { "user-agent": "Mozilla/5.0", accept: "application/pdf", referer: "https://www.bseindia.com/" }, signal: AbortSignal.timeout(20000), redirect: "error" });
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
      const name = candidate.listing_notice_no + ".pdf";
      fs.writeFileSync(path.join(evidenceDir, name), bytes);
      fs.writeFileSync(path.join(dir, "notice.pdf"), bytes);
      execFileSync("pdftotext", ["-f", "1", "-l", "3", "-layout", path.join(dir, "notice.pdf"), path.join(dir, "notice.txt")], { timeout: 20000, stdio: "ignore" });
      const extracted = fs.readFileSync(path.join(dir, "notice.txt"), "utf8");
      attempt.extracted_text_sha256 = sha256(extracted);
      const checked = verifyListingPdfText(extracted, candidate, attempt.collected_at);
      attempt.status = checked.status;
      attempt.reasons = checked.reasons;
      attempt.response_text = checked.response_text;
      applyPdfVerificationResult(result, checked, {
        url,
        attempt,
        bytesLength: bytes.length,
        evidenceFile: name
      });
    } catch (error) { attempt.error = String(error?.message || error); }
    finally { attempt.collected_at ||= new Date().toISOString(); fs.rmSync(dir, { recursive: true, force: true }); }
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
