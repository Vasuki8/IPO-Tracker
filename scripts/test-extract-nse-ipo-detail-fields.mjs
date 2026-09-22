import assert from "node:assert/strict";
import {
  applyIssueSize,
  applyListingDate,
  applyMinimumBid,
  issuePriceCandidatesFromIpoDetail,
  issueSizeCandidatesFromIpoDetail,
  parseIssueSizeInrFromIpoDetail,
  listingDateCandidatesFromIpoDetail,
  applyPriceBand,
  parseListingDateFromIpoDetail,
  parseMinimumBidFromIpoDetail,
  parsePriceBandFromIpoDetail,
  priceBandCandidatesFromIpoDetail,
  resolveNseIdentity
} from "./extract-nse-ipo-detail-fields.mjs";

const pureFreshLakhs = parseIssueSizeInrFromIpoDetail({
  issueInfo: {
    dataList: [{
      title: "Issue Size",
      value: "Initial Public offering comprising of fresh issue aggregating up to Rs. 30,000 Lakhs (including Anchor portion of 10,65,000 Equity Shares)"
    }]
  }
});
assert.equal(pureFreshLakhs.value, 3_000_000_000);

const pureFreshMillion = parseIssueSizeInrFromIpoDetail({
  issueInfo: {
    dataList: [{
      title: "Issue Size",
      value: "Initial Public offer comprising of Fresh issue aggregating up to Rs. 21,000 million (Including Anchor reservation portion of 2,61,04,972 equity shares)"
    }]
  }
});
assert.equal(pureFreshMillion.value, 21_000_000_000);

const mixedUnitsRejected = parseIssueSizeInrFromIpoDetail({
  issueInfo: {
    dataList: [{
      title: "Issue Size",
      value: "Initial Public offer comprising of Fresh issue aggregating up to Rs. 12,850 Lakhs and Offer for Sale of upto 17,50,000 Equity Shares"
    }]
  }
});
assert.equal(mixedUnitsRejected.value, null);
assert.equal(mixedUnitsRejected.reason, "no_safe_overall_inr_total");

const shareCountRejected = parseIssueSizeInrFromIpoDetail({
  issueInfo: {
    dataList: [{
      title: "Issue Size",
      value: "Initial Public Offer comprising of Fresh Issue up to 93,98,000 Equity Shares"
    }]
  }
});
assert.equal(shareCountRejected.value, null);

const issueSizeCandidates = issueSizeCandidatesFromIpoDetail({
  issueInfo: {
    dataList: [
      { title: "Issue Size", value: "Rs. 500 million" },
      { title: "Fresh Issue Size", value: "Rs. 300 million" },
      { title: "Market Lot", value: "1,000 Equity Shares" }
    ]
  }
});
assert.deepEqual(issueSizeCandidates, [
  { title: "Issue Size", value: "Rs. 500 million" }
]);

assert.deepEqual(
  issueSizeCandidatesFromIpoDetail({
    issueInfo: {
      dataList: [
        { title: "Total Issue Size", value: "10,00,000 Equity Shares" },
        { title: "Offer Size", value: "Rs. 250 crore" }
      ]
    }
  }),
  [
    { title: "Total Issue Size", value: "10,00,000 Equity Shares" },
    { title: "Offer Size", value: "Rs. 250 crore" }
  ]
);

assert.deepEqual(
  issueSizeCandidatesFromIpoDetail({
    issueInfo: { dataList: [{ title: "Fresh Issue Size", value: "Rs. 100 crore" }] }
  }),
  []
);

const issuePriceCandidates = issuePriceCandidatesFromIpoDetail({
  issueInfo: {
    dataList: [
      { title: "Issue Price", value: "Rs.139 per Equity Share" },
      { title: "Price Range", value: "Rs.132 to Rs.139 per Equity Share" }
    ]
  },
  metaInfo: {
    finalIssuePrice: "139"
  }
});
assert.deepEqual(issuePriceCandidates, [
  {
    source: "issueInfo.dataList",
    title: "Issue Price",
    value: "Rs.139 per Equity Share"
  },
  {
    source: "metaInfo",
    title: "finalIssuePrice",
    value: "139"
  }
]);

