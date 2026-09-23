import assert from "node:assert/strict";
import { buildOperatorReport, latestTimestamp, renderMarkdown, verifiedLotSize } from "./operator-report.mjs";

assert.equal(latestTimestamp([null, "2026-09-22T01:00:00Z", "2026-09-23T01:00:00Z"]), "2026-09-23T01:00:00Z");
assert.equal(verifiedLotSize({ market_lot: { value: 120, status: "verified" }, minimum_bid_quantity: { value: 60, status: "verified" } }), 120);
assert.equal(verifiedLotSize({ market_lot: { value: 120, status: "provisional" }, minimum_bid_quantity: { value: 60, status: "verified" } }), 60);
assert.equal(verifiedLotSize({ market_lot: { value: null, status: "missing" }, minimum_bid_quantity: { value: 60, status: "conflict" } }), null);

const fixture = {
  schema_version: "1.2.0",
  generated_at: "2026-09-23T03:00:00Z",
  collection_started_at: "2026-09-22T02:00:00Z",
  records: [
    {
      first_observed_at: "2026-09-22T04:00:00Z", last_collected_at: "2026-09-23T02:30:00Z",
      market_lot: { value: 40, status: "verified", evidence: [{ collected_at: "2026-09-23T02:00:00Z" }] },
      minimum_bid_quantity: { value: 40, status: "verified", evidence: [] },
      price_band: { value: { min: 10, max: 12 }, status: "verified", evidence: [] },
      issue_price: { value: null, status: "missing", evidence: [] },
      issue_size_inr: { value: null, status: "missing", evidence: [] },
      open_date: { value: "2026-09-23", status: "verified", evidence: [] },
      close_date: { value: "2026-09-25", status: "verified", evidence: [] },
      listing_date: { value: null, status: "missing", evidence: [] },
      board_evidence: [{ collected_at: "2026-09-23T02:10:00Z" }], status_evidence: [],
      documents: [{ collected_at: "2026-09-23T02:20:00Z" }]
    },
    {
      first_observed_at: "2026-09-23T01:00:00Z", last_collected_at: "2026-09-23T02:45:00Z",
      market_lot: { value: null, status: "missing", evidence: [] },
      minimum_bid_quantity: { value: 111, status: "verified", evidence: [{ collected_at: "2026-09-23T02:40:00Z" }] },
      price_band: { value: { min: 100, max: 110 }, status: "verified", evidence: [] },
      issue_price: { value: 110, status: "verified", evidence: [] },
      issue_size_inr: { value: 1000000000, status: "provisional", evidence: [] },
      open_date: { value: "2026-09-23", status: "verified", evidence: [] },
      close_date: { value: "2026-09-25", status: "verified", evidence: [] },
      listing_date: { value: "2026-10-01", status: "verified", evidence: [] },
      board_evidence: [], status_evidence: [], documents: []
    }
  ]
};

const pagesStatus = {\n  schema_version: "1.0.0",\n  latest_attempt: { status: "failure", completed_at: "2026-09-23T03:20:00Z", commit_sha: "bad", workflow_run_id: "122", page_url: null },\n  last_successful: { status: "success", completed_at: "2026-09-23T03:10:00Z", commit_sha: "good", workflow_run_id: "121", page_url: "https://vasuki8.github.io/IPO-Tracker/" }\n};\n\nconst report = buildOperatorReport(fixture, {
  NSE_COLLECTION_OUTCOME: "success", SEBI_COLLECTION_OUTCOME: "success",
  REBUILD_OUTCOME: "success", VALIDATION_OUTCOME: "success", REPOSITORY_PUBLISH_OUTCOME: "success",
  GITHUB_RUN_ID: "123", GITHUB_SHA: "abc", OPERATOR_REPORT_AT: "2026-09-23T03:30:00Z"
});
assert.equal(report.pipeline.collection_health, "collection_success");
assert.equal(report.dataset.records, 2);
assert.equal(report.dataset.lot_size.verified, 2);
assert.equal(report.dataset.lot_size.direct_market_lot, 1);
assert.equal(report.dataset.lot_size.verified_minimum_bid_fallback, 1);
assert.equal(report.dataset.field_coverage.issue_size_inr.non_verified, 1);
assert.equal(report.dataset.latest_record_collected_at, "2026-09-23T02:45:00Z");
assert.equal(report.dataset.latest_evidence_collected_at, "2026-09-23T02:40:00Z");\nassert.equal(report.pages_publication.latest_attempt_status, "failure");\nassert.equal(report.pages_publication.last_successful_at, "2026-09-23T03:10:00Z");\nassert.equal(report.pages_publication.last_successful_commit_sha, "good");

const failed = buildOperatorReport(fixture, { NSE_COLLECTION_OUTCOME: "failure", SEBI_COLLECTION_OUTCOME: "skipped", OPERATOR_REPORT_AT: "2026-09-23T03:30:00Z" });
assert.equal(failed.pipeline.collection_health, "collection_failure");

const markdown = renderMarkdown(report);
assert.match(markdown, /Collection health: \*\*collection_success\*\*/);
assert.match(markdown, /Verified Lot Size: \*\*2\/2\*\*/);
assert.match(markdown, /does \*\*not\*\* mean the source necessarily contains that value/);
assert.match(markdown, /GitHub Pages publication: \*\*not persisted by this sync workflow\*\*/);
console.log("Operator freshness report tests passed.");
