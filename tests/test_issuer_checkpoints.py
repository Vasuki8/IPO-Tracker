"""Completed issuer repairs survive interruption of a later document."""
import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import requests

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from parser_loader import isolated_module


class IssuerCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = isolated_module("run_issuer_offer_docs")

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.data_file = Path(self.directory.name) / "ipos.json"
        self.queue_file = Path(self.directory.name) / "queue.json"
        self.specs = {
            key: {
                "company": f"{name} Industries Limited",
                "url": f"https://{key}.example/prospectus.pdf",
                "host": f"{key}.example",
                "type": "PROSPECTUS",
                "title": "Final Prospectus",
                "sourcePage": f"https://{key}.example/offer-documents/",
            }
            for key, name in (("alpha", "Alpha"), ("beta", "Beta"))
        }
        self.original = {
            "meta": {"retained": "unrelated metadata"},
            "ipos": [
                {"id": key, "company": spec["company"], "registrar": None}
                for key, spec in self.specs.items()
            ] + [{"id": "unselected", "company": "Untouched Limited", "retained": True}],
        }
        self.queue = {
            "queue": [
                {"id": key, "company": spec["company"], "priority": 4,
                 "missingFields": ["offer.registrar"]}
                for key, spec in self.specs.items()
            ]
        }
        self.data_file.write_text(json.dumps(self.original), encoding="utf-8")
        self.queue_file.write_text(json.dumps(self.queue), encoding="utf-8")
        self.pdf = b"%PDF fixture; extraction is supplied by the test"
        self.output = io.StringIO()
        self.errors = io.StringIO()

    @contextmanager
    def mocked_sources(self, effects):
        text = "PROSPECTUS\nALPHA INDUSTRIES LIMITED\nBETA INDUSTRIES LIMITED"
        parsed = {"registrar": "Verified Issuer Registrar", "extractedFields": ["registrar"]}
        with (
            mock.patch.object(self.runner.base, "DATA_FILE", self.data_file),
            mock.patch.object(self.runner.base, "QUEUE_FILE", self.queue_file),
            mock.patch.dict(self.runner.base.ISSUER_DOCUMENTS, self.specs, clear=True),
            mock.patch.object(self.runner.parser, "download_pdf", side_effect=effects) as download,
            mock.patch.object(self.runner.parser.base, "extract_pdf_text",
                              return_value=(text, 30, 30)),
            mock.patch.object(self.runner.parser, "parse_document_text", return_value=parsed),
            mock.patch.object(requests.sessions.Session, "request",
                              side_effect=AssertionError("Network access is forbidden")),
            mock.patch.object(sys, "argv", ["run_issuer_offer_docs.py", "--priority-max", "4", "--limit", "2"]),
            redirect_stdout(self.output),
            redirect_stderr(self.errors),
        ):
            yield download

    def stored(self):
        return json.loads(self.data_file.read_text(encoding="utf-8"))

    def test_later_interruption_preserves_completed_value_and_matching_proof(self):
        with self.mocked_sources([self.pdf, KeyboardInterrupt("later document stopped")]):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.main()

        saved = self.stored()
        first = saved["ipos"][0]
        self.assertEqual(first["registrar"], "Verified Issuer Registrar")
        proof = first["staticFieldProvenance"]["registrar"]
        self.assertEqual(proof["value"], first["registrar"])
        self.assertEqual(proof["sourceUrl"], self.specs["alpha"]["url"])
        self.assertEqual(proof["sha256"], hashlib.sha256(self.pdf).hexdigest())
        extraction = first["issuerDocumentExtraction"]
        self.assertEqual(extraction["documentUrl"], proof["sourceUrl"])
        self.assertEqual(extraction["sha256"], proof["sha256"])
        self.assertIn("registrar", extraction["canonicalFields"])
        self.assertEqual(saved["ipos"][1:], self.original["ipos"][1:])
        self.assertEqual(saved["meta"]["retained"], self.original["meta"]["retained"])
        health = saved["meta"]["issuerOfferDocumentHealth"]
        self.assertEqual((health["status"], health["selected"], health["remaining"]),
                         ("in_progress", 2, 1))
        self.assertEqual((health["attempted"], health["extracted"], health["updated"], health["failed"]),
                         (1, 1, 1, 0))
        self.assertEqual([(row["id"], row["status"]) for row in health["outcomes"]],
                         [("alpha", "updated")])
        self.assertEqual(saved["meta"]["sourceHealth"]["Issuer-offer-docs"]["remaining"], 1)

    def test_later_interruption_preserves_failure_for_retry_ordering(self):
        with self.mocked_sources([requests.ReadTimeout("issuer timed out"), KeyboardInterrupt()]):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.main()
            saved = self.stored()
            selected = self.runner._identity_safe_targets(saved, self.queue, 4, 2)

        self.assertEqual(saved["ipos"], self.original["ipos"])
        health = saved["meta"]["issuerOfferDocumentHealth"]
        self.assertEqual((health["attempted"], health["failed"], health["remaining"]), (1, 1, 1))
        self.assertFalse(health["ok"])
        self.assertEqual(health["errors"], ["Alpha Industries Limited: issuer timed out"])
        self.assertEqual(health["outcomes"][0]["status"], "failed")
        self.assertEqual([record["id"] for record, _item, _spec in selected], ["beta", "alpha"])

    def test_checkpoint_disk_failure_stops_without_reporting_a_source_failure(self):
        before = self.data_file.read_bytes()
        with self.mocked_sources([self.pdf, self.pdf]) as download:
            with mock.patch.object(Path, "replace", side_effect=OSError("checkpoint disk failure")):
                with self.assertRaisesRegex(OSError, "checkpoint disk failure"):
                    self.runner.main()
        self.assertEqual(download.call_count, 1)
        self.assertEqual(self.data_file.read_bytes(), before)
        self.assertEqual(self.stored(), self.original)
        self.assertNotIn("fallback failed", self.errors.getvalue())
        self.assertNotIn("Issuer offer docs: attempted=", self.output.getvalue())

    def test_failed_metadata_merge_rolls_back_policy_writes_before_checkpoint(self):
        with self.mocked_sources([self.pdf, KeyboardInterrupt()]):
            with mock.patch.object(self.runner, "_record_document_metadata",
                                   side_effect=ValueError("metadata merge failed")):
                with self.assertRaises(KeyboardInterrupt):
                    self.runner.main()
        saved = self.stored()
        self.assertEqual(saved["ipos"], self.original["ipos"])
        self.assertNotIn("staticFieldProvenance", saved["ipos"][0])
        self.assertNotIn("issuerDocumentExtraction", saved["ipos"][0])
        health = saved["meta"]["issuerOfferDocumentHealth"]
        self.assertEqual((health["attempted"], health["extracted"], health["updated"], health["failed"]),
                         (1, 0, 0, 1))
        self.assertEqual(health["errors"], ["Alpha Industries Limited: metadata merge failed"])

    def test_interruption_preserves_unattempted_prior_failure_retry_penalty(self):
        self.specs["gamma"] = {
            "company": "Gamma Industries Limited",
            "url": "https://gamma.example/prospectus.pdf",
            "host": "gamma.example",
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
        }
        self.original["ipos"].append({"id": "gamma", "company": "Gamma Industries Limited", "registrar": None})
        self.original["meta"]["issuerOfferDocumentHealth"] = {
            "errors": ["Alpha Industries Limited: prior timeout"],
        }
        self.queue["queue"].append({
            "id": "gamma", "company": "Gamma Industries Limited", "priority": 4,
            "missingFields": ["offer.registrar"],
        })
        self.data_file.write_text(json.dumps(self.original), encoding="utf-8")
        self.queue_file.write_text(json.dumps(self.queue), encoding="utf-8")
        with self.mocked_sources([self.pdf, KeyboardInterrupt()]) as download:
            with self.assertRaises(KeyboardInterrupt):
                self.runner.main()
            saved = self.stored()
            selected = self.runner._identity_safe_targets(saved, self.queue, 4, 2)
        self.assertEqual([call.args[1] for call in download.call_args_list],
                         [self.specs["beta"]["url"], self.specs["gamma"]["url"]])
        health = saved["meta"]["issuerOfferDocumentHealth"]
        self.assertEqual((health["failed"], health["errors"]), (0, []))
        self.assertEqual(health["retryErrors"], ["Alpha Industries Limited: prior timeout"])
        self.assertEqual([record["id"] for record, _item, _spec in selected], ["gamma", "alpha"])

    def test_final_checkpoint_marks_all_outcomes_completed(self):
        self.original["meta"]["issuerOfferDocumentHealth"] = {
            "retryErrors": ["Alpha Industries Limited: prior timeout"],
        }
        self.data_file.write_text(json.dumps(self.original), encoding="utf-8")
        # Keep the source order fixed here so the test checks that a successful
        # retry clears its old error while a new failed attempt is retained.
        with self.mocked_sources([self.pdf, requests.ReadTimeout("issuer timed out")]):
            with mock.patch.object(self.runner.base, "_targets", side_effect=lambda payload, *_args: [
                (payload["ipos"][index], self.queue["queue"][index], spec)
                for index, spec in enumerate(self.specs.values())
            ]):
                self.assertEqual(self.runner.main(), 0)
        health = self.stored()["meta"]["issuerOfferDocumentHealth"]
        self.assertEqual((health["status"], health["selected"], health["remaining"]),
                         ("completed", 2, 0))
        self.assertEqual((health["attempted"], health["extracted"], health["failed"]), (2, 1, 1))
        self.assertEqual([row["status"] for row in health["outcomes"]], ["updated", "failed"])
        self.assertEqual(health["retryErrors"], ["Beta Industries Limited: issuer timed out"])

    def test_zero_targets_still_publishes_completed_health(self):
        self.queue_file.write_text(json.dumps({"queue": []}), encoding="utf-8")
        with self.mocked_sources([]) as download:
            self.assertEqual(self.runner.main(), 0)
        saved = self.stored()
        self.assertEqual(saved["ipos"], self.original["ipos"])
        self.assertEqual(download.call_count, 0)
        health = saved["meta"]["issuerOfferDocumentHealth"]
        self.assertEqual((health["status"], health["selected"], health["remaining"], health["attempted"]),
                         ("completed", 0, 0, 0))
        self.assertTrue(health["ok"])
        self.assertEqual(health["outcomes"], [])

    def test_plain_legacy_main_remains_callable_without_checkpoint(self):
        with self.mocked_sources([self.pdf, self.pdf]):
            self.assertEqual(self.runner.base.main(), 0)
        health = self.stored()["meta"]["issuerOfferDocumentHealth"]
        self.assertEqual((health["status"], health["attempted"], health["remaining"]),
                         ("completed", 2, 0))


if __name__ == "__main__":
    unittest.main()
