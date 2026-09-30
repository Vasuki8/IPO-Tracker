import assert from "node:assert/strict";
import { test } from "node:test";
import { buildPagesPublicationStatus, emptyPagesPublicationStatus } from "./record-pages-publication.mjs";

const env = {
  PAGES_DEPLOY_OUTCOME: "success",
  PAGES_VERIFY_OUTCOME: "success",
  PAGES_DEPLOY_COMMIT_SHA: "actual-deployed-revision",
  PAGES_DEPLOY_COMPLETED_AT: "2026-09-23T05:00:00Z",
  PAGES_URL: "https://vasuki8.github.io/IPO-Tracker/",
  GITHUB_RUN_ID: "111",
  GITHUB_RUN_ATTEMPT: "1",
  GITHUB_WORKFLOW: "Deploy IPO Tracker to GitHub Pages",
  GITHUB_SHA: "upstream-workflow-revision"
};
const previous = { ...emptyPagesPublicationStatus(), last_successful: { status: "success", commit_sha: "previous-deployment" } };

test("verified deployment records the actual uploaded revision instead of workflow event SHA", () => {
  const result = buildPagesPublicationStatus(previous, env);
  assert.equal(result.latest_attempt.status, "success");
  assert.equal(result.latest_attempt.commit_sha, env.PAGES_DEPLOY_COMMIT_SHA);
  assert.equal(result.latest_attempt.completed_at, env.PAGES_DEPLOY_COMPLETED_AT);
  assert.equal(result.latest_attempt.workflow_run_id, "111");
  assert.deepEqual(result.last_successful, result.latest_attempt);
});

for (const outcome of ["failure", "cancelled", "skipped", "unknown"]) {
  test(`served verification ${outcome} preserves the last successful deployment`, () => {
    const result = buildPagesPublicationStatus(previous, { ...env, PAGES_VERIFY_OUTCOME: outcome });
    assert.equal(result.latest_attempt.status, outcome);
    assert.deepEqual(result.last_successful, previous.last_successful);
  });
}

test("missing verification outcome never marks a deployment successful", () => {
  const result = buildPagesPublicationStatus(previous, { ...env, PAGES_VERIFY_OUTCOME: undefined });
  assert.equal(result.latest_attempt.status, "unknown");
  assert.deepEqual(result.last_successful, previous.last_successful);
});

test("missing checked-out revision does not substitute upstream workflow SHA", () => {
  const result = buildPagesPublicationStatus(previous, { ...env, PAGES_DEPLOY_COMMIT_SHA: undefined });
  assert.equal(result.latest_attempt.commit_sha, null);
  assert.equal(result.latest_attempt.status, "unknown");
  assert.deepEqual(result.last_successful, previous.last_successful);
});

for (const outcome of ["failure", "cancelled", "skipped", "unknown"]) {
  test(`deployment ${outcome} preserves previous success even with successful verification`, () => {
    const result = buildPagesPublicationStatus(previous, { ...env, PAGES_DEPLOY_OUTCOME: outcome });
    assert.equal(result.latest_attempt.status, outcome);
    assert.deepEqual(result.last_successful, previous.last_successful);
  });
}

test("blank URLs remain null", () => {
  assert.equal(buildPagesPublicationStatus(previous, { ...env, PAGES_URL: "   " }).latest_attempt.page_url, null);
});
