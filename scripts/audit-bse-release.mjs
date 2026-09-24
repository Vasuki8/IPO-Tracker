import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { issuerKey, sha256 } from './verify-bse-listing-candidates.mjs';
import { validateEvidenceBatch } from './apply-verified-bse-listings.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const LIVE_URL = 'https://vasuki8.github.io/IPO-Tracker/data/ipos.json';
const FIELDS = ['listing_date', 'market_lot', 'issue_price'];
const OTHER_FIELDS = ['price_band', 'open_date', 'close_date', 'issue_size_inr', 'minimum_bid_quantity', 'minimum_application_amount_inr'];
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const read = (file) => JSON.parse(fs.readFileSync(file, 'utf8'));

// Compare a pinned reviewed release, not an expected whole-site record count.
// Unrelated source enrichment or additional IPOs must not fail this check.
export function auditBseRelease({ batches, recoveryRecords, published, deployed = null }) {
  if (!Array.isArray(batches) || !batches.length) throw new Error('reviewed_batches_required');
  const targets = batches.flatMap(({ manifest, discovery, manifestPath }) =>
    validateEvidenceBatch(manifest, discovery).map((entry) => ({ entry, manifest, manifestPath })));
  if (new Set(targets.map(({ entry }) => entry.listing_notice_no)).size !== targets.length) {
    throw new Error('duplicate_release_target');
  }
  if (!Array.isArray(recoveryRecords)) throw new Error('invalid_recovery_records');
  const datasets = { repository: published, ...(deployed ? { deployed } : {}) };
  for (const [name, data] of Object.entries(datasets)) {
    if (data?.schema_version !== '1.2.0' || !Array.isArray(data.records) ||
        !Number.isFinite(Date.parse(data.generated_at))) throw new Error('invalid_' + name + '_dataset');
  }
  const entries = targets.map(({ entry: e, manifest, manifestPath }) => {
    const errors = [], checks = {};
    const matches = recoveryRecords.filter((r) => issuerKey(r.issuer_name) === issuerKey(e.issuer_name));
    const raw = matches.length === 1 ? matches[0] : null;
    if (!raw) errors.push('recovery_identity_missing_or_duplicate');
    if (recoveryRecords.some((r) => r.bse_scrip_code === e.bse_scrip_code &&
        issuerKey(r.issuer_name) !== issuerKey(e.issuer_name))) errors.push('recovery_code_collision');
    if (raw) {
      if (raw.bse_scrip_code !== e.bse_scrip_code || raw.board !== 'SME' || raw.status !== 'listed') errors.push('recovery_identity_mismatch');
      const batch = raw.bse_verified_listing_batch;
      const expected = { manifest: manifestPath, verifier_version: manifest.verifier_version,
        source_run_id: manifest.source_run_id, source_artifact_id: manifest.source_artifact_id,
        source_artifact_sha256: manifest.source_artifact_sha256, listing_notice_no: e.listing_notice_no };
      if (!Object.entries(expected).every(([k, v]) => batch?.[k] === v)) errors.push('recovery_batch_provenance_mismatch');
      if (!(raw.documents || []).some((d) => d.url === e.source_url && d.document_sha256 === e.document_sha256)) errors.push('recovery_document_hash_mismatch');
      for (const f of FIELDS) {
        const field = raw[f], source = field?.source;
        if (field?.value !== e.facts[f].value || field?.status !== 'verified' ||
            field?.source_value !== e.facts[f].source_value || (field?.page ?? null) !== (e.facts[f].page ?? null) ||
            source?.url !== e.source_url || source?.document_sha256 !== e.document_sha256 ||
            source?.document_identity !== e.document_identity || source?.publication_date !== e.publication_date ||
            source?.collected_at !== e.collected_at) errors.push('recovery_' + f + '_mismatch');
      }
    }
    for (const [name, data] of Object.entries(datasets)) {
      const found = data.records.filter((r) => issuerKey(r.issuer_name) === issuerKey(e.issuer_name) || (raw && r.id === raw.id));
      const r = found.length === 1 ? found[0] : null;
      checks[name] = { occurrences: found.length, fields_verified: 0, unsupported_fields_missing: 0, serialized_document_hashes: 0 };
      if (!r) { errors.push(name + '_identity_missing_or_duplicate'); continue; }
      if (r.id !== raw?.id || issuerKey(r.issuer_name) !== issuerKey(e.issuer_name) || r.board !== 'SME' || r.status !== 'listed') errors.push(name + '_identity_mismatch');
      for (const f of FIELDS) {
        const field = r[f];
        const evidence = field?.evidence?.filter((s) => s.url === e.source_url && s.document_identity === e.document_identity &&
          s.document_type === (e.evidence_kind === 'official_notice_html' ? 'BSE Listing Notice' : 'BSE Listing Notice PDF') &&
          s.publication_date === e.publication_date && s.collected_at === e.collected_at &&
          (s.page ?? null) === (e.facts[f].page ?? null)) || [];
        if (field?.value !== e.facts[f].value || field?.status !== 'verified' || !evidence.length ||
            !equal(field?.corrections, raw?.[f]?.corrections ?? [])) errors.push(name + '_' + f + '_mismatch');
        else checks[name].fields_verified++;
        // The current public schema omits hashes. Never label a raw-only hash as live evidence.
        for (const s of evidence) if (s.document_sha256 != null) {
          if (s.document_sha256 !== e.document_sha256) errors.push(name + '_' + f + '_hash_mismatch');
          else checks[name].serialized_document_hashes++;
        }
      }
      if (!(r.documents || []).some((d) => d.url === e.source_url && d.identity === e.document_identity &&
          d.publication_date === e.publication_date && d.collected_at === e.collected_at)) errors.push(name + '_document_missing');
      for (const f of OTHER_FIELDS) {
        const field = r[f];
        if (field?.value === null && field.status === 'missing' && Array.isArray(field.evidence) && !field.evidence.length) checks[name].unsupported_fields_missing++;
        else if (field?.value == null || !['verified', 'provisional', 'conflict'].includes(field.status) ||
            !Array.isArray(field.evidence) || !field.evidence.length || field.evidence.some((s) => !s.url)) errors.push(name + '_' + f + '_unsupported_value');
      }
    }
    return { issuer_name: e.issuer_name, listing_notice_no: e.listing_notice_no, bse_scrip_code: e.bse_scrip_code,
      manifest: manifestPath, status: errors.length ? 'failed' : 'verified', checks, errors };
  });
  return { status: entries.every((e) => e.status === 'verified') ? 'verified' : 'failed',
    stats: { issuers: entries.length, verified: entries.filter((e) => e.status === 'verified').length,
      failed: entries.filter((e) => e.status === 'failed').length, expected_fields_per_dataset: entries.length * FIELDS.length },
    snapshots: Object.fromEntries(Object.entries(datasets).map(([name, data]) => [name, { records: data.records.length, generated_at: data.generated_at }])), entries };
}

