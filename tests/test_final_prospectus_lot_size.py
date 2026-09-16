import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_parser as parser


class FinalProspectusLotSizeTests(unittest.TestCase):
    @staticmethod
    def pages(*entries):
        return "\f".join(f"[PAGE {page}]\n{text}" for page, text in entries)

    def test_explicit_bid_lot_beyond_front_matter_is_recovered_with_evidence(self):
        text = self.pages(
            *[(page, "general prospectus text") for page in range(1, 31)],
            (31, "Minimum Bid Lot shall be 160 Equity Shares."),
        )

        lot, evidence = parser.extract_final_lot_size(text)
        parsed = parser.parse_document_text(text)

        self.assertEqual(lot, 160)
        self.assertEqual(evidence["lotSize"]["page"], 31)
        self.assertEqual(evidence["lotSize"]["value"], 160)
        self.assertIn("explicit Bid Lot", evidence["lotSize"]["basis"])
        self.assertEqual(parsed["lotSize"], 160)
        self.assertEqual(parsed["fieldEvidence"]["lotSize"]["page"], 31)
        self.assertIn("lotSize", parsed["extractedFields"])

    def test_generic_minimum_equity_quantity_is_not_a_lot(self):
        text = self.pages(
            (44, "The Offer comprises a minimum of 10,000 Equity Shares for allocation purposes."),
        )
        self.assertEqual(parser.extract_final_lot_size(text), (None, {}))

    def test_minimum_bid_quantity_without_bid_lot_is_not_a_lot(self):
        text = self.pages(
            (52, "Minimum Bid Quantity is 2,000 Equity Shares and bids may be made in multiples thereafter."),
        )
        self.assertEqual(parser.extract_final_lot_size(text), (None, {}))

    def test_conflicting_explicit_bid_lots_fail_closed(self):
        text = self.pages(
            (21, "Minimum Bid Lot is 160 Equity Shares."),
            (89, "Bid Lot means 320 Equity Shares."),
        )
        self.assertEqual(parser.extract_final_lot_size(text), (None, {}))

    def test_repeated_same_explicit_bid_lot_is_unambiguous(self):
        text = self.pages(
            (5, "The Bid Lot for the Offer is 283 Equity Shares."),
            (205, "Bid Lot means 283 Equity Shares."),
        )
        lot, evidence = parser.extract_final_lot_size(text)
        self.assertEqual(lot, 283)
        self.assertEqual(evidence["lotSize"]["value"], 283)

    def test_parser_version_bumped_for_deep_lot_revalidation(self):
        self.assertGreaterEqual(parser.PARSER_VERSION, parser.base.PARSER_VERSION + 3)


if __name__ == "__main__":
    unittest.main()
