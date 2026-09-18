import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_missing_queue as queue_builder
import enrich_issuer_offer_docs as legacy_issuer
import run_issuer_offer_docs as issuer
import run_offer_documents as primary
import run_p4_offer_residuals as residual
from source_review_queue import review_task


class SourceReviewSelectorTests(unittest.TestCase):
    def row(self, field="financials.FY2025.ebitdaCr", priority=4):
        record = {"id": "ardee", "company": "Ardee Industries Limited", "documents": []}
        return queue_builder.operational_queue_entry({
            **record, "priority": priority, "missingFields": [], "missingFieldCount": 0,
            "sourceReviewCount": 1,
            "sourceReviewItems": [review_task(record, {"field": field, "reason": "Needs source review"})],
        }, [])

    def test_residual_admits_review_only_record_but_preserves_retry_and_p5_bounds(self):
        row = self.row()
        queue = {"queue": [row, {**row, "id": "older", "priority": 5}, self.row("listingDate")]}
        self.assertEqual(residual.p4_offer_queue_order(queue), {"ardee": 0})
        spec = issuer.base.ISSUER_DOCUMENTS["ardee"]
        record = {"id": "ardee", "company": spec["company"]}
        with patch.object(residual.base, "document_for", return_value=spec):
            self.assertIsNotNone(residual._candidate(record, False, queue_target=True))
            record["p4OfferResidualRepair"] = {
                "parserVersion": residual.residual.PARSER_VERSION,
                "mainParserVersion": residual.parser.PARSER_VERSION,
                "documentUrl": spec["url"],
            }
            self.assertIsNone(residual._candidate(record, False, queue_target=True))
            record["p4OfferResidualRepair"]["mainParserVersion"] -= 1
            self.assertIsNotNone(residual._candidate(record, False, queue_target=True))

    def test_issuer_review_route_selects_eligible_document_without_repeating_current_version(self):
        spec = issuer.base.ISSUER_DOCUMENTS["ardee"]
        record = {"id": "ardee", "company": spec["company"]}
        row = self.row()
        queue = {"queue": [row]}
        self.assertFalse(legacy_issuer._has_priority_gap(row))
        self.assertEqual(legacy_issuer._needs_deep_scan(row, {}), (False, False))
        self.assertTrue(issuer._has_priority_or_revalidation_gap(row))
        self.assertEqual(len(issuer._identity_safe_targets({"ipos": [record]}, queue, 4, 10)), 1)
        self.assertEqual(issuer._needs_deep_scan_with_revalidation(row, {}), (True, False))
        record["issuerDocumentExtraction"] = {
            "status": "extracted", "parserVersion": issuer.base.PARSER_VERSION,
            "documentUrl": spec["url"], "documentType": "PROSPECTUS", "documentTitle": "Final Prospectus",
        }
        self.assertEqual(issuer._identity_safe_targets({"ipos": [record]}, queue, 4, 10), [])
        self.assertEqual(issuer._identity_safe_targets({"ipos": [record]}, {"queue": [self.row(priority=5)]}, 4, 10), [])

    def test_primary_parses_eligible_review_only_record_and_defers_current_version(self):
        spec = issuer.base.ISSUER_DOCUMENTS["ardee"]
        record = {"id": "ardee", "company": spec["company"], "documents": [spec]}
        queue = {"queue": [self.row(), {**self.row("listingDate"), "id": "manual"}]}
        with tempfile.TemporaryDirectory() as tmp:
            queue_file = Path(tmp) / "queue.json"
            queue_file.write_text(json.dumps(queue))
            with patch.object(primary, "QUEUE_FILE", queue_file):
                priorities = primary._load_queue_priorities()
                self.assertIn(primary._priority_key(record), priorities)
                self.assertNotIn(("manual", primary.core.canonical_company(spec["company"])), priorities)
                with patch.object(primary, "extract", return_value=({}, "hash", 1, 1)) as extract, patch.object(primary, "correct_record", return_value=[]):
                    health = primary.run({"ipos": [copy.deepcopy(record)]}, workers=1, priority_max=4)
                    self.assertEqual(health["attempted"], 1)
                    self.assertEqual(extract.call_count, 1)
                    record["offerDocumentExtraction"] = {
                        "status": "extracted", "parserVersion": primary.parser.PARSER_VERSION,
                        "documentUrl": spec["url"], "documentType": "PROSPECTUS", "documentTitle": "Final Prospectus",
                        "conflicts": ["FY2025.ebitdaCr"],
                    }
                    deferred = primary.run({"ipos": [record]}, workers=1, priority_max=4)
                    self.assertEqual(deferred["attempted"], 0)
                    self.assertEqual(extract.call_count, 1)


if __name__ == "__main__":
    unittest.main()
