import assert from "node:assert/strict";
import {
  applyPastIssueListingDate,
  applyPastIssuePrice,
  parsePastIssuePrice,
  selectPastIssueRow
} from "./extract-nse-past-issues-fields.mjs";

assert.equal(parsePastIssuePrice(139), 139);
assert.equal(parsePastIssuePrice("   429"), 429);
assert.equal(parsePastIssuePrice("Rs.254"), 254);
assert.equal(parsePastIssuePrice("₹127 per Equity Share"), 127);
assert.equal(parsePastIssuePrice("Rs.132 to Rs.139"), null);
assert.equal(parsePastIssuePrice("[●]"), null);
assert.equal(parsePastIssuePrice("N/A"), null);

const record = {
  issuer_name: "Example Limited",
  nse_symbol: "EXAMPLE",
  nse_series: "EQ",
  listing_date: { value: "2026-09-17" },
  issue_price: undefined,
  documents: []
};

const row = {
  symbol: "EXAMPLE",
  company: "Example Limited",
  securityType: "EQ",
  listingDate: "17-SEP-2026",
  issuePrice: "139"
};

assert.equal(selectPastIssueRow(record, [row]).row, row);
assert.equal(
  selectPastIssueRow(record, [{ ...row, securityType: "SME" }]).reason,
  "series_mismatch"
);
assert.equal(
  selectPastIssueRow(record, [{ ...row, listingDate: "18-SEP-2026" }]).reason,
  "listing_date_mismatch"
);
assert.equal(
  selectPastIssueRow(record, [row, { ...row }]).reason,
  "ambiguous_symbol_match"
);
assert.equal(
  selectPastIssueRow(record, []).reason,
  "no_symbol_match"
);

assert.equal(
  applyPastIssuePrice(record, row, "2026-09-22T14:50:00Z"),
  true
);
assert.equal(record.issue_price.value, 139);
assert.equal(record.issue_price.status, "verified");
assert.equal(record.issue_price.source.document_type, "NSE Public Past Issues");
assert.equal(record.issue_price.source.url, "https://www.nseindia.com/api/public-past-issues");
assert.equal(record.documents.length, 1);

assert.equal(
  applyPastIssuePrice(record, { ...row, issuePrice: "140" }, "2026-09-22T14:51:00Z"),
  false
);
assert.equal(record.issue_price.value, 139);

console.log("NSE public-past-issues final-price extraction tests passed.");

const missingListing = {
  issuer_name: "Another Limited",
  nse_symbol: "ANOTHER",
  nse_series: "EQ",
  listing_date: { value: null },
  issue_price: { value: null },
  documents: []
};
const missingListingRow = {
  symbol: "ANOTHER",
  company: "Another Limited",
  securityType: "EQ",
  listingDate: "23-SEP-2026",
  issuePrice: "210"
};
assert.equal(
  applyPastIssueListingDate(missingListing, missingListingRow, "2026-09-23T15:30:00Z"),
  true
);
assert.equal(missingListing.listing_date.value, "2026-09-23");
assert.equal(missingListing.listing_date.status, "verified");
assert.equal(missingListing.listing_date.source.document_type, "NSE Public Past Issues");
assert.equal(
  applyPastIssuePrice(missingListing, missingListingRow, "2026-09-23T15:30:00Z"),
  true
);
assert.equal(missingListing.issue_price.value, 210);
assert.equal(missingListing.documents.length, 1);

const badListing = {
  issuer_name: "Bad Date Limited",
  nse_symbol: "BADDATE",
  nse_series: "EQ",
  listing_date: { value: null },
  documents: []
};
assert.equal(
  applyPastIssueListingDate(
    badListing,
    { symbol: "BADDATE", securityType: "EQ", listingDate: "not-a-date", issuePrice: "100" },
    "2026-09-23T15:30:00Z"
  ),
  false
);
assert.equal(badListing.listing_date.value, null);
