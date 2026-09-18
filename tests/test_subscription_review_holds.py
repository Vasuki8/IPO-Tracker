"""Market snapshot holds are independent of static PDF authority and never repairs."""
import copy
from datetime import date
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from source_review_holds import active_hold_reviews, display_holds, display_hold_matches, value_digest, _validate_hold
from public_quality import project_record
from build_company_pages import public_profile_record, public_summary_record
from validate_data import validate_record
from source_review_queue import review_task, compact_review_items, expand_review_items, review_gaps
from publication_mode import push_mode
from phase_status import status
import verify_review_release as release

TODAY = date(2026, 9, 18)
IDS = {'sona', 'ssretail', 'jsipl', 'heromotors', 'nse', 'kheriaauto', 'spectraa', 'axiomgas'}

class SubscriptionReviewHoldsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {r['id']: r for r in json.loads((ROOT/'tests/subscription_reviews_retained.json').read_text())['ipos']}
        cls.holds = {h['id']: h for h in display_holds() if h.get('scope') == 'subscription_snapshot'}

    def test_eight_real_retained_snapshots_are_withheld_across_public_projections(self):
        self.assertEqual(set(self.rows), IDS)
        self.assertEqual(set(self.holds), IDS)
        for key, row in self.rows.items():
            with self.subTest(id=key):
                before = copy.deepcopy(row)
                for projected in (project_record(row, today=TODAY), public_profile_record(row), public_summary_record(row)):
                    self.assertFalse(projected.get('subscription'))
                    self.assertFalse(projected.get('subscriptionHistory'))
                    self.assertEqual(projected['publicQuality']['fields']['subscription'],
                                     {'state':'under_review', 'reason':'subscription_snapshot_conflict'})
                    self.assertEqual(projected.get('subscriptionObservedAt'), row.get('subscriptionObservedAt'))
                    self.assertEqual(projected.get('subscriptionCollectedAt'), row.get('subscriptionCollectedAt'))
                self.assertEqual(row, before)

    def test_hold_values_and_provenance_match_independent_published_diagnostic(self):
        diagnostic = json.loads((ROOT/'docs/releases/2026-09-18-bse-source-authority.json').read_text())['nextRepairDiagnostic']
        for change in diagnostic['changes']:
            row = self.rows[change['id']]
            self.assertEqual(row['subscription']['total'], change['afterTotal'])
            self.assertNotEqual(row['subscription']['total'], change['beforeTotal'])
            for k,v in change['unchangedCategories'].items(): self.assertEqual(row['subscription'][k],v)
            for k,v in change['unchangedSnapshotMetadata'].items(): self.assertEqual(row.get(k),v)
            self.assertTrue(display_hold_matches(row,'subscription',self.holds[row['id']]))

    def test_every_identity_component_must_match_no_id_only_hold(self):
        for field in ('id','company','symbol','openDate','closeDate'):
            row = copy.deepcopy(self.rows['sona']); row[field] += '-different'
            self.assertFalse(display_hold_matches(row,'subscription',self.holds['sona']))

    def test_collection_clock_and_history_changes_cannot_release_mixed_facts(self):
        for key in IDS:
            row = copy.deepcopy(self.rows[key])
            row['subscriptionCollectedAt'] = row['subscriptionAsOf'] = '2026-09-19T01:00:00Z'
            row['subscriptionHistory'] = [{'total':999, 'capturedAt':'2026-09-19T01:00:00Z'}]
            projected = project_record(row, today=TODAY)
            self.assertIsNone(projected['subscription'])
            self.assertEqual(projected['subscriptionHistory'], [])

    def test_distinct_complete_snapshot_is_not_relabelled_as_same_review(self):
        for field, value in [('subscription',{'total':0}), ('subscriptionSource','Other (secondary)'),
                             ('subscriptionSourceUrl','https://www.bseindia.com/other'),
                             ('subscriptionObservedAt','2026-09-18T23:00:00+05:30'),
                             ('subscriptionTimeBasis','source-observation')]:
            row=copy.deepcopy(self.rows['sona']);row[field]=value
            self.assertFalse(display_hold_matches(row,'subscription',self.holds['sona']))
        # Matching a different record never confers Final Prospectus verification.
        self.assertNotEqual(project_record(row,today=TODAY)['publicQuality']['fields']['subscription']['state'],'final_verified')

    def test_missing_null_and_numeric_types_are_not_conflated(self):
        row=copy.deepcopy(self.rows['spectraa']); row['subscriptionSourceUrl']=None
        self.assertFalse(display_hold_matches(row,'subscription',self.holds['spectraa']))
        for value in (0, False, None):
            row=copy.deepcopy(self.rows['sona']);row['subscription']['total']=value
            self.assertFalse(display_hold_matches(row,'subscription',self.holds['sona']))
        self.assertNotEqual(value_digest(0),value_digest(False))
        self.assertNotEqual(value_digest({}),value_digest({'total':None}))

    def test_malformed_bindings_fail_closed_instead_of_disappearing(self):
        mutations = [lambda h:h['identity'].pop('closeDate'),
            lambda h:h['identity'].update(closeDate='2020-01-01'),
            lambda h:h.update(scope='all_subscriptions'),
            lambda h:h['fields'].update(lotSize=h['fields']['subscription']),
            lambda h:h['fields']['subscription'].update(sha256='a'*64),
            lambda h:h['fields']['subscription'].update(snapshotDigest='a'*64),
            lambda h:h['fields']['subscription']['snapshot']['subscription'].update(total=False),
            lambda h:h.update(reviewedAt='2026-09-18'),
            lambda h:h.update(reason='')]
        for mutate in mutations:
            h=copy.deepcopy(self.holds['sona']);mutate(h)
            with self.assertRaises(ValueError):_validate_hold(h)

    def test_unknown_source_stays_unknown_without_fabricated_pdf_binding(self):
        row=self.rows['spectraa']; public=project_record(row,today=TODAY)
        self.assertEqual(public['subscriptionAuthority'],'unknown')
        self.assertIsNone(public['subscriptionSourceUrl']);self.assertIsNone(public['subscriptionObservedAt'])
        issue=active_hold_reviews(row,[self.holds['spectraa']])[0]
        self.assertEqual(issue['displayHold']['source'],{})
        self.assertNotIn('sha256',issue['displayHold']['binding'])
        self.assertNotIn('documentType',issue['displayHold']['source'])

    def test_manual_review_survives_compaction_and_blocks_p4(self):
        issues=[];queued=[]
        for key,row in self.rows.items():
            relevant=[r for r in validate_record(row) if r.get('reviewType')=='subscription_snapshot_conflict']
            self.assertEqual(len(relevant),1);issues.extend(relevant)
            task=review_task(row,relevant[0]);self.assertEqual(task['route'],'manual-source-review')
            self.assertIsNone(task['repairGap']);self.assertIn('/subscription',task['evidencePaths'])
            defs=[];rich={'sourceReviewItems':[task]};compact={'sourceReviewItems':compact_review_items(rich,defs)}
            self.assertEqual(expand_review_items(compact,defs),[task]);self.assertFalse(review_gaps(rich))
            queued.append({'id':key,'priority':0})
        gate=status({'queue':queued},{'issues':issues,'reviewCount':8,'errorCount':0})
        self.assertEqual(gate['p4']['blockingSourceReviewItems'],8)
        self.assertEqual(gate['p4']['unmappedSourceReviewItems'],0)
        self.assertEqual(gate['p5']['status'],'waiting_for_p4')

    def test_all_canonical_and_proposal_bytes_remain_unchanged_by_projection(self):
        files=[ROOT/'data'/name for name in ('ipos.json','pending_updates.json','public_display_holds.json','phase_status.json')]
        before={p:p.read_bytes() for p in files}
        for row in json.loads(before[files[0]])['ipos']: project_record(row,today=TODAY)
        self.assertEqual(before,{p:p.read_bytes() for p in files})

    def test_milestone_uses_existing_review_publisher_not_source_collection(self):
        self.assertEqual(push_mode(['scripts/source_review_holds.py','scripts/source_review_queue.py',
            'scripts/public_quality.py','data/public_display_holds.json','public-quality.js','company.js',
            'tests/test_subscription_review_holds.py','tests/frontend_source_holds.cjs',
            'docs/PROJECT_STATUS.md']), 'review')

    def test_release_acceptance_checks_values_history_queue_and_live_sampling(self):
        row=copy.deepcopy(self.rows['sona']); hold=self.holds['sona']
        issue=active_hold_reviews(row,[hold])[0];task=review_task(row,issue)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'data').mkdir();(root/'ipo/sona').mkdir(parents=True)
            data={'public_display_holds.json':{'holds':[hold]},'ipos.json':{'ipos':[row]},
                'ipos-summary.json':{'ipos':[public_summary_record(row)]},
                'validation.json':{'issues':[issue]},'missing_queue.json':{'queue':[{'id':'sona','sourceReviewItems':[task]}]}}
            data['ipos-summary.json']['ipos'][0]['profilePath']='ipo/sona/'
            profile=public_profile_record(row)
            def save():
                for name, value in data.items():(root/'data'/name).write_text(json.dumps(value))
                (root/'ipo/sona/index.html').write_text('<script type="application/json" id="ipo-profile-data">'+json.dumps({'ipo':profile})+'</script>')
            save();receipt={'expectedSha256':{},'sampledProfiles':[]}
            self.assertTrue(release.verify_subscription_holds(root,receipt)[0]['active'])
            self.assertIn('ipo/sona/index.html',receipt['expectedSha256'])
            for field,value in [('subscription',{'total':123}),('subscriptionHistory',[{'total':123}])]:
                profile[field]=value;save()
                with self.assertRaisesRegex(ValueError,'leaked'):release.verify_subscription_holds(root,receipt)
                profile.pop(field);save()
            data['validation.json']['issues']=[];save()
            with self.assertRaisesRegex(ValueError,'validation'):release.verify_subscription_holds(root,receipt)
            data['validation.json']['issues']=[issue];data['missing_queue.json']['queue'][0]['sourceReviewItems']=[];save()
            with self.assertRaisesRegex(ValueError,'queue'):release.verify_subscription_holds(root,receipt)

if __name__ == '__main__': unittest.main()
