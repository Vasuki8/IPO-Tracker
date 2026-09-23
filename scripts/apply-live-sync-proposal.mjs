import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function clone(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function equal(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function uniqueAppend(current, additions) {
  const result = Array.isArray(current) ? clone(current) : [];
  const seen = new Set(result.map((item) => JSON.stringify(item)));
  for (const item of additions) {
    const key = JSON.stringify(item);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(clone(item));
  }
  return result;
}

function arrayDifference(after, before) {
  const beforeKeys = new Set((before || []).map((item) => JSON.stringify(item)));
  return (after || []).filter((item) => !beforeKeys.has(JSON.stringify(item)));
}

function hasArrayRemovals(before, after) {
  const afterKeys = new Set((after || []).map((item) => JSON.stringify(item)));
  return (before || []).some((item) => !afterKeys.has(JSON.stringify(item)));
}

export function mergeThreeWay(current, before, after, stats = { applied: 0, conflicts: 0, already: 0 }) {
  if (equal(before, after)) return { value: clone(current), changed: false, stats };
  if (equal(current, after)) {
    stats.already += 1;
    return { value: clone(current), changed: false, stats };
  }

  if (Array.isArray(before) && Array.isArray(after) && Array.isArray(current)) {
    if (!hasArrayRemovals(before, after)) {
      const additions = arrayDifference(after, before);
      const merged = uniqueAppend(current, additions);
      const changed = !equal(merged, current);
      if (changed) stats.applied += 1;
      else stats.already += 1;
      return { value: merged, changed, stats };
    }
  }

  if (isObject(before) && isObject(after) && isObject(current)) {
    const result = clone(current);
    let changed = false;
    const keys = new Set([...Object.keys(before), ...Object.keys(after)]);
    for (const key of keys) {
      const beforeHas = Object.prototype.hasOwnProperty.call(before, key);
      const afterHas = Object.prototype.hasOwnProperty.call(after, key);
      const currentHas = Object.prototype.hasOwnProperty.call(current, key);

      if (!beforeHas && !afterHas) continue;

      if (!beforeHas && afterHas) {
        if (!currentHas) {
          result[key] = clone(after[key]);
          stats.applied += 1;
          changed = true;
        } else if (equal(current[key], after[key])) {
          stats.already += 1;
        } else {
          stats.conflicts += 1;
        }
        continue;
      }

      if (beforeHas && !afterHas) {
        if (currentHas && equal(current[key], before[key])) {
          delete result[key];
          stats.applied += 1;
          changed = true;
        } else if (!currentHas) {
          stats.already += 1;
        } else {
          stats.conflicts += 1;
        }
        continue;
      }

      const merged = mergeThreeWay(
        currentHas ? current[key] : undefined,
        before[key],
        after[key],
        stats
      );
      if (merged.changed) {
        result[key] = merged.value;
        changed = true;
      }
    }
    return { value: result, changed, stats };
  }

  if (equal(current, before)) {
    stats.applied += 1;
    return { value: clone(after), changed: true, stats };
  }

  stats.conflicts += 1;
  return { value: clone(current), changed: false, stats };
}

function maxTimestamp(a, b) {
  const ta = Date.parse(a || "");
  const tb = Date.parse(b || "");
  if (!Number.isFinite(ta)) return b ?? a ?? null;
  if (!Number.isFinite(tb)) return a ?? b ?? null;
  return ta >= tb ? a : b;
}

export function applyRecoveryProposal(currentManifest, proposal) {
  const stats = {
    added_records: 0,
    changed_records: 0,
    removed_records: 0,
    applied_operations: 0,
    conflicts: 0,
    already_present: 0
  };

  if (!currentManifest) {
    if (proposal?.new_manifest) {
      return { manifest: clone(proposal.new_manifest), changed: true, stats: { ...stats, added_records: proposal.new_manifest.records?.length || 0 } };
    }
    return { manifest: null, changed: false, stats };
  }

  const manifest = clone(currentManifest);
  manifest.records ||= [];
  const byId = new Map(manifest.records.map((record) => [record.id, record]));
  let changed = false;

  for (const record of proposal?.added_records || []) {
    if (!byId.has(record.id)) {
      const added = clone(record);
      manifest.records.push(added);
      byId.set(added.id, added);
      stats.added_records += 1;
      changed = true;
    } else if (equal(byId.get(record.id), record)) {
      stats.already_present += 1;
    } else {
      stats.conflicts += 1;
    }
  }

  for (const change of proposal?.changed_records || []) {
    const current = byId.get(change.id);
    if (!current) {
      stats.conflicts += 1;
      continue;
    }
    const mergeStats = { applied: 0, conflicts: 0, already: 0 };
    const merged = mergeThreeWay(current, change.before, change.after, mergeStats);
    stats.applied_operations += mergeStats.applied;
    stats.conflicts += mergeStats.conflicts;
    stats.already_present += mergeStats.already;
    if (merged.changed) {
      const index = manifest.records.findIndex((record) => record.id === change.id);
      manifest.records[index] = merged.value;
      byId.set(change.id, merged.value);
      stats.changed_records += 1;
      changed = true;
    }
  }

  for (const removal of proposal?.removed_records || []) {
    const current = byId.get(removal.id);
    if (!current) {
      stats.already_present += 1;
      continue;
    }
    if (!equal(current, removal.before)) {
      stats.conflicts += 1;
      continue;
    }
    manifest.records = manifest.records.filter((record) => record.id !== removal.id);
    byId.delete(removal.id);
    stats.removed_records += 1;
    changed = true;
  }

  if (changed) {
    manifest.records.sort((a, b) => String(a.issuer_name || "").localeCompare(String(b.issuer_name || "")));
    manifest.generated_at = maxTimestamp(
      manifest.generated_at,
      proposal?.manifest_generated_at_after ?? null
    );
  }

  return { manifest, changed, stats };
}

function readJson(file) {
  return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, "utf8")) : undefined;
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + "\n");
}

