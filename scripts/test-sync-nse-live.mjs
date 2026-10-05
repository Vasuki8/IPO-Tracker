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
assert.equal(
  merged[0].__field_sources.issuePrice,
  "https://www.nseindia.com/api/all-upcoming-issues?category=ipo",
  "price provenance must remain attached to the endpoint that supplied the price"
);
assert.equal(
  merged[0].__field_sources.status,
  "https://www.nseindia.com/api/ipo-current-issue",
  "status provenance must follow the endpoint that supplied the status"
);
assert.deepEqual(merged[0].__source_urls, [
  "https://www.nseindia.com/api/all-upcoming-issues?category=ipo",
  "https://www.nseindia.com/api/ipo-current-issue"
]);

const provenanceRecord = buildNewRecoveryRecord(merged[0], "2026-09-22T03:31:00Z");
assert.equal(
  provenanceRecord.price_band.source.url,
  "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
);
assert.equal(
  provenanceRecord.status_evidence[0].url,
  "https://www.nseindia.com/api/ipo-current-issue"
);
assert.ok(provenanceRecord.documents.some((doc) => doc.url === "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"));
assert.ok(provenanceRecord.documents.some((doc) => doc.url === "https://www.nseindia.com/api/ipo-current-issue"));

const disagreeing = mergeFeeds(
  [{
    companyName: "Conflict Limited",
    issueStartDate: "23-Sep-2026",
    issueEndDate: "25-Sep-2026",
    issuePrice: "Rs.100 to Rs.110",
    series: "EQ",
    status: "Forthcoming",
    symbol: "CONFLICT"
  }],
  [{
    companyName: "Conflict Limited",
    issueStartDate: "23-Sep-2026",
    issueEndDate: "25-Sep-2026",
    issuePrice: "Rs.120 to Rs.130",
    series: "EQ",
    status: "Active",
    symbol: "CONFLICT"
  }]
)[0];
assert.equal(disagreeing.__field_conflicts.issuePrice.length, 2);
const conflictRecord = buildNewRecoveryRecord(disagreeing, "2026-09-22T03:32:00Z");
assert.equal(conflictRecord.price_band.status, "conflict");
assert.deepEqual(conflictRecord.price_band.value, { min: 120, max: 130 });
assert.equal(conflictRecord.price_band.additional_sources.length, 1);
assert.equal(conflictRecord.price_band.corrections[0].kind, "official_live_feed_disagreement");
assert.equal(conflictRecord.price_band.corrections[0].status, "unresolved");

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

const amendedBand = structuredClone(liveRecord);
const originalBandEvidence = structuredClone(amendedBand.price_band.source);
assert.equal(enrichExistingRecord(amendedBand, {
  companyName: "Live Recovery Limited",
  issueStartDate: "24-Sep-2026",
  issueEndDate: "29-Sep-2026",
  issuePrice: "Rs.325 to Rs.340",
  lotSize: "50",
  series: "EQ",
  status: "Active",
  symbol: "LIVE",
  __source_url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
}, "2026-09-23T04:00:00Z"), true);
assert.deepEqual(amendedBand.price_band.value, { min: 325, max: 340 });
assert.deepEqual(amendedBand.terms.price_band, { min: 325, max: 340 });
assert.equal(amendedBand.market_lot.value, 50);
assert.equal(amendedBand.terms.market_lot, 50);
assert.equal(amendedBand.close_date.value, "2026-09-29");
assert.equal(amendedBand.terms.close_date, "2026-09-29");
assert.deepEqual(amendedBand.price_band.corrections.at(-1).previous_value, { min: 300, max: 320 });
assert.equal(amendedBand.price_band.corrections.at(-1).reason.includes("Later official NSE live-feed observation"), true);
assert.ok(amendedBand.price_band.additional_sources.some((item) => item.url === originalBandEvidence.url));
assert.equal(
  enrichExistingRecord(amendedBand, {
    companyName: "Live Recovery Limited",
    issueStartDate: "24-Sep-2026",
    issueEndDate: "29-Sep-2026",
    issuePrice: "Rs.325 to Rs.340",
    lotSize: "50",
    series: "EQ",
    status: "Active",
    symbol: "LIVE",
    __source_url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
  }, "2026-09-23T04:00:00Z"),
  false,
  "replaying the same amended live observation must be idempotent"
);

const fixedRecord = buildNewRecoveryRecord({
  companyName: "Fixed Price Limited",
  issueStartDate: "23-Sep-2026",
  issueEndDate: "25-Sep-2026",
  issuePrice: "Rs.125",
  series: "EQ",
  status: "Forthcoming",
  symbol: "FIXED",
  __source_url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
}, "2026-09-22T03:33:00Z");
assert.equal(enrichExistingRecord(fixedRecord, {
  companyName: "Fixed Price Limited",
  issueStartDate: "23-Sep-2026",
  issueEndDate: "25-Sep-2026",
  issuePrice: "Rs.130",
  series: "EQ",
  status: "Active",
  symbol: "FIXED",
  __source_url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
}, "2026-09-23T03:33:00Z"), true);
assert.equal(fixedRecord.issue_price.value, 130);
assert.equal(fixedRecord.issue_price.corrections.at(-1).previous_value, 125);

console.log("NSE live sync parser, amendment retention and per-field provenance tests passed.");

for(const liveStatus of ["Closed","Forthcoming","Active"]){
 const listedRecord={...structuredClone(liveRecord),status:"listed",status_evidence:[{url:"https://www.nseindia.com/api/public-past-issues",document_type:"NSE Public Past Issues",document_identity:"NSE Public Past Issues — LIVE",publication_date:null,collected_at:"2026-09-29T00:00:00Z"}]};
 const priorEvidence=structuredClone(listedRecord.status_evidence[0]);
 assert.equal(enrichExistingRecord(listedRecord,{companyName:"Live Recovery Limited",symbol:"LIVE",series:"EQ",status:liveStatus},"2026-09-30T00:00:00Z"),true);
 assert.equal(listedRecord.status,"listed","Live "+liveStatus+" must not demote a listed issuer");
 assert.deepEqual(listedRecord.status_evidence[0],priorEvidence);
 assert.equal(listedRecord.status_evidence.length,2,"Live observation evidence remains available");
 assert.equal(enrichExistingRecord(listedRecord,{companyName:"Live Recovery Limited",symbol:"LIVE",series:"EQ",status:liveStatus},"2026-09-30T00:00:00Z"),false);
}
console.log("Live IPO feed preserves listed lifecycle status and retains observations.");

// Run admission/identity regressions in the existing collector CI entrypoint.
await import('./test-live-identity-safety.mjs');
