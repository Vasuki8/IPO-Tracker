import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import p4_offer_layouts as residual
import run_p4_offer_residuals as runner


class P4OfferResidualRunnerTests(unittest.TestCase):
    def test_invalid_promoters_and_toc_objects_are_replaced_and_audited(self):
        record = {
            "id": "apexeco",
            "company": "Apex Ecotech Limited",
            "openDate": "2024-11-27",
            "leadManagers": ["Share India Capital Services Private Limited"],
            "promoters": ["namely Mr. Anuj Dosajh", "Mr. Ajay Raina", "Mr"],
            "objectsOfIssue": [
                {"purpose": "BASIS FOR ISSUE PRICE", "amountCr": 97.0},
                {"purpose": "OUR MANAGEMENT", "amountCr": 162.0},
            ],
        }
        parsed = {
            "leadManagers": copy.deepcopy(record["leadManagers"]),
            "promoters": ["Anuj Dosajh", "Ramakrishnan Balasundaram Aiyer", "Ajay Raina", "Lalit Mohan Datta"],
            "objectsOfIssue": [{"purpose": "Working Capital Requirements", "amountCr": 10.0}],
        }
        doc = {"url": "https://nsearchives.nseindia.com/emerge/corporates/content/ApexEcotechLimited_PROSP.pdf"}

        changed = runner._replace_invalid_residuals(record, parsed, doc, "hash")

        self.assertEqual(set(changed), {"promoters", "objectsOfIssue"})
        self.assertTrue(residual.valid_promoters(record["promoters"]))
        self.assertTrue(residual.valid_objects(record["objectsOfIssue"]))
        audited = {row["field"] for row in record["dataCorrections"]}
        self.assertEqual(audited, {"promoters", "objectsOfIssue"})
        self.assertTrue(all(row["sourceUrl"] == doc["url"] for row in record["dataCorrections"]))

    def test_good_existing_residual_fields_are_not_replaced(self):
        record = {
            "promoters": ["Anuj Dosajh", "Ajay Raina"],
            "objectsOfIssue": [{"purpose": "Working Capital Requirements", "amountCr": 10.0}],
        }
        before = copy.deepcopy(record)
        parsed = {
            "promoters": ["Other Person", "Another Person"],
            "objectsOfIssue": [{"purpose": "General Corporate Purposes", "amountCr": 5.0}],
        }
        changed = runner._replace_invalid_residuals(
            record,
            parsed,
            {"url": "https://nsearchives.nseindia.com/official.pdf"},
            "hash",
        )
        self.assertEqual(changed, [])
        self.assertEqual(record, before)

    def test_extract_uses_final_prospectus_parser_for_primary_fields(self):
        record = {
            "company": "Example Limited",
            "priceBand": {"min": 100.0, "max": 100.0},
        }
        doc = {"url": "https://nsearchives.nseindia.com/emerge/corporates/content/Example_PROSP.pdf"}
        text = "Example Limited\nFinal Prospectus"
        primary = {
            "issuePrice": 100.0,
            "issueComposition": {"freshIssueCr": 10.0, "ofsCr": 0.0, "totalIssueSizeCr": 10.0},
            "fieldEvidence": {"issuePrice": {"basis": "final prospectus issue price"}},
        }
        supplement = {
            "promoters": ["Valid Person"],
            "fieldEvidence": {"promoters": {"heading": "OUR PROMOTERS"}},
        }
        combined = {
            **primary,
            "promoters": supplement["promoters"],
            "fieldEvidence": {**primary["fieldEvidence"], **supplement["fieldEvidence"]},
        }

        with patch.object(runner.base, "pdf_bytes", return_value=b"%PDF-final"), patch.object(
            runner.parser, "extract_pdf_text", return_value=(text, 1, 1)
        ), patch.object(
            runner.parser, "parse_document_text", return_value=primary
        ) as parse_primary, patch.object(
            runner.residual, "parse_document_text", return_value=supplement
        ), patch.object(
            runner.residual, "merge_parsed", return_value=combined
        ):
            parsed, digest, pages, page_count = runner.extract(record, doc)

        self.assertEqual(runner.parser.__name__, "final_prospectus_parser")
        parse_primary.assert_called_once_with(text, record["priceBand"])
        self.assertEqual(parsed["issuePrice"], 100.0)
        self.assertEqual(parsed["issueComposition"]["freshIssueCr"], 10.0)
        self.assertEqual(parsed["promoters"], ["Valid Person"])
        self.assertEqual(pages, 1)
        self.assertEqual(page_count, 1)
        self.assertTrue(digest)

    def test_same_parser_and_document_are_throttled_after_attempt(self):
        record = {
            "id": "x",
            "company": "Example Limited",
            "openDate": "2026-01-01",
            "promoters": ["Mr"],
            "objectsOfIssue": [],
            "sources": [{"url": "https://nsearchives.nseindia.com/emerge/corporates/content/Example_PROSP.pdf"}],
            "p4OfferResidualRepair": {
                "parserVersion": residual.PARSER_VERSION,
                "mainParserVersion": runner.parser.PARSER_VERSION,
                "documentUrl": "https://nsearchives.nseindia.com/emerge/corporates/content/Example_PROSP.pdf",
            },
        }
        with patch.object(runner.base, "document_for", return_value={"url": record["p4OfferResidualRepair"]["documentUrl"]}):
            self.assertIsNone(runner._candidate(record, force=False))
            self.assertIsNotNone(runner._candidate(record, force=True))

    def test_verified_document_is_persisted_once(self):
        record = {"documents": []}
        doc = {
            "url": "https://nsearchives.nseindia.com/emerge/corporates/content/Example_PROSP.pdf",
            "type": "Prospectus",
            "title": "Example Limited Prospectus",
            "source": "NSE",
            "filedDate": "2026-01-05",
        }
        self.assertTrue(runner._retain_verified_document(record, doc, "abc123"))
        self.assertEqual(len(record["documents"]), 1)
        saved = record["documents"][0]
        self.assertEqual(saved["url"], doc["url"])
        self.assertEqual(saved["type"], "Prospectus")
        self.assertEqual(saved["sha256"], "abc123")
        self.assertFalse(runner._retain_verified_document(record, doc, "abc123"))
        self.assertEqual(len(record["documents"]), 1)

    def test_queue_order_targets_p4_offer_and_document_gaps_only(self):
        queue = {
            "queue": [
                {"id": "dhanlaxmi", "priority": 4, "missingFields": ["offer.registrar", "offer.financials"]},
                {"id": "lot-only", "priority": 4, "missingFields": ["exchange.lotSize"]},
                {"id": "history", "priority": 5, "missingFields": ["offer.financials"]},
                {"id": "credent", "priority": 4, "missingFields": ["provenance.documents"]},
            ]
        }
        self.assertEqual(runner.p4_offer_queue_order(queue), {"dhanlaxmi": 0, "credent": 3})

    def test_run_prioritizes_p4_offer_queue_before_newer_cleanup(self):
        payload = {
            "ipos": [
                {"id": "newer", "company": "Newer Limited", "openDate": "2026-08-01", "promoters": ["Mr"]},
                {"id": "dhanlaxmi", "company": "Dhanlaxmi Crop Science Limited", "openDate": "2024-12-09", "promoters": ["Mr"]},
                {"id": "middle", "company": "Middle Limited", "openDate": "2025-08-01", "promoters": ["Mr"]},
            ]
        }
        queue = {
            "queue": [
                {"id": "dhanlaxmi", "priority": 4, "missingFields": ["offer.registrar", "offer.financials"]},
            ]
        }
        doc = {"url": "https://nsearchives.nseindia.com/example.pdf"}
        attempted = []

        def fake_extract(record, _doc):
            attempted.append(record["id"])
            return {"promoters": ["Valid Person"], "leadManagers": [], "fieldEvidence": {}}, "hash", 1, 1

        with patch.object(runner.base, "document_for", return_value=doc), patch.object(
            runner, "extract", side_effect=fake_extract
        ), patch.object(runner, "apply_result", return_value=["promoters"]):
            health = runner.run(payload, limit=1, workers=1, queue_payload=queue)

        self.assertEqual(attempted, ["dhanlaxmi"])
        self.assertEqual(health["p4QueueTargets"], 1)
        self.assertEqual(health["p4QueueTargetsAttempted"], 1)

    def test_run_targets_only_recent_incomplete_records_with_documents(self):
        payload = {
            "ipos": [
                {"id": "recent", "company": "Recent Limited", "openDate": "2026-01-01", "promoters": ["Mr"]},
                {"id": "old", "company": "Old Limited", "openDate": "2020-01-01", "promoters": ["Mr"]},
            ]
        }
        doc = {"url": "https://nsearchives.nseindia.com/recent.pdf"}
        with patch.object(runner.base, "document_for", side_effect=lambda r: doc if r["id"] == "recent" else None), patch.object(
            runner, "extract", return_value=({"promoters": ["Valid Person"], "leadManagers": [], "fieldEvidence": {}}, "hash", 1, 1)
        ), patch.object(runner, "apply_result", return_value=["promoters"]):
            health = runner.run(payload, limit=30, workers=1, queue_payload={"queue": []})
        self.assertEqual(health["attempted"], 1)
        self.assertEqual(health["changedFields"], 1)
        self.assertEqual(health["outcomes"][0]["id"], "recent")


if __name__ == "__main__":
    unittest.main()