assert.deepEqual(
  issuePriceCandidatesFromIpoDetail({
    issueInfo: { dataList: [{ title: "Price Range", value: "Rs.132 to Rs.139 per Equity Share" }] }
  }),
  []
);

const axiomBand = parsePriceBandFromIpoDetail({
  issueInfo: {
    dataList: [
      { title: "Price Range", value: "Rs.51 to Rs.54 per equity share" }
    ]
  }
});
assert.deepEqual(axiomBand.value, { min: 51, max: 54 });
assert.equal(axiomBand.source_title, "Price Range");

assert.deepEqual(
  parsePriceBandFromIpoDetail({
    issueInfo: {
      dataList: [{ title: "Price Range", value: "Rs. 601/- to Rs. 632/- per Equity Share" }]
    }
  }).value,
  { min: 601, max: 632 }
);

assert.equal(
  parsePriceBandFromIpoDetail({
    issueInfo: { dataList: [{ title: "Price Range", value: "Rs.94 per equity share" }] }
  }).value,
  null
);

assert.equal(
  parsePriceBandFromIpoDetail({
    issueInfo: {
      dataList: [
        { title: "Price Range", value: "Rs.51 to Rs.54 per equity share" },
        { title: "Price Band", value: "Rs.52 to Rs.54 per equity share" }
      ]
    }
  }).reason,
  "official_term_conflict"
);

const priceBandCandidates = priceBandCandidatesFromIpoDetail({
  issueInfo: {
    dataList: [
      { title: "Price Range", value: "₹ 120 to ₹ 127 per Equity Share" },
      { title: "Market Lot", value: "1,000 Equity Shares" }
    ]
  }
});
assert.deepEqual(priceBandCandidates, [
  { title: "Price Range", value: "₹ 120 to ₹ 127 per Equity Share" }
]);

assert.deepEqual(
  priceBandCandidatesFromIpoDetail({
    issueInfo: { dataList: [{ title: "Price Band", value: "₹100 - ₹105" }] }
  }),
  [{ title: "Price Band", value: "₹100 - ₹105" }]
);

assert.deepEqual(
  priceBandCandidatesFromIpoDetail({
    issueInfo: { dataList: [{ title: "Issue Price", value: "₹127" }] }
  }),
  []
);

const listingDate = parseListingDateFromIpoDetail({
  metaInfo: { listingDate: "2026-09-17" }
});
assert.equal(listingDate.value, "2026-09-17");
assert.equal(listingDate.source_key, "listingDate");

assert.equal(
  parseListingDateFromIpoDetail({ metaInfo: { listingDate: "17-Sep-2026" } }).value,
  null
);
assert.equal(
  parseListingDateFromIpoDetail({ metaInfo: { listingDate: "2026-02-30" } }).value,
  null
);
assert.equal(
  parseListingDateFromIpoDetail({ metaInfo: { issueEndDate: "2026-09-17" } }).value,
  null
);

const listingDateCandidates = listingDateCandidatesFromIpoDetail({
  metaInfo: {
    symbol: "EXAMPLE",
    listingDate: "2026-09-30",
    industry: "Example"
  }
});
assert.deepEqual(listingDateCandidates, [
  { key: "listingDate", value: "2026-09-30" }
]);

assert.deepEqual(
  listingDateCandidatesFromIpoDetail({
    metaInfo: { dateOfListing: "30-Sep-2026" }
  }),
  [{ key: "dateOfListing", value: "30-Sep-2026" }]
);

assert.deepEqual(
  listingDateCandidatesFromIpoDetail({ metaInfo: { issueEndDate: "2026-09-25" } }),
  []
);

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

const directIdentity = resolveNseIdentity({
  nse_symbol: "EXAMPLE",
  nse_series: "EQ"
});
assert.deepEqual(directIdentity, {
  symbol: "EXAMPLE",
  series: "EQ",
  source: "retained_fields"
});

const legacyIdentity = resolveNseIdentity({
  nse_source: {
    url: "https://www.nseindia.com/market-data/issue-information?series=SME&symbol=QUALIANCE&type=Active"
  },
  documents: []
});
assert.deepEqual(legacyIdentity, {
  symbol: "QUALIANCE",
  series: "SME",
  source: "retained_official_url"
});

