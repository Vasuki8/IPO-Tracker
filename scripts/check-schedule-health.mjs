import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

export const SCHEDULE_SPECS = [
  {
    key: "live_ipo_sync",
    name: "Sync live IPO data",
    path: ".github/workflows/update-ipos.yml",
    expected_minutes: 60,
    overdue_minutes: 180,
    severity: "critical"
  },
  {
    key: "pre_ipo_sync",
    name: "Sync Pre-IPO draft sources",
    path: ".github/workflows/update-drhp.yml",
    expected_minutes: 120,
    overdue_minutes: 360,
    severity: "critical"
  },
  {
    key: "bse_notice_backfill",
    name: "Backfill historical BSE SME addition notices",
    path: ".github/workflows/backfill-bse-sme-addition-notices.yml",
    expected_minutes: 120,
    overdue_minutes: 480,
    severity: "warning"
  },
  {
    key: "offer_date_backfill",
    name: "Backfill historical IPO offer dates",
    path: ".github/workflows/backfill-historical-offer-dates.yml",
    expected_minutes: 60,
    overdue_minutes: 480,
    severity: "warning"
  },
  {
    key: "pdf_field_backfill",
    name: "Backfill historical IPO PDF fields",
    path: ".github/workflows/backfill-historical-pdf-fields.yml",
    expected_minutes: 60,
    overdue_minutes: 480,
    severity: "warning"
  }
];

function isoMillis(value) {
  const millis = Date.parse(value || "");
  return Number.isFinite(millis) ? millis : null;
}

function roundedMinutes(ms) {
  return Math.round((ms / 60000) * 10) / 10;
}

function normalizeRuns(entry) {
  return (entry?.runs || [])
    .filter((run) => run?.event === "schedule" && isoMillis(run.created_at) !== null)
    .sort((a, b) => isoMillis(b.created_at) - isoMillis(a.created_at));
}

export function evaluateScheduleHealth(payload, now = new Date()) {
  const nowMillis = now instanceof Date ? now.getTime() : isoMillis(now);
  if (!Number.isFinite(nowMillis)) throw new Error("invalid schedule-health evaluation clock");
  const source = new Map((payload?.workflows || []).map((entry) => [entry.path, entry]));
  const results = [];

  for (const spec of SCHEDULE_SPECS) {
    const entry = source.get(spec.path);
    const runs = normalizeRuns(entry);
    const latest = runs[0] || null;
    const latestMillis = latest ? isoMillis(latest.created_at) : null;
    const futureClock = latestMillis !== null && latestMillis > nowMillis + 5 * 60 * 1000;
    const ageMinutes = latestMillis === null ? null : roundedMinutes(nowMillis - latestMillis);
    const gaps = [];
    for (let i = 0; i < runs.length - 1; i += 1) {
      const newer = isoMillis(runs[i].created_at);
      const older = isoMillis(runs[i + 1].created_at);
      if (newer !== null && older !== null && newer >= older) gaps.push(roundedMinutes(newer - older));
    }
    const maxRecentGapMinutes = gaps.length ? Math.max(...gaps) : null;
    const startOverdue = latestMillis === null || futureClock || ageMinutes > spec.overdue_minutes;
    const gapExceeded = maxRecentGapMinutes !== null && maxRecentGapMinutes > spec.overdue_minutes;
    const executionStatus = latest
      ? latest.status === "in_progress" || latest.status === "queued"
        ? latest.status
        : latest.conclusion || latest.status || "unknown"
      : "not_observed";
    const latestFailed = latest && latest.status === "completed" && latest.conclusion !== "success";
    const reasons = [];
    if (latestMillis === null) reasons.push("no_scheduled_start_observed");
    else if (futureClock) reasons.push("scheduled_start_clock_invalid");
    else if (startOverdue) reasons.push("scheduled_start_overdue");
    if (gapExceeded) reasons.push("recent_schedule_gap_exceeded");
    if (latestFailed) reasons.push("latest_scheduled_run_failed");

    results.push({
      ...spec,
      trigger_status: startOverdue ? "missed_or_delayed" : "observed",
      execution_status: executionStatus,
      latest_schedule_started_at: latest?.created_at || null,
      latest_schedule_completed_at: latest?.updated_at || null,
      latest_run_id: latest?.id || null,
      latest_run_url: latest?.html_url || null,
      age_minutes: ageMinutes,
      max_recent_gap_minutes: maxRecentGapMinutes,
      sampled_scheduled_runs: runs.length,
      reasons
    });
  }

  const critical = results.filter((row) => row.severity === "critical" && row.reasons.length > 0);
  const warnings = results.filter((row) => row.severity === "warning" && row.reasons.length > 0);
  return {
    schema_version: "1.0.0",
    checked_at: new Date(nowMillis).toISOString(),
    overall: critical.length ? "critical" : warnings.length ? "warning" : "healthy",
    critical_count: critical.length,
    warning_count: warnings.length,
    workflows: results
  };
}

function parseArgs(argv) {
  const result = {};
  for (const arg of argv) {
    const match = arg.match(/^--([^=]+)=(.*)$/);
    if (match) result[match[1]] = match[2];
  }
  return result;
}

async function runCli() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.input || !args.output) throw new Error("use --input=PATH --output=PATH");
  const payload = JSON.parse(fs.readFileSync(path.resolve(args.input), "utf8"));
  const report = evaluateScheduleHealth(payload, args.now || new Date());
  fs.mkdirSync(path.dirname(path.resolve(args.output)), { recursive: true });
  fs.writeFileSync(path.resolve(args.output), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({
    overall: report.overall,
    critical_count: report.critical_count,
    warning_count: report.warning_count,
    workflows: report.workflows.map((row) => ({
      key: row.key,
      trigger_status: row.trigger_status,
      execution_status: row.execution_status,
      age_minutes: row.age_minutes,
      max_recent_gap_minutes: row.max_recent_gap_minutes,
      reasons: row.reasons
    }))
  }));
  if (report.overall === "critical") process.exitCode = 1;
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) runCli().catch((error) => {
  console.error(error);
  process.exit(1);
});
