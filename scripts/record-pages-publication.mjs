import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const PAGES_STATUS_PATH = path.join(ROOT, "ops", "pages-publication.json");

const ALLOWED_OUTCOMES = new Set(["success", "failure", "cancelled", "skipped"]);

function normalizeOutcome(value) {
  return ALLOWED_OUTCOMES.has(value) ? value : "unknown";
}

function optionalString(value) {
  if (value === null || value === undefined) return null;
  const normalized = String(value).trim();
  return normalized || null;
}

export function emptyPagesPublicationStatus() {
  return {
    schema_version: "1.0.0",
    latest_attempt: null,
    last_successful: null
  };
}

export function readPagesPublicationStatus(statusPath = PAGES_STATUS_PATH) {
  try {
    return JSON.parse(fs.readFileSync(statusPath, "utf8"));
  } catch (error) {
    if (error?.code === "ENOENT") return emptyPagesPublicationStatus();
    throw error;
  }
}

export function buildPagesPublicationStatus(previous = emptyPagesPublicationStatus(), env = process.env) {
  const attempt = {
    status: normalizeOutcome(env.PAGES_DEPLOY_OUTCOME),
    workflow_run_id: optionalString(env.GITHUB_RUN_ID),
    workflow_run_attempt: optionalString(env.GITHUB_RUN_ATTEMPT),
    workflow: optionalString(env.GITHUB_WORKFLOW),
    commit_sha: optionalString(env.GITHUB_SHA),
    completed_at: optionalString(env.PAGES_DEPLOY_COMPLETED_AT) ?? new Date().toISOString(),
    page_url: optionalString(env.PAGES_URL)
  };

  return {
    schema_version: "1.0.0",
    latest_attempt: attempt,
    last_successful: attempt.status === "success"
      ? { ...attempt }
      : previous?.last_successful ?? null
  };
}

export function writePagesPublicationStatus(status, statusPath = PAGES_STATUS_PATH) {
  fs.mkdirSync(path.dirname(statusPath), { recursive: true });
  fs.writeFileSync(statusPath, JSON.stringify(status, null, 2) + "\n");
}

function main() {
  const previous = readPagesPublicationStatus();
  const next = buildPagesPublicationStatus(previous);
  writePagesPublicationStatus(next);
  process.stdout.write(
    `Recorded GitHub Pages attempt: ${next.latest_attempt.status} at ${next.latest_attempt.completed_at}\n`
  );
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) main();
