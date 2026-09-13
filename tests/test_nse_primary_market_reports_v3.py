import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_nse_primary_market_reports_v3.py"
spec = importlib.util.spec_from_file_location("enrich_nse_primary_market_reports_v3", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


SYMBOLLESS_HEADER = [
    "Sr. No.", "Company_Name", "Isin_Number", "Isin_Descriptor", "Sector",
    "Exchange", "Issue_Type", "Instrument_Type", "Date_of_Shareholding_ Meeting",
    "Relevant_Date", "Name Of The Registrar", "Merchant_Banker_Name",
    "Total_Issue_Size", "Fresh_Issue_Size", "Offer_For_Sale", "Issue_Open_Date",
    "Issue_Close_Date", "Listing_Date", "Face_Value", "Premium", "Issue_Price",
    "Issue Size (In cr.)", "No_of_Allottees",
]

SYMBOL_HEADER = [
    "Sr. No.", "Company_Name", "Symbol", "Isin_Number", "Isin_Descriptor", "Sector",
    "Exchange", "Issue_Type", "Instrument_Type", "Date_of_Shareholding_ Meeting",
    "Relevant_Date", "Name Of The Registrar", "Merchant_Banker_Name",
    "Total_Issue_Size", "Fresh_Issue_Size", "Offer_For_Sale", "Issue_Open_Date",
    "Issue_Close_Date", "Listing_Date", "Face_Value", "Premium", "Issue_Price",
    "Issue_Size (In Crores)", "No_of_Allottees",
]


class NSEPrimaryMarketReportV3Tests(unittest.TestCase):
    def test_parser_version(self):
        self.assertEqual(mod.PARSER_VERSION, 3)

    def test_symbol_is_optional_and_old_issue_size_header_is_supported(self):
        row = [
            "1", "Premier Energies Limited", "INE0BS701011", "", "Private", "NSE/BSE",
            "IPO", "Equity", "", "", "KFin Technologies Limited", "Kotak Capital",
            "62909200", "28709200", "34200000", "45531", "45533", "45538", "1",
            "449", "450", "2830.4", "686082",
        ]
        parsed = mod.parse_report_rows([SYMBOLLESS_HEADER, row], "https://nse.example/sep24.xlsx")
        self.assertEqual(len(parsed), 1)
        item = parsed[0]
        self.assertIsNone(item["symbol"])
        self.assertEqual(item["issueSizeCr"], 2830.4)
        self.assertEqual(item["issueComposition"]["freshShares"], 28_709_200)
        self.assertEqual(item["issueComposition"]["ofsShares"], 34_200_000)
        self.assertEqual(item["openDate"], "2024-08-27")

    def test_blank_instrument_type_is_allowed_for_explicit_ipo(self):
        row = [
            "3", "Bharat Coking Coal Limited", "INE05XR01022", "", "Public", "BSE/NSE",
            "IPO", "", "", "", "KFin Technologies Limited", "ICICI Securities Limited",
            "465700000", "0", "465700000", "46031", "46035", "46041", "10", "13",
            "23", "1068.78", "323111",
        ]
        parsed = mod.parse_report_rows([SYMBOLLESS_HEADER, row], "https://nse.example/jan26.xlsx")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["company"], "Bharat Coking Coal Limited")
        self.assertEqual(parsed[0]["issueComposition"]["ofsShares"], 465_700_000)

    def test_non_equity_instrument_is_rejected(self):
        row = [
            "3", "Example Limited", "INE000000001", "", "Private", "NSE", "IPO",
            "Warrants", "", "", "", "", "1000000", "1000000", "0", "46031",
            "46035", "46041", "10", "13", "23", "2.3", "100",
        ]
        self.assertEqual(mod.parse_report_rows([SYMBOLLESS_HEADER, row], "https://example/x.xlsx"), [])

    def test_exact_symbol_and_company_survive_bad_report_date(self):
        rows = [{
            "company": "Highway Infrastructure Limited",
            "matchKey": mod.core.canonical_company("Highway Infrastructure Limited"),
            "symbol": "HILINFRA",
            "openDate": "2025-07-05",
        }]
        record = {
            "company": "Highway Infrastructure Limited",
            "symbol": "HILINFRA",
            "openDate": "2025-08-05",
        }
        self.assertIs(mod.best_report_row(rows, record), rows[0])

    def test_same_symbol_different_company_is_not_strong_match(self):
        rows = [{
            "company": "Different Limited",
            "matchKey": mod.core.canonical_company("Different Limited"),
            "symbol": "EXAMPLE",
            "openDate": "2025-07-05",
        }]
        record = {
            "company": "Example Limited",
            "symbol": "EXAMPLE",
            "openDate": "2025-08-05",
        }
        self.assertIsNone(mod.best_report_row(rows, record))

    def test_symbol_less_company_match_requires_near_date(self):
        rows = [{
            "company": "Premier Energies Limited",
            "matchKey": mod.core.canonical_company("Premier Energies Limited"),
            "symbol": None,
            "openDate": "2024-08-27",
        }]
        record = {
            "company": "Premier Energies Limited",
            "symbol": "PREMIERENE",
            "openDate": "2024-08-27",
        }
        self.assertIs(mod.best_report_row(rows, record), rows[0])
        record["openDate"] = "2024-10-01"
        self.assertIsNone(mod.best_report_row(rows, record))

    def test_symbol_layout_still_parses(self):
        row = [
            "6", "Highway Infrastructure Limited", "HILINFRA", "INE00RL01028", "",
            "Private", "NSE/BSE", "IPO", "", "", "", "Bigshare Services",
            "Pantomath Capital", "18571428", "13931428", "4640000", "45843", "45845",
            "45881", "5", "65", "70", "130", "37234",
        ]
        parsed = mod.parse_report_rows([SYMBOL_HEADER, row], "https://nse.example/aug25.xlsx")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["symbol"], "HILINFRA")
        self.assertEqual(parsed[0]["issueSizeCr"], 130.0)


if __name__ == "__main__":
    unittest.main()
