import assert from "node:assert/strict";
import { buildOperatorSnapshot } from "./record-operator-snapshot.mjs";

const report = {
  dataset: {
    dataset_generated_at: "2026-09-23T14:00:00Z",
    collection_started_at: "2026-09-23T13:55:00Z",
    latest_record_collected_at: "2026-09-23T13:59:00Z",
    latest_evidence_collected_at: "2026-09-23T13:58:00Z"
  },
  pipeline: {
    report_generated_at: "2026-09-23T14:02:00Z",
    run_id: "999",
    run_attempt: "2",
    workflow: "Sync live IPO data",
    commit_sha: "abc",
    collection_health: "collection_success",
    stages: {
      nse_collection: "success",
      sebi_collection: "success",
      rebuild: "success",
      validation: "success",
      repository_publish: "success"
    }
  },
  pages_publication: {
    latest_attempt_status: "success",
    latest_attempt_at: "2026-09-23T14:01:00Z",
    last_successful_at: "2026-09-23T14:01:00Z",
    last_successful_commit_sha: "def"
  },
  health: {
    overall: "healthy",
    reasons: [],
    thresholds_hours: { dataset_generated: 3 },
    ages_hours: { dataset_generated: 0.03 }
  },
  recovery_guidance: []
};

const snapshot = buildOperatorSnapshot(report);
assert.equal(snapshot.schema_version, "1.0.0");
assert.equal(snapshot.generated_at, "2026-09-23T14:02:00Z");
assert.deepEqual(snapshot.run, {
  id: "999",
  attempt: "2",
  workflow: "Sync live IPO data",
  commit_sha: "abc"
});
assert.equal(snapshot.health.overall, "healthy");
assert.deepEqual(snapshot.recovery_guidance, []);
assert.equal(snapshot.pipeline.collection_health, "collection_success");
assert.equal(snapshot.freshness.dataset_generated_at, "2026-09-23T14:00:00Z");
assert.equal(snapshot.pages_publication.last_successful_commit_sha, "def");
assert.equal("records" in snapshot, false);
assert.equal("field_coverage" in snapshot, false);

console.log("Operator snapshot tests passed.");
