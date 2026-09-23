import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const CURSOR_PATHS = [
  "ops/sebi-historical-search.json",
  "ops/nse-historical-detail.json"
];

function clone(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function equal(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function readJson(file) {
  return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, "utf8")) : undefined;
}

function gitJson(ref, relativePath) {
  try {
    const content = execFileSync("git", ["show", `${ref}:${relativePath}`], {
      cwd: ROOT,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"]
    });
    return JSON.parse(content);
  } catch {
    return undefined;
  }
}

function baselineRecoveryPaths(ref) {
  try {
    const output = execFileSync(
      "git",
      ["ls-tree", "-r", "--name-only", ref, "data/recovery"],
      { cwd: ROOT, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }
    );
    return output.split("\n")
      .map((line) => line.trim())
      .filter((line) => /^data\/recovery\/20\d{2}\/nse-issue-information\.json$/.test(line));
  } catch {
    return [];
  }
}

function workingRecoveryPaths() {
  if (!fs.existsSync(RECOVERY_ROOT)) return [];
  return fs.readdirSync(RECOVERY_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^20\d{2}$/.test(entry.name))
    .map((entry) => `data/recovery/${entry.name}/nse-issue-information.json`)
    .filter((relative) => fs.existsSync(path.join(ROOT, relative)));
}

export function buildRecoveryProposal(before, after) {
  if (!after || !Array.isArray(after.records)) return null;
  if (!before) {
    return {
      new_manifest: clone(after),
      added_records: [],
      changed_records: [],
      removed_records: []
    };
  }

  const beforeById = new Map((before.records || []).map((record) => [record.id, record]));
  const afterById = new Map((after.records || []).map((record) => [record.id, record]));
  const addedRecords = [];
  const changedRecords = [];
  const removedRecords = [];

  for (const [id, record] of afterById) {
    const prior = beforeById.get(id);
    if (!prior) {
      addedRecords.push(clone(record));
    } else if (!equal(prior, record)) {
      changedRecords.push({ id, before: clone(prior), after: clone(record) });
    }
  }

  for (const [id, record] of beforeById) {
    if (!afterById.has(id)) removedRecords.push({ id, before: clone(record) });
  }

  if (addedRecords.length === 0 && changedRecords.length === 0 && removedRecords.length === 0 &&
      before.generated_at === after.generated_at) {
    return null;
  }

  return {
    new_manifest: null,
    manifest_generated_at_before: before.generated_at ?? null,
    manifest_generated_at_after: after.generated_at ?? null,
    added_records: addedRecords,
    changed_records: changedRecords,
    removed_records: removedRecords
  };
}

export function buildJsonProposal(before, after) {
  if (equal(before, after)) return null;
  return {
    before_exists: before !== undefined,
    after_exists: after !== undefined,
    before: clone(before),
    after: clone(after)
  };
}

export function prepareLiveSyncProposal(ref = "HEAD") {
  const recoveryPaths = [...new Set([...baselineRecoveryPaths(ref), ...workingRecoveryPaths()])].sort();
  const recovery = {};

  for (const relative of recoveryPaths) {
    const before = gitJson(ref, relative);
    const after = readJson(path.join(ROOT, relative));
    if (!after) continue;
    const proposal = buildRecoveryProposal(before, after);
    if (proposal) recovery[relative] = proposal;
  }

  const cursors = {};
  for (const relative of CURSOR_PATHS) {
    const before = gitJson(ref, relative);
    const after = readJson(path.join(ROOT, relative));
    const proposal = buildJsonProposal(before, after);
    if (proposal) cursors[relative] = proposal;
  }

  const publishedBefore = gitJson(ref, "data/ipos.json");
  const publishedAfter = readJson(path.join(ROOT, "data/ipos.json"));

  return {
    schema_version: "1.0.0",
    base_ref: ref,
    prepared_at: new Date().toISOString(),
    published_data_changed: !equal(publishedBefore, publishedAfter),
    recovery,
    cursors
  };
}

async function run() {
  const outputArg = process.argv.find((arg) => arg.startsWith("--output="));
  if (!outputArg) throw new Error("--output=<proposal.json> is required");
  const refArg = process.argv.find((arg) => arg.startsWith("--base="));
  const ref = refArg ? refArg.slice("--base=".length) : "HEAD";
  const output = outputArg.slice("--output=".length);
  const proposal = prepareLiveSyncProposal(ref);
  fs.mkdirSync(path.dirname(path.resolve(output)), { recursive: true });
  fs.writeFileSync(path.resolve(output), JSON.stringify(proposal, null, 2) + "\n");

  const stats = {
    recovery_manifests: Object.keys(proposal.recovery).length,
    changed_records: Object.values(proposal.recovery)
      .reduce((sum, item) => sum + (item.changed_records?.length || 0), 0),
    added_records: Object.values(proposal.recovery)
      .reduce((sum, item) => sum + (item.added_records?.length || 0), 0),
    cursor_files: Object.keys(proposal.cursors).length,
    published_data_changed: proposal.published_data_changed
  };
  console.log(JSON.stringify({ live_sync_proposal: stats }, null, 2));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => { console.error(error); process.exit(1); });
