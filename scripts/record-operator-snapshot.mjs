import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildOperatorReport } from "./operator-report.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DATA_PATH = path.join(ROOT, "data", "ipos.json");
const PAGES_STATUS_PATH = path.join(ROOT, "ops", "pages-publication.json");
export const OPERATOR_SNAPSHOT_PATH = path.join(ROOT, "ops", "operator-snapshot.json");

export function buildOperatorSnapshot(report) {
  return {
    schema_version: "1.0.0",
    generated_at: report.pipeline.report_generated_at,
    run: {
      id: report.pipeline.run_id,
      attempt: report.pipeline.run_attempt,
      workflow: report.pipeline.workflow,
      commit_sha: report.pipeline.commit_sha
    },
    health: report.health,
    recovery_guidance: report.recovery_guidance,
    pipeline: {
      collection_health: report.pipeline.collection_health,
      stages: report.pipeline.stages
    },
    freshness: {
      dataset_generated_at: report.dataset.dataset_generated_at,
      collection_started_at: report.dataset.collection_started_at,
      latest_record_collected_at: report.dataset.latest_record_collected_at,
      latest_evidence_collected_at: report.dataset.latest_evidence_collected_at
    },
    pages_publication: report.pages_publication
  };
}

export function writeOperatorSnapshot(snapshot, snapshotPath = OPERATOR_SNAPSHOT_PATH) {
  fs.mkdirSync(path.dirname(snapshotPath), { recursive: true });
  fs.writeFileSync(snapshotPath, JSON.stringify(snapshot, null, 2) + "\n");
}

function main() {
  const data = JSON.parse(fs.readFileSync(DATA_PATH, "utf8"));
  const pagesStatus = fs.existsSync(PAGES_STATUS_PATH)
    ? JSON.parse(fs.readFileSync(PAGES_STATUS_PATH, "utf8"))
    : null;
  const report = buildOperatorReport(data, process.env, pagesStatus);
  const snapshot = buildOperatorSnapshot(report);
  writeOperatorSnapshot(snapshot);
  process.stdout.write(
    `Recorded operator snapshot: ${snapshot.health.overall} for run ${snapshot.run.id ?? "unknown"}\n`
  );
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) main();
