import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {checkRepository, DISPOSITION, validateDisposition} from './check-bse-2022-disposition.mjs';

const approvalPath = 'data/verified-bse-listings/2026-09-28-fixture.json';
const pub = 'published_reviewed_ipo', alias = 'existing_recovery_alias', wait = 'awaiting_issuer_specific_official_review';
function fixture() {
  const records = [
    {id: 'alpha', issuer_name: 'Alpha Limited', batch: {manifest: approvalPath}},
    {id: 'childrens', issuer_name: 'Childrens Limited'}
  ];
  return {
    disposition: {schema_version: '1.0.0', source_year: 2022, auto_import_allowed: false, complete_indian_ipo_universe: false,
      original_official_rows: 3, original_exact_matches: 0, original_unmatched: 3, reviewed_and_published: 1, reconciled_existing_aliases: 1, awaiting_review: 1, next_bounded_review_codes: ['543003'],
      rows: [
        {issuer_name: 'Alpha Limited', bse_scrip_code: '543001', source_year: 2022, source_row_index: 0, disposition: pub, stable_id: 'alpha', manifest: approvalPath, release_pr: 1},
        {issuer_name: "Children's Limited", bse_scrip_code: '543002', source_year: 2022, source_row_index: 1, disposition: alias, stable_id: 'childrens', manifest: null},
        {issuer_name: 'Pending Limited', bse_scrip_code: '543003', source_year: 2022, source_row_index: 2, disposition: wait, stable_id: null, manifest: null}
      ]},
    recoveryByYear: {'2022': {records}}, published: {schema_version: '1.2.0', records: structuredClone(records)},
    manifests: {[approvalPath]: {target_year: 2022, actions: [{stable_id: 'alpha'}]}},
    projectStatus: '## Exact next bounded task\nReview Pending Limited (543003).\n1 reviewed/published + 1 existing-recovery alias + 1 awaiting review\n\n## Previous release\nOld task (543001).',
    readme: '## Handoff for the next prompt\nReview (543003). 1 reviewed/published + 1 existing-recovery alias + 1 awaiting review\n\n### Exact next backend task\nReview Pending Limited (543003) from remaining **1**.\n\n### History\nOld (543002).'
  };
}
const base = fixture(), before = structuredClone(base);
assert.deepEqual(validateDisposition(base), {ok: true, source_year: 2022, original_unmatched: 3, published: 1, aliases: 1, awaiting: 1, next: ['543003'], warnings: []});
assert.deepEqual(base, before, 'validation must not mutate any input');
const rejected = [
  [x => { x.disposition.reviewed_and_published = 2; }, /disposition_count_mismatch/],
  [x => { x.disposition.reconciled_existing_aliases = 0; }, /disposition_count_mismatch/],
  [x => { x.disposition.awaiting_review = 0; }, /disposition_count_mismatch/],
  [x => { x.disposition.original_unmatched = 2; }, /source_count_mismatch/],
  [x => { x.disposition.original_official_rows = -1; }, /invalid_source_counts/],
  [x => { x.disposition.rows[2].bse_scrip_code = '543001'; }, /duplicate_discovery_code/],
  [x => { x.disposition.rows[2].source_row_index = 0; }, /duplicate_source_row/],
  [x => { x.disposition.rows[2].source_row_index = 3; }, /duplicate_source_row/],
  [x => { x.disposition.rows[2].disposition = 'guessed'; }, /unknown_disposition/],
  [x => { x.disposition.auto_import_allowed = true; }, /unsafe_scope_claim/],
  [x => { x.disposition.complete_indian_ipo_universe = true; }, /unsafe_scope_claim/],
  [x => { x.disposition.next_bounded_review_codes = ['543001']; }, /next_queue_not_awaiting/],
  [x => { x.disposition.next_bounded_review_codes = ['999999']; }, /next_queue_not_awaiting/],
  [x => { x.disposition.next_bounded_review_codes = ['543003', '543003']; }, /invalid_next_queue/],
  [x => { x.disposition.next_bounded_review_codes = []; }, /invalid_next_queue/],
  [x => { x.disposition.rows[2].stable_id = 'pending'; }, /awaiting_row_has_release_identity/],
  [x => { x.recoveryByYear['2023'] = x.recoveryByYear['2022']; delete x.recoveryByYear['2022']; }, /closed_row_missing_2022_recovery/],
  [x => { x.recoveryByYear['2023'] = {records: [x.recoveryByYear['2022'].records[0]]}; }, /duplicate_recovery_id/],
  [x => { x.published.records.pop(); }, /missing_or_mismatched_public_record/],
  [x => { x.published.records.push(x.published.records[0]); }, /duplicate_public_id/],
  [x => { x.published.records[0].issuer_name = 'Wrong'; }, /mismatched_public_record/],
  [x => { x.disposition.rows[0].issuer_name = 'Wrong'; }, /closed_row_issuer_mismatch/],
  [x => { x.disposition.rows[0].manifest = '../secrets.json'; }, /invalid_release_reference/],
  [x => { x.disposition.rows[0].release_pr = null; }, /invalid_release_reference/],
  [x => { x.manifests[approvalPath].actions = []; }, /missing_manifest_approval/],
  [x => { x.recoveryByYear['2022'].records[0].batch.manifest = 'wrong'; }, /recovery_manifest_binding_missing/],
  [x => { x.disposition.rows[1].manifest = approvalPath; }, /alias_must_not_claim_import/],
  [x => { x.projectStatus = x.projectStatus.replace('(543003)', '(543001)'); }, /status_next_queue_mismatch/],
  [x => { x.readme = x.readme.replace('Pending Limited (543003)', 'Pending Limited (543001)'); }, /readme_next_queue_mismatch/],
  [x => { x.projectStatus = x.projectStatus.replace('1 reviewed/published', '2 reviewed/published'); }, /status_count_mismatch/],
  [x => { x.readme = x.readme.replace('remaining **1**', 'remaining **2**'); }, /readme_count_mismatch/],
  [x => { x.projectStatus = ''; }, /missing_handoff_section/],
  [x => { x.readme = x.readme.replace('Review (543003)', 'Review (543001)'); }, /readme_overview_next_queue_mismatch/],
  [x => { x.readme = x.readme.replace('1 reviewed/published', '2 reviewed/published'); }, /readme_overview_count_mismatch/]
];
for (const [mutate, reason] of rejected) { const x = fixture(); mutate(x); assert.throws(() => validateDisposition(x), reason); }
const legacy = fixture(); legacy.manifests[approvalPath] = {target_year: 2022, import_ids: ['alpha']};
assert.equal(validateDisposition(legacy).ok, true, 'legacy reviewed manifest must remain supported');
const pending = fixture(); pending.recoveryByYear['2022'].records.push({id: 'pending', issuer_name: 'Pending Limited'});
assert.equal(validateDisposition(pending).warnings[0].reason, 'reconcile_existing_identity_before_import');
assert.equal(pending.disposition.rows[2].disposition, wait, 'possible matches are not auto-closed');
// A discovery disagreement must not overwrite (or reject) retained IPO facts.
const conflict = fixture(); conflict.disposition.rows[0].issue_price = 999; conflict.published.records[0].issue_price = {value: 100, status: 'conflict'};
assert.equal(validateDisposition(conflict).ok, true);
const finished = fixture(); finished.disposition.rows.pop(); finished.disposition.original_unmatched = 2; finished.disposition.original_official_rows = 2;
finished.disposition.awaiting_review = 0; finished.disposition.next_bounded_review_codes = [];
finished.projectStatus = '## Exact next bounded task\n1 reviewed/published + 1 existing-recovery alias + 0 awaiting review';
finished.readme = '## Handoff for the next prompt\n1 reviewed/published + 1 existing-recovery alias + 0 awaiting review\n\n### Exact next backend task\nNo rows remain; remaining **0**.';
assert.equal(validateDisposition(finished).awaiting, 0);
// Once this queue is complete, later-year task codes belong to that year's checker.
const nextYear = structuredClone(finished);
nextYear.projectStatus += '\nNext 2023 candidate (543998).';
nextYear.readme = nextYear.readme.replace('existing-recovery alias + 0 awaiting review', 'existing-recovery alias + 0 awaiting review\nNext 2023 candidate (543998).') + '\nNext 2023 candidate (543998).';
assert.equal(validateDisposition(nextYear).ok, true, 'completed 2022 queue must allow a 2023 handoff');
for (const sectionName of ['status', 'overview', 'footer']) {
  const bad = structuredClone(nextYear);
  if (sectionName === 'status') bad.projectStatus = bad.projectStatus.replace('543998', '543001');
  else if (sectionName === 'overview') bad.readme = bad.readme.replace('543998', '543001');
  else bad.readme = bad.readme.slice(0, bad.readme.lastIndexOf('543998')) + bad.readme.slice(bad.readme.lastIndexOf('543998')).replace('543998', '543001');
  assert.throws(() => validateDisposition(bad), /next_queue_mismatch/, 'closed 2022 code must not become the next task again');
}
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ipo-disposition-'));
try {
  const x = fixture();
  const files = {[DISPOSITION]: JSON.stringify(x.disposition), 'data/ipos.json': JSON.stringify(x.published), 'data/recovery/2022/nse-issue-information.json': JSON.stringify(x.recoveryByYear['2022']), [approvalPath]: JSON.stringify(x.manifests[approvalPath]), 'docs/PROJECT_STATUS.md': x.projectStatus, 'README.md': x.readme};
  for (const [p, text] of Object.entries(files)) { fs.mkdirSync(path.dirname(path.join(temp, p)), {recursive: true}); fs.writeFileSync(path.join(temp, p), text); }
  assert.equal(checkRepository(temp).ok, true);
  for (const [p, text] of Object.entries(files)) assert.equal(fs.readFileSync(path.join(temp, p), 'utf8'), text, 'repository check is read-only');
} finally { fs.rmSync(temp, {recursive: true, force: true}); }
console.log(JSON.stringify({bse_2022_disposition_tests: {rejected_mutations: rejected.length + 3, next_year_handoff: true, legacy_manifest: true, alias_preserved: true, pending_closeout_warning: true, no_fact_inference: true, empty_queue: true, read_only: true}}));
