import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_progressive.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_progressive", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OfferDocsProgressiveTests(unittest.TestCase):
    def test_scheduler_keeps_parser_v13(self):
        self.assertEqual(mod.PARSER_VERSION, 13)
        self.assertEqual(mod.parser_v13.PARSER_VERSION, 13)

    def test_unattempted_documents_precede_errors_then_oldest_error_first(self):
        doc = {"url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/example.pdf"}
        records = [
            {
                "id": "new-error",
                "status": "listed",
                "openDate": "2026-08-01",
                "offerDocumentExtraction": {
                    "status": "error",
                    "parserVersion": 13,
                    "documentUrl": doc["url"],
                    "lastAttemptAt": "2026-09-13T12:00:00+05:30",
                },
            },
            {
                "id": "unattempted",
                "status": "listed",
                "openDate": "2026-07-01",
            },
            {
                "id": "old-error",
                "status": "listed",
                "openDate": "2026-08-10",
                "offerDocumentExtraction": {
                    "status": "error",
                    "parserVersion": 13,
                    "documentUrl": doc["url"],
                    "lastAttemptAt": "2026-09-12T12:00:00+05:30",
                },
            },
        ]
        ordered = sorted(records, key=lambda row: mod.candidate_sort_key(row, doc))
        self.assertEqual(
            [row["id"] for row in ordered],
            ["unattempted", "old-error", "new-error"],
        )

    def test_error_for_different_document_is_treated_as_new_work(self):
        doc = {"url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/new.pdf"}
        record = {
            "status": "listed",
            "openDate": "2026-08-01",
            "offerDocumentExtraction": {
                "status": "error",
                "parserVersion": 13,
                "documentUrl": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/old.pdf",
                "lastAttemptAt": "2026-09-13T12:00:00+05:30",
            },
        }
        self.assertEqual(mod.candidate_sort_key(record, doc)[0], 0)


if __name__ == "__main__":
    unittest.main()
