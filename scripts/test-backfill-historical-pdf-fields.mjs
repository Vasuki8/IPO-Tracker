import assert from "node:assert/strict";
import {
  applyHistoricalPdfFields,
  candidateHistoricalPdf,
  HISTORICAL_PDF_DOWNLOAD_MAX_SECONDS,
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
const rhp = {
  type: "SEBI RHP PDF",
  identity: "Example Limited - RHP — PDF",
  url: "https://www.sebi.gov.in/sebi_data/attachdocs/nov-2025/example-rhp.pdf",
  publication_date: "2025-11-28"
};
record.documents.push(rhp);

assert.equal(candidateHistoricalPdf(record, 2026), rhp);
assert.equal(historicalPdfCandidates([{record}], {issuers:{}}, 2026, 10).length, 1);

const finalOnlyRecord = {
  id: "final-only-limited",
  issuer_name: "Final Only Limited",
  listing_date: { value: "2025-12-10" },
  issue_price: { value: null },
  price_band: { value: { min: 120, max: 125 } },
  issue_size_inr: { value: null },
  market_lot: { value: 120 },
  minimum_bid_quantity: { value: 120 },
  terms: { price_band: null, market_lot: null, minimum_bid_quantity: null },
  documents: [record.documents[0], rhp]
};
assert.equal(candidateHistoricalPdf(finalOnlyRecord, 2026), record.documents[0]);

const rhpOnlyRecord = {
  ...finalOnlyRecord,
  id: "rhp-only-limited",
  issuer_name: "RHP Only Limited",
  documents: [rhp]
};
assert.equal(candidateHistoricalPdf(rhpOnlyRecord, 2026), rhp);

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

assert.equal(HISTORICAL_PDF_DOWNLOAD_MAX_SECONDS, 75);
