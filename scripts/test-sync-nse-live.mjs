import assert from "node:assert/strict";
import {
  buildNewRecoveryRecord,
  mapBoard,
  mapNseStatus,
  mergeFeeds,
  parseIssuePrice,
  parseNseDate
} from "./sync-nse-live.mjs";

assert.equal(parseNseDate("22-Sep-2026"), "2026-09-22");
assert.equal(parseNseDate(""), null);

assert.deepEqual(parseIssuePrice("Rs.140 to Rs.148"), {
  kind: "band",
  value: { min: 140, max: 148 },
  raw: "Rs.140 to Rs.148"
});
assert.deepEqual(parseIssuePrice("₹125"), {
  kind: "fixed",
  value: 125,
  raw: "₹125"
});

assert.equal(mapNseStatus("Active"), "open");
assert.equal(mapNseStatus("Forthcoming"), "upcoming");
assert.equal(mapNseStatus("Closed"), "closed");
assert.equal(mapBoard("SME"), "SME");
assert.equal(mapBoard("EQ"), "Mainboard");

const merged = mergeFeeds(
  [{
    companyName: "Example Industries Limited",
    issueStartDate: "23-Sep-2026",
    issueEndDate: "25-Sep-2026",
    issuePrice: "Rs.100 to Rs.110",
    series: "EQ",
    status: "Forthcoming",
    symbol: "EXAMPLE"
  }],
  [{
    companyName: "Example Industries Limited",
    issueStartDate: "23-Sep-2026",
    issueEndDate: "25-Sep-2026",
    series: "EQ",
    status: "Active",
    symbol: "EXAMPLE",
    noOfTime: "1.25"
  }]
);

assert.equal(merged.length, 1);
assert.equal(merged[0].issuePrice, "Rs.100 to Rs.110");
assert.equal(merged[0].status, "Active");

const record = buildNewRecoveryRecord({
  companyName: "Example SME Limited",
  issueStartDate: "23-Sep-2026",
  issueEndDate: "25-Sep-2026",
  issuePrice: "Rs.74 to Rs.78",
  lotSize: "1600",
  series: "SME",
  status: "Forthcoming",
  symbol: "EXSME",
  __source_url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
}, "2026-09-22T03:30:00.000Z");

assert.equal(record.board, "SME");
assert.equal(record.status, "upcoming");
assert.deepEqual(record.terms.price_band, { min: 74, max: 78 });
assert.equal(record.terms.market_lot, 1600);
assert.equal(record.terms.minimum_bid_quantity, null);
assert.equal(record.issue_size_inr, undefined);
assert.equal(record.board_evidence.length, 1);
assert.equal(record.status_evidence.length, 1);

console.log("NSE live sync parser tests passed.");