assert.equal(
  resolveNseIdentity({
    nse_source: { url: "https://example.com/?symbol=BAD&series=EQ" }
  }),
  null
);

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

assert.equal(
  applyIssueSize(
    record,
    {
      value: 3_000_000_000,
      source_value: "Initial Public offering comprising of fresh issue aggregating up to Rs. 30,000 Lakhs",
      source_title: "Issue Size"
    },
    "https://www.nseindia.com/api/ipo-detail?symbol=EXAMPLE&series=EQ",
    "2026-10-04T12:20:00Z"
  ),
  true
);
assert.equal(record.issue_size_inr.value, 3_000_000_000);
assert.equal(record.issue_size_inr.status, "verified");
assert.equal(record.issue_size_inr.source.document_type, "NSE Issue Information API");
assert.equal(record.documents.length, 1);

assert.equal(
  applyIssueSize(
    record,
    {
      value: 3_100_000_000,
      source_value: "Rs. 31,000 Lakhs",
      source_title: "Issue Size"
    },
    "https://www.nseindia.com/api/ipo-detail?symbol=EXAMPLE&series=EQ",
    "2026-10-05T12:20:00Z"
  ),
  false
);
assert.equal(record.issue_size_inr.value, 3_000_000_000);

assert.equal(
  applyPriceBand(
    record,
    {
      value: { min: 51, max: 54 },
      source_value: "Rs.51 to Rs.54 per equity share",
      source_title: "Price Range"
    },
    "https://www.nseindia.com/api/ipo-detail?symbol=EXAMPLE&series=EQ",
    "2026-10-04T12:30:00Z"
  ),
  true
);
assert.deepEqual(record.price_band.value, { min: 51, max: 54 });
assert.equal(record.price_band.status, "verified");
assert.equal(record.price_band.source.document_type, "NSE Issue Information API");
assert.equal(record.documents.length, 1);

assert.equal(
  applyPriceBand(
    record,
    {
      value: { min: 52, max: 54 },
      source_value: "Rs.52 to Rs.54 per equity share",
      source_title: "Price Range"
    },
    "https://www.nseindia.com/api/ipo-detail?symbol=EXAMPLE&series=EQ",
    "2026-10-05T12:30:00Z"
  ),
  false
);
assert.deepEqual(record.price_band.value, { min: 51, max: 54 });

assert.equal(
  applyListingDate(
    record,
    { value: "2026-10-01", source_value: "2026-10-01", source_key: "listingDate" },
    "https://www.nseindia.com/api/ipo-detail?symbol=EXAMPLE&series=EQ",
    "2026-10-02T12:30:00Z"
  ),
  true
);
assert.equal(record.listing_date.value, "2026-10-01");
assert.equal(record.listing_date.status, "verified");
assert.equal(record.listing_date.source.document_type, "NSE Issue Information API");
assert.equal(record.documents.length, 1);

assert.equal(
  applyListingDate(
    record,
    { value: "2026-10-02", source_value: "2026-10-02", source_key: "listingDate" },
    "https://www.nseindia.com/api/ipo-detail?symbol=EXAMPLE&series=EQ",
    "2026-10-03T12:30:00Z"
  ),
  false
);
assert.equal(record.listing_date.value, "2026-10-01");

const legacyRecord = {
  issuer_name: "Legacy Limited",
  nse_symbol: null,
  nse_series: null,
  nse_source: {
    url: "https://www.nseindia.com/market-data/issue-information?series=SME&symbol=LEGACY&type=Past"
  },
  terms: { minimum_bid_quantity: null },
  documents: []
};

assert.equal(
  applyMinimumBid(
    legacyRecord,
    { value: 500, source_value: "500 Equity Shares", source_title: "Minimum Order Quantity" },
    "https://www.nseindia.com/api/ipo-detail?symbol=LEGACY&series=SME",
    "2026-09-22T12:30:00Z"
  ),
  true
);
assert.equal(legacyRecord.nse_symbol, "LEGACY");
assert.equal(legacyRecord.nse_series, "SME");
assert.equal(legacyRecord.minimum_bid_quantity.value, 500);

console.log("NSE ipo-detail minimum-bid extraction tests passed.");
