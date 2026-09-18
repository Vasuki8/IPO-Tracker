"""Source reviews remain actionable independently of missing-field coverage."""
import copy
import io
import json
import sys
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stdout
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_missing_queue as queue_builder
import phase_status
import source_review_queue as routing
from validate_data import validate_payload, validate_record


TODAY = date(2026, 9, 18)


def complete_record():
    return {
        "id": "complete", "company": "Complete Limited", "symbol": "COMPLETE",
        "board": "Mainboard", "exchange": "NSE", "openDate": "2026-04-01",
        "closeDate": "2026-04-03", "listingDate": "2026-04-10",
        "priceBand": {"min": 100, "max": 110}, "lotSize": 100,
        "issueSizeCr": 500, "freshIssueCr": 500, "ofsCr": 0,
        "sources": [{"name": "NSE", "url": "https://www.nseindia.com/"}],
        "validation": {"status": "single-source"},
    }


def conflict_record():
    record = complete_record()
    record["financials"] = {"periods": [{"period": "FY2025", "revenueCr": 100, "patCr": None}]}
    record["documentFieldProvenance"] = {
        "evidence": {"financials": {"FY2025.revenueCr": {"normalizedValue": 100}}},
    }
    record["offerDocumentExtraction"] = {"conflicts": ["FY2025.patCr"]}
    return record


def review_counter(items):
    return Counter((item["field"], item["reason"]) for item in items)


def save_queue(payload, today=TODAY):
    """Exercise the actual saved format without writing a project artifact."""
    now = datetime(today.year, today.month, today.day, 12, tzinfo=queue_builder.IST)
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "missing_queue.json"
        with patch.object(queue_builder, "datetime") as clock, redirect_stdout(io.StringIO()):
            clock.now.return_value = now
            result = queue_builder.main(payload=payload, output_file=output)
        if result != 0:
            raise AssertionError(f"Queue generation returned {result}")
        encoded = output.read_bytes()
    return json.loads(encoded), len(encoded)


def resolve_pointer(record, pointer):
    if not pointer.startswith("/"):
        raise AssertionError(f"Not a record-relative JSON pointer: {pointer!r}")
    value = record
    for component in pointer[1:].split("/"):
        key = component.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


