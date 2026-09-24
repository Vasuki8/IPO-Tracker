import assert from "node:assert/strict";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { applyReviewedListingBatches, applyVerifiedListings, reviewedManifestPaths, validateEvidenceBatch } from "./apply-verified-bse-listings.mjs";
import { isOfficialListingPdfUrl } from "./retry-bse-listing-pdf.mjs";
import { listingUrl, sha256 } from "./verify-bse-listing-candidates.mjs";
const read = (url) => JSON.parse(fs.readFileSync(fileURLToPath(new URL(url, import.meta.url)), "utf8"));
const manifest = read("../data/verified-bse-listings/2026-09-24.json");
const discovery = read("../data/discovery/bse-listing-candidates-2026-09-24.json");
assert.equal(validateEvidenceBatch(manifest, discovery).length, 15);
const original = { 2026: { generated_at: "2026-09-24T02:00:00Z", records: [{ id: "unrelated", issuer_name: "Unrelated Limited", terms: { market_lot: null }, documents: [{ url: "https://www.nseindia.com/" }], corrections: [{ old_value: 1 }] }] } };
const snapshot = JSON.stringify(original);
const result = applyVerifiedListings(original, manifest, discovery);
assert.equal(result.stats.added, 15);
assert.equal(result.recovery[2026].records.length, 16);
assert.equal(result.recovery[2026].generated_at, original[2026].generated_at, "must not roll generation time backward");
assert.equal(JSON.stringify(original), snapshot, "pure apply must not mutate input");
assert.deepEqual(result.recovery[2026].records.find((r) => r.id === "unrelated"), original[2026].records[0]);
for (const r of result.recovery[2026].records.filter((r) => r.id !== "unrelated")) {
  assert.equal(r.board, "SME"); assert.equal(r.status, "listed");
  assert.equal(r.listing_date.page, 2); assert.equal(r.issue_price.page, 2); assert.equal(r.market_lot.page, 2);
  assert.equal(r.terms.price_band, null); assert.equal(r.terms.open_date, null); assert.equal(r.terms.close_date, null);
  assert.equal(r.terms.minimum_bid_quantity, null); assert.equal(r.issue_size_inr, undefined);
  assert.equal(r.minimum_application_amount_inr, undefined);
  assert.equal(r.board_evidence[0].page, 1); assert.equal(r.status_evidence[0].page, 2);
  assert.match(r.market_lot.source.document_sha256, /^[a-f0-9]{64}$/);
}
const rerun = applyVerifiedListings(result.recovery, manifest, discovery);
assert.equal(rerun.stats.added, 0); assert.equal(rerun.stats.already_present, 15);
assert.deepEqual(rerun.changed_years, []); assert.deepEqual(rerun.recovery, result.recovery);
const concurrent = structuredClone(result.recovery);
const changed = concurrent[2026].records.find((r) => r.bse_scrip_code === "544876");
changed.issue_price.value = 123; changed.issue_price.corrections.push({ reason: "later_official_evidence" });
const protectedResult = applyVerifiedListings(concurrent, manifest, discovery);
assert.equal(protectedResult.stats.held_existing, 1);
assert.deepEqual(protectedResult.recovery, concurrent, "never replace a concurrent value or its evidence");
const conflict = { 2025: { records: [{ id: "different", issuer_name: "Different Limited", bse_scrip_code: "544876" }] } };
const held = applyVerifiedListings(conflict, manifest, discovery);
assert.equal(held.stats.held_identity_conflict, 1); assert.equal(held.stats.added, 14);
assert.equal(held.recovery[2025].records[0].issuer_name, "Different Limited");
for (const mutate of [
  (m) => m.entries[0].facts.issue_price.value++,
  (m) => m.entries[0].facts.market_lot.page = 1,
  (m) => m.entries[0].facts.minimum_bid_quantity = { value: 1000 },
  (m) => m.entries[0].source_url = "https://evil.example/notice.pdf",
  (m) => m.entries[0].document_sha256 = "not-a-hash",
  (m) => m.entries[0].publication_date = "2026-02-30",
  (m) => m.entries[0].collected_at = "2026-01-01T00:00:00Z",
  (m) => m.entries[0].bse_scrip_code = "544770",
  (m) => m.entries[0].excerpt_pages[1].text = "unrelated content",
  (m) => m.entries[0].identity_pages.notice = 0,
  (m) => m.entries.push(m.entries[0]),
  (m) => m.verifier_version = "0.0.0"
]) {
  const invalid = structuredClone(manifest); mutate(invalid);
  assert.throws(() => applyVerifiedListings(original, invalid, discovery));
  assert.equal(JSON.stringify(original), snapshot);
}
console.log("Reviewed BSE listing import, null preservation, conflict and idempotency tests passed.");

