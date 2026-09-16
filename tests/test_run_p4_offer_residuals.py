import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import p4_offer_parser as residual
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
            health = runner.run(payload, limit=30, workers=1)
        self.assertEqual(health["attempted"], 1)
        self.assertEqual(health["changedFields"], 1)
        self.assertEqual(health["outcomes"][0]["id"], "recent")


if __name__ == "__main__":
    unittest.main()
