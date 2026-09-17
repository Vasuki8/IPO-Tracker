"""Verified issuer copies remain usable after failed exchange downloads."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import final_prospectus_identity as identity
from parser_loader import isolated_module


EXPECTED = {
    "sunshine": {
        "company": "Sunshine Pictures Limited",
        "url": "https://sunshinepictures.in/wp-content/uploads/2026/08/FinalSunshineProspectus-GYR.pdf",
        "host": "sunshinepictures.in",
        "sourcePage": "https://sunshinepictures.in/offer-documents/",
        "filedDate": "2026-08-21",
        "oldUrl": "https://www.bseindia.com/downloads/ipo/361148/ipo_T3/Prospectus_20260821184134.pdf",
    },
    "orklaindia": {
        "company": "Orkla India Limited",
        "url": "https://www.orklaindia.com/wp-content/uploads/sites/3/2025/11/Orkla-India-Limited-Prospectus.pdf",
        "host": "www.orklaindia.com",
        "sourcePage": "https://www.orklaindia.com/offer-documents/prospectus/",
        "filedDate": "2025-10-31",
        "oldUrl": "https://nsearchives.nseindia.com/corporate/FP_INE16NZ01023_03NOV2025.pdf",
    },
}


class IssuerProspectusFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = isolated_module("run_issuer_offer_docs")

    def record(self, record_id):
        expected = EXPECTED[record_id]
        return {
            "id": record_id,
            "company": expected["company"],
            "registrar": "Unverified legacy registrar",
            "documents": [{
                "type": "PROSPECTUS", "title": expected["company"] + " Final Prospectus",
                "url": expected["oldUrl"], "source": "Exchange archive",
            }],
            "documentRepair": {
                "status": "source_blocked", "sourceUrl": expected["oldUrl"],
                "error": "Prior exchange download failed",
            },
            "issuerDocumentExtraction": {
                "status": "extracted", "parserVersion": self.runner.parser.PARSER_VERSION,
                "documentType": "PROSPECTUS", "documentTitle": "Final Prospectus",
                "documentUrl": expected["oldUrl"],
            },
        }

    def queue(self, priority=4):
        return {"queue": [
            {"id": key, "company": expected["company"], "priority": priority,
             "missingFields": ["offer.registrar", "provenance.finalProspectus.registrar"]}
            for key, expected in EXPECTED.items()
        ]}

    def test_registry_points_to_explicit_final_issuer_documents(self):
        for key, expected in EXPECTED.items():
            with self.subTest(issuer=key):
                spec = self.runner.base.ISSUER_DOCUMENTS[key]
                for field in ("company", "url", "host", "sourcePage", "filedDate"):
                    self.assertEqual(spec[field], expected[field])
                self.assertTrue(self.runner.source_policy.is_final_prospectus(spec))
                self.assertTrue(self.runner.base._host_matches(spec["url"], spec["host"]))
                self.assertFalse(self.runner.base._host_matches(
                    "https://unrelated.example/" + spec["host"] + "/prospectus.pdf",
                    spec["host"],
                ))
                self.assertEqual(spec["sourceKind"], "issuer-filing")

    def test_registry_targets_unique_issuer_ids_from_committed_dataset(self):
        committed = json.loads((SCRIPTS.parent / "data" / "ipos.json").read_text(encoding="utf-8"))
        actual_records = []
        for expected_id, expected in EXPECTED.items():
            matches = [record for record in committed["ipos"]
                       if record.get("company") == expected["company"]]
            self.assertEqual(len(matches), 1, expected["company"])
            record = matches[0]
            self.assertEqual(record["id"], expected_id)
            self.assertIn(record["id"], self.runner.base.ISSUER_DOCUMENTS)
            actual_records.append(copy.deepcopy(record))
            if expected_id == "orklaindia":
                self.assertTrue(any(doc.get("url") == expected["oldUrl"]
                                    for doc in record.get("documents") or []))
        queue = {"queue": [
            {"id": record["id"], "company": record["company"], "priority": 4,
             "missingFields": ["provenance.finalProspectus.registrar"]}
            for record in actual_records
        ]}
        targets = self.runner._identity_safe_targets({"ipos": actual_records}, queue, 4, 2)
        self.assertEqual({record["id"] for record, _, _ in targets}, set(EXPECTED))
        for record, _item, spec in targets:
            self.assertEqual(spec["url"], EXPECTED[record["id"]]["url"])

    def test_old_extraction_and_failed_primary_cannot_hide_new_registry_copy(self):
        payload = {"ipos": [self.record(key) for key in EXPECTED]}
        selected = self.runner._identity_safe_targets(payload, self.queue(), 4, 2)
        self.assertEqual(len(selected), 2)
        for record, _item, spec in selected:
            self.assertEqual(spec["url"], EXPECTED[record["id"]]["url"])
            self.assertNotEqual(spec["url"], record["issuerDocumentExtraction"]["documentUrl"])

    def test_fallbacks_stay_out_of_p5_and_ambiguous_issuer_records(self):
        payload = {"ipos": [self.record(key) for key in EXPECTED]}
        before = copy.deepcopy(payload)
        self.assertEqual(self.runner._identity_safe_targets(payload, self.queue(5), 4, 2), [])
        self.assertEqual(payload, before)
        wrong = copy.deepcopy(payload)
        wrong["ipos"][0]["company"] = "Unrelated Pictures Limited"
        wrong["ipos"].append(copy.deepcopy(wrong["ipos"][1]))
        self.assertEqual(self.runner._identity_safe_targets(wrong, self.queue(), 4, 2), [])

    def test_new_registry_entries_cannot_bypass_final_only_gate(self):
        specs = copy.deepcopy(self.runner.base.ISSUER_DOCUMENTS)
        for key in EXPECTED:
            specs[key]["type"] = "RHP"
            specs[key]["title"] = "Red Herring Prospectus"
        with mock.patch.dict(self.runner.base.ISSUER_DOCUMENTS, specs, clear=True):
            payload = {"ipos": [self.record(key) for key in EXPECTED]}
            self.assertEqual(self.runner._identity_safe_targets(payload, self.queue(), 4, 2), [])

    def test_successful_fallback_retains_issuer_page_date_and_original_document(self):
        for key, expected in EXPECTED.items():
            with self.subTest(issuer=key):
                record = self.record(key)
                spec = self.runner.base.ISSUER_DOCUMENTS[key]
                self.runner._record_document_metadata(record, spec)
                added = next(doc for doc in record["documents"] if doc["url"] == spec["url"])
                self.assertEqual(added["sourcePage"], expected["sourcePage"])
                self.assertEqual(added["filedDate"], expected["filedDate"])
                self.assertEqual(added["source"], "Issuer website")
                self.assertTrue(any(doc["url"] == expected["oldUrl"] for doc in record["documents"]))
                chosen = identity.choose_candidate(
                    record, self.runner.source_policy.final_prospectus_candidates(record)
                )
                self.assertEqual(chosen["url"], spec["url"])
                added["retainedNote"] = "keep existing document metadata"
                self.runner._record_document_metadata(record, spec)
                self.assertEqual(len(record["documents"]), 2)
                self.assertEqual(record["documents"][1]["retainedNote"], "keep existing document metadata")

    def test_runner_repairs_both_records_via_new_issuer_specs_with_source_proof(self):
        payload = {"meta": {}, "ipos": [self.record(key) for key in EXPECTED]}
        pdf = b"%PDF mocked transport; issuer text is supplied by the extractor"
        parsed = {"registrar": "Verified Issuer Registrar", "extractedFields": ["registrar"]}
        identity_text = "PROSPECTUS\nSUNSHINE PICTURES LIMITED\nORKLA INDIA LIMITED"
        with tempfile.TemporaryDirectory() as directory:
            data_file = Path(directory) / "ipos.json"
            queue_file = Path(directory) / "queue.json"
            data_file.write_text(json.dumps(payload), encoding="utf-8")
            queue_file.write_text(json.dumps(self.queue()), encoding="utf-8")
            with (
                mock.patch.object(self.runner.base, "DATA_FILE", data_file),
                mock.patch.object(self.runner.base, "QUEUE_FILE", queue_file),
                mock.patch.object(self.runner.parser, "download_pdf", return_value=pdf) as download,
                mock.patch.object(self.runner.parser.base, "extract_pdf_text",
                                  return_value=(identity_text, 30, 472)),
                mock.patch.object(self.runner.parser, "parse_document_text", return_value=parsed),
                mock.patch.object(sys, "argv", ["run_issuer_offer_docs.py", "--priority-max", "4", "--limit", "2"]),
            ):
                self.assertEqual(self.runner.main(), 0)
            updated = json.loads(data_file.read_text(encoding="utf-8"))
        self.assertEqual([call.args[1] for call in download.call_args_list],
                         [expected["url"] for expected in EXPECTED.values()])
        self.assertEqual(updated["meta"]["issuerOfferDocumentHealth"]["failed"], 0)
        self.assertEqual(updated["meta"]["issuerOfferDocumentHealth"]["updated"], 2)
        for record in updated["ipos"]:
            expected = EXPECTED[record["id"]]
            self.assertEqual(record["registrar"], "Verified Issuer Registrar")
            proof = record["staticFieldProvenance"]["registrar"]
            self.assertEqual(proof["sourceUrl"], expected["url"])
            self.assertEqual(proof["sha256"], hashlib.sha256(pdf).hexdigest())
            extraction = record["issuerDocumentExtraction"]
            self.assertEqual(extraction["sourcePage"], expected["sourcePage"])
            self.assertEqual(extraction["documentUrl"], expected["url"])
            self.assertEqual(extraction["sourcePolicy"], "final-prospectus-only")
            self.assertIn("registrar", extraction["canonicalFields"])

    def test_opening_page_identity_failure_cannot_write_fields(self):
        self.assertFalse(self.runner.base._identity_matches(
            "Sunshine Pictures Limited", "PROSPECTUS\nUNRELATED INDUSTRIES LIMITED"
        ))
        self.assertFalse(self.runner.base._identity_matches(
            "Orkla India Limited", "PROSPECTUS\nUNRELATED INDUSTRIES LIMITED"
        ))


if __name__ == "__main__":
    unittest.main()
