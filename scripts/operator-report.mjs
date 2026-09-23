import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DATA_PATH = path.join(ROOT, "data", "ipos.json");
const PAGES_STATUS_PATH = path.join(ROOT, "ops", "pages-publication.json");
const OPERATOR_HISTORY_PATH = path.join(ROOT, "ops", "operator-health-history.json");

export const DEFAULT_STALENESS_THRESHOLDS_HOURS = {
  dataset_generated: 3,
  record_collection: 3,
  evidence_collection: 24,
  pages_publication: 3
};

export const RECOVERY_GUIDANCE = {
  collection_failure: {
    priority: "high",
    diagnostic: "Inspect the failed NSE/SEBI collection step and its workflow logs before changing source parsers.",
    recovery: "After identifying a transient source/network failure or a confirmed parser repair, rerun the live IPO sync and verify collection succeeds."
  },
  pages_deployment_failure: {
    priority: "high",
    diagnostic: "Inspect the latest GitHub Pages deployment run and the Deploy to GitHub Pages / publication-health steps.",
    recovery: "Fix the deployment-specific failure, then rerun the Pages workflow and confirm a new successful publication is recorded."
  },
  stale_dataset: {
    priority: "medium",
    diagnostic: "Check whether the hourly sync has completed since the dataset generated_at timestamp and whether rebuild/validation were successful.",
    recovery: "If collection is healthy but generation is stale, inspect rebuild/validation/publication before considering a sync rerun."
  },
  stale_record_collection: {
    priority: "medium",
    diagnostic: "Check the latest hourly sync and NSE/SEBI collection outcomes; confirm retained records are receiving current collection timestamps.",
    recovery: "Investigate collection or merge logic if successful runs are not advancing retained record collection time."
  },
  stale_evidence_collection: {
    priority: "low",
    diagnostic: "Confirm collectors are succeeding, then check whether current official sources actually contain new document or field evidence.",
    recovery: "Do not rerun solely because evidence is old; repair a source path only when newer official evidence exists but is not being retained."
  },
  stale_pages_publication: {
    priority: "medium",
    diagnostic: "Compare the latest main commit/dataset generation with the last successful Pages publication and inspect recent Pages runs.",
    recovery: "Rerun or repair Pages only when repository content is newer than the last successful publication or the deployment pipeline is unhealthy."
  },
  dataset_generated_time_missing: {
    priority: "medium",
    diagnostic: "Validate the published dataset contract and inspect the rebuild step for a missing generated_at timestamp.",
    recovery: "Repair dataset generation metadata rather than inventing a timestamp."
  },
  record_collection_time_missing: {
    priority: "medium",
    diagnostic: "Inspect retained recovery records and collector merge logic for missing last_collected_at values.",
    recovery: "Restore collection timestamp retention from real collection events; do not synthesize historical times."
  },
  pages_publication_time_missing: {
    priority: "medium",
    diagnostic: "Inspect ops/pages-publication.json and the latest Pages workflow publication-health step.",
    recovery: "Restore publication-health recording from an actual Pages run; do not substitute dataset generated_at."
  },
  invalid_report_time: {
    priority: "medium",
    diagnostic: "Inspect the operator report clock input and ensure it is a valid ISO timestamp.",
    recovery: "Correct the report-time input before using staleness classifications."
  }
};

export const MONITORED_FIELDS = [
  "price_band",
  "issue_price",
  "issue_size_inr",
  "open_date",
  "close_date",
  "listing_date"
];

function fieldValue(field) {
  return field && field.value !== null && field.value !== undefined ? field.value : null;
}

function verifiedValue(field) {
  return field?.status === "verified" && fieldValue(field) !== null ? fieldValue(field) : null;
}

export function verifiedLotSize(record) {
  return verifiedValue(record.market_lot) ?? verifiedValue(record.minimum_bid_quantity);
}

export function latestTimestamp(values) {
  return values.filter(Boolean).map(String).sort().at(-1) ?? null;
}

