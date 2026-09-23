import assert from "node:assert/strict";
import {
  buildPagesPublicationStatus,
  emptyPagesPublicationStatus
} from "./record-pages-publication.mjs";

const success = buildPagesPublicationStatus(emptyPagesPublicationStatus(), {
  PAGES_DEPLOY_OUTCOME: "success",
  PAGES_DEPLOY_COMPLETED_AT: "2026-09-23T05:00:00Z",
  PAGES_URL: "https://vasuki8.github.io/IPO-Tracker/",
  GITHUB_RUN_ID: "111",
  GITHUB_RUN_ATTEMPT: "1",
  GITHUB_WORKFLOW: "Deploy IPO Tracker to GitHub Pages",
  GITHUB_SHA: "abc123"
});

assert.equal(success.latest_attempt.status, "success");
assert.equal(success.latest_attempt.completed_at, "2026-09-23T05:00:00Z");
assert.equal(success.latest_attempt.commit_sha, "abc123");
assert.equal(success.last_successful.status, "success");
assert.equal(success.last_successful.workflow_run_id, "111");

const failure = buildPagesPublicationStatus(success, {
  PAGES_DEPLOY_OUTCOME: "failure",
  PAGES_DEPLOY_COMPLETED_AT: "2026-09-23T06:00:00Z",
  GITHUB_RUN_ID: "222",
  GITHUB_RUN_ATTEMPT: "1",
  GITHUB_WORKFLOW: "Deploy IPO Tracker to GitHub Pages",
  GITHUB_SHA: "def456"
});

assert.equal(failure.latest_attempt.status, "failure");
assert.equal(failure.latest_attempt.page_url, null);
assert.equal(failure.latest_attempt.commit_sha, "def456");
assert.deepEqual(failure.last_successful, success.last_successful);

const unknown = buildPagesPublicationStatus(failure, {
  PAGES_DEPLOY_OUTCOME: "unexpected",
  PAGES_DEPLOY_COMPLETED_AT: "2026-09-23T07:00:00Z",
  PAGES_URL: "   "
});
assert.equal(unknown.latest_attempt.status, "unknown");
assert.equal(unknown.latest_attempt.page_url, null);
assert.deepEqual(unknown.last_successful, success.last_successful);

console.log("GitHub Pages publication status tests passed.");
