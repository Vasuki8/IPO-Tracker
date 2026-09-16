import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_missing_queue as queue_builder


class FixedPriceFinalProspectusQueueTests(unittest.TestCase):
    def _record(self):
        return {
            "id": "fixed",
            "company": "Fixed Price Limited",
            "symbol": "FIXED",
            "openDate": "2026-08-01",
            "closeDate": "2026-08-05",
            "listingDate": "2026-08-10",
            "priceBand": {"min": 125, "max": 125},
            "listing": {"issuePrice": 125},
            "staticSourcePolicy": {
                "policy": "final-prospectus-only",
                "pendingRevalidationFields": ["priceBand"],
            },
            "staticFieldProvenance": {
                "listing.issuePrice": {
                    "source": "Final Prospectus",
                    "sourceUrl": "https://nsearchives.nseindia.com/emerge/corporates/content/Fixed_PROSP.pdf",
                    "documentType": "PROSPECTUS",
                    "value": 125,
                }
            },
        }

    def test_matching_fixed_issue_price_resolves_legacy_one_point_band(self):
        record = self._record()
        self.assertTrue(queue_builder.fixed_price_band_finally_verified(record))
        pending = queue_builder.pending_final_prospectus_fields(record, date(2026, 9, 16))
        self.assertNotIn("priceBand", pending)

    def test_real_book_built_band_still_requires_explicit_final_band_evidence(self):
        record = self._record()
        record["priceBand"] = {"min": 120, "max": 125}
        self.assertFalse(queue_builder.fixed_price_band_finally_verified(record))
        pending = queue_builder.pending_final_prospectus_fields(record, date(2026, 9, 16))
        self.assertIn("priceBand", pending)

    def test_mismatched_fixed_price_is_not_resolved(self):
        record = self._record()
        record["priceBand"] = {"min": 124, "max": 124}
        self.assertFalse(queue_builder.fixed_price_band_finally_verified(record))
        pending = queue_builder.pending_final_prospectus_fields(record, date(2026, 9, 16))
        self.assertIn("priceBand", pending)

    def test_non_final_issue_price_provenance_is_not_accepted(self):
        record = self._record()
        record["staticFieldProvenance"]["listing.issuePrice"]["source"] = "NSE"
        self.assertFalse(queue_builder.fixed_price_band_finally_verified(record))
        pending = queue_builder.pending_final_prospectus_fields(record, date(2026, 9, 16))
        self.assertIn("priceBand", pending)

    def test_missing_issue_price_provenance_is_not_accepted(self):
        record = self._record()
        record["staticFieldProvenance"] = {}
        self.assertFalse(queue_builder.fixed_price_band_finally_verified(record))
        pending = queue_builder.pending_final_prospectus_fields(record, date(2026, 9, 16))
        self.assertIn("priceBand", pending)


if __name__ == "__main__":
    unittest.main()
