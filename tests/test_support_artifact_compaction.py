import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load(name):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


queue = load("build_missing_queue")
performance = load("build_performance_summary")


class SupportArtifactCompactionTests(unittest.TestCase):
    def test_operational_queue_projection_keeps_consumer_fields(self):
        record = {
            "id": "sample",
            "company": "Sample Limited",
            "symbol": "SAMPLE",
            "board": "Mainboard",
            "exchange": "NSE",
            "openDate": "2026-01-01",
            "closeDate": "2026-01-03",
            "listingDate": "2026-01-10",
            "priceBand": {"min": 100, "max": 110},
            "lotSize": None,
            "issueSizeCr": None,
            "sources": [{"name": "NSE"}],
            "validation": {"status": "single-source"},
            "profilePath": "ipo/sample/",
        }
        rich = queue.queue_entry(record, date(2026, 9, 15))
        compact = queue.operational_queue_entry(rich)
        for field in ("id", "company", "priority", "priorityLabel", "missingFields", "missingFieldCount", "profilePath"):
            self.assertEqual(compact[field], rich[field])
        self.assertNotIn("symbol", compact)
        self.assertNotIn("closeDate", compact)
        self.assertNotIn("listingDate", compact)
        self.assertNotIn("expectedFieldCount", compact)
        self.assertNotIn("resolvedUnavailableFields", compact)

    def test_resolution_projection_keeps_index_but_not_duplicate_evidence(self):
        rich = {
            "id": "sample",
            "company": "Sample Limited",
            "symbol": "SAMPLE",
            "priority": 4,
            "priorityLabel": "P4 recent history (2y)",
            "resolvedFields": ["exchange.lotSize"],
            "resolutions": {"exchange.lotSize": {"status": "exhausted-official-sources", "reason": "long evidence"}},
            "profilePath": "ipo/sample/",
        }
        compact = queue.operational_resolved_entry(rich)
        self.assertEqual(compact["resolvedFields"], ["exchange.lotSize"])
        self.assertNotIn("resolutions", compact)
        self.assertNotIn("symbol", compact)

    def test_performance_report_keeps_denominators_and_omits_null_scaffolding(self):
        payload = {
            "ipos": [
                {"id": "a", "company": "A", "symbol": "A", "listingDate": "2026-01-01", "listing": {}},
                {
                    "id": "b", "company": "B", "symbol": "B", "listingDate": "2026-01-02",
                    "listing": {"issuePrice": 100},
                    "performance": {"latest": {"price": 125, "observedAt": "2026-09-15T10:00:00+05:30"}, "returnSinceIssuePct": 25},
                },
                {"id": "event", "company": "Event", "listingDate": "2026-01-03", "issueEventType": "special"},
            ]
        }
        report = performance.build_report(payload, generated_at="fixed")
        self.assertEqual(report["listedRecords"], 2)
        self.assertEqual(report["withFinalIssuePrice"], 1)
        self.assertEqual(report["withPriceObservation"], 1)
        empty_row = report["records"][0]
        self.assertNotIn("issuePrice", empty_row)
        self.assertNotIn("latest", empty_row)
        self.assertNotIn("returnSinceIssuePct", empty_row)
        self.assertNotIn("lastAttemptStatus", empty_row)
        populated = report["records"][1]
        self.assertEqual(populated["issuePrice"], 100)
        self.assertEqual(populated["returnSinceIssuePct"], 25)


if __name__ == "__main__":
    unittest.main()
