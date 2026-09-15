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


if __name__ == '__main__':
    unittest.main()
