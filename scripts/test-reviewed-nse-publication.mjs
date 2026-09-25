import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { loadReviewed, loadRecovery } from './apply-reviewed-nse-ipos.mjs';
import { auditReviewedPublication } from './verify-reviewed-nse-publication.mjs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..'), temp = fs.mkdtempSync(path.join(os.tmpdir(), 'reviewed-nse-'));
try {
  for (const d of ['scripts', 'data', 'assets']) fs.cpSync(path.join(root, d), path.join(temp, d), { recursive: true });
  const batches = loadReviewed(temp), batch = batches[0], file = path.join(temp, 'data/ipos.json'), before = JSON.parse(fs.readFileSync(file));
  const run = (s, ...a) => execFileSync(process.execPath, ['scripts/' + s, ...a], { cwd: temp, encoding: 'utf8' });
  const imported = JSON.parse(run('apply-reviewed-nse-ipos.mjs'));
  run('build-published-data.mjs'); run('build-published-data.mjs', '--check'); run('validate-data.mjs');
  const bytes = fs.readFileSync(file), data = JSON.parse(bytes), byId = new Map(data.records.map(r => [r.id, r]));
  for (const r of before.records) assert.deepEqual(byId.get(r.id), r, 'existing public record changed: ' + r.id);
  assert.equal(data.records.length - before.records.length, imported.reviewed_nse_import.added);
  assert.ok(imported.reviewed_nse_import.added >= 0 && imported.reviewed_nse_import.added <= batches.reduce((n, b) => n + b.manifest.entries.length, 0));
  const recovery = loadRecovery(temp), checkedAt = new Date().toISOString();
  for (const selected of batches) assert.equal(auditReviewedPublication({ batch: selected, recovery, data, checkedAt }).status, 'verified');
  const audit = auditReviewedPublication({ batch, recovery, data, checkedAt });
  assert.equal(audit.status, 'verified'); assert.equal(audit.checked_issuers, 14); assert.equal(audit.checked_fields, 83);
  for (const result of audit.results) {
    const r = byId.get(result.id); assert.equal(r.minimum_application_amount_inr.value, null);
    const raw = recovery['2026'].records.find(r => r.id === result.id); assert.equal(raw.nse_verified_ipo_batch.manifest, batch.manifest_path);
  }
  for (const [label, mutate] of [
    ['missing issuer', d => { d.records = d.records.filter(r => r.id !== audit.results[0].id); }],
    ['wrong field', d => { d.records.find(r => r.id === audit.results[0].id).market_lot.value = 1; }],
    ['wrong evidence clock', d => { d.records.find(r => r.id === audit.results[0].id).listing_date.evidence[0].collected_at = '2020-01-01T00:00:00Z'; }],
    ['wrong board', d => { d.records.find(r => r.id === audit.results[0].id).board = 'Mainboard'; }]
  ]) { const d = structuredClone(data); mutate(d); assert.equal(auditReviewedPublication({ batch, recovery, data: d, checkedAt }).status, 'failed', label); }
  assert.throws(() => auditReviewedPublication({ batch, recovery, data: { ...data, records: [...data.records, data.records[0]] }, checkedAt }));
  const saved = Object.fromEntries(Object.keys(recovery).map(y => [y, fs.readFileSync(path.join(temp, 'data/recovery', y, 'nse-issue-information.json'))]));
  run('apply-reviewed-nse-ipos.mjs'); run('build-published-data.mjs');
  assert.deepEqual(fs.readFileSync(file), bytes, 'repeat import changed published bytes');
  for (const [y, b] of Object.entries(saved)) assert.deepEqual(fs.readFileSync(path.join(temp, 'data/recovery', y, 'nse-issue-information.json')), b);
  console.log(JSON.stringify({ reviewed_nse_rehearsal: { before: before.records.length, after: data.records.length, added: imported.reviewed_nse_import.added,
    existing_unchanged: before.records.length, fields_verified: audit.checked_fields, batches: batches.map(b => { const a = auditReviewedPublication({ batch: b, recovery, data, checkedAt }); return { manifest: b.manifest_path, issuers: a.checked_issuers, facts: a.checked_fields, status: a.status }; }), idempotent: true, live_mutations_rejected: 5 } }));
} finally { fs.rmSync(temp, { recursive: true, force: true }); }
