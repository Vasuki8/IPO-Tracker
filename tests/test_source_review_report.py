"""Optional PDF diagnostics cannot discard completed source validation."""
import hashlib
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import review_source_repairs as review
from objects_evidence_fixtures import objects_parsed


class SourceReviewReportTests(unittest.TestCase):
    def preview(self, directory, *, invalid=False, interrupt=False, residual=False, unsupported=False, untouched=False, queue_case=False, reviewed=False):
        root = Path(directory)
        (root / "data").mkdir()
        cache = root / "cache"
        cache.mkdir()
        data_file = root / "data/ipos.json"
        report_file = root / "data/source_review.json"
        data_file.write_text(json.dumps({"ipos": [
            {"id": "first", "company": "First Limited"},
            {"id": "second", "company": "Second Limited"},
        ]}))
        registry = {"reviewedObjects": []}
        if reviewed:
            initial = json.loads(data_file.read_text())
            identity = {"id": "first", "company": "First Limited", "symbol": "FIRST", "openDate": "2026-01-01"}
            initial["ipos"][0].update(identity)
            initial["ipos"][0].update(
                closeDate="2026-01-03", listingDate="2026-01-08",
                documents=[{"type": "PROSPECTUS", "url": "https://www.sebi.gov.in/files/first.pdf"}],
            )
            data_file.write_text(json.dumps(initial))
            registry["reviewedObjects"].append({
                "identity": identity,
                "beforeHash": review.corrections.fingerprint([{"purpose": "Working capital", "amountCr": 10.0}]),
                "source": {"type": "PROSPECTUS", "url": "https://www.sebi.gov.in/files/first.pdf"},
                "evidence": {"sha256": "source-bytes"},
                "findings": ["The reviewed document gives conflicting net proceeds."],
                "reason": "Withheld pending authoritative source reconciliation.",
                "scope": "document",
                "reviewedAt": "2026-09-17T20:00:00+00:00",
            })
        (root / "data/verified_corrections.json").write_text(json.dumps(registry))
        if queue_case:
            initial = json.loads(data_file.read_text())
            for record in initial["ipos"]:
                record.update(openDate="2026-01-01", closeDate="2026-01-03", listingDate="2026-01-08")
                record["documents"] = [{"type": "PROSPECTUS", "url": f"https://www.sebi.gov.in/files/{record['id']}.pdf"}]
                record["objectsOfIssueReview"] = {"status": "quarantined", "snapshot": {
                    "before": [{"purpose": "Unverified legacy allocation", "amountCr": 1}],
                }}
            data_file.write_text(json.dumps(initial))
        if untouched:
            initial = json.loads(data_file.read_text())
            initial["ipos"].append({"id": "untouched", "company": "Untouched Limited"})
            review.final_policy.apply_policy(initial)
            data_file.write_text(json.dumps(initial))

        def document(record):
            return {"url": f"https://www.sebi.gov.in/files/{record['id']}.pdf"}

        for identifier in ("first", "second"):
            url = document({"id": identifier})["url"]
            (cache / (hashlib.sha256(url.encode()).hexdigest() + ".pdf")).write_bytes(b"cached PDF")

        def collect(payload, **kwargs):
            for record in payload["ipos"]:
                if record["id"] == "untouched":
                    continue
                record["documentRepair"] = {"status": "updated"}
                record["dataReview"] = {"financials": "Annual financial table remains queued"}
                if invalid:
                    record["lotSize"] = -1

        def save(payload):
            data_file.write_text(json.dumps(payload))

        def collect_residuals(payload, **kwargs):
            self.assertEqual(kwargs["limit"], 2)
            self.assertEqual(kwargs["workers"], 3)
            self.assertIn("queue", kwargs["queue_payload"])
            self.assertTrue(all(row["documentRepair"]["status"] == "updated" for row in payload["ipos"][:2]))
            record = payload["ipos"][0]
            rows = [{"purpose": "Working capital", "amountCr": 10.0}]
            if unsupported:
                record["objectsOfIssue"] = rows
            else:
                review.final_policy.policy.apply_final_prospectus_static_fields(
                    record, objects_parsed(rows),
                    {"type": "PROSPECTUS", **document(record)}, sha256="source-bytes",
                )
            record["p4OfferResidualRepair"] = {"status": "updated", "changedFields": ["objectsOfIssue"]}
            kwargs["checkpoint"](payload)
            return {"attempted": 1, "changedFields": 1, "failed": 0}

        source_pages = [f"[PAGE {page}]\nneutral context" for page in range(1, 47)]
        for page in (1, 2, 45, 46):
            source_pages[page - 1] += f"\nFINANCIAL HEADER page {page}\nrow from page {page}"
        source_pages[2] += "\nFINANCIAL HEADER contents .... 45"
        text = "\f".join(source_pages)

        def diagnostic(data, *, page_limit):
            # A workflow cancellation during the first diagnostic must still
            # leave the report for every processed document on disk.
            saved = json.loads(report_file.read_text())
            self.assertEqual([row["id"] for row in saved["records"]], ["first", "second"])
            self.assertEqual(page_limit, 45)
            if interrupt:
                raise KeyboardInterrupt("diagnostics interrupted after completed collection")
            return text, 46, 46

        output = io.StringIO()
        with ExitStack() as stack:
            stack.enter_context(patch.object(review, "ROOT", root))
            stack.enter_context(patch.object(review.documents, "DATA_FILE", data_file))
            stack.enter_context(patch.object(review.documents, "CACHE", cache))
            stack.enter_context(patch.object(review.documents, "run", side_effect=collect))
            residual_run = stack.enter_context(patch.object(review.residuals, "run", side_effect=collect_residuals))
            stack.enter_context(patch.object(review.documents, "atomic_save", side_effect=save))
            stack.enter_context(patch.object(review.documents, "document_for", side_effect=document))
            stack.enter_context(patch.object(review.documents, "pdf_bytes", return_value=b"cached PDF"))
            stack.enter_context(patch.object(review.parser, "extract_pdf_text", side_effect=diagnostic))
            stack.enter_context(patch.object(review.parser, "_HEADING", re.compile(r"^FINANCIAL HEADER")))
            stack.enter_context(patch.object(sys, "argv", ["review_source_repairs.py"] + (["--residual-limit", "2"] if residual else [])))
            stack.enter_context(redirect_stdout(output))
            if interrupt:
                with self.assertRaises(KeyboardInterrupt):
                    review.main()
                result = None
            else:
                result = review.main()
            self.assertEqual(residual_run.call_count, 1 if residual else 0)
        return result, json.loads(report_file.read_text()), json.loads(data_file.read_text()), output.getvalue()

    def test_completed_report_survives_interrupted_optional_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            _, report, data, output = self.preview(directory, interrupt=True)
        self.assertEqual(report["before"]["errorCount"], 0)
        self.assertEqual(report["after"]["errorCount"], 0)
        self.assertEqual(report["after"]["reviewCount"], 2)
        self.assertEqual(len(report["records"]), 2)
        self.assertTrue(all(row["documentRepair"]["status"] == "updated" for row in data["ipos"]))
        self.assertIn("SOURCE_REVIEW_SUMMARY ", output)

    def test_bounded_diagnostics_preserve_excerpt_order_and_strict_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            result, report, _, output = self.preview(directory, invalid=True)
        self.assertEqual(result, 1)
        self.assertGreater(report["after"]["errorCount"], 0)
        layouts = [json.loads(line.removeprefix("SOURCE_LAYOUT "))
                   for line in output.splitlines() if line.startswith("SOURCE_LAYOUT ")]
        self.assertEqual(len(layouts), 2)
        for layout in layouts:
            self.assertEqual(len(layout["snippets"]), 3)
            for snippet, page in zip(layout["snippets"], (1, 2, 45)):
                self.assertIn(f"row from page {page}", snippet)
            self.assertNotIn("contents ....", "\n".join(layout["snippets"]))
            self.assertNotIn("row from page 46", "\n".join(layout["snippets"]))

    def test_residual_changes_are_in_complete_report_before_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            _, report, data, _ = self.preview(directory, residual=True, interrupt=True)
        self.assertEqual(report["residuals"], {"attempted": 1, "changedFields": 1, "failed": 0})
        self.assertEqual(report["records"][0]["objectsOfIssue"], data["ipos"][0]["objectsOfIssue"])
        self.assertEqual(report["records"][0]["residualRepair"]["changedFields"], ["objectsOfIssue"])
        self.assertEqual({k: v for k, v in report["after"].items() if k != "generatedAt"},
                         {k: v for k, v in review.validate_payload(data).items() if k != "generatedAt"})
        self.assertEqual(report["after"]["errorCount"], 0)

    def test_final_policy_runs_after_residuals_before_saved_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            result, report, data, _ = self.preview(directory, residual=True, unsupported=True)
        self.assertEqual(result, 0)
        self.assertIsNone(data["ipos"][0]["objectsOfIssue"])
        self.assertEqual(data["ipos"][0]["objectsOfIssueReview"]["status"], "quarantined")
        self.assertIsNone(report["records"][0]["objectsOfIssue"])
        self.assertEqual({k: v for k, v in report["after"].items() if k != "generatedAt"},
                         {k: v for k, v in review.validate_payload(data).items() if k != "generatedAt"})

    def test_new_residual_allocation_receives_document_review_before_report_and_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            _, report, data, _ = self.preview(directory, residual=True, reviewed=True, interrupt=True)
            queue = json.loads((Path(directory) / "data/missing_queue.json").read_text())
        row = data["ipos"][0]
        self.assertIsNone(row["objectsOfIssue"])
        held = row["objectsOfIssueReview"]
        self.assertEqual(held["status"], "quarantined")
        self.assertEqual(held["reviewKind"], "source-review")
        self.assertEqual(held["snapshot"]["reviewedSource"]["scope"], "document")
        self.assertEqual(held["snapshot"]["before"], [{"purpose": "Working capital", "amountCr": 10.0}])
        self.assertEqual(held["snapshot"]["sourceEvidence"]["sha256"], "source-bytes")
        self.assertNotIn("objectsOfIssue", row["staticFieldProvenance"])
        self.assertIsNone(report["records"][0]["objectsOfIssue"])
        self.assertEqual(report["residuals"]["changedFields"], 1)
        entry = next(item for item in queue["queue"] if item["id"] == "first")
        self.assertIn("offer.objectsOfIssue", entry["missingFields"])
        self.assertEqual({k: v for k, v in report["after"].items() if k != "generatedAt"},
                         {k: v for k, v in review.validate_payload(data).items() if k != "generatedAt"})

    def test_residual_preview_budget_cannot_be_unbounded(self):
        for value in ("-1", "31"):
            with patch.object(sys, "argv", ["review_source_repairs.py", "--residual-limit", value]), \
                 patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit) as raised:
                review.main()
            self.assertEqual(raised.exception.code, 2)

    def test_policy_timestamp_alone_does_not_enter_changed_record_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            result, report, data, output = self.preview(directory, residual=True, untouched=True)
        self.assertEqual(result, 0)
        self.assertEqual([row["id"] for row in report["records"]], ["first", "second"])
        self.assertEqual(len(data["ipos"]), 3)
        self.assertNotIn('"id": "untouched"', output)

    def test_saved_final_queue_removes_recovered_objects_and_keeps_held_objects(self):
        with tempfile.TemporaryDirectory() as directory:
            _, report, data, _ = self.preview(directory, residual=True, queue_case=True, interrupt=True)
            queue = json.loads((Path(directory) / "data/missing_queue.json").read_text())
        entries = {row["id"]: row for row in queue["queue"]}
        self.assertNotIn("offer.objectsOfIssue", entries["first"]["missingFields"])
        self.assertIn("offer.objectsOfIssue", entries["second"]["missingFields"])
        self.assertEqual(queue["recordCount"], len(data["ipos"]))
        self.assertEqual(queue["queueCount"], len(queue["queue"]))
        self.assertEqual(report["after"]["errorCount"], 0)


if __name__ == "__main__":
    unittest.main()
