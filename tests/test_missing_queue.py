import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

MODULE = SCRIPTS / "build_missing_queue.py"
spec = importlib.util.spec_from_file_location("build_missing_queue", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class MissingQueueTests(unittest.TestCase):
    def test_open_issue_gets_highest_priority(self):
        record = {
            "id": "open",
            "company": "Open Limited",
            "symbol": "OPEN",
            "board": "Mainboard",
            "exchange": "NSE",
            "openDate": "2026-09-10",
            "closeDate": "2026-09-14",
            "priceBand": {"min": 100, "max": 110},
            "lotSize": 100,
            "issueSizeCr": 500,
            "freshIssueCr": 500,
            "sources": [{"name": "NSE"}],
            "validation": {"status": "single-source"},
        }
        entry = mod.queue_entry(record, date(2026, 9, 12))
        self.assertEqual(entry["priority"], 0)
        self.assertIn("subscription.qib", entry["missingFields"])
        self.assertIn("subscription.total", entry["missingFields"])

    def test_draft_filing_is_not_penalized_for_exchange_terms(self):
        record = {
            "id": "draft",
            "company": "Draft Limited",
            "lifecycle": {"stage": "drhp"},
            "documents": [{"type": "DRHP", "url": "https://example.test/drhp.pdf"}],
            "sources": [{"name": "SEBI"}],
            "validation": {"status": "single-source"},
        }
        entry = mod.queue_entry(record, date(2026, 9, 12))
        self.assertIsNone(entry)

    def test_matured_issue_requires_listing_but_not_optional_allotment(self):
        record = {
            "id": "closed",
            "company": "Closed Limited",
            "symbol": "CLOSED",
            "board": "SME",
            "exchange": "NSE",
            "openDate": "2026-07-01",
            "closeDate": "2026-07-03",
            "priceBand": {"min": 50, "max": 55},
            "lotSize": 2000,
            "issueSizeCr": 40,
            "freshIssueCr": 40,
            "sources": [{"name": "NSE"}],
            "validation": {"status": "single-source"},
        }
        entry = mod.queue_entry(record, date(2026, 9, 12))
        self.assertNotIn("lifecycle.allotmentDate", entry["missingFields"])
        self.assertIn("lifecycle.listingDate", entry["missingFields"])

    def test_old_exchange_record_does_not_queue_archival_issue_composition(self):
        record = {
            "id": "old",
            "company": "Old Limited",
            "symbol": "OLD",
            "board": "Mainboard",
            "exchange": "NSE",
            "openDate": "2018-01-01",
            "closeDate": "2018-01-03",
            "listingDate": "2018-01-10",
            "priceBand": {"min": 100, "max": 110},
            "lotSize": None,
            "issueSizeCr": None,
            "sources": [{"name": "NSE"}],
            "validation": {"status": "single-source"},
        }
        entry = mod.queue_entry(record, date(2026, 9, 12))
        self.assertNotIn("exchange.issueComposition", entry["missingFields"])
        self.assertIn("exchange.lotSize", entry["missingFields"])
        self.assertIn("exchange.issueSizeCr", entry["missingFields"])

    def test_legacy_exchange_record_does_not_require_documents(self):
        record = {
            "id": "old-complete",
            "company": "Old Complete Limited",
            "symbol": "OLDC",
            "board": "Mainboard",
            "exchange": "NSE",
            "openDate": "2018-01-01",
            "closeDate": "2018-01-03",
            "listingDate": "2018-01-10",
            "priceBand": {"min": 100, "max": 110},
            "lotSize": 100,
            "issueSizeCr": 500,
            "sources": [{"name": "NSE"}],
            "validation": {"status": "single-source"},
        }
        self.assertIsNone(mod.queue_entry(record, date(2026, 9, 12)))

    def test_queue_sorts_open_before_history(self):
        today = date(2026, 9, 12)
        common = {
            "board": "Mainboard",
            "exchange": "NSE",
            "priceBand": {"min": 100, "max": 110},
            "sources": [{"name": "NSE"}],
            "validation": {"status": "single-source"},
        }
        records = [
            {**common, "id": "old", "company": "Old", "symbol": "OLD", "openDate": "2020-01-01", "closeDate": "2020-01-03"},
            {**common, "id": "open", "company": "Open", "symbol": "OPEN", "openDate": "2026-09-10", "closeDate": "2026-09-14"},
        ]
        queue = mod.build_queue(records, today)
        self.assertEqual(queue[0]["id"], "open")


if __name__ == "__main__":
    unittest.main()
