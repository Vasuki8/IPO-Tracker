import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "track_subscriptions.py"
spec = importlib.util.spec_from_file_location("track_subscriptions", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class SubscriptionParserTests(unittest.TestCase):
    def test_parse_headline_categories(self):
        payload = {
            "bidDetails": [
                {"category": "Qualified Institutional Buyers", "noOfTime": "41.20"},
                {"category": "Non Institutional Investors", "noOfTime": "28.60"},
                {"category": "Retail Individual Investors", "noOfTime": "12.30"},
                {"category": "Total", "noOfTime": "27.44"},
            ]
        }
        self.assertEqual(
            mod.parse_bid_details(payload),
            {"qib": 41.2, "nii": 28.6, "retail": 12.3, "total": 27.44},
        )

    def test_nii_sub_buckets_are_not_used_as_aggregate(self):
        payload = {
            "bidDetails": [
                {"category": "NII bid amount above ₹10 lakh", "noOfTime": "99.0"},
                {"category": "Non Institutional Investors", "noOfTime": "14.2"},
            ]
        }
        self.assertEqual(mod.parse_bid_details(payload)["nii"], 14.2)

    def test_sme_individual_investor_maps_to_retail_bucket(self):
        payload = {"bidDetails": [{"category": "Individual Investor", "noOfTime": "3.5"}]}
        self.assertEqual(mod.parse_bid_details(payload)["retail"], 3.5)

    def test_root_total_is_used_when_bid_details_omit_total(self):
        payload = {
            "noOfTime": "4.8",
            "bidDetails": [
                {"category": "Qualified Institutional Buyers", "noOfTime": "3.16"},
            ],
        }
        parsed = mod.parse_bid_details(payload)
        self.assertEqual(parsed["qib"], 3.16)
        self.assertEqual(parsed["total"], 4.8)


class SubscriptionHistoryTests(unittest.TestCase):
    def test_identical_snapshot_is_deduplicated(self):
        record = {
            "subscriptionHistory": [
                {
                    "capturedAt": "2026-09-11T10:00:00+05:30",
                    "qib": 1.0,
                    "nii": 2.0,
                    "retail": 3.0,
                    "total": 2.2,
                }
            ]
        }
        added = mod.append_snapshot(
            record,
            {
                "capturedAt": "2026-09-11T11:00:00+05:30",
                "qib": 1.0,
                "nii": 2.0,
                "retail": 3.0,
                "total": 2.2,
            },
        )
        self.assertFalse(added)
        self.assertEqual(len(record["subscriptionHistory"]), 1)

    def test_changed_snapshot_is_appended(self):
        record = {
            "subscriptionHistory": [
                {
                    "capturedAt": "2026-09-11T10:00:00+05:30",
                    "qib": 1.0,
                    "nii": 2.0,
                    "retail": 3.0,
                    "total": 2.2,
                }
            ]
        }
        added = mod.append_snapshot(
            record,
            {
                "capturedAt": "2026-09-11T11:00:00+05:30",
                "qib": 1.5,
                "nii": 2.0,
                "retail": 3.0,
                "total": 2.4,
            },
        )
        self.assertTrue(added)
        self.assertEqual(len(record["subscriptionHistory"]), 2)

    def test_update_record_preserves_existing_total_when_detail_omits_it(self):
        record = {
            "symbol": "TEST",
            "subscription": {"total": 4.8},
            "sources": [],
        }
        detail = {
            "bidDetails": [
                {"category": "Qualified Institutional Buyers", "noOfTime": "3.16"},
                {"category": "Non Institutional Investors", "noOfTime": "7.41"},
                {"category": "Retail Individual Investors", "noOfTime": "4.82"},
            ]
        }
        self.assertTrue(mod.update_record(record, detail))
        self.assertEqual(record["subscription"]["total"], 4.8)
        self.assertEqual(record["subscription"]["qib"], 3.16)
        self.assertEqual(record["subscriptionHistory"][-1]["total"], 4.8)
        self.assertTrue(any(s.get("name") == "NSE subscription detail" for s in record["sources"]))


if __name__ == "__main__":
    unittest.main()
