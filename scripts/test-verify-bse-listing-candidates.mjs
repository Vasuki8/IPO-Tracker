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
assert.equal(verify(html.replace("effective from Friday, August 21, 2026", "e ective from Friday, August 21, 2026")).status, "verified");
assert.equal(
  verify(html.replace("effective from Friday, August 21, 2026", "effective from Friday, August 21 , 2026")).status,
  "verified"
);
assert.equal(strictDate("December 31 , 2025"), "2025-12-31");
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

{
  const candidate = {
    issuer_name: "GLOBTIER INFOTECH LIMITED",
    bse_scrip_code: "544494",
    listing_notice_no: "20250901-44",
    listing_date: "2025-09-02",
    listing_notice_url: listingUrl("20250901-44")
  };
  const checked = verifyListingHtml(
    "Notice No. 20250901-44 Notice Date 01 Sep 2025 Category Company related Segment SME " +
    "Subject Listing of Equity Shares of Globtier Infotech Limited Attachments Annexure I.pdf Content " +
    "Trading Members are informed that effective from Tuesday, September 02, 2025, the Equity Shares of " +
    "&ldquo;Globtier Infotech limited&rdquo; shall be listed and admitted to dealings. " +
    "Name of the company Globtier Infotech limited Registered Office Noida Scrip Code 544494 " +
    "Market Lot 1,600 Issue Price for the current Public issue Rs. 72",
    candidate,
    "2026-09-24T00:00:00Z"
  );
  assert.equal(checked.status, "verified");
  assert.equal(checked.observed_identity.issuer_name, "Globtier Infotech limited");
  assert.equal(checked.facts.market_lot.value, 1600);
  assert.equal(checked.facts.issue_price.value, 72);
}


{
  const candidate = {
    issuer_name: "PIOTEX INDUSTRIES LIMITED",
    bse_scrip_code: "544178",
    listing_notice_no: "20240516-37",
    listing_date: "2024-05-17",
    listing_notice_url: listingUrl("20240516-37")
  };
  const source =
    "Notice No. 20240516-37 Notice Date 16 May 2024 Category Company related Segment SME " +
    "Subject Listing of Equity Shares of PIOTEX INDUSTRIES LIMITED Attachments Annexure I.pdf Content " +
    "Trading Members are hereby informed that effective from Friday, May 17, 2024, the Equity Shares of " +
    "PIOTEX INDUSTRIES LIMITED shall be listed and admitted Name of the company PIOTEX INDUSTRIES LIMITED " +
    "Registered Office Pune Scrip Code 544178 Issue Price for the current Public issue Rs. 94/- per share " +
    "Trades effected in this scrip will be in minimum market lot (i.e.1200equity shares) and the same shall be modified.";
  const checked = verifyListingHtml(source, candidate, "2026-09-24T00:00:00Z");
  assert.equal(checked.status, "verified");
  assert.equal(checked.facts.market_lot.value, 1200);
  assert.match(checked.facts.market_lot.source_value, /minimum market lot/i);
  assert.equal(checked.facts.issue_price.value, 94);
  assert.equal(
    verifyListingHtml(source + " Market Lot 1000", candidate, "2026-09-24T00:00:00Z").status,
    "rejected",
    "conflicting standard and minimum-market-lot clauses must fail closed"
  );
}

{
  const candidate = {
    issuer_name: "Neopolitan Pizza and Foods Ltd",
    bse_scrip_code: "544269",
    listing_notice_no: "20241008-60",
    listing_date: "2024-10-09",
    listing_notice_url: listingUrl("20241008-60")
  };
  const source =
    "Notice No. 20241008-60 Notice Date 08 Oct 2024 Category Company related Segment SME " +
    "Subject Listing of Equity Shares of NEOPOLITAN PIZZA AND FOODS LIMITED (Formerly Known as Neopolitan Pizza Limited) " +
    "Attachments Annexure I.pdf Content Trading Members are hereby informed that effective from Wednesday, October 09, 2024, " +
    "the Equity Shares of NEOPOLITAN PIZZA AND FOODS LIMITED (Formerly Known as Neopolitan Pizza Limited) shall be listed and admitted " +
    "Name of the company NEOPOLITAN PIZZA AND FOODS LIMITED (Formerly Known as Neopolitan Pizza Limited) Registered Office Vadodara " +
    "Scrip Code 544269 Market Lot 6000 Issue Price for the current Public issue Rs. 20/- per share";
  const checked = verifyListingHtml(source, candidate, "2026-09-24T00:00:00Z");
  assert.equal(checked.status, "verified");
  assert.equal(
    checked.observed_identity.issuer_name,
    "NEOPOLITAN PIZZA AND FOODS LIMITED (Formerly Known as Neopolitan Pizza Limited)"
  );
  assert.equal(checked.facts.market_lot.value, 6000);
  assert.equal(checked.facts.issue_price.value, 20);
  assert.equal(
    verifyListingHtml(source, { ...candidate, issuer_name: "Neopolitan Pizza Limited" }, "2026-09-24T00:00:00Z").status,
    "rejected",
    "former legal name must not replace the current issuer identity"
  );
}


{
  const city = {
    issuer_name: "CITY CROPS AGRO LIMITED",
    bse_scrip_code: "544000",
    listing_notice_no: "20231009-25",
    listing_date: "2023-10-10",
    listing_notice_url: listingUrl("20231009-25")
  };
  const source =
    "Notice No. 20231009-25 Notice Date 09 Oct 2023 Category Company related Segment SME " +
    "Subject Listing of Equity Shares of CITY CROPS AGRO LIMITED Attachments Annexure II.pdf Content " +
    "Trading Members are hereby informed that effective from Tuesday, October 10, 2023, the Equity Shares of " +
    "CITY CROPS AGRO LIMITED shall be listed and admitted to dealings. Name of the company CITY CROPS AGRO LIMITED " +
    "Registered & Corporate Office Registered Office: Ahmedabad Scrip Code 544000 Market Lot 6000 " +
    "Issue Price for the current Public issue Rs. 25/- per share";
  const checked = verifyListingHtml(source, city, "2026-09-24T00:00:00Z");
  assert.equal(checked.status, "verified");
  assert.equal(checked.observed_identity.issuer_name, "CITY CROPS AGRO LIMITED");
  assert.equal(checked.facts.market_lot.value, 6000);
  assert.equal(checked.facts.issue_price.value, 25);
}
