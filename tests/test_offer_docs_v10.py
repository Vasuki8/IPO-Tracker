import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v10.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v10", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OfferDocsV10Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 10)

    def test_explicit_total_a_plus_b_pre_offer_row_is_parsed(self):
        text = """
        Details of shareholding of our Promoters and members of the Promoter Group
        Name of the Shareholder Pre-Offer Post-Offer
        Promoters
        Total (A) 93,74,976 72.68% [●] [●]
        Promoter Group
        Total (B) 19,35,928 15.00% [●] [●]
        Total (A+B) 1,13,10,904 87.68% [●] [●]
        """
        self.assertEqual(
            mod.extract_promoter_shareholding(text),
            {"promoters": [], "promoterPreIssuePct": 87.68},
        )

    def test_total_a_plus_b_without_pre_offer_context_is_rejected(self):
        text = """
        Promoters and Promoter Group
        Total (A+B) 1,13,10,904 87.68%
        Minimum Promoters' Contribution 20% of post-Offer capital.
        """
        self.assertIsNone(mod._explicit_ab_total(text))

    def test_promoter_contribution_is_not_used_as_combined_ownership(self):
        text = """
        Pre-Offer capital structure
        Promoters and Promoter Group
        Minimum Promoters' Contribution 20% of post-Offer capital.
        """
        self.assertIsNone(mod._explicit_ab_total(text))


if __name__ == "__main__":
    unittest.main()
