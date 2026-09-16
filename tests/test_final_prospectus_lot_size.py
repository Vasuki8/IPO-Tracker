import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_parser as parser
import final_prospectus_policy as policy


class FinalProspectusLotSizeTests(unittest.TestCase):
    def test_accepts_minimum_bid_lot_without_equity_word(self):
        text = """
        PROSPECTUS
        Minimum Bid Lot: 46 Shares and in multiples of 46 Shares thereafter.
        """
        parsed = parser.parse_document_text(text)
        self.assertEqual(parsed["lotSize"], 46)
        self.assertIn("lotSize", parsed["extractedFields"])
        self.assertEqual(parsed["fieldEvidence"]["lotSize"]["value"], 46)

    def test_scans_lot_term_beyond_front_twenty_pages(self):
        pages = [f"PROSPECTUS boilerplate page {index}" for index in range(1, 26)]
        pages.append("Bid Lot Size is 75 Equity Shares and in multiples of 75 thereafter.")
        parsed = parser.parse_document_text("\f".join(pages))
        self.assertEqual(parsed["lotSize"], 75)
        self.assertEqual(parsed["fieldEvidence"]["lotSize"]["page"], 26)

    def test_conflicting_explicit_lot_sizes_fail_closed(self):
        text = """
        Minimum Bid Lot: 30 Shares.
        \f
        Market Lot: 60 Equity Shares.
        """
        parsed = parser.parse_document_text(text)
        self.assertNotIn("lotSize", parsed)
        self.assertNotIn("lotSize", parsed["extractedFields"])
        self.assertEqual(
            parsed["fieldEvidence"]["lotSizeConflict"]["values"],
            [30, 60],
        )

    def test_policy_promotes_lot_with_final_prospectus_evidence(self):
        record = {
            "id": "example-lot",
            "openDate": "2026-09-01",
            "lotSize": 25,
        }
        doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://www.sebi.gov.in/files/final-lot.pdf",
            "filedDate": "2026-09-10",
        }
        parsed = parser.parse_document_text(
            "PROSPECTUS\nMinimum Application Size: 50 Shares."
        )
        policy.apply_final_prospectus_static_fields(
            record,
            parsed,
            doc,
            sha256="abc",
            parser_version=parser.PARSER_VERSION,
            checked_at="2026-09-16T00:00:00Z",
        )
        self.assertEqual(record["lotSize"], 50)
        self.assertEqual(
            record["staticFieldProvenance"]["lotSize"]["documentType"],
            "PROSPECTUS",
        )
        self.assertNotIn(
            "lotSize",
            record["staticSourcePolicy"]["pendingRevalidationFields"],
        )


if __name__ == "__main__":
    unittest.main()
