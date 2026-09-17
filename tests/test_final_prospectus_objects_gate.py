import copy
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import build_missing_queue as queue
import enforce_final_prospectus_policy as enforcement
import final_prospectus_parser as parser
import final_prospectus_policy as policy
import p4_offer_parser as residual
from publish_transaction import merge_payload
from validate_data import validate_record


DOC = {"type": "PROSPECTUS", "title": "Final Prospectus",
       "url": "https://www.sebi.gov.in/files/issuer-final.pdf"}
GOOD = [{"purpose": "Funding working capital requirements", "amountCr": 25.0}]
TOC = [{"purpose": "BASIS FOR ISSUE PRICE", "amountCr": 117.0},
       {"purpose": "STATEMENT OF POSSIBLE SPECIAL TAX BENEFITS", "amountCr": 127.0},
       {"purpose": "INDUSTRY OVERVIEW", "amountCr": 130.0}]
TEXT = """[PAGE 4]
TABLE OF CONTENTS
OBJECTS OF THE ISSUE 100
BASIS FOR ISSUE PRICE 117
STATEMENT OF POSSIBLE SPECIAL TAX BENEFITS 127
SECTION IV: ABOUT OUR COMPANY 130
INDUSTRY OVERVIEW 130
OUR BUSINESS 213
"""


