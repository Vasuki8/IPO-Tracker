import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "backfill_recent_nse_lot_sizes.py"
spec = importlib.util.spec_from_file_location("backfill_recent_nse_lot_sizes", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class NSELotBackfillTests(unittest.TestCase):
    def test_explicit_lot_field_mainboard(self):
        payload = {"issueDetail": {"lotSize": 44, "minimumBidQuantity": 44}}
        self.assertEqual(mod.extract_lot_size(payload, "Mainboard"), 44)

    def test_explicit_lot_field_sme(self):
        payload = {"issueDetail": {"marketLot": 1200, "minimumBidQuantity": 2400}}
        self.assertEqual(mod.extract_lot_size(payload, "SME"), 1200)

    def test_sme_minimum_bid_quantity_is_not_assumed_to_be_one_lot(self):
        payload = {"issueDetail": {"minimumBidQuantity": 2400}}
        self.assertIsNone(mod.extract_lot_size(payload, "SME"))

    def test_mainboard_minimum_bid_quantity_can_fill_when_unambiguous(self):
        payload = {"issueDetail": {"minimumBidQuantity": 35}}
        self.assertEqual(mod.extract_lot_size(payload, "Mainboard"), 35)

    def test_conflicting_explicit_lot_fields_are_rejected(self):
        payload = {"issueDetail": {"lotSize": 50, "marketLot": 100}}
        self.assertIsNone(mod.extract_lot_size(payload, "Mainboard"))

    def test_investor_category_rows_do_not_create_fallback_lot(self):
        payload = {
            "bidDetails": [
                {"category": "Retail Individual Investors", "minimumBidQuantity": 100},
                {"category": "Qualified Institutional Buyers", "minimumBidQuantity": 5000},
            ]
        }
        self.assertIsNone(mod.extract_lot_size(payload, "Mainboard"))

    def test_symbol_guard_rejects_wrong_response(self):
        record = {
            "id": "example",
            "symbol": "RIGHT",
            "board": "Mainboard",
            "lotSize": None,
            "priceBand": {"max": 100},
            "sources": [],
            "observations": {},
        }
        payload = {"symbol": "WRONG", "issueDetail": {"lotSize": 50}}
        self.assertEqual(mod.apply_lot_size(record, payload, series="EQ"), [])
        self.assertIsNone(record["lotSize"])

    def test_fill_only_and_min_investment(self):
        record = {
            "id": "example",
            "symbol": "EXAMPLE",
            "board": "Mainboard",
            "lotSize": None,
            "minInvestment": None,
            "priceBand": {"min": 95, "max": 100},
            "sources": [],
            "observations": {},
        }
        payload = {"symbol": "EXAMPLE", "issueDetail": {"lotSize": 50}}
        changed = mod.apply_lot_size(record, payload, series="EQ")
        self.assertEqual(record["lotSize"], 50)
        self.assertEqual(record["minInvestment"], 5000.0)
        self.assertIn("lotSize", changed)
        self.assertIn("minInvestment", changed)

        second = {"symbol": "EXAMPLE", "issueDetail": {"lotSize": 75}}
        self.assertEqual(mod.apply_lot_size(record, second, series="EQ"), [])
        self.assertEqual(record["lotSize"], 50)

    def test_queue_targets_only_p4_lot_gaps(self):
        queue = {
            "queue": [
                {"id": "a", "priorityLabel": "P4 recent history (2y)", "missingFields": ["exchange.lotSize"]},
                {"id": "b", "priorityLabel": "P4 recent history (2y)", "missingFields": ["exchange.issueSizeCr"]},
                {"id": "c", "priorityLabel": "P5 historical", "missingFields": ["exchange.lotSize"]},
            ]
        }
        self.assertEqual(mod.queue_targets(queue), {"a"})


if __name__ == "__main__":
    unittest.main()
