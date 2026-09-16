import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import p4_offer_layouts as residual
import run_p4_offer_residuals as runner


class HigherPriorityFinalResidualTests(unittest.TestCase):
    def test_queue_targets_all_pre_p5_final_residuals_only(self):
        queue = {
            "queue": [
                {"id": "open-final", "priority": 0, "missingFields": ["provenance.finalProspectus.lotSize"]},
                {"id": "recent-final", "priority": 2, "missingFields": ["provenance.finalProspectus.issueComposition"]},
                {"id": "history-p4", "priority": 4, "missingFields": ["offer.financials"]},
                {"id": "exchange-only", "priority": 2, "missingFields": ["exchange.lotSize"]},
                {"id": "p5-final", "priority": 5, "missingFields": ["provenance.finalProspectus.lotSize"]},
            ]
        }

        self.assertEqual(
            runner.p4_offer_queue_order(queue),
            {"open-final": 0, "recent-final": 1, "history-p4": 2},
        )

    def test_p2_final_only_gap_bypasses_generic_residual_predicates(self):
        record = {
            "id": "recent-final",
            "company": "Recent Final Limited",
            "openDate": "2026-09-01",
            "registrar": "Bigshare Services Private Limited",
            "leadManagers": ["Example Capital Limited"],
            "promoters": ["Valid Person"],
            "objectsOfIssue": [{"purpose": "Working Capital Requirements", "amountCr": 10.0}],
            "financials": {
                "periods": [
                    {"period": "FY2025", "revenueCr": 10.0},
                    {"period": "FY2024", "revenueCr": 9.0},
                ]
            },
            "shareholding": {"promoterPreIssuePct": 70.0},
            "documentFieldProvenance": {"registrar": {"documentUrl": "https://example.test/old.pdf"}},
        }
        self.assertFalse(residual.needs_repair(record))
        payload = {"ipos": [record]}
        queue = {
            "queue": [
                {
                    "id": "recent-final",
                    "priority": 2,
                    "missingFields": ["provenance.finalProspectus.lotSize"],
                }
            ]
        }
        doc = {
            "type": "PROSPECTUS",
            "title": "Recent Final Limited Final Prospectus",
            "url": "https://nsearchives.nseindia.com/corporate/FP_RECENT.pdf",
        }

        with patch.object(runner.base, "document_for", return_value=doc), patch.object(
            runner, "extract", return_value=({"lotSize": 100, "fieldEvidence": {}}, "hash", 1, 1)
        ), patch.object(runner, "apply_result", return_value=["lotSize"]):
            health = runner.run(payload, limit=1, workers=1, queue_payload=queue)

        self.assertEqual(health["p4QueueTargets"], 1)
        self.assertEqual(health["p4QueueTargetsAttempted"], 1)
        self.assertEqual(health["attempted"], 1)
        self.assertEqual(health["outcomes"][0]["id"], "recent-final")
        self.assertTrue(health["outcomes"][0]["p4QueueTarget"])


if __name__ == "__main__":
    unittest.main()
