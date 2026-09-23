import assert from "node:assert/strict";
import { buildOperatorReport, buildRecoveryGuidance, classifyOperatorHealth, latestTimestamp, renderMarkdown, summarizeHealthHistory, verifiedLotSize } from "./operator-report.mjs";

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

const pagesStatus = {
  schema_version: "1.0.0",
  latest_attempt: { status: "failure", completed_at: "2026-09-23T03:20:00Z", commit_sha: "bad", workflow_run_id: "122", page_url: null },
  last_successful: { status: "success", completed_at: "2026-09-23T03:10:00Z", commit_sha: "good", workflow_run_id: "121", page_url: "https://vasuki8.github.io/IPO-Tracker/" }
};

const report = buildOperatorReport(fixture, {
  NSE_COLLECTION_OUTCOME: "success", SEBI_COLLECTION_OUTCOME: "success",
  REBUILD_OUTCOME: "success", VALIDATION_OUTCOME: "success", REPOSITORY_PUBLISH_OUTCOME: "success",
  GITHUB_RUN_ID: "123", GITHUB_SHA: "abc", OPERATOR_REPORT_AT: "2026-09-23T03:30:00Z"
}, pagesStatus, { now: "2026-09-23T03:30:00Z" });
assert.equal(report.pipeline.collection_health, "collection_success");
assert.equal(report.dataset.records, 2);
assert.equal(report.dataset.lot_size.verified, 2);
assert.equal(report.dataset.lot_size.direct_market_lot, 1);
assert.equal(report.dataset.lot_size.verified_minimum_bid_fallback, 1);
assert.equal(report.dataset.field_coverage.issue_size_inr.non_verified, 1);
assert.equal(report.dataset.latest_record_collected_at, "2026-09-23T02:45:00Z");
assert.equal(report.dataset.latest_evidence_collected_at, "2026-09-23T02:40:00Z");
assert.equal(report.pages_publication.latest_attempt_status, "failure");
assert.equal(report.pages_publication.last_successful_at, "2026-09-23T03:10:00Z");
assert.equal(report.pages_publication.last_successful_commit_sha, "good");
assert.equal(report.health.overall, "failure");
assert.deepEqual(report.health.reasons, ["pages_deployment_failure"]);
assert.equal(report.health.ages_hours.dataset_generated, 0.5);
assert.equal(report.health.ages_hours.pages_publication, 0.33);
assert.equal(report.recovery_guidance.length, 1);
assert.equal(report.recovery_guidance[0].reason, "pages_deployment_failure");
assert.equal(report.recovery_guidance[0].priority, "high");

const failed = buildOperatorReport(fixture, { NSE_COLLECTION_OUTCOME: "failure", SEBI_COLLECTION_OUTCOME: "skipped", OPERATOR_REPORT_AT: "2026-09-23T03:30:00Z" });
assert.equal(failed.pipeline.collection_health, "collection_failure");

const markdown = renderMarkdown(report);
assert.match(markdown, /Collection health: \*\*collection_success\*\*/);
assert.match(markdown, /Verified Lot Size: \*\*2\/2\*\*/);
assert.match(markdown, /does \*\*not\*\* mean the source necessarily contains that value/);
assert.match(markdown, /GitHub Pages latest attempt: \*\*failure\*\*/);
assert.match(markdown, /GitHub Pages last successful publication: 2026-09-23T03:10:00Z \(commit good\)/);
console.log("Operator freshness report tests passed.");

const healthy = classifyOperatorHealth(
  {
    dataset_generated_at: "2026-09-23T10:00:00Z",
    latest_record_collected_at: "2026-09-23T10:15:00Z",
    latest_evidence_collected_at: "2026-09-23T09:00:00Z"
  },
  { report_generated_at: "2026-09-23T11:00:00Z", collection_health: "collection_success" },
  { latest_attempt_status: "success", last_successful_at: "2026-09-23T10:30:00Z" }
);
assert.equal(healthy.overall, "healthy");
assert.deepEqual(healthy.reasons, []);

const stale = classifyOperatorHealth(
  {
    dataset_generated_at: "2026-09-23T06:00:00Z",
    latest_record_collected_at: "2026-09-23T06:00:00Z",
    latest_evidence_collected_at: "2026-09-22T09:00:00Z"
  },
  { report_generated_at: "2026-09-23T11:00:00Z", collection_health: "collection_success" },
  { latest_attempt_status: "success", last_successful_at: "2026-09-23T06:00:00Z" }
);
assert.equal(stale.overall, "stale");
assert.deepEqual(stale.reasons, ["stale_dataset", "stale_record_collection", "stale_evidence_collection", "stale_pages_publication"]);

const unknown = classifyOperatorHealth(
  { dataset_generated_at: null, latest_record_collected_at: null, latest_evidence_collected_at: null },
  { report_generated_at: "2026-09-23T11:00:00Z", collection_health: "not_measured" },
  { latest_attempt_status: "not_recorded", last_successful_at: null }
);
assert.equal(unknown.overall, "unknown");
assert.deepEqual(unknown.reasons, ["dataset_generated_time_missing", "record_collection_time_missing", "pages_publication_time_missing"]);

