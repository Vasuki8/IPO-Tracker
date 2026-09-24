import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { applyPdfVerificationResult, archiveProbeUrl, attachmentProbeUrlsFromHtml, isOfficialListingPdfUrl, retryPdf } from "./retry-bse-listing-pdf.mjs";
import { listingUrl } from "./verify-bse-listing-candidates.mjs";
assert.equal(archiveProbeUrl("20260820-37"), "https://www.bseindia.com/downloads/UploadDocs/Notices/20260820-37/20260820-37.pdf");
assert.throws(() => archiveProbeUrl("../../unsafe"));
const attachment = "https://www.bseindia.com/markets/MarketInfo/DownloadAttach.aspx?id=20260820-37&attachedId=9a1df38b-4dcf-4e58-b182-f378e4c2a8b3";
assert.equal(isOfficialListingPdfUrl(attachment, "20260820-37"), true);
assert.equal(isOfficialListingPdfUrl(attachment.replace("20260820-37", "20260820-38"), "20260820-37"), false);
assert.equal(isOfficialListingPdfUrl("https://evil.example/markets/MarketInfo/DownloadAttach.aspx?id=20260820-37&attachedId=9a1df38b-4dcf-4e58-b182-f378e4c2a8b3", "20260820-37"), false);
assert.deepEqual(
  attachmentProbeUrlsFromHtml(`<a href=${attachment}>Annexure-I.pdf</a><a href="${attachment}">duplicate</a>`, "20260820-37"),
  [attachment]
);
const candidate = { issuer_name: "Example Limited", bse_scrip_code: "544876", listing_notice_no: "20260820-37", listing_date: "2026-08-21", listing_notice_url: listingUrl("20260820-37") };
const report = { schema_version: "1.0.0", results: [{ candidate, status: "rejected", facts: null }] };
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "bse-pdf-retry-test-"));
try {
  const rejected = await retryPdf(structuredClone(report), dir, async () => new Response("<html>Not a PDF</html>"));
  assert.equal(rejected.results[0].pdf_archive_attempt.error, "not_a_pdf");
  assert.equal(rejected.stats.verified, 0);
  assert.equal(rejected.results[0].facts, null);
  const missing = await retryPdf(structuredClone(report), dir, async () => new Response("", {status:404}));
  assert.equal(missing.results[0].pdf_archive_attempt.error, "http_404");
  const verified = structuredClone(report); verified.results[0].status = "verified";
  await retryPdf(verified, dir, async () => { throw new Error("must_not_fetch_verified_record"); });
  assert.equal(verified.results[0].pdf_archive_attempt, undefined);
  const upgrade = structuredClone(verified);
  await retryPdf(upgrade, dir, async () => new Response("<html>Not a PDF</html>"), { upgradeVerifiedHtml: true });
  assert.equal(upgrade.results[0].status, "verified");
  assert.equal(upgrade.results[0].pdf_archive_attempt.error, "not_a_pdf");
} finally { fs.rmSync(dir, {recursive:true,force:true}); }
console.log("BSE PDF archive retry tests passed.");

const classified = {
  candidate,
  status: "unavailable",
  source_url: candidate.listing_notice_url,
  response_sha256: "a".repeat(64),
  collected_at: "2026-09-24T01:00:00Z",
  evidence_file: "20260820-37.html",
  reasons: ["notice_content_missing"]
};
applyPdfVerificationResult(
  classified,
  {
    status: "rejected",
    reasons: ["issuer_mismatch_or_missing"],
    observed_identity: { issuer_name: "Other Limited" },
    facts: null,
    response_text: "official pdf text"
  },
  {
    url: archiveProbeUrl(candidate.listing_notice_no),
    attempt: {
      response_sha256: "b".repeat(64),
      http_status: 200,
      content_type: "application/pdf",
      collected_at: "2026-09-24T01:01:00Z"
    },
    bytesLength: 12345,
    evidenceFile: "20260820-37.pdf"
  }
);
assert.equal(classified.status, "rejected");
assert.deepEqual(classified.reasons, ["issuer_mismatch_or_missing"]);
assert.equal(classified.source_kind, "BSE Listing Notice PDF");
assert.equal(classified.evidence_file, "20260820-37.pdf");
assert.equal(classified.html_attempt.evidence_file, "20260820-37.html");
assert.equal(classified.facts, null);
