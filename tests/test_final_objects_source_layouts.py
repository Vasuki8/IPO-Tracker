"""Normal Final Prospectus collection uses the bounded allocation producer."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_parser as parser
from objects_of_issue_checks import objects_evidence_problems
from objects_evidence_fixtures import objects_parsed
from validate_data import validate_record


class FinalObjectsSourceLayoutsTests(unittest.TestCase):
    def test_normal_parser_recovers_the_four_exact_allocation_fixtures(self):
        expected = {
            "deepa": [215, 12.148], "priority": [75, 18.852],
            "sheel": [9.1195, 15.88, 4.768, 4.2525],
            "dhanlaxmi": [20.0577, 2.2463, 1.5],
        }
        for issuer, amounts in expected.items():
            with self.subTest(issuer=issuer):
                text = (ROOT / f"tests/fixtures/objects_of_issue/{issuer}-allocation-table.txt").read_text()
                parsed = parser.parse_document_text(text)
                self.assertEqual([row["amountCr"] for row in parsed["objectsOfIssue"]], amounts)
                self.assertEqual(parsed["extractedFields"].count("objectsOfIssue"), 1)
                self.assertEqual(objects_evidence_problems(parsed["objectsOfIssue"],
                    parsed["fieldEvidence"]["objectsOfIssue"]), [])

    def test_main_adapter_replaces_legacy_value_and_evidence_together(self):
        text = (ROOT / "tests/fixtures/objects_of_issue/priority-allocation-table.txt").read_text()
        legacy = objects_parsed([{"purpose": "Working capital", "amountCr": 999}])
        before = copy.deepcopy(legacy)
        with patch.object(parser.base, "parse_document_text", return_value=legacy):
            parsed = parser.parse_document_text(text)
        self.assertEqual([row["amountCr"] for row in parsed["objectsOfIssue"]], [75, 18.852])
        self.assertNotEqual(parsed["fieldEvidence"]["objectsOfIssue"], before["fieldEvidence"]["objectsOfIssue"])
        self.assertEqual(parsed["fieldEvidence"]["objectsOfIssue"]["rows"], parsed["objectsOfIssue"])

    def test_unproven_base_parser_objects_cannot_survive_as_extracted_fields(self):
        legacy = objects_parsed([{"purpose": "Working capital", "amountCr": 999}])
        with patch.object(parser.base, "parse_document_text", return_value=legacy):
            parsed = parser.parse_document_text("No allocation table in this source")
        self.assertNotIn("objectsOfIssue", parsed)
        self.assertNotIn("objectsOfIssue", parsed["fieldEvidence"])
        self.assertNotIn("objectsOfIssue", parsed["extractedFields"])

    def test_semantic_validation_rejects_visible_allocations_without_matching_proof(self):
        rows = [{"purpose": "Working capital", "amountCr": 10}]
        record = {"id": "example", "objectsOfIssue": rows}
        self.assertTrue(any(issue["field"] == "objectsOfIssue" and issue["severity"] == "error"
                            for issue in validate_record(record)))
        record["staticFieldProvenance"] = {"objectsOfIssue": {
            "value": rows, "sourceUrl": "https://www.sebi.gov.in/example.pdf", "sha256": "source-bytes",
            "documentType": "PROSPECTUS", "evidence": objects_parsed(rows)["fieldEvidence"]["objectsOfIssue"],
        }}
        self.assertFalse(any(issue["field"] == "objectsOfIssue" for issue in validate_record(record)))
        for document_type in ("RHP", None):
            record["staticFieldProvenance"]["objectsOfIssue"]["documentType"] = document_type
            self.assertTrue(any(issue["field"] == "objectsOfIssue" and issue["severity"] == "error"
                                for issue in validate_record(record)))


if __name__ == "__main__":
    unittest.main()
