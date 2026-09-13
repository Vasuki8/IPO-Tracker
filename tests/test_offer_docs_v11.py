import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v11.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v11", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OfferDocsV11Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 11)

    def test_injecto_combined_promoter_group_row_is_parsed(self):
        text = """
        Shareholding, as a % assuming full conversion of convertible securities
        No. of Equity Shares held in dematerialized form
        Number of Voting Rights Total as a % of (A+B+C)
        Total (A) Promoter and Promoter Group 15 1,33,77,200 - -
        1,33,77,200 88.14 13377200 - 13377200 88.14 - 88.14
        (B) Public 44 18,00,000 - - 18,00,000 11.86
        """
        self.assertEqual(
            mod.extract_promoter_shareholding(text),
            {"promoters": [], "promoterPreIssuePct": 88.14},
        )

    def test_injecto_shareholder_count_is_not_mistaken_for_pct(self):
        text = """
        Pre-Issue Shareholding
        Promoter Group
        Total (A) Promoter and Promoter Group 15 1,33,77,200 88.14
        """
        self.assertIsNone(mod._explicit_combined_ownership(text))

    def test_injecto_requires_following_public_row(self):
        text = """
        Shareholding Pattern
        Number of Voting Rights Total as a % of (A+B+C)
        Total (A) Promoter and Promoter Group 15 1,33,77,200 - -
        1,33,77,200 88.14
        """
        self.assertIsNone(mod._explicit_combined_ownership(text))

    def test_manika_total_c_a_plus_b_row_is_parsed(self):
        text = """
        Equity Shareholding of the Promoters and Promoter Group
        As on the date of this Red Herring Prospectus
        Sr. No. Name of the Shareholders Pre-Offer Post-Offer
        Promoters
        Total - A 94,287,500 99.25 [●] [●]
        Promoter Group
        Total - B 712,500 0.75 [●] [●]
        Total – C (A+B) 95,000,000 100.00 [●] [●]
        """
        self.assertEqual(
            mod.extract_promoter_shareholding(text),
            {"promoters": [], "promoterPreIssuePct": 100.0},
        )

    def test_combined_rows_without_pre_offer_context_are_rejected(self):
        text = """
        Promoter Group
        Total – C (A+B) 95,000,000 100.00
        Total (A) Promoter and Promoter Group 15 1,33,77,200 88.14
        """
        self.assertIsNone(mod._explicit_combined_ownership(text))

    def test_promoter_contribution_does_not_trigger_v11(self):
        text = """
        Pre-Offer capital
        Promoter Group
        Minimum Promoters' Contribution 20% of post-Offer capital.
        """
        self.assertIsNone(mod._explicit_combined_ownership(text))


if __name__ == "__main__":
    unittest.main()
