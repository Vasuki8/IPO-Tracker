import assert from "node:assert/strict";
import fs from "node:fs";
import { evaluateScheduleHealth, SCHEDULE_SPECS } from "./check-schedule-health.mjs";

const now = "2026-09-28T15:00:00.000Z";
const run = (id, created_at, conclusion = "success", status = "completed") => ({
  id,
  event: "schedule",
  created_at,
  updated_at: created_at,
  status,
  conclusion,
  html_url: "https://github.com/Vasuki8/IPO-Tracker/actions/runs/" + id
});

function healthyPayload() {
  return {
    workflows: SCHEDULE_SPECS.map((spec, index) => {
      const minutes = spec.expected_minutes;
      const latest = new Date(Date.parse(now) - minutes * 60 * 1000).toISOString();
      const previous = new Date(Date.parse(latest) - minutes * 60 * 1000).toISOString();
      return { path: spec.path, runs: [run(index * 10 + 1, latest), run(index * 10 + 2, previous)] };
    })
  };
}

const healthy = evaluateScheduleHealth(healthyPayload(), now);
assert.equal(healthy.overall, "healthy");
assert.equal(healthy.critical_count, 0);
assert.equal(healthy.warning_count, 0);
assert.ok(healthy.workflows.every((row) => row.trigger_status === "observed"));
assert.ok(healthy.workflows.every((row) => row.execution_status === "success"));

const missedLivePayload = healthyPayload();
missedLivePayload.workflows.find((entry) => entry.path === ".github/workflows/update-ipos.yml").runs = [
  run(100, "2026-09-28T10:00:00.000Z"),
  run(99, "2026-09-28T09:00:00.000Z")
];
const missedLive = evaluateScheduleHealth(missedLivePayload, now);
const liveMiss = missedLive.workflows.find((row) => row.key === "live_ipo_sync");
assert.equal(missedLive.overall, "critical");
assert.equal(liveMiss.trigger_status, "missed_or_delayed");
assert.equal(liveMiss.execution_status, "success");
assert.ok(liveMiss.reasons.includes("scheduled_start_overdue"));

const failedLivePayload = healthyPayload();
failedLivePayload.workflows.find((entry) => entry.path === ".github/workflows/update-ipos.yml").runs[0] =
  run(200, "2026-09-28T14:17:00.000Z", "failure");
const failedLive = evaluateScheduleHealth(failedLivePayload, now);
const liveFailure = failedLive.workflows.find((row) => row.key === "live_ipo_sync");
assert.equal(failedLive.overall, "critical");
assert.equal(liveFailure.trigger_status, "observed");
assert.equal(liveFailure.execution_status, "failure");
assert.ok(liveFailure.reasons.includes("latest_scheduled_run_failed"));
assert.ok(!liveFailure.reasons.includes("scheduled_start_overdue"));

const warningPayload = healthyPayload();
warningPayload.workflows.find((entry) => entry.path === ".github/workflows/backfill-historical-offer-dates.yml").runs = [
  run(300, "2026-09-28T05:00:00.000Z"),
  run(299, "2026-09-28T04:00:00.000Z")
];
const warning = evaluateScheduleHealth(warningPayload, now);
assert.equal(warning.overall, "warning");
assert.equal(warning.critical_count, 0);
assert.equal(warning.warning_count, 1);

const gapPayload = healthyPayload();
gapPayload.workflows.find((entry) => entry.path === ".github/workflows/update-drhp.yml").runs = [
  run(400, "2026-09-28T14:00:00.000Z"),
  run(399, "2026-09-28T06:00:00.000Z"),
  run(398, "2026-09-28T04:00:00.000Z")
];
const gap = evaluateScheduleHealth(gapPayload, now);
const drhpGap = gap.workflows.find((row) => row.key === "pre_ipo_sync");
assert.equal(drhpGap.trigger_status, "observed");
assert.ok(drhpGap.reasons.includes("recent_schedule_gap_exceeded"));
assert.equal(gap.overall, "critical");

const workflowText = fs.readFileSync(".github/workflows/monitor-scheduled-operations.yml", "utf8");
assert.match(workflowText, /actions:\s*read/);
assert.match(workflowText, /contents:\s*read/);
assert.doesNotMatch(workflowText, /contents:\s*write/);
for (const spec of SCHEDULE_SPECS) assert.ok(workflowText.includes(spec.path), spec.path);

console.log(JSON.stringify({
  schedule_health_tests: {
    healthy: true,
    missed_start_distinguished: true,
    failed_execution_distinguished: true,
    warning_severity: true,
    historical_gap_detected: true,
    workflow_read_only: true
  }
}));
