import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_recent_offer_terms.py"
spec = importlib.util.spec_from_file_location("enrich_recent_offer_terms", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class RecentOfferTermsTests(unittest.TestCase):
    def test_minimum_bid_lot_wording(self):
        text = "The minimum Bid Lot is 84 Equity Shares and in multiples of 84 Equity Shares thereafter."
        self.assertEqual(mod.extract_lot_size(text), 84)

    def test_bid_minimum_wording(self):
        text = "Bids can be made for a minimum of 151 Equity Shares and in multiples of 151 Equity Shares thereafter."
        self.assertEqual(mod.extract_lot_size(text), 151)

    def test_real_prospectus_glossary_bid_lot_row(self):
        text = "Bid Lot 151 Equity Shares of face value ₹ 10 each and in multiples of 151 Equity Shares of face value ₹ 10 each thereafter."
        self.assertEqual(mod.extract_lot_size(text), 151)

    def test_rhp_placeholder_lot_is_not_invented(self):
        text = "Bid Lot [●] Equity Shares and in multiples of [●] Equity Shares thereafter."
        self.assertIsNone(mod.extract_lot_size(text))

    def test_minimum_application_size_wording(self):
        text = "The minimum application size shall be 2,000 Equity Shares and thereafter in multiples of 2,000 Equity Shares."
        self.assertEqual(mod.extract_lot_size(text), 2000)

    def test_generic_issue_share_count_is_not_a_lot(self):
        text = "The Offer comprises 12,345,678 Equity Shares aggregating to the Issue size."
        self.assertIsNone(mod.extract_lot_size(text))

    def test_anchor_investor_bid_lot_fallback_is_rejected(self):
        text = "For Anchor Investor allocation, the Bid Lot shall comprise 10,000 Equity Shares."
        self.assertIsNone(mod.extract_lot_size(text))

    def test_choose_full_prospectus_over_abridged_rhp(self):
        record = {
            "documents": [
                {
                    "type": "RHP",
                    "title": "Example - Abridged Prospectus",
                    "url": "https://www.sebi.gov.in/sebi_data/commondocs/sep-2026/example-ap_p.pdf",
                    "filedDate": "2026-09-01",
                },
                {
                    "type": "RHP",
                    "title": "SEBI RHP",
                    "url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/example-rhp.pdf",
                    "filedDate": "2026-09-01",
                },
                {
                    "type": "PROSPECTUS",
                    "title": "SEBI Prospectus",
                    "url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/example-prospectus.pdf",
                    "filedDate": "2026-09-05",
                },
            ]
        }
        chosen = mod.choose_full_document(record)
        self.assertIn("example-prospectus.pdf", chosen["url"])

    def test_lot_only_requires_final_prospectus(self):
        gaps = {"exchange.lotSize"}
        rhp = {"type": "RHP"}
        prospectus = {"type": "PROSPECTUS"}
        self.assertFalse(mod.should_attempt_document(gaps, rhp))
        self.assertTrue(mod.should_attempt_document(gaps, prospectus))
        self.assertTrue(mod.should_attempt_document({"exchange.lotSize", "exchange.issueComposition"}, rhp))

    def test_supplemental_document_is_not_selected(self):
        record = {
            "documents": [
                {
                    "type": "ADDENDUM",
                    "title": "Addendum to RHP",
                    "url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/addendum.pdf",
                }
            ]
        }
        self.assertIsNone(mod.choose_full_document(record))

    def test_merge_is_fill_only_for_lot_and_issue_terms(self):
        record = {
            "lotSize": 50,
            "issueSizeCr": 100.0,
            "issueComposition": {"freshIssueCr": 100.0, "ofsCr": 0.0},
            "priceBand": {"min": 100, "max": 110},
            "sources": [],
            "observations": {},
        }
        doc = {
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/example.pdf",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/sep-2026/example.html",
        }
        text = "The minimum Bid Lot is 84 Equity Shares and in multiples of 84 Equity Shares thereafter."
        changed = mod.merge_terms(record, text, doc)
        self.assertEqual(record["lotSize"], 50)
        self.assertEqual(record["issueSizeCr"], 100.0)
        self.assertNotIn("lotSize", changed)


if __name__ == "__main__":
    unittest.main()
