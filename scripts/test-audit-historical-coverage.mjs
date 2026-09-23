import assert from "node:assert/strict";
import { buildHistoricalCoverageAudit, summarizeHistoricalYear } from "./audit-historical-coverage.mjs";

const manifest = {
  records: [
    {
      board: "Mainboard",
      terms: {
        price_band: { min: 10, max: 12 },
        market_lot: null,
        minimum_bid_quantity: null,
        open_date: null,
        close_date: null
      },
      issue_price: { value: 12 },
      issue_size_inr: { value: null },
      listing_date: { value: "2025-01-10" },
      documents: [{ type: "BSE Listing Notice", url: "https://www.bseindia.com/example" }]
    },
    {
      board: "SME",
      terms: {
        price_band: null,
        market_lot: 1000,
        minimum_bid_quantity: 1000,
        open_date: "2025-02-01",
        close_date: "2025-02-03"
      },
      issue_price: { value: 50 },
      issue_size_inr: { value: null },
      listing_date: { value: "2025-02-10" },
      documents: [{ type: "SEBI RHP filing", url: "https://www.sebi.gov.in/example" }]
    }
  ]
};

const summary = summarizeHistoricalYear(2025, manifest, 3);
assert.equal(summary.records, 2);
assert.equal(summary.mainboard, 1);
assert.equal(summary.sme, 1);
assert.equal(summary.bse_verified_sources, 3);
assert.equal(summary.bse_attached_records, 1);
assert.equal(summary.sebi_attached_records, 1);
assert.deepEqual(summary.coverage, {
  price_band: 1,
  issue_price: 2,
  issue_size_inr: 0,
  market_lot: 1,
  minimum_bid_quantity: 1,
  open_date: 1,
  close_date: 1,
  listing_date: 2
});

const rows = buildHistoricalCoverageAudit(
  [2026, 2025, 2024],
  new Map([[2026, { records: [] }], [2025, manifest]]),
  [{ year: 2025 }, { year: 2025 }]
);
assert.equal(rows[0].status, "materialized");
assert.equal(rows[0].records, 0);
assert.equal(rows[1].records, 2);
assert.equal(rows[1].bse_verified_sources, 2);
assert.equal(rows[2].status, "universe_not_materialized");

console.log("Historical coverage audit tests passed.");
