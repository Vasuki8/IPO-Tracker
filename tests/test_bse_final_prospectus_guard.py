import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import enforce_final_prospectus_policy as enforcement
import final_prospectus_identity as identity
import final_prospectus_policy as policy

MODULE = ROOT / "scripts" / "enrich_exchange_details.py"
spec = importlib.util.spec_from_file_location("bse_detail_guard", MODULE)
bse = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bse
spec.loader.exec_module(bse)


class BSEFinalProspectusGuardTests(unittest.TestCase):
    NOTICE_URL = "https://www.bseindia.com/downloads/UploadDocs/Notices/20260910-50/20260910-50.pdf"
    PROSPECTUS_URL = "https://www.bseindia.com/corporates/download/123/IPO/PROSPECTUS_EXAMPLE.pdf"

    def test_nested_issue_row_does_not_promote_exchange_notice(self):
        html = f"""
        <table>
          <tr>
            <td>
              <table>
                <tr><td>Prospectus &amp; GID</td><td>Click Here</td></tr>
                <tr><td>Exchange Notices</td><td><a href="{self.NOTICE_URL}">Public Issue Notice</a></td></tr>
              </table>
            </td>
            <td>Issue information</td>
          </tr>
        </table>
        """
        detail = bse.parse_detail_html(html)
        self.assertEqual(detail["documents"], [])

    def test_exact_prospectus_gid_value_cell_is_retained(self):
        html = f"""
        <table>
          <tr><td>Security Type</td><td>Equity</td></tr>
          <tr><td>Prospectus &amp; GID</td><td><a href="{self.PROSPECTUS_URL}">Click Here</a></td></tr>
        </table>
        """
        detail = bse.parse_detail_html(html)
        self.assertEqual(len(detail["documents"]), 1)
        self.assertEqual(detail["documents"][0]["url"], self.PROSPECTUS_URL)
        self.assertEqual(detail["documents"][0]["type"], "PROSPECTUS")

    def test_bse_exchange_notice_is_never_final_prospectus(self):
        doc = {
            "type": "PROSPECTUS",
            "title": "Prospectus & GID",
            "url": self.NOTICE_URL,
            "source": "BSE",
        }
        record = {"company": "Example Limited", "openDate": "2026-09-10", "documents": [doc]}
        self.assertFalse(policy.is_final_prospectus(doc))
        self.assertTrue(identity.known_non_final_document_url(record, self.NOTICE_URL))
        self.assertFalse(identity.candidate_acceptable(record, doc))
        self.assertEqual(policy.final_prospectus_candidates(record), [])

    def test_true_bse_prospectus_route_remains_eligible(self):
        doc = {
            "type": "PROSPECTUS",
            "title": "Prospectus & GID",
            "url": self.PROSPECTUS_URL,
            "source": "BSE",
        }
        record = {"company": "Example Limited", "openDate": "2026-09-10", "documents": [doc]}
        self.assertTrue(policy.is_final_prospectus(doc))
        self.assertFalse(identity.known_non_final_document_url(record, self.PROSPECTUS_URL))
        self.assertTrue(identity.candidate_acceptable(record, doc))
        self.assertEqual(policy.final_prospectus_candidates(record)[0]["url"], self.PROSPECTUS_URL)

    def test_legacy_notice_provenance_is_demoted_for_revalidation(self):
        record = {
            "id": "example",
            "company": "Example Limited",
            "openDate": "2026-09-10",
            "lotSize": 100,
            "documents": [
                {
                    "type": "PROSPECTUS",
                    "title": "Prospectus & GID",
                    "url": self.NOTICE_URL,
                    "source": "BSE",
                }
            ],
            "offerDocumentExtraction": {
                "status": "extracted",
                "documentType": "PROSPECTUS",
                "documentTitle": "Prospectus & GID",
                "documentUrl": self.NOTICE_URL,
                "canonicalFields": ["lotSize"],
            },
            "staticFieldProvenance": {
                "lotSize": {
                    "documentType": "PROSPECTUS",
                    "sourceUrl": self.NOTICE_URL,
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
