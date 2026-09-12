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


if __name__ == "__main__":
    unittest.main()
