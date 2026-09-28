import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const TARGET = 'data/recovery/2020/nse-issue-information.json';
const REVIEW = 'data/discovery/bse-2020-unmatched-review-2026-09-26.json';
const RECEIPT = 'data/evidence/bse-2020-unmatched-source-receipt-2026-09-26.json';
const MANIFEST = 'data/verified-bse-listings/2026-09-26-bse-2020-unmatched-four.json';
const INPUTS = [TARGET, REVIEW, RECEIPT, MANIFEST];
const protectedBytes = new Map(INPUTS.map(p => [p, fs.readFileSync(path.join(ROOT, p))]));
const review = JSON.parse(protectedBytes.get(REVIEW));
const recovery = JSON.parse(protectedBytes.get(TARGET));
const ids = new Set(review.actions.map(a => a.stable_id));
assert.equal(ids.size, 4);
for (const a of review.actions) {
  const hits = recovery.records.filter(r => r.id === a.stable_id);
  assert.ok(hits.length <= 1, `duplicate reviewed candidate: ${a.stable_id}`);
  if (hits.length) assert.equal(hits[0].bse_2020_unmatched_import?.action_key, a.key);
}

// A one-shot importer intentionally rejects later enrichment. Test its release
// lifecycle in an isolated copy, never by replaying it against mutable production.
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ipo-2020-import-'));
try {
  for (const p of [...INPUTS, 'scripts/apply-reviewed-bse-2020-unmatched.mjs', 'scripts/materialize-bse-2020-unmatched-evidence.mjs']) {
    fs.mkdirSync(path.dirname(path.join(tmp, p)), {recursive: true});
    fs.copyFileSync(path.join(ROOT, p), path.join(tmp, p));
  }
  const file = path.join(tmp, TARGET);
  const before = structuredClone(recovery);
  before.records = before.records.filter(r => !ids.has(r.id));
  fs.writeFileSync(file, JSON.stringify(before, null, 2) + '\n');
  const run = (...args) => spawnSync(process.execPath, [path.join(tmp, 'scripts/apply-reviewed-bse-2020-unmatched.mjs'), ...args], {cwd: tmp, encoding: 'utf8', timeout: 10000});
  const checkedBytes = fs.readFileSync(file), check = run('--check');
  assert.equal(check.status, 0, check.stderr);
  assert.deepEqual(JSON.parse(check.stdout).bse_2020_unmatched_import, {records: 4, changed: true});
  assert.deepEqual(fs.readFileSync(file), checkedBytes, 'check must be read-only');
  const apply = run();
  assert.equal(apply.status, 0, apply.stderr);
  const afterBytes = fs.readFileSync(file), after = JSON.parse(afterBytes);
  assert.equal(after.records.length, before.records.length + 4);
  for (const old of before.records) assert.deepEqual(after.records.find(r => r.id === old.id), old);
  for (const a of review.actions) {
    const hits = after.records.filter(r => r.id === a.stable_id);
    assert.equal(hits.length, 1);
    assert.equal(hits[0].bse_2020_unmatched_import.action_key, a.key);
    assert.equal(hits[0].bse_2020_unmatched_import.manifest, MANIFEST);
    assert.equal(hits[0].issue_price.value, a.target.issue_price);
    assert.equal(hits[0].listing_date.value, a.target.listing_date);
    assert.equal(hits[0].issue_size_inr.value, null);
  }
  const repeatCheck = run('--check');
  assert.equal(repeatCheck.status, 0, repeatCheck.stderr);
  assert.deepEqual(JSON.parse(repeatCheck.stdout).bse_2020_unmatched_import, {records: 4, changed: false});
  assert.equal(run().status, 0);
  assert.deepEqual(fs.readFileSync(file), afterBytes, 'exact rerun must be byte-stable');
  for (const change of [r => r.issue_price.value++, r => { r.last_collected_at = '2099-01-01T00:00:00Z'; }, r => { r.documents.push({type: 'Later evidence', url: 'https://www.sebi.gov.in/later.pdf'}); }]) {
    const enriched = structuredClone(after);
    change(enriched.records.find(r => r.id === review.actions[0].stable_id));
    fs.writeFileSync(file, JSON.stringify(enriched, null, 2) + '\n');
    const guardedBytes = fs.readFileSync(file);
    for (const args of [['--check'], []]) {
      const rejected = run(...args);
      assert.notEqual(rejected.status, 0, 'changed evidence must not be overwritten');
      assert.match(rejected.stderr, /collision:/);
      assert.deepEqual(fs.readFileSync(file), guardedBytes, 'rejection must not modify input');
    }
  }
} finally {
  fs.rmSync(tmp, {recursive: true, force: true});
  for (const [p, bytes] of protectedBytes) assert.deepEqual(fs.readFileSync(path.join(ROOT, p)), bytes, `production input modified: ${p}`);
}
console.log(JSON.stringify({bse_2020_unmatched_import_tests: {records: 4,isolated_lifecycle: true,read_only: true,rerun_safe: true,enrichment_collision_guards: 6,unrelated_records_unchanged: true,production_unchanged: true}}));
