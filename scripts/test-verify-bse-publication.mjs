import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { applyReviewedListingBatches } from './apply-verified-bse-listings.mjs';
import { sha256 } from './verify-bse-listing-candidates.mjs';
import { auditPublishedRelease, loadRelease, fetchPublishedSnapshot, verifyLiveRelease, LIVE_DATA_URL } from './verify-bse-publication.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const paths = [18, 19].map((n) => `data/verified-bse-listings/2026-09-24-batch${n}.json`);
const batches = loadRelease(root, paths);
const recoveryByYear = applyReviewedListingBatches({}, batches).recovery;
const generatedAt = '2026-09-24T08:00:00.000Z', checkedAt = '2026-09-24T15:00:00.000Z';
const otherFields = ['price_band', 'open_date', 'close_date', 'issue_size_inr', 'minimum_bid_quantity', 'minimum_application_amount_inr'];
const records = Object.values(recoveryByYear).flatMap((m) => m.records).map((r) => ({
  id: r.id, issuer_name: r.issuer_name, board: r.board, status: r.status,
  board_evidence: r.board_evidence, status_evidence: r.status_evidence,
  ...Object.fromEntries(['listing_date', 'market_lot', 'issue_price'].map((f) => [f, {
    value: r[f].value, status: r[f].status, corrections: [], evidence: [{ ...r[f].source, page: r[f].page }]
  }])),
  ...Object.fromEntries(otherFields.map((f) => [f, { value: null, status: 'missing', evidence: [], corrections: [] }]))
}));
const fixture = { batches, recoveryByYear, data: { schema_version: '1.2.0', generated_at: generatedAt, records }, checkedAt };
const before = JSON.stringify(fixture);
const good = auditPublishedRelease(fixture);
assert.equal(good.status, 'verified'); assert.equal(good.checked_issuers, 23); assert.equal(good.checked_fields, 69);
assert.equal(good.checked_at, checkedAt); assert.equal(good.dataset_generated_at, generatedAt);
assert.ok(good.results.every((r) => r.null_fields.length === 6));

const mutations = [
  (f) => f.data.records[0].market_lot.value++,
  (f) => f.data.records[0].issue_price.status = 'provisional',
  (f) => f.data.records[0].listing_date.value = null,
  (f) => f.data.records[0].market_lot.evidence[0].document_sha256 = '0'.repeat(64),
  (f) => f.data.records[0].listing_date.evidence[0].url = 'https://example.com/not-official',
  (f) => f.data.records[0].listing_date.evidence[0].page = 2,
  (f) => f.data.records[0].listing_date.evidence[0].collected_at = checkedAt,
  (f) => f.data.records[0].listing_date.evidence[0].publication_date = '2025-01-01',
  (f) => f.data.records[0].listing_date.evidence[0].document_identity = 'Another document',
  (f) => f.data.records[0].issue_price.corrections = null,
  (f) => f.data.records[0].board_evidence = [],
  (f) => f.data.records[0].status = 'upcoming',
  (f) => f.data.records[0].board = null,
  (f) => f.data.records[0].minimum_bid_quantity.value = 0,
  (f) => f.data.records[0].open_date = { value: '2025-01-01', status: 'verified', evidence: [] },
  (f) => f.data.records.push({ ...f.data.records[0], id: 'duplicate-name-new-id' }),
  (f) => f.data.records.shift(),
  (f) => f.recoveryByYear[2025].records[0].bse_scrip_code = '999999',
  (f) => f.recoveryByYear[2025].records[0].bse_verified_listing_batch.source_run_id = '123',
  (f) => f.recoveryByYear[2025].records[0].market_lot.value++,
  (f) => f.recoveryByYear[2024] = { records: [f.recoveryByYear[2025].records.pop()] }
];
for (const mutate of mutations) {
  const changed = structuredClone(fixture); mutate(changed);
  assert.equal(auditPublishedRelease(changed).status, 'failed', mutate.toString());
}
for (const mutate of [
  (f) => f.data.records.push(f.data.records[0]),
  (f) => f.data.schema_version = 'bad',
  (f) => f.data.generated_at = '2027-01-01T00:00:00Z',
  (f) => f.data.generated_at = 'not a date',
  (f) => f.batches = [],
  (f) => f.batches.push(f.batches[0]),
  (f) => f.batches[0].manifest.entries[0].facts.market_lot.value++
]) {
  const changed = structuredClone(fixture); mutate(changed);
  assert.throws(() => auditPublishedRelease(changed));
}
const enriched = structuredClone(fixture);
enriched.data.records[0].open_date = { value: '2025-01-01', status: 'verified', evidence: [{ url: 'https://www.bseindia.com/' }] };
assert.equal(auditPublishedRelease(enriched).status, 'verified', 'later evidenced fields are not forced back to null');
assert.equal(JSON.stringify(fixture), before, 'audit must not mutate records, evidence or clocks');
for (const paths of [[], ['../escape.json'], ['https://example.com'], ['data/verified-bse-listings/2026-09-24-batch18.json', 'data/verified-bse-listings/2026-09-24-batch18.json']]) {
  assert.throws(() => loadRelease(root, paths));
}
await assert.rejects(fetchPublishedSnapshot(async () => new Response('', { status: 403 })), /live_http_403/);
await assert.rejects(fetchPublishedSnapshot(async () => new Response('123456'), 5), /snapshot_size_limit/);
await assert.rejects(fetchPublishedSnapshot(async () => new Response('1', { headers: { 'content-length': '100' } }), 5), /snapshot_size_limit/);
await assert.rejects(fetchPublishedSnapshot(async () => { throw new Error('timeout'); }), /timeout/);

