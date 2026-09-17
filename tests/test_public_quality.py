"""Trust-boundary tests with real retained records and hostile/legacy inputs."""
import copy
from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from public_quality import project_record, value_digest, display_holds
from build_company_pages import public_profile_record, public_summary_record

TODAY = date(2026, 9, 17)
SOURCE = 'https://nsearchives.nseindia.com/corporate/FINAL.pdf'

def evidence(record, field, value, detail=None):
    record.setdefault('openDate', '2026-09-01')
    record[field] = copy.deepcopy(value)
    record.setdefault('staticFieldProvenance', {})[field] = {
        'value': copy.deepcopy(value), 'sourceUrl': SOURCE, 'documentType': 'PROSPECTUS',
        'sha256': 'a' * 64, 'issueOpenDate': record.get('openDate'),
        'documentDate': '2026-09-10', 'parserVersion': 32,
        'evidence': detail or {'page': 1, 'heading': field, 'value': copy.deepcopy(value)},
    }
    return record

class PublicQualityTests(unittest.TestCase):
    def project(self, record, **kwargs):
        return project_record(record, today=TODAY, holds=[], **kwargs)

    def test_whole_record_verified_badge_cannot_verify_fields(self):
        record = {'id': 'legacy', 'status': 'listed', 'lotSize': 120,
                  'validation': {'status': 'verified'},
                  'staticSourcePolicy': {'verifiedFields': ['lotSize']}}
        actual = self.project(record)
        self.assertIsNone(actual['lotSize'])
        self.assertEqual(actual['publicQuality']['fields']['lotSize']['state'], 'under_review')
        self.assertEqual(record['lotSize'], 120)

    def test_exact_final_source_field_is_retained_with_source_identity(self):
        record = evidence({'id': 'final', 'openDate': '2026-09-01'}, 'lotSize', 120)
        actual = self.project(record)
        self.assertEqual(actual['lotSize'], 120)
        decision = actual['publicQuality']['fields']['lotSize']
        self.assertEqual(decision['state'], 'final_verified')
        self.assertEqual(actual['publicQuality']['sources'][decision['source']]['sha256'], 'a'*64)

    def test_mismatch_missing_hash_rhp_and_pending_proof_are_never_verified(self):
        for change in ({'value': 121}, {'sha256': None}, {'documentType': 'RHP'}, {'sourceUrl': 'javascript:alert(1)'}):
            with self.subTest(change=change):
                record = evidence({'id': 'bad'}, 'lotSize', 120)
                record['staticFieldProvenance']['lotSize'].update(change)
                self.assertIsNone(self.project(record)['lotSize'])
        record = evidence({'id': 'pending'}, 'lotSize', 120)
        record['staticSourcePolicy'] = {'pendingRevalidationFields': ['lotSize']}
        self.assertIsNone(self.project(record)['lotSize'])

    def test_source_failure_missing_disclosure_and_review_are_distinct(self):
        record = {'id': 'empty', 'dataAvailability': {'exchange.lotSize': {'status': 'source-unavailable'}},
                  'dataReview': {'registrar': 'Unsupported table'}}
        states = self.project(record)['publicQuality']['fields']
        self.assertEqual(states['lotSize']['state'], 'source_unavailable')
        self.assertEqual(states['priceBand']['state'], 'awaiting_disclosure')
        self.assertEqual(states['registrar']['state'], 'under_review')

    def test_complete_composition_is_withheld_for_one_conflicting_component(self):
        record = {'id': 'conflict', 'issueSizeCr': 20, 'freshIssueCr': 25, 'ofsCr': 25,
                  'issueComposition': {'freshShares': 10, 'ofsShares': 10},
                  'validation': {'status': 'verified'}}
        actual = self.project(record)
        for field in ('issueComposition','issueSizeCr','freshIssueCr','ofsCr'):
            self.assertIsNone(actual[field])
            self.assertEqual(actual['publicQuality']['fields'][field]['state'],'under_review')

    def test_zero_subscription_is_real_but_zero_lot_is_invalid(self):
        actual = self.project({'id': 'zero', 'lotSize': 0, 'subscription': {'total': 0}})
        self.assertEqual(actual['subscription']['total'], 0)
        self.assertIsNone(actual['lotSize'])

    def test_active_provisional_requires_equal_issue_bound_official_observation(self):
        record = {'id': 'active', 'status': 'open', 'openDate': '2026-09-15', 'closeDate': '2026-09-18',
                  'priceBand': {'min': 100, 'max': 110},
                  'observations': {'NSE': {'openDate': '2026-09-15', 'closeDate': '2026-09-18', 'priceBand': {'min': 100, 'max': 110}}},
                  'sources': [{'name': 'NSE current', 'url': 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo', 'asOf': '2026-09-17T10:00:00+05:30'}]}
        actual = self.project(record)
        self.assertEqual(actual['priceBand'], record['priceBand'])
        self.assertEqual(actual['publicQuality']['fields']['priceBand']['state'], 'provisional')
        self.assertEqual(actual['publicQuality']['fields']['priceBand']['until'], '2026-09-18')
        for path, value in [('status','listed'), ('closeDate','2026-09-16')]:
            changed = copy.deepcopy(record); changed[path] = value
            self.assertIsNone(self.project(changed)['priceBand'])
        record['observations']['NSE']['priceBand']['max'] = 111
        self.assertIsNone(self.project(record)['priceBand'])

    def test_raw_rhp_attachment_cannot_prove_a_disclosed_value(self):
        actual = self.project({'id': 'rhp', 'status': 'open', 'openDate': '2026-09-15', 'closeDate': '2026-09-18',
                               'lotSize': 120, 'documents': [{'type': 'RHP', 'url': SOURCE}]})
        self.assertIsNone(self.project(actual)['lotSize'])

    def test_collection_time_is_not_promoted_to_observation_time(self):
        actual = self.project({'id': 'time', 'subscription': {'total': 1}, 'subscriptionAsOf': '2026-09-17T23:14:00+05:30'})
        self.assertIsNone(actual['subscriptionObservedAt'])
        self.assertEqual(actual['subscriptionCollectedAt'], '2026-09-17T23:14:00+05:30')
        self.assertEqual(actual['subscriptionTimeBasis'], 'collection-only')
        self.assertEqual(actual['subscriptionAuthority'], 'unknown')

    def test_current_secondary_snapshot_cannot_borrow_an_official_history_url(self):
        record = {'id': 'time', 'subscription': {'total': 2}, 'subscriptionSource': 'Example (secondary)',
                  'subscriptionHistory': [{'total': 1, 'source': 'NSE', 'sourceUrl': SOURCE, 'capturedAt': '2026-09-17T10:00:00+05:30'}]}
        actual = self.project(record)
        self.assertIsNone(actual['subscriptionSourceUrl'])
        self.assertEqual(actual['subscriptionAuthority'], 'secondary')

    def test_matching_history_can_supply_url_but_never_replaces_current_times(self):
        record = {'id': 'time', 'subscription': {'total': 2}, 'subscriptionSource': 'Example (secondary)',
                  'subscriptionObservedAt': '2026-09-17T20:18:00+05:30', 'subscriptionCollectedAt': '2026-09-17T23:14:00+05:30',
                  'subscriptionHistory': [{'total': 2, 'source': 'Example (secondary)', 'sourceUrl': 'https://example.com/subscription',
                                            'observedAt': '2026-09-17T20:18:00+05:30', 'capturedAt': '2026-09-17T21:00:00+05:30'}]}
        actual = self.project(record)
        self.assertEqual(actual['subscriptionObservedAt'], record['subscriptionObservedAt'])
        self.assertEqual(actual['subscriptionCollectedAt'], record['subscriptionCollectedAt'])
        self.assertEqual(actual['subscriptionSourceUrl'], 'https://example.com/subscription')

    def test_minimum_bid_is_not_inferred_from_bid_or_market_lot(self):
        record = evidence({'id': 'lots'}, 'lotSize', 2000)
        evidence(record, 'marketLot', 1000)
        actual = self.project(record)
        self.assertEqual(actual['lotSize'], 2000)
        self.assertEqual(actual['marketLot'], 1000)
        self.assertIsNone(actual['minimumBidQuantity'])
        self.assertNotIn('minimumApplicationAmount', actual)

    def test_hold_is_exactly_bound_and_does_not_modify_a_later_repair(self):
        record = evidence({'id': 'held'}, 'lotSize', 120)
        hold = {'id': 'held', 'fields': {'lotSize': {'sha256': 'a'*64, 'valueDigest': value_digest(120)}}}
        self.assertIsNone(project_record(record, today=TODAY, holds=[hold])['lotSize'])
        evidence(record, 'lotSize', 121)
        self.assertEqual(project_record(record, today=TODAY, holds=[hold])['lotSize'], 121)

    def test_public_projection_does_not_mutate_canonical_audit_or_proofs(self):
        record = evidence({'id': 'audit', 'dataCorrections': [{'before': 1, 'after': 2}],
                           'dataReview': {'lotSize': 'Source review'}}, 'lotSize', 120)
        before = copy.deepcopy(record)
        actual = self.project(record)
        self.assertEqual(record, before)
        self.assertIsNone(actual['lotSize'])
        self.assertEqual(actual['dataCorrections'], before['dataCorrections'])

class RetainedProductionDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {r['id']: r for r in json.loads((ROOT/'tests/public_quality_retained.json').read_text(encoding='utf-8'))['ipos']}

    def test_shakti_conflicting_amounts_absent_from_both_public_projections(self):
        # Regression uses the immutable retained production row; not a claim about the
        # correct replacement numbers in its source document.
        row = self.rows['shakti-polytarp-limited']
        for projection in (public_summary_record, public_profile_record):
            result = projection(row)
            self.assertNotIn('issueSizeCr',result)
            self.assertEqual(result['publicQuality']['fields']['issueSizeCr']['state'],'under_review')
        result = public_profile_record(row)
        for field in ('freshIssueCr','ofsCr','issueComposition','financials','promoters'):
            self.assertNotIn(field,result)

    def test_retained_pr94_holds_bind_current_data_and_remain_presentation_only(self):
        for hold in display_holds():
            row = self.rows[hold['id']]
            for field, binding in hold['fields'].items():
                # Immutable, selected production values must match every guard;
                # a mismatch must fail rather than silently skipping acceptance.
                proof = row.get('staticFieldProvenance',{}).get(field,{})
                self.assertEqual(proof.get('sha256'), binding['sha256'])
                self.assertEqual(value_digest(row.get(field)), binding['valueDigest'])
                result = public_profile_record(row)
                self.assertNotIn(field, result)
                decision = result['publicQuality']['fields'][field]
                self.assertEqual(decision['state'], 'under_review')
                self.assertEqual(decision['reason'], 'composition_review' if hold['id'] == 'emmvee' else 'pending_source_repair')

if __name__ == '__main__':
    unittest.main()
