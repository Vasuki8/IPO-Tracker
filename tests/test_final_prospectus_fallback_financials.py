import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

MODULE = SCRIPTS / "run_issuer_offer_docs.py"
spec = importlib.util.spec_from_file_location("run_issuer_offer_docs_financial_guard", MODULE)
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


class FinalProspectusFallbackFinancialGuardTests(unittest.TestCase):
    def setUp(self):
        self.original_merge = runner._ORIGINAL_MERGE

    def tearDown(self):
        runner._ORIGINAL_MERGE = self.original_merge

    @staticmethod
    def doc():
        return {
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/example.pdf",
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/example.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
        }

    @staticmethod
    def parsed():
        return {
            "financials": {
                "unit": "₹ crore",
                "periods": [
                    {"period": "FY2025", "revenueCr": 999.0, "patCr": 99.0},
                    {"period": "FY2024", "revenueCr": 888.0, "patCr": 88.0},
                ],
            },
            "fieldEvidence": {
                "financials": {"FY2025.revenueCr": {"normalizedValue": 999.0}},
            },
            "issueComposition": {
                "freshShares": 1_000_000,
                "ofsShares": 0,
                "freshIssueCr": 100.0,
                "ofsCr": 0.0,
                "totalIssueSizeCr": 100.0,
            },
            "extractedFields": ["financials", "issueComposition"],
        }

    def test_canonical_payload_removes_legacy_financials_and_evidence(self):
        safe = runner._canonical_fallback_payload(self.parsed())
        self.assertNotIn("financials", safe)
        self.assertNotIn("financials", safe["extractedFields"])
        self.assertNotIn("financials", safe.get("fieldEvidence", {}))
        self.assertIn("issueComposition", safe)

    def test_fallback_does_not_overwrite_strict_financials_or_evidence(self):
        strict_financials = {
            "unit": "₹ crore",
            "periods": [
                {"period": "FY2025", "revenueCr": 123.0, "patCr": 12.0},
                {"period": "FY2024", "revenueCr": 111.0, "patCr": 10.0},
            ],
        }
        strict_evidence = {
            "financials": {
                "FY2025.revenueCr": {"normalizedValue": 123.0},
                "FY2024.revenueCr": {"normalizedValue": 111.0},
            }
        }
        record = {
            "id": "example",
            "company": "Example Limited",
            "openDate": "2026-01-01",
            "financials": copy.deepcopy(strict_financials),
            "documentFieldProvenance": {"evidence": copy.deepcopy(strict_evidence)},
            "staticFieldProvenance": {
                "financials": {"source": "Final Prospectus", "value": copy.deepcopy(strict_financials)}
            },
            "documents": [],
            "sources": [],
            "observations": {},
        }

        def guarded_merge(current, parsed, doc, **kwargs):
            self.assertNotIn("financials", parsed)
            current["issuerDocumentExtraction"] = {
                "status": "extracted",
                "documentUrl": doc["url"],
                "documentTitle": doc["title"],
            }
            return []

        runner._ORIGINAL_MERGE = guarded_merge
        changed = runner.merge_validated_offer_enrichment(
            record,
            self.parsed(),
            self.doc(),
            pdf_hash="abc",
            pages_read=30,
            page_count=100,
        )

        self.assertEqual(record["financials"], strict_financials)
        self.assertEqual(record["documentFieldProvenance"]["evidence"], strict_evidence)
        self.assertEqual(record["staticFieldProvenance"]["financials"]["value"], strict_financials)
        self.assertEqual(record["issueComposition"]["freshIssueCr"], 100.0)
        self.assertNotIn("financials", record["issuerDocumentExtraction"]["extractedFields"])
        self.assertIn("issueComposition", changed)

    def test_fallback_does_not_add_legacy_financials_when_canonical_is_blank(self):
        record = {
            "id": "example",
            "company": "Example Limited",
            "openDate": "2026-01-01",
            "financials": None,
            "documents": [],
            "sources": [],
            "observations": {},
        }

        def guarded_merge(current, parsed, doc, **kwargs):
            self.assertNotIn("financials", parsed)
            current["issuerDocumentExtraction"] = {
                "status": "extracted",
                "documentUrl": doc["url"],
                "documentTitle": doc["title"],
            }
            return []

        runner._ORIGINAL_MERGE = guarded_merge
        runner.merge_validated_offer_enrichment(
            record,
            self.parsed(),
            self.doc(),
            pdf_hash="abc",
            pages_read=30,
            page_count=100,
        )
        self.assertIsNone(record["financials"])
        self.assertNotIn("financials", record.get("staticFieldProvenance", {}))


if __name__ == "__main__":
    unittest.main()
