import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { validateEvidenceBatch } from './apply-verified-bse-listings.mjs';
import { issuerKey, sha256 } from './verify-bse-listing-candidates.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const LIVE_DATA_URL = 'https://vasuki8.github.io/IPO-Tracker/data/ipos.json';
const FIELDS = ['listing_date', 'market_lot', 'issue_price'];
const OTHER_FIELDS = ['price_band', 'open_date', 'close_date', 'issue_size_inr',
  'minimum_bid_quantity', 'minimum_application_amount_inr'];
const stamp = (v) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}T[\d:.]+Z$/.test(v) && Number.isFinite(Date.parse(v));
// Recovery must retain the original hash. Public evidence is a projection that
// currently omits it; an explicitly published hash must still match exactly.
const sourceMatches = (s, e, page, hashRequired = true) => s?.url === e.source_url &&
  s?.document_identity === e.document_identity &&
  s?.document_type === (e.evidence_kind === 'official_notice_html' ? 'BSE Listing Notice' : 'BSE Listing Notice PDF') &&
  (s?.document_sha256 === e.document_sha256 || (!hashRequired && !Object.hasOwn(s, 'document_sha256'))) &&
  s?.publication_date === e.publication_date && s?.collected_at === e.collected_at &&
  (page === undefined || s?.page === page);

