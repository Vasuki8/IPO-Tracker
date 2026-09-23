import assert from "node:assert/strict";
import { applyOfferDatePlan, buildOfferDatePlan } from "./reconcile-historical-offer-date-results.mjs";

const baseByYear = new Map([[2025, {
  records: [{
    id: "alpha",
    issuer_name: "Alpha Limited",
    terms: { open_date: null, close_date: null },
    listing_date: { value: "2025-12-10" }
  }]
}]]);

const plannedOpen = {
  value: "2025-12-03",
  source_value: "Bid Opening Date December 3, 2025",
  page: 1,
  status: "verified",
  source: {
    url: "https://www.sebi.gov.in/sebi_data/attachdocs/dec-2025/alpha.pdf",
    document_type: "SEBI Prospectus PDF",
    collected_at: "2026-09-23T20:00:00Z"
  }
};
const currentByYear = new Map([[2025, {
  records: [{
    id: "alpha",
    issuer_name: "Alpha Limited",
    terms: { open_date: null, close_date: null },
    open_date: plannedOpen,
    listing_date: { value: "2025-12-10" }
  }]
}]]);

const plan = buildOfferDatePlan(baseByYear, currentByYear, {
  issuers: {
    "2025|alpha": {
      last_attempted_at: "2026-09-23T20:00:00Z",
      status: "extracted"
    }
  }
});
assert.equal(plan.changes.length, 1);
assert.equal(plan.changes[0].fields.open_date.value, "2025-12-03");

const latestByYear = new Map([[2025, {
  records: [{
    id: "alpha",
    issuer_name: "Alpha Limited",
    terms: { open_date: null, close_date: null },
    minimum_bid_quantity: { value: 10 },
    listing_date: { value: "2025-12-10" }
  }]
}]]);
const cursor = { issuers: {} };
const stats = applyOfferDatePlan(latestByYear, cursor, plan);
assert.equal(stats.changed_records, 1);
assert.equal(stats.changed_fields, 1);
assert.equal(stats.conflicts, 0);
assert.equal(latestByYear.get(2025).records[0].open_date.value, "2025-12-03");
assert.equal(latestByYear.get(2025).records[0].minimum_bid_quantity.value, 10);
assert.equal(cursor.issuers["2025|alpha"].status, "extracted");

const conflictingLatest = new Map([[2025, {
  records: [{
    id: "alpha",
    issuer_name: "Alpha Limited",
    terms: { open_date: null, close_date: null },
    open_date: { value: "2025-12-04" }
  }]
}]]);
const conflictStats = applyOfferDatePlan(conflictingLatest, { issuers: {} }, plan);
assert.equal(conflictStats.changed_fields, 0);
assert.equal(conflictStats.conflicts, 1);
assert.equal(conflictingLatest.get(2025).records[0].open_date.value, "2025-12-04");

console.log("Historical offer-date reconciliation tests passed.");
