import assert from "node:assert/strict";
import { buildOperatorSnapshot, updateOperatorHealthHistory } from "./record-operator-snapshot.mjs";

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

const firstHistory = updateOperatorHealthHistory(null, snapshot, 3);
assert.equal(firstHistory.entries.length, 1);
assert.equal(firstHistory.entries[0].overall, "healthy");
assert.equal(firstHistory.entries[0].observations, 1);

const repeatedSnapshot = {
  ...snapshot,
  generated_at: "2026-09-23T15:02:00Z",
  run: { ...snapshot.run, id: "1000" }
};
const repeatedHistory = updateOperatorHealthHistory(firstHistory, repeatedSnapshot, 3);
assert.equal(repeatedHistory.entries.length, 1);
assert.equal(repeatedHistory.entries[0].observations, 2);
assert.equal(repeatedHistory.entries[0].last_run_id, "1000");
assert.equal(repeatedHistory.entries[0].last_observed_at, "2026-09-23T15:02:00Z");

const failedSnapshot = {
  ...snapshot,
  generated_at: "2026-09-23T16:02:00Z",
  run: { ...snapshot.run, id: "1001" },
  health: { ...snapshot.health, overall: "failure", reasons: ["collection_failure"] }
};
const failedHistory = updateOperatorHealthHistory(repeatedHistory, failedSnapshot, 3);
assert.equal(failedHistory.entries.length, 2);
assert.equal(failedHistory.entries[1].overall, "failure");
assert.deepEqual(failedHistory.entries[1].reasons, ["collection_failure"]);

let bounded = failedHistory;
for (let i = 0; i < 4; i += 1) {
  bounded = updateOperatorHealthHistory(bounded, {
    ...snapshot,
    generated_at: `2026-09-23T${17 + i}:02:00Z`,
    run: { ...snapshot.run, id: String(1100 + i) },
    health: { ...snapshot.health, overall: i % 2 ? "stale" : "unknown", reasons: [`reason_${i}`] }
  }, 3);
}
assert.equal(bounded.entries.length, 3);
assert.deepEqual(bounded.entries.map((entry) => entry.run_id), ["1101", "1102", "1103"]);
