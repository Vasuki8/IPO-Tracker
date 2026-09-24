import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'bse-publication-'));
try {
  // Run the real importer, publisher and validators in an isolated copy.
  for (const name of ['scripts', 'data', 'assets']) fs.cpSync(path.join(root, name), path.join(temp, name), { recursive: true });
  const file = path.join(temp, 'data/ipos.json');
  const before = JSON.parse(fs.readFileSync(file));
  const run = (script, ...args) => execFileSync(process.execPath, [script, ...args], { cwd: temp, encoding: 'utf8' });
  const importOutput = run('scripts/apply-verified-bse-listings.mjs');
  run('scripts/build-published-data.mjs'); run('scripts/build-published-data.mjs', '--check'); run('scripts/validate-data.mjs');
  const after = JSON.parse(fs.readFileSync(file));
  const byId = new Map(after.records.map((r) => [r.id, r]));
  for (const record of before.records) assert.deepEqual(byId.get(record.id), record, 'existing record changed: ' + record.id);
  const added = after.records.length - before.records.length;
  const beforeIds = new Set(before.records.map((record) => record.id));
  const addedRecords = after.records.filter((record) => !beforeIds.has(record.id));
  assert.equal(addedRecords.length, added);

  const verifiedRoot = path.join(temp, 'data/verified-bse-listings');
  const manifestNames = fs.readdirSync(verifiedRoot)
    .filter((name) => /^\d{4}-\d{2}-\d{2}(?:-batch\d+)?\.json$/.test(name));
  const approvedManifests = new Set(manifestNames.map((name) => 'data/verified-bse-listings/' + name));
  const approvedYears = new Set();
  let approvedEntries = 0;
  for (const name of manifestNames) {
    const manifest = JSON.parse(fs.readFileSync(path.join(verifiedRoot, name), 'utf8'));
    approvedEntries += manifest.entries.length;
    for (const entry of manifest.entries) approvedYears.add(entry.facts.listing_date.value.slice(0, 4));
  }
  assert.ok(added >= 0 && added <= approvedEntries, 'only approved reviewed records may be created');

  const recoveryPaths = fs.readdirSync(path.join(temp, 'data/recovery')).filter((y) => /^20\d{2}$/.test(y));
  const retainedById = new Map();
  for (const y of recoveryPaths) {
    const recoveryFile = path.join(temp, 'data/recovery', y, 'nse-issue-information.json');
    if (!fs.existsSync(recoveryFile)) continue;
    for (const record of JSON.parse(fs.readFileSync(recoveryFile, 'utf8')).records || []) {
      assert.ok(!retainedById.has(record.id), 'duplicate retained recovery id: ' + record.id);
      retainedById.set(record.id, record);
    }
  }
  for (const record of addedRecords) {
    const retained = retainedById.get(record.id);
    assert.ok(retained, 'added public record missing from retained recovery: ' + record.id);
    assert.ok(
      approvedManifests.has(retained.bse_verified_listing_batch?.manifest),
      'added record lacks approved reviewed-BSE provenance: ' + record.id
    );
  }

  for (const y of recoveryPaths.filter((y) => !approvedYears.has(y))) {
    const rel = 'data/recovery/' + y + '/nse-issue-information.json';
    assert.deepEqual(fs.readFileSync(path.join(temp, rel)), fs.readFileSync(path.join(root, rel)), 'unrelated historical manifest changed');
  }

  const firstBytes = fs.readFileSync(file);
  const recoveryBytes = new Map();
  for (const y of recoveryPaths) {
    const recoveryFile = path.join(temp, 'data/recovery', y, 'nse-issue-information.json');
    if (fs.existsSync(recoveryFile)) recoveryBytes.set(recoveryFile, fs.readFileSync(recoveryFile));
  }
  run('scripts/apply-verified-bse-listings.mjs'); run('scripts/build-published-data.mjs');
  assert.deepEqual(fs.readFileSync(file), firstBytes, 'repeat import freshened the public dataset');
  for (const [recoveryFile, bytes] of recoveryBytes) {
    assert.deepEqual(fs.readFileSync(recoveryFile), bytes, 'repeat import changed retained evidence: ' + recoveryFile);
  }
  console.log(JSON.stringify({ bse_publication_rehearsal: { before: before.records.length, after: after.records.length, added, existing_unchanged: before.records.length, idempotent: true }, import: JSON.parse(importOutput) }));
} finally { fs.rmSync(temp, { recursive: true, force: true }); }
