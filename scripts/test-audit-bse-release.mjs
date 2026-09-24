import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { auditBseRelease, fetchDeployedSnapshot, cursorSummary } from './audit-bse-release.mjs';
import { applyVerifiedListings } from './apply-verified-bse-listings.mjs';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const manifestPath = 'data/verified-bse-listings/2026-09-24-batch18.json';
const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, manifestPath)));
manifest.entries = manifest.entries.slice(0, 1);
const discovery = JSON.parse(fs.readFileSync(path.join(ROOT, manifest.discovery_batch)));
discovery.candidates = discovery.candidates.slice(0, 1);
const raw = applyVerifiedListings({}, manifest, discovery, manifestPath).recovery[2025].records[0];
const publicRecord = { id: raw.id, issuer_name: raw.issuer_name, board: 'SME', status: 'listed', documents: raw.documents };
for (const f of ['listing_date', 'market_lot', 'issue_price']) {
  const source = { ...raw[f].source }; delete source.document_sha256;
  publicRecord[f] = { value: raw[f].value, status: 'verified', evidence: [{ ...source, page: raw[f].page }], corrections: [] };
}
for (const f of ['price_band', 'open_date', 'close_date', 'issue_size_inr', 'minimum_bid_quantity', 'minimum_application_amount_inr']) {
  publicRecord[f] = { value: null, status: 'missing', evidence: [], corrections: [] };
}
const fixture = () => ({ batches: [{ manifest, discovery, manifestPath }], recoveryRecords: [structuredClone(raw)],
  published: { schema_version: '1.2.0', generated_at: '2026-09-24T10:00:00Z', records: [structuredClone(publicRecord)] },
  deployed: { schema_version: '1.2.0', generated_at: '2026-09-24T11:00:00Z', records: [structuredClone(publicRecord)] } });
assert.equal(auditBseRelease(fixture()).status, 'verified');
assert.equal(auditBseRelease(fixture()).entries[0].checks.deployed.serialized_document_hashes, 0);
let cases = 0;
function rejects(change, reason) { const x = fixture(); change(x); const r = auditBseRelease(x); assert.equal(r.status, 'failed', reason); assert.ok(r.entries[0].errors.includes(reason), JSON.stringify(r)); cases++; }
rejects((x) => x.deployed.records = [], 'deployed_identity_missing_or_duplicate');
rejects((x) => x.deployed.records.push(structuredClone(publicRecord)), 'deployed_identity_missing_or_duplicate');
rejects((x) => x.recoveryRecords.push({ ...raw, id: 'collision', issuer_name: 'Different issuer' }), 'recovery_code_collision');
rejects((x) => x.recoveryRecords[0].bse_verified_listing_batch.source_artifact_sha256 = '0'.repeat(64), 'recovery_batch_provenance_mismatch');
rejects((x) => x.recoveryRecords[0].issue_price.source.document_sha256 = '0'.repeat(64), 'recovery_issue_price_mismatch');
rejects((x) => x.recoveryRecords[0].market_lot.page = 88, 'recovery_market_lot_mismatch');
rejects((x) => x.deployed.records[0].market_lot.value++, 'deployed_market_lot_mismatch');
rejects((x) => x.deployed.records[0].listing_date.evidence[0].url = 'https://www.bseindices.com/', 'deployed_listing_date_mismatch');
rejects((x) => x.deployed.records[0].issue_price.evidence[0].document_identity = 'Other document', 'deployed_issue_price_mismatch');
rejects((x) => x.deployed.records[0].listing_date.evidence[0].collected_at = '2026-09-24T12:00:00Z', 'deployed_listing_date_mismatch');
rejects((x) => x.deployed.records[0].market_lot.corrections = [{ silently: 'rewritten' }], 'deployed_market_lot_mismatch');
rejects((x) => x.deployed.records[0].issue_price.evidence[0].document_sha256 = '0'.repeat(64), 'deployed_issue_price_hash_mismatch');
rejects((x) => x.deployed.records[0].documents = [], 'deployed_document_missing');
rejects((x) => x.deployed.records[0].open_date.value = '2025-01-01', 'deployed_open_date_unsupported_value');
rejects((x) => x.published.records[0].board = null, 'repository_identity_mismatch');
const enriched = fixture();
enriched.deployed.records.push({ id: 'unrelated', issuer_name: 'Unrelated additional issuer' });
enriched.deployed.records[0].open_date = { value: '2025-03-26', status: 'verified', evidence: [{ url: 'https://www.bseindia.com/example' }] };
assert.equal(auditBseRelease(enriched).status, 'verified', 'independent enrichment and site growth are permitted');
assert.throws(() => auditBseRelease({ ...fixture(), published: {} }), /invalid_repository_dataset/);
assert.throws(() => auditBseRelease({ ...fixture(), batches: [] }), /reviewed_batches_required/);
const duplicate = fixture(); duplicate.batches.push(duplicate.batches[0]);
assert.throws(() => auditBseRelease(duplicate), /duplicate_release_target/);
const stamp = '2026-09-24T12:00:00Z';
const snapshot = await fetchDeployedSnapshot({ fetchImpl: async () => new Response(JSON.stringify(fixture().deployed)), now: () => stamp });
assert.equal(snapshot.checked_at, stamp); assert.equal(snapshot.data.generated_at, '2026-09-24T11:00:00Z');
await assert.rejects(fetchDeployedSnapshot({ fetchImpl: async () => new Response('', { status: 503 }) }), /deployed_http_503/);
await assert.rejects(fetchDeployedSnapshot({ fetchImpl: async () => new Response('123456789'), maxBytes: 5 }), /deployed_size_limit/);
await assert.rejects(fetchDeployedSnapshot({ fetchImpl: async () => new Response('ok', { headers: { 'content-length': '100' } }), maxBytes: 5 }), /deployed_size_limit/);
await assert.rejects(fetchDeployedSnapshot({ fetchImpl: async () => new Response('<html>Unavailable</html>') }));
await assert.rejects(fetchDeployedSnapshot({ fetchImpl: async () => { throw new Error('network_timeout'); } }), /network_timeout/);
const candidate = discovery.candidates[0];
const state = { parser_version: '1.2.0', catalog: { eligible_count: 9 }, notices: {
  old: { notice_no: 'old', status: 'parsed', first_attempted_at: '2026-09-24T01:00:00Z', parsed_entries: [candidate] },
  new: { notice_no: 'new', status: 'parsed', first_attempted_at: '2026-09-24T02:00:00Z', parsed_entries: [{ ...candidate, listing_notice_no: '20250403-99' }] },
  failed: { status: 'unparseable', parsed_entries: [] }
} };
assert.equal(cursorSummary(state, [discovery]).unpinned_references, 1);
assert.equal(cursorSummary(state, [discovery]).statuses.unparseable, 1);
assert.equal(cursorSummary(state, []).pending[0].index_notice_no, 'old');

