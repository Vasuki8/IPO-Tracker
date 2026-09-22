import assert from "node:assert/strict";
import {
  applyMinimumBid,
  parseMinimumBidFromIpoDetail
} from "./extract-nse-ipo-detail-fields.mjs";

const both = parseMinimumBidFromIpoDetail({
  issueInfo: {
    dataList: [
      { title: "Bid Lot", value: "70 Equity Shares and in multiples thereof" },
      { title: "Minimum Order Quantity", value: "70 Equity Shares" }
    ]
  }
});
assert.equal(both.value, 70);
assert.equal(both.source_title, "Minimum Order Quantity");

const onlyBidLot = parseMinimumBidFromIpoDetail({
  issueInfo: {
    dataList: [
      { title: "Bid Lot", value: "1,200 Equity Shares and in multiples thereof" }
    ]
  }
});
assert.equal(onlyBidLot.value, 1200);

const placeholder = parseMinimumBidFromIpoDetail({
  issueInfo: {
    dataList: [
      { title: "Bid Lot", value: "[●] Equity Shares and in multiples thereof" },
      { title: "Minimum Order Quantity", value: "[●] Equity Shares" }
    ]
  }
});
assert.equal(placeholder.value, null);
assert.equal(placeholder.reason, "placeholder_or_unparseable");

const conflict = parseMinimumBidFromIpoDetail({
  issueInfo: {
    dataList: [
      { title: "Bid Lot", value: "100 Equity Shares and in multiples thereof" },
      { title: "Minimum Order Quantity", value: "200 Equity Shares" }
    ]
  }
});
assert.equal(conflict.value, null);
assert.equal(conflict.reason, "official_term_conflict");

const unrelated = parseMinimumBidFromIpoDetail({
  issueInfo: {
    dataList: [
      { title: "Market Lot", value: "400 Equity Shares" },
      { title: "Issue Size", value: "₹500 million" }
    ]
  }
});
assert.equal(unrelated.value, null);
assert.equal(unrelated.reason, "term_absent");

const record = {
  issuer_name: "Example Limited",
  nse_symbol: "EXAMPLE",
  nse_series: "EQ",
  terms: { minimum_bid_quantity: null },
  documents: []
};
assert.equal(
  applyMinimumBid(
    record,
    { value: 70, source_value: "70 Equity Shares", source_title: "Minimum Order Quantity" },
    "https://www.nseindia.com/api/ipo-detail?symbol=EXAMPLE&series=EQ",
    "2026-09-22T12:30:00Z"
  ),
  true
);
assert.equal(record.minimum_bid_quantity.value, 70);
assert.equal(record.minimum_bid_quantity.status, "verified");
assert.equal(record.minimum_bid_quantity.source.document_type, "NSE Issue Information API");
assert.equal(record.documents.length, 1);

console.log("NSE ipo-detail minimum-bid extraction tests passed.");
