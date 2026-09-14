import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from collect_final_issue_prices import matched_report, merge_price, existing_verified_prices
from update_data import canonical_company


class FinalPriceTests(unittest.TestCase):
    def setUp(self):
        self.record = {"id": "x", "company": "Example Industries Limited", "symbol": "EXAMPLE", "openDate": "2025-08-01", "priceBand": {"min": 90, "max": 100}}
        self.row = {"company": self.record["company"], "matchKey": canonical_company(self.record["company"]), "symbol": "EXAMPLE", "openDate": "2025-08-01", "issuePrice": 98, "sourceUrl": "https://nsearchives.nseindia.com/official.xlsx", "sha256": "a" * 64}

    def test_explicit_price_is_saved_with_evidence_and_is_idempotent(self):
        self.assertTrue(merge_price(self.record, self.row))
        self.assertEqual(self.record["listing"]["issuePrice"], 98)
        self.assertEqual(self.record["listing"]["issuePriceEvidence"]["value"], 98)
        self.assertFalse(merge_price(self.record, self.row))

    def test_price_cap_cannot_supply_a_missing_final_price(self):
        self.row.pop("issuePrice")
        self.assertIsNone(matched_report(self.record, [self.row]))
        self.assertNotIn("listing", self.record)

    def test_reused_symbol_wrong_date_or_issuer_rejected(self):
        for change in ({"openDate": "2024-08-01"}, {"symbol": "OTHER"}, {"matchKey": "OTHER"}, {"sourceUrl": "https://example.com/month.xlsx"}):
            self.assertIsNone(matched_report(self.record, [{**self.row, **change}]))

    def test_conflicting_reports_are_not_arbitrarily_selected(self):
        self.assertIsNone(matched_report(self.record, [self.row, {**self.row, "issuePrice": 99}]))

    def test_prior_final_price_and_band_disagreement_are_preserved(self):
        self.record["listing"] = {"issuePrice": 97}
        self.assertFalse(merge_price(self.record, self.row))
        self.assertEqual(self.record["listing"]["issuePrice"], 97)
        self.record.pop("listing")
        self.row["issuePrice"] = 101
        self.assertFalse(merge_price(self.record, self.row))

    def test_verified_circular_requires_explicit_final_price_and_issue_date(self):
        self.record["observations"] = {"VerifiedP4FinalIssueTerms": {"issuePrice": 98, "openDate": "2025-08-01", "sourceBasis": "Listing circular fixes final issue price at Rs 98", "sourceUrls": ["https://nsearchives.nseindia.com/content/circulars/CML123.zip"]}}
        self.assertEqual(existing_verified_prices({"ipos": [self.record]}), 1)
        other = copy.deepcopy(self.record)
        other.pop("listing")
        other["observations"]["VerifiedP4FinalIssueTerms"]["openDate"] = "2024-08-01"
        self.assertEqual(existing_verified_prices({"ipos": [other]}), 0)


if __name__ == "__main__":
    unittest.main()
