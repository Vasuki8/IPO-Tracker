import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { applyReviewedBatch, loadReviewed, loadRecovery, validateReviewedBatch, reviewedRecord, hash, FIELD_NAMES } from './apply-reviewed-nse-ipos.mjs';
import { issuerKey } from './verify-bse-listing-candidates.mjs';
import { fetchPublishedSnapshot, LIVE_DATA_URL } from './verify-bse-publication.mjs';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const sourceMatch = (actual, expected) => ['url', 'document_type', 'document_identity', 'publication_date', 'page', 'collected_at']
  .every(k => actual?.[k] === expected[k]) && (!Object.hasOwn(actual || {}, 'document_sha256') || actual.document_sha256 === expected.document_sha256);

// Read-only verification of the selected release, not an assertion that all
// fields of the entire IPO universe have been independently reverified.
export function auditReviewedPublication({ batch, recovery, data, checkedAt }) {
  if (data?.schema_version !== '1.2.0' || !Array.isArray(data.records) || !Number.isFinite(Date.parse(checkedAt)) ||
      !Number.isFinite(Date.parse(data.generated_at)) || Date.parse(data.generated_at) > Date.parse(checkedAt) ||
      new Set(data.records.map(r => r.id)).size !== data.records.length) throw new Error('invalid_public_snapshot');
  const { manifest, queue, manifest_path } = batch;
  const checked = validateReviewedBatch(manifest, queue);
  const plan = applyReviewedBatch(recovery, data, manifest, queue, manifest_path);
  if (plan.stats.added !== 0) throw new Error('reviewed_records_not_in_recovery');
  const results = checked.map((c, i) => {
    const expected = reviewedRecord(manifest.entries[i], c, manifest, manifest_path), errors = [];
    const raw = recovery[expected.listing_date.value.slice(0, 4)].records.find(r => r.id === expected.id);
    const hits = data.records.filter(r => r.id === expected.id || issuerKey(r.issuer_name) === issuerKey(expected.issuer_name));
    const live = hits.length === 1 ? hits[0] : null;
    if (!live || live.id !== expected.id || issuerKey(live.issuer_name) !== issuerKey(expected.issuer_name) ||
        live.board !== expected.board || live.status !== expected.status) errors.push('identity_board_status');
    for (const label of ['board_evidence', 'status_evidence']) if (!live?.[label]?.some(s => sourceMatch(s, expected[label][0]))) errors.push(label);
    for (const [f, fact] of Object.entries(c.facts)) {
      if (!same(live?.[f]?.value, fact.value) || live?.[f]?.status !== 'verified' ||
          !same(live?.[f]?.corrections, raw[f].corrections || []) || !live?.[f]?.evidence?.some(s => sourceMatch(s, fact.source))) errors.push(f);
    }
    const other = [...FIELD_NAMES, 'issue_size_inr', 'minimum_application_amount_inr'].filter(f => !c.facts[f]);
    for (const f of other) {
      const displayed = live?.[f], retained = raw[f];
      if (!displayed || !Array.isArray(displayed.evidence) || (displayed.value === null
        ? displayed.status !== 'missing' || displayed.evidence.length !== 0
        : displayed.status !== 'verified' || !same(retained?.value, displayed.value) || !retained?.source?.url || displayed.evidence.length === 0)) errors.push('unsupported_' + f);
    }
    if (live?.minimum_application_amount_inr?.value !== null) errors.push('out_of_scope_application_amount');
    return { symbol: c.candidate.nse_symbol, issuer_name: expected.issuer_name, id: expected.id, occurrences: hits.length,
      checked_fields: Object.keys(c.facts).length, retained_document_hash_fields: Object.keys(c.facts).length,
      facts: Object.fromEntries(Object.keys(c.facts).map(f => [f, live?.[f]?.value ?? null])),
      null_fields: other.filter(f => live?.[f]?.value === null), errors };
  });
  return { schema_version: '1.0.0', status: results.every(r => !r.errors.length) ? 'verified' : 'failed',
    checked_at: checkedAt, dataset_generated_at: data.generated_at, published_records: data.records.length,
    checked_issuers: results.length, checked_fields: results.reduce((n, r) => n + r.checked_fields, 0),
    failed_issuers: results.filter(r => r.errors.length).length,
    hash_scope: 'Original document hashes checked in recovery; public projection omits hashes.', results };
}
async function run() {
  const args = process.argv.slice(2);
  if (args.some(a => !a.startsWith('--manifest=') && !a.startsWith('--output-dir='))) throw new Error('invalid_arguments');
  const manifestPath = args.find(a => a.startsWith('--manifest='))?.slice(11);
  const output = args.find(a => a.startsWith('--output-dir='))?.slice(13);
  if (!manifestPath || !output) throw new Error('manifest_and_output_directory_required');
  const batch = loadReviewed(ROOT).find(b => b.manifest_path === manifestPath);
  if (!batch) throw new Error('unknown_reviewed_manifest');
  fs.mkdirSync(output, { recursive: true });
  fs.rmSync(path.join(output, 'deployed-data.json'), { force: true });
  let report = { status: 'failed', source_url: LIVE_DATA_URL, run_id: process.env.GITHUB_RUN_ID || null, read_only: true };
  try {
    const bytes = await fetchPublishedSnapshot(), fetchedAt = new Date().toISOString();
    fs.writeFileSync(path.join(output, 'deployed-data.json'), bytes);
    const audit = auditReviewedPublication({ batch, recovery: loadRecovery(ROOT), data: JSON.parse(bytes), checkedAt: new Date().toISOString() });
    report = { ...report, ...audit, manifest: manifestPath, snapshot_fetched_at: fetchedAt, snapshot_sha256: hash(bytes), snapshot_bytes: bytes.length };
  } catch (e) { report.error = e.message; }
  fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
  if (report.status !== 'verified') process.exitCode = 1;
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) await run();