const staleGuidance = buildRecoveryGuidance(stale);
assert.deepEqual(staleGuidance.map((item) => item.reason), [
  "stale_dataset",
  "stale_record_collection",
  "stale_evidence_collection",
  "stale_pages_publication"
]);
assert.match(staleGuidance.find((item) => item.reason === "stale_evidence_collection").recovery, /Do not rerun solely because evidence is old/);

const failureGuidance = buildRecoveryGuidance({
  reasons: ["collection_failure", "pages_deployment_failure"]
});
assert.deepEqual(failureGuidance.map((item) => item.priority), ["high", "high"]);
assert.match(failureGuidance[0].diagnostic, /failed NSE\/SEBI collection step/);

const healthyGuidance = buildRecoveryGuidance({ reasons: [] });
assert.deepEqual(healthyGuidance, []);

const unknownGuidance = buildRecoveryGuidance({
  reasons: ["dataset_generated_time_missing", "record_collection_time_missing", "pages_publication_time_missing"]
});
assert.equal(unknownGuidance.length, 3);
assert.match(unknownGuidance[0].recovery, /rather than inventing a timestamp/);

const history = {
  schema_version: "1.0.0",
  max_entries: 48,
  entries: [
    {
      observed_at: "2026-09-23T08:00:00Z",
      last_observed_at: "2026-09-23T09:00:00Z",
      overall: "healthy",
      reasons: [],
      observations: 2,
      run_id: "1",
      last_run_id: "2"
    },
    {
      observed_at: "2026-09-23T10:00:00Z",
      last_observed_at: "2026-09-23T12:00:00Z",
      overall: "failure",
      reasons: ["collection_failure"],
      observations: 3,
      run_id: "3",
      last_run_id: "5"
    }
  ]
};
const recurrence = summarizeHealthHistory(history);
assert.equal(recurrence.recorded, true);
assert.equal(recurrence.transition_count, 2);
assert.equal(recurrence.current.overall, "failure");
assert.equal(recurrence.current.observations, 3);
assert.equal(recurrence.current.last_run_id, "5");
assert.equal(recurrence.recent_transitions.length, 2);

const noHistory = summarizeHealthHistory(null);
assert.equal(noHistory.recorded, false);
assert.equal(noHistory.transition_count, 0);
assert.equal(noHistory.current, null);

const reportWithHistory = buildOperatorReport(fixture, {
  NSE_COLLECTION_OUTCOME: "success", SEBI_COLLECTION_OUTCOME: "success",
  REBUILD_OUTCOME: "success", VALIDATION_OUTCOME: "success", REPOSITORY_PUBLISH_OUTCOME: "success",
  OPERATOR_REPORT_AT: "2026-09-23T12:00:00Z"
}, pagesStatus, { now: "2026-09-23T12:00:00Z" }, history);
const recurrenceMarkdown = renderMarkdown(reportWithHistory);
assert.match(recurrenceMarkdown, /Recurrence context/);
assert.match(recurrenceMarkdown, /Current retained state: \*\*failure\*\* across \*\*3\*\* consecutive observation/);
assert.match(recurrenceMarkdown, /collection_failure/);

const pipelineFailureDataset = {
  dataset_generated_at: "2026-09-23T10:30:00Z",
  latest_record_collected_at: "2026-09-23T10:30:00Z",
  latest_evidence_collected_at: "2026-09-23T10:30:00Z"
};
const pipelineFailurePages = { latest_attempt_status: "success", last_successful_at: "2026-09-23T10:30:00Z" };

const rebuildFailure = classifyOperatorHealth(
  pipelineFailureDataset,
  {
    report_generated_at: "2026-09-23T11:00:00Z",
    collection_health: "collection_success",
    stages: { rebuild: "failure", validation: "skipped", repository_publish: "skipped" }
  },
  pipelineFailurePages
);
assert.equal(rebuildFailure.overall, "failure");
assert.deepEqual(rebuildFailure.reasons, ["rebuild_failure"]);

const validationFailure = classifyOperatorHealth(
  pipelineFailureDataset,
  {
    report_generated_at: "2026-09-23T11:00:00Z",
    collection_health: "collection_success",
    stages: { rebuild: "success", validation: "failure", repository_publish: "skipped" }
  },
  pipelineFailurePages
);
assert.equal(validationFailure.overall, "failure");
assert.deepEqual(validationFailure.reasons, ["validation_failure"]);

const publicationFailure = classifyOperatorHealth(
  pipelineFailureDataset,
  {
    report_generated_at: "2026-09-23T11:00:00Z",
    collection_health: "collection_success",
    stages: { rebuild: "success", validation: "success", repository_publish: "failure" }
  },
  pipelineFailurePages
);
assert.equal(publicationFailure.overall, "failure");
assert.deepEqual(publicationFailure.reasons, ["repository_publication_failure"]);

const stageGuidance = buildRecoveryGuidance({
  reasons: ["rebuild_failure", "validation_failure", "repository_publication_failure"]
});
assert.deepEqual(stageGuidance.map((item) => item.priority), ["high", "high", "high"]);
assert.match(stageGuidance[0].diagnostic, /dataset rebuild step/);
assert.match(stageGuidance[1].recovery, /validation to pass/);
assert.match(stageGuidance[2].recovery, /without recollecting sources unless needed/);
