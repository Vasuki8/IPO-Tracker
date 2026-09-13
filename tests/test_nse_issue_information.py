import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "enrich_nse_issue_information.py"
spec = importlib.util.spec_from_file_location("enrich_nse_issue_information", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class NSEIssueInformationTests(unittest.TestCase):
    def payload(self, *, symbol="SENCO", company="Senco Gold Limited", debt=False):
        return {
            "companyName": company,
            "metaInfo": {
                "symbol": symbol,
                "companyName": company,
                "isDebtSec": debt,
                "segment": "EQUITY",
            },
            "issueInfo": {
                "dataList": [
                    {"title": "Symbol", "value": symbol},
                    {"title": "Bid Lot", "value": "47 Equity Shares and in multiples thereof"},
                    {"title": "Minimum Order Quantity", "value": "47 Equity Shares"},
                ]
            },
        }

    def record(self):
        return {
            "id": "senco",
            "company": "Senco Gold Limited",
            "matchKey": "SENCOGOLD",
            "symbol": "SENCO",
            "board": "Mainboard",
            "exchange": "NSE",
            "openDate": "2026-08-01",
            "lotSize": None,
            "sources": [],
            "observations": {"NSE": {"lotSize": None}},
        }

    def test_parse_bid_lot_and_minimum_order_quantity(self):
        terms = mod.parse_lot_terms(self.payload())
        self.assertEqual(terms["bidLot"], 47)
        self.assertEqual(terms["minimumOrderQuantity"], 47)
        self.assertEqual(terms["lotSize"], 47)

    def test_minimum_order_quantity_wins_when_both_exist(self):
        payload = self.payload()
        payload["issueInfo"]["dataList"][1]["value"] = "100 Equity Shares"
        payload["issueInfo"]["dataList"][2]["value"] = "50 Equity Shares"
        terms = mod.parse_lot_terms(payload)
        self.assertEqual(terms["lotSize"], 50)

    def test_identity_requires_exact_symbol_and_canonical_company(self):
        record = self.record()
        self.assertTrue(mod.identity_matches(record, self.payload()))
        self.assertFalse(mod.identity_matches(record, self.payload(symbol="OTHER")))
        self.assertFalse(mod.identity_matches(record, self.payload(company="Other Limited")))
        self.assertFalse(mod.identity_matches(record, self.payload(debt=True)))

    def test_series_mapping_handles_nse_emerge(self):
        self.assertEqual(mod.series_for(self.record()), "EQ")
        record = self.record()
        record["board"] = "SME"
        record["exchange"] = "NSE Emerge"
        self.assertEqual(mod.series_for(record), "SME")

    def test_recent_missing_lot_is_candidate_with_own_cooldown(self):
        record = self.record()
        today = date(2026, 9, 13)
        self.assertTrue(mod.is_candidate(record, today, 730, retry_days=14))
        record[mod.ATTEMPT_KEY] = {"lastAttemptAt": "2026-09-13T10:00:00+05:30"}
        self.assertFalse(mod.is_candidate(record, today, 730, retry_days=14))
        record.pop(mod.ATTEMPT_KEY)
        record["historicalDetailBackfill"] = {"lastAttemptAt": "2026-09-13T10:00:00+05:30"}
        self.assertTrue(mod.is_candidate(record, today, 730, retry_days=14))

    def test_merge_is_fill_only_and_stamps_provenance(self):
        record = self.record()
        changed = mod.merge_lot(
            record,
            self.payload(),
            page_url="https://www.nseindia.com/market-data/issue-information?series=EQ&symbol=SENCO&type=Past",
        )
        self.assertTrue(changed)
        self.assertEqual(record["lotSize"], 47)
        self.assertEqual(record["minimumBidQuantity"], 47)
        self.assertEqual(record["marketLot"], 47)
        self.assertEqual(record["observations"]["NSE"]["lotSize"], 47)
        self.assertEqual(record["observations"]["NSE-issue-info"]["lotSize"], 47)
        self.assertTrue(any(s.get("name") == mod.SOURCE_NAME for s in record["sources"]))

        # Existing exchange-normalized values always win.
        record["lotSize"] = 99
        changed = mod.merge_lot(
            record,
            self.payload(),
            page_url="https://www.nseindia.com/market-data/issue-information?series=EQ&symbol=SENCO&type=Past",
        )
        self.assertFalse(changed)
        self.assertEqual(record["lotSize"], 99)


if __name__ == "__main__":
    unittest.main()
