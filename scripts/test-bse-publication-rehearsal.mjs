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
  assert.ok(added >= 0 && added <= 27, 'only approved reviewed records may be created');
  const recoveryPaths = fs.readdirSync(path.join(temp, 'data/recovery')).filter((y) => /^20\d{2}$/.test(y));
  for (const y of recoveryPaths.filter((y) => y !== '2026')) {
    const rel = 'data/recovery/' + y + '/nse-issue-information.json';
    assert.deepEqual(fs.readFileSync(path.join(temp, rel)), fs.readFileSync(path.join(root, rel)), 'unrelated historical manifest changed');
  }
  const firstBytes = fs.readFileSync(file);
  const recoveryFile = path.join(temp, 'data/recovery/2026/nse-issue-information.json');
  const recoveryBytes = fs.readFileSync(recoveryFile);
  run('scripts/apply-verified-bse-listings.mjs'); run('scripts/build-published-data.mjs');
  assert.deepEqual(fs.readFileSync(file), firstBytes, 'repeat import freshened the public dataset');
  assert.deepEqual(fs.readFileSync(recoveryFile), recoveryBytes, 'repeat import changed retained evidence');
  console.log(JSON.stringify({ bse_publication_rehearsal: { before: before.records.length, after: after.records.length, added, existing_unchanged: before.records.length, idempotent: true }, import: JSON.parse(importOutput) }));
} finally { fs.rmSync(temp, { recursive: true, force: true }); }
