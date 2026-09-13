import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_issuer_offer_docs_v4.py"
spec = importlib.util.spec_from_file_location("run_issuer_offer_docs_v4", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class IssuerOfferDocsV4Tests(unittest.TestCase):
    def test_current_parser_remains_v13(self):
        self.assertEqual(mod.base.PARSER_VERSION, 13)

    def test_new_official_sebi_fallbacks(self):
        expected = {
            "indomim": ("INDO-MIM Limited", "RHP", "1784523106091.pdf"),
            "omni": ("Omnitech Engineering Limited", "RHP", "1771933506852.pdf"),
            "rsl": ("Rajputana Stainless Limited", "Prospectus", "1775629467259.pdf"),
        }
        for record_id, (company, doc_type, pdf_name) in expected.items():
            entry = mod.base.ISSUER_DOCUMENTS[record_id]
            self.assertEqual(entry["company"], company)
            self.assertEqual(entry["host"], "www.sebi.gov.in")
            self.assertEqual(entry["type"], doc_type)
            self.assertEqual(entry["extractionSource"], "SEBI")
            self.assertEqual(entry["documentSource"], "SEBI")
            self.assertEqual(entry["sourceKind"], "regulatory-filing")
            self.assertTrue(entry["url"].endswith(pdf_name))
            self.assertTrue(entry["sourcePage"].startswith("https://www.sebi.gov.in/filings/public-issues/"))

    def test_new_official_nse_fallbacks(self):
        expected = {
            "ardee": (
                "Ardee Industries Limited",
                "Prospectus",
                "FP_INE0XNF01022_10AUG2026.pdf",
            ),
            "powerica": (
                "Powerica Limited",
                "Prospectus",
                "FP_INE921L01032_30MAR2026.pdf",
            ),
        }
        for record_id, (company, doc_type, pdf_name) in expected.items():
            entry = mod.base.ISSUER_DOCUMENTS[record_id]
            self.assertEqual(entry["company"], company)
            self.assertEqual(entry["host"], "nsearchives.nseindia.com")
            self.assertEqual(entry["type"], doc_type)
            self.assertEqual(entry["extractionSource"], "NSE")
            self.assertEqual(entry["documentSource"], "NSE")
            self.assertEqual(entry["sourceKind"], "exchange-filing")
            self.assertTrue(entry["url"].endswith(pdf_name))
            self.assertEqual(entry["sourcePage"], entry["url"])

    def test_duplicate_id_selects_exact_registered_issuer(self):
        payload = {
            "ipos": [
                {
                    "id": "rsl",
                    "company": "Rajputana Stainless Limited",
                    "stage": "listed",
                },
                {
                    "id": "rsl",
                    "company": "Rajputana Stainless Limited-Special Withdrawal Option",
                    "stage": "closed",
                },
            ]
        }
        queue = {
            "queue": [
                {
                    "id": "rsl",
                    "company": "Rajputana Stainless Limited",
                    "priority": 4,
                    "missingFields": ["offer.registrar"],
                },
                {
                    "id": "rsl",
                    "company": "Rajputana Stainless Limited-Special Withdrawal Option",
                    "priority": 4,
                    "missingFields": ["exchange.issueSizeCr"],
                },
            ]
        }

        targets = mod._identity_safe_targets(payload, queue, priority_max=4, limit=10)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0][0]["company"], "Rajputana Stainless Limited")
        self.assertEqual(targets[0][2]["company"], "Rajputana Stainless Limited")

    def test_ambiguous_same_issuer_duplicates_are_not_guessed(self):
        payload = {
            "ipos": [
                {"id": "rsl", "company": "Rajputana Stainless Limited"},
                {"id": "rsl", "company": "Rajputana Stainless Limited"},
            ]
        }
        queue = {
            "queue": [
                {
                    "id": "rsl",
                    "company": "Rajputana Stainless Limited",
                    "priority": 4,
                    "missingFields": ["offer.registrar"],
                }
            ]
        }
        self.assertEqual(mod._identity_safe_targets(payload, queue, 4, 10), [])

    def test_current_parser_success_for_same_document_is_skipped(self):
        spec_entry = mod.base.ISSUER_DOCUMENTS["ardee"]
        payload = {
            "ipos": [
                {
                    "id": "ardee",
                    "company": "Ardee Industries Limited",
                    "issuerDocumentExtraction": {
                        "status": "extracted",
                        "parserVersion": mod.base.PARSER_VERSION,
                        "documentUrl": spec_entry["url"],
                    },
                }
            ]
        }
        queue = {
            "queue": [
                {
                    "id": "ardee",
                    "company": "Ardee Industries Limited",
                    "priority": 4,
                    "missingFields": ["offer.financials"],
                }
            ]
        }
        self.assertEqual(mod._identity_safe_targets(payload, queue, 4, 10), [])

    def test_previous_batch_failure_moves_behind_fresh_candidate(self):
        payload = {
            "meta": {
                "issuerOfferDocumentHealth": {
                    "errors": ["Ardee Industries Limited: read timeout"]
                }
            },
            "ipos": [
                {"id": "ardee", "company": "Ardee Industries Limited"},
                {"id": "indomim", "company": "INDO-MIM Limited"},
            ],
        }
        queue = {
            "queue": [
                {
                    "id": "ardee",
                    "company": "Ardee Industries Limited",
                    "priority": 4,
                    "missingFields": ["offer.financials"],
                },
                {
                    "id": "indomim",
                    "company": "INDO-MIM Limited",
                    "priority": 4,
                    "missingFields": ["offer.financials"],
                },
            ]
        }

        targets = mod._identity_safe_targets(payload, queue, priority_max=4, limit=1)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0][0]["id"], "indomim")

    def test_document_change_reenables_previous_success(self):
        spec_entry = mod.base.ISSUER_DOCUMENTS["ardee"]
        payload = {
            "ipos": [
                {
                    "id": "ardee",
                    "company": "Ardee Industries Limited",
                    "issuerDocumentExtraction": {
                        "status": "extracted",
                        "parserVersion": mod.base.PARSER_VERSION,
                        "documentUrl": "https://example.invalid/old-ardee.pdf",
                    },
                }
            ]
        }
        queue = {
            "queue": [
                {
                    "id": "ardee",
                    "company": "Ardee Industries Limited",
                    "priority": 4,
                    "missingFields": ["exchange.issueComposition"],
                }
            ]
        }

        targets = mod._identity_safe_targets(payload, queue, priority_max=4, limit=10)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0][2]["url"], spec_entry["url"])


if __name__ == "__main__":
    unittest.main()
