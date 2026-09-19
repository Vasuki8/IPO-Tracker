"""Collection clocks describe real attempts, including failures, never observations."""
import copy
from datetime import date, datetime
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('isolated_core_clocks', ROOT / 'scripts/update_data.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
from normalize_source_health import normalize_source_health
from publish_transaction import merge_payload, merge_value

NOW = datetime.fromisoformat('2026-09-19T00:01:00+05:30')
OLD = '2026-09-17T20:00:00Z'


class CoreCollectionClockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'ipos.json'
        self.accepted = {'meta': {'schemaVersion': 8, 'generatedAt': OLD,
            'publication': {'runId': 'accepted'}, 'offerDocumentHealth': {'failed': 1},
            'sourceHealth': {'BSE': {'ok': False, 'checkedAt': OLD, 'error': 'old failure'},
                             'Issuer-offer-docs': {'ok': False, 'failed': 1}}},
            'ipos': [{'id': 'retained', 'company': 'Retained Limited', 'issueSizeCr': None,
                      'sources': [{'name': 'BSE', 'url': core.BSE_URL}],
                      'issueCompositionReview': {'status': 'pending'},
                      'dataCorrections': [{'source': 'retained'}]}]}
        self.path.write_text(json.dumps(self.accepted), encoding='utf-8')
        self.nse = Mock()
        self.nse.current.return_value = []
        self.nse.upcoming.return_value = []
        self.nse.past.return_value = []
        self.sebi = SimpleNamespace(fetch_recent_filings=Mock(return_value=[]))
        self.bse = SimpleNamespace(current_issues=Mock(return_value=[]))
        for target, value in [('DATA_FILE', self.path), ('now_ist', Mock(return_value=NOW)),
                              ('NSEClient', Mock(return_value=self.nse)),
                              ('SEBIClient', Mock(return_value=self.sebi)),
                              ('BSEClient', Mock(return_value=self.bse))]:
            patcher = patch.object(core, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        sleeper = patch.object(core.time, 'sleep')
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def run_core(self, *args):
        with patch.object(sys, 'argv', ['collector', '--history-days', '1', *args]):
            result = core.main()
        return result, json.loads(self.path.read_text(encoding='utf-8'))

    def test_all_failed_preserves_actual_payload_not_wrapper_cleaned_view(self):
        for call in (self.nse.current, self.nse.upcoming, self.nse.past,
                     self.sebi.fetch_recent_filings, self.bse.current_issues):
            call.side_effect = RuntimeError('HTTP 403')
        with patch.object(core, 'load_existing', return_value={'ipos': []}):
            code, result = self.run_core()
        self.assertEqual(code, 2)
        self.assertEqual(result['ipos'], self.accepted['ipos'])
        for key in ('generatedAt', 'schemaVersion', 'publication', 'offerDocumentHealth'):
            self.assertEqual(result['meta'][key], self.accepted['meta'][key])
        for name in ('NSE-live', 'NSE-history', 'BSE', 'SEBI'):
            health = result['meta']['sourceHealth'][name]
            self.assertFalse(health['ok'])
            self.assertEqual(health['checkedAt'], NOW.isoformat())
            self.assertIn('HTTP 403', str(health['errors']))
            self.assertNotIn('observedAt', health)
        # The existing serialized publisher accepts the metadata while preserving
        # rows/reviews/corrections; this is not a second publication path.
        merged, conflicts = merge_payload(self.accepted, result, self.accepted)
        self.assertEqual(conflicts, [])
        self.assertEqual(merged['ipos'], self.accepted['ipos'])
        self.assertEqual(merged['meta']['sourceHealth'], result['meta']['sourceHealth'])

    def test_zero_history_rows_is_a_real_success_without_an_observation(self):
        code, result = self.run_core('--skip-bse', '--skip-sebi')
        self.assertEqual(code, 0)
        health = result['meta']['sourceHealth']['NSE-history']
        self.assertTrue(health['ok'])
        self.assertEqual(health['status'], 'checked')
        self.assertEqual(health['checkedAt'], '2026-09-19T00:01:00+05:30')
        self.assertEqual(health['checks'][0]['toDate'], '2026-09-19')
        self.assertNotIn('observedAt', health)
        self.assertEqual(result['ipos'], self.accepted['ipos'])

    def test_skips_preserve_previous_failure_without_checking_or_restamping(self):
        _, result = self.run_core('--skip-bse', '--skip-sebi')
        self.sebi.fetch_recent_filings.assert_not_called()
        self.bse.current_issues.assert_not_called()
        health = result['meta']['sourceHealth']['BSE']
        self.assertEqual(health['status'], 'deferred')
        self.assertNotIn('checkedAt', health)
        self.assertNotIn('ok', health)
        self.assertEqual(health['lastAttempt'], self.accepted['meta']['sourceHealth']['BSE'])
        _, repeated = self.run_core('--skip-bse', '--skip-sebi')
        self.assertEqual(repeated['meta']['sourceHealth']['BSE'], health)

    def test_successful_live_endpoint_survives_failed_sibling_in_both_orders(self):
        row = {'companyName': 'New Example Limited', 'symbol': 'NEWEX'}
        for successful, failed in ((self.nse.current, self.nse.upcoming),
                                   (self.nse.upcoming, self.nse.current)):
            successful.side_effect = None
            successful.return_value = [row]
            failed.side_effect = RuntimeError('HTTP 503')
            code, result = self.run_core('--skip-bse', '--skip-sebi')
            self.assertEqual(code, 0)
            self.assertIn('New Example Limited', [x['company'] for x in result['ipos']])
            health = result['meta']['sourceHealth']['NSE-live']
            self.assertTrue(health['ok'])
            self.assertEqual((health['attempted'], health['failed']), (2, 1))
            self.assertEqual([x['url'] for x in health['checks']], [
                f'{core.NSE_API}/ipo-current-issue', f'{core.NSE_API}/all-upcoming-issues?category=ipo'])

    def test_history_partial_and_unattempted_ranges_survive_legacy_normalizer(self):
        ranges = [(date(2026, 1, i), date(2026, 1, i)) for i in (1, 2, 3)]
        self.nse.past.side_effect = [[], RuntimeError('blocked'), []]
        with patch.object(core, 'history_ranges', return_value=ranges):
            _, result = self.run_core('--skip-bse', '--skip-sebi')
        health = result['meta']['sourceHealth']['NSE-history']
        self.assertEqual((health['attempted'], health['failed'], health['deferred']), (2, 1, 1))
        self.assertTrue(health['ok'])
        self.assertNotIn('checkedAt', health['checks'][-1])
        before = copy.deepcopy(result)
        self.assertEqual(normalize_source_health(result), before)
        self.assertEqual(self.nse.past.call_count, 2)

    def test_bootstrap_continues_after_failed_range(self):
        ranges = [(date(2026, 1, i), date(2026, 1, i)) for i in (1, 2, 3)]
        self.nse.past.side_effect = [[], RuntimeError('blocked'), []]
        with patch.object(core, 'history_ranges', return_value=ranges):
            _, result = self.run_core('--bootstrap-history', '--skip-bse', '--skip-sebi')
        health = result['meta']['sourceHealth']['NSE-history']
        self.assertEqual((health['attempted'], health['failed'], health['deferred']), (3, 1, 0))

    def test_sebi_partial_pages_retain_failures_and_successful_filings(self):
        # Exercise the real client separately from the main-method mock.
        with patch.object(core.requests, 'Session'):
            client = ORIGINAL_SEBI()
        response = SimpleNamespace(text='<a href="/filing.html">Example Limited - RHP</a>',
                                   raise_for_status=lambda: None)
        client.s = Mock()
        client.s.get.side_effect = [response, RuntimeError('HTTP 403')]
        rows = client.fetch_recent_filings(2)
        self.assertEqual(len(rows), 1)
        health = core.collection_health(client.collection_checks, len(rows))
        self.assertTrue(health['ok'])
        self.assertEqual(health['failed'], 1)
        self.assertEqual(health['checks'][1]['page'], 2)
        self.assertEqual(health['checkedAt'], NOW.isoformat())

    def test_sebi_parser_failure_keeps_previous_page_and_attempt_receipt(self):
        with patch.object(core.requests, 'Session'):
            client = ORIGINAL_SEBI()
        client.s = Mock()
        client.s.get.return_value = SimpleNamespace(text='page', raise_for_status=lambda: None)
        client.parse_filings = Mock(side_effect=[[{'url': 'https://www.sebi.gov.in/one', 'type': 'RHP'}],
                                                 ValueError('unsupported table')])
        rows = client.fetch_recent_filings(2)
        self.assertEqual(len(rows), 1)
        self.assertEqual(client.collection_checks[-1]['error'], 'unsupported table')

    def test_attachment_failure_cannot_hide_behind_failed_endpoint_or_change_rows(self):
        self.bse.current_issues.return_value = [{'company': 'New'}]
        self.bse.collection_checks = [core.collection_check('https://bse.test/one', 1),
                                     core.collection_check('https://bse.test/two', error='HTTP 403')]
        def failed_attach(records, rows):
            records['incomplete'] = {'company': 'must not survive'}
            raise ValueError('identity conflict')
        with patch.object(core, 'attach_bse', side_effect=failed_attach):
            code, result = self.run_core('--skip-sebi')
        health = result['meta']['sourceHealth']['BSE']
        self.assertEqual(code, 2)
        self.assertFalse(health['ok'])
        self.assertEqual(health['attempted'], 2)
        self.assertEqual(health['processingError'], 'attachment: identity conflict')
        self.assertIn('HTTP 403', str(health['errors']))
        self.assertEqual(result['ipos'], self.accepted['ipos'])

    def test_nse_unrecognized_payload_is_not_a_successful_empty_list(self):
        with patch.object(core.requests, 'Session'):
            client = ORIGINAL_NSE()
        client.primed = True
        response = Mock()
        response.json.return_value = {'message': 'Access denied'}
        client.s = Mock()
        client.s.get.return_value = response
        with self.assertRaisesRegex(ValueError, 'Unsupported NSE response'):
            client.current()
        response.json.return_value = {'data': []}
        self.assertEqual(client.current(), [])

    def test_concurrent_publication_cannot_combine_success_with_failed_attempt_clock(self):
        base = core.collection_health([core.collection_check('https://nse.test', error='403')])
        proposed = core.collection_health([core.collection_check('https://nse.test', 2)], 2)
        current = copy.deepcopy(base)
        current['checkedAt'] = '2026-09-19T01:00:00+05:30'
        current['checks'][0]['checkedAt'] = current['checkedAt']
        path = ['meta', 'sourceHealth', 'NSE-live']
        conflicts = []
        self.assertEqual(merge_value(base, proposed, current, path, conflicts), current)
        self.assertEqual(merge_value(base, proposed, base, path, conflicts), proposed)
        self.assertEqual(conflicts, [])  # existing metadata current-wins policy
        before_meta = {'sourceHealth': {'NSE-live': base, 'BSE': base}}
        proposed_meta = {'sourceHealth': {'NSE-live': proposed, 'BSE': base}}
        current_meta = {'sourceHealth': {'NSE-live': base, 'BSE': current}}
        merged = merge_value(before_meta, proposed_meta, current_meta, ['meta'], [])
        self.assertEqual(merged['sourceHealth'], {'NSE-live': proposed, 'BSE': current})
        deferred = core.deferred_collection(current, 'Explicit skip')
        self.assertEqual(merge_value(base, proposed, deferred, path, []), deferred)
        later_success = {**proposed, 'checkedAt': '2026-09-19T02:00:00+05:30'}
        self.assertEqual(merge_value(proposed, current, later_success, path, []), later_success)

    def test_stage_publication_keeps_status_exit_and_clock_of_same_attempt(self):
        base = {'status': 'failed', 'exitCode': 2, 'checkedAt': OLD}
        proposed = {'status': 'no_change', 'exitCode': 0, 'checkedAt': NOW.isoformat()}
        current = {**base, 'checkedAt': '2026-09-19T02:00:00+05:30'}
        path = ['meta', 'pipelineStages', 'run_update_final_policy.py']
        self.assertEqual(merge_value(base, proposed, current, path, []), current)


ORIGINAL_SEBI = core.SEBIClient
ORIGINAL_NSE = core.NSEClient


if __name__ == '__main__':
    unittest.main()
