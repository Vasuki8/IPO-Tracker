import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const CURSOR_PATH = path.join(ROOT, "ops", "sebi-historical-offer-dates.json");

function fieldValue(record, field) {
  return record?.[field]?.value ?? record?.terms?.[field] ?? null;
}

function newerCursorEntry(a, b) {
  if (!a) return b;
  if (!b) return a;
  const at = Date.parse(a.last_attempted_at || "");
  const bt = Date.parse(b.last_attempted_at || "");
  if (!Number.isFinite(at)) return b;
  if (!Number.isFinite(bt)) return a;
  return bt >= at ? b : a;
}

export function buildOfferDatePlan(baseByYear, currentByYear, cursorState = { issuers: {} }) {
  const changes = [];
  for (const [year, currentManifest] of currentByYear.entries()) {
    const baseManifest = baseByYear.get(year) || { records: [] };
    const baseById = new Map((baseManifest.records || []).map((record) => [record.id, record]));
    for (const record of currentManifest.records || []) {
      const base = baseById.get(record.id);
      if (!base) continue;
      const fields = {};
      for (const field of ["open_date", "close_date"]) {
        const before = fieldValue(base, field);
        const after = record?.[field]?.value ?? null;
        if (after !== null && after !== before && record[field]) {
          fields[field] = record[field];
        }
      }
      if (Object.keys(fields).length > 0) {
        changes.push({ year, id: record.id, issuer_name: record.issuer_name, fields });
      }
    }
  }
  return {
    schema_version: "1.0.0",
    changes,
    cursor_state: {
      schema_version: "1.0.0",
      issuers: cursorState?.issuers || {}
    }
  };
}

export function applyOfferDatePlan(latestByYear, currentCursor = { issuers: {} }, plan) {
  const stats = {
    planned_records: (plan?.changes || []).length,
    changed_records: 0,
    changed_fields: 0,
    conflicts: 0,
    missing_records: 0,
    cursor_updates: 0
  };

  for (const change of plan?.changes || []) {
    const manifest = latestByYear.get(Number(change.year));
    if (!manifest) {
      stats.missing_records += 1;
      continue;
    }
    const record = (manifest.records || []).find((item) => item.id === change.id);
    if (!record) {
      stats.missing_records += 1;
      continue;
    }

    let recordChanged = false;
    for (const field of ["open_date", "close_date"]) {
      const planned = change.fields?.[field];
      if (!planned?.value) continue;
      const existing = fieldValue(record, field);
      if (existing !== null) {
        if (existing !== planned.value) stats.conflicts += 1;
        continue;
      }
      record[field] = planned;
      recordChanged = true;
      stats.changed_fields += 1;
    }

    if (recordChanged) {
      const collected = ["open_date", "close_date"]
        .map((field) => record?.[field]?.source?.collected_at)
        .filter(Boolean)
        .sort()
        .at(-1);
      if (collected) record.last_collected_at = collected;
      stats.changed_records += 1;
    }
  }

  currentCursor.issuers ||= {};
  for (const [key, planned] of Object.entries(plan?.cursor_state?.issuers || {})) {
    const chosen = newerCursorEntry(currentCursor.issuers[key], planned);
    if (chosen !== currentCursor.issuers[key]) {
      currentCursor.issuers[key] = chosen;
      stats.cursor_updates += 1;
    }
  }

  return stats;
}

function recoveryFiles() {
  if (!fs.existsSync(RECOVERY_ROOT)) return [];
  return fs.readdirSync(RECOVERY_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^20\d{2}$/.test(entry.name))
    .map((entry) => ({
      year: Number(entry.name),
      file: path.join(RECOVERY_ROOT, entry.name, "nse-issue-information.json"),
      relative: path.posix.join("data", "recovery", entry.name, "nse-issue-information.json")
    }))
    .filter((item) => fs.existsSync(item.file))
    .sort((a, b) => a.year - b.year);
}

function gitHeadJson(relativePath) {
  try {
    const content = execFileSync("git", ["show", "HEAD:" + relativePath], {
      cwd: ROOT,
      encoding: "utf8",
      maxBuffer: 64 * 1024 * 1024
    });
    return JSON.parse(content);
  } catch {
    return null;
  }
}

function readCursor() {
  if (!fs.existsSync(CURSOR_PATH)) return { schema_version: "1.0.0", issuers: {} };
  const state = JSON.parse(fs.readFileSync(CURSOR_PATH, "utf8"));
  state.issuers ||= {};
  return state;
}

function exportPlan(planPath) {
  const baseByYear = new Map();
  const currentByYear = new Map();
  for (const item of recoveryFiles()) {
    const base = gitHeadJson(item.relative);
    if (base) baseByYear.set(item.year, base);
    currentByYear.set(item.year, JSON.parse(fs.readFileSync(item.file, "utf8")));
  }
  const plan = buildOfferDatePlan(baseByYear, currentByYear, readCursor());
  fs.writeFileSync(planPath, JSON.stringify(plan, null, 2) + "\n");
  console.log(JSON.stringify({
    exported_plan: planPath,
    date_change_records: plan.changes.length,
    cursor_entries: Object.keys(plan.cursor_state.issuers || {}).length
  }, null, 2));
}

function applyPlan(planPath) {
  const plan = JSON.parse(fs.readFileSync(planPath, "utf8"));
  const latestByYear = new Map();
  const fileByYear = new Map();
  for (const item of recoveryFiles()) {
    latestByYear.set(item.year, JSON.parse(fs.readFileSync(item.file, "utf8")));
    fileByYear.set(item.year, item.file);
  }
  const cursor = readCursor();
  const stats = applyOfferDatePlan(latestByYear, cursor, plan);
  const now = new Date().toISOString();

  for (const change of plan.changes || []) {
    const year = Number(change.year);
    const manifest = latestByYear.get(year);
    const file = fileByYear.get(year);
    if (!manifest || !file) continue;
    const touched = (manifest.records || []).some((record) =>
      record.id === change.id &&
      ["open_date", "close_date"].some((field) => record?.[field]?.value === change.fields?.[field]?.value)
    );
    if (!touched) continue;
    manifest.generated_at = now;
    fs.writeFileSync(file, JSON.stringify(manifest, null, 2) + "\n");
  }

  if (Object.keys(plan?.cursor_state?.issuers || {}).length > 0) {
    fs.mkdirSync(path.dirname(CURSOR_PATH), { recursive: true });
    fs.writeFileSync(CURSOR_PATH, JSON.stringify({
      schema_version: "1.0.0",
      issuers: cursor.issuers
    }, null, 2) + "\n");
  }

  console.log(JSON.stringify({ applied_historical_offer_date_plan: stats }, null, 2));
  if (stats.conflicts > 0 || stats.missing_records > 0) {
    console.warn("Historical offer-date plan applied with non-destructive conflicts/missing records.");
  }
}

function argValue(prefix) {
  const arg = process.argv.find((value) => value.startsWith(prefix + "="));
  return arg ? arg.slice(prefix.length + 1) : null;
}

function run() {
  const exportPath = argValue("--export-plan");
  const applyPath = argValue("--apply-plan");
  if (Boolean(exportPath) === Boolean(applyPath)) {
    throw new Error("Specify exactly one of --export-plan=<path> or --apply-plan=<path>");
  }
  if (exportPath) exportPlan(exportPath);
  else applyPlan(applyPath);
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run();
