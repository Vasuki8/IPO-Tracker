import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { listingUrl, validateBatch, strictDate, verifyListingHtml, verifyBatch, sha256 } from "./verify-bse-listing-candidates.mjs";
const candidate = { issuer_name: "Example Industries Limited", bse_scrip_code: "544876", listing_notice_no: "20260820-37", listing_date: "2026-08-21", listing_notice_url: listingUrl("20260820-37") };
const html = `<div>Notice No. 20260820-37 Notice Date 20 Aug 2026 Category Company related Segment SME Subject Listing of Equity Shares of Example Industries Limited Attachments Annexure.pdf Content Trading Members are informed that effective from Friday, August 21, 2026, the Equity Shares shall be listed and admitted to dealings. Scrip Code 544876 Market Lot 1000 Issue Price for the current Public issue Rs. 50/- per share</div>`;
const asOf = "2026-09-24T00:00:00Z";
const verify = (h, c = candidate) => verifyListingHtml(h, c, asOf);
assert.equal(verify(html).status, "verified");
assert.equal(verify(html).facts.issue_price.value, 50);
assert.equal(verify(html).facts.market_lot.value, 1000);
assert.equal(verify(html).facts.listing_date.value, "2026-08-21");
assert.equal(verify(html, { ...candidate, issuer_name: "Other Industries Limited" }).status, "rejected");
for (const [a,b] of [["Scrip Code 544876","Scrip Code 544877"],["20260820-37","20260820-35"],["August 21","August 22"],["Segment SME","Segment Equity"],["August 21","February 30"]]) assert.equal(verify(html.replace(a,b)).status, "rejected");
assert.equal(verify(html.replace("Scrip Code", "Security Code")).status, "verified");
assert.equal(verify(html.replace("effective from Friday, August 21, 2026", "Effective at the open of Friday, August 21, 2026")).status, "rejected");
assert.equal(verify(html + " Scrip Code 544877").status, "rejected");
assert.equal(verify(html + " Market Lot 2000").status, "rejected");
assert.equal(verify(html + " Issue Price for the current Public issue Rs. 70/-").status, "rejected");
assert.equal(verify('<title>BSE</title><div id="app"></div>').status, "unavailable");
assert.equal(verify(html.replace("Market Lot 1000", "").replace("Issue Price for the current Public issue Rs. 50/- per share", "")).status, "verified");
assert.equal(verify(html.replace("Market Lot 1000", "")).facts.market_lot, undefined);
assert.equal(strictDate("February 29, 2024"), "2024-02-29");
assert.equal(strictDate("February 29, 2026"), null);
assert.equal(strictDate("2026-02-30"), null);
assert.throws(() => validateBatch({ schema_version: "1.0.0", candidates: [] }));
assert.throws(() => validateBatch({ schema_version: "1.0.0", candidates: Array(16).fill(candidate) }));
assert.throws(() => validateBatch({ schema_version: "1.0.0", candidates: [candidate,candidate] }));
assert.throws(() => validateBatch({ schema_version: "1.0.0", candidates: [{...candidate, listing_notice_url: "https://evil.example/"}] }));
const batch = { schema_version: "1.0.0", candidates: [candidate] };
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "bse-verification-test-"));
try {
  const good = await verifyBatch(batch, { fetchImpl: async (url) => new Response(url === candidate.listing_notice_url ? html : "", { headers: { "content-type": "text/html" } }), now: () => asOf, evidenceDir: dir });
  assert.equal(good.status, "complete");
  assert.equal(good.stats.verified, 1);
  const bytes = fs.readFileSync(path.join(dir, "20260820-37.html"));
  assert.equal(good.results[0].response_sha256, sha256(bytes));
  assert.equal(bytes.toString(), html);
  const bad = await verifyBatch(batch, { fetchImpl: async () => { throw new Error("source_unavailable"); }, now: () => asOf });
  assert.equal(bad.status, "failed"); assert.equal(bad.stats.unavailable, 1);
  const empty = await verifyBatch(batch, { fetchImpl: async () => new Response("<html>Shell</html>"), now: () => asOf });
  assert.equal(empty.status, "failed"); assert.equal(empty.stats.unavailable, 1);
} finally { fs.rmSync(dir, { recursive: true, force: true }); }
for (const value of ["1000.5", "1000-2000", "1000 to 2000", "0"]) {
  assert.equal(verify(html.replace("Market Lot 1000", "Market Lot " + value)).status, "rejected");
}
for (const value of ["50-70", "50 to 70", "0"]) {
  assert.equal(verify(html.replace("Rs. 50/-", "Rs. " + value + "/-")).status, "rejected");
}
const emptyTemplate = "Notice Number NOTICES Notice No. Notice Date Category Segment Subject Content";
assert.deepEqual(verify(emptyTemplate).reasons, ["notice_content_missing"]);
assert.equal(verify(emptyTemplate).status, "unavailable");
console.log("BSE listing candidate verification tests passed.");

assert.equal(verify(html + " Refer to Exchange notice no. 20120216-29 dated February 16, 2012.").status, "verified");
assert.equal(verify(html.replace("Notice Date 20 Aug 2026", "Notice Date 20 Aug 2026")).observed_identity.publication_date, "2026-08-20");
const wrapped = html.replace("Subject Listing of Equity Shares of Example Industries Limited", "Listing of Equity Shares of Example Subject Industries Limited") + " Name of the company Example Industries Limited Registered Office Address";
assert.equal(verify(wrapped).status, "verified");
assert.equal(verify(html + " Name of the company Other Limited Registered Office Address").status, "rejected");