class SourceReviewQueueRoutingTests(unittest.TestCase):
    def test_review_only_conflict_retains_missing_value_and_full_completeness(self):
        self.assertIsNone(queue_builder.queue_entry(complete_record(), TODAY))
        record = conflict_record()
        before = copy.deepcopy(record)

        row = queue_builder.queue_entry(record, TODAY)

        self.assertIsNotNone(row)
        self.assertEqual(row["priority"], 4)
        self.assertEqual(row["missingFields"], [])
        self.assertEqual(row["missingFieldCount"], 0)
        self.assertEqual(row["completenessPct"], 100)
        self.assertEqual(row["sourceReviewCount"], 1)
        task = row["sourceReviewItems"][0]
        self.assertEqual(task["field"], "financials.FY2025.patCr")
        self.assertEqual(task["reason"], "Source tables disagree; conflicting metric excluded pending review")
        self.assertEqual(task["route"], "final-prospectus-review")
        self.assertEqual(task["repairGap"], "offer.financials")
        self.assertTrue(task["nextAction"])
        self.assertIn("/offerDocumentExtraction", task["evidencePaths"])
        for pointer in task["evidencePaths"]:
            resolve_pointer(record, pointer)
        self.assertEqual(routing.actionable_gaps(row), {"offer.financials"})
        self.assertEqual(record, before)
        self.assertIsNone(record["financials"]["periods"][0]["patCr"])

    def test_populated_unverified_metric_is_review_work_without_an_invented_gap(self):
        record = complete_record()
        record["financials"] = {"periods": [{"period": "FY2025", "patCr": 8.5}]}

        row = queue_builder.queue_entry(record, TODAY)

        self.assertEqual(row["missingFields"], [])
        self.assertEqual(row["missingFieldCount"], 0)
        self.assertEqual(row["completenessPct"], 100)
        self.assertEqual(row["sourceReviewCount"], 1)
        self.assertEqual(row["sourceReviewItems"][0]["reason"], "Source table/period evidence has not been revalidated")
        self.assertEqual(routing.actionable_gaps(row), {"offer.financials"})
        self.assertEqual(record["financials"]["periods"][0]["patCr"], 8.5)

    def test_availability_resolution_does_not_resolve_source_review(self):
        record = conflict_record()
        record["lotSize"] = None
        record["dataAvailability"] = {
            "exchange.lotSize": {"status": "exhausted-official-sources", "reason": "Historical notices checked"},
            "offer.financials": {"status": "source-unavailable", "reason": "Prior fetch failed"},
        }

        row = queue_builder.queue_entry(record, TODAY)
        resolved = queue_builder.resolved_availability_entries([record], TODAY)

        self.assertEqual(row["missingFields"], [])
        self.assertEqual(row["missingFieldCount"], 0)
        self.assertLess(row["completenessPct"], 100)
        self.assertEqual(row["resolvedUnavailableFields"], ["exchange.lotSize"])
        self.assertEqual(resolved[0]["resolvedFields"], ["exchange.lotSize"])
        self.assertEqual(row["sourceReviewCount"], 1)
        self.assertEqual(routing.actionable_gaps(row), {"offer.financials"})

    def test_missing_field_and_review_route_are_both_actionable(self):
        record = conflict_record()
        record["lotSize"] = None

        row = queue_builder.queue_entry(record, TODAY)

        self.assertEqual(row["missingFields"], ["exchange.lotSize"])
        self.assertEqual(row["missingFieldCount"], 1)
        self.assertEqual(row["sourceReviewCount"], 1)
        self.assertEqual(routing.actionable_gaps(row), {"exchange.lotSize", "offer.financials"})

    def test_compact_roundtrip_preserves_duplicate_occurrences_and_distinct_reasons(self):
        record = conflict_record()
        record["offerDocumentExtraction"]["conflicts"].append("FY2025.patCr")
        record["financials"]["periods"][0]["patCr"] = 8.5
        expected = [item for item in validate_record(record) if item["severity"] == "review"]
        self.assertEqual(len(expected), 3)
        rich = queue_builder.queue_entry(record, TODAY)

        saved, _ = save_queue({"ipos": [record]})
        compact = saved["queue"][0]
        restored = routing.expand_review_items(compact, saved["sourceReviewDefinitions"])

        self.assertEqual(saved["sourceReviewFormatVersion"], 1)
        self.assertEqual(compact["sourceReviewCount"], 3)
        self.assertEqual(review_counter(restored), review_counter(expected))
        self.assertEqual(restored, rich["sourceReviewItems"])
        self.assertTrue(all(isinstance(item, list) and len(item) == 2 for item in compact["sourceReviewItems"]))
        self.assertEqual(routing.actionable_gaps(compact), routing.actionable_gaps(rich))
        self.assertEqual(compact["sourceReviewGaps"], ["offer.financials"])

    def test_unknown_and_malformed_financial_fields_require_manual_triage(self):
        for field in ("unknown", "financials", "financials.FY25.patCr", "financials.FY2025.unsupportedMetric", "financials.FY2025.patCr.extra"):
            with self.subTest(field=field):
                record = complete_record()
                reason = "Retained source does not establish this field / unit ~ period"
                record["dataReview"] = {field: reason}

                row = queue_builder.queue_entry(record, TODAY)
                task = row["sourceReviewItems"][0]

                self.assertEqual(task["field"], field)
                self.assertEqual(task["reason"], reason)
                self.assertEqual(task["route"], "manual-triage")
                self.assertIsNone(task["repairGap"])
                self.assertTrue(task["nextAction"])
                self.assertEqual(routing.actionable_gaps(row), set())
                saved, _ = save_queue({"ipos": [record]})
                compact = saved["queue"][0]
                self.assertEqual(routing.actionable_gaps(compact), set())
                self.assertEqual(routing.expand_review_items(compact, saved["sourceReviewDefinitions"]), [task])

    def test_listing_conflict_requires_official_exchange_review(self):
        record = complete_record()
        record["listing"] = {"priceConflicts": [{"field": "closePrice", "retained": 95, "official": 92.5}]}

        row = queue_builder.queue_entry(record, TODAY)
        task = row["sourceReviewItems"][0]

        self.assertEqual(row["missingFields"], [])
        self.assertEqual(task["field"], "listing")
        self.assertEqual(task["route"], "official-exchange-review")
        self.assertIsNone(task["repairGap"])
        self.assertIn("/listing/priceConflicts", task["evidencePaths"])
        self.assertEqual(routing.actionable_gaps(row), set())

    def test_final_issue_price_and_retained_roles_use_final_document_routes(self):
        record = complete_record()
        record.update({
            "listing": {"issuePrice": 110},
            "leadManagers": ["Example Capital Advisors Limited"],
            "registrar": "Kfin Technologies Limited",
            "documentRepair": {"status": "needs_review"},
        })

        row = queue_builder.queue_entry(record, TODAY)

        self.assertEqual(row["missingFields"], [])
        tasks = {task["field"]: task for task in row["sourceReviewItems"]}
        self.assertEqual(set(tasks), {"listing.issuePrice", "leadManagers", "registrar"})
        self.assertTrue(all(task["route"] == "final-prospectus-review" for task in tasks.values()))
        self.assertEqual(routing.actionable_gaps(row), {
            "provenance.finalProspectus.listing.issuePrice", "offer.leadManagers", "offer.registrar",
        })

    def test_unrecognized_automatic_gap_is_not_accepted_from_rich_or_compact_rows(self):
        for row in (
            {"sourceReviewItems": [{"route": "final-prospectus-review", "repairGap": "offer.unknown"}]},
            {"sourceReviewGaps": ["offer.unknown", "lifecycle.listingDate", None, 1]},
            {"sourceReviewItems": [{"route": "manual-triage", "repairGap": "offer.financials"}]},
        ):
            with self.subTest(row=row):
                self.assertEqual(routing.actionable_gaps(row), set())

    def test_invalid_compact_reference_fails_instead_of_dropping_review(self):
        saved, _ = save_queue({"ipos": [conflict_record()]})
        for reference in (-1, len(saved["sourceReviewDefinitions"]), "0", True):
            with self.subTest(reference=reference):
                row = copy.deepcopy(saved["queue"][0])
                row["sourceReviewItems"][0][1] = reference
                with self.assertRaises(ValueError):
                    routing.expand_review_items(row, saved["sourceReviewDefinitions"])


class CheckedInSourceReviewCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((ROOT / "data/ipos.json").read_text())
        cls.previous_queue = json.loads((ROOT / "data/missing_queue.json").read_text())
        cls.previous_phase = json.loads((ROOT / "data/phase_status.json").read_text())
        cls.validation = validate_payload(cls.payload)
        cls.saved, cls.size_bytes = save_queue(cls.payload, date.fromisoformat(cls.previous_queue["asOfDate"]))
        cls.expanded = {
            row["id"]: routing.expand_review_items(row, cls.saved["sourceReviewDefinitions"])
            for row in cls.saved["queue"]
        }

    def test_every_current_review_including_previously_unmapped_items_is_persisted(self):
        expected = Counter(
            (item["id"], item["field"], item["reason"])
            for item in self.validation["issues"] if item["severity"] == "review"
        )
        actual = Counter(
            (record_id, task["field"], task["reason"])
            for record_id, tasks in self.expanded.items() for task in tasks
        )
        self.assertEqual(actual, expected)
        self.assertEqual(self.saved["sourceReviewCount"], self.validation["reviewCount"])
        self.assertEqual(sum(row.get("sourceReviewCount", 0) for row in self.saved["queue"]), sum(expected.values()))
        old_ids = {row["id"] for row in self.previous_queue["queue"]}
        previously_unmapped = Counter({identity: count for identity, count in expected.items() if identity[0] not in old_ids})
        self.assertEqual(previously_unmapped - actual, Counter())
        for row in self.saved["queue"]:
            self.assertEqual(row.get("sourceReviewCount", 0), len(self.expanded[row["id"]]))

    def test_routing_does_not_clear_source_reviews_or_enable_p5(self):
        phase = phase_status.status(self.saved, self.validation)
        # Compare routing under the same current validator. Committed reports may
        # predate a new source hold until the serialized review publisher runs.
        before_routing = phase_status.status(self.previous_queue, self.validation)

        self.assertEqual(phase["p4"]["sourceReviewItems"], self.validation["reviewCount"])
        self.assertEqual(phase["p4"]["unmappedSourceReviewItems"], 0)
        self.assertEqual(phase["p4"]["blockingSourceReviewItems"], before_routing["p4"]["blockingSourceReviewItems"])
        self.assertEqual(phase["p4"]["p5OnlySourceReviewItems"], self.previous_phase["p4"]["p5OnlySourceReviewItems"])
        self.assertEqual(phase["p4"]["status"], self.previous_phase["p4"]["status"])
        self.assertEqual(phase["p5"]["status"], self.previous_phase["p5"]["status"])

    def test_saved_queue_fits_existing_transfer_budget(self):
        self.assertLessEqual(self.size_bytes, 642_593)


if __name__ == "__main__":
    unittest.main()
