import assert from "node:assert/strict";
import { validateOperatorHistory, validateOperatorSnapshot, validatePagesPublication } from "./validate-operator-state.mjs";

const snapshot = {
  schema_version: "1.0.0",
  generated_at: "2026-09-23T15:00:00Z",
  run: { id: "1", commit_sha: "abc" },
  health: { overall: "healthy", reasons: [] },
  recovery_guidance: [],
  pipeline: { collection_health: "collection_success", stages: { rebuild: "success" } },
  freshness: { dataset_generated_at: "2026-09-23T14:59:00Z" },
  pages_publication: { latest_attempt_status: "success" }
};
assert.deepEqual(validateOperatorSnapshot(snapshot), []);
assert.ok(validateOperatorSnapshot({ ...snapshot, health: { overall: "banana", reasons: [] } }).some((e) => e.includes("overall")));
assert.ok(validateOperatorSnapshot({ ...snapshot, generated_at: null }).some((e) => e.includes("generated_at")));

const history = {
  schema_version: "1.0.0",
  max_entries: 48,
  entries: [{
    observed_at: "2026-09-23T14:00:00Z",
    last_observed_at: "2026-09-23T15:00:00Z",
    overall: "healthy",
    reasons: [],
    observations: 2
  }]
};
assert.deepEqual(validateOperatorHistory(history), []);
assert.ok(validateOperatorHistory({ ...history, max_entries: 0 }).some((e) => e.includes("max_entries")));
assert.ok(validateOperatorHistory({ ...history, entries: [{ ...history.entries[0], observations: 0 }] }).some((e) => e.includes("observations")));

console.log("Operator state validation tests passed.");

const pages = {
  schema_version: "1.0.0",
  latest_attempt: {
    status: "success", workflow_run_id: "10", commit_sha: "abc",
    completed_at: "2026-09-23T15:00:00Z"
  },
  last_successful: {
    status: "success", workflow_run_id: "10", commit_sha: "abc",
    completed_at: "2026-09-23T15:00:00Z"
  }
};
assert.deepEqual(validatePagesPublication(pages), []);
assert.ok(validatePagesPublication({ ...pages, latest_attempt: { ...pages.latest_attempt, status: "banana" } }).some((e) => e.includes("status")));
