import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import phase_status


class PhaseStatusReviewScopeTests(unittest.TestCase):
    @staticmethod
    def queue(*rows):
        return {"queue": list(rows), "resolvedUnavailableRecordCount": 0}

    @staticmethod
    def validation(*issues, error_count=0, review_count=None):
        if review_count is None:
            review_count = sum(item.get("severity") == "review" for item in issues)
        return {
            "errorCount": error_count,
            "reviewCount": review_count,
            "issues": list(issues),
        }

    def test_p5_only_review_does_not_block_p5(self):
        queue = self.queue({"id": "historical", "priority": 5, "missingFields": ["offer.financials"]})
        validation = self.validation(
            {"id": "historical", "field": "financials.FY2023.revenueCr", "severity": "review", "reason": "needs source evidence"}
        )

        result = phase_status.status(queue, validation)

        self.assertEqual(result["p4"]["status"], "complete")
        self.assertEqual(result["p5"]["status"], "enabled")
        self.assertEqual(result["p4"]["sourceReviewItems"], 1)
        self.assertEqual(result["p4"]["blockingSourceReviewItems"], 0)
        self.assertEqual(result["p4"]["p5OnlySourceReviewItems"], 1)

    def test_p0_to_p4_review_still_blocks_p5(self):
        for priority in (0, 1, 2, 4):
            with self.subTest(priority=priority):
                queue = self.queue({"id": "blocking", "priority": priority, "missingFields": []})
                validation = self.validation(
                    {"id": "blocking", "field": "listing.issuePrice", "severity": "review", "reason": "needs source evidence"}
                )
                result = phase_status.status(queue, validation)
                self.assertEqual(result["p4"]["status"], "incomplete")
                self.assertEqual(result["p5"]["status"], "waiting_for_p4")
                self.assertEqual(result["p4"]["blockingSourceReviewItems"], 1)

    def test_unmapped_review_fails_closed(self):
        queue = self.queue({"id": "historical", "priority": 5, "missingFields": []})
        validation = self.validation(
            {"id": "not-in-queue", "field": "registrar", "severity": "review", "reason": "needs source evidence"}
        )

        result = phase_status.status(queue, validation)

        self.assertEqual(result["p5"]["status"], "waiting_for_p4")
        self.assertEqual(result["p4"]["blockingSourceReviewItems"], 1)
        self.assertEqual(result["p4"]["unmappedSourceReviewItems"], 1)

    def test_aggregate_only_legacy_review_count_fails_closed(self):
        queue = self.queue({"id": "historical", "priority": 5, "missingFields": []})
        validation = self.validation(review_count=2)

        result = phase_status.status(queue, validation)

        self.assertEqual(result["p5"]["status"], "waiting_for_p4")
        self.assertEqual(result["p4"]["blockingSourceReviewItems"], 2)
        self.assertEqual(result["p4"]["unmappedSourceReviewItems"], 2)

    def test_structural_error_remains_global_blocker(self):
        queue = self.queue({"id": "historical", "priority": 5, "missingFields": []})
        validation = self.validation(error_count=1)

        result = phase_status.status(queue, validation)

        self.assertEqual(result["p4"]["status"], "incomplete")
        self.assertEqual(result["p5"]["status"], "waiting_for_p4")
        self.assertEqual(result["p4"]["semanticErrors"], 1)


if __name__ == "__main__":
    unittest.main()
