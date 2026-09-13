import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v7.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v7", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OfferDocsV7Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 7)
        self.assertEqual(mod.base.PARSER_VERSION, 7)

    def test_ss_retail_a_b_subtotals_are_combined(self):
        text = """
        Pre-Offer shareholding as at the date of the Red Herring Prospectus
        Post Offer shareholding at Allotment
        Promoter
        1. Siddharth Gunvant Shah 33,608,600 51.03 [●] [●]
        2. Deepa Siddharth Shah 8,740,150 13.27 [●] [●]
        3. Harshal Kishor Parekh 5,559,850 8.44 [●] [●]
        4. Bhavini Harshal Parekh 1,950,000 2.96 [●] [●]
        Sub-total (A) 49,858,600 75.70 [●] [●]
        Promoter Group (Other than our Promoters)
        1. Kishor Ratilal Parekh 25,000 0.04 [●] [●]
        Sub-total (B) 25,000 0.04 [●] [●]
        Additional top 10 Shareholders
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 75.74, places=2)

    def test_jindal_total_a_b_rows_are_combined(self):
        text = """
        Pre-Offer and post-Offer shareholding of our Promoters, members of the Promoter Group
        and top 10 Shareholders
        Promoters
        1. Abhishek Jindal 3,26,15,661 80.97 % [●] [●]
        2. Sonam Jindal 4,28,400 1.06 % [●] [●]
        Total (A) 3,30,44,061 82.03 % [●] [●]
        Promoter Group
        1. VVJ Enterprise Private Limited 36,66,600 9.10 % [●] [●]
        2. Janak Raj Jindal & Sons HUF 35,61,259 8.84 % [●] [●]
        3. Abhishek Jindal HUF 10,500 0.03 % [●] [●]
        Total (B) 72,38,559 17.97 % [●] [●]
        Additional top 10 shareholder NIL
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 100.0, places=2)

    def test_hero_individual_promoter_and_group_rows_are_summed(self):
        text = """
        Pre-Offer shareholding at the date of the Red Herring Prospectus
        Name of the shareholder Number of Equity Shares Shareholding on a fully diluted basis (in %)
        Promoter
        1. O P Munjal Holdings 273,123,055 70.60% [●] [●]
        2. Pankaj Munjal 9,400,436 2.43% [●] [●]
        3. Charu Munjal 942,425 0.24% [●] [●]
        4. Abhishek Munjal 706,210 0.18% [●] [●]
        Promoter Group
        1. Hero Cycles Limited 7,752,750 2.00% [●] [●]
        2. Aditya Munjal 707,022 0.18% [●] [●]
        3. Bhagyoday Investments Private Limited 23,978,804 6.20% [●] [●]
        4. Pankaj Munjal on behalf of Munjal Sales Corporation 392,344 0.10% [●] [●]
        5. Pankaj Munjal on behalf of AOP 10,537,140 2.72% [●] [●]
        Additional top 10 Shareholders
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 84.65, places=2)

    def test_tempsens_individual_rows_ignore_negligible_group_holdings(self):
        text = """
        Pre-Offer and Post-Offer shareholding of our Promoters, members of the Promoter Group
        and the additional top 10 Shareholders
        Promoters
        1. Vinay Rathi 24,196,970 30.00 [●] [●]
        2. Virendra Prakash Rathi 12,502,750 15.50 [●] [●]
        3. Pratap Singh Talesara 508,475 0.63 [●] [●]
        Promoter Group
        1. Rathi Family Trust 7,663,280 9.50 [●] [●]
        2. Amit Talesara 6,852,756 8.50 [●] [●]
        3. Chandra Prakash Talesara 6,850,940 8.49 [●] [●]
        4. Puneet Talesara 6,369,298 7.90 [●] [●]
        5. Sonal Rathi 1,650 Negligible [●] [●]
        6. Aryan Rathi 1,100 Negligible [●] [●]
        7. Tanya Rathi 275 Negligible [●] [●]
        Additional top 10 shareholders
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 80.52, places=2)

    def test_shareholding_pattern_a_row_is_used_for_combined_ownership(self):
        text = """
        Shareholding Pattern of our Company
        Category (I) Category of Shareholder (II) Total number of Equity Shares held
        (A) Promoter and Promoter Group 9 52,071,136 - - 52,071,136 61.53%
        52,071,136 - 52,071,136 61.53 %
        (B) Public 12 32,567,414 38.47%
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 61.53, places=2)

    def test_combined_row_outranks_promoter_only_narrative(self):
        text = """
        OUR PROMOTERS AND PROMOTER GROUP
        As on the date of this Prospectus, our Promoters collectively hold 42,046,063 Equity Shares,
        representing 49.68% of the pre-Offer issued share capital of our Company.
        Shareholding Pattern of our Company
        (A) Promoter and Promoter Group 9 52,071,136 61.53%
        (B) Public 12 32,567,414 38.47%
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 61.53, places=2)

    def test_combined_as_of_prospectus_narrative_is_supported(self):
        text = """
        For details of their shareholding pre and post-Offer, see Capital Structure.
        As on the date of this Prospectus, our Promoters along with members of our Promoter Group
        collectively held 61.53% of the share capital of our Company on a fully diluted basis.
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 61.53, places=2)

    def test_promoter_contribution_lock_in_remains_rejected(self):
        text = """
        CAPITAL STRUCTURE
        Pre-Offer paid-up share capital consists of 10,000,000 Equity Shares.
        Promoters Contribution 20% of the post-Offer capital shall be locked in.
        """
        self.assertIsNone(mod.extract_promoter_shareholding(text))


if __name__ == "__main__":
    unittest.main()
