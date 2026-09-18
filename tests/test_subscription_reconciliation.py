"""Subscription triage separates exact comparison, source binding and two clocks."""
import copy
from datetime import date
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('subscription_report', ROOT / 'tools/reconcile_pending_updates.py')
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)
TODAY = date(2026, 9, 18)


def proposal(base, proposed, path=None):
    entry = {'path': path or ['ipos', 'example', 'subscriptionSnapshot'],
             'baseExists': True, 'base': copy.deepcopy(base),
             'proposedExists': True, 'proposed': copy.deepcopy(proposed), 'status': 'pending_conflict_review'}
    entry['fingerprint'] = report.digest(json.dumps(entry, sort_keys=True).encode())
    entry['runId'] = '123'
    return entry


class SubscriptionReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.identity = {'id': 'example', 'company': 'Example Ltd', 'symbol': 'EXAMPLE',
                         'openDate': '2026-09-16', 'closeDate': '2026-09-18', 'status': 'open'}
        self.current = {
            'subscription': {'qib': 0, 'nii': 1.1, 'retail': 2.2, 'total': 1.5},
            'subscriptionSource': 'NSE subscription detail',
            'subscriptionSourceUrl': 'https://www.nseindia.com/api/ipo-detail?symbol=EXAMPLE',
            'subscriptionObservedAt': '2026-09-18T10:00:00+05:30',
            'subscriptionCollectedAt': '2026-09-18T10:02:00+05:30',
            'subscriptionAsOf': '2026-09-18T10:02:00+05:30',
            'subscriptionTimeBasis': 'source-observation', 'subscriptionDegraded': False,
        }
        self.base = copy.deepcopy(self.current)
        self.base['subscription']['total'] = 1

    def build(self, proposed=None, *, current=None, base=None, extras=None, items=None, rows=None):
        current = self.current if current is None else current
        proposed = current if proposed is None else proposed
        canonical = {'ipos': rows if rows is not None else [{**self.identity, **copy.deepcopy(current), **(extras or {})}]}
        pending = {'updates': items if items is not None else [proposal(self.base if base is None else base, proposed)]}
        before = copy.deepcopy((canonical, pending))
        result = report.build_report(canonical, pending, as_of=TODAY, holds=[])
        self.assertEqual((canonical, pending), before)
        self.assertEqual(result['resolutionsApplied'], 0)
        self.assertEqual(len(result['entries']), len(pending['updates']))
        for entry in result['entries']:
            self.assertEqual(entry['status'], 'pending_conflict_review')
            self.assertFalse(entry['resolutionChanged'])
        return result

    def test_exact_zero_snapshot_is_reported_not_final_verified_or_resolved(self):
        result = self.build()
        e = result['entries'][0]
        self.assertEqual(result['schemaVersion'], 2)
        self.assertEqual(e['comparisonState'], 'already_applied_exact')
        self.assertEqual(result['summary']['subscriptionSnapshotProposals'], 1)
        self.assertEqual(result['summary']['documentWithValueDifferences'], 0)
        d = e['subscriptionComparison']
        self.assertEqual(d['current']['publicState'], 'reported')
        self.assertEqual(d['current']['authority'], 'official_exchange')
        self.assertFalse(d['current']['requiresSourceReview'])
        self.assertEqual(d['current']['missingCategories'], [])
        self.assertEqual(d['sourceRelation'], 'same_label_and_url')
        self.assertEqual(d['current']['finality'], 'not_established_by_snapshot')
        self.assertFalse(d['orderingIsResolution'])

    def test_identical_values_from_new_secondary_source_still_conflict(self):
        candidate = copy.deepcopy(self.current)
        candidate.update(subscriptionSource='Example data (secondary)', subscriptionSourceUrl='https://example.test/bids',
                         subscriptionObservedAt='2026-09-18T10:01:00+05:30')
        e = self.build(candidate)['entries'][0]
        self.assertEqual(e['comparisonState'], 'still_conflicting')
        self.assertEqual(e['differingValueFields'], [])
        self.assertEqual(e['subscriptionComparison']['proposed']['authority'], 'secondary')
        self.assertEqual(e['subscriptionComparison']['sourceRelation'], 'different_source')
        self.assertEqual(e['subscriptionComparison']['observationRelation'], 'proposed_newer')

    def test_exchange_name_or_impostor_url_is_not_official_authority(self):
        for url in (None, 'https://www.nseindia.com.example.test/bids', 'http://www.nseindia.com/bids',
                    'https://user:secret@www.nseindia.com/bids'):
            with self.subTest(url=url):
                candidate = copy.deepcopy(self.current)
                candidate['subscriptionSourceUrl'] = url
                d = self.build(candidate)['entries'][0]['subscriptionComparison']['proposed']
                self.assertEqual(d['authority'], 'unknown')
                self.assertTrue(d['requiresSourceReview'])

    def test_no_borrowed_source_or_observation_from_current_record_or_history(self):
        candidate = copy.deepcopy(self.current)
        candidate.pop('subscriptionSourceUrl')
        candidate.pop('subscriptionObservedAt')
        history = [{'source': candidate['subscriptionSource'], 'sourceUrl': self.current['subscriptionSourceUrl'],
                    'observedAt': None, **candidate['subscription']}]
        extras = {'sources': [{'name': candidate['subscriptionSource'], 'url': self.current['subscriptionSourceUrl']}],
                  'subscriptionHistory': history}
        d = self.build(candidate, extras=extras)['entries'][0]['subscriptionComparison']['proposed']
        self.assertIsNone(d['sourceUrl'])
        self.assertEqual(d['authority'], 'unknown')
        self.assertEqual(d['observed']['status'], 'missing')
        self.assertNotIn('subscriptionObservedAt', d['storedClocks'])

    def test_same_total_with_different_category_is_not_the_same_snapshot(self):
        candidate = copy.deepcopy(self.current)
        candidate['subscription']['qib'] = 0.5
        e = self.build(candidate)['entries'][0]
        self.assertEqual(e['comparisonState'], 'still_conflicting')
        self.assertEqual(e['differingValueFields'], ['subscription'])
        self.assertEqual(e['subscriptionComparison']['observationRelation'], 'same_instant')

    def test_old_observation_with_new_collection_is_never_a_new_observation(self):
        candidate = copy.deepcopy(self.current)
        candidate.update(subscriptionObservedAt='2026-09-18T09:00:00+05:30',
                         subscriptionCollectedAt='2026-09-18T11:00:00+05:30',
                         subscriptionAsOf='2026-09-18T11:00:00+05:30')
        e = self.build(candidate)['entries'][0]
        self.assertEqual(e['comparisonState'], 'still_conflicting')
        self.assertEqual(e['subscriptionComparison']['observationRelation'], 'proposed_older')
        self.assertEqual(e['subscriptionComparison']['collectionRelation'], 'proposed_newer')

    def test_offsets_compare_instants_but_do_not_rewrite_exact_snapshot(self):
        candidate = copy.deepcopy(self.current)
        candidate['subscriptionObservedAt'] = '2026-09-18T04:30:00Z'
        e = self.build(candidate)['entries'][0]
        self.assertEqual(e['comparisonState'], 'still_conflicting')
        d = e['subscriptionComparison']
        self.assertEqual(d['observationRelation'], 'same_instant')
        self.assertEqual(d['proposed']['storedClocks']['subscriptionObservedAt'], '2026-09-18T04:30:00Z')

    def test_collection_only_and_legacy_asof_never_order_source_observations(self):
        for observed in (None, self.current['subscriptionObservedAt']):
            with self.subTest(observed=observed):
                candidate = copy.deepcopy(self.current)
                candidate.update(subscriptionObservedAt=observed, subscriptionTimeBasis='collection-only')
                candidate.pop('subscriptionCollectedAt')
                d = self.build(candidate)['entries'][0]['subscriptionComparison']
                self.assertEqual(d['observationRelation'], 'not_comparable')
                self.assertEqual(d['proposed']['collected']['field'], 'subscriptionAsOf')
                self.assertIn('source_observation_unavailable', d['proposed']['issues'])
                if observed is not None:
                    self.assertIn('observation_present_but_basis_collection_only', d['proposed']['issues'])

    def test_missing_invalid_naive_and_inconsistent_clocks_are_explicit(self):
        for value in (None, '', False, '2026-09-18', '2026-09-18T10:00:00',
                      '2026-02-30T10:00:00Z', '2026-09-18T10:00:00+25:00'):
            with self.subTest(value=value):
                candidate = copy.deepcopy(self.current)
                candidate['subscriptionObservedAt'] = value
                d = self.build(candidate)['entries'][0]['subscriptionComparison']
                self.assertEqual(d['observationRelation'], 'not_comparable')
                self.assertTrue(d['proposed']['requiresSourceReview'])
        candidate = copy.deepcopy(self.current)
        candidate['subscriptionCollectedAt'] = 'invalid'
        d = self.build(candidate)['entries'][0]['subscriptionComparison']
        self.assertEqual(d['collectionRelation'], 'not_comparable')  # No fallback to valid AsOf.
        candidate['subscriptionCollectedAt'] = '2026-09-18T09:00:00+05:30'
        issues = self.build(candidate)['entries'][0]['subscriptionComparison']['proposed']['issues']
        self.assertIn('collection_alias_disagrees', issues)
        self.assertIn('source_observation_after_collection', issues)
        candidate['subscriptionTimeBasis'] = 'unknown'
        d = self.build(candidate)['entries'][0]['subscriptionComparison']
        self.assertEqual(d['observationRelation'], 'not_comparable')

    def test_missing_null_zero_and_boolean_categories_and_metadata_differ(self):
        for defect in ('missing', 'null', 'false'):
            with self.subTest(defect=defect):
                candidate = copy.deepcopy(self.current)
                if defect == 'missing':
                    candidate['subscription'].pop('qib')
                else:
                    candidate['subscription']['qib'] = None if defect == 'null' else False
                e = self.build(candidate)['entries'][0]
                self.assertEqual(e['comparisonState'], 'still_conflicting')
                self.assertIn('subscription', e['differingValueFields'])
                self.assertTrue(e['subscriptionComparison']['proposed']['requiresSourceReview'])
        for value in (None, 0, True):
            candidate = {**self.current, 'subscriptionDegraded': value}
            self.assertEqual(self.build(candidate)['entries'][0]['comparisonState'], 'still_conflicting')
        candidate = copy.deepcopy(self.current)
        candidate.pop('subscriptionDegraded')
        self.assertEqual(self.build(candidate)['entries'][0]['currentOnlyFields'], ['subscriptionDegraded'])

    def test_malformed_numeric_snapshot_and_current_review_stay_unaccepted(self):
        for value in (-1, '2x', False):
            candidate = copy.deepcopy(self.current)
            candidate['subscription']['total'] = value
            d = self.build(candidate)['entries'][0]['subscriptionComparison']['proposed']
            self.assertEqual(d['publicState'], 'under_review')
            self.assertTrue(d['requiresSourceReview'])
        e = self.build(extras={'dataReview': {'subscription': 'Conflicting retained evidence'}})['entries'][0]
        self.assertEqual(e['comparisonState'], 'already_applied_exact')
        self.assertEqual(e['subscriptionComparison']['current']['publicState'], 'under_review')
        candidate = {**self.current, 'subscription': ['bad shape']}
        d = self.build(candidate)['entries'][0]['subscriptionComparison']['proposed']
        self.assertEqual(d['status'], 'assessment_failed')

    def test_unchanged_base_no_change_and_recollection_are_distinct_not_retry_authority(self):
        candidate = copy.deepcopy(self.current)
        candidate['subscription']['total'] = 3
        e = self.build(candidate, base=self.current)['entries'][0]
        self.assertEqual(e['comparisonState'], 'base_unchanged')
        e = self.build(self.base, base=self.base)['entries'][0]
        self.assertEqual(e['comparisonState'], 'no_change_proposal')
        candidate = copy.deepcopy(self.current)
        candidate.update(subscriptionCollectedAt='2026-09-18T10:03:00+05:30', subscriptionAsOf='2026-09-18T10:03:00+05:30')
        e = self.build(candidate)['entries'][0]
        self.assertEqual(e['comparisonState'], 'still_conflicting')
        self.assertEqual(e['subscriptionComparison']['observationRelation'], 'same_instant')

    def test_unknown_group_fields_nested_paths_and_missing_issuers_remain_visible(self):
        candidate = {**self.current, 'undocumentedFinalFlag': True}
        e = self.build(candidate)['entries'][0]
        self.assertEqual(e['comparisonState'], 'legacy_group_scope')
        self.assertIn('undocumentedFinalFlag', e['unsupportedFields'])
        nested = proposal({}, {}, ['ipos', 'example', 'subscriptionSnapshot', 'subscription'])
        self.assertEqual(self.build(items=[nested])['entries'][0]['comparisonState'], 'not_assessed')
        for rows, state in (([], 'missing_record'), ([self.identity, self.identity], 'ambiguous_record')):
            self.assertEqual(self.build(rows=rows)['entries'][0]['comparisonState'], state)

    def test_malformed_envelope_and_group_cannot_pass_as_empty_equality(self):
        for item in (proposal(None, None), proposal({}, []),
                     {**proposal({}, {}), 'fingerprint': '0' * 64},
                     {**proposal({}, {}), 'proposedExists': False}):
            self.assertEqual(self.build(items=[item])['entries'][0]['comparisonState'], 'malformed_proposal')

    def test_duplicate_occurrences_and_all_other_families_are_preserved(self):
        sub = proposal(self.base, self.current)
        other = proposal({}, {}, ['ipos', 'example', 'lotTerms'])
        result = self.build(items=[other, sub, copy.deepcopy(sub)])
        self.assertEqual([e['inputIndex'] for e in result['entries']], [0, 1, 2])
        self.assertEqual(result['summary']['duplicateFingerprintOccurrences'], 1)
        self.assertEqual(result['summary']['subscriptionSnapshotProposals'], 2)
        self.assertEqual(result['entries'][0]['comparisonState'], 'not_assessed')

    def test_after_close_does_not_turn_last_intraday_observation_into_final(self):
        e = self.build(extras={'status': 'listed', 'closeDate': '2026-09-17'})['entries'][0]
        self.assertEqual(e['subscriptionComparison']['current']['publicState'], 'reported')
        self.assertEqual(e['subscriptionComparison']['current']['finality'], 'not_established_by_snapshot')


if __name__ == '__main__':
    unittest.main()