// Exercise the real importer and publisher, then prove the audit is read-only.
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'bse-release-test-'));
const output = fs.mkdtempSync(path.join(os.tmpdir(), 'bse-release-output-'));
try {
  for (const name of ['scripts', 'data', 'ops']) fs.cpSync(path.join(ROOT, name), path.join(temp, name), { recursive: true });
  const run = (script, ...args) => execFileSync(process.execPath, [script, ...args], { cwd: temp, encoding: 'utf8' });
  run('scripts/apply-verified-bse-listings.mjs'); run('scripts/build-published-data.mjs');
  const before = fs.readFileSync(path.join(temp, 'data/ipos.json'));
  const cursorBefore = fs.readFileSync(path.join(temp, 'ops/bse-sme-addition-notices.json'));
  const args = ['--manifests=' + manifestPath, '--output-dir=' + output, '--live=false'];
  const cli = JSON.parse(run('scripts/audit-bse-release.mjs', ...args));
  assert.equal(cli.status, 'verified'); assert.equal(cli.stats.issuers, 15);
  assert.equal(fs.existsSync(path.join(output, 'deployed-snapshot.json')), false);
  assert.deepEqual(fs.readFileSync(path.join(temp, 'data/ipos.json')), before);
  assert.deepEqual(fs.readFileSync(path.join(temp, 'ops/bse-sme-addition-notices.json')), cursorBefore);
  assert.throws(() => run('scripts/audit-bse-release.mjs', '--manifests=' + manifestPath, '--output-dir=' + temp), /outside_repository/);
} finally { fs.rmSync(temp, { recursive: true, force: true }); fs.rmSync(output, { recursive: true, force: true }); }
console.log(JSON.stringify({ bse_release_audit: 'passed', negative_identity_value_provenance_cases: cases, bounded_fetch_and_timestamp_tests: 'passed', real_pipeline_read_only_check: 'passed' }));
