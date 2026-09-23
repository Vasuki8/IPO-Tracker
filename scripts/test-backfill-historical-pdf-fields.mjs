import assert from "node:assert/strict";
import {
  applyHistoricalPdfFields,
  candidateHistoricalPdf,
  historicalPdfCandidates,
  missingHistoricalPdfFields
} from "./backfill-historical-pdf-fields.mjs";

const record = {
  id: "example-limited",
  issuer_name: "Example Limited",
  listing_date: { value: "2025-12-10" },
  issue_price: { value: null },
  price_band: { value: null },
  issue_size_inr: { value: null },
  market_lot: { value: null },
  minimum_bid_quantity: { value: null },
  terms: { price_band: null, market_lot: null, minimum_bid_quantity: null },
  documents: [{
    type: "SEBI Prospectus PDF",
    identity: "Example Limited - Prospectus — PDF",
    url: "https://www.sebi.gov.in/sebi_data/attachdocs/dec-2025/example.pdf",
    publication_date: "2025-12-08"
  }]
};
assert.deepEqual(missingHistoricalPdfFields(record), ["issue_price","price_band","issue_size_inr","market_lot","minimum_bid_quantity"]);
assert.ok(candidateHistoricalPdf(record, 2026));
assert.equal(historicalPdfCandidates([{record}], {issuers:{}}, 2026, 10).length, 1);

const pages = [
  "Issue Price ₹125 per Equity Share. Price Band: ₹120 to ₹125 per Equity Share. Total Issue Size ₹500 crore. Market Lot: 120 Equity Shares. Bid Lot 120 Equity Shares."
];
const result = applyHistoricalPdfFields(record, record.documents[0], pages, "2026-09-23T20:00:00Z");
assert.deepEqual(result.changed.sort(), ["issue_price","issue_size_inr","market_lot","minimum_bid_quantity","price_band"]);
assert.equal(record.issue_price.value,125);
assert.deepEqual(record.price_band.value,{min:120,max:125});
assert.equal(record.issue_size_inr.value,5_000_000_000);
assert.equal(record.market_lot.value,120);
assert.equal(record.minimum_bid_quantity.value,120);
assert.equal(record.issue_size_inr.source.document_type,"SEBI Prospectus PDF");
assert.deepEqual(result.remaining,[]);

console.log("Historical SEBI PDF field backfill tests passed.");
