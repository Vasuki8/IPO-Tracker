"""Explicit value-hold identity cannot spill into another issuer or offer.

Synthetic source proofs exercise display binding, not a new source-value audit.
"""
import copy
from datetime import date
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from public_quality import project_record, value_digest
from build_company_pages import public_profile_record, public_summary_record

TODAY = date(2026, 9, 18)


class ValueHoldIdentityTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            'id': 'example', 'company': 'Example Limited', 'symbol': 'EXAMPLE',
            'openDate': '2025-08-29', 'closeDate': '2025-09-02', 'status': 'listed',
            'lotSize': 100, 'dataCorrections': [{'reason': 'Retained original event'}],
            'staticFieldProvenance': {'lotSize': {
                'value': 100, 'sourceUrl': 'https://www.sebi.gov.in/files/final.pdf',
                'documentType': 'PROSPECTUS', 'documentDate': '2025-09-03',
                'sha256': 'a' * 64, 'issueOpenDate': '2025-08-29',
                'checkedAt': '2026-09-18T01:00:00Z', 'parserVersion': 32,
                'evidence': {'page': 5, 'row': 'Bid lot: 100 equity shares'},
            }},
        }
        self.hold = {
            'id': 'example', 'scope': 'value',
            'identity': {k: self.record[k] for k in ('id', 'company', 'symbol', 'openDate')},
            'fields': {'lotSize': {'sha256': 'a' * 64, 'valueDigest': value_digest(100)}},
        }

    def project(self, record=None, hold=None):
        record = copy.deepcopy(self.record if record is None else record)
        hold = copy.deepcopy(self.hold if hold is None else hold)
        before = copy.deepcopy((record, hold))
        result = project_record(record, today=TODAY, holds=[hold])
        self.assertEqual((record, hold), before)
        return result

    def test_matching_identity_withholds_but_retains_original_evidence_and_history(self):
        public = self.project()
        self.assertIsNone(public['lotSize'])
        self.assertEqual(public['publicQuality']['fields']['lotSize']['reason'], 'pending_source_repair')
        self.assertEqual(public['dataCorrections'], self.record['dataCorrections'])
        self.assertEqual(public['staticFieldProvenance'], self.record['staticFieldProvenance'])

    def test_same_pdf_and_value_cannot_transfer_hold_to_different_issuer_or_offer(self):
        for field, value in [('id', 'different-id'), ('company', 'Other Limited'),
                             ('symbol', 'OTHER'), ('openDate', '2025-08-28')]:
            with self.subTest(field=field):
                row = copy.deepcopy(self.record)
                row[field] = value
                if field == 'openDate':
                    row['staticFieldProvenance']['lotSize']['issueOpenDate'] = value
                public = self.project(row)
                self.assertEqual(public['lotSize'], 100)
                self.assertEqual(public['publicQuality']['fields']['lotSize']['state'], 'final_verified')

    def test_mismatching_proof_offer_cannot_claim_this_hold_or_source_verification(self):
        row = copy.deepcopy(self.record)
        row['staticFieldProvenance']['lotSize']['issueOpenDate'] = '2024-08-29'
        decision = self.project(row)['publicQuality']['fields']['lotSize']
        self.assertEqual(decision['state'], 'under_review')
        self.assertNotEqual(decision.get('reason'), 'pending_source_repair')

    def test_explicit_malformed_identity_fails_instead_of_becoming_a_broad_value_hold(self):
        for identity in (None, {}, [], '', {'id': 'example'}, {**self.hold['identity'], 'id': 'wrong'}):
            with self.subTest(identity=identity), self.assertRaisesRegex(ValueError, 'issuer and offer identity'):
                self.project(hold={**self.hold, 'identity': identity})
        for key in self.hold['identity']:
            for value in (None, False, 100, ''):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    self.project(hold={**self.hold, 'identity': {**self.hold['identity'], key: value}})

    def test_invalid_scope_fails_even_when_issuer_identity_would_not_match(self):
        row = {**self.record, 'company': 'Other Limited'}
        with self.assertRaisesRegex(ValueError, 'Unsupported public display hold scope'):
            self.project(row, {**self.hold, 'scope': 'unknown'})

    def test_legacy_value_only_hold_keeps_its_original_pdf_and_value_scope(self):
        legacy = copy.deepcopy(self.hold)
        legacy.pop('identity')
        row = {**self.record, 'company': 'Different name not bound by this historical review'}
        self.assertIsNone(self.project(row, legacy)['lotSize'])
        row = copy.deepcopy(self.record)
        row['staticFieldProvenance']['lotSize']['sha256'] = 'b' * 64
        self.assertEqual(self.project(row, legacy)['lotSize'], 100)

    def test_new_collection_clock_parser_or_mirror_cannot_release_an_exact_bound_value(self):
        row = copy.deepcopy(self.record)
        row['staticFieldProvenance']['lotSize'].update(
            sourceUrl='https://nsearchives.nseindia.com/mirror.pdf',
            checkedAt='2026-09-18T05:00:00Z', parserVersion=999)
        self.assertIsNone(self.project(row)['lotSize'])

    def test_changed_value_still_needs_matching_proof_not_just_release_from_hold(self):
        row = copy.deepcopy(self.record)
        row['lotSize'] = 200
        public = self.project(row)
        self.assertIsNone(public['lotSize'])
        self.assertEqual(public['publicQuality']['fields']['lotSize']['state'], 'under_review')
        row['staticFieldProvenance']['lotSize'].update(
            value=200, evidence={'page': 6, 'row': 'Bid lot: 200 equity shares'})
        self.assertEqual(self.project(row)['lotSize'], 200)

    def test_document_conflict_keeps_its_stronger_same_pdf_scope(self):
        hold = copy.deepcopy(self.hold)
        hold['scope'] = 'document'
        hold['fields']['lotSize'].pop('valueDigest')
        row = copy.deepcopy(self.record)
        row['lotSize'] = row['staticFieldProvenance']['lotSize']['value'] = 200
        self.assertEqual(self.project(row, hold)['publicQuality']['fields']['lotSize']['reason'], 'document_conflict')
        row['company'] = 'Other Limited'
        self.assertEqual(self.project(row, hold)['lotSize'], 200)

    def test_profile_and_directory_export_contract_apply_the_same_offer_binding(self):
        for company, expected in [('Example Limited', None), ('Other Limited', 100)]:
            with self.subTest(company=company):
                row = copy.deepcopy(self.record)
                row['company'] = company
                with patch('public_quality.display_holds', return_value=[self.hold]):
                    profile = public_profile_record(row)
                    summary = public_summary_record(row)
                self.assertEqual(profile.get('lotSize'), expected)
                self.assertEqual(summary.get('lotSize'), expected)
                self.assertEqual(profile['publicQuality']['fields']['lotSize']['state'],
                                 summary['publicQuality']['fields']['lotSize']['state'])


if __name__ == '__main__':
    unittest.main()
