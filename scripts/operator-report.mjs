import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DATA_PATH = path.join(ROOT, "data", "ipos.json");\nconst PAGES_STATUS_PATH = path.join(ROOT, "ops", "pages-publication.json");

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

export function renderMarkdown(report) {
  const { dataset, pipeline, pages_publication: pages } = report;
  const lines = [
    "# IPO Tracker operator report",
    "",
    "## Pipeline health",
    "",
    `- Collection health: **${pipeline.collection_health}**`,
    `- NSE collection: **${pipeline.stages.nse_collection}**`,
    `- SEBI collection: **${pipeline.stages.sebi_collection}**`,
    `- Dataset rebuild: **${pipeline.stages.rebuild}**`,
    `- Data validation: **${pipeline.stages.validation}**`,
    `- Repository publication step: **${pipeline.stages.repository_publish}**`,
    `- GitHub Pages latest attempt: **${pages.latest_attempt_status}**${pages.latest_attempt_at ? ` at ${pages.latest_attempt_at}` : ""}`,\n    `- GitHub Pages last successful publication: ${pages.last_successful_at || "not recorded"}${pages.last_successful_commit_sha ? ` (commit ${pages.last_successful_commit_sha})` : ""}`,
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
  ];
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

export function buildOperatorReport(data, env = process.env) {
  return { dataset: summarizeDataset(data), pipeline: summarizePipeline(env) };
}

function main() {
  const data = JSON.parse(fs.readFileSync(DATA_PATH, "utf8"));
  const report = buildOperatorReport(data);
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