export async function fetchDeployedSnapshot({ fetchImpl = fetch, now = () => new Date().toISOString(), maxBytes = 16 * 1024 * 1024 } = {}) {
  const response = await fetchImpl(LIVE_URL, { redirect: 'error', signal: AbortSignal.timeout(30000), headers: { 'cache-control': 'no-cache' } });
  if (!response.ok) { await response.body?.cancel(); throw new Error('deployed_http_' + response.status); }
  if (Number(response.headers.get('content-length')) > maxBytes) { await response.body?.cancel(); throw new Error('deployed_size_limit'); }
  const chunks = []; let size = 0;
  for await (const chunk of response.body) {
    size += chunk.length;
    if (size > maxBytes) throw new Error('deployed_size_limit');
    chunks.push(Buffer.from(chunk));
  }
  const bytes = Buffer.concat(chunks);
  return { url: LIVE_URL, checked_at: now(), response_sha256: sha256(bytes), response_bytes: size, data: JSON.parse(bytes.toString('utf8')) };
}

export function cursorSummary(state, pinnedBatches) {
  const pinned = new Set(pinnedBatches.flatMap((b) => (b.candidates || []).map((c) => c.listing_notice_no + '|' + c.bse_scrip_code)));
  const notices = Object.values(state.notices || {}), counts = {}, pending = [];
  for (const n of notices) {
    counts[n.status] = (counts[n.status] || 0) + 1;
    if (n.status !== 'parsed') continue;
    for (const e of n.parsed_entries || []) if (!pinned.has(e.listing_notice_no + '|' + e.bse_scrip_code)) {
      pending.push({ ...e, index_notice_no: n.notice_no, index_notice_source_url: n.source_url,
        extracted_text_sha256: n.extracted_text_sha256, first_attempted_at: n.first_attempted_at });
    }
  }
  pending.sort((a, b) => String(a.first_attempted_at).localeCompare(String(b.first_attempted_at)) || b.listing_date.localeCompare(a.listing_date));
  return { parser_version: state.parser_version, observed_at: state.updated_at, tracked_notices: notices.length,
    eligible_notices: state.catalog?.eligible_count ?? null, statuses: counts, unpinned_references: pending.length,
    pending, scope_note: 'Unpinned discovery references are not confirmed missing IPOs. Reconcile before independent source verification; do not skip older unprocessed segments.' };
}

