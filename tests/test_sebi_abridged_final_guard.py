import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import enforce_final_prospectus_policy as enforcement
import final_prospectus_identity as identity
import final_prospectus_policy as policy

MODULE = ROOT / "scripts" / "enrich_sebi_document_links.py"
spec = importlib.util.spec_from_file_location("sebi_abridged_guard", MODULE)
links = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = links
spec.loader.exec_module(links)


class SebiAbridgedFinalGuardTests(unittest.TestCase):
    AP_URL = "https://www.sebi.gov.in/sebi_data/commondocs/sep-2026/Example%20Limited%20-%20AP_p.pdf"
    FINAL_URL = "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1789000000000.pdf"

    def page(self):
        return f"""
        <html><body>
          <a href="{self.AP_URL}">Example Limited - Abridged Prospectus</a>
          <a href="https://www.sebi.gov.in/web/?file=https%3A%2F%2Fwww.sebi.gov.in%2Fsebi_data%2Fattachdocs%2Fsep-2026%2F1789000000000.pdf">Example Limited - Prospectus</a>
        </body></html>
        """

    def test_rhp_landing_keeps_abridged_as_rhp_history(self):
        docs = links.extract_pdf_links(
            self.page(),
            "https://www.sebi.gov.in/filings/public-issues/sep-2026/example-rhp.html",
            fallback_type="RHP",
        )
        by_url = {doc["url"]: doc for doc in docs}
        self.assertEqual(by_url[self.AP_URL]["type"], "RHP")
        self.assertEqual(by_url[self.FINAL_URL]["type"], "PROSPECTUS")

    def test_final_landing_does_not_promote_abridged_pdf(self):
        docs = links.extract_pdf_links(
            self.page(),
            "https://www.sebi.gov.in/filings/public-issues/sep-2026/example-prospectus.html",
            fallback_type="PROSPECTUS",
        )
        by_url = {doc["url"]: doc for doc in docs}
        self.assertEqual(by_url[self.AP_URL]["type"], "ABRIDGED")
        self.assertEqual(by_url[self.FINAL_URL]["type"], "PROSPECTUS")

    def test_legacy_abridged_pdf_typed_prospectus_is_not_final(self):
        doc = {
            "type": "PROSPECTUS",
            "title": "Example Limited - Abridged Prospectus",
            "url": self.AP_URL,
            "source": "SEBI",
        }
        record = {"company": "Example Limited", "openDate": "2026-09-16", "documents": [doc]}
        self.assertFalse(policy.is_final_prospectus(doc))
        self.assertTrue(identity.known_non_final_document_url(record, self.AP_URL))
        self.assertFalse(identity.candidate_acceptable(record, doc))
        self.assertEqual(policy.final_prospectus_candidates(record), [])

    def test_true_final_wins_when_legacy_abridged_copy_is_also_attached(self):
        abridged = {
            "type": "PROSPECTUS",
            "title": "Example Limited - Abridged Prospectus",
            "url": self.AP_URL,
            "source": "SEBI",
        }
        final = {
            "type": "PROSPECTUS",
            "title": "SEBI PROSPECTUS",
            "url": self.FINAL_URL,
            "source": "SEBI",
        }
        record = {
            "company": "Example Limited",
            "openDate": "2026-09-10",
            "documents": [abridged, final],
        }
        selected = identity.choose_candidate(record, policy.final_prospectus_candidates(record))
        self.assertIsNotNone(selected)
        self.assertEqual(selected["url"], self.FINAL_URL)

    def test_legacy_abridged_provenance_is_demoted(self):
        record = {
            "id": "example",
            "company": "Example Limited",
            "openDate": "2026-09-16",
            "lotSize": 100,
            "documents": [
                {
                    "type": "PROSPECTUS",
                    "title": "Example Limited - Abridged Prospectus",
                    "url": self.AP_URL,
                    "source": "SEBI",
                }
            ],
            "offerDocumentExtraction": {
                "status": "extracted",
                "documentType": "PROSPECTUS",
                "documentTitle": "Example Limited - Abridged Prospectus",
                "documentUrl": self.AP_URL,
                "canonicalFields": ["lotSize"],
            },
            "staticFieldProvenance": {
                "lotSize": {
                    "documentType": "PROSPECTUS",
                    "sourceUrl": self.AP_URL,
                    "value": 100,
                }
            },
        }

        enforcement.apply_policy({"ipos": [record]})

        self.assertNotIn("lotSize", record["staticFieldProvenance"])
        self.assertNotIn("lotSize", record["staticSourcePolicy"]["verifiedFields"])
        self.assertIn("lotSize", record["staticSourcePolicy"]["pendingRevalidationFields"])
        self.assertEqual(record["staticSourcePolicy"]["status"], "awaiting-final-prospectus")


if __name__ == "__main__":
    unittest.main()
