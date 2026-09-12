import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "audit_data_completeness.py"
spec = importlib.util.spec_from_file_location("audit_data_completeness", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class CompletenessRuleTests(unittest.TestCase):
    def test_present_keeps_numeric_zero(self):
        self.assertTrue(mod.present(0))
        self.assertFalse(mod.present(None))
        self.assertFalse(mod.present("N/A"))

    def test_filing_pipeline_not_misclassified_as_exchange_issue(self):
        record = {
            "company": "Example Limited",
            "lifecycle": {"stage": "drhp", "stageDate": "2026-09-01"},
            "documents": [{"type": "DRHP", "url": "https://example.test/drhp.pdf"}],
        }
        self.assertEqual(mod.lifecycle_stage(record, date(2026, 9, 12)), "filing-pipeline")
        self.assertFalse(mod.present(record.get("openDate")))

    def test_open_issue_is_identified_from_dates(self):
        record = {"openDate": "2026-09-10", "closeDate": "2026-09-14"}
        self.assertEqual(mod.lifecycle_stage(record, date(2026, 9, 12)), "open")

    def test_issue_composition_accepts_fresh_or_ofs(self):
        self.assertTrue(mod.has_issue_composition({"freshIssueCr": 100.0}))
        self.assertTrue(mod.has_issue_composition({"issueComposition": {"ofsShares": 1000000}}))
        self.assertFalse(mod.has_issue_composition({}))

    def test_offer_document_detection(self):
        self.assertTrue(
            mod.has_offer_document(
                {"documents": [{"type": "RHP", "url": "https://example.test/rhp.pdf"}]}
            )
        )
        self.assertFalse(
            mod.has_offer_document(
                {"documents": [{"type": "DRHP", "url": "https://example.test/drhp.pdf"}]}
            )
        )

    def test_coverage_uses_only_supplied_denominator(self):
        records = [{"symbol": "AAA"}, {"symbol": None}]
        result = mod.coverage(records, [("symbol", lambda r: mod.present(r.get("symbol")))])
        self.assertEqual(result["symbol"]["present"], 1)
        self.assertEqual(result["symbol"]["missing"], 1)
        self.assertEqual(result["symbol"]["pct"], 50.0)

    def test_financials_require_at_least_one_real_metric(self):
        self.assertFalse(mod.has_financials({"financials": {"periods": [{"period": "FY26"}]}}))
        self.assertTrue(
            mod.has_financials(
                {"financials": {"periods": [{"period": "FY26", "revenueCr": 250.5}]}}
            )
        )

    def test_old_exchange_only_record_does_not_require_issue_composition(self):
        record = {
            "openDate": "2018-01-01",
            "symbol": "OLD",
            "board": "Mainboard",
            "exchange": "NSE",
        }
        names = [name for name, _ in mod.expected_exchange_rules(record, date(2026, 9, 13))]
        self.assertNotIn("issueComposition", names)
        self.assertIn("lotSize", names)
        self.assertIn("issueSizeCr", names)

    def test_old_record_with_offer_document_still_requires_issue_composition(self):
        record = {
            "openDate": "2018-01-01",
            "documents": [{"type": "RHP", "url": "https://example.test/rhp.pdf"}],
        }
        names = [name for name, _ in mod.expected_exchange_rules(record, date(2026, 9, 13))]
        self.assertIn("issueComposition", names)

    def test_document_provenance_is_only_expected_for_filing_or_offer_records(self):
        old = {
            "openDate": "2018-01-01",
            "symbol": "OLD",
            "sources": [{"name": "NSE"}],
            "validation": {"status": "single-source"},
        }
        filing = {
            "lifecycle": {"stage": "drhp"},
            "documents": [{"type": "DRHP", "url": "https://example.test/drhp.pdf"}],
        }
        old_names = [name for name, _ in mod.expected_provenance_rules(old, date(2026, 9, 13))]
        filing_names = [name for name, _ in mod.expected_provenance_rules(filing, date(2026, 9, 13))]
        self.assertNotIn("documents", old_names)
        self.assertIn("documents", filing_names)

    def test_allotment_is_optional_not_actionable_lifecycle_gap(self):
        actionable = [name for name, _ in mod.MATURED_LIFECYCLE_FIELDS]
        optional = [name for name, _ in mod.OPTIONAL_LIFECYCLE_FIELDS]
        self.assertEqual(actionable, ["listingDate"])
        self.assertEqual(optional, ["allotmentDate"])

    def test_dynamic_coverage_uses_field_specific_denominator(self):
        today = date(2026, 9, 13)
        records = [
            {"openDate": "2026-09-01", "freshIssueCr": 100},
            {"openDate": "2018-01-01"},
        ]
        result = mod.dynamic_coverage(records, lambda r: mod.expected_exchange_rules(r, today))
        self.assertEqual(result["issueComposition"]["expected"], 1)
        self.assertEqual(result["issueComposition"]["present"], 1)
        self.assertEqual(result["issueComposition"]["pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
