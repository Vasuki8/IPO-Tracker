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
from objects_evidence_fixtures import objects_evidence

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
        for hold in (item for item in display_holds() if item.get('scope', 'value') == 'value'):
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


class DocumentReviewDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {row['id']: row for row in json.loads(
            (ROOT / 'tests/public_document_reviews_retained.json').read_text(encoding='utf-8'))['ipos']}
        cls.holds = {hold['id']: hold for hold in display_holds() if hold.get('scope') == 'document'}

    def assert_held(self, row):
        before = copy.deepcopy(row)
        actual = project_record(row, today=TODAY)
        self.assertIsNone(actual['objectsOfIssue'])
        decision = actual['publicQuality']['fields']['objectsOfIssue']
        self.assertEqual(decision['state'], 'under_review')
        self.assertEqual(decision['reason'], 'pending_source_repair')
        self.assertEqual(actual['publicQuality']['sources'][decision['source']]['sha256'],
                         row['staticFieldProvenance']['objectsOfIssue']['sha256'])
        profile = public_profile_record(row)
        self.assertNotIn('objectsOfIssue', profile)
        self.assertEqual(profile['publicQuality']['fields']['objectsOfIssue']['state'], 'under_review')
        self.assertEqual(row, before)

    def test_all_reviewed_documents_bind_real_issuer_offer_and_field_proofs(self):
        self.assertEqual(set(self.holds), {'blackbuck', 'mbel', 'shriahimsa', 'genxai', 'kaytex', 'speb'})
        self.assertEqual(set(self.holds), set(self.rows))
        for identifier, row in self.rows.items():
            with self.subTest(id=identifier):
                hold = self.holds[identifier]
                proof = row['staticFieldProvenance']['objectsOfIssue']
                self.assertEqual(hold['identity'], {key: row[key] for key in ('id', 'company', 'symbol', 'openDate')})
                self.assertEqual(proof['issueOpenDate'], row['openDate'])
                self.assertEqual(proof['sha256'], hold['fields']['objectsOfIssue']['sha256'])
                self.assertEqual(proof['sourceUrl'], hold['fields']['objectsOfIssue']['sourceUrl'])
                self.assertEqual(proof['value'], row['objectsOfIssue'])
                self.assertNotIn('objectsOfIssueReview', row)
                # These structurally supported values were otherwise verified;
                # no pre-existing canonical quarantine supplies this protection.
                self.assertEqual(project_record(row, today=TODAY, holds=[])['publicQuality']['fields']['objectsOfIssue']['state'], 'final_verified')
                self.assert_held(row)

    def test_mirror_urls_and_changed_allocations_cannot_resolve_document_review(self):
        for identifier in ('genxai', 'kaytex', 'speb'):
            for variant in ('query', 'mirror', 'changed_allocation'):
                with self.subTest(id=identifier, variant=variant):
                    row = copy.deepcopy(self.rows[identifier])
                    proof = row['staticFieldProvenance']['objectsOfIssue']
                    if variant == 'query':
                        proof['sourceUrl'] += '?mirror=1'
                    elif variant == 'mirror':
                        proof['sourceUrl'] = 'https://www.sebi.gov.in/mirrored-final-prospectus.pdf'
                    else:
                        # A synthetic, internally valid alternate extraction:
                        # it is not evidence of a corrected source allocation.
                        row['objectsOfIssue'] = [{'purpose': 'Working capital requirements', 'amountCr': 1.0}]
                        proof['value'] = copy.deepcopy(row['objectsOfIssue'])
                        proof['evidence'] = objects_evidence(row['objectsOfIssue'])
                    self.assertEqual(project_record(row, today=TODAY, holds=[])['publicQuality']['fields']['objectsOfIssue']['state'], 'final_verified')
                    self.assert_held(row)

    def test_empty_allocation_with_retained_reviewed_proof_stays_under_review(self):
        for empty in (None, []):
            with self.subTest(value=empty):
                row = copy.deepcopy(self.rows['kaytex'])
                row['objectsOfIssue'] = empty
                self.assert_held(row)
        row = copy.deepcopy(self.rows['kaytex'])
        row['objectsOfIssue'] = None
        row.pop('staticFieldProvenance')
        self.assertEqual(project_record(row, today=TODAY)['publicQuality']['fields']['objectsOfIssue']['state'], 'awaiting_disclosure')

    def test_different_document_can_be_verified_under_ordinary_evidence_rules(self):
        for original in self.rows.values():
            with self.subTest(id=original['id']):
                row = copy.deepcopy(original)
                proof = row['staticFieldProvenance']['objectsOfIssue']
                proof['sha256'] = 'a' * 64
                proof['sourceUrl'] = 'https://www.sebi.gov.in/later-final-prospectus.pdf'
                before = copy.deepcopy(row)
                projected = project_record(row, today=TODAY)
                self.assertEqual(projected['objectsOfIssue'], row['objectsOfIssue'])
                self.assertEqual(projected['publicQuality']['fields']['objectsOfIssue']['state'], 'final_verified')
                self.assertEqual(row, before)
                proof['documentType'] = 'RHP'
                self.assertIsNone(project_record(row, today=TODAY)['objectsOfIssue'])

    def test_same_pdf_cannot_transfer_the_hold_to_another_issuer_or_offer(self):
        for field, value in (('id', 'other-issue'), ('company', 'Another Issuer Limited'),
                             ('symbol', 'ANOTHER'), ('openDate', '2026-08-01')):
            with self.subTest(field=field):
                row = copy.deepcopy(self.rows['kaytex'])
                row[field] = value
                if field == 'openDate':
                    row['closeDate'] = '2026-08-03'
                    row['staticFieldProvenance']['objectsOfIssue']['issueOpenDate'] = value
                before = copy.deepcopy(row)
                projected = project_record(row, today=TODAY)
                self.assertEqual(projected['objectsOfIssue'], row['objectsOfIssue'])
                self.assertEqual(projected['publicQuality']['fields']['objectsOfIssue']['state'], 'final_verified')
                self.assertEqual(row, before)

    def test_proof_must_bind_the_exact_reviewed_offer_date(self):
        for value in (None, '2026-08-01'):
            with self.subTest(proof_date=value):
                row = copy.deepcopy(self.rows['kaytex'])
                row['staticFieldProvenance']['objectsOfIssue']['issueOpenDate'] = value
                projected = project_record(row, today=TODAY)
                self.assertIsNone(projected['objectsOfIssue'])
                self.assertEqual(projected['publicQuality']['fields']['objectsOfIssue']['reason'], 'final_evidence_required')

    def test_malformed_document_scope_cannot_silently_skip_the_hold(self):
        for mutation in ('company', 'symbol', 'openDate', 'id', 'scope'):
            hold = copy.deepcopy(self.holds['kaytex'])
            if mutation == 'scope':
                hold['scope'] = 'unknown'
            else:
                hold['identity'].pop(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                project_record(self.rows['kaytex'], today=TODAY, holds=[hold])

    def test_canonical_proofs_review_and_correction_history_survive_public_withholding(self):
        row = copy.deepcopy(self.rows['speb'])
        row['dataCorrections'] = [{'field': 'objectsOfIssue', 'before': None, 'after': copy.deepcopy(row['objectsOfIssue'])}]
        row['objectsOfIssueReview'] = {'status': 'resolved', 'snapshot': {'retained': 'earlier review'}}
        row['documentFieldProvenance'] = {'evidence': {'objectsOfIssue': copy.deepcopy(row['staticFieldProvenance']['objectsOfIssue']['evidence'])}}
        row['subscription'] = {'total': 2.5}
        self.assert_held(row)
        projected = project_record(row, today=TODAY)
        for field in ('dataCorrections', 'objectsOfIssueReview', 'staticFieldProvenance', 'documentFieldProvenance', 'subscription'):
            self.assertEqual(projected[field], row[field])

    def test_layout_holds_remain_value_scoped_for_same_document_repairs(self):
        holds = {hold['id']: hold for hold in display_holds()}
        for identifier in ('emmvee', 'teamtech', 'unimech'):
            self.assertEqual(holds[identifier].get('scope', 'value'), 'value')
            self.assertTrue(all(binding.get('valueDigest') for binding in holds[identifier]['fields'].values()))
        for identifier in ('teamtech', 'unimech'):
            row = evidence({'id': identifier}, 'objectsOfIssue',
                           [{'purpose': 'Working capital requirements', 'amountCr': 1.0}],
                           objects_evidence([{'purpose': 'Working capital requirements', 'amountCr': 1.0}]))
            row['staticFieldProvenance']['objectsOfIssue']['sha256'] = holds[identifier]['fields']['objectsOfIssue']['sha256']
            self.assertEqual(project_record(row, today=TODAY)['objectsOfIssue'], row['objectsOfIssue'])

if __name__ == '__main__':
    unittest.main()
