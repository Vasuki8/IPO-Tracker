"""Real accepted BSE receipts through cleanup, update and publication boundaries."""
import copy
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from bse_active_offer_helpers import cohort, EXPECTED
from reviewed_corrections import prepare
from accepted_data_guard import assert_preserved, retain_provenance_changes
from public_quality import project_record
from publish_transaction import merge_payload
import run_pipeline

ROOT = Path(__file__).resolve().parents[1]


def accepted():
    payload, registry, groups = cohort()
    candidate = prepare(payload, registry, groups, list(EXPECTED))
    candidate['ipos'] = [r for r in candidate['ipos'] if r['id'] in EXPECTED]
    return candidate


class AcceptedDataPreservationTests(unittest.TestCase):
    def test_real_success_partial_empty_and_failed_core_refreshes_twice(self):
        # Separate interpreter exercises the real wrapper stack without leaking
        # its module monkeypatches into the rest of the suite. Only HTTP is fake.
        original = accepted()
        controls = json.loads((ROOT / 'data/ipos.json').read_text())['ipos']
        original['ipos'].extend(copy.deepcopy(r) for r in controls if r['id'] in {'axiomgas', 'varmora'})
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'ipos.json'
            driver = r'''
import copy,json,sys
from unittest.mock import patch
sys.path.insert(0, 'scripts')
import run_update_final_policy as update
from accepted_data_guard import assert_preserved
core=update.core
from pathlib import Path
core.DATA_FILE=Path(sys.argv[1]); mode=sys.argv[2]
before=json.loads(core.DATA_FILE.read_text())
class NSE:
 def current(self):
  if mode=='all_failed': raise TimeoutError('NSE transport failed')
  return [{'companyName':'Independent NSE Limited','symbol':'INDEP','issueStartDate':'2026-09-21','issueEndDate':'2026-09-23'}]
 def upcoming(self): return []
 def past(self,*args): return []
class BSE:
 def current_issues(self):
  if mode in ('failed','all_failed'): raise TimeoutError('BSE transport failed')
  rows=[]
  selected=before['ipos'] if mode in ('complete', 'incomplete') else before['ipos'][:1] if mode=='partial' else []
  for old in selected:
   row={k:copy.deepcopy(old[k]) for k in ('id','company','board','openDate','closeDate','exchange') if k in old}
   row['sources']=[{'name':'BSE public issue','url':'https://beta.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p','asOf':'2026-09-19T19:00:00+05:30'}]
   row['observations']=copy.deepcopy(old.get('observations',{}))
   if mode=='incomplete':
    row['observations'].get('BSE',{}).pop('priceBand',None)
    row['observations'].get('BSE',{}).pop('staticOfferTerms',None)
   rows.append(row)
  return rows
with patch.object(core,'NSEClient',NSE),patch.object(core,'BSEClient',BSE),patch.object(core.time,'sleep'),patch.object(sys,'argv',['run_update_final_policy.py','--history-days','1','--skip-sebi']):
 for repeat in range(2):
  update.main()
  after=json.loads(core.DATA_FILE.read_text());assert_preserved(before,after)
  by_id={r['id']:r for r in after['ipos']}
  for old in before['ipos']:
   new=by_id[old['id']]
   for field in ('activeOfferTerms','dataCorrections'):
    assert old[field]==new[field], (mode,repeat,old['id'],field)
   if mode=='incomplete' and 'BSE' in old.get('observations',{}):
    assert new['observations']['BSE']==old['observations']['BSE']
   for source in old['sources']:
    assert source in new['sources']
'''
            for mode in ('complete', 'partial', 'empty', 'failed', 'all_failed', 'incomplete'):
                with self.subTest(mode=mode):
                    test_input = copy.deepcopy(original)
                    if mode == 'incomplete':
                        for row in test_input['ipos']:
                            if row['id'] in EXPECTED:
                                row['observations']['BSE']['priceBand'] = {'min': 1, 'max': 2}
                    data.write_text(json.dumps(test_input))
                    result = subprocess.run([sys.executable, '-c', driver, str(data), mode], cwd=ROOT,
                                            text=True, capture_output=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_guard_rejects_receipt_proof_history_and_whole_row_loss(self):
        before = accepted()
        mutations = [lambda p: p['ipos'].pop(),
                     lambda p: p['ipos'][0].pop('activeOfferTerms'),
                     lambda p: p['ipos'][0].update(dataCorrections=[]),
                     lambda p: p['ipos'][0]['activeOfferTerms']['source'].update(collectedAt='2099-01-01'),
                     lambda p: p['ipos'][0]['sources'].pop()]
        for mutate in mutations:
            after = copy.deepcopy(before); mutate(after)
            with self.subTest(mutate=mutate), self.assertRaisesRegex(ValueError, 'preservation failed'):
                assert_preserved(before, after)

    def test_ordinary_three_way_merge_cannot_justify_receipt_loss(self):
        before = accepted(); proposed = copy.deepcopy(before)
        proposed['ipos'][0].pop('activeOfferTerms'); proposed['ipos'][0]['dataCorrections'] = []
        candidate, _ = merge_payload(before, proposed, before)
        with self.assertRaises(ValueError): assert_preserved(before, candidate)

    def test_invalid_and_expired_receipts_remain_stored_and_conflicts_survive_cleanup(self):
        from run_update import clean_existing_record
        before = accepted()
        for row in before['ipos']:
            row['observations']['BSE']['priceBand'] = {'min': 1, 'max': 2}
            cleaned = clean_existing_record(row)
            self.assertEqual(cleaned, row)
            self.assertIsNone(project_record(cleaned, today=date(2026, 9, 19)).get('priceBand'))
            self.assertIsNone(project_record(cleaned, today=date(2026, 9, 26)).get('priceBand'))
            self.assertIn('activeOfferTerms', cleaned)
        assert_preserved(before, copy.deepcopy(before))

    def test_valid_but_truncated_stage_output_rolls_back_each_affected_path(self):
        before = accepted()
        for script in ('run_update_final_policy.py', 'run_offer_documents.py', 'run_issuer_offer_docs.py', 'enforce_final_prospectus_policy.py'):
            with self.subTest(script=script), tempfile.TemporaryDirectory() as directory:
                data = Path(directory) / 'ipos.json'; data.write_text(json.dumps(before))
                original = data.read_bytes()
                def broken(*args, **kwargs):
                    data.write_text(json.dumps({'ipos': []}))
                    return SimpleNamespace(returncode=2, stdout='partial collection')
                with patch.object(run_pipeline, 'DATA', data), patch.object(run_pipeline.subprocess, 'run', side_effect=broken):
                    result = run_pipeline.step(script)
                self.assertEqual(result['status'], 'failed')
                self.assertEqual(data.read_bytes(), original)
                self.assertIn('accepted issuer removed', result['diagnostics'])

    def test_exact_policy_proof_history_allows_withdrawal_but_generic_reason_does_not(self):
        proof = {'value': 10, 'sha256': 'a' * 64, 'sourceUrl': 'https://example.test/final.pdf'}
        old = {'id': 'one', 'issueSizeCr': 10, 'staticFieldProvenance': {'issueSizeCr': proof}}
        new = copy.deepcopy(old); new['staticFieldProvenance'] = {}
        new['dataCorrections'] = [{'field': 'unrelated', 'reason': 'policy correction'}]
        with self.assertRaises(ValueError): assert_preserved({'ipos':[old]}, {'ipos':[new]})
        retain_provenance_changes(old, new, reason='Existing policy withdrew unsupported evidence', checked_at='2026-09-19')
        assert_preserved({'ipos':[old]}, {'ipos':[new]})
        previous = copy.deepcopy(new)
        retain_provenance_changes(previous, new, reason='Same policy repeated', checked_at='2026-09-20')
        self.assertEqual(new, previous)

    def test_ordinary_publication_detects_matching_blanks_and_preserves_real_serialization(self):
        from build_company_pages import public_profile_record, public_summary_record
        import verify_public_release as verifier
        before = accepted()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'data').mkdir()
            baseline = root / 'baseline.json'; baseline.write_text(json.dumps(before))
            (root / 'data/public_display_holds.json').write_bytes((ROOT / 'data/public_display_holds.json').read_bytes())
            def build(payload):
                payload.setdefault('meta', {})['publication'] = {'status': 'published'}
                (root / 'data/ipos.json').write_text(json.dumps(payload))
                summaries = [public_summary_record(r) for r in payload['ipos']]
                (root / 'data/ipos-summary.json').write_text(json.dumps({'ipos': summaries}))
                for row in payload['ipos']:
                    profile = public_profile_record(row); path = root / row['profilePath'] / 'index.html'
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text('<script type="application/json" id="ipo-profile-data">' + json.dumps({'ipo': profile}) + '</script>')
            build(copy.deepcopy(before))
            receipt = {'expectedSha256': {}, 'sampledProfiles': []}
            self.assertEqual(verifier.verify_accepted_preservation(root, receipt, baseline)['status'], 'passed')
            broken = copy.deepcopy(before)
            broken['ipos'][0].pop('activeOfferTerms'); broken['ipos'][0]['dataCorrections'] = []
            build(broken)
            with self.assertRaisesRegex(ValueError, 'preservation failed'):
                verifier.verify_accepted_preservation(root, receipt, baseline)

    def test_no_accepted_extraction_preserves_raw_document_proof(self):
        from final_prospectus_policy import apply_final_prospectus_static_fields
        row = {'id':'one','documentFieldProvenance':{'sha256':'a'*64,'evidence':{'registrar':{'page':2}}}}
        before = copy.deepcopy(row)
        self.assertEqual(apply_final_prospectus_static_fields(row, {}, {'type':'PROSPECTUS','url':'https://example.test/final.pdf'}), [])
        self.assertEqual(row['documentFieldProvenance'], before['documentFieldProvenance'])


if __name__ == '__main__': unittest.main()
