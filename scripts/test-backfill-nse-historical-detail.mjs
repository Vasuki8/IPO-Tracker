import assert from "node:assert/strict";
import {
  applyHistoricalDetailPayload,
  historicalDetailCandidates,
  historicalDetailKey,
  missingHistoricalDetailFields
} from "./backfill-nse-historical-detail.mjs";

const record = {
  id: "alpha-limited",
  issuer_name: "Alpha Limited",
  nse_symbol: "ALPHA",
  nse_series: "EQ",
  nse_source: { document_type: "NSE Public Past Issues" },
  listing_date: { value: "2025-05-01" },
  terms: { price_band: null, market_lot: null, minimum_bid_quantity: null },
  documents: []
};
assert.deepEqual(missingHistoricalDetailFields(record), ["issue_price","price_band","market_lot","minimum_bid_quantity","issue_size_inr"]);
assert.equal(historicalDetailKey(record), "2025|alpha-limited");
assert.equal(historicalDetailCandidates([{record}], {issuers:{}}, 2026, 10).length, 1);

const payload = {
  issueInfo: {
    dataList: [
      { title: "Issue Price", value: "Rs.125 per Equity Share" },
      { title: "Price Range", value: "Rs.120 to Rs.125 per Equity Share" },
      { title: "Market Lot", value: "120 Equity Shares" },
      { title: "Minimum Order Quantity", value: "120 Equity Shares" },
      { title: "Issue Size", value: "Fresh Issue aggregating up to Rs. 500 crore" }
    ]
  }
};
const result = applyHistoricalDetailPayload(record, payload, "https://www.nseindia.com/api/ipo-detail?symbol=ALPHA&series=EQ", "2026-09-23T20:00:00Z");
assert.deepEqual(result.changed.sort(), ["issue_price","issue_size_inr","market_lot","minimum_bid_quantity","price_band"]);
assert.deepEqual(result.remaining, []);
assert.equal(result.reasons.issue_price, null);
assert.equal(result.reasons.price_band, null);
assert.equal(result.reasons.market_lot, null);
assert.equal(result.reasons.minimum_bid_quantity, null);
assert.equal(result.reasons.issue_size_inr, null);
assert.equal(record.issue_price.value,125);
assert.deepEqual(record.price_band.value, {min:120,max:125});
assert.equal(record.market_lot.value,120);
assert.equal(record.minimum_bid_quantity.value,120);
assert.equal(record.issue_size_inr.value,5_000_000_000);

const state={issuers:{[historicalDetailKey(record)]:{parser_version:"1.0.0",status:"extracted",last_attempted_at:"2026-09-23T20:00:00Z"}}};
assert.equal(historicalDetailCandidates([{record}],state,2026,10).length,0);
console.log("Historical NSE detail backfill tests passed.");

const missingRecord = {
  id: "missing-limited",
  issuer_name: "Missing Limited",
  nse_symbol: "MISSING",
  nse_series: "EQ",
  listing_date: { value: "2024-01-01" },
  terms: { price_band: null, market_lot: null, minimum_bid_quantity: null },
  documents: []
};
const missingResult = applyHistoricalDetailPayload(
  missingRecord,
  { issueInfo: { dataList: [] }, metaInfo: {} },
  "https://www.nseindia.com/api/ipo-detail?symbol=MISSING&series=EQ",
  "2026-09-23T20:00:00Z"
);
assert.equal(missingResult.reasons.issue_price, "term_absent");
assert.equal(missingResult.reasons.price_band, "term_absent");
assert.equal(missingResult.reasons.market_lot, "term_absent");
assert.equal(missingResult.reasons.issue_size_inr, "term_absent");
