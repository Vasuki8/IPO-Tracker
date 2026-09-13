import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v12.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v12", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OfferDocsV12Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 12)

    def test_minimum_bid_lot_is_extracted(self):
        text = "The Minimum Bid Lot is 125 Equity Shares and in multiples of 125 Equity Shares thereafter."
        self.assertEqual(mod.extract_lot_size(text), 125)

    def test_minimum_bid_sentence_is_extracted(self):
        text = "Bids can be made for a minimum of 1,200 Equity Shares and in multiples of 1,200 Equity Shares thereafter."
        self.assertEqual(mod.extract_lot_size(text), 1200)

    def test_minimum_quantity_with_label_after_value_is_extracted(self):
        text = "A minimum of 2,000 Equity Shares (the Minimum Bid Lot) must be applied for."
        self.assertEqual(mod.extract_lot_size(text), 2000)

    def test_generic_minimum_equity_quantity_is_not_a_lot(self):
        text = "The Promoters shall contribute a minimum of 2,000 Equity Shares before the Offer."
        self.assertIsNone(mod.extract_lot_size(text))

    def test_price_band_is_extracted(self):
        text = "The Price Band is ₹ 94 to ₹ 99 per Equity Share."
        self.assertEqual(mod.extract_price_band(text), {"min": 94.0, "max": 99.0})

    def test_floor_and_cap_price_are_extracted(self):
        text = "The Floor Price is ₹ 100 and the Cap Price is ₹ 110 per Equity Share."
        self.assertEqual(mod.extract_price_band(text), {"min": 100.0, "max": 110.0})

    def test_fixed_issue_price_is_extracted(self):
        text = "Issue Price: ₹ 70 per Equity Share."
        self.assertEqual(mod.extract_price_band(text), {"min": 70.0, "max": 70.0})

    def test_face_value_and_discount_are_not_price_band(self):
        text = "Face Value ₹ 10 per Equity Share. Employee Discount ₹ 5 per Equity Share."
        self.assertIsNone(mod.extract_price_band(text))

    def test_parse_document_text_exposes_offer_terms(self):
        parsed = mod.parse_document_text(
            "Price Band: ₹ 140 - ₹ 147 per Equity Share. Minimum Bid Lot: 100 Equity Shares."
        )
        self.assertEqual(parsed["lotSize"], 100)
        self.assertEqual(parsed["priceBand"], {"min": 140.0, "max": 147.0})
        self.assertIn("lotSize", parsed["extractedFields"])
        self.assertIn("priceBand", parsed["extractedFields"])

    def test_apply_is_fill_only_and_keeps_document_observation(self):
        record = {
            "lotSize": 75,
            "priceBand": None,
            "observations": {},
        }
        parsed = {
            "leadManagers": [],
            "registrar": None,
            "promoters": [],
            "issueComposition": {},
            "financials": None,
            "objectsOfIssue": [],
            "shareholding": None,
            "lotSize": 100,
            "priceBand": {"min": 94.0, "max": 99.0},
            "extractedFields": ["lotSize", "priceBand"],
        }
        doc = {
            "url": "https://www.sebi.gov.in/example.pdf",
            "type": "RHP",
            "filedDate": "2026-09-01",
            "title": "Red Herring Prospectus",
        }
        mod.apply_enrichment(record, parsed, doc, "abc", 10, 50)

        self.assertEqual(record["lotSize"], 75)
        self.assertEqual(record["priceBand"], {"min": 94.0, "max": 99.0})
        self.assertEqual(record["observations"]["SEBI-offer"]["lotSize"], 100)
        self.assertEqual(
            record["observations"]["SEBI-offer"]["documentUrl"],
            "https://www.sebi.gov.in/example.pdf",
        )
        self.assertEqual(record["offerDocumentExtraction"]["parserVersion"], 12)
        self.assertEqual(record["offerDocumentExtraction"]["changedFields"], ["priceBand"])


if __name__ == "__main__":
    unittest.main()
