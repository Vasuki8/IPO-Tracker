import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import enforce_final_prospectus_policy as enforcement


class FinalProspectusEnforcementTests(unittest.TestCase):
    def record(self):
        return {
            "id": "example",
            "company": "Example Limited",
            "openDate": "2026-04-01",
            "financials": {
                "unit": "₹ crore",
                "periods": [
                    {"period": "FY2025", "revenueCr": 100.0, "patCr": 10.0},
                    {"period": "FY2024", "revenueCr": 90.0, "patCr": 9.0},
                ],
            },
            "documents": [
                {
                    "type": "PROSPECTUS",
                    "title": "Final Prospectus",
                    "url": "https://www.sebi.gov.in/files/final.pdf",
                }
            ],
        }

    def evidence(self):
        return {
            "FY2025.revenueCr": {"page": 100, "normalizedValue": 100.0},
            "FY2025.patCr": {"page": 100, "normalizedValue": 10.0},
            "FY2024.revenueCr": {"page": 100, "normalizedValue": 90.0},
            "FY2024.patCr": {"page": 100, "normalizedValue": 9.0},
        }

    def test_legacy_final_marker_without_cell_evidence_is_demoted(self):
        record = self.record()
        record["staticFieldProvenance"] = {
            "financials": {
                "documentType": "PROSPECTUS",
                "sourceUrl": "https://www.sebi.gov.in/files/final.pdf",
                "value": record["financials"],
            }
        }
        record["offerDocumentExtraction"] = {
            "status": "extracted",
            "documentType": "PROSPECTUS",
            "documentTitle": "Final Prospectus",
            "documentUrl": "https://www.sebi.gov.in/files/final.pdf",
            "extractedFields": ["financials"],
        }

        enforcement.apply_policy({"ipos": [record]})

        self.assertNotIn("financials", record["staticFieldProvenance"])
        self.assertNotIn("financials", record["staticSourcePolicy"]["verifiedFields"])
        self.assertIn("financials", record["staticSourcePolicy"]["pendingRevalidationFields"])

    def test_canonical_fields_prevent_rejected_extracted_financial_bootstrap(self):
        record = self.record()
        record["offerDocumentExtraction"] = {
            "status": "extracted",
            "documentType": "PROSPECTUS",
            "documentTitle": "Final Prospectus",
            "documentUrl": "https://www.sebi.gov.in/files/final.pdf",
            "extractedFields": ["financials", "lotSize"],
            "canonicalFields": ["lotSize"],
        }
        record["lotSize"] = 100

        enforcement.apply_policy({"ipos": [record]})

        self.assertIn("lotSize", record["staticSourcePolicy"]["verifiedFields"])
        self.assertNotIn("financials", record["staticSourcePolicy"]["verifiedFields"])
        self.assertIn("financials", record["staticSourcePolicy"]["pendingRevalidationFields"])

    def test_supported_legacy_document_evidence_can_migrate_financials(self):
        record = self.record()
        record["offerDocumentExtraction"] = {
            "status": "extracted",
            "documentType": "PROSPECTUS",
            "documentTitle": "Final Prospectus",
            "documentUrl": "https://www.sebi.gov.in/files/final.pdf",
            "extractedFields": ["financials"],
            "sha256": "abc",
            "parserVersion": 22,
        }
        record["documentFieldProvenance"] = {
            "sourceUrl": "https://www.sebi.gov.in/files/final.pdf",
            "documentType": "PROSPECTUS",
            "evidence": {"financials": self.evidence()},
        }

        enforcement.apply_policy({"ipos": [record]})

        self.assertIn("financials", record["staticSourcePolicy"]["verifiedFields"])
        self.assertNotIn("financials", record["staticSourcePolicy"]["pendingRevalidationFields"])
        provenance = record["staticFieldProvenance"]["financials"]
        self.assertEqual(provenance["value"], record["financials"])
        self.assertEqual(provenance["evidence"], self.evidence())


if __name__ == "__main__":
    unittest.main()
