import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

export const DISPOSITION = 'data/discovery/bse-2022-unmatched-disposition-2026-09-27.json';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PUBLISHED = 'published_reviewed_ipo';
const ALIAS = 'existing_recovery_alias';
const AWAITING = 'awaiting_issuer_specific_official_review';
const manifestPath = p => typeof p === 'string' && /^data\/verified-bse-listings\/[a-z0-9-]+\.json$/.test(p);
const nameKey = value => String(value ?? '').toLowerCase().replace(/['’]/g, '').replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim();
const requireThat = (condition, reason) => { if (!condition) throw new Error(reason); };

function uniqueIndex(records, label) {
  requireThat(Array.isArray(records), `invalid_${label}_records`);
  const result = new Map();
  for (const record of records) {
    requireThat(typeof record?.id === 'string' && record.id.length > 0, `invalid_${label}_id`);
    requireThat(!result.has(record.id), `duplicate_${label}_id:${record.id}`);
    result.set(record.id, record);
  }
  return result;
}
function section(text, heading) {
  requireThat(typeof text === 'string' && text.includes(heading), `missing_handoff_section:${heading}`);
  return text.split(heading)[1].split(/\n#{1,6} /)[0];
}

// Checks bookkeeping against committed evidence. Discovery prices/dates are
// deliberately NOT treated as authority for correcting published IPO facts.
export function validateDisposition({disposition: d, recoveryByYear, published, manifests, projectStatus, readme}) {
  requireThat(d?.schema_version === '1.0.0' && d.source_year === 2022 && Array.isArray(d.rows), 'invalid_disposition');
  requireThat(d.auto_import_allowed === false && d.complete_indian_ipo_universe === false, 'unsafe_scope_claim');
  requireThat([d.original_official_rows, d.original_exact_matches, d.original_unmatched].every(n => Number.isSafeInteger(n) && n >= 0), 'invalid_source_counts');
  requireThat(d.original_exact_matches + d.original_unmatched === d.original_official_rows && d.rows.length === d.original_unmatched, 'source_count_mismatch');
  requireThat(recoveryByYear && typeof recoveryByYear === 'object', 'invalid_recovery');
  const recoveryRows = Object.entries(recoveryByYear).flatMap(([year, m]) => {
    requireThat(/^20\d{2}$/.test(year) && Array.isArray(m?.records), 'invalid_recovery_manifest');
    return m.records.map(record => ({...record, recovery_year: Number(year)}));
  });
  const recovery = uniqueIndex(recoveryRows, 'recovery');
  requireThat(published?.schema_version === '1.2.0', 'invalid_public_schema');
  const publicRows = uniqueIndex(published.records, 'public');
  const codes = new Map(), indices = new Set(), counts = {[PUBLISHED]: 0, [ALIAS]: 0, [AWAITING]: 0};
  const warnings = [];
  for (const row of d.rows) {
    requireThat(/^\d{6}$/.test(row.bse_scrip_code) && !codes.has(row.bse_scrip_code), 'invalid_or_duplicate_discovery_code');
    requireThat(row.source_year === 2022 && Number.isSafeInteger(row.source_row_index) && row.source_row_index >= 0 && row.source_row_index < d.original_official_rows && !indices.has(row.source_row_index), 'invalid_or_duplicate_source_row');
    requireThat(Object.hasOwn(counts, row.disposition), 'unknown_disposition');
    codes.set(row.bse_scrip_code, row); indices.add(row.source_row_index); counts[row.disposition]++;
    if (row.disposition === AWAITING) {
      requireThat(row.stable_id == null && row.manifest == null, 'awaiting_row_has_release_identity');
      const hits = recoveryRows.filter(r => nameKey(r.issuer_name) === nameKey(row.issuer_name) || String(r.bse_scrip_code ?? '') === row.bse_scrip_code);
      // Separate publication and closeout commits are intentional. Surface a
      // possible pending closeout, but never auto-import or auto-close a row.
      if (hits.length) warnings.push({code: row.bse_scrip_code, reason: 'reconcile_existing_identity_before_import', ids: hits.map(r => r.id)});
      continue;
    }
    const retained = recovery.get(row.stable_id), served = publicRows.get(row.stable_id);
    requireThat(retained && retained.recovery_year === 2022, `closed_row_missing_2022_recovery:${row.stable_id}`);
    requireThat(served && served.issuer_name === retained.issuer_name, `closed_row_missing_or_mismatched_public_record:${row.stable_id}`);
    requireThat(nameKey(retained.issuer_name) === nameKey(row.reviewed_issuer_name ?? row.issuer_name), `closed_row_issuer_mismatch:${row.stable_id}`);
    if (row.disposition === ALIAS) {
      requireThat(row.manifest == null, 'alias_must_not_claim_import');
      continue;
    }
    requireThat(Number.isSafeInteger(row.release_pr) && row.release_pr > 0 && manifestPath(row.manifest), 'invalid_release_reference');
    const approval = manifests[row.manifest];
    const approvedIds = [...(approval?.actions ?? []).map(a => a.stable_id), ...(approval?.import_ids ?? [])];
    requireThat(approval?.target_year === 2022 && approvedIds.includes(row.stable_id), `missing_manifest_approval:${row.stable_id}`);
    requireThat(Object.values(retained).some(v => v && typeof v === 'object' && v.manifest === row.manifest), `recovery_manifest_binding_missing:${row.stable_id}`);
  }
  requireThat(d.reviewed_and_published === counts[PUBLISHED] && d.reconciled_existing_aliases === counts[ALIAS] && d.awaiting_review === counts[AWAITING], 'disposition_count_mismatch');
  const next = d.next_bounded_review_codes;
  requireThat(Array.isArray(next) && new Set(next).size === next.length && next.length <= 2 && (counts[AWAITING] === 0 ? next.length === 0 : next.length > 0), 'invalid_next_queue');
  for (const code of next) requireThat(codes.get(code)?.disposition === AWAITING, `next_queue_not_awaiting:${code}`);
  const statusSection = section(projectStatus, '## Exact next bounded task');
  const readmeSection = section(readme, '### Exact next backend task');
  const overview = section(readme, '## Handoff for the next prompt');
  for (const [label, text] of [['status', statusSection], ['readme', readmeSection], ['readme_overview', overview]]) {
    const mentionedCodes = [...text.matchAll(/\((\d{6})\)/g)].map(m => m[1]);
    requireThat(JSON.stringify(mentionedCodes) === JSON.stringify(next), `${label}_next_queue_mismatch`);
  }
  requireThat(statusSection.includes(`${counts[PUBLISHED]} reviewed/published + ${counts[ALIAS]} existing-recovery alias + ${counts[AWAITING]} awaiting review`), 'status_count_mismatch');
  requireThat(readmeSection.includes(`remaining **${counts[AWAITING]}**`), 'readme_count_mismatch');
  requireThat(overview.includes(`${counts[PUBLISHED]} reviewed/published + ${counts[ALIAS]} existing-recovery alias + ${counts[AWAITING]} awaiting review`), 'readme_overview_count_mismatch');
  return {ok: true, source_year: 2022, original_unmatched: d.original_unmatched, published: counts[PUBLISHED], aliases: counts[ALIAS], awaiting: counts[AWAITING], next, warnings};
}

export function checkRepository(root = ROOT) {
  const read = relative => JSON.parse(fs.readFileSync(path.join(root, relative), 'utf8'));
  const d = read(DISPOSITION), recoveryByYear = {}, manifests = {};
  for (const entry of fs.readdirSync(path.join(root, 'data/recovery'), {withFileTypes: true})) {
    if (!entry.isDirectory() || !/^20\d{2}$/.test(entry.name)) continue;
    const p = `data/recovery/${entry.name}/nse-issue-information.json`;
    if (fs.existsSync(path.join(root, p))) recoveryByYear[entry.name] = read(p);
  }
  for (const row of d.rows ?? []) if (row.disposition === PUBLISHED) {
    requireThat(manifestPath(row.manifest), 'invalid_release_reference');
    manifests[row.manifest] = read(row.manifest);
  }
  return validateDisposition({disposition: d, recoveryByYear, manifests, published: read('data/ipos.json'), projectStatus: fs.readFileSync(path.join(root, 'docs/PROJECT_STATUS.md'), 'utf8'), readme: fs.readFileSync(path.join(root, 'README.md'), 'utf8')});
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try { console.log(JSON.stringify({bse_2022_disposition: checkRepository()}, null, 2)); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
