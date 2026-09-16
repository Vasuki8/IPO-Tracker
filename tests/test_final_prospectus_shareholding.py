import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_parser as parser


class FinalProspectusShareholdingTests(unittest.TestCase):
    @staticmethod
    def pages(*entries):
        return "\f".join(f"[PAGE {page}]\n{text}" for page, text in entries)

    def test_deep_pre_offer_promoter_total_is_recovered_with_evidence(self):
        text = self.pages(
            *[(page, "general prospectus text") for page in range(1, 70)],
            (
                70,
                "PRE-OFFER SHAREHOLDING OF OUR COMPANY\n"
                "(A) Promoters\n(B) Promoter Group\n"
                "Total (A + B) 1,000,000 72.50",
            ),
        )

        shareholding, evidence = parser.extract_final_promoter_shareholding(text)
        parsed = parser.parse_document_text(text)

        self.assertEqual(shareholding["promoterPreIssuePct"], 72.5)
        self.assertEqual(evidence["shareholding"]["page"], 70)
        self.assertEqual(evidence["shareholding"]["promoterPreIssuePct"], 72.5)
        self.assertEqual(parsed["shareholding"]["promoterPreIssuePct"], 72.5)
        self.assertEqual(parsed["fieldEvidence"]["shareholding"]["page"], 70)
        self.assertIn("shareholding", parsed["extractedFields"])

    def test_post_offer_table_without_pre_offer_context_is_rejected(self):
        text = self.pages(
            (
                88,
                "POST-OFFER SHAREHOLDING OF OUR COMPANY\n"
                "Promoters and Promoter Group\nTotal (A + B) 1,000,000 42.00",
            ),
        )
        self.assertEqual(parser.extract_final_promoter_shareholding(text), (None, {}))

    def test_minimum_promoter_contribution_table_is_not_ownership(self):
        text = self.pages(
            (
                102,
                "PRE-OFFER SHAREHOLDING\nPromoters and Promoter Group\n"
                "Minimum Promoters' Contribution\nTotal (A + B) 1,000,000 20.00",
            ),
        )
        self.assertEqual(parser.extract_final_promoter_shareholding(text), (None, {}))

    def test_conflicting_deep_promoter_totals_fail_closed(self):
        text = self.pages(
            (
                60,
                "PRE-OFFER SHAREHOLDING\nPromoters\nPromoter Group\n"
                "Total (A + B) 1,000,000 72.50",
            ),
            *[(page, "general text") for page in range(61, 100)],
            (
                100,
                "PRE-ISSUE SHAREHOLDING\nPromoters\nPromoter Group\n"
                "Total (A + B) 1,000,000 60.00",
            ),
        )
        self.assertEqual(parser.extract_final_promoter_shareholding(text), (None, {}))

    def test_repeated_same_total_is_unambiguous(self):
        text = self.pages(
            (
                50,
                "PRE-OFFER SHAREHOLDING\nPromoters\nPromoter Group\n"
                "Total (A + B) 1,000,000 81.25",
            ),
            *[(page, "general text") for page in range(51, 90)],
            (
                90,
                "PRE-ISSUE SHAREHOLDING\nPromoters\nPromoter Group\n"
                "Total (A + B) 1,000,000 81.25",
            ),
        )
        shareholding, _ = parser.extract_final_promoter_shareholding(text)
        self.assertEqual(shareholding["promoterPreIssuePct"], 81.25)

    def test_parser_version_bumped_for_deep_shareholding_revalidation(self):
        self.assertGreaterEqual(parser.PARSER_VERSION, parser.base.PARSER_VERSION + 4)


if __name__ == "__main__":
    unittest.main()
