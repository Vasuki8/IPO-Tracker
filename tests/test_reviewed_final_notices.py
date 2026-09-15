import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from apply_corrections import apply, fill_reviewed_fields, fingerprint


class ReviewedFinalNoticeTests(unittest.TestCase):
    def setUp(self):
        self.identity = {'id': 'example', 'company': 'Example Limited', 'symbol': 'EXAMPLE', 'openDate': '2026-01-01'}
        self.entry = {'identity': self.identity, 'field': 'lotSize', 'value': 400,
                      'source': {'name': 'Issuer final notice', 'url': 'https://example.com/final.pdf', 'kind': 'offer-document'},
                      'evidence': {'page': 9, 'basis': 'Lot size: 400 shares; minimum application: two lots.'},
                      'reviewedAt': '2026-09-15T04:40:00+00:00'}
        self.rows = {'example': dict(self.identity)}

    def test_fill_preserves_evidence_and_is_idempotent(self):
        self.assertEqual(fill_reviewed_fields(self.rows, [self.entry]), (1, []))
        row = self.rows['example']
        self.assertEqual(row['lotSize'], 400)
        self.assertNotIn('minInvestment', row)
        self.assertEqual(row['dataCorrections'][0]['evidence'], self.entry['evidence'])
        self.assertEqual(row['sources'][0]['url'], self.entry['source']['url'])
        once = copy.deepcopy(self.rows)
        self.assertEqual(fill_reviewed_fields(self.rows, [self.entry]), (0, []))
        self.assertEqual(self.rows, once)

    def test_wrong_issuer_or_offer_cannot_receive_terms(self):
        for field in self.identity:
            with self.subTest(field=field):
                rows = copy.deepcopy(self.rows)
                rows['example'][field] = 'changed'
                applied, conflicts = fill_reviewed_fields(rows, [self.entry])
                self.assertEqual(applied, 0)
                self.assertTrue(conflicts)
                self.assertNotIn('lotSize', rows['example'])

    def test_existing_value_keeps_its_provenance(self):
        self.rows['example']['lotSize'] = 800
        before = copy.deepcopy(self.rows)
        applied, conflicts = fill_reviewed_fields(self.rows, [self.entry])
        self.assertEqual(applied, 0)
        self.assertTrue(conflicts)
        self.assertEqual(self.rows, before)

    def test_final_notice_is_independent_of_older_migration_conflicts(self):
        row = dict(self.identity, registrar='Current Services Limited')
        registry = {'changes': [{'id': 'example', 'field': 'registrar', 'beforeHash': fingerprint(None), 'after': 'Earlier Services Limited'}],
                    'fillMissing': [self.entry]}
        applied, conflicts = apply({'ipos': [row]}, registry)
        self.assertEqual(applied, 1)
        self.assertTrue(conflicts)
        self.assertEqual(row['lotSize'], 400)
        self.assertEqual(row['registrar'], 'Current Services Limited')

    def test_invalid_lot_and_listing_date_are_rejected(self):
        for field, value in [('lotSize', True), ('lotSize', -2), ('listingDate', '2025-12-31')]:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    fill_reviewed_fields(self.rows, [{**self.entry, 'field': field, 'value': value}])
        self.assertEqual(self.rows['example'], self.identity)

    def test_composition_requires_explicit_nonnegative_share_counts(self):
        entry = {**self.entry, 'field': 'issueComposition', 'value': {'freshShares': 4598400, 'ofsShares': 0}}
        for value in ({'freshShares': 1}, {'freshShares': 0, 'ofsShares': 0},
                      {'freshShares': True, 'ofsShares': 0}, {'freshShares': -1, 'ofsShares': 2}):
            with self.assertRaises(ValueError):
                fill_reviewed_fields(self.rows, [{**entry, 'value': value}])
        self.assertEqual(fill_reviewed_fields(self.rows, [entry]), (1, []))
        entry['value']['freshShares'] = 1
        self.assertEqual(self.rows['example']['issueComposition']['freshShares'], 4598400)

    def test_replacement_group_requires_identity_and_matching_prior_values(self):
        row = dict(self.identity, exchange='NSE', issueComposition={'freshShares': 100, 'ofsShares': 0})
        entries = [{**self.entry, 'id': 'example', 'field': field, 'beforeHash': fingerprint(row[field]), 'after': after}
                   for field, after in [('exchange', 'BSE'), ('issueComposition', {'freshShares': 0, 'ofsShares': 100})]]
        registry = {'changes': entries}
        for changed in ({'openDate': '2026-02-01'}, {'exchange': 'Changed source'}):
            other = {**copy.deepcopy(row), **changed}
            applied, conflicts = apply({'ipos': [other]}, registry)
            self.assertEqual(applied, 0)
            self.assertTrue(conflicts)
            self.assertNotIn('dataCorrections', other)
        self.assertEqual(apply({'ipos': [row]}, registry), (2, []))
        self.assertEqual(row['exchange'], 'BSE')
        self.assertEqual(row['dataCorrections'][1]['before']['freshShares'], 100)
        self.assertEqual(len(row['sources']), 1)
        self.assertEqual(apply({'ipos': [row]}, registry), (0, []))
        self.assertEqual(len(row['dataCorrections']), 2)


if __name__ == '__main__':
    unittest.main()
