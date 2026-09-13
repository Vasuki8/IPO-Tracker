import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v13.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v13", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class FakePage:
    def __init__(self, text=""):
        self.text = text

    def extract_text(self):
        return self.text


class FakeReader:
    def __init__(self, pages):
        self.pages = pages
        self.is_encrypted = False


class OfferDocsV13Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 13)
        self.assertEqual(mod.base.PARSER_VERSION, 13)

    def test_exact_lot_page_outranks_generic_price_page(self):
        lot = mod._offer_term_page_score(
            "Issue Procedure. Minimum Bid Lot: 125 Equity Shares and multiples thereafter."
        )
        price = mod._offer_term_page_score("The Issue Price may be determined in accordance with law.")
        self.assertGreater(lot, price)
        self.assertGreater(lot, 0)

    def test_irrelevant_equity_quantity_does_not_select_page(self):
        self.assertEqual(
            mod._offer_term_page_score(
                "The Promoters shall contribute a minimum of 2,000 Equity Shares before the Offer."
            ),
            0,
        )

    def test_deep_bid_lot_page_is_appended_to_parser_text(self):
        pages = [FakePage() for _ in range(40)]
        pages[35] = FakePage(
            "Issue Procedure. Minimum Bid Lot: 125 Equity Shares and in multiples of 125 Equity Shares thereafter."
        )
        pages[36] = FakePage("How to Apply")

        old_reader = mod.PdfReader
        old_first = mod._ORIGINAL_FIRST_PAGES
        try:
            mod.PdfReader = lambda _stream: FakeReader(pages)
            mod._ORIGINAL_FIRST_PAGES = lambda _data: ("Cover text", 30, 40)
            text, pages_read, page_count = mod.extract_pdf_text(b"fake")
        finally:
            mod.PdfReader = old_reader
            mod._ORIGINAL_FIRST_PAGES = old_first

        self.assertIn("Minimum Bid Lot: 125 Equity Shares", text)
        self.assertEqual(pages_read, 40)
        self.assertEqual(page_count, 40)
        parsed = mod.parse_document_text(text)
        self.assertEqual(parsed["lotSize"], 125)
        self.assertIn("lotSize", parsed["extractedFields"])

    def test_v12_recognition_and_fill_only_semantics_are_retained(self):
        parsed = mod.parse_document_text(
            "Price Band is ₹ 94 to ₹ 99 per Equity Share. Minimum Bid Quantity: 150 Equity Shares."
        )
        self.assertEqual(parsed["lotSize"], 150)
        self.assertEqual(parsed["priceBand"], {"min": 94.0, "max": 99.0})

        record = {"lotSize": 100, "priceBand": None, "observations": {}}
        doc = {
            "url": "https://www.sebi.gov.in/example.pdf",
            "type": "RHP",
            "filedDate": "2026-09-01",
            "title": "RHP",
        }
        mod.apply_enrichment(record, parsed, doc, "hash", 40, 100)
        self.assertEqual(record["lotSize"], 100)
        self.assertEqual(record["priceBand"], {"min": 94.0, "max": 99.0})
        self.assertEqual(record["offerDocumentExtraction"]["parserVersion"], 13)
        self.assertEqual(record["observations"]["SEBI-offer"]["parserVersion"], 13)


if __name__ == "__main__":
    unittest.main()