export function summarizeDataset(data) {
  const records = Array.isArray(data?.records) ? data.records : [];
  const fieldCoverage = Object.fromEntries(
    MONITORED_FIELDS.map((field) => {
      const verified = records.filter((record) => verifiedValue(record[field]) !== null).length;
      const missing = records.filter((record) => fieldValue(record[field]) === null).length;
      const nonVerified = records.length - verified - missing;
      return [field, { verified, missing, non_verified: nonVerified, total: records.length }];
    })
  );

  const lotVerified = records.filter((record) => verifiedLotSize(record) !== null).length;
  const lotDirect = records.filter((record) => verifiedValue(record.market_lot) !== null).length;
  const lotFallback = records.filter((record) =>
    verifiedValue(record.market_lot) === null && verifiedValue(record.minimum_bid_quantity) !== null
  ).length;

  const evidenceTimes = [];
  for (const record of records) {
    for (const field of Object.values(record)) {
      if (field && typeof field === "object" && Array.isArray(field.evidence)) {
        for (const item of field.evidence) evidenceTimes.push(item?.collected_at);
      }
    }
    for (const item of record.board_evidence || []) evidenceTimes.push(item?.collected_at);
    for (const item of record.status_evidence || []) evidenceTimes.push(item?.collected_at);
    for (const item of record.documents || []) evidenceTimes.push(item?.collected_at);
  }

  return {
    schema_version: data?.schema_version ?? null,
    records: records.length,
    dataset_generated_at: data?.generated_at ?? null,
    collection_started_at: data?.collection_started_at ?? null,
    latest_first_observed_at: latestTimestamp(records.map((record) => record.first_observed_at)),
    latest_record_collected_at: latestTimestamp(records.map((record) => record.last_collected_at)),
    latest_evidence_collected_at: latestTimestamp(evidenceTimes),
    field_coverage: fieldCoverage,
    lot_size: {
      verified: lotVerified,
      direct_market_lot: lotDirect,
      verified_minimum_bid_fallback: lotFallback,
      missing: records.length - lotVerified,
      total: records.length
    }
  };
}

function normalizedOutcome(value) {
  const allowed = new Set(["success", "failure", "cancelled", "skipped"]);
  return allowed.has(value) ? value : "unknown";
}

export function summarizePipeline(env = process.env) {
  const stages = {
    nse_collection: normalizedOutcome(env.NSE_COLLECTION_OUTCOME),
    sebi_collection: normalizedOutcome(env.SEBI_COLLECTION_OUTCOME),
    rebuild: normalizedOutcome(env.REBUILD_OUTCOME),
    validation: normalizedOutcome(env.VALIDATION_OUTCOME),
    repository_publish: normalizedOutcome(env.REPOSITORY_PUBLISH_OUTCOME)
  };
  const collectionOutcomes = [stages.nse_collection, stages.sebi_collection];
  const collectionHealth = collectionOutcomes.includes("failure") || collectionOutcomes.includes("cancelled")
    ? "collection_failure"
    : collectionOutcomes.every((value) => value === "success")
      ? "collection_success"
      : "not_measured";

  return {
    run_id: env.GITHUB_RUN_ID ?? null,
    run_attempt: env.GITHUB_RUN_ATTEMPT ?? null,
    commit_sha: env.GITHUB_SHA ?? null,
    workflow: env.GITHUB_WORKFLOW ?? null,
    report_generated_at: env.OPERATOR_REPORT_AT ?? new Date().toISOString(),
    collection_health: collectionHealth,
    stages,
    pages_publication: "not_recorded_in_sync_workflow"
  };
}

function ageHours(timestamp, nowMs) {
  if (!timestamp) return null;
  const value = Date.parse(timestamp);
  if (!Number.isFinite(value)) return null;
  return Math.max(0, (nowMs - value) / 3_600_000);
}

export function classifyOperatorHealth(dataset, pipeline, pages, options = {}) {
  const now = options.now ?? pipeline.report_generated_at ?? new Date().toISOString();
  const nowMs = Date.parse(now);
  const thresholds = { ...DEFAULT_STALENESS_THRESHOLDS_HOURS, ...(options.thresholds_hours || {}) };
  if (!Number.isFinite(nowMs)) {
    return { overall: "unknown", reasons: ["invalid_report_time"], thresholds_hours: thresholds, ages_hours: {} };
  }

  const ages = {
    dataset_generated: ageHours(dataset.dataset_generated_at, nowMs),
    record_collection: ageHours(dataset.latest_record_collected_at, nowMs),
    evidence_collection: ageHours(dataset.latest_evidence_collected_at, nowMs),
    pages_publication: ageHours(pages.last_successful_at, nowMs)
  };

  const reasons = [];
  if (pipeline.collection_health === "collection_failure") reasons.push("collection_failure");
  if (pages.latest_attempt_status === "failure" || pages.latest_attempt_status === "cancelled") reasons.push("pages_deployment_failure");

  const staleChecks = [
    ["dataset_generated", "stale_dataset"],
    ["record_collection", "stale_record_collection"],
    ["evidence_collection", "stale_evidence_collection"],
    ["pages_publication", "stale_pages_publication"]
  ];
  for (const [key, reason] of staleChecks) {
    if (ages[key] !== null && ages[key] > thresholds[key]) reasons.push(reason);
  }

  const missingSignals = [];
  if (ages.dataset_generated === null) missingSignals.push("dataset_generated_time_missing");
  if (ages.record_collection === null) missingSignals.push("record_collection_time_missing");
  if (ages.pages_publication === null) missingSignals.push("pages_publication_time_missing");

  let overall = "healthy";
  if (reasons.includes("collection_failure") || reasons.includes("pages_deployment_failure")) overall = "failure";
  else if (reasons.some((reason) => reason.startsWith("stale_"))) overall = "stale";
  else if (missingSignals.length || pipeline.collection_health === "not_measured") overall = "unknown";

  return {
    overall,
    reasons: [...reasons, ...missingSignals],
    thresholds_hours: thresholds,
    ages_hours: Object.fromEntries(Object.entries(ages).map(([key, value]) => [
      key,
      value === null ? null : Math.round(value * 100) / 100
    ]))
  };
}

