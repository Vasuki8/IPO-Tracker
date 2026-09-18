"""Retained source holds stay actionable when canonical fields become populated."""
import copy
import json
import sys
import unittest
from collections import Counter
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_missing_queue as queue_builder
import phase_status
import source_review_queue as routing
from objects_evidence_fixtures import objects_evidence
from source_review_holds import active_hold_reviews, display_holds
from validate_data import validate_payload, validate_record


TODAY = date(2026, 9, 18)
HOLD_TYPES = {"document_conflict", "source_display_hold"}
DOCUMENT_IDS = {"blackbuck", "mbel", "shriahimsa", "genxai", "kaytex", "speb", "teamtech"}


def hold_reviews(record, holds=None):
    return [issue for issue in validate_record(record, holds=holds)
            if issue.get("reviewType") in HOLD_TYPES]


def resolve_pointer(record, pointer):
    value = record
    if not pointer.startswith("/"):
        raise AssertionError(f"Not a canonical-record JSON pointer: {pointer}")
    for part in pointer[1:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


class ActiveDisplayHoldRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {row["id"]: row for row in json.loads(
            (ROOT / "tests/public_document_reviews_retained.json").read_text())["ipos"]}
        cls.values = {row["id"]: row for row in json.loads(
            (ROOT / "tests/public_quality_retained.json").read_text())["ipos"]}
        cls.production = {row["id"]: row for row in json.loads(
            (ROOT / "data/ipos.json").read_text())["ipos"]}
        cls.holds = {hold["id"]: hold for hold in display_holds()}

    def test_every_retained_document_conflict_becomes_an_evidenced_manual_review(self):
        self.assertEqual(set(self.documents), DOCUMENT_IDS)
        for identifier in DOCUMENT_IDS:
            with self.subTest(id=identifier):
                record = copy.deepcopy(self.documents[identifier])
                before = copy.deepcopy(record)
                hold = self.holds[identifier]
                reviews = hold_reviews(record)
                self.assertEqual(len(reviews), 1)
                review = reviews[0]
                self.assertEqual((review["field"], review["severity"], review["reviewType"]),
                                 ("objectsOfIssue", "review", "document_conflict"))
                self.assertIn(hold["reason"], review["reason"])
                task = routing.review_task(record, review)
                self.assertEqual(task["route"], "manual-source-review")
                self.assertIsNone(task["repairGap"])
                self.assertTrue(task["nextAction"])
                metadata = task["displayHold"]
                self.assertEqual(metadata["registryPath"], "data/public_display_holds.json")
                self.assertEqual(metadata["holdId"], identifier)
                self.assertEqual(metadata["scope"], "document")
                self.assertEqual(metadata["identity"], hold["identity"])
                self.assertEqual(metadata["reviewUrl"], hold["review"])
                self.assertEqual(metadata["reviewedAt"], hold["reviewedAt"])
                for key, value in hold["fields"]["objectsOfIssue"].items():
                    self.assertEqual(metadata["binding"][key], value)
                self.assertEqual(metadata["source"]["sha256"],
                                 record["staticFieldProvenance"]["objectsOfIssue"]["sha256"])
                self.assertTrue(task["evidencePaths"])
                for pointer in task["evidencePaths"]:
                    resolve_pointer(record, pointer)
                self.assertEqual(record, before)

    def test_all_five_retained_value_holds_are_actionable_without_document_reclassification(self):
        expected = {("emmvee", field) for field in
                    ("issueComposition", "issueSizeCr", "freshIssueCr", "ofsCr")}
        expected.add(("unimech", "objectsOfIssue"))
        actual = set()
        for identifier in ("emmvee", "unimech"):
            record = self.values[identifier]
            for review in hold_reviews(record):
                actual.add((identifier, review["field"]))
                self.assertEqual(review["reviewType"], "source_display_hold")
                task = routing.review_task(record, review)
                self.assertEqual(task["route"], "manual-source-review")
                self.assertIsNone(task["repairGap"])
                self.assertEqual(task["displayHold"]["scope"], "value")
                binding = self.holds[identifier]["fields"][review["field"]]
                self.assertEqual(task["displayHold"]["binding"]["valueDigest"], binding["valueDigest"])
                self.assertEqual(task["displayHold"]["source"]["sha256"], binding["sha256"])
        self.assertEqual(actual, expected)

    def test_restored_kaytex_and_speb_values_gain_tasks_without_fabricated_missing_gaps(self):
        for identifier in ("kaytex", "speb"):
            with self.subTest(id=identifier):
                record = copy.deepcopy(self.production[identifier])
                # Keep this restoration regression bound to the retained reviewed PDF,
                # even after future source work changes unrelated production fields.
                record.update(copy.deepcopy(self.documents[identifier]))
                before = copy.deepcopy(record)
                with patch.object(queue_builder, "validate_record",
                                  lambda row: validate_record(row, holds=[])):
                    without_hold = queue_builder.analyze_record(record, TODAY)
                with_hold = queue_builder.analyze_record(record, TODAY)
                self.assertEqual([field for field, _ in with_hold["rules"]],
                                 [field for field, _ in without_hold["rules"]])
                for key in ("rawMissing", "actionable", "resolved"):
                    self.assertEqual(with_hold[key], without_hold[key])
                queued = queue_builder.queue_entry(record, TODAY)
                without_hold_row = queue_builder._queue_entry_from_analysis(record, without_hold)
                self.assertEqual(queued["completenessPct"], without_hold_row["completenessPct"])
                self.assertEqual(queued["missingFieldCount"], without_hold_row["missingFieldCount"])
                self.assertNotIn("offer.objectsOfIssue", queued["missingFields"])
                self.assertNotIn("provenance.finalProspectus.objectsOfIssue", queued["missingFields"])
                tasks = [task for task in queued["sourceReviewItems"] if task.get("displayHold")]
                self.assertEqual(len(tasks), 1)
                self.assertEqual(tasks[0]["field"], "objectsOfIssue")
                self.assertEqual(tasks[0]["route"], "manual-source-review")
                self.assertIsNone(tasks[0]["repairGap"])
                self.assertEqual(record, before)

    def test_mirrors_alternate_allocations_and_empty_values_do_not_resolve_same_document_review(self):
        for variant in ("query", "mirror", "allocation", "empty"):
            with self.subTest(variant=variant):
                record = copy.deepcopy(self.documents["kaytex"])
                proof = record["staticFieldProvenance"]["objectsOfIssue"]
                if variant == "query":
                    proof["sourceUrl"] += "?mirror=1"
                elif variant == "mirror":
                    proof["sourceUrl"] = "https://www.sebi.gov.in/mirrored-final-prospectus.pdf"
                elif variant == "allocation":
                    record["objectsOfIssue"] = [{"purpose": "Working capital requirements", "amountCr": 1.0}]
                    proof["value"] = copy.deepcopy(record["objectsOfIssue"])
                    proof["evidence"] = objects_evidence(record["objectsOfIssue"])
                else:
                    record["objectsOfIssue"] = None
                reviews = hold_reviews(record)
                self.assertEqual(len(reviews), 1)
                task = routing.review_task(record, reviews[0])
                # Original review binding and current extraction remain distinguishable.
                self.assertEqual(task["displayHold"]["binding"]["sourceUrl"],
                                 self.holds["kaytex"]["fields"]["objectsOfIssue"]["sourceUrl"])
                self.assertEqual(task["displayHold"]["source"]["sourceUrl"], proof["sourceUrl"])
                self.assertEqual(task["route"], "manual-source-review")

    def test_different_pdf_issuer_or_offer_never_inherits_document_review(self):
        changes = (("sha256", "a" * 64), ("id", "other-offer"),
                   ("company", "Another Company Limited"), ("symbol", "OTHER"),
                   ("openDate", "2026-08-01"), ("issueOpenDate", "2026-08-01"))
        for field, value in changes:
            with self.subTest(field=field):
                record = copy.deepcopy(self.documents["kaytex"])
                if field in ("sha256", "issueOpenDate"):
                    record["staticFieldProvenance"]["objectsOfIssue"][field] = value
                else:
                    record[field] = value
                    if field == "openDate":
                        record["staticFieldProvenance"]["objectsOfIssue"]["issueOpenDate"] = value
                self.assertEqual(list(active_hold_reviews(record)), [])

    def test_value_hold_releases_only_the_changed_value_binding(self):
        record = copy.deepcopy(self.values["emmvee"])
        record["issueSizeCr"] += 1
        reviews = list(active_hold_reviews(record))
        self.assertEqual({review["field"] for review in reviews},
                         {"issueComposition", "freshIssueCr", "ofsCr"})
        record = copy.deepcopy(self.values["unimech"])
        record["objectsOfIssue"][0]["amountCr"] += 1
        self.assertEqual(list(active_hold_reviews(record)), [])

    def test_duplicate_hold_is_counted_once_without_discarding_other_review_occurrences(self):
        record = copy.deepcopy(self.documents["kaytex"])
        record["offerDocumentExtraction"] = {"conflicts": ["FY2024.patCr", "FY2024.patCr"]}
        hold = self.holds["kaytex"]
        issues = validate_record(record, holds=[hold, copy.deepcopy(hold)])
        holds = [item for item in issues if item.get("reviewType") in HOLD_TYPES]
        financial = [item for item in issues if item["field"] == "financials.FY2024.patCr"]
        self.assertEqual(len(holds), 1)
        self.assertEqual(len(financial), 2)
        self.assertTrue(all(item["reason"] == "Source tables disagree; conflicting metric excluded pending review"
                            for item in financial))

    def test_compact_roundtrip_preserves_hold_evidence_without_enabling_automatic_repairs(self):
        definitions = []
        records = [*self.documents.values(), self.values["emmvee"], self.values["unimech"]]
        for record in records:
            with self.subTest(id=record["id"]):
                tasks = [routing.review_task(record, issue) for issue in hold_reviews(record)]
                rich = {"id": record["id"], "missingFields": [], "sourceReviewItems": tasks}
                compact = {"id": record["id"], "missingFields": [],
                           "sourceReviewItems": routing.compact_review_items(rich, definitions),
                           "sourceReviewGaps": sorted(routing.review_gaps(rich))}
                serialized = json.loads(json.dumps({"row": compact, "definitions": definitions}))
                restored = routing.expand_review_items(serialized["row"], serialized["definitions"])
                self.assertEqual(restored, tasks)
                self.assertEqual(routing.actionable_gaps(rich), set())
                self.assertEqual(routing.actionable_gaps(serialized["row"]), set())
                self.assertEqual(compact["sourceReviewGaps"], [])

    def test_active_document_reviews_are_counted_by_validation_and_the_p4_gate(self):
        records = list(self.documents.values())
        validation = validate_payload({"ipos": records})
        reviews = [issue for issue in validation["issues"] if issue.get("reviewType") == "document_conflict"]
        self.assertEqual(Counter(issue["id"] for issue in reviews), Counter(DOCUMENT_IDS))
        self.assertEqual(validation["reviewCount"], 7)
        self.assertEqual(validation["errorCount"], 0)
        queue = {"queue": [queue_builder.queue_entry(record, TODAY) for record in records],
                 "resolvedUnavailableRecordCount": 0}
        result = phase_status.status(queue, validation)
        self.assertEqual(result["p4"]["sourceReviewItems"], 7)
        self.assertEqual(result["p4"]["blockingSourceReviewItems"], 7)
        self.assertEqual(result["p4"]["unmappedSourceReviewItems"], 0)
        self.assertEqual(result["p4"]["status"], "incomplete")
        self.assertEqual(result["p5"]["status"], "waiting_for_p4")

    def test_malformed_review_identity_scope_or_fingerprint_fails_closed(self):
        for mutation in ("scope", "identity", "fingerprint"):
            with self.subTest(mutation=mutation):
                hold = copy.deepcopy(self.holds["kaytex"])
                if mutation == "scope":
                    hold["scope"] = "unknown"
                elif mutation == "identity":
                    del hold["identity"]["symbol"]
                else:
                    hold["fields"]["objectsOfIssue"]["sha256"] = "not-a-document-hash"
                with self.assertRaises(ValueError):
                    list(active_hold_reviews(self.documents["kaytex"], holds=[hold]))


if __name__ == "__main__":
    unittest.main()
