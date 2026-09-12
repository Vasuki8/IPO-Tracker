import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_nse_primary_market_reports.py"
spec = importlib.util.spec_from_file_location("enrich_nse_primary_market_reports", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


HEADER = [
    "Sr. No.",
    "Company_Name",
    "Symbol",
    "Isin_Number",
    "Isin_Descriptor",
    "Sector",
    "Exchange",
    "Issue_Type",
    "Instrument_Type",
    "Date_of_Shareholding_ Meeting",
    "Relevant_Date",
    "Name Of The Registrar",
    "Merchant_Banker_Name",
    "Total_Issue_Size",
    "Fresh_Issue_Size",
    "Offer_For_Sale",
    "Issue_Open_Date",
    "Issue_Close_Date",
    "Listing_Date",
    "Face_Value",
    "Premium",
    "Issue_Price",
    "Issue_Size (In Crores)",
    "No_of_Allottees",
]


class NSEPrimaryMarketReportTests(unittest.TestCase):
    def test_excel_serial_date(self):
        self.assertEqual(mod.excel_date("46204"), "2026-07-01")
        self.assertEqual(mod.excel_date("2026-07-01"), "2026-07-01")
        self.assertIsNone(mod.excel_date("NA"))

    def test_ipo_row_parses_issue_composition(self):
        row = [
            "8",
            "Knack Packaging Limited",
            "KNACK",
            "INE17QZ01016",
            "",
            "Private",
            "BSE/NSE",
            "IPO",
            "Equity",
            "",
            "",
            "MUFG Intime India Private Limited",
            "Systematix Corporate Services Limited",
            "25865164",
            "22365164",
            "3500000",
            "46204",
            "46206",
            "46211",
            "10",
            "160",
            "170",
            "439.5",
            "105956",
        ]
        parsed = mod.parse_report_rows([HEADER, row], "https://nsearchives.nseindia.com/report.xlsx")
        self.assertEqual(len(parsed), 1)
        item = parsed[0]
        self.assertEqual(item["symbol"], "KNACK")
        self.assertEqual(item["openDate"], "2026-07-01")
        self.assertEqual(item["closeDate"], "2026-07-03")
        self.assertEqual(item["listingDate"], "2026-07-08")
        self.assertEqual(item["sharesOffered"], 25_865_164)
        self.assertEqual(item["issueSizeCr"], 439.5)
        self.assertEqual(item["issueComposition"]["freshShares"], 22_365_164)
        self.assertEqual(item["issueComposition"]["ofsShares"], 3_500_000)
        self.assertAlmostEqual(item["freshIssueCr"], 380.2078, places=4)
        self.assertEqual(item["ofsCr"], 59.5)
        self.assertEqual(item["issueComposition"]["totalIssueSizeCr"], 439.5)

    def test_non_ipo_primary_market_row_is_rejected(self):
        row = [
            "20", "Example Ltd", "EXAMPLE", "INE000000001", "", "Private", "NSE/BSE",
            "Preferential", "Equity", "", "", "", "", "1000000", "1000000", "0",
            "", "", "46204", "10", "90", "100", "10", "1",
        ]
        self.assertEqual(mod.parse_report_rows([HEADER, row], "https://example/report.xlsx"), [])

    def test_nse_sme_ipo_is_accepted(self):
        row = [
            "3", "Shreedhar Spinners Limited", "SHREEDHAR", "INE0K3301012", "", "Private", "NSE",
            "NSE SME IPO", "Equity", "", "", "", "", "5788000", "5788000", "0",
            "46196", "46198", "46204", "10", "43", "53", "30.68", "623",
        ]
        parsed = mod.parse_report_rows([HEADER, row], "https://example/report.xlsx")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["issueComposition"]["ofsShares"], 0)
        self.assertEqual(parsed[0]["issueSizeCr"], 30.68)

    def test_best_row_requires_near_issue_date(self):
        rows = [
            {
                "symbol": "EXAMPLE",
                "matchKey": "EXAMPLE",
                "openDate": "2024-01-01",
            },
            {
                "symbol": "EXAMPLE",
                "matchKey": "EXAMPLE",
                "openDate": "2026-07-01",
            },
        ]
        record = {"symbol": "EXAMPLE", "company": "Example Limited", "openDate": "2026-07-02"}
        self.assertEqual(mod.best_report_row(rows, record)["openDate"], "2026-07-01")
        record["openDate"] = "2025-01-01"
        self.assertIsNone(mod.best_report_row(rows, record))

    def test_merge_is_fill_only_and_adds_nse_provenance(self):
        record = {
            "company": "Knack Packaging Limited",
            "symbol": "KNACK",
            "openDate": "2026-07-01",
            "closeDate": "2026-07-03",
            "listingDate": None,
            "sharesOffered": None,
            "issueSizeCr": 440.0,
            "freshIssueCr": None,
            "ofsCr": None,
            "issueComposition": None,
            "sources": [{"name": "NSE past", "url": "https://nse.example"}],
            "observations": {"NSE": {"openDate": "2026-07-01", "issueSizeCr": None}},
        }
        row = {
            "symbol": "KNACK",
            "openDate": "2026-07-01",
            "closeDate": "2026-07-03",
            "listingDate": "2026-07-08",
            "sharesOffered": 25_865_164,
            "issueSizeCr": 439.5,
            "freshIssueCr": 380.2078,
            "ofsCr": 59.5,
            "issueComposition": {
                "freshShares": 22_365_164,
                "ofsShares": 3_500_000,
                "freshIssueCr": 380.2078,
                "ofsCr": 59.5,
                "totalIssueSizeCr": 439.5,
                "valuationPriceUsed": 170.0,
            },
            "sourceUrl": "https://nsearchives.nseindia.com/report.xlsx",
        }
        changed = mod.merge_report_row(record, row)
        self.assertEqual(record["issueSizeCr"], 440.0)
        self.assertEqual(record["sharesOffered"], 25_865_164)
        self.assertEqual(record["listingDate"], "2026-07-08")
        self.assertEqual(record["issueComposition"]["ofsShares"], 3_500_000)
        self.assertIn("issueComposition", changed)
        self.assertEqual(record["observations"]["NSE"]["issueSizeCr"], 439.5)
        self.assertTrue(any(s["name"] == "NSE primary-market monthly report" for s in record["sources"]))

    def test_candidate_scope_is_recent_and_missing_exchange_fact(self):
        today = date(2026, 9, 13)
        self.assertTrue(
            mod.is_candidate(
                {"openDate": "2026-07-01", "issueSizeCr": None, "issueComposition": None, "listingDate": None},
                today,
                730,
            )
        )
        self.assertFalse(
            mod.is_candidate(
                {"openDate": "2020-07-01", "issueSizeCr": None, "issueComposition": None, "listingDate": None},
                today,
                730,
            )
        )


if __name__ == "__main__":
    unittest.main()