export function buildRecoveryGuidance(health) {
  return (health?.reasons || []).map((reason) => ({
    reason,
    ...(RECOVERY_GUIDANCE[reason] || {
      priority: "medium",
      diagnostic: "Inspect the operator report inputs and relevant workflow logs for this unrecognized health reason.",
      recovery: "Do not mutate IPO data until the operational cause is understood."
    })
  }));
}

export function summarizeHealthHistory(history, limit = 5) {
  const entries = Array.isArray(history?.entries) ? history.entries : [];
  const current = entries.at(-1) ?? null;
  return {
    recorded: entries.length > 0,
    transition_count: entries.length,
    current: current ? {
      overall: current.overall,
      reasons: current.reasons || [],
      observations: current.observations || 1,
      observed_at: current.observed_at ?? null,
      last_observed_at: current.last_observed_at ?? current.observed_at ?? null,
      run_id: current.run_id ?? null,
      last_run_id: current.last_run_id ?? current.run_id ?? null
    } : null,
    recent_transitions: entries.slice(-limit).map((entry) => ({
      overall: entry.overall,
      reasons: entry.reasons || [],
      observations: entry.observations || 1,
      observed_at: entry.observed_at ?? null,
      last_observed_at: entry.last_observed_at ?? entry.observed_at ?? null
    }))
  };
}

export function renderMarkdown(report) {
  const { dataset, pipeline, pages_publication: pages, health, recovery_guidance: guidance, recurrence } = report;
  const lines = [
    "# IPO Tracker operator report",
    "",
    "## Operator health",
    "",
    `- Overall: **${health.overall}**`,
    `- Reasons: ${health.reasons.length ? health.reasons.join(", ") : "none"}`,
    `- Dataset age: ${health.ages_hours.dataset_generated ?? "unknown"}h (stale after ${health.thresholds_hours.dataset_generated}h)`,
    `- Record collection age: ${health.ages_hours.record_collection ?? "unknown"}h (stale after ${health.thresholds_hours.record_collection}h)`,
    `- Evidence collection age: ${health.ages_hours.evidence_collection ?? "unknown"}h (stale after ${health.thresholds_hours.evidence_collection}h)`,
    `- Last successful Pages publication age: ${health.ages_hours.pages_publication ?? "unknown"}h (stale after ${health.thresholds_hours.pages_publication}h)`,
    "",
    "## Recurrence context",
    "",
    recurrence.recorded
      ? `- Current retained state: **${recurrence.current.overall}** across **${recurrence.current.observations}** consecutive observation(s)`
      : "- Health-transition history: **not recorded yet**",
    recurrence.recorded
      ? `- Retained transitions: **${recurrence.transition_count}**`
      : "- Retained transitions: **0**",
    ""
  ];
  if (recurrence.recorded) {
    lines.push("- Recent transitions:");
    for (const item of recurrence.recent_transitions) {
      const reasons = item.reasons.length ? item.reasons.join(", ") : "none";
      lines.push(`  - ${item.overall} ×${item.observations} — reasons: ${reasons} — ${item.observed_at || "unknown"} → ${item.last_observed_at || "unknown"}`);
    }
  }
  lines.push(
    "",
    "## Recovery guidance",
    ""
  ];
  if (guidance.length === 0) {
    lines.push("- No recovery action indicated.");
  } else {
    for (const item of guidance) {
      lines.push(`- **${item.reason}** [${item.priority}] — Diagnose: ${item.diagnostic} Recovery: ${item.recovery}`);
    }
  }
  lines.push(
    "",
    "## Pipeline health",
    "",
    `- Collection health: **${pipeline.collection_health}**`,
    `- NSE collection: **${pipeline.stages.nse_collection}**`,
    `- SEBI collection: **${pipeline.stages.sebi_collection}**`,
    `- Dataset rebuild: **${pipeline.stages.rebuild}**`,
    `- Data validation: **${pipeline.stages.validation}**`,
    `- Repository publication step: **${pipeline.stages.repository_publish}**`,
    `- GitHub Pages latest attempt: **${pages.latest_attempt_status}**${pages.latest_attempt_at ? ` at ${pages.latest_attempt_at}` : ""}`,
    `- GitHub Pages last successful publication: ${pages.last_successful_at || "not recorded"}${pages.last_successful_commit_sha ? ` (commit ${pages.last_successful_commit_sha})` : ""}`,
    "",
    "## Freshness timestamps",
    "",
    `- Report generated: ${pipeline.report_generated_at || "unknown"}`,
    `- Dataset generated: ${dataset.dataset_generated_at || "unknown"}`,
    `- Recovery collection started: ${dataset.collection_started_at || "unknown"}`,
    `- Latest record collection: ${dataset.latest_record_collected_at || "unknown"}`,
    `- Latest retained evidence collection: ${dataset.latest_evidence_collected_at || "unknown"}`,
    `- Latest first-observed IPO: ${dataset.latest_first_observed_at || "unknown"}`,
    "",
    "## Coverage",
    "",
    `- Published records: **${dataset.records}**`,
    `- Verified Lot Size: **${dataset.lot_size.verified}/${dataset.lot_size.total}** (direct market lot ${dataset.lot_size.direct_market_lot}, verified bid-quantity fallback ${dataset.lot_size.verified_minimum_bid_fallback})`
  );
  for (const [field, coverage] of Object.entries(dataset.field_coverage)) {
    lines.push(`- ${field}: verified **${coverage.verified}/${coverage.total}**, missing **${coverage.missing}**, non-verified **${coverage.non_verified}**`);
  }
  lines.push(
    "",
    "## Interpretation",
    "",
    "- A successful collector with a missing field means the current run completed; it does **not** mean the source necessarily contains that value.",
    "- A failed/cancelled NSE or SEBI stage is reported as **collection_failure** and should not be confused with a source-null field.",
    "- Field-specific source-null decisions remain documented in `docs/PROJECT_STATUS.md`; this report intentionally does not infer source-null from a null value alone.",
    "- GitHub Pages publication time is operational metadata stored separately from IPO data and dataset generation time.",
    ""
  );
  return lines.join("\n");
}

