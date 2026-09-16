import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import collect_nse_offer_filings_final_policy as collector
import final_prospectus_policy as policy


class FinalProspectusDiscoveryTests(unittest.TestCase):
    def record(self):
        return {
            "id": "example-2026-06-01",
            "company": "Example Industries Limited",
            "symbol": "EXAMPLE",
            "isin": "INE000000001",
            "openDate": "2026-06-01",
            "closeDate": "2026-06-03",
            # These populated legacy fields must not suppress Final Prospectus discovery.
            "lotSize": 100,
            "registrar": "Legacy Registrar Limited",
            "leadManagers": ["Legacy Capital Limited"],
            "documents": [],
            "staticSourcePolicy": {
                "policy": "final-prospectus-only",
                "pendingRevalidationFields": ["lotSize", "registrar", "leadManagers"],
            },
        }

    def entry(self, **overrides):
        row = {
            "company": "Example Industries Limited",
            "symbol": "EXAMPLE",
            "isin": "INE000000001",
            "issue_open_date": "2026-06-01",
            "issue_close_date": "2026-06-03",
            "fpAttach": "https://nsearchives.nseindia.com/corporate/EXAMPLE_PROSPECTUS.pdf",
            "fpDate": "2026-06-09",
            "rhpAttach": "https://nsearchives.nseindia.com/corporate/EXAMPLE_RHP.pdf",
            "rhpDate": "2026-05-25",
        }
        row.update(overrides)
        return row

    def test_import_does_not_mutate_shared_legacy_merge_function(self):
        self.assertIsNot(collector.base.merge_terms, collector.merge_dynamic_only)

    def test_populated_legacy_fields_do_not_suppress_final_discovery(self):
        record = self.record()
        docs = collector.eligible_final_documents(record, [self.entry()])
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["type"], "PROSPECTUS")
        self.assertIn("PROSPECTUS.pdf", docs[0]["url"])

    def test_rhp_only_row_is_not_a_canonical_discovery(self):
        record = self.record()
        docs = collector.eligible_final_documents(
            record,
            [self.entry(fpAttach=None, fpDate=None)],
        )
        self.assertEqual(docs, [])

    def test_identity_or_issue_date_mismatch_fails_closed(self):
        record = self.record()
        self.assertEqual(
            collector.eligible_final_documents(
                record,
                [self.entry(issue_open_date="2026-05-01")],
            ),
            [],
        )
        self.assertEqual(
            collector.eligible_final_documents(
                record,
                [self.entry(company="Different Industries Limited")],
            ),
            [],
        )

    def test_out_of_window_final_filing_is_rejected(self):
        record = self.record()
        docs = collector.eligible_final_documents(
            record,
            [self.entry(fpDate="2026-09-30")],
        )
        self.assertEqual(docs, [])

    def test_discovery_attaches_final_and_preserves_legacy_values_for_revalidation(self):
        record = self.record()
        payload = {"ipos": [record], "meta": {}}
        health = collector.discover_final_prospectuses(
            payload,
            [self.entry()],
            limit=10,
            history_days=730,
            documents_limit=10,
            retry_days=7,
            today=date(2026, 9, 16),
        )
        self.assertEqual(health["documentsDiscovered"], 1)
        self.assertEqual(health["recordsWithFinalProspectus"], 1)
        self.assertEqual(record["lotSize"], 100)
        self.assertEqual(record["registrar"], "Legacy Registrar Limited")
        self.assertEqual(record["documents"][0]["type"], "PROSPECTUS")
        self.assertIsNotNone(policy.choose_final_prospectus(record))

    def test_unchanged_register_fingerprint_is_bounded_by_retry_window(self):
        record = self.record()
        rows = [self.entry(fpAttach=None, fpDate=None)]
        fingerprint = collector._entry_fingerprint(rows)
        record[collector.DISCOVERY_ATTEMPT] = {
            "fingerprint": fingerprint,
            "lastAttemptAt": "2026-09-15T12:00:00Z",
            "status": "no_final_prospectus",
        }
        health = collector.discover_final_prospectuses(
            {"ipos": [record], "meta": {}},
            rows,
            limit=10,
            history_days=730,
            documents_limit=10,
            retry_days=7,
            today=date(2026, 9, 16),
        )
        self.assertEqual(health["attempted"], 0)
        self.assertEqual(health["skippedRecentFingerprint"], 1)


if __name__ == "__main__":
    unittest.main()
