import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  collectHistoricalIpoEvidence,
  trustedHistoricalSourceUrl,
  validateHistoricalEvidenceReceipt,
  validateHistoricalReview,
  sha256
} from "./materialize-historical-ipo-evidence.mjs";

const source = (key, url, type = "Prospectus") => ({
  key,
  authority: "National Stock Exchange of India Limited",
  document_type: type,
  url,
  page: 1,
  evidence_locator: "test locator",
  source_bytes_sha256: null,
  projection: { issuer: key },
  projection_sha256: "a".repeat(64)
});
const review = {
  schema_version: "1.0.0",
  status: "historical_ipo_coverage_verified_import_pending",
  result: { historical_ipos_verified: 9 },
  decisions: Array.from({length:9},(_,i)=>({excluded_event_symbol:"X"+i})),
  sources: [
    source("pdf-one", "https://nsearchives.nseindia.com/emerge/corporates/content/example.pdf"),
    source("html-one", "https://nsearchives.nseindia.com/corporate/ixbrl/example_WEB.html", "NSE iXBRL"),
    ...Array.from({length:7},(_,i)=>source("pdf-"+(i+2), "https://archives.nseindia.com/emerge/corporates/content/example-"+(i+2)+".pdf"))
  ]
};
const reviewBytes = Buffer.from(JSON.stringify(review));
assert.ok(trustedHistoricalSourceUrl(review.sources[0].url));
assert.ok(trustedHistoricalSourceUrl("https://www.visioninfraindia.com/wp-content/uploads/2024/08/RHP.pdf"));
for (const bad of [
  "http://nsearchives.nseindia.com/a.pdf",
  "https://nsearchives.nseindia.com.evil.test/a.pdf",
  "https://evil.test/a.pdf",
  "javascript:alert(1)"
]) assert.equal(trustedHistoricalSourceUrl(bad), null);
assert.deepEqual(validateHistoricalReview(review).source_keys.size, 9);

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "historical-ipo-evidence-"));
try {
  const pdf = Buffer.from("%PDF-1.7\nsynthetic official pdf\n");
  const html = Buffer.from("<!doctype html><html><body>synthetic official html</body></html>");
  const fetchImpl = async (url) => {
    const body = url.endsWith(".html") ? html : pdf;
    const response = new Response(body, {
      status: 200,
      headers: {"content-type": url.endsWith(".html") ? "text/html; charset=utf-8" : "application/pdf"}
    });
    Object.defineProperty(response, "url", { value: url });
    return response;
  };
  let tick = 0;
  const receipt = await collectHistoricalIpoEvidence({
    review,
    reviewBytes,
    evidenceDir: dir,
    fetchImpl,
    clock: () => `2026-09-26T12:00:${String(tick++).padStart(2,"0")}.000Z`
  });
  assert.equal(receipt.documents.length, 9);
  assert.equal(receipt.documents.filter(d=>d.detected_type==="pdf").length, 8);
  assert.equal(receipt.documents.filter(d=>d.detected_type==="html").length, 1);
  assert.equal(receipt.review_sha256, sha256(reviewBytes));
  assert.deepEqual(validateHistoricalEvidenceReceipt(receipt, review, reviewBytes), {
    documents: 9,
    bytes: 8 * pdf.length + html.length
  });
  assert.equal(fs.readdirSync(dir).length, 9);

  const tampered = structuredClone(receipt);
  tampered.documents[0].response_sha256 = "not-a-sha256";
  assert.throws(() => validateHistoricalEvidenceReceipt(tampered, review, reviewBytes));

  const badReview = structuredClone(review);
  badReview.sources[0].url = "https://evil.test/example.pdf";
  assert.throws(() => validateHistoricalReview(badReview));
} finally {
  fs.rmSync(dir, {recursive:true, force:true});
}

console.log(JSON.stringify({historical_ipo_evidence_tests:{
  trusted_host_guards:true,
  exact_review_hash:true,
  per_document_hash_and_bytes:true,
  artifact_files_written:true,
  malformed_hash_rejected:true
}}));
