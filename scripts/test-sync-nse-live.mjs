import assert from "node:assert/strict";
import {
  buildNewRecoveryRecord,
  enrichExistingRecord,
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

const liveIssue = {
  companyName: "Manual Recovery Limited",
  issueStartDate: "23-Sep-2026",
  issueEndDate: "25-Sep-2026",
  issuePrice: "Rs.200 to Rs.220",
  lotSize: "50",
  series: "EQ",
  status: "Active",
  symbol: "MANUAL",
  __source_url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
};

const manualRecord = {
  id: "manual-recovery-limited",
  issuer_name: "Manual Recovery Limited",
  board: null,
  status: null,
  nse_source: {
    url: "https://www.nseindia.com/market-data/issue-information?series=EQ&symbol=MANUAL&type=Active",
    document_type: "NSE Issue Information",
    document_identity: "NSE Issue Information — MANUAL",
    publication_date: null,
    collected_at: "2026-09-21T00:00:00Z"
  },
  terms: {
    price_band: null,
    market_lot: null,
    minimum_bid_quantity: null,
    open_date: null,
    close_date: null
  },
  documents: [],
  board_evidence: [],
  status_evidence: []
};

assert.equal(enrichExistingRecord(manualRecord, liveIssue, "2026-09-22T04:00:00Z"), true);
assert.equal(manualRecord.board, "Mainboard");
assert.equal(manualRecord.status, "open");
assert.equal(manualRecord.terms.price_band, null);
assert.equal(manualRecord.terms.market_lot, null);
assert.equal(manualRecord.terms.open_date, null);
assert.equal(manualRecord.terms.close_date, null);

const liveRecord = buildNewRecoveryRecord({
  companyName: "Live Recovery Limited",
  issueStartDate: "",
  issueEndDate: "",
  issuePrice: "",
  series: "EQ",
  status: "Forthcoming",
  symbol: "LIVE",
  __source_url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
}, "2026-09-22T03:30:00Z");

assert.equal(enrichExistingRecord(liveRecord, {
  companyName: "Live Recovery Limited",
  issueStartDate: "24-Sep-2026",
  issueEndDate: "28-Sep-2026",
  issuePrice: "Rs.300 to Rs.320",
  lotSize: "45",
  series: "EQ",
  status: "Active",
  symbol: "LIVE",
  __source_url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
}, "2026-09-22T04:00:00Z"), true);
assert.deepEqual(liveRecord.terms.price_band, { min: 300, max: 320 });
assert.equal(liveRecord.terms.market_lot, 45);
assert.equal(liveRecord.terms.open_date, "2026-09-24");
assert.equal(liveRecord.terms.close_date, "2026-09-28");

console.log("NSE live sync parser and provenance tests passed.");
