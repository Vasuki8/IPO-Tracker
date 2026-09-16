"""Regressions from bounded, issuer-specific Final Prospectus excerpts."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_parser as parser

FIXTURES = ROOT / "tests" / "fixtures" / "issue_composition"


class FinalCompositionSourceLayoutTests(unittest.TestCase):
    def source(self, issuer):
        return (FIXTURES / (issuer + "-final-offer.txt")).read_text()

    def test_actual_final_offer_clauses_keep_each_component_with_its_amount(self):
        expected = {
            "annu": (17_683_000, 0, 175.062, 0.0, 175.062, 99.0, 2),
            "arcil": (0, 52_731_946, 0.0, 732.974, 732.974, 139.0, 3),
            "mpimanipal": (9_439_528, 14_306_785, 320.0, 485.0, 805.0, 339.0, 3),
            "skyways": (28_898_300, 13_333_300, 398.7965, 183.9995, 582.796, 138.0, 2),
        }
        fields = ("freshShares", "ofsShares", "freshIssueCr", "ofsCr", "totalIssueSizeCr", "valuationPriceUsed")
        for issuer, values in expected.items():
            with self.subTest(issuer=issuer):
                composition, evidence = parser.extract_final_issue_composition(self.source(issuer))
                self.assertEqual(composition, dict(zip(fields, values[:6])))
                proof = evidence["issueComposition"]
                self.assertEqual(proof["method"], "bounded-final-offer-clauses-v1")
                self.assertEqual(proof["page"], values[6])
                for field in fields[:5]:
                    self.assertEqual(proof["fields"][field]["normalizedValue"], composition[field])
                    self.assertEqual(proof["fields"][field]["page"], values[6])
                    self.assertTrue(proof["fields"][field]["row"])

    def test_individual_sellers_are_not_the_total_offer_for_sale(self):
        composition, evidence = parser.extract_final_issue_composition(self.source("arcil"))
        self.assertNotEqual(composition["ofsShares"], 24_823_910)
        self.assertIn("52,731,946", evidence["issueComposition"]["fields"]["ofsShares"]["row"])
        self.assertNotIn("24,823,910", evidence["issueComposition"]["fields"]["ofsShares"]["row"])

    def test_historical_pre_ipo_placement_does_not_replace_final_fresh_issue(self):
        composition, _ = parser.extract_final_issue_composition(self.source("skyways"))
        self.assertEqual(composition["freshShares"], 28_898_300)
        self.assertNotEqual(composition["freshShares"], 32_917_700)
        self.assertEqual(composition["valuationPriceUsed"], 138.0)

    def test_price_band_definitions_are_not_conflicting_final_issue_prices(self):
        value, evidence = parser.extract_final_issue_price(self.source("mpimanipal"))
        self.assertEqual(value, 339.0)
        self.assertEqual(evidence["issuePrice"]["page"], 3)

    def test_conflicting_explicit_final_prices_still_fail_closed(self):
        text = "OFFER PRICE IS ₹339 PER EQUITY SHARE\fISSUE PRICE: ₹322 PER EQUITY SHARE"
        self.assertEqual(parser.extract_final_issue_price(text), (None, {}))

    def test_price_band_cap_cannot_value_final_share_counts(self):
        text = """
        PROSPECTUS
        Price Band ₹100 to ₹125 per Equity Share
        DETAILS OF THE ISSUE
        Fresh Issue of 8,000,000 Equity Shares
        Offer for Sale of 2,000,000 Equity Shares
        """
        composition, _ = parser.extract_final_issue_composition(text, {"min": 100, "max": 125})
        self.assertEqual(composition, {"freshShares": 8_000_000, "ofsShares": 2_000_000})

    def test_unvalued_component_cannot_take_the_next_component_amount(self):
        text = """
        PROSPECTUS
        DETAILS OF THE ISSUE
        Fresh Issue of 8,000,000 Equity Shares
        Offer for Sale of 2,000,000 Equity Shares aggregating to ₹25 crore
        """
        composition, _ = parser.extract_final_issue_composition(text)
        self.assertNotIn("freshIssueCr", composition)
        self.assertEqual(composition["ofsCr"], 25.0)
        self.assertNotIn("totalIssueSizeCr", composition)

    def test_unvalued_component_cannot_take_an_unrelated_sentence_amount(self):
        text = """
        DETAILS OF THE ISSUE
        Fresh Issue of 8,000,000 Equity Shares. Expenditure aggregating to ₹25 crore.
        """
        composition, _ = parser.extract_final_issue_composition(text)
        self.assertEqual(composition, {"freshShares": 8_000_000})

    def test_unrecognized_cover_table_does_not_flatten_adjacent_columns(self):
        text = """
        DETAILS OF THE ISSUE
        Fresh Issue              Offer for Sale
        8,000,000 Equity Shares   2,000,000 Equity Shares
        aggregating to ₹100 crore aggregating to ₹25 crore
        """
        self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_absent_component_is_not_zero_without_complete_offer_evidence(self):
        text = "DETAILS OF THE ISSUE\nFresh Issue of 8,000,000 Equity Shares aggregating to ₹100 crore"
        composition, _ = parser.extract_final_issue_composition(text)
        self.assertNotIn("ofsShares", composition)
        self.assertNotIn("ofsCr", composition)
        self.assertNotIn("totalIssueSizeCr", composition)

    def test_conflicting_final_component_clauses_fail_closed(self):
        text = """
        DETAILS OF THE ISSUE
        Fresh Issue of 8,000,000 Equity Shares aggregating to ₹100 crore
        Fresh Issue of 9,000,000 Equity Shares aggregating to ₹100 crore
        """
        self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_total_share_count_must_match_the_components(self):
        text = """
        INITIAL PUBLIC OFFER OF 10,000,000 EQUITY SHARES AGGREGATING TO ₹100 CRORE
        COMPRISING A FRESH ISSUE OF 8,000,000 EQUITY SHARES AGGREGATING TO ₹80 CRORE
        AND AN OFFER FOR SALE OF 3,000,000 EQUITY SHARES AGGREGATING TO ₹20 CRORE
        """
        self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_rejected_strict_extraction_cannot_keep_legacy_composition(self):
        legacy_result = {
            "issueComposition": {"freshIssueCr": 999},
            "extractedFields": ["issueComposition"],
            "fieldEvidence": {"issueComposition": {"basis": "legacy"}},
        }
        with patch.object(parser.base, "parse_document_text", return_value=legacy_result):
            parsed = parser.parse_document_text("PROSPECTUS\nNo supported offer composition clause")
        self.assertNotIn("issueComposition", parsed)
        self.assertNotIn("issueComposition", parsed["extractedFields"])
        self.assertNotIn("issueComposition", parsed["fieldEvidence"])


if __name__ == "__main__":
    unittest.main()
