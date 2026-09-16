import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import p4_offer_layouts as parser


GANESH_WITH_EXPLICIT_TOTAL = """
Aggregate Pre-Issue shareholding of our Promoters and Promoter Group
As on date of this Prospectus, the aggregate Pre-Issue shareholding of our Promoters and Promoter
Group, as a percentage of the Pre-Issue paid-up Equity Share capital of our Company is set out below:
Sr. No. Name of Shareholder Number of Equity Shares Percentage of the Pre-Issue Equity Share Capital (%)
Promoters
1. Vibhoar Agrawal 1,37,22,312 44.49
2. Rachita Agrawal 1,15,22,285 37.36
Promoter Group
Nil
Total 2,52,44,597 81.8421
"""

GANESH_WITHOUT_TOTAL = """
Aggregate Pre-Issue shareholding of our Promoters and Promoter Group
Name of shareholder No. of Equity Shares Percentage
Vibhoar Agrawal 31,544,000 44.49
Rachita Agrawal 26,488,000 37.36
Promoter Group Nil Nil
"""


class P4PromoterShareholdingTotalTests(unittest.TestCase):
    def test_explicit_total_row_is_preferred_over_component_sum(self):
        shareholding, evidence = parser.extract_promoter_shareholding(GANESH_WITH_EXPLICIT_TOTAL)
        self.assertEqual(shareholding["promoterPreIssuePct"], 81.8421)
        self.assertEqual(
            evidence["shareholding"]["basis"],
            "explicit aggregate pre-issue promoter Total row",
        )

    def test_component_sum_remains_fallback_when_total_is_absent(self):
        shareholding, evidence = parser.extract_promoter_shareholding(GANESH_WITHOUT_TOTAL)
        self.assertEqual(shareholding["promoterPreIssuePct"], 81.85)
        self.assertEqual(evidence["shareholding"]["basis"], "aggregate pre-issue promoter table")


if __name__ == "__main__":
    unittest.main()
