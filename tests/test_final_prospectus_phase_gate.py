import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_missing_queue as queue_builder
import phase_status
import run_issuer_offer_docs as issuer_runner


class FinalProspectusPhaseGateTests(unittest.TestCase):
    def _complete_recent_record(self):
        return {
            "id": "recent", "company": "Recent Limited", "symbol": "RECENT", "board": "Mainboard", "exchange": "NSE",
            "openDate": "2026-04-01", "closeDate": "2026-04-03", "listingDate": "2026-04-10",
            "priceBand": {"min": 100, "max": 110}, "lotSize": 100, "issueSizeCr": 500, "freshIssueCr": 500,
            "issueComposition": {"freshIssueCr": 500, "ofsCr": 0}, "leadManagers": ["Example Capital Advisors Limited"],
            "registrar": "Example Technologies Limited", "promoters": ["Example Promoter"],
            "financials": {"periods": [{"period": "FY2025", "revenueCr": 100}]},
            "objectsOfIssue": [{"purpose": "Working capital", "amountCr": 100}], "shareholding": {"promoterPreIssuePct": 75},
            "sources": [{"name": "NSE"}],
            "documents": [{"type": "PROSPECTUS", "title": "Final Prospectus", "url": "https://www.sebi.gov.in/files/final.pdf"}],
            "validation": {"status": "single-source"},
        }

    def _pending_record(self, *, close_date="2026-04-03", listing_date=None, with_final=False):
        record = self._complete_recent_record()
        record["closeDate"] = close_date
        record["listingDate"] = listing_date
        record["documents"] = ([{"type": "PROSPECTUS", "title": "Final Prospectus", "url": "https://www.sebi.gov.in/files/final.pdf"}] if with_final else [])
        record["staticSourcePolicy"] = {"policy": "final-prospectus-only", "pendingRevalidationFields": ["lotSize", "financials"]}
        return record

    def test_populated_legacy_static_field_enters_queue_until_revalidated(self):
        record = self._complete_recent_record()
        record["staticSourcePolicy"] = {"policy": "final-prospectus-only", "pendingRevalidationFields": ["lotSize", "financials"]}
        entry = queue_builder.queue_entry(record, date(2026, 9, 16))
        self.assertIsNotNone(entry)
        self.assertIn("provenance.finalProspectus.lotSize", entry["missingFields"])
        self.assertIn("provenance.finalProspectus.financials", entry["missingFields"])

    def test_open_or_upcoming_issue_is_not_blocked_on_unfiled_final_prospectus(self):
        record = self._pending_record(close_date="2026-09-20")
        names = [name for name, _ in queue_builder.expected_rules(record, date(2026, 9, 16))]
        self.assertFalse(any(name.startswith("provenance.finalProspectus.") for name in names))
        self.assertFalse(queue_builder.final_prospectus_expected(record, date(2026, 9, 16)))

    def test_recently_closed_issue_gets_bounded_final_prospectus_grace_period(self):
        record = self._pending_record(close_date="2026-09-15")
        names = [name for name, _ in queue_builder.expected_rules(record, date(2026, 9, 16))]
        self.assertFalse(any(name.startswith("provenance.finalProspectus.") for name in names))
        mature_names = [name for name, _ in queue_builder.expected_rules(record, date(2026, 9, 23))]
        self.assertIn("provenance.finalProspectus.lotSize", mature_names)
        self.assertIn("provenance.finalProspectus.financials", mature_names)

    def test_listing_or_attached_final_document_starts_revalidation_immediately(self):
        listed = self._pending_record(close_date="2026-09-15", listing_date="2026-09-16")
        self.assertTrue(queue_builder.final_prospectus_expected(listed, date(2026, 9, 16)))
        attached = self._pending_record(close_date="2026-09-20", with_final=True)
        self.assertTrue(queue_builder.final_prospectus_expected(attached, date(2026, 9, 16)))
        names = [name for name, _ in queue_builder.expected_rules(attached, date(2026, 9, 16))]
        self.assertIn("provenance.finalProspectus.lotSize", names)

    def test_verified_static_field_does_not_create_revalidation_gap(self):
        record = self._complete_recent_record()
        record["staticSourcePolicy"] = {"policy": "final-prospectus-only", "pendingRevalidationFields": [], "verifiedFields": ["lotSize", "financials"]}
        names = [name for name, _ in queue_builder.expected_rules(record, date(2026, 9, 16))]
        self.assertFalse(any(name.startswith("provenance.finalProspectus.") for name in names))

    def test_pending_marker_for_blank_field_is_not_double_counted(self):
        record = self._complete_recent_record()
        record["lotSize"] = None
        record["staticSourcePolicy"] = {"policy": "final-prospectus-only", "pendingRevalidationFields": ["lotSize"]}
        entry = queue_builder.queue_entry(record, date(2026, 9, 16))
        self.assertIn("exchange.lotSize", entry["missingFields"])
        self.assertNotIn("provenance.finalProspectus.lotSize", entry["missingFields"])

    def test_p4_revalidation_blocks_p5_and_is_reported_separately(self):
        queue = {"queue": [{"id": "recent", "priority": 4, "missingFields": ["provenance.finalProspectus.lotSize", "provenance.finalProspectus.financials"]}, {"id": "historical", "priority": 5, "missingFields": ["provenance.finalProspectus.lotSize"]}], "resolvedUnavailableRecordCount": 0}
        status = phase_status.status(queue, {"errorCount": 0, "reviewCount": 0})
        self.assertEqual(status["p4"]["status"], "incomplete")
        self.assertEqual(status["p5"]["status"], "waiting_for_p4")
        self.assertEqual(status["p4"]["finalProspectusRevalidationRecords"], 1)
        self.assertEqual(status["p4"]["finalProspectusRevalidationFields"], 2)

    def test_p5_revalidation_alone_does_not_prevent_p5_from_being_enabled(self):
        queue = {"queue": [{"id": "historical", "priority": 5, "missingFields": ["provenance.finalProspectus.lotSize"]}], "resolvedUnavailableRecordCount": 0}
        status = phase_status.status(queue, {"errorCount": 0, "reviewCount": 0})
        self.assertEqual(status["p4"]["status"], "complete")
        self.assertEqual(status["p5"]["status"], "enabled")
        self.assertEqual(status["p5"]["actionableRecords"], 1)

    def test_final_registry_reopens_same_document_for_pending_revalidation(self):
        spec = issuer_runner.base.ISSUER_DOCUMENTS["ardee"]
        payload = {"ipos": [{"id": "ardee", "company": "Ardee Industries Limited", "issuerDocumentExtraction": {"status": "extracted", "parserVersion": issuer_runner.base.PARSER_VERSION, "documentUrl": spec["url"], "documentType": "PROSPECTUS", "documentTitle": "Prospectus"}}]}
        queue = {"queue": [{"id": "ardee", "company": "Ardee Industries Limited", "priority": 4, "missingFields": ["provenance.finalProspectus.financials"]}]}
        targets = issuer_runner._identity_safe_targets(payload, queue, 4, 10)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0][0]["id"], "ardee")
        need_financials, need_shareholding = issuer_runner._needs_deep_scan_with_revalidation(queue["queue"][0], {})
        self.assertTrue(need_financials)
        self.assertFalse(need_shareholding)


if __name__ == "__main__":
    unittest.main()
