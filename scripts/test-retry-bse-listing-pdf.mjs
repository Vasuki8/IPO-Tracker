import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { archiveProbeUrl, retryPdf } from "./retry-bse-listing-pdf.mjs";
import { listingUrl } from "./verify-bse-listing-candidates.mjs";
assert.equal(archiveProbeUrl("20260820-37"), "https://www.bseindia.com/downloads/UploadDocs/Notices/20260820-37/20260820-37.pdf");
assert.throws(() => archiveProbeUrl("../../unsafe"));
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
} finally { fs.rmSync(dir, {recursive:true,force:true}); }
console.log("BSE PDF archive retry tests passed.");