assert.ok(
  reviewedManifestPaths().includes("data/verified-bse-listings/2026-09-24.json"),
  "reviewed manifest discovery must include the first approved batch"
);

const batchA = { ...structuredClone(manifest), entries: [structuredClone(manifest.entries[0])] };
const batchB = { ...structuredClone(manifest), entries: [structuredClone(manifest.entries[1])] };
const multi = applyReviewedListingBatches(
  { 2026: { generated_at: "2026-09-24T02:00:00Z", records: [] } },
  [
    { manifest_path: "data/verified-bse-listings/test-batch-a.json", manifest: batchA, discovery },
    { manifest_path: "data/verified-bse-listings/test-batch-b.json", manifest: batchB, discovery }
  ]
);
assert.equal(multi.stats.added, 2);
assert.equal(multi.recovery[2026].records.length, 2);
assert.deepEqual(
  new Set(multi.recovery[2026].records.map((record) => record.bse_verified_listing_batch.manifest)),
  new Set([
    "data/verified-bse-listings/test-batch-a.json",
    "data/verified-bse-listings/test-batch-b.json"
  ])
);

const attachmentManifest = structuredClone(manifest);
attachmentManifest.entries = [structuredClone(manifest.entries[0])];
attachmentManifest.entries[0].source_url = "https://www.bseindia.com/markets/MarketInfo/DownloadAttach.aspx?id=" +
  attachmentManifest.entries[0].listing_notice_no + "&attachedId=9a1df38b-4dcf-4e58-b182-f378e4c2a8b3";
assert.equal(isOfficialListingPdfUrl(attachmentManifest.entries[0].source_url, attachmentManifest.entries[0].listing_notice_no), true);
assert.equal(validateEvidenceBatch(attachmentManifest, discovery).length, 1);

const htmlManifest = structuredClone(manifest);
htmlManifest.entries = [structuredClone(manifest.entries[0])];
const htmlEntry = htmlManifest.entries[0];
htmlEntry.evidence_kind = "official_notice_html";
htmlEntry.source_url = listingUrl(htmlEntry.listing_notice_no);
htmlEntry.document_sha256 = "c".repeat(64);
htmlEntry.evidence_text = htmlEntry.excerpt_pages.map((page) => page.text).join(" ");
htmlEntry.normalized_text_sha256 = sha256(htmlEntry.evidence_text);
delete htmlEntry.excerpt_pages;
delete htmlEntry.identity_pages;
for (const fact of Object.values(htmlEntry.facts)) delete fact.page;
assert.equal(validateEvidenceBatch(htmlManifest, discovery).length, 1);
const htmlApplied = applyVerifiedListings({ 2026: { generated_at: "2026-09-24T02:00:00Z", records: [] } }, htmlManifest, discovery);
assert.equal(htmlApplied.stats.added, 1);
assert.equal(htmlApplied.recovery[2026].records[0].documents[0].type, "BSE Listing Notice");
assert.equal(htmlApplied.recovery[2026].records[0].listing_date.page, null);
assert.equal(htmlApplied.recovery[2026].records[0].market_lot.page, null);
const badHtml = structuredClone(htmlManifest);
badHtml.entries[0].normalized_text_sha256 = "d".repeat(64);
assert.throws(() => validateEvidenceBatch(badHtml, discovery));
