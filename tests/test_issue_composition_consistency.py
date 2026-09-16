import copy
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import build_missing_queue as queue
import enforce_final_prospectus_policy as enforcement
import final_prospectus_policy as policy
from issue_composition_checks import COMPOSITION_FIELDS, composition_problems
from validate_data import validate_record


DOC = {"type": "PROSPECTUS", "title": "Final Prospectus", "url": "https://www.sebi.gov.in/files/skyways-final.pdf"}
# PDF cover figures: fresh 28,898,300 shares, OFS 13,333,300 shares at Rs 138.
GOOD = {"freshShares": 28_898_300, "ofsShares": 13_333_300,
        "freshIssueCr": 398.7965, "ofsCr": 183.9995,
        "totalIssueSizeCr": 582.796, "valuationPriceUsed": 138.0}


class IssueCompositionConsistencyTests(unittest.TestCase):
    def record(self):
        record = {"id": "skyways", "company": "Skyways Air Services Limited",
                  "openDate": "2026-08-24", "closeDate": "2026-08-26", "documents": [DOC]}
        policy.apply_final_prospectus_static_fields(record, {"issueComposition": GOOD}, DOC, sha256="proof", parser_version=26)
        record["offerDocumentExtraction"] = {"status": "extracted", "documentType": "PROSPECTUS",
            "documentUrl": DOC["url"], "canonicalFields": list(COMPOSITION_FIELDS), "extractedFields": ["issueComposition"]}
        return record

    def broken_record(self):
        record = self.record()
        record["issueComposition"]["ofsShares"] = 28_898_300
        record["staticFieldProvenance"]["issueComposition"]["value"] = copy.deepcopy(record["issueComposition"])
        return record

    def test_document_rounding_is_accepted_but_duplicate_seller_count_is_rejected(self):
        self.assertEqual(composition_problems(GOOD), [])
        bad = {**GOOD, "ofsShares": GOOD["freshShares"]}
        self.assertTrue(composition_problems(bad))

    def test_missing_and_explicit_zero_components_are_different(self):
        self.assertEqual(composition_problems({"freshIssueCr": 100.0}), [])
        self.assertTrue(composition_problems({"ofsShares": 0, "ofsCr": 100.0}))
        self.assertTrue(composition_problems({"freshIssueCr": 100.0, "totalIssueSizeCr": 80.0}))

    def test_policy_rejects_invalid_incoming_group_without_overwriting_accepted_terms(self):
        record = self.record()
        before = {field: copy.deepcopy(record[field]) for field in COMPOSITION_FIELDS}
        bad = {**GOOD, "ofsShares": GOOD["freshShares"]}
        policy.apply_final_prospectus_static_fields(record, {"issueComposition": bad}, DOC)
        self.assertEqual({field: record[field] for field in COMPOSITION_FIELDS}, before)

    def test_semantic_validator_blocks_contradictory_verified_amounts(self):
        findings = validate_record(self.broken_record())
        self.assertTrue(any(item["severity"] == "error" and item["field"] == "issueComposition.ofsCr" for item in findings))

    def test_partial_incoming_component_cannot_mix_with_incompatible_retained_total(self):
        record = {"id": "legacy", "issueSizeCr": 80.0, "ofsCr": 50.0}
        policy.apply_final_prospectus_static_fields(record, {"issueComposition": {"freshIssueCr": 100.0}}, DOC)
        self.assertEqual(record["issueSizeCr"], 80.0)
        self.assertNotIn("freshIssueCr", record)
        self.assertNotIn("issueComposition", record["staticFieldProvenance"])

    def test_legacy_mixed_source_disagreement_remains_a_review_without_fabricated_correction(self):
        record = {"id": "legacy", "freshIssueCr": 175.062, "ofsCr": 175.062, "issueSizeCr": 175.062}
        before = copy.deepcopy(record)
        enforcement.apply_policy({"ipos": [record]})
        self.assertTrue(any(item["severity"] == "review" for item in validate_record(record)))
        self.assertEqual(record["freshIssueCr"], before["freshIssueCr"])
        self.assertNotIn("issueCompositionReview", record)

    def test_quarantine_preserves_source_snapshot_and_cannot_bootstrap_again(self):
        record = self.broken_record()
        before = copy.deepcopy(record["issueComposition"])
        payload = {"ipos": [record]}
        enforcement.apply_policy(payload)
        self.assertTrue(all(record[field] is None for field in COMPOSITION_FIELDS))
        snapshot = record["issueCompositionReview"]["snapshot"]
        self.assertEqual(snapshot["before"]["issueComposition"], before)
        self.assertEqual(snapshot["sourceEvidence"]["issueComposition"]["sha256"], "proof")
        count = len(record["dataCorrections"])
        enforcement.apply_policy(payload)
        self.assertEqual(len(record["dataCorrections"]), count)
        self.assertFalse(set(COMPOSITION_FIELDS) & set(record["staticFieldProvenance"]))
        self.assertEqual(record["staticSourcePolicy"]["status"], "pending-revalidation")

    def test_quarantined_null_fields_stay_in_final_prospectus_queue(self):
        record = self.broken_record()
        enforcement.apply_policy({"ipos": [record]})
        entry = queue.queue_entry(record, date(2026, 9, 16))
        self.assertTrue({"provenance.finalProspectus." + field for field in COMPOSITION_FIELDS} <= set(entry["missingFields"]))
        self.assertTrue(any(item["severity"] == "review" and "quarantined" in item["reason"] for item in validate_record(record)))

    def test_old_extraction_fields_cannot_bootstrap_contradictory_verification(self):
        record = self.broken_record()
        record.pop("staticFieldProvenance")
        enforcement.apply_policy({"ipos": [record]})
        self.assertFalse(set(COMPOSITION_FIELDS) & set(record["staticFieldProvenance"]))
        self.assertEqual(record["staticSourcePolicy"]["status"], "pending-revalidation")
        self.assertFalse(any(item["severity"] == "error" for item in validate_record(record)))

    def test_availability_exclusion_cannot_complete_active_quarantine(self):
        record = self.broken_record()
        enforcement.apply_policy({"ipos": [record]})
        fields = {"provenance.finalProspectus." + field for field in COMPOSITION_FIELDS}
        record["dataAvailability"] = {field: {"status": "source-unavailable"} for field in fields}
        entry = queue.queue_entry(record, date(2026, 9, 16))
        self.assertTrue(fields <= set(entry["missingFields"]))
        self.assertFalse(fields & set(entry["resolvedUnavailableFields"]))

    def test_partial_repair_does_not_resolve_unread_components(self):
        record = self.broken_record()
        enforcement.apply_policy({"ipos": [record]})
        policy.apply_final_prospectus_static_fields(record, {"issueComposition": {"freshIssueCr": 398.7965}}, DOC)
        enforcement.apply_policy({"ipos": [record]})
        self.assertEqual(record["issueCompositionReview"]["status"], "quarantined")
        self.assertEqual(set(record["issueCompositionReview"]["fields"]), {"ofsCr", "issueSizeCr"})
        self.assertIsNone(record["ofsCr"])
        self.assertEqual(record["freshIssueCr"], 398.7965)

    def test_full_source_repair_resolves_quarantine_and_retains_before_evidence(self):
        record = self.broken_record()
        enforcement.apply_policy({"ipos": [record]})
        policy.apply_final_prospectus_static_fields(record, {"issueComposition": GOOD}, DOC, sha256="new-proof")
        enforcement.apply_policy({"ipos": [record]})
        self.assertEqual(record["issueCompositionReview"]["status"], "resolved")
        self.assertEqual(record["issueComposition"], GOOD)
        self.assertFalse(any("quarantined" in item["reason"] for item in validate_record(record)))
        self.assertEqual(record["dataCorrections"][0]["before"]["issueComposition"]["ofsShares"], 28_898_300)


if __name__ == "__main__":
    unittest.main()
