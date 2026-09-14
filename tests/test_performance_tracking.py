import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from performance_tracking import apply_quote, percentage


class PerformanceTests(unittest.TestCase):
    def quote(self, when='14-Sep-2025 15:30:00', symbol='EXAMPLE'):
        return {'info': {'symbol': symbol}, 'metadata': {'lastUpdateTime': when}, 'priceInfo': {'lastPrice': 125, 'open': 120}}

    def test_later_open_is_not_listing_day_price(self):
        row = {'symbol': 'EXAMPLE', 'listingDate': '2025-09-10', 'listing': {'issuePrice': 100}}
        apply_quote(row, self.quote())
        self.assertEqual(row['performance']['returnSinceIssuePct'], 25)
        self.assertNotIn('listPrice', row['listing'])
        self.assertIsNone(row['performance']['benchmarkExcessReturnPct'])

    def test_listing_day_and_deduplication(self):
        row = {'symbol': 'EXAMPLE', 'listingDate': '2025-09-14', 'listing': {'issuePrice': 100}}
        apply_quote(row, self.quote())
        apply_quote(row, self.quote())
        self.assertEqual(row['listing']['gainPct'], 20)
        self.assertEqual(len(row['performance']['observations']), 1)

    def test_cap_is_not_final_issue_price(self):
        row = {'symbol': 'EXAMPLE', 'priceBand': {'max': 100}}
        apply_quote(row, self.quote())
        self.assertIsNone(row['performance']['returnSinceIssuePct'])

    def test_wrong_identity_and_undated_quotes_rejected(self):
        with self.assertRaises(ValueError):
            apply_quote({'symbol': 'EXAMPLE'}, self.quote(symbol='OTHER'))
        with self.assertRaises(ValueError):
            apply_quote({'symbol': 'EXAMPLE'}, self.quote(when=''))

    def test_stale_quote_does_not_replace_newer_value(self):
        row = {'symbol': 'EXAMPLE'}
        apply_quote(row, self.quote())
        self.assertFalse(apply_quote(row, self.quote('11-Sep-2025 15:30:00')))
        self.assertEqual(row['performance']['latest']['observedAt'][:10], '2025-09-14')


if __name__ == '__main__':
    unittest.main()
