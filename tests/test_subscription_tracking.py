import copy
import importlib.util
import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

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

    def test_parse_bse_cumulative_demand(self):
        html = """
        <table>
          <tr><th>Sr.No.</th><th>Category</th><th>Offered</th><th>Bid</th><th>Times</th></tr>
          <tr><td>1</td><td>Qualified Institutional Buyers (QIBs)</td><td>38,20,095</td><td>2,93,98,278</td><td>7.70</td></tr>
          <tr><td>2</td><td>Non Institutional Investors(NIIS)</td><td>28,65,072</td><td>45,36,662</td><td>1.58</td></tr>
          <tr><td>2.1</td><td>Non Institutional Investors(Bid amount of more than Ten Lakh Rupees)</td><td>19,10,048</td><td>33,28,143</td><td>1.74</td></tr>
          <tr><td>3</td><td>Retail Individual Investors (RIIs)</td><td>66,85,168</td><td>46,27,506</td><td>0.69</td></tr>
          <tr><td>Total</td><td>1,34,12,842</td><td>3,86,35,766</td><td>2.88</td></tr>
        </table>
        """
        self.assertEqual(
            mod.parse_bse_demand_html(html),
            {"qib": 7.7, "nii": 1.58, "retail": 0.69, "total": 2.88},
        )

    def test_extract_bse_cumulative_demand_link(self):
        soup = BeautifulSoup(
            '<tr><td>Example Limited</td><td><a href="CummDemandSchedule.aspx?ID=7154&amp;status=L">Cumulative Bid Details</a></td></tr>',
            "html.parser",
        )
        url = mod._extract_bse_demand_url(
            soup.select_one("tr"),
            "https://www.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p",
        )
        self.assertEqual(
            url,
            "https://www.bseindia.com/markets/PublicIssues/CummDemandSchedule.aspx?ID=7154&status=L",
        )

    def test_display_ipo_url_maps_to_cumulative_demand(self):
        url = mod._demand_url_from_display_url(
            "https://www.bseindia.com/markets/publicIssues/DisplayIPO.aspx?IPONo=7425&id=4279&idtype=1&status=L&type=IPO"
        )
        self.assertEqual(
            url,
            "https://www.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID=7425&status=L",
        )


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

    def test_incomplete_response_cannot_relabel_an_old_total_as_a_new_observation(self):
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
        before = copy.deepcopy(record)
        with self.assertRaisesRegex(ValueError, "Incomplete subscription response"):
            mod.update_record(record, detail)
        self.assertEqual(record, before)


if __name__ == "__main__":
    unittest.main()
