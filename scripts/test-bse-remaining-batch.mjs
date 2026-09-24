import assert from "node:assert/strict";
import fs from "node:fs";
import { listingUrl, validateBatch, verifyListingHtml } from "./verify-bse-listing-candidates.mjs";
import { verifyListingPdfText } from "./retry-bse-listing-pdf.mjs";

const candidate = { issuer_name: "Example Industries Limited", bse_scrip_code: "544876", listing_notice_no: "20260820-37", listing_date: "2026-08-21", listing_notice_url: listingUrl("20260820-37") };
const header = "Notice No. 20260820-37 Notice Date 20 Aug 2026 Category Company related Segment SME Subject Listing of Equity Shares of Example Industries Limited Attachments Annexure.pdf";
const body = "Trading Members are informed that e ective from Friday, August 21, 2026, the Equity Shares of Example Industries Limited shall be listed and admitted to dealings. Scrip Code 544876 Market Lot 1000 Issue Price for the current Public issue Rs. 50/- per share";
const text = header + "\f" + body;
const asOf = "2026-09-24T00:00:00Z";
const result = verifyListingPdfText(text, candidate, asOf);
assert.equal(result.status, "verified");
assert.equal(result.facts.listing_date.source_value, "e ective from Friday, August 21, 2026");
assert.equal(result.facts.listing_date.page, 2);
assert.equal(result.facts.listing_date.value, "2026-08-21");
for (const replacement of ["e xective from", "Effective at the open of", "e ective at the open of"]) {
  assert.equal(verifyListingHtml(text.replace("e ective from", replacement), candidate, asOf).status, "rejected");
}
assert.equal(verifyListingHtml(text.replace("August 21", "August 22"), candidate, asOf).status, "rejected");
assert.equal(verifyListingHtml(text + " effective from August 22, 2026", candidate, asOf).status, "rejected");
const first = validateBatch(JSON.parse(fs.readFileSync(new URL("../data/discovery/bse-listing-candidates-2026-09-24.json", import.meta.url))));
const remaining = validateBatch(JSON.parse(fs.readFileSync(new URL("../data/discovery/bse-listing-candidates-2026-09-24-batch-02.json", import.meta.url))));
assert.equal(remaining.length, 12);
assert.ok(remaining.every((c) => c.bse_scrip_code !== "544770"));
assert.ok(remaining.every((c) => !first.some((old) => old.listing_notice_no === c.listing_notice_no || old.bse_scrip_code === c.bse_scrip_code)));
console.log("Remaining BSE batch and missing-ff label regression tests passed.");
