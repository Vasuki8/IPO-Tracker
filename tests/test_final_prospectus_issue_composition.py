import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_parser as parser
import final_prospectus_policy as policy


class FinalProspectusIssueCompositionTests(unittest.TestCase):
    def test_final_prospectus_extracts_fresh_ofs_and_total_issue_size(self):
        text = """
        PROSPECTUS
        OFFER PRICE: ₹ 100 PER EQUITY SHARE
        DETAILS OF THE ISSUE
        Fresh Issue of 10,000,000 Equity Shares aggregating to ₹ 100 crore
        Offer for Sale of 5,000,000 Equity Shares aggregating to ₹ 50 crore
        Total Issue Size aggregating to ₹ 150 crore
        RISKS IN RELATION TO THE FIRST OFFER
        """
        parsed = parser.parse_document_text(text)
        composition = parsed.get("issueComposition")
        self.assertIsNotNone(composition)
        self.assertEqual(composition["freshShares"], 10_000_000)
        self.assertEqual(composition["ofsShares"], 5_000_000)
        self.assertEqual(composition["freshIssueCr"], 100.0)
        self.assertEqual(composition["ofsCr"], 50.0)
        self.assertEqual(composition["totalIssueSizeCr"], 150.0)
        self.assertIn("issueComposition", parsed["extractedFields"])

    def test_final_fixed_price_can_value_explicit_share_counts(self):
        text = """
        PROSPECTUS
        ISSUE PRICE: ₹ 125 PER EQUITY SHARE
        DETAILS OF THE ISSUE
        Fresh Issue of 8,000,000 Equity Shares
        Offer for Sale of 2,000,000 Equity Shares
        RISKS IN RELATION TO THE FIRST OFFER
        """
        parsed = parser.parse_document_text(text)
        composition = parsed.get("issueComposition")
        self.assertIsNotNone(composition)
        self.assertEqual(parsed["issuePrice"], 125.0)
        self.assertNotIn("priceBand", parsed)
        self.assertNotIn("priceBand", parsed["extractedFields"])
        self.assertEqual(composition["freshIssueCr"], 100.0)
        self.assertEqual(composition["ofsCr"], 25.0)
        self.assertEqual(composition["totalIssueSizeCr"], 125.0)

    def test_explicit_price_band_is_kept_separate_from_final_issue_price(self):
        text = """
        PROSPECTUS
        The Price Band was ₹ 120 to ₹ 125 per Equity Share.
        OFFER PRICE: ₹ 125 PER EQUITY SHARE
        DETAILS OF THE ISSUE
        Fresh Issue of 8,000,000 Equity Shares
        RISKS IN RELATION TO THE FIRST OFFER
        """
        parsed = parser.parse_document_text(text)
        self.assertEqual(parsed["issuePrice"], 125.0)
        self.assertEqual(parsed["priceBand"], {"min": 120.0, "max": 125.0})
        self.assertIn("priceBand", parsed["extractedFields"])

    def test_conflicting_total_fails_closed(self):
        self.assertIsNone(
            parser.validate_issue_composition(
                {
                    "freshIssueCr": 100.0,
                    "ofsCr": 50.0,
                    "totalIssueSizeCr": 200.0,
                    "freshShares": 10_000_000,
                    "ofsShares": 5_000_000,
                }
            )
        )

    def test_policy_promotes_validated_composition_to_canonical_amounts(self):
        record = {
            "id": "example",
            "openDate": "2026-09-01",
            "issueSizeCr": 999.0,
            "freshIssueCr": 999.0,
            "ofsCr": 0.0,
        }
        doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://www.sebi.gov.in/files/final.pdf",
            "filedDate": "2026-09-10",
        }
        composition = {
            "freshShares": 10_000_000,
            "ofsShares": 5_000_000,
            "freshIssueCr": 100.0,
            "ofsCr": 50.0,
            "totalIssueSizeCr": 150.0,
        }
        policy.apply_final_prospectus_static_fields(
            record,
            {"issueComposition": composition},
            doc,
            sha256="abc",
            parser_version=parser.PARSER_VERSION,
            checked_at="2026-09-16T00:00:00Z",
        )
        self.assertEqual(record["issueSizeCr"], 150.0)
        self.assertEqual(record["freshIssueCr"], 100.0)
        self.assertEqual(record["ofsCr"], 50.0)
        for field in ("issueComposition", "issueSizeCr", "freshIssueCr", "ofsCr"):
            self.assertEqual(
                record["staticFieldProvenance"][field]["documentType"],
                "PROSPECTUS",
            )


if __name__ == "__main__":
    unittest.main()
