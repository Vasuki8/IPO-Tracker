"""A collection must not manufacture a source binding for an older observation."""
import copy
from datetime import datetime
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tools'))
import track_subscriptions as collector
from public_quality import project_record
from publish_transaction import merge_payload
from publication_mode import push_mode
from reconcile_pending_updates import SUBSCRIPTION_FIELDS, subscription_evidence

NOW = datetime.fromisoformat('2026-09-18T16:00:00+05:30')
BSE = 'https://www.bseindia.com/markets/PublicIssues/CummDemandSchedule.aspx?ID=123&status=L'
SECONDARY = 'https://ipopremium.in/ipo-subscription'
VALUES = {'qib': 0, 'nii': 2.5, 'retail': 1.5, 'total': 1.6}


class SubscriptionSnapshotBindingTests(unittest.TestCase):
    def setUp(self):
        self.row = {'id': 'example', 'company': 'Example Limited', 'symbol': 'EXAMPLE',
                    'openDate': '2026-09-16', 'closeDate': '2026-09-21', 'status': 'open',
                    'sources': [], 'dataCorrections': [{'reason': 'retained prior correction'}]}
        self.clock_patch = patch.object(collector.core, 'now_ist', return_value=NOW)
        self.clock_patch.start()
        self.addCleanup(self.clock_patch.stop)

    def apply(self, values=None, **kwargs):
        args = dict(source_name='BSE cumulative demand', source_url=BSE,
                    snapshot_source='BSE cumulative demand')
        args.update(kwargs)
        return collector.apply_subscription(self.row, VALUES if values is None else values, **args)

    def test_official_url_is_in_the_complete_atomic_group_not_only_history(self):
        self.apply()
        self.assertIn('subscriptionSourceUrl', SUBSCRIPTION_FIELDS)
        self.assertEqual(self.row['subscriptionSourceUrl'], BSE)
        self.assertEqual(self.row['subscriptionHistory'][-1]['sourceUrl'], BSE)
        isolated = {k: self.row[k] for k in SUBSCRIPTION_FIELDS if k in self.row}
        result = subscription_evidence(self.row, isolated, as_of=NOW.date(), holds=[])
        self.assertEqual(result['authority'], 'official_exchange')
        self.assertNotIn('snapshot_source_url_missing_or_invalid', result['issues'])
        self.assertIn('source_observation_unavailable', result['issues'])
        self.assertEqual(self.row['dataCorrections'], [{'reason': 'retained prior correction'}])

    def test_secondary_url_and_observation_are_not_promoted_to_official(self):
        observed = '2026-09-18T15:40:00+05:30'
        self.apply(source_name='IPO Premium subscription (secondary)', source_url=SECONDARY,
                   snapshot_source='IPO Premium subscription (secondary)', observed_at=observed)
        public = project_record(self.row, today=NOW.date(), holds=[])
        self.assertEqual(public['subscriptionAuthority'], 'secondary')
        self.assertEqual(public['subscriptionSourceUrl'], SECONDARY)
        self.assertEqual(public['subscriptionObservedAt'], observed)
        self.assertEqual(public['subscriptionCollectedAt'], NOW.isoformat())
        self.assertNotIn('subscriptionFinal', self.row)

    def test_unchanged_values_with_changed_source_keep_both_evidence_events(self):
        self.apply()
        original = copy.deepcopy(self.row['subscriptionHistory'])
        self.assertTrue(self.apply(source_name='IPO Premium subscription (secondary)', source_url=SECONDARY,
                                   snapshot_source='IPO Premium subscription (secondary)'))
        self.assertEqual(self.row['subscriptionHistory'][:1], original)
        self.assertEqual(len(self.row['subscriptionHistory']), 2)
        self.assertEqual(self.row['subscriptionSourceUrl'], SECONDARY)

    def test_unchanged_values_with_changed_url_or_observation_are_not_deduplicated(self):
        self.apply(observed_at='2026-09-18T15:30:00+05:30')
        self.assertTrue(self.apply(source_url=BSE + '&view=full', observed_at='2026-09-18T15:30:00+05:30'))
        self.assertTrue(self.apply(source_url=BSE + '&view=full', observed_at='2026-09-18T15:45:00+05:30'))
        self.assertEqual(len(self.row['subscriptionHistory']), 3)

    def test_collection_only_poll_can_deduplicate_without_losing_current_binding(self):
        self.apply()
        original = copy.deepcopy(self.row['subscriptionHistory'])
        later = datetime.fromisoformat('2026-09-18T16:15:00+05:30')
        with patch.object(collector.core, 'now_ist', return_value=later):
            self.assertFalse(self.apply())
        self.assertEqual(self.row['subscriptionHistory'], original)
        self.assertEqual(self.row['subscriptionCollectedAt'], later.isoformat())
        self.assertIsNone(self.row['subscriptionObservedAt'])
        self.assertEqual(self.row['subscriptionSourceUrl'], BSE)

    def test_unknown_source_time_does_not_inherit_previous_observation(self):
        self.apply(observed_at='2026-09-18T15:30:00+05:30')
        self.assertTrue(self.apply())
        self.assertIsNone(self.row['subscriptionObservedAt'])
        self.assertEqual(self.row['subscriptionTimeBasis'], 'collection-only')
        self.assertEqual(self.row['subscriptionHistory'][0]['observedAt'], '2026-09-18T15:30:00+05:30')

    def test_incomplete_refresh_preserves_entire_previous_snapshot_including_zero(self):
        self.apply()
        before = copy.deepcopy(self.row)
        for omitted in VALUES:
            with self.subTest(omitted=omitted):
                response = {k: v + 1 for k, v in VALUES.items() if k != omitted}
                with self.assertRaisesRegex(ValueError, 'Incomplete subscription response'):
                    self.apply(response, source_name='Different source', source_url=SECONDARY)
                self.assertEqual(self.row, before)

    def test_partial_first_observation_keeps_missing_categories_missing(self):
        self.apply({'total': 0})
        self.assertEqual(self.row['subscription'], {'qib': None, 'nii': None, 'retail': None, 'total': 0})
        self.assertEqual(self.row['subscriptionHistory'][-1]['total'], 0)
        self.assertIsNone(self.row['subscriptionHistory'][-1]['qib'])

    def test_invalid_or_empty_values_fail_before_any_write(self):
        before = copy.deepcopy(self.row)
        for response in ({}, {'total': None}, {'total': False}, {'total': -1}, {'total': float('nan')},
                         {'total': float('inf')}, {'total': '1.2'}, {'total': 1, 'unmapped': 9}, []):
            with self.subTest(response=response), self.assertRaises(ValueError):
                self.apply(response)
            self.assertEqual(self.row, before)

    def test_missing_or_unsafe_source_binding_fails_before_any_write(self):
        before = copy.deepcopy(self.row)
        for url in (None, '', 'http://example.test/', 'https://user:pass@example.test/',
                    'https://example.test/#fragment', 'https://example.test/\n', 'https://example.test:bad/'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.apply(source_url=url)
            self.assertEqual(self.row, before)
        for label in (None, '', ' '):
            with self.subTest(label=label), self.assertRaises(ValueError):
                self.apply(source_name=label)
            self.assertEqual(self.row, before)

    def test_invalid_naive_or_future_observation_never_refreshes_source_clock(self):
        self.apply()
        before = copy.deepcopy(self.row)
        for observed in ('', 'bad', '2026-09-18', '2026-09-18T15:30:00',
                         '2026-09-18T16:00:01+05:30', True, []):
            with self.subTest(observed=observed), self.assertRaises(ValueError):
                self.apply(observed_at=observed)
            self.assertEqual(self.row, before)

    def test_older_pending_group_cannot_detach_current_source_binding(self):
        self.apply()
        base = {'meta': {}, 'ipos': [copy.deepcopy(self.row)]}
        proposed = copy.deepcopy(base)
        proposed['ipos'][0]['subscription']['total'] = 8
        proposed['ipos'][0].pop('subscriptionSourceUrl')
        self.apply(source_url=BSE + '&view=full')
        current = {'meta': {}, 'ipos': [copy.deepcopy(self.row)]}
        result, conflicts = merge_payload(base, proposed, current)
        self.assertEqual(result['ipos'][0]['subscriptionSourceUrl'], BSE + '&view=full')
        self.assertEqual(result['ipos'][0]['subscription'], VALUES)
        self.assertTrue(any(c['path'] == ['ipos', 'example', 'subscriptionSnapshot'] for c in conflicts))


class SubscriptionPublicationScopeTests(unittest.TestCase):
    def test_leaf_collector_change_uses_existing_subscription_stage(self):
        self.assertEqual(push_mode(['scripts/track_subscriptions.py', 'scripts/publication_mode.py',
            'tests/test_subscription_snapshot_binding.py', 'docs/PROJECT_STATUS.md']), 'subscriptions')

    def test_mixed_policy_collector_or_data_change_still_requires_repair(self):
        for path in ('scripts/run_pipeline.py', 'scripts/run_priority_subscriptions_v3.py',
                     'scripts/final_prospectus_parser.py', 'scripts/public_quality.py',
                     'scripts/publish_transaction.py', 'data/ipos.json', 'data/pending_updates.json',
                     'data/public_display_holds.json', 'uv.lock', 'pyproject.toml',
                     '.github/workflows/refresh.yml', 'tools/report_update_health.py', '../docs/note', None):
            with self.subTest(path=path):
                self.assertEqual(push_mode(['scripts/track_subscriptions.py', path]), 'repair')

    def test_request_mixed_with_collector_fails_closed(self):
        with self.assertRaises(RuntimeError):
            push_mode(['scripts/track_subscriptions.py', 'data/reviewed_publication_request.json'])


if __name__ == '__main__':
    unittest.main()
