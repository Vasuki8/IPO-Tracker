import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_issuer_offer_docs_v3.py"
spec = importlib.util.spec_from_file_location("run_issuer_offer_docs_v3", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class IssuerOfferDocsV3Tests(unittest.TestCase):
    def test_current_parser_is_v13(self):
        self.assertEqual(mod.base.PARSER_VERSION, 13)
        self.assertEqual(mod.parser_v13.PARSER_VERSION, 13)
        self.assertIs(mod.base._extract_targeted_full_text, mod.parser_v13.extract_targeted_pdf_text)

    def test_validated_terms_remain_fill_only_and_stamp_v13(self):
        record = {
            "lotSize": None,
            "priceBand": {"min": 80.0, "max": 85.0},
            "sources": [],
            "documents": [],
            "observations": {},
        }
        parsed = {
            "issueComposition": {},
            "leadManagers": [],
            "registrar": None,
            "promoters": [],
            "financials": None,
            "objectsOfIssue": [],
            "shareholding": None,
            "lotSize": 100,
            "priceBand": {"min": 90.0, "max": 95.0},
            "extractedFields": ["lotSize", "priceBand"],
        }
        doc = {
            "url": "https://www.bseindia.com/example.pdf",
            "sourcePage": "https://www.bseindia.com/example.pdf",
            "host": "www.bseindia.com",
            "type": "Prospectus",
            "title": "Prospectus",
            "extractionSource": "BSE",
            "documentSource": "BSE",
            "sourceName": "BSE final Prospectus",
            "sourceKind": "exchange-filing",
        }

        changed = mod.merge_validated_terms(
            record,
            parsed,
            doc,
            pdf_hash="abc",
            pages_read=300,
            page_count=450,
        )

        self.assertEqual(record["lotSize"], 100)
        self.assertEqual(record["priceBand"], {"min": 80.0, "max": 85.0})
        self.assertIn("lotSize", changed)
        self.assertNotIn("priceBand", changed)
        self.assertEqual(record["observations"]["Offer-document"]["parserVersion"], 13)
        self.assertEqual(record["issuerDocumentExtraction"]["parserVersion"], 13)


if __name__ == "__main__":
    unittest.main()