// Pure comparison. A successful workflow/deployment is never evidence of a live value.
export function auditPublishedRelease({ batches, recoveryByYear, data, checkedAt }) {
  if (!Array.isArray(batches) || !batches.length) throw new Error('empty_release');
  if (data?.schema_version !== '1.2.0' || !Array.isArray(data.records)) throw new Error('invalid_live_dataset');
  if (!stamp(checkedAt) || !stamp(data.generated_at) || Date.parse(data.generated_at) > Date.parse(checkedAt)) {
    throw new Error('invalid_or_future_dataset_clock');
  }
  const ids = new Set();
  for (const r of data.records) {
    if (!r || typeof r.id !== 'string' || !r.id || typeof r.issuer_name !== 'string' || ids.has(r.id)) {
      throw new Error('invalid_or_duplicate_live_identity');
    }
    ids.add(r.id);
  }
  const recovery = Object.entries(recoveryByYear).flatMap(([year, m]) =>
    (m.records || []).map((r) => ({ year, record: r })));
  const seen = new Set(), results = [];
  for (const { manifest_path, manifest, discovery } of batches) {
    for (const e of validateEvidenceBatch(manifest, discovery)) {
      if (seen.has(e.bse_scrip_code)) throw new Error('duplicate_release_identity');
      seen.add(e.bse_scrip_code);
      const key = issuerKey(e.issuer_name), errors = [];
      const rawHits = recovery.filter(({ record: r }) => issuerKey(r.issuer_name) === key ||
        r.bse_scrip_code === e.bse_scrip_code || (r.documents || []).some((d) => d.url === e.source_url));
      const raw = rawHits.length === 1 ? rawHits[0].record : null;
      if (!raw || issuerKey(raw.issuer_name) !== key || raw.bse_scrip_code !== e.bse_scrip_code ||
          rawHits[0].year !== e.facts.listing_date.value.slice(0, 4)) errors.push('recovery_identity_mismatch');
      const provenance = raw?.bse_verified_listing_batch;
      if (!provenance || provenance.manifest !== manifest_path || provenance.listing_notice_no !== e.listing_notice_no ||
          provenance.verifier_version !== manifest.verifier_version || provenance.source_run_id !== manifest.source_run_id ||
          provenance.source_artifact_id !== manifest.source_artifact_id ||
          provenance.source_artifact_sha256 !== manifest.source_artifact_sha256) errors.push('recovery_provenance_mismatch');
      const hits = data.records.filter((r) => issuerKey(r.issuer_name) === key || (raw && r.id === raw.id));
      const live = hits.length === 1 ? hits[0] : null;
      if (!live || !raw || live.id !== raw.id || issuerKey(live.issuer_name) !== key) errors.push('live_identity_mismatch');
      if (live?.board !== e.board || live?.status !== 'listed') errors.push('live_board_or_status_mismatch');
      for (const evidence of ['board_evidence', 'status_evidence']) {
        if (!live?.[evidence]?.some((s) => sourceMatches(s, e, undefined, false))) errors.push(evidence + '_mismatch');
      }
      for (const field of FIELDS) {
        const fact = e.facts[field], retained = raw?.[field], displayed = live?.[field];
        if (retained?.value !== fact.value || retained?.status !== 'verified' || retained?.source_value !== fact.source_value ||
            !sourceMatches(retained?.source, e) || retained?.page !== (fact.page ?? null)) {
          errors.push('recovery_' + field + '_mismatch');
        }
        if (displayed?.value !== fact.value || displayed?.status !== 'verified' ||
            !Array.isArray(displayed?.corrections) ||
            JSON.stringify(displayed.corrections) !== JSON.stringify(retained?.corrections ?? []) ||
            !displayed?.evidence?.some((s) => sourceMatches(s, e, fact.page ?? null, false))) {
          errors.push('live_' + field + '_mismatch');
        }
      }
      // Later source-backed enrichment is allowed; missing must never mean zero/guessed.
      for (const field of OTHER_FIELDS) {
        const f = live?.[field];
        if (!f || !['missing', 'verified', 'provisional', 'conflict'].includes(f.status) || !Array.isArray(f.evidence) ||
            (f.status === 'missing' ? f.value !== null || f.evidence.length !== 0 : f.value == null || !f.evidence.length)) {
          errors.push('invalid_' + field);
        }
      }
      results.push({ issuer_name: e.issuer_name, listing_notice_no: e.listing_notice_no,
        manifest: manifest_path, public_occurrences: hits.length, recovery_occurrences: rawHits.length,
        facts: Object.fromEntries(FIELDS.map((f) => [f, live?.[f]?.value ?? null])),
        null_fields: OTHER_FIELDS.filter((f) => live?.[f]?.value === null),
        retained_document_hash_fields: FIELDS.filter((f) => raw?.[f]?.source?.document_sha256 === e.document_sha256).length,
        live_document_hash_fields: FIELDS.filter((f) => live?.[f]?.evidence?.some((s) => s.document_sha256 === e.document_sha256)).length, errors });
    }
  }
  return { status: results.every((r) => !r.errors.length) ? 'verified' : 'failed',
    checked_at: checkedAt, dataset_generated_at: data.generated_at, published_records: data.records.length,
    checked_issuers: results.length, checked_fields: results.length * FIELDS.length,
    failed_issuers: results.filter((r) => r.errors.length).length,
    document_hash_scope: { retained_fields: results.reduce((n, r) => n + r.retained_document_hash_fields, 0),
      serialized_live_fields: results.reduce((n, r) => n + r.live_document_hash_fields, 0),
      note: 'Original document hashes are verified in retained recovery. Missing public hashes are not reported as live hash verification.' }, results };
}

export function loadRelease(root, paths) {
  if (!Array.isArray(paths) || !paths.length || paths.length > 15 || new Set(paths).size !== paths.length) {
    throw new Error('invalid_manifest_selection');
  }
  return paths.map((manifest_path) => {
    if (!/^data\/verified-bse-listings\/\d{4}-\d{2}-\d{2}(?:-batch\d+)?\.json$/.test(manifest_path)) {
      throw new Error('invalid_manifest_path');
    }
    const bytes = fs.readFileSync(path.join(root, manifest_path));
    const manifest = JSON.parse(bytes);
    if (!/^data\/discovery\/bse-listing-candidates-\d{4}-\d{2}-\d{2}(?:-batch\d+)?\.json$/.test(manifest.discovery_batch)) {
      throw new Error('invalid_discovery_path');
    }
    const discovery = JSON.parse(fs.readFileSync(path.join(root, manifest.discovery_batch)));
    validateEvidenceBatch(manifest, discovery);
    return { manifest_path, manifest_sha256: sha256(bytes), manifest, discovery };
  });
}

