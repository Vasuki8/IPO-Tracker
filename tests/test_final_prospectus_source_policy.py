import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_parser as final_parser
import final_prospectus_policy as policy
import run_offer_documents as offer_runner


class FinalProspectusSourcePolicyTests(unittest.TestCase):
    def test_only_final_prospectus_is_eligible(self):
        self.assertTrue(policy.is_final_prospectus({"type": "PROSPECTUS", "title": "Prospectus"}))
        self.assertTrue(policy.is_final_prospectus({"type": "Final Prospectus"}))
        self.assertFalse(policy.is_final_prospectus({"type": "RHP", "title": "Red Herring Prospectus"}))
        self.assertFalse(policy.is_final_prospectus({"type": "DRHP", "title": "Draft Red Herring Prospectus"}))
        self.assertFalse(policy.is_final_prospectus({"title": "Red Herring Prospectus"}))

    def test_document_selection_ignores_newer_rhp(self):
        record = {
            "documents": [
                {
                    "type": "PROSPECTUS",
                    "title": "Final Prospectus",
                    "url": "https://www.sebi.gov.in/files/final.pdf",
                    "filedDate": "2026-08-20",
                },
                {
                    "type": "RHP",
                    "title": "Red Herring Prospectus",
                    "url": "https://www.sebi.gov.in/files/rhp.pdf",
                    "filedDate": "2026-09-01",
                },
            ]
        }
        selected = policy.choose_final_prospectus(record)
        self.assertEqual(selected["url"], "https://www.sebi.gov.in/files/final.pdf")
        self.assertEqual(offer_runner.document_for(record)["type"], "PROSPECTUS")

    def test_rhp_only_record_has_no_canonical_document(self):
        record = {
            "documents": [
                {
                    "type": "RHP",
                    "title": "Red Herring Prospectus",
                    "url": "https://www.sebi.gov.in/files/rhp.pdf",
                }
            ]
        }
        self.assertIsNone(policy.choose_final_prospectus(record))
        self.assertIsNone(offer_runner.document_for(record))

    def test_official_fp_source_can_be_promoted_but_rhp_cannot(self):
        fp = policy.final_prospectus_from_source(
            {
                "name": "NSE final Prospectus",
                "url": "https://nsearchives.nseindia.com/corporate/FP_INE000001_01SEP2026.pdf",
            }
        )
        self.assertEqual(fp["type"], "PROSPECTUS")
        self.assertIsNone(
            policy.final_prospectus_from_source(
                {
                    "name": "NSE RHP",
                    "url": "https://nsearchives.nseindia.com/corporate/ABC_RHP_01SEP2026.pdf",
                }
            )
        )

    def test_final_prospectus_overwrites_legacy_static_values(self):
        record = {
            "lotSize": 999,
            "priceBand": {"min": 10, "max": 20},
            "leadManagers": ["Legacy Capital Limited"],
            "issueSizeCr": 50.0,
            "listing": {"issuePrice": 20.0},
        }
        parsed = {
            "lotSize": 1200,
            "priceBand": {"min": 118, "max": 124},
            "leadManagers": ["Final Capital Limited"],
            "issuePrice": 124.0,
            "issueComposition": {
                "freshIssueCr": 80.0,
                "ofsCr": 20.0,
                "totalIssueSizeCr": 100.0,
            },
        }
        doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://www.sebi.gov.in/files/final.pdf",
            "filedDate": "2026-09-10",
        }
        changes = policy.apply_final_prospectus_static_fields(
            record,
            parsed,
            doc,
            sha256="abc",
            parser_version=23,
            checked_at="2026-09-16T00:00:00Z",
        )
        changed = {entry["field"] for entry in changes}
        self.assertIn("lotSize", changed)
        self.assertIn("listing.issuePrice", changed)
        self.assertEqual(record["lotSize"], 1200)
        self.assertEqual(record["issueSizeCr"], 100.0)
        self.assertEqual(record["listing"]["issuePrice"], 124.0)
        self.assertEqual(
            record["staticFieldProvenance"]["lotSize"]["documentType"],
            "PROSPECTUS",
        )
        self.assertEqual(
            record["listing"]["issuePriceEvidence"]["source"],
            "Final Prospectus",
        )

    def test_financials_without_exact_table_evidence_are_not_promoted(self):
        old_financials = {
            "unit": "₹ crore",
            "periods": [
                {"period": "FY2025", "revenueCr": 80.0, "patCr": 8.0},
                {"period": "FY2024", "revenueCr": 70.0, "patCr": 7.0},
            ],
        }
        record = {
            "openDate": "2026-04-01",
            "financials": old_financials,
        }
        parsed = {
            "financials": {
                "unit": "₹ crore",
                "periods": [
                    {"period": "FY2025", "revenueCr": 100.0, "patCr": 10.0},
                    {"period": "FY2024", "revenueCr": 90.0, "patCr": 9.0},
                ],
            },
            "fieldEvidence": {"financials": {}},
        }
        doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://www.sebi.gov.in/files/final.pdf",
        }
        changes = policy.apply_final_prospectus_static_fields(
            record,
            parsed,
            doc,
            sha256="abc",
            parser_version=24,
            checked_at="2026-09-16T00:00:00Z",
        )
        self.assertEqual(record["financials"], old_financials)
        self.assertNotIn("financials", {entry["field"] for entry in changes})
        self.assertNotIn("financials", record["staticFieldProvenance"])
        self.assertNotIn("financials", record["documentFieldProvenance"]["evidence"])
        self.assertIn("financials", record["staticSourcePolicy"]["pendingRevalidationFields"])

    def test_financials_and_table_evidence_are_promoted_atomically(self):
        financials = {
            "unit": "₹ crore",
            "periods": [
                {"period": "FY2025", "revenueCr": 100.0, "patCr": 10.0},
                {"period": "FY2024", "revenueCr": 90.0, "patCr": 9.0},
            ],
        }
        financial_evidence = {
            "FY2025.revenueCr": {"page": 100, "normalizedValue": 100.0},
            "FY2025.patCr": {"page": 100, "normalizedValue": 10.0},
            "FY2024.revenueCr": {"page": 100, "normalizedValue": 90.0},
            "FY2024.patCr": {"page": 100, "normalizedValue": 9.0},
        }
        record = {"openDate": "2026-04-01", "financials": None}
        parsed = {
            "financials": financials,
            "fieldEvidence": {"financials": financial_evidence},
        }
        doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://www.sebi.gov.in/files/final.pdf",
            "filedDate": "2026-04-08",
        }
        changes = policy.apply_final_prospectus_static_fields(
            record,
            parsed,
            doc,
            sha256="abc",
            parser_version=24,
            checked_at="2026-09-16T00:00:00Z",
        )
        self.assertIn("financials", {entry["field"] for entry in changes})
        self.assertEqual(record["financials"], financials)
        self.assertEqual(
            record["documentFieldProvenance"]["evidence"]["financials"],
            financial_evidence,
        )
        self.assertEqual(
            record["staticFieldProvenance"]["financials"]["evidence"],
            financial_evidence,
        )
        self.assertNotIn("financials", record["staticSourcePolicy"]["pendingRevalidationFields"])

    def test_stale_financial_table_far_from_issue_year_fails_closed(self):
        financials = {
            "unit": "₹ crore",
            "periods": [
                {"period": "FY2016", "revenueCr": 100.0, "patCr": 10.0},
                {"period": "FY2015", "revenueCr": 90.0, "patCr": 9.0},
            ],
        }
        evidence = {
            "FY2016.revenueCr": {"normalizedValue": 100.0},
            "FY2016.patCr": {"normalizedValue": 10.0},
            "FY2015.revenueCr": {"normalizedValue": 90.0},
            "FY2015.patCr": {"normalizedValue": 9.0},
        }
        record = {"openDate": "2026-04-01", "financials": None}
        policy.apply_final_prospectus_static_fields(
            record,
            {"financials": financials, "fieldEvidence": {"financials": evidence}},
            {"type": "PROSPECTUS", "url": "https://www.sebi.gov.in/files/final.pdf"},
            parser_version=24,
        )
        self.assertIsNone(record["financials"])
        self.assertNotIn("financials", record["staticFieldProvenance"])

    def test_non_final_document_cannot_write_static_fields(self):
        with self.assertRaises(ValueError):
            policy.apply_final_prospectus_static_fields(
                {"lotSize": None},
                {"lotSize": 1200},
                {"type": "RHP", "url": "https://www.sebi.gov.in/files/rhp.pdf"},
            )

    def test_fixed_offer_price_is_extracted_from_final_prospectus(self):
        text = """
        PROSPECTUS
        OFFER PRICE: ₹ 124 PER EQUITY SHARE
        The face value of the Equity Shares is ₹10 each.
        """
        price, evidence = final_parser.extract_final_issue_price(text)
        self.assertEqual(price, 124.0)
        self.assertIn("issuePrice", evidence)

    def test_conflicting_fixed_prices_fail_closed(self):
        text = """
        OFFER PRICE: ₹ 124 PER EQUITY SHARE
        ISSUE PRICE: ₹ 125 PER EQUITY SHARE
        """
        price, _ = final_parser.extract_final_issue_price(text)
        self.assertIsNone(price)

    def test_market_updater_keeps_static_terms_observation_only(self):
        code = r'''
import json
import run_update_final_policy as mod
row = mod.normalize_nse_record({
    "companyName": "Example Limited",
    "symbol": "EXAMPLE",
    "issueStartDate": "01-Sep-2026",
    "issueEndDate": "03-Sep-2026",
    "minPrice": 118,
    "maxPrice": 124,
    "lotSize": 1200,
    "issueSizeCr": 100,
}, "current")
merged = mod.merge_fill_only(
    {"company": "Example Limited", "lotSize": None, "priceBand": None, "listingDate": None},
    {"lotSize": 1200, "priceBand": {"min": 118, "max": 124}, "listingDate": "2026-09-10"},
)
print(json.dumps({"row": row, "merged": merged}))
'''
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "scripts")},
            text=True,
            capture_output=True,
            check=True,
        )
        data = json.loads(result.stdout.strip())
        row = data["row"]
        self.assertIsNone(row["lotSize"])
        self.assertIsNone(row["priceBand"])
        self.assertIsNone(row["issueSizeCr"])
        observed = row["observations"]["NSE"]["staticOfferTerms"]
        self.assertEqual(observed["lotSize"], 1200)
        self.assertEqual(observed["priceBand"], {"min": 118.0, "max": 124.0})
        self.assertEqual(observed["issueSizeCr"], 100.0)
        self.assertIsNone(data["merged"]["lotSize"])
        self.assertIsNone(data["merged"]["priceBand"])
        self.assertEqual(data["merged"]["listingDate"], "2026-09-10")

    def test_pipeline_has_no_mixed_static_backfill_stages(self):
        pipeline = (ROOT / "scripts" / "run_pipeline.py").read_text(encoding="utf-8")
        forbidden = (
            "apply_verified_recent_issue_terms.py",
            "collect_final_issue_prices.py",
            "enrich_nse_issue_information.py",
            "backfill_recent_nse_lot_sizes.py",
            "backfill_recent_sebi_other_docs_lot_sizes.py",
            "backfill_p4_lot_sizes.py",
            "enrich_recent_offer_terms.py",
            "apply_verified_filing_offer_fields.py",
        )
        for name in forbidden:
            self.assertNotIn(name, pipeline)
        self.assertIn("run_update_final_policy.py", pipeline)
        self.assertIn("run_offer_documents.py", pipeline)
        self.assertIn("enforce_final_prospectus_policy.py", pipeline)

    def test_publish_workflow_does_not_restore_old_static_sources(self):
        workflow = (ROOT / ".github" / "workflows" / "refresh.yml").read_text(encoding="utf-8")
        self.assertNotIn("apply_verified_recent_issue_terms.py", workflow)
        self.assertNotIn("backfill_recent_nse_lot_sizes.py", workflow)
        self.assertIn("enforce_final_prospectus_policy.py", workflow)


if __name__ == "__main__":
    unittest.main()
