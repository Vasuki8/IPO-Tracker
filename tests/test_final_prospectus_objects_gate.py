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
from build_company_pages import public_profile_record
from publish_transaction import merge_payload
from validate_data import validate_record
from objects_evidence_fixtures import objects_evidence, objects_parsed


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
LOT_TERMS = [{
    "purpose": "Lot Size The Market lot and Trading lot for the Equity Share is 1,200 and in multiples of",
    "amountCr": 1200.0,
}]
LOT_TEXT = """[PAGE 11]
For further details refer to “Objects of the Issue” beginning on page 77 of this Prospectus.
Lot Size  The Market lot and Trading lot for the Equity Share is 1,200 and in multiples of 1,200
thereafter; subject to a minimum allotment of 1,200 Equity Shares.
"""


class FinalProspectusObjectsGateTests(unittest.TestCase):
    def record(self, invalid=False):
        record = {"id": "issuer", "company": "Issuer Limited", "documents": [DOC],
                  "openDate": "2026-09-01", "closeDate": "2026-09-03", "dataCorrections": []}
        parsed = objects_parsed(GOOD)
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

    def test_lot_definition_after_objects_cross_reference_cannot_supply_proceeds(self):
        # Paramount's PDF page 11 defines shares per lot. The nearby objects
        # cross-reference is not the monetary allocation table on page 77.
        parsed = parser.parse_document_text(LOT_TEXT)
        self.assertFalse(parsed.get("objectsOfIssue"))
        self.assertNotIn("objectsOfIssue", parsed["extractedFields"])
        self.assertNotIn("objectsOfIssue", parsed["fieldEvidence"])
        supplement = residual.parse_document_text(LOT_TEXT)
        self.assertFalse(residual.merge_parsed(parsed, supplement).get("objectsOfIssue"))

    def test_verified_lot_metadata_is_held_with_audit_and_removed_from_public_profile(self):
        record = self.record()
        record["lotSize"] = 1200
        record["objectsOfIssue"] = copy.deepcopy(LOT_TERMS)
        record["staticFieldProvenance"]["objectsOfIssue"]["value"] = copy.deepcopy(LOT_TERMS)
        original_proof = copy.deepcopy(record["staticFieldProvenance"]["objectsOfIssue"])
        self.assertTrue(any(row["field"] == "objectsOfIssue" and row["severity"] == "error"
                            for row in validate_record(record)))

        payload = {"ipos": [record]}
        enforcement.apply_policy(payload)
        self.assertIsNone(record["objectsOfIssue"])
        self.assertNotIn("objectsOfIssue", public_profile_record(record))
        self.assertEqual(record["lotSize"], 1200)
        snapshot = copy.deepcopy(record["objectsOfIssueReview"]["snapshot"])
        self.assertEqual(snapshot["before"], LOT_TERMS)
        self.assertEqual(snapshot["sourceEvidence"], original_proof)
        self.assertNotIn("objectsOfIssue", record["staticFieldProvenance"])
        entry = queue.queue_entry(record, date(2026, 9, 17))
        self.assertTrue({"offer.objectsOfIssue", "provenance.finalProspectus.objectsOfIssue"}
                        <= set(entry["missingFields"]))

        corrections = copy.deepcopy(record["dataCorrections"])
        enforcement.apply_policy(payload)
        policy.apply_final_prospectus_static_fields(record, {"objectsOfIssue": LOT_TERMS}, DOC)
        self.assertIsNone(record["objectsOfIssue"])
        self.assertEqual(record["dataCorrections"], corrections)
        self.assertFalse(any(row["severity"] == "error" for row in validate_record(record)))

        policy.apply_final_prospectus_static_fields(record, objects_parsed(GOOD), DOC,
                                                   sha256="reviewed-allocation-table")
        enforcement.apply_policy(payload)
        self.assertEqual(record["objectsOfIssue"], GOOD)
        self.assertEqual(record["objectsOfIssueReview"]["status"], "resolved")
        self.assertEqual(record["objectsOfIssueReview"]["snapshot"], snapshot)

    def test_canonical_gate_rejects_contents_rows_without_overwriting_valid_objects(self):
        record = self.record()
        evidence = copy.deepcopy(record["staticFieldProvenance"]["objectsOfIssue"])
        policy.apply_final_prospectus_static_fields(record, {"objectsOfIssue": TOC}, DOC)
        self.assertEqual(record["objectsOfIssue"], GOOD)
        self.assertEqual(record["staticFieldProvenance"]["objectsOfIssue"], evidence)

    def test_missing_or_mismatched_evidence_cannot_overwrite_supported_objects(self):
        replacement = [{"purpose": "General corporate purposes", "amountCr": 5.0}]
        incomplete = [
            {"objectsOfIssue": replacement},
            {"objectsOfIssue": replacement, "fieldEvidence": {"objectsOfIssue": objects_evidence(GOOD)}},
        ]
        for parsed in incomplete:
            with self.subTest(parsed=parsed):
                record = self.record()
                evidence = copy.deepcopy(record["staticFieldProvenance"]["objectsOfIssue"])
                changes = policy.apply_final_prospectus_static_fields(record, parsed, DOC, sha256="other-source")
                enforcement.apply_policy({"ipos": [record]})
                self.assertEqual(record["objectsOfIssue"], GOOD)
                self.assertEqual(record["staticFieldProvenance"]["objectsOfIssue"], evidence)
                self.assertNotIn("objectsOfIssue", {row["field"] for row in changes})

    def test_matching_source_rows_and_value_are_promoted_together(self):
        rows = [
            {"purpose": "Working capital requirements", "amountCr": 0.0},
            {"purpose": "General corporate purposes", "amountCr": None},
        ]
        record = self.record()
        parsed = objects_parsed(rows)
        changes = policy.apply_final_prospectus_static_fields(record, parsed, DOC, sha256="exact-table")
        enforcement.apply_policy({"ipos": [record]})
        self.assertEqual(record["objectsOfIssue"], rows)
        self.assertIn("objectsOfIssue", {row["field"] for row in changes})
        proof = record["staticFieldProvenance"]["objectsOfIssue"]
        self.assertEqual(proof["value"], rows)
        self.assertEqual(proof["evidence"], parsed["fieldEvidence"]["objectsOfIssue"])
        self.assertEqual(proof["sha256"], "exact-table")

    def test_new_objects_need_both_source_url_and_hash(self):
        rows = [{"purpose": "General corporate purposes", "amountCr": 5.0}]
        for doc, digest in ((DOC, None), ({"type": "PROSPECTUS"}, "source-proof")):
            with self.subTest(doc=doc, digest=digest):
                record = self.record()
                proof = copy.deepcopy(record["staticFieldProvenance"]["objectsOfIssue"])
                changes = policy.apply_final_prospectus_static_fields(record, objects_parsed(rows), doc, sha256=digest)
                self.assertEqual(record["objectsOfIssue"], GOOD)
                self.assertEqual(record["staticFieldProvenance"]["objectsOfIssue"], proof)
                self.assertNotIn("objectsOfIssue", {row["field"] for row in changes})

    def test_stale_proof_for_absent_objects_cannot_rebootstrap_verification(self):
        for value in (None, []):
            with self.subTest(value=value):
                record = self.record()
                record["objectsOfIssue"] = value
                record["staticFieldProvenance"]["objectsOfIssue"]["value"] = value
                enforcement.apply_policy({"ipos": [record]})
                self.assertNotIn("objectsOfIssue", record["staticFieldProvenance"])
                self.assertNotIn("objectsOfIssue", record["staticSourcePolicy"]["verifiedFields"])
                self.assertEqual(record["dataCorrections"], [])

    def test_legacy_rows_without_raw_evidence_are_withheld_without_calling_them_wrong(self):
        record = self.record()
        weak = {"page": 100, "heading": "OBJECTS OF THE ISSUE", "unit": "crore", "rows": copy.deepcopy(GOOD)}
        record["staticFieldProvenance"]["objectsOfIssue"]["evidence"] = copy.deepcopy(weak)
        record["documentFieldProvenance"]["evidence"]["objectsOfIssue"] = copy.deepcopy(weak)
        original_proof = copy.deepcopy(record["staticFieldProvenance"]["objectsOfIssue"])
        original_document = copy.deepcopy(record["documentFieldProvenance"])
        original_extractions = {key: copy.deepcopy(record[key]) for key in ("offerDocumentExtraction", "issuerDocumentExtraction")}

        enforcement.apply_policy({"ipos": [record]})

        self.assertIsNone(record["objectsOfIssue"])
        self.assertNotIn("objectsOfIssue", public_profile_record(record))
        review = record["objectsOfIssueReview"]
        self.assertEqual(review["reviewKind"], "source-evidence-required")
        snapshot = copy.deepcopy(review["snapshot"])
        self.assertEqual(snapshot["before"], GOOD)
        self.assertEqual(snapshot["sourceEvidence"], original_proof)
        self.assertEqual(snapshot["documentProvenance"], original_document)
        self.assertEqual(snapshot["extractionEvidence"], original_extractions)
        self.assertIn("lack matching source-table evidence", snapshot["reason"])
        self.assertNotIn("Invalid", snapshot["reason"])
        corrections = copy.deepcopy(record["dataCorrections"])
        entry = queue.queue_entry(record, date(2026, 9, 17))
        self.assertTrue({"offer.objectsOfIssue", "provenance.finalProspectus.objectsOfIssue"} <= set(entry["missingFields"]))

        enforcement.apply_policy({"ipos": [record]})
        self.assertEqual(record["dataCorrections"], corrections)
        self.assertEqual(record["objectsOfIssueReview"]["snapshot"], snapshot)

    def test_extraction_markers_cannot_rebootstrap_objects_without_raw_evidence(self):
        for extraction_key in ("offerDocumentExtraction", "issuerDocumentExtraction"):
            for field_key in ("canonicalFields", "extractedFields"):
                with self.subTest(extraction_key=extraction_key, field_key=field_key):
                    record = self.record()
                    record.pop("staticFieldProvenance")
                    record.pop("documentFieldProvenance")
                    for key in ("offerDocumentExtraction", "issuerDocumentExtraction"):
                        record.pop(key)
                    record[extraction_key] = {
                        "status": "extracted", "documentType": "PROSPECTUS", "documentUrl": DOC["url"],
                        "sha256": "source-proof", field_key: ["objectsOfIssue"],
                    }
                    self.assertNotIn("objectsOfIssue", enforcement._extraction_fields(record, record[extraction_key]))
                    enforcement.apply_policy({"ipos": [record]})
                    self.assertIsNone(record["objectsOfIssue"])
                    self.assertEqual(record["objectsOfIssueReview"]["snapshot"]["before"], GOOD)
                    self.assertNotIn("objectsOfIssue", record["staticSourcePolicy"]["verifiedFields"])

    def test_legacy_complete_document_evidence_migrates_only_for_same_url_and_hash(self):
        for field_key in ("canonicalFields", "extractedFields"):
            for source_url, digest, accepted in (
                (DOC["url"], "source-proof", True),
                ("https://www.sebi.gov.in/files/other.pdf", "source-proof", False),
                (DOC["url"], "other-bytes", False),
                (DOC["url"], None, False),
            ):
                with self.subTest(field_key=field_key, source_url=source_url, digest=digest):
                    record = self.record()
                    record.pop("staticFieldProvenance")
                    record.pop("issuerDocumentExtraction")
                    record["offerDocumentExtraction"] = {
                        "status": "extracted", "documentType": "PROSPECTUS", "documentUrl": source_url,
                        "sha256": digest, field_key: ["objectsOfIssue"],
                    }
                    enforcement.apply_policy({"ipos": [record]})
                    if accepted:
                        self.assertEqual(record["objectsOfIssue"], GOOD)
                        proof = record["staticFieldProvenance"]["objectsOfIssue"]
                        self.assertEqual(proof["value"], GOOD)
                        self.assertEqual(proof["evidence"], objects_evidence(GOOD))
                        self.assertIn("objectsOfIssue", record["staticSourcePolicy"]["verifiedFields"])
                    else:
                        self.assertIsNone(record["objectsOfIssue"])
                        self.assertNotIn("objectsOfIssue", record["staticSourcePolicy"]["verifiedFields"])

    def test_existing_proof_document_fallback_requires_matching_url_hash_and_value(self):
        for changed_key, changed_value in (
            (None, None),
            ("sourceUrl", "https://www.sebi.gov.in/files/other.pdf"),
            ("sha256", "different-bytes"),
            ("value", [{"purpose": "General corporate purposes", "amountCr": 5.0}]),
        ):
            with self.subTest(changed_key=changed_key):
                record = self.record()
                proof = record["staticFieldProvenance"]["objectsOfIssue"]
                proof.pop("evidence")
                if changed_key:
                    proof[changed_key] = changed_value
                enforcement.apply_policy({"ipos": [record]})
                if changed_key:
                    self.assertIsNone(record["objectsOfIssue"])
                    self.assertNotIn("objectsOfIssue", record["staticSourcePolicy"]["verifiedFields"])
                else:
                    self.assertEqual(record["objectsOfIssue"], GOOD)
                    self.assertEqual(proof["evidence"], objects_evidence(GOOD))

    def test_non_final_source_cannot_support_legacy_objects_even_with_raw_evidence(self):
        record = self.record()
        record["documents"] = [{**DOC, "type": "RHP", "title": "Red Herring Prospectus"}]
        enforcement.apply_policy({"ipos": [record]})
        self.assertIsNone(record["objectsOfIssue"])
        self.assertEqual(record["objectsOfIssueReview"]["reviewKind"], "source-evidence-required")

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

    def test_rejected_replacement_cannot_resolve_quarantine(self):
        record = self.record(invalid=True)
        enforcement.apply_policy({"ipos": [record]})
        original = copy.deepcopy(record["objectsOfIssueReview"])
        for parsed in (
            {"objectsOfIssue": GOOD},
            {"objectsOfIssue": GOOD, "fieldEvidence": {"objectsOfIssue": objects_evidence(
                [{"purpose": "General corporate purposes", "amountCr": 5.0}]
            )}},
        ):
            policy.apply_final_prospectus_static_fields(record, parsed, DOC, sha256="rejected")
            enforcement.apply_policy({"ipos": [record]})
            self.assertIsNone(record["objectsOfIssue"])
            self.assertEqual(record["objectsOfIssueReview"], original)
            self.assertNotIn("objectsOfIssue", record["staticFieldProvenance"])

    def test_valid_final_source_replacement_resolves_quarantine_and_keeps_audit(self):
        record = self.record(invalid=True)
        enforcement.apply_policy({"ipos": [record]})
        policy.apply_final_prospectus_static_fields(record, objects_parsed(GOOD), DOC, sha256="replacement")
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
        policy.apply_final_prospectus_static_fields(proposed, objects_parsed(GOOD), DOC, sha256="replacement")
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
