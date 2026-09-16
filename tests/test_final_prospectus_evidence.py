import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_policy as policy
import validate_data


class FinalProspectusEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://www.sebi.gov.in/files/final.pdf",
            "filedDate": "2026-09-10",
        }

    def test_final_static_terms_replace_legacy_issue_specific_evidence(self):
        record = {
            "id": "example",
            "company": "Example Limited",
            "openDate": "2026-09-01",
            "lotSize": 500,
            "lotSizeEvidence": {
                "source": "NSE issue information",
                "sourceUrl": "https://www.nseindia.com/example",
                "value": 500,
                "issueOpenDate": "2026-09-01",
            },
            "listing": {
                "issuePrice": 100.0,
                "issuePriceEvidence": {
                    "source": "NSE final listing",
                    "sourceUrl": "https://www.nseindia.com/final",
                    "value": 100.0,
                    "issueOpenDate": "2026-09-01",
                },
            },
        }
        policy.apply_final_prospectus_static_fields(
            record,
            {"lotSize": 1200, "issuePrice": 124.0},
            self.doc,
            sha256="abc",
            parser_version=24,
            checked_at="2026-09-16T00:00:00Z",
        )

        self.assertEqual(record["lotSizeEvidence"]["source"], "Final Prospectus")
        self.assertEqual(record["lotSizeEvidence"]["value"], 1200)
        self.assertEqual(record["lotSizeEvidence"]["issueOpenDate"], record["openDate"])
        issue_evidence = record["listing"]["issuePriceEvidence"]
        self.assertEqual(issue_evidence["source"], "Final Prospectus")
        self.assertEqual(issue_evidence["value"], 124.0)
        self.assertEqual(issue_evidence["issueOpenDate"], record["openDate"])

        errors = [issue for issue in validate_data.validate_record(record) if issue["severity"] == "error"]
        self.assertNotIn("lotSize", {issue["field"] for issue in errors})
        self.assertNotIn("listing.issuePrice", {issue["field"] for issue in errors})

    def test_final_evidence_is_refreshed_even_when_value_is_unchanged(self):
        record = {
            "id": "same-value",
            "company": "Same Value Limited",
            "openDate": "2026-09-01",
            "lotSize": 1200,
            "lotSizeEvidence": {
                "source": "Legacy exchange source",
                "sourceUrl": "https://www.nseindia.com/legacy",
                "value": 1200,
                "issueOpenDate": "2026-09-01",
            },
            "listing": {"issuePrice": 124.0},
        }
        changes = policy.apply_final_prospectus_static_fields(
            record,
            {"lotSize": 1200, "issuePrice": 124.0},
            self.doc,
            sha256="same",
            parser_version=24,
            checked_at="2026-09-16T00:00:00Z",
        )

        self.assertEqual(changes, [])
        self.assertEqual(record["lotSizeEvidence"]["documentType"], "PROSPECTUS")
        self.assertEqual(record["listing"]["issuePriceEvidence"]["documentType"], "PROSPECTUS")
        self.assertEqual(
            record["staticFieldProvenance"]["listing.issuePrice"]["issueOpenDate"],
            record["openDate"],
        )


if __name__ == "__main__":
    unittest.main()