export function summarizePagesPublication(status) {
  const latest = status?.latest_attempt ?? null;
  const successful = status?.last_successful ?? null;
  return {
    latest_attempt_status: latest?.status ?? "not_recorded",
    latest_attempt_at: latest?.completed_at ?? null,
    latest_attempt_commit_sha: latest?.commit_sha ?? null,
    latest_attempt_run_id: latest?.workflow_run_id ?? null,
    last_successful_at: successful?.completed_at ?? null,
    last_successful_commit_sha: successful?.commit_sha ?? null,
    last_successful_run_id: successful?.workflow_run_id ?? null,
    page_url: successful?.page_url ?? latest?.page_url ?? null
  };
}

export function buildOperatorReport(data, env = process.env, pagesStatus = null, options = {}, history = null) {
  const dataset = summarizeDataset(data);
  const pipeline = summarizePipeline(env);
  const pagesPublication = summarizePagesPublication(pagesStatus);
  const report = {
    dataset,
    pipeline,
    pages_publication: pagesPublication,
    health: classifyOperatorHealth(dataset, pipeline, pagesPublication, options),
    recurrence: summarizeHealthHistory(history)
  };
  report.recovery_guidance = buildRecoveryGuidance(report.health);
  return report;
}

function main() {
  const data = JSON.parse(fs.readFileSync(DATA_PATH, "utf8"));
  const pagesStatus = fs.existsSync(PAGES_STATUS_PATH)
    ? JSON.parse(fs.readFileSync(PAGES_STATUS_PATH, "utf8"))
    : null;
  const history = fs.existsSync(OPERATOR_HISTORY_PATH)
    ? JSON.parse(fs.readFileSync(OPERATOR_HISTORY_PATH, "utf8"))
    : null;
  const report = buildOperatorReport(data, process.env, pagesStatus, {}, history);
  const markdown = renderMarkdown(report);
  if (process.argv.includes("--json")) process.stdout.write(JSON.stringify(report, null, 2) + "\n");
  else process.stdout.write(markdown + "\n");
  if (process.argv.includes("--github-summary")) {
    const summaryPath = process.env.GITHUB_STEP_SUMMARY;
    if (!summaryPath) throw new Error("GITHUB_STEP_SUMMARY is required for --github-summary");
    fs.appendFileSync(summaryPath, markdown + "\n");
  }
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) main();
