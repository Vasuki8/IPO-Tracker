import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SNAPSHOT_PATH = path.join(ROOT, "ops", "operator-snapshot.json");
const HISTORY_PATH = path.join(ROOT, "ops", "operator-health-history.json");
const PAGES_PATH = path.join(ROOT, "ops", "pages-publication.json");
const HEALTH = new Set(["healthy", "stale", "failure", "unknown"]);

function requireObject(value, label, errors) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    errors.push(`${label} must be an object`);
    return false;
  }
  return true;
}

function requireString(value, label, errors, nullable = false) {
  if (nullable && value === null) return;
  if (typeof value !== "string" || value.length === 0) errors.push(`${label} must be a non-empty string`);
}

function requireStringArray(value, label, errors) {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) errors.push(`${label} must be an array of strings`);
}

export function validateOperatorSnapshot(snapshot) {
  const errors = [];
  if (!requireObject(snapshot, "snapshot", errors)) return errors;
  if (snapshot.schema_version !== "1.0.0") errors.push("snapshot.schema_version must be 1.0.0");
  requireString(snapshot.generated_at, "snapshot.generated_at", errors);
  if (requireObject(snapshot.run, "snapshot.run", errors)) {
    requireString(snapshot.run.id, "snapshot.run.id", errors, true);
    requireString(snapshot.run.commit_sha, "snapshot.run.commit_sha", errors, true);
  }
  if (requireObject(snapshot.health, "snapshot.health", errors)) {
    if (!HEALTH.has(snapshot.health.overall)) errors.push("snapshot.health.overall is invalid");
    requireStringArray(snapshot.health.reasons, "snapshot.health.reasons", errors);
  }
  if (!Array.isArray(snapshot.recovery_guidance)) errors.push("snapshot.recovery_guidance must be an array");
  if (requireObject(snapshot.pipeline, "snapshot.pipeline", errors)) {
    requireString(snapshot.pipeline.collection_health, "snapshot.pipeline.collection_health", errors);
    requireObject(snapshot.pipeline.stages, "snapshot.pipeline.stages", errors);
  }
  requireObject(snapshot.freshness, "snapshot.freshness", errors);
  requireObject(snapshot.pages_publication, "snapshot.pages_publication", errors);
  return errors;
}

export function validateOperatorHistory(history) {
  const errors = [];
  if (!requireObject(history, "history", errors)) return errors;
  if (history.schema_version !== "1.0.0") errors.push("history.schema_version must be 1.0.0");
  if (!Number.isInteger(history.max_entries) || history.max_entries < 1 || history.max_entries > 48) {
    errors.push("history.max_entries must be an integer between 1 and 48");
  }
  if (!Array.isArray(history.entries)) {
    errors.push("history.entries must be an array");
    return errors;
  }
  if (Number.isInteger(history.max_entries) && history.entries.length > history.max_entries) {
    errors.push("history.entries exceeds max_entries");
  }
  history.entries.forEach((entry, index) => {
    const label = `history.entries[${index}]`;
    if (!requireObject(entry, label, errors)) return;
    requireString(entry.observed_at, `${label}.observed_at`, errors);
    requireString(entry.last_observed_at, `${label}.last_observed_at`, errors);
    if (!HEALTH.has(entry.overall)) errors.push(`${label}.overall is invalid`);
    requireStringArray(entry.reasons, `${label}.reasons`, errors);
    if (!Number.isInteger(entry.observations) || entry.observations < 1) errors.push(`${label}.observations must be >= 1`);
  });
  return errors;
}

export function validatePagesPublication(status) {
  const errors = [];
  if (!requireObject(status, "pages", errors)) return errors;
  if (status.schema_version !== "1.0.0") errors.push("pages.schema_version must be 1.0.0");
  for (const key of ["latest_attempt", "last_successful"]) {
    const attempt = status[key];
    if (attempt === null && key === "last_successful") continue;
    if (!requireObject(attempt, `pages.${key}`, errors)) continue;
    if (!["success", "failure", "cancelled", "skipped", "unknown"].includes(attempt.status)) {
      errors.push(`pages.${key}.status is invalid`);
    }
    requireString(attempt.completed_at, `pages.${key}.completed_at`, errors);
    requireString(attempt.workflow_run_id, `pages.${key}.workflow_run_id`, errors, true);
    requireString(attempt.commit_sha, `pages.${key}.commit_sha`, errors, true);
  }
  return errors;
}

export function validateOperatorFiles(snapshot, history, pages = null) {
  return [
    ...validateOperatorSnapshot(snapshot),
    ...validateOperatorHistory(history),
    ...(pages ? validatePagesPublication(pages) : [])
  ];
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function main() {
  const errors = validateOperatorFiles(readJson(SNAPSHOT_PATH), readJson(HISTORY_PATH), readJson(PAGES_PATH));
  if (errors.length) {
    for (const error of errors) process.stderr.write(`- ${error}\n`);
    process.exitCode = 1;
    return;
  }
  process.stdout.write("Validated operator snapshot/history contracts.\n");
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) main();