function applyCursorProposal(current, proposal) {
  const stats = { applied: 0, conflicts: 0, already: 0 };
  const before = proposal?.before_exists ? proposal.before : undefined;
  const after = proposal?.after_exists ? proposal.after : undefined;
  const merged = mergeThreeWay(current, before, after, stats);
  return { value: merged.value, changed: merged.changed, stats };
}

async function run() {
  const inputArg = process.argv.find((arg) => arg.startsWith("--input="));
  if (!inputArg) throw new Error("--input=<proposal.json> is required");
  const proposal = readJson(path.resolve(inputArg.slice("--input=".length)));
  if (!proposal || proposal.schema_version !== "1.0.0") throw new Error("invalid live-sync proposal");

  const totals = {
    manifests: 0,
    changed_manifests: 0,
    added_records: 0,
    changed_records: 0,
    removed_records: 0,
    applied_operations: 0,
    conflicts: 0,
    already_present: 0,
    cursor_files: 0,
    changed_cursor_files: 0
  };

  for (const [relative, recoveryProposal] of Object.entries(proposal.recovery || {})) {
    totals.manifests += 1;
    const file = path.join(ROOT, relative);
    const current = readJson(file);
    const result = applyRecoveryProposal(current, recoveryProposal);
    if (!result.manifest) continue;
    const s = result.stats;
    totals.added_records += s.added_records;
    totals.changed_records += s.changed_records;
    totals.removed_records += s.removed_records;
    totals.applied_operations += s.applied_operations;
    totals.conflicts += s.conflicts;
    totals.already_present += s.already_present;
    if (result.changed) {
      writeJson(file, result.manifest);
      totals.changed_manifests += 1;
    }
  }

  for (const [relative, cursorProposal] of Object.entries(proposal.cursors || {})) {
    totals.cursor_files += 1;
    const file = path.join(ROOT, relative);
    const current = readJson(file);
    const result = applyCursorProposal(current, cursorProposal);
    totals.applied_operations += result.stats.applied;
    totals.conflicts += result.stats.conflicts;
    totals.already_present += result.stats.already;
    if (result.changed) {
      if (cursorProposal.after_exists) writeJson(file, result.value);
      else if (fs.existsSync(file)) fs.unlinkSync(file);
      totals.changed_cursor_files += 1;
    }
  }

  console.log(JSON.stringify({ live_sync_semantic_merge: totals }, null, 2));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => { console.error(error); process.exit(1); });
