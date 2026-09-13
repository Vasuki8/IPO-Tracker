import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_issuer_offer_docs_v2.py"
spec = importlib.util.spec_from_file_location("run_issuer_offer_docs_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class IssuerOfferDocsV2Tests(unittest.TestCase):
    def test_current_parser_is_v12(self):
        self.assertEqual(mod.base.PARSER_VERSION, 12)
        self.assertEqual(mod.parser_v12.PARSER_VERSION, 12)

    def test_validated_terms_are_fill_only(self):
        record = {
            "lotSize": 50,
            "priceBand": None,
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
            "priceBand": {"min": 80.0, "max": 85.0},
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
            pages_read=12,
            page_count=20,
        )

        self.assertEqual(record["lotSize"], 50)
        self.assertEqual(record["priceBand"], {"min": 80.0, "max": 85.0})
        self.assertIn("priceBand", changed)
        self.assertNotIn("lotSize", changed)
        self.assertEqual(record["observations"]["Offer-document"]["lotSize"], 100)
        self.assertEqual(record["observations"]["Offer-document"]["source"], "BSE")
        self.assertEqual(record["issuerDocumentExtraction"]["parserVersion"], 12)


if __name__ == "__main__":
    unittest.main()
