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

  // A retained field is an indivisible observation: never merge its value,
  // status, source or correction history independently. On concurrent edits,
  // hold the complete current field and report a collision for review. This
  // applies to nested application requirements and to null/cleared fields too.
  const atomicField = [current, before, after].some((value) =>
    isObject(value) && Object.hasOwn(value, "value"));
  if (atomicField) {
    if (equal(current, before)) {
      stats.applied += 1;
      return { value: clone(after), changed: true, stats };
    }
    stats.conflicts += 1;
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

  for (const record of [...(proposal?.new_manifest?.records || []), ...(proposal?.added_records || [])]) {
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
      proposal?.manifest_generated_at_after ?? proposal?.new_manifest?.generated_at ?? null
    );
  }

  return { manifest, changed, stats };
}

function recordLocations(manifests) {
  const locations = new Map();
  for (const [relative, manifest] of Object.entries(manifests || {})) {
    for (const record of manifest?.records || []) {
      if (!record?.id) continue;
      const list = locations.get(record.id) || [];
      list.push({ relative, record });
      locations.set(record.id, list);
    }
  }
  return locations;
}

function comparableWithoutGeneratedAt(manifest) {
  if (!manifest) return manifest;
  const copy = clone(manifest);
  delete copy.generated_at;
  return copy;
}

function restoreIdentityFromCurrent(staged, current, id) {
  const paths = new Set([...Object.keys(staged), ...Object.keys(current)]);
  for (const relative of paths) {
    const stagedManifest = staged[relative];
    const currentManifest = current[relative];
    if (!stagedManifest && !currentManifest) continue;

    const currentRecords = currentManifest?.records || [];
    const currentRecord = currentRecords.find((record) => record.id === id);

    if (!stagedManifest) {
      if (currentRecord) staged[relative] = clone(currentManifest);
      continue;
    }

    const next = clone(stagedManifest);
    next.records = (next.records || []).filter((record) => record.id !== id);
    if (currentRecord) next.records.push(clone(currentRecord));
    next.records.sort((a, b) => String(a.issuer_name || "").localeCompare(String(b.issuer_name || "")));

    if (!currentManifest && next.records.length === 0) {
      delete staged[relative];
      continue;
    }

    if (currentManifest && equal(comparableWithoutGeneratedAt(next), comparableWithoutGeneratedAt(currentManifest))) {
      staged[relative] = clone(currentManifest);
    } else {
      staged[relative] = next;
    }
  }
}

function recoveryDelta(currentManifest, stagedManifest) {
  const before = new Map((currentManifest?.records || []).map((record) => [record.id, record]));
  const after = new Map((stagedManifest?.records || []).map((record) => [record.id, record]));
  let added = 0, removed = 0, changed = 0;
  for (const [id, record] of after) {
    if (!before.has(id)) added += 1;
    else if (!equal(before.get(id), record)) changed += 1;
  }
  for (const id of before.keys()) if (!after.has(id)) removed += 1;
  return { added, removed, changed };
}

export function applyRecoveryProposals(currentManifests, recoveryProposals) {
  const current = Object.fromEntries(
    Object.entries(currentManifests || {}).map(([relative, manifest]) => [relative, clone(manifest)])
  );
  const baselineLocations = recordLocations(current);
  for (const [id, locations] of baselineLocations) {
    if (locations.length > 1) {
      throw new Error("preexisting_recovery_identity_collision:" + id + ":" +
        locations.map((item) => item.relative).join(","));
    }
  }

  const staged = { ...current };
  const perManifest = {};
  let mergeConflicts = 0;
  let alreadyPresent = 0;
  let appliedOperations = 0;

  for (const [relative, proposal] of Object.entries(recoveryProposals || {})) {
    const result = applyRecoveryProposal(current[relative], proposal);
    perManifest[relative] = result;
    if (result.manifest) staged[relative] = result.manifest;
    else delete staged[relative];
    mergeConflicts += result.stats.conflicts;
    alreadyPresent += result.stats.already_present;
    appliedOperations += result.stats.applied_operations;
  }

  const stagedLocations = recordLocations(staged);
  const rolledBackIdentities = [];
  for (const [id, locations] of stagedLocations) {
    if (locations.length <= 1) continue;
    // A cross-year move is one logical identity transition. If a concurrent
    // edit prevents the source removal, roll the whole identity back rather
    // than accepting the target addition and creating duplicate stable IDs.
    restoreIdentityFromCurrent(staged, current, id);
    rolledBackIdentities.push(id);
  }

  const finalLocations = recordLocations(staged);
  for (const [id, locations] of finalLocations) {
    if (locations.length > 1) {
      throw new Error("unresolved_recovery_identity_collision:" + id + ":" +
        locations.map((item) => item.relative).join(","));
    }
  }

  const changedPaths = [];
  let addedRecords = 0, removedRecords = 0, changedRecords = 0;
  for (const relative of new Set([...Object.keys(current), ...Object.keys(staged), ...Object.keys(recoveryProposals || {})])) {
    const before = current[relative];
    const after = staged[relative];
    const delta = recoveryDelta(before, after);
    addedRecords += delta.added;
    removedRecords += delta.removed;
    changedRecords += delta.changed;
    if (!equal(before, after)) changedPaths.push(relative);
  }

  return {
    manifests: staged,
    changed_paths: changedPaths.sort(),
    stats: {
      manifests: Object.keys(recoveryProposals || {}).length,
      changed_manifests: changedPaths.length,
      added_records: addedRecords,
      changed_records: changedRecords,
      removed_records: removedRecords,
      applied_operations: appliedOperations,
      conflicts: mergeConflicts + rolledBackIdentities.length,
      already_present: alreadyPresent,
      cross_year_identity_rollbacks: rolledBackIdentities.length
    },
    rolled_back_identities: rolledBackIdentities.sort()
  };
}

function readJson(file) {
  return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, "utf8")) : undefined;
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + "\n");
}

function recoveryManifestPaths(root = ROOT) {
  const recoveryRoot = path.join(root, "data", "recovery");
  if (!fs.existsSync(recoveryRoot)) return [];
  return fs.readdirSync(recoveryRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^20\d{2}$/.test(entry.name))
    .map((entry) => `data/recovery/${entry.name}/nse-issue-information.json`)
    .filter((relative) => fs.existsSync(path.join(root, relative)))
    .sort();
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

  const currentRecovery = {};
  const recoveryPaths = [...new Set([
    ...recoveryManifestPaths(),
    ...Object.keys(proposal.recovery || {})
  ])].sort();
  for (const relative of recoveryPaths) {
    currentRecovery[relative] = readJson(path.join(ROOT, relative));
  }
  const recoveryResult = applyRecoveryProposals(currentRecovery, proposal.recovery || {});
  Object.assign(totals, {
    manifests: recoveryResult.stats.manifests,
    changed_manifests: recoveryResult.stats.changed_manifests,
    added_records: recoveryResult.stats.added_records,
    changed_records: recoveryResult.stats.changed_records,
    removed_records: recoveryResult.stats.removed_records,
    applied_operations: recoveryResult.stats.applied_operations,
    conflicts: recoveryResult.stats.conflicts,
    already_present: recoveryResult.stats.already_present
  });
  totals.cross_year_identity_rollbacks = recoveryResult.stats.cross_year_identity_rollbacks;

  for (const relative of recoveryResult.changed_paths) {
    const file = path.join(ROOT, relative);
    const manifest = recoveryResult.manifests[relative];
    if (manifest) writeJson(file, manifest);
    else if (fs.existsSync(file)) fs.unlinkSync(file);
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
