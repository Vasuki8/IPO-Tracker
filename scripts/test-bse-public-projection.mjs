import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { auditPublishedRelease, loadRelease, verifyLiveRelease } from './verify-bse-publication.mjs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const manifests = [18, 19].map((n) => `data/verified-bse-listings/2026-09-24-batch${n}.json`);
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'bse-public-projection-'));
const output = fs.mkdtempSync(path.join(os.tmpdir(), 'bse-projection-receipt-'));
try {
  // Build actual public output. Recovery-only hashes must not be injected into fixtures.
  for (const name of ['scripts', 'data', 'ops']) fs.cpSync(path.join(root, name), path.join(temp, name), { recursive: true });
  const run = (script) => execFileSync(process.execPath, [script], { cwd: temp, encoding: 'utf8' });
  run('scripts/apply-verified-bse-listings.mjs'); run('scripts/build-published-data.mjs');
  const dataPath = path.join(temp, 'data/ipos.json');
  const bytes = fs.readFileSync(dataPath);
  const cursorPath = path.join(temp, 'ops/bse-sme-addition-notices.json');
  const cursorBytes = fs.readFileSync(cursorPath);
  const report = await verifyLiveRelease({ root: temp, manifestPaths: manifests, outputDir: output,
    fetchImpl: async () => new Response(bytes) });
  assert.equal(report.status, 'verified', JSON.stringify(report));
  assert.equal(report.checked_issuers, 23); assert.equal(report.checked_fields, 69);
  assert.equal(report.document_hash_scope.retained_fields, 69);
  assert.equal(report.document_hash_scope.serialized_live_fields, 0);
  assert.deepEqual(fs.readFileSync(dataPath), bytes);
  assert.deepEqual(fs.readFileSync(cursorPath), cursorBytes);

  const recoveryByYear = Object.fromEntries(fs.readdirSync(path.join(temp, 'data/recovery'))
    .filter((y) => /^20\d{2}$/.test(y)).map((y) => [y, JSON.parse(fs.readFileSync(path.join(temp, 'data/recovery', y, 'nse-issue-information.json')))]));
  const fixture = { batches: loadRelease(temp, manifests), recoveryByYear, data: JSON.parse(bytes), checkedAt: new Date().toISOString() };
  const notice = fixture.batches[0].manifest.entries[0].listing_notice_no;
  const getRaw = (f) => f.recoveryByYear[2025].records.find((r) => r.bse_verified_listing_batch?.listing_notice_no === notice);
  const getLive = (f) => f.data.records.find((r) => r.id === getRaw(f).id);
  const cases = [
    (f) => delete getRaw(f).market_lot.source.document_sha256,
    (f) => getRaw(f).market_lot.source.document_sha256 = '0'.repeat(64),
    (f) => getRaw(f).market_lot.source_value = 'Unrelated source text',
    (f) => getLive(f).market_lot.evidence[0].document_sha256 = '0'.repeat(64),
    (f) => getLive(f).market_lot.evidence[0].document_sha256 = null,
    (f) => getLive(f).market_lot.evidence[0].document_type = 'BSE Index Notice',
    (f) => getLive(f).market_lot.corrections = [{ overwritten: 'history' }],
    (f) => getLive(f).open_date = { value: null, status: 'provisional', evidence: [] }
  ];
  for (const mutate of cases) {
    const changed = structuredClone(fixture); mutate(changed);
    assert.equal(auditPublishedRelease(changed).status, 'failed', mutate.toString());
  }
  const explicit = structuredClone(fixture);
  getLive(explicit).market_lot.evidence[0].document_sha256 = getRaw(explicit).market_lot.source.document_sha256;
  assert.equal(auditPublishedRelease(explicit).status, 'verified');
  assert.equal(auditPublishedRelease(explicit).document_hash_scope.serialized_live_fields, 1);
  console.log('Real publisher projection passed: 23 issuers / 69 fields; eight hash, type, history and null mutations rejected; files unchanged.');
} finally { fs.rmSync(temp, { recursive: true, force: true }); fs.rmSync(output, { recursive: true, force: true }); }