class FinalProspectusObjectsGateTests(unittest.TestCase):
    def record(self, invalid=False):
        record = {"id": "issuer", "company": "Issuer Limited", "documents": [DOC],
                  "openDate": "2026-09-01", "closeDate": "2026-09-03", "dataCorrections": []}
        parsed = {"objectsOfIssue": copy.deepcopy(GOOD), "fieldEvidence": {"objectsOfIssue": {
            "page": 100, "heading": "OBJECTS OF THE ISSUE", "unit": "crore", "rows": copy.deepcopy(GOOD)}}}
        policy.apply_final_prospectus_static_fields(record, parsed, DOC, sha256="source-proof")
        for key in ("offerDocumentExtraction", "issuerDocumentExtraction"):
            record[key] = {"status": "extracted", "documentType": "PROSPECTUS",
                           "documentUrl": DOC["url"], "extractedFields": ["objectsOfIssue"],
                           "canonicalFields": ["objectsOfIssue"]}
        if invalid:
            record["objectsOfIssue"] = copy.deepcopy(TOC)
            record["staticFieldProvenance"]["objectsOfIssue"]["value"] = copy.deepcopy(TOC)
        return record

    def test_final_parser_drops_contents_page_values_and_recognition(self):
        parsed = parser.parse_document_text(TEXT)
        self.assertFalse(parsed.get("objectsOfIssue"))
        self.assertNotIn("objectsOfIssue", parsed["extractedFields"])
        self.assertNotIn("objectsOfIssue", parsed["fieldEvidence"])
        supplement = residual.parse_document_text(TEXT)
        self.assertFalse(residual.merge_parsed(parsed, supplement).get("objectsOfIssue"))

    def test_canonical_gate_rejects_contents_rows_without_overwriting_valid_objects(self):
        record = self.record()
        evidence = copy.deepcopy(record["staticFieldProvenance"]["objectsOfIssue"])
        policy.apply_final_prospectus_static_fields(record, {"objectsOfIssue": TOC}, DOC)
        self.assertEqual(record["objectsOfIssue"], GOOD)
        self.assertEqual(record["staticFieldProvenance"]["objectsOfIssue"], evidence)

    def test_semantic_validator_blocks_old_contents_values(self):
        findings = validate_record(self.record(invalid=True))
        self.assertTrue(any(row["field"] == "objectsOfIssue" and row["severity"] == "error" for row in findings))

    def test_quarantine_preserves_evidence_and_cannot_bootstrap_from_either_extraction(self):
        record = self.record(invalid=True)
        payload = {"ipos": [record]}
        enforcement.apply_policy(payload)
        self.assertIsNone(record["objectsOfIssue"])
        snapshot = record["objectsOfIssueReview"]["snapshot"]
        self.assertEqual(snapshot["before"], TOC)
        self.assertEqual(snapshot["sourceEvidence"]["sha256"], "source-proof")
        count = len(record["dataCorrections"])
        enforcement.apply_policy(payload)
        self.assertEqual(len(record["dataCorrections"]), count)
        self.assertNotIn("objectsOfIssue", record["staticFieldProvenance"])
        for key in ("offerDocumentExtraction", "issuerDocumentExtraction"):
            self.assertNotIn("objectsOfIssue", record[key]["canonicalFields"])
            self.assertNotIn("objectsOfIssue", record[key]["extractedFields"])
        self.assertIn("objectsOfIssue", record["staticSourcePolicy"]["pendingRevalidationFields"])
        self.assertFalse(any(row["severity"] == "error" for row in validate_record(record)))
        self.assertTrue(any(row["field"] == "objectsOfIssue" and row["severity"] == "review" for row in validate_record(record)))

    def test_legacy_contents_values_are_held_even_without_canonical_provenance(self):
        record = self.record(invalid=True)
        record.pop("staticFieldProvenance")
        enforcement.apply_policy({"ipos": [record]})
        self.assertIsNone(record["objectsOfIssue"])
        self.assertEqual(record["objectsOfIssueReview"]["snapshot"]["sourceUrl"], DOC["url"])
        self.assertNotIn("objectsOfIssue", record["staticFieldProvenance"])

    def test_missing_objects_stay_actionable_despite_availability_exclusions(self):
        record = self.record(invalid=True)
        enforcement.apply_policy({"ipos": [record]})
        fields = {"offer.objectsOfIssue", "provenance.finalProspectus.objectsOfIssue"}
        record["dataAvailability"] = {field: {"status": "source-unavailable"} for field in fields}
        entry = queue.queue_entry(record, date(2026, 9, 16))
        self.assertTrue(fields <= set(entry["missingFields"]))
        self.assertFalse(fields & set(entry["resolvedUnavailableFields"]))

    def test_unrelated_source_update_cannot_resolve_objects_quarantine(self):
        record = self.record(invalid=True)
        enforcement.apply_policy({"ipos": [record]})
        policy.apply_final_prospectus_static_fields(record, {"lotSize": 100}, DOC)
        self.assertIn("objectsOfIssue", record["staticSourcePolicy"]["pendingRevalidationFields"])
        enforcement.apply_policy({"ipos": [record]})
        self.assertEqual(record["objectsOfIssueReview"]["status"], "quarantined")
        self.assertIsNone(record["objectsOfIssue"])

    def test_valid_final_source_replacement_resolves_quarantine_and_keeps_audit(self):
        record = self.record(invalid=True)
        enforcement.apply_policy({"ipos": [record]})
        policy.apply_final_prospectus_static_fields(record, {"objectsOfIssue": GOOD}, DOC, sha256="replacement")
        enforcement.apply_policy({"ipos": [record]})
        self.assertEqual(record["objectsOfIssue"], GOOD)
        self.assertEqual(record["objectsOfIssueReview"]["status"], "resolved")
        self.assertEqual(record["objectsOfIssueReview"]["snapshot"]["before"], TOC)
        self.assertEqual(record["staticFieldProvenance"]["objectsOfIssue"]["sha256"], "replacement")
        self.assertNotIn("objectsOfIssue", record["staticSourcePolicy"]["pendingRevalidationFields"])

    def test_residual_parser_cannot_bypass_nonfinite_amount_guard(self):
        self.assertFalse(residual.valid_objects([{"purpose": "Working capital", "amountCr": float("nan")}]))

    def test_concurrent_publication_keeps_objects_value_proof_and_quarantine_together(self):
        before = self.record(invalid=True)
        proposed = copy.deepcopy(before)
        policy.apply_final_prospectus_static_fields(proposed, {"objectsOfIssue": GOOD}, DOC, sha256="replacement")
        current = copy.deepcopy(before)
        enforcement.apply_policy({"ipos": [current]})
        payloads = [{"meta": {}, "ipos": [record]} for record in (before, proposed, current)]
        merged, conflicts = merge_payload(*payloads)
        record = merged["ipos"][0]
        self.assertIsNone(record["objectsOfIssue"])
        self.assertEqual(record["objectsOfIssueReview"]["status"], "quarantined")
        self.assertNotIn("objectsOfIssue", record["staticFieldProvenance"])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["path"], ["ipos", "issuer", "documentFields"])


if __name__ == "__main__":
    unittest.main()
