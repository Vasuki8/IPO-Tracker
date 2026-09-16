import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import backfill_recent_nse_lot_sizes as lot_backfill


def issue_payload(symbol="TEST", company="Test Limited", rows=None):
    return {
        "metaInfo": {"symbol": symbol, "companyName": company, "isDebtSec": False},
        "companyName": company,
        "issueInfo": {"dataList": rows or []},
    }


class P4NseLotBackfillTests(unittest.TestCase):
    def test_sme_prefers_explicit_bid_lot_over_minimum_order(self):
        payload = issue_payload(rows=[
            {"title": "Bid Lot", "value": "1,200"},
            {"title": "Minimum Order Quantity", "value": "2,400"},
        ])
        self.assertEqual(lot_backfill.extract_lot_size(payload, "SME"), 1200)

    def test_sme_rejects_minimum_order_without_explicit_lot(self):
        payload = issue_payload(rows=[
            {"title": "Minimum Order Quantity", "value": "2,400"},
        ])
        self.assertIsNone(lot_backfill.extract_lot_size(payload, "SME"))

    def test_mainboard_may_use_unambiguous_minimum_order(self):
        payload = issue_payload(rows=[
            {"title": "Minimum Order Quantity", "value": "35"},
        ])
        self.assertEqual(lot_backfill.extract_lot_size(payload, "Mainboard"), 35)

    def test_conflicting_explicit_lot_values_fail_closed(self):
        payload = issue_payload(rows=[
            {"title": "Bid Lot", "value": "1,200"},
        ])
        payload["lotSize"] = 1600
        self.assertIsNone(lot_backfill.extract_lot_size(payload, "SME"))

    def test_issue_information_payload_requires_issuer_identity(self):
        payload = issue_payload(symbol="ABC", company="Different Issuer Limited", rows=[
            {"title": "Bid Lot", "value": "1,200"},
        ])
        record = {
            "id": "abc",
            "company": "Expected Issuer Limited",
            "symbol": "ABC",
            "board": "SME",
            "lotSize": None,
        }
        self.assertEqual(lot_backfill.apply_lot_size(record, payload, series="SME"), [])
        self.assertIsNone(record["lotSize"])

    def test_client_reuses_issue_information_bootstrap(self):
        payload = issue_payload(symbol="ABC", company="ABC Limited")
        page_url = "https://www.nseindia.com/market-data/issue-information?series=SME&symbol=ABC&type=Past"
        api_url = "https://www.nseindia.com/api/ipo-detail?symbol=ABC&series=SME"
        client = lot_backfill.NSEIssueDetailClient()
        with patch.object(
            lot_backfill.issue_info,
            "fetch_detail",
            return_value=(payload, page_url, api_url),
        ) as mocked:
            actual, series, source_url = client.detail("ABC", "SME")
        self.assertIs(actual, payload)
        self.assertEqual(series, "SME")
        self.assertEqual(source_url, page_url)
        mocked.assert_called_once_with(client.s, "ABC", "SME")


if __name__ == "__main__":
    unittest.main()