export async function fetchPublishedSnapshot(fetchImpl = fetch, maxBytes = 32 * 1024 * 1024) {
  const response = await fetchImpl(LIVE_DATA_URL, { redirect: 'error', signal: AbortSignal.timeout(30000),
    headers: { 'cache-control': 'no-cache', accept: 'application/json' } });
  if (!response.ok || Number(response.headers.get('content-length')) > maxBytes) {
    await response.body?.cancel(); throw new Error(response.ok ? 'snapshot_size_limit' : 'live_http_' + response.status);
  }
  const chunks = []; let size = 0;
  for await (const chunk of response.body) {
    size += chunk.length;
    if (size > maxBytes) throw new Error('snapshot_size_limit');
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}

export async function verifyLiveRelease({ root = ROOT, manifestPaths, outputDir, fetchImpl = fetch,
  now = () => new Date().toISOString() }) {
  fs.mkdirSync(outputDir, { recursive: true });
  fs.rmSync(path.join(outputDir, 'deployed-data.json'), { force: true });
  const report = { schema_version: '1.0.0', status: 'failed', source_url: LIVE_DATA_URL,
    started_at: now(), checked_at: null, code_commit_sha: process.env.GITHUB_SHA || null,
    run_id: process.env.GITHUB_RUN_ID || null, read_only: true };
  try {
    const batches = loadRelease(root, manifestPaths);
    report.manifests = batches.map(({ manifest_path, manifest_sha256 }) => ({ path: manifest_path, sha256: manifest_sha256 }));
    const recoveryByYear = {};
    for (const year of fs.readdirSync(path.join(root, 'data/recovery')).filter((y) => /^20\d{2}$/.test(y))) {
      const file = path.join(root, 'data/recovery', year, 'nse-issue-information.json');
      if (fs.existsSync(file)) recoveryByYear[year] = JSON.parse(fs.readFileSync(file));
    }
    const bytes = await fetchPublishedSnapshot(fetchImpl);
    report.snapshot_fetched_at = now();
    report.snapshot_sha256 = sha256(bytes);
    report.snapshot_bytes = bytes.length;
    report.snapshot_file = 'deployed-data.json';
    fs.writeFileSync(path.join(outputDir, report.snapshot_file), bytes);
    Object.assign(report, auditPublishedRelease({ batches, recoveryByYear, data: JSON.parse(bytes), checkedAt: now() }));
    const file = path.join(root, 'ops/bse-sme-addition-notices.json');
    if (fs.existsSync(file)) {
      const cursor = JSON.parse(fs.readFileSync(file));
      const entries = Object.values(cursor.notices || {});
      report.cursor = { parser_version: cursor.parser_version, updated_at: cursor.updated_at,
        catalog: cursor.catalog, tracked: entries.length,
        statuses: entries.reduce((out, e) => { out[e.status] = (out[e.status] || 0) + 1; return out; }, {}) };
    }
  } catch (error) { report.status = 'failed'; report.error = String(error?.message || error); }
  report.finished_at = now();
  fs.writeFileSync(path.join(outputDir, 'publication-report.json'), JSON.stringify(report, null, 2) + '\n');
  return report;
}

async function run() {
  const args = Object.fromEntries(process.argv.slice(2).map((a) => {
    const i = a.indexOf('='); if (i < 0) throw new Error('arguments_require_equals'); return [a.slice(0, i), a.slice(i + 1)];
  }));
  if (!args['--manifests'] || !args['--output-dir'] || Object.keys(args).some((k) => !['--manifests', '--output-dir'].includes(k))) {
    throw new Error('use --manifests=<comma-separated-reviewed-paths> --output-dir=<artifact-directory>');
  }
  const report = await verifyLiveRelease({ manifestPaths: args['--manifests'].split(','), outputDir: path.resolve(args['--output-dir']) });
  console.log(JSON.stringify(report, null, 2));
  if (report.status !== 'verified') process.exitCode = 1;
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  run().catch((e) => { console.error(e); process.exitCode = 1; });
}