const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'bse-live-audit-'));
try {
  for (const b of batches) {
    for (const rel of [b.manifest_path, b.manifest.discovery_batch]) {
      const out = path.join(temp, rel); fs.mkdirSync(path.dirname(out), { recursive: true });
      fs.copyFileSync(path.join(root, rel), out);
    }
  }
  fs.mkdirSync(path.join(temp, 'data/recovery/2025'), { recursive: true });
  const rawPath = path.join(temp, 'data/recovery/2025/nse-issue-information.json');
  fs.writeFileSync(rawPath, JSON.stringify(recoveryByYear[2025]));
  const rawHash = sha256(fs.readFileSync(rawPath));
  const outputDir = path.join(temp, 'receipt');
  const bytes = JSON.stringify(fixture.data);
  const report = await verifyLiveRelease({ root: temp, manifestPaths: paths, outputDir, now: () => checkedAt,
    fetchImpl: async (url, options) => {
      assert.equal(url, LIVE_DATA_URL); assert.equal(options.redirect, 'error');
      assert.equal(options.headers['cache-control'], 'no-cache');
      return new Response(bytes);
    } });
  assert.equal(report.status, 'verified'); assert.equal(report.snapshot_sha256, sha256(bytes));
  assert.equal(report.snapshot_fetched_at, checkedAt);
  assert.equal(fs.readFileSync(path.join(outputDir, 'deployed-data.json'), 'utf8'), bytes);
  const failed = await verifyLiveRelease({ root: temp, manifestPaths: paths, outputDir, now: () => checkedAt,
    fetchImpl: async () => new Response('', { status: 503 }) });
  assert.equal(failed.status, 'failed'); assert.equal(failed.checked_at, null);
  assert.equal(failed.snapshot_sha256, undefined);
  assert.ok(!fs.existsSync(path.join(outputDir, 'deployed-data.json')), 'failed retry must not leave a stale live snapshot');
  assert.equal(JSON.parse(fs.readFileSync(path.join(outputDir, 'publication-report.json'))).error, 'live_http_503');
  const invalid = await verifyLiveRelease({ root: temp, manifestPaths: paths, outputDir, now: () => checkedAt,
    fetchImpl: async () => new Response('<html>Unavailable</html>') });
  assert.equal(invalid.status, 'failed'); assert.ok(invalid.snapshot_sha256);
  assert.equal(sha256(fs.readFileSync(rawPath)), rawHash, 'receipt never rewrites recovery');
} finally { fs.rmSync(temp, { recursive: true, force: true }); }
console.log('BSE live publication checks passed: 23 issuers / 69 fields; mutation, identity, provenance, clocks, HTTP/size failures and read-only receipt tests.');
