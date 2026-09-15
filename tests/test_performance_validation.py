import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from collect_price_history import apply_daily
from validate_data import validate_record


class PerformanceValidationTests(unittest.TestCase):
    def setUp(self):
        self.record = {"id": "example", "symbol": "EXAMPLE", "listingDate": "2025-09-10"}
        for day, close in (("2025-09-10", 125), ("2025-09-12", 150)):
            apply_daily(self.record, {"EXAMPLE": {"symbol": "EXAMPLE", "series": "EQ", "date": day, "open": 120, "close": close}},
                        {"symbol": "NIFTY 50", "date": day, "value": 20000}, day,
                        "https://nsearchives.nseindia.com/prices.csv", "https://nsearchives.nseindia.com/index.csv", "hash")

    def test_valid_close_based_history_passes(self):
        self.assertEqual(validate_record(self.record), [])

    def test_stale_return_is_rejected(self):
        self.record["performance"]["benchmarkExcessReturnPct"] = 25
        self.assertTrue(any(item["field"] == "performance.benchmarkExcessReturnPct" for item in validate_record(self.record)))

    def test_price_observation_requires_a_positive_value_date_and_source(self):
        for changes in ({"price": float("nan")}, {"price": -1}, {"observedAt": "2025-09-09"}, {"observedAt": "invalid"}, {"sourceUrl": None}):
            with self.subTest(changes=changes):
                record = copy.deepcopy(self.record)
                record["performance"]["latest"].update(changes)
                self.assertTrue(any(item["field"] == "performance.observations" for item in validate_record(record)))

    def test_listing_conflicts_stay_in_review_queue(self):
        self.record["listing"]["priceConflicts"] = [{"field": "listPrice", "proposed": 121}]
        self.assertTrue(any(item["field"] == "listing" and item["severity"] == "review" for item in validate_record(self.record)))


if __name__ == "__main__":
    unittest.main()
