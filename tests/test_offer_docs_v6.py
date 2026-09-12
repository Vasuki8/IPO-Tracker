import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v6.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v6", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OfferDocsV6Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 6)
        self.assertEqual(mod.base.PARSER_VERSION, 6)

    def test_aggregate_promoter_narrative_is_parsed(self):
        text = """
        E. PRE-ISSUE SHAREHOLDING OF PROMOTERS AND PROMOTER GROUP
        Our Promoters and Promoter Group collectively holds 50,09,040 Equity shares
        of our Company aggregating to 77.67% of the pre-Issue paid-up Share Capital
        of our Company.
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 77.67, places=2)

    def test_grand_total_percentage_without_percent_sign_is_parsed(self):
        text = """
        PRE-ISSUE SHAREHOLDING OF PROMOTERS AND PROMOTER GROUP
        Sr. No Names Pre IPO Post IPO
        Shares Held % Shares Held Shares Held % Shares Held
        Promoters
        1 Shashi Kumar Chaudhary 47,57,120 73.76 [●] [●]
        2 Seema Chaudhary 2,51,920 3.91 [●] [●]
        Promoter Group
        3 Sangita Dokania 11,20,000 17.37 [●] [●]
        Grand Total (A+B) 64,49,280 100.00 [●] [●]
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 100.0, places=2)

    def test_direct_promoter_holding_pre_issue_is_parsed(self):
        text = """
        SHAREHOLDING PATTERN
        Promoter Holding Pre Issue 89.20%
        Promoter Holding Post Issue 77.51%
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 89.2, places=2)

    def test_promoter_contribution_is_still_rejected(self):
        text = """
        CAPITAL STRUCTURE
        Pre-Issue paid-up capital consists of 10,000,000 Equity Shares.
        Promoters Contribution 20% of the post-Issue capital shall be locked in.
        """
        self.assertIsNone(mod.extract_promoter_shareholding(text))

    def test_ranked_windows_prefer_numeric_shareholding_table(self):
        toc = "PRE-ISSUE SHAREHOLDING OF PROMOTERS AND PROMOTER GROUP ........ 72"
        table = """
        PRE-ISSUE SHAREHOLDING OF PROMOTERS AND PROMOTER GROUP
        Promoters and Promoter Group 6,449,280 100.00 6,449,280 73.61
        Grand Total 6,449,280 100.00
        """
        self.assertGreater(mod._shareholding_score(table), mod._shareholding_score(toc))

    def test_pat_alias_profit_loss_after_tax_is_supported_and_merged(self):
        text = """
        SUMMARY OF FINANCIAL INFORMATION
        (₹ in million)
        Fiscal 2026 Fiscal 2025 Fiscal 2024
        Revenue from operations 3,869.88 2,659.59 1,927.01
        Profit / (Loss) After Tax 1,042.99 431.06 224.12
        Net Worth 2,958.10 1,836.10 1,396.10
        """
        parsed = mod.extract_financials(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["periods"][0]["revenueCr"], 386.988, places=3)
        self.assertAlmostEqual(parsed["periods"][0]["patCr"], 104.299, places=3)
        self.assertAlmostEqual(parsed["periods"][0]["netWorthCr"], 295.81, places=2)


if __name__ == "__main__":
    unittest.main()