async function run() {
  const args = Object.fromEntries(process.argv.slice(2).map((a) => {
    const i = a.indexOf('='); if (i < 0) throw new Error('arguments_require_equals'); return [a.slice(0, i), a.slice(i + 1)];
  }));
  if (!args['--manifests'] || !args['--output-dir'] || Object.keys(args).some((k) => !['--manifests', '--output-dir', '--live'].includes(k)) ||
      (args['--live'] != null && !['true', 'false'].includes(args['--live']))) throw new Error('use --manifests=<paths,comma-separated> --output-dir=<outside-repository> [--live=true]');
  const output = path.resolve(args['--output-dir']);
  if (output === ROOT || output.startsWith(ROOT + path.sep)) throw new Error('output_must_be_outside_repository');
  fs.mkdirSync(output, { recursive: true });
  const report = { schema_version: '1.0.0', checked_at: new Date().toISOString(), run_id: process.env.GITHUB_RUN_ID || null,
    commit_sha: process.env.GITHUB_SHA || null, status: 'failed' };
  try {
    const batches = args['--manifests'].split(',').map((manifestPath) => {
      if (!/^data\/verified-bse-listings\/\d{4}-\d{2}-\d{2}(?:-batch\d+)?\.json$/.test(manifestPath)) throw new Error('invalid_manifest_path');
      const manifest = read(path.join(ROOT, manifestPath));
      if (!/^data\/discovery\/bse-listing-candidates-[\w-]+\.json$/.test(manifest.discovery_batch)) throw new Error('invalid_discovery_path');
      return { manifestPath, manifest, discovery: read(path.join(ROOT, manifest.discovery_batch)) };
    });
    const recoveryRecords = fs.readdirSync(path.join(ROOT, 'data/recovery')).filter((y) => /^20\d{2}$/.test(y))
      .flatMap((y) => read(path.join(ROOT, 'data/recovery', y, 'nse-issue-information.json')).records);
    const published = read(path.join(ROOT, 'data/ipos.json'));
    const live = args['--live'] === 'true' ? await fetchDeployedSnapshot() : null;
    if (live) fs.writeFileSync(path.join(output, 'deployed-snapshot.json'), JSON.stringify(live) + '\n');
    Object.assign(report, auditBseRelease({ batches, recoveryRecords, published, deployed: live?.data }));
    report.deployed_observation = live ? { checked_at: live.checked_at, url: live.url, response_sha256: live.response_sha256, response_bytes: live.response_bytes } : null;
    const pins = fs.readdirSync(path.join(ROOT, 'data/discovery')).filter((f) => /^bse-listing-candidates-.*\.json$/.test(f)).map((f) => read(path.join(ROOT, 'data/discovery', f)));
    report.cursor = cursorSummary(read(path.join(ROOT, 'ops/bse-sme-addition-notices.json')), pins);
  } catch (error) { report.status = 'failed'; report.error = String(error.message || error); }
  fs.writeFileSync(path.join(output, 'release-audit.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ status: report.status, stats: report.stats, snapshots: report.snapshots, error: report.error }));
  if (report.status !== 'verified') process.exitCode = 1;
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) run().catch((e) => { console.error(e); process.exitCode = 1; });
