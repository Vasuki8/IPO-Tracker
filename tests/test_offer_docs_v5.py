import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v5.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v5", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OfferDocsV5Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 5)
        self.assertEqual(mod.base.PARSER_VERSION, 5)

    def test_vertical_financial_table_is_parsed(self):
        text = """
        SUMMARY OF FINANCIAL INFORMATION
        (₹ in lakhs, except ratios)
        Particulars
        Fiscal 2026
        Fiscal 2025
        Fiscal 2024

        Revenue from Operations
        12,500.20
        10,100.10
        8,900.00

        EBITDA
        2,500.00
        2,100.00
        1,700.00

        Profit after Tax (PAT)
        1,200.50
        980.20
        740.10

        Net Worth
        6,500.00
        5,300.00
        4,200.00
        """
        parsed = mod.extract_financials(text)
        self.assertIsNotNone(parsed)
        self.assertEqual([row["period"] for row in parsed["periods"]], ["FY2026", "FY2025", "FY2024"])
        self.assertAlmostEqual(parsed["periods"][0]["revenueCr"], 125.002, places=3)
        self.assertAlmostEqual(parsed["periods"][1]["patCr"], 9.802, places=3)
        self.assertAlmostEqual(parsed["periods"][2]["netWorthCr"], 42.0, places=2)

    def test_new_financial_heading_alias_is_supported(self):
        text = """
        FINANCIAL INFORMATION OF OUR COMPANY
        (Rs. in million)
        Year ended March 31, 2026
        Year ended March 31, 2025
        Year ended March 31, 2024
        Total Income 945.0 810.0 700.0
        Profit after tax 90.0 74.0 62.0
        Net Worth 410.0 330.0 270.0
        """
        parsed = mod.extract_financials(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["periods"][0]["revenueCr"], 94.5, places=2)
        self.assertAlmostEqual(parsed["periods"][0]["patCr"], 9.0, places=2)

    def test_financial_fallback_rejects_single_narrative_metric(self):
        text = """
        KEY FINANCIAL INFORMATION
        Fiscal 2026 Fiscal 2025 Fiscal 2024
        Revenue from Operations was 100 crore in 2026 compared with 90 crore in
        2025 and 80 crore in 2024. No financial table is presented here.
        """
        parsed = mod.extract_financials(text)
        self.assertIsNone(parsed)

    def test_page_scoring_prefers_real_financial_table_over_toc(self):
        toc = """
        TABLE OF CONTENTS
        Summary of Restated Financial Information ........ 210
        Key Performance Indicators ........................ 58
        """
        table = """
        SUMMARY OF RESTATED FINANCIAL INFORMATION
        Fiscal 2026 Fiscal 2025 Fiscal 2024
        Revenue from Operations 12,500 10,100 8,900
        EBITDA 2,500 2,100 1,700
        Profit after Tax 1,200 980 740
        Net Worth 6,500 5,300 4,200
        """
        self.assertGreater(mod._financial_page_score(table), mod._financial_page_score(toc))

    def test_shareholding_table_without_percent_symbols_uses_header_context(self):
        text = """
        SHAREHOLDING PATTERN
        Category  Pre-Issue Shares  Pre-Issue Percentage  Post-Issue Shares  Post-Issue Percentage
        Promoter and Promoter Group  6,449,280  100.00  6,449,280  73.61
        Public  0  0.00  2,312,000  26.39
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 100.0, places=2)

    def test_shareholding_page_scoring_rejects_plain_toc_reference(self):
        toc = "Capital Structure ................................ 72"
        data = """
        CAPITAL STRUCTURE
        Pre-Issue shareholding of Promoter and Promoter Group
        Promoter and Promoter Group 6,449,280 100.00%
        """
        self.assertGreater(mod._shareholding_page_score(data), mod._shareholding_page_score(toc))


if __name__ == "__main__":
    unittest.main()
