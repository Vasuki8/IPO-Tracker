import assert from "node:assert/strict";
import { mergeHistoricalPdfFieldProposal } from "./apply-historical-pdf-field-state.mjs";

const record = {
  id: "alpha-limited",
  issuer_name: "Alpha Limited",
  listing_date: { value: "2025-12-10" },
  issue_price: { value: null },
  price_band: { value: null },
  issue_size_inr: { value: null },
  market_lot: { value: null },
  minimum_bid_quantity: { value: null },
  terms: { price_band: null, market_lot: null, minimum_bid_quantity: null },
  documents: []
};
const groups = [{ recovery: { records: [record] }, changed: false }];
const proposal = {
  issuers: {
    "2025|alpha-limited": {
      issuer_name: "Alpha Limited",
      listing_date: "2025-12-10",
      last_attempted_at: "2026-09-23T21:10:00Z",
      parser_version: "1.0.0",
      status: "extracted",
      extractions: {
        issue_price: { value: 125, source_value: "Issue Price ₹125 per Equity Share", page: 1 },
        price_band: { value: { min: 120, max: 125 }, source_value: "Price Band: ₹120 to ₹125 per Equity Share", page: 1 },
        issue_size_inr: { value: 5000000000, source_value: "₹500 crore", page: 2 },
        market_lot: { value: 120, source_value: "Market Lot: 120 Equity Shares", page: 2 },
        minimum_bid_quantity: { value: 120, source_value: "Bid Lot 120 Equity Shares", page: 3 }
      },
      document: {
        type: "SEBI Prospectus PDF",
        identity: "Alpha Prospectus — PDF",
        url: "https://www.sebi.gov.in/sebi_data/attachdocs/dec-2025/alpha.pdf",
        publication_date: "2025-12-08"
      }
    }
  }
};
const current = { issuers: {} };
const stats = mergeHistoricalPdfFieldProposal(groups, current, proposal);
assert.equal(stats.extracted_records, 1);
assert.equal(stats.extracted_fields, 5);
assert.equal(record.issue_price.value, 125);
assert.deepEqual(record.price_band.value, { min: 120, max: 125 });
assert.equal(record.issue_size_inr.value, 5000000000);
assert.equal(record.market_lot.value, 120);
assert.equal(record.minimum_bid_quantity.value, 120);
assert.equal(record.issue_size_inr.source.document_type, "SEBI Prospectus PDF");
assert.equal(groups[0].changed, true);

const concurrentRecord = {
  id: "beta-limited",
  issuer_name: "Beta Limited",
  listing_date: { value: "2024-11-10" },
  issue_price: { value: 99 },
  price_band: { value: { min: 95, max: 99 } },
  issue_size_inr: { value: 1000000000 },
  market_lot: { value: 50 },
  minimum_bid_quantity: { value: 50 },
  terms: { price_band: null, market_lot: null, minimum_bid_quantity: null },
  documents: []
};
const concurrentGroups = [{ recovery: { records: [concurrentRecord] }, changed: false }];
const concurrentProposal = {
  issuers: {
    "2024|beta-limited": {
      issuer_name: "Beta Limited",
      listing_date: "2024-11-10",
      last_attempted_at: "2026-09-23T21:10:00Z",
      parser_version: "1.0.0",
      status: "extracted",
      extractions: {
        issue_price: { value: 98, source_value: "Issue Price ₹98", page: 1 },
        price_band: { value: { min: 94, max: 98 }, source_value: "Price Band ₹94 to ₹98", page: 1 },
        issue_size_inr: { value: 900000000, source_value: "₹90 crore", page: 2 },
        market_lot: { value: 40, source_value: "Market Lot 40 Equity Shares", page: 2 },
        minimum_bid_quantity: { value: 40, source_value: "Bid Lot 40 Equity Shares", page: 3 }
      },
      document: {
        type: "SEBI RHP PDF",
        identity: "Beta RHP — PDF",
        url: "https://www.sebi.gov.in/sebi_data/attachdocs/nov-2024/beta.pdf",
        publication_date: "2024-11-01"
      }
    }
  }
};
const concurrentStats = mergeHistoricalPdfFieldProposal(concurrentGroups, { issuers: {} }, concurrentProposal);
assert.equal(concurrentStats.extracted_records, 0);
assert.equal(concurrentStats.already_present, 1);
assert.equal(concurrentRecord.issue_price.value, 99);
assert.deepEqual(concurrentRecord.price_band.value, { min: 95, max: 99 });
assert.equal(concurrentRecord.issue_size_inr.value, 1000000000);
assert.equal(concurrentRecord.market_lot.value, 50);
assert.equal(concurrentRecord.minimum_bid_quantity.value, 50);

console.log("Historical PDF field semantic merge tests passed.");
