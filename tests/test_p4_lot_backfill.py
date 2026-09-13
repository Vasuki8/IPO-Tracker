import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "backfill_p4_lot_sizes.py"
spec = importlib.util.spec_from_file_location("backfill_p4_lot_sizes", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class P4LotBackfillTests(unittest.TestCase):
    def test_p4_uses_independent_attempt_marker(self):
        self.assertEqual(mod.P4_ATTEMPT_KEY, "p4LotSizeBackfill")
        self.assertEqual(mod.base.ATTEMPT_KEY, mod.P4_ATTEMPT_KEY)
        self.assertNotEqual(mod.P4_ATTEMPT_KEY, "historicalDetailBackfill")

    def test_core_only_targets_lot_size_not_issue_size(self):
        lot_gap = {
            "openDate": "2026-08-01",
            "lotSize": None,
            "issueSizeCr": 250.0,
        }
        issue_size_only_gap = {
            "openDate": "2026-08-01",
            "lotSize": 100,
            "issueSizeCr": None,
        }
        today = date(2026, 9, 13)

        self.assertTrue(mod.is_candidate(lot_gap, today, 730, core_only=True))
        self.assertFalse(mod.is_candidate(issue_size_only_gap, today, 730, core_only=True))

    def test_p4_marker_does_not_inherit_archival_marker(self):
        record = {
            "openDate": "2026-08-01",
            "lotSize": None,
            "historicalDetailBackfill": {"lastAttemptAt": "2026-09-13T10:00:00+05:30"},
        }
        today = date(2026, 9, 13)

        self.assertFalse(mod.attempted_recently(record, today, 14))
        self.assertTrue(
            mod.is_candidate(record, today, 730, core_only=True, retry_days=14)
        )

    def test_mark_attempt_writes_p4_marker(self):
        record = {}
        mod.mark_attempt(
            record,
            status="validated",
            archive_url="https://www.bseindia.com/history",
            detail_url="https://www.bseindia.com/detail",
            changed_fields=[],
        )
        self.assertIn(mod.P4_ATTEMPT_KEY, record)
        self.assertNotIn("historicalDetailBackfill", record)


if __name__ == "__main__":
    unittest.main()
