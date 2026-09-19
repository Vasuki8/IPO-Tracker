"""Operational recency never establishes source accuracy or resolves pending work."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('health_report', ROOT / 'tools/report_update_health.py')
health = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(health)
AT = '2026-09-18T08:00:00Z'
OLD = '2026-09-18T04:00:00Z'
RECENT = '2026-09-18T07:50:00Z'


class UpdateHealthTests(unittest.TestCase):
    def setUp(self):
        self.row = {'id': 'example', 'company': 'Example Limited', 'symbol': 'EXAMPLE',
                    'openDate': '2026-09-17', 'closeDate': '2026-09-18', 'status': 'open',
                    'subscription': {'total': 0, 'qib': 0, 'retail': 0, 'nii': 0},
                    'subscriptionSource': 'BSE cumulative demand',
                    'subscriptionSourceUrl': 'https://www.bseindia.com/demand?issue=example',
                    'subscriptionObservedAt': OLD, 'subscriptionCollectedAt': RECENT,
                    'subscriptionTimeBasis': 'source-observation'}
        self.payload = {'meta': {'recordCount': 1, 'generatedAt': RECENT,
            'publication': {'runId': '10', 'collectorCommit': 'a' * 40, 'status': 'published', 'pendingConflictCount': 2},
            'pipelineStages': {'run_update_final_policy.py': {'status': 'no_change', 'checkedAt': RECENT, 'exitCode': 0}},
            'sourceHealth': {'NSE-live': {'ok': True, 'records': 0}}}, 'ipos': [self.row]}
        self.phase = {'p4': {'status': 'incomplete', 'higherPriorityRecords': 2, 'blockingSourceReviewItems': 9},
                      'p5': {'status': 'waiting_for_p4'}}
        self.run = {'id': 11, 'run_attempt': 1, 'repository': {'full_name': health.REPOSITORY},
                    'head_repository': {'full_name': health.REPOSITORY}, 'event': 'schedule',
                    'head_branch': 'main', 'path': '.github/workflows/refresh.yml', 'head_sha': 'b' * 40,
                    'status': 'in_progress', 'conclusion': None, 'updated_at': RECENT}
        self.jobs = {'total_count': 2, 'jobs': [
            {'name': 'collect', 'run_id': 11, 'run_attempt': 1, 'status': 'completed', 'conclusion': 'success',
             'started_at': OLD, 'completed_at': '2026-09-18T07:00:00Z'},
            {'name': 'publish', 'run_id': 11, 'run_attempt': 1, 'status': 'queued', 'conclusion': None,
             'started_at': None, 'completed_at': None}]}

    def build(self, *, at=AT, workflow=False):
        before = copy.deepcopy((self.payload, self.phase, self.run, self.jobs))
        result = health.build_report(self.payload, self.phase, [], as_of=at,
                                    run=self.run if workflow else None, jobs=self.jobs if workflow else None)
        self.assertEqual(before, (self.payload, self.phase, self.run, self.jobs))
        self.assertEqual(result['mutationsApplied'], 0)
        self.assertEqual(result['phaseGateEvidence'], self.phase)
        return result

    def test_new_publication_and_collection_do_not_refresh_an_old_observation(self):
        r = self.build()
        self.assertEqual(r['acceptedPublication']['snapshotAge']['state'], 'within_tolerance')
        self.assertEqual(r['subscriptions'][0]['collectionFreshness']['state'], 'within_tolerance')
        self.assertEqual(r['subscriptions'][0]['observationFreshness']['state'], 'overdue')
        self.assertEqual(r['subscriptions'][0]['publicState'], 'reported')
        self.assertEqual(r['subscriptions'][0]['finality'], 'not_established_by_snapshot')

    def test_unknown_source_time_is_not_collection_or_legacy_asof(self):
        for basis in ('collection-only', None):
            with self.subTest(basis=basis):
                self.row['subscriptionObservedAt'] = None
                self.row['subscriptionTimeBasis'] = basis
                self.row['subscriptionAsOf'] = RECENT
                self.assertEqual(self.build()['subscriptions'][0]['observationFreshness']['state'], 'source_time_unknown')

    def test_source_checks_without_their_own_time_remain_unknown(self):
        row = next(r for r in self.build()['sources'] if r['name'] == 'NSE-live')
        self.assertEqual(row['attemptFreshness']['state'], 'missing')
        self.assertTrue(row['requiresInvestigation'])
        # 0 new rows is not a failure, just an undated check.
        self.assertFalse(row['failureEvidence'])

    def test_failed_deferred_and_partial_outcomes_survive_recent_timestamps(self):
        for status in ('source_blocked', 'failed', 'deferred'):
            self.payload['meta']['pipelineStages']['run_offer_documents.py'] = {'status': status, 'checkedAt': RECENT}
            row = next(r for r in self.build()['stages'] if r['name'] == 'run_offer_documents.py')
            self.assertEqual(row['reportedOutcome'], status)
            self.assertEqual(row['attemptFreshness']['state'], 'within_tolerance')
            self.assertTrue(row['requiresInvestigation'])
        self.payload['meta']['sourceHealth']['IPO-subscription'] = {'ok': True, 'failed': 2, 'attempted': 5, 'asOf': RECENT}
        row = next(r for r in self.build()['sources'] if r['name'] == 'IPO-subscription')
        self.assertTrue(row['failureEvidence'])

    def test_invalid_health_metadata_or_nonzero_exit_is_not_success(self):
        original = copy.deepcopy(self.payload['meta']['pipelineStages']['run_update_final_policy.py'])
        for extra in ({'ok': 'true'}, {'failed': False}, {'degraded': 'false'}, {'exitCode': 1}):
            self.payload['meta']['pipelineStages']['run_update_final_policy.py'] = copy.deepcopy(original)
            self.payload['meta']['pipelineStages']['run_update_final_policy.py'].update(extra)
            row = next(r for r in self.build()['stages'] if r['name'] == 'run_update_final_policy.py')
            self.assertTrue(row['requiresInvestigation'])

    def test_retired_stage_is_recorded_not_scheduled_as_live_work(self):
        self.payload['meta']['pipelineStages']['legacy.py'] = {'status': 'no_change', 'checkedAt': '2020-01-01T00:00:00Z'}
        row = next(r for r in self.build()['stages'] if r['name'] == 'legacy.py')
        self.assertEqual(row['attemptFreshness']['state'], 'recorded_only')
        self.assertFalse(row['requiresInvestigation'])

    def test_timezone_offsets_boundaries_and_future_times(self):
        now = health.instant(AT)
        self.assertEqual(health.age('2026-09-18T11:30:00+05:30', now, 120)['state'], 'within_tolerance')
        self.assertEqual(health.age('2026-09-18T05:59:59Z', now, 120)['state'], 'overdue')
        self.assertEqual(health.age('2026-09-18T08:00:01Z', now, 120)['state'], 'future_timestamp')
        for stamp in (False, '', '2026-09-18', '2026-09-18T08:00:00'):
            self.assertEqual(health.age(stamp, now, 120)['state'], 'invalid')

    def test_schedule_window_is_not_an_assumed_exchange_calendar(self):
        for stamp in ('2026-09-18T04:30:00Z', '2026-09-18T15:00:00Z', '2026-09-19T08:00:00Z'):
            self.assertFalse(health.subscription_deadline(health.instant(stamp)))
        self.assertTrue(health.subscription_deadline(health.instant('2026-09-18T05:30:00Z')))
        self.assertEqual(self.build(at='2026-09-18T04:30:00Z')['subscriptions'][0]['observationFreshness']['state'], 'outside_monitoring_deadline')

    def test_closed_withdrawn_and_unknown_lifecycle_are_not_live_final_subscriptions(self):
        self.assertEqual(self.build(at='2026-09-19T08:00:00Z')['subscriptions'], [])
        self.row['status'] = 'withdrawn'
        self.assertEqual(self.build()['summary']['lifecycleScopes'], {'not_live_status': 1})
        self.row['status'] = 'open'
        self.row['closeDate'] = None
        self.assertEqual(self.build()['summary']['lifecycleScopes'], {'unknown_dates': 1})
        self.row['closeDate'] = '2026-09-16'
        self.assertEqual(self.build()['summary']['lifecycleScopes'], {'invalid_dates': 1})

    def test_conflicting_clocks_and_missing_source_binding_remain_visible(self):
        self.row['subscriptionAsOf'] = OLD
        self.row.pop('subscriptionSourceUrl')
        self.row['sources'] = [{'name': 'BSE', 'url': 'https://www.bseindia.com/'}]
        row = self.build()['subscriptions'][0]
        self.assertIsNone(row['source']['url'])
        self.assertEqual(row['collectionFreshness']['state'], 'conflicting_collection_clocks')
        self.row['subscriptionObservedAt'] = '2026-09-18T07:59:00Z'
        self.assertEqual(self.build()['subscriptions'][0]['observationFreshness']['state'], 'inconsistent_source_clock')

    def test_old_snapshot_without_workflow_evidence_is_not_proven_publication_delay(self):
        self.payload['meta']['generatedAt'] = OLD
        r = self.build()['acceptedPublication']
        self.assertEqual(r['snapshotAge']['state'], 'overdue')
        self.assertEqual(r['delivery']['state'], 'not_assessed')
        self.assertEqual(r['liveDeployment'], 'not_assessed_by_this_offline_report')

    def test_collected_unpublished_work_can_be_overdue_or_within_grace(self):
        r = self.build(workflow=True)['acceptedPublication']['delivery']
        self.assertEqual(r['state'], 'recorded_publication_overdue')
        self.jobs['jobs'][0]['completed_at'] = RECENT
        self.assertEqual(self.build(workflow=True)['acceptedPublication']['delivery']['state'], 'recorded_publication_waiting')

    def test_collection_failures_and_publication_failures_are_distinct(self):
        for conclusion in ('failure', 'timed_out', 'cancelled'):
            self.jobs['jobs'][0]['conclusion'] = conclusion
            self.assertEqual(self.build(workflow=True)['acceptedPublication']['delivery']['state'], 'collection_' + conclusion)
        self.jobs['jobs'][0]['conclusion'] = 'success'
        self.jobs['jobs'][1].update(status='completed', conclusion='failure')
        self.assertEqual(self.build(workflow=True)['acceptedPublication']['delivery']['state'], 'publication_failure')

    def test_successful_no_change_run_is_not_a_failed_publication(self):
        self.jobs['jobs'][1].update(status='completed', conclusion='success')
        self.run.update(status='completed', conclusion='success')
        self.assertEqual(self.build(workflow=True)['acceptedPublication']['delivery']['state'], 'completed_without_matching_acceptance')
        self.payload['meta']['publication'].update(runId='11', collectorCommit='b' * 40)
        self.assertEqual(self.build(workflow=True)['acceptedPublication']['delivery']['state'], 'accepted_run_matches')
        self.payload['meta']['publication']['collectorCommit'] = 'c' * 40
        self.assertEqual(self.build(workflow=True)['acceptedPublication']['delivery']['state'], 'acceptance_binding_conflict')

    def test_missing_future_or_inverted_completion_time_cannot_prove_delay(self):
        for stamp in (None, '2026-09-18T09:00:00Z', '2026-09-18T03:00:00Z'):
            self.jobs['jobs'][0]['completed_at'] = stamp
            self.assertEqual(self.build(workflow=True)['acceptedPublication']['delivery']['state'], 'collection_completion_time_unknown')

    def test_foreign_partial_or_wrong_attempt_evidence_fails_closed(self):
        original = copy.deepcopy((self.run, self.jobs))
        for defect in ('repo', 'fork', 'workflow', 'branch', 'event', 'run', 'attempt', 'partial', 'duplicate'):
            self.run, self.jobs = copy.deepcopy(original)
            with self.subTest(defect=defect):
                if defect == 'repo': self.run['repository']['full_name'] = 'other/repo'
                elif defect == 'fork': self.run['head_repository']['full_name'] = 'other/repo'
                elif defect == 'workflow': self.run['path'] = '.github/workflows/validate.yml'
                elif defect == 'branch': self.run['head_branch'] = 'feature'
                elif defect == 'event': self.run['event'] = 'pull_request'
                elif defect == 'run': self.jobs['jobs'][0]['run_id'] = 12
                elif defect == 'attempt': self.jobs['jobs'][0]['run_attempt'] = 2
                elif defect == 'partial': self.jobs['total_count'] = 3
                else:
                    self.jobs['jobs'].append(copy.deepcopy(self.jobs['jobs'][0])); self.jobs['total_count'] = 3
                with self.assertRaises(ValueError): self.build(workflow=True)

    def test_real_snapshot_is_reproducible_network_free_and_read_only(self):
        paths = [ROOT / 'data' / p for p in ('ipos.json', 'pending_updates.json', 'phase_status.json', 'missing_queue.json', 'public_display_holds.json')]
        before = {p: p.read_bytes() for p in paths}
        with patch('requests.sessions.Session.request', side_effect=AssertionError('No networking')):
            first = health.from_files(paths[0], paths[2], as_of=AT)
            second = health.from_files(paths[0], paths[2], as_of=AT)
        self.assertEqual(first, second)
        self.assertEqual(before, {p: p.read_bytes() for p in paths})
        self.assertEqual(sum(first['summary']['lifecycleScopes'].values()), len(json.loads(before[paths[0]])['ipos']))
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / 'report.json'
            report.write_text(json.dumps(first))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(health.main(['--check-report', str(report)]), 0)
            self.assertEqual(json.loads(output.getvalue())['freshNow'], 'not_asserted')
            first['asOf'] = '2026-09-20T08:00:00Z'; report.write_text(json.dumps(first))
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(health.main(['--check-report', str(report)]), 1)

    def test_required_instant_missing_inputs_and_ambiguous_inventory_fail(self):
        for args in ([], ['--as-of', 'yesterday'], ['--as-of', AT, '--workflow-run', 'run.json'],
                     ['--as-of', AT, '--data', '/missing-file']):
            with contextlib.redirect_stderr(io.StringIO()): self.assertEqual(health.main(args), 1)
        self.payload['ipos'].append(copy.deepcopy(self.row)); self.payload['meta']['recordCount'] = 2
        with self.assertRaises(ValueError): self.build()

    def test_schedule_changes_cannot_silently_reuse_old_deadlines(self):
        original = Path.read_text
        def changed(path, *args, **kwargs):
            text = original(path, *args, **kwargs)
            return text.replace('17 * * * *', '17 1 * * *') if path.name == 'refresh.yml' else text
        with patch.object(Path, 'read_text', changed), self.assertRaisesRegex(ValueError, 'schedule changed'):
            health.from_files(ROOT / 'data/ipos.json', ROOT / 'data/phase_status.json', as_of=AT)

    def test_ci_reports_before_rehearsals_without_a_new_writer_or_schedule(self):
        workflow = (ROOT / '.github/workflows/validate.yml').read_text()
        self.assertLess(workflow.index('tools/report_update_health.py --as-of'), workflow.index('python scripts/apply_corrections.py'))
        self.assertIn('--check-report artifacts/proposal-reconciliation/update-health.json', workflow)
        self.assertNotIn('contents: write', workflow)
        self.assertNotIn('schedule:', workflow)
        self.assertNotIn('report_update_health', (ROOT / '.github/workflows/refresh.yml').read_text())

    def test_python_javascript_recorded_outcome_and_clock_contract(self):
        cases = json.loads((ROOT / 'tests/contracts/operational_health.json').read_text())
        for case in cases:
            with self.subTest(case=case['name']):
                self.assertEqual(health.recorded_outcome(case['health']), case['outcome'])
                self.assertEqual(health.check_clock(case['health'])['state'], case['clock'])

    def test_source_unavailability_and_deferral_do_not_borrow_previous_stage_success(self):
        self.payload['meta']['sourceHealth']['NSE-live'] = {'status':'source_unavailable', 'available':False, 'checkedAt':RECENT, 'error':'Endpoint unavailable'}
        row = next(r for r in self.build()['sources'] if r['name']=='NSE-live')
        self.assertEqual(row['collectionOutcome'],'source_unavailable')
        self.assertEqual(row['lastSourceObservation']['state'],'missing')
        self.assertEqual(row['lastSuccessfulStageOutcome']['status'],'no_change')
        self.assertTrue(row['failureEvidence'])
        self.assertEqual(row['latestFailureOrDeferredReason']['error'],'Endpoint unavailable')
        self.payload['meta']['pipelineStages']['run_update_final_policy.py'] = {'status':'deferred','checkedAt':RECENT,'diagnostics':'Budget exhausted'}
        row = next(r for r in self.build()['sources'] if r['name']=='NSE-live')
        self.assertIsNone(row['lastSuccessfulStageOutcome'])

    def test_current_official_source_and_stale_secondary_source_are_independent(self):
        self.row['subscriptionObservedAt']=RECENT
        current=self.build()['subscriptions'][0]
        self.assertEqual(current['source']['authority'],'official_exchange')
        self.assertFalse(current['observationOlderThanTolerance'])
        self.row.update(subscriptionSource='IPO Premium subscription (secondary)',subscriptionSourceUrl='https://ipopremium.in/example',subscriptionObservedAt=OLD,subscriptionDegraded=True)
        stale=self.build()['subscriptions'][0]
        self.assertEqual(stale['source']['authority'],'secondary')
        self.assertTrue(stale['observationOlderThanTolerance'])
        self.assertEqual(stale['collectionFreshness']['state'],'within_tolerance')

    def test_active_provisional_issue_does_not_become_final_from_a_recent_collection(self):
        self.row.update(lifecycle={'stage':'rhp'},documents=[{'type':'RHP','url':'https://www.sebi.gov.in/rhp.pdf'}])
        before=copy.deepcopy(self.row)
        row=self.build()['subscriptions'][0]
        self.assertEqual(row['lifecycle'],'active_issue_by_recorded_dates')
        self.assertEqual(row['finality'],'not_established_by_snapshot')
        self.assertEqual(self.row,before)

    def test_successful_publisher_window_is_not_an_exact_accepted_commit_clock(self):
        self.payload['meta']['publication'].update(runId='11',collectorCommit='b'*40)
        self.jobs['jobs'][1].update(status='completed',conclusion='success',started_at='2026-09-18T07:01:00Z',completed_at='2026-09-18T07:02:00Z')
        report=self.build(workflow=True)
        self.assertIsNone(report['acceptedPublication']['acceptedAt'])
        delivery=report['acceptedPublication']['delivery']
        self.assertEqual(delivery['publisherWindow']['completedAt'],'2026-09-18T07:02:00Z')
        self.assertIsNone(delivery['publisherWindow']['acceptedAt'])
        self.assertEqual(delivery['collectionToPublisherCompletion']['minutes'],2)
        self.jobs['jobs'][1]['completed_at']='2026-09-18T06:00:00Z'
        self.assertEqual(self.build(workflow=True)['acceptedPublication']['delivery']['publisherWindow']['state'],'publisher_time_not_verified')

    def test_unresolved_proposal_age_remains_unknown_with_separate_origin_execution_bounds(self):
        pending={'summary':{'retainedProposals':1},'entries':[{'inputIndex':0,'fingerprint':'f','runId':'11','comparisonState':'already_applied_exact','nextAction':'Review source before any disposition.'}]}
        self.jobs['jobs'][1].update(status='completed',conclusion='success',started_at='2026-09-18T07:01:00Z',completed_at='2026-09-18T07:02:00Z')
        bundles=[{'run':self.run,'jobs':self.jobs}]
        original=copy.deepcopy((pending,bundles))
        report=health.proposal_health(pending,bundles,health.instant(AT))
        self.assertEqual(report['retainedProposals'],1)
        self.assertEqual(report['resolutionsApplied'],0)
        self.assertEqual(report['entries'][0]['proposalAge']['state'],'unknown')
        bounds=report['entries'][0]['originatingPublisherAgeRange']
        self.assertEqual((bounds['minimumMinutes'],bounds['maximumMinutes']),(58,59))
        self.assertEqual(original,(pending,bundles))
        self.assertIsNone(health.proposal_health(pending,[],health.instant(AT))['entries'][0]['originatingPublisherAgeRange'])
        with self.assertRaises(ValueError): health.proposal_health(pending,bundles+bundles,health.instant(AT))

    def test_source_review_queue_is_reused_without_resolving_items(self):
        queue={'queueCount':1,'queue':[{'id':'example','sourceReviewCount':3}],'generatedAt':RECENT}
        report=health.build_report(self.payload,self.phase,[],as_of=AT,queue=queue)
        self.assertEqual(report['sourceReviewQueue']['sourceReviewItems'],3)
        queue['queueCount']=2
        with self.assertRaises(ValueError): health.build_report(self.payload,self.phase,[],as_of=AT,queue=queue)

    def test_human_report_preserves_unknowns_and_escapes_diagnostics(self):
        self.payload['meta']['sourceHealth']['NSE-live'] = {'ok':False, 'error':'failed | retry\nlater'}
        report = self.build()
        before = copy.deepcopy(report)
        rendered = health.markdown_report(report)
        self.assertIn('Exact accepted publication time: **unknown**', rendered)
        self.assertIn('failed &#124; retry', rendered)
        self.assertIn('NSE-live / official_exchange', rendered)
        self.assertIn('unknown (missing)', rendered)
        self.assertEqual(report, before)

    def test_conflicting_acceptance_cannot_supply_accepted_publisher_window(self):
        self.payload['meta']['publication'].update(runId='11', collectorCommit='c'*40)
        self.jobs['jobs'][1].update(status='completed',conclusion='success',started_at='2026-09-18T07:01:00Z',completed_at='2026-09-18T07:02:00Z')
        delivery = self.build(workflow=True)['acceptedPublication']['delivery']
        self.assertEqual(delivery['state'], 'acceptance_binding_conflict')
        self.assertEqual(delivery['publisherWindow']['state'], 'publisher_time_not_verified')
        self.assertIsNone(delivery['collectionToPublisherCompletion']['minutes'])


if __name__ == '__main__':
    unittest.main()
