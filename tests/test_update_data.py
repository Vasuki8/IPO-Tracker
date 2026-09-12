import importlib.util
import unittest
import sys
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "update_data.py"
spec = importlib.util.spec_from_file_location("update_data", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class NormalizerTests(unittest.TestCase):
    def test_company_key_ignores_legal_suffix_and_filing_words(self):
        self.assertEqual(mod.canonical_company("Example Limited - RHP"), "EXAMPLE")
        self.assertEqual(mod.canonical_company("Example Ltd DRHP"), "EXAMPLE")

    def test_period_parser(self):
        self.assertEqual(mod.parse_period("13 Oct 2026 to 17 Oct 2026"), ("2026-10-13", "2026-10-17"))

    def test_price_band_parser(self):
        self.assertEqual(mod.parse_price_band_text("Rs 100 - Rs 110"), {"min": 100.0, "max": 110.0})
        self.assertEqual(mod.parse_price_band_text("₹99"), {"min": 99.0, "max": 99.0})

    def test_issue_size_tolerance(self):
        self.assertTrue(mod.field_equal("issueSizeCr", 500.0, 501.0))
        self.assertFalse(mod.field_equal("issueSizeCr", 500.0, 510.0))

    def test_conflict_is_not_overwritten(self):
        base = {"openDate": "2026-09-10", "lotSize": 100, "company": "Example Limited"}
        incoming = {"openDate": "2026-09-11", "lotSize": 125, "company": "Example Limited"}
        out = mod.merge_fill_only(base, incoming, protected={"openDate", "lotSize", "company"})
        self.assertEqual(out["openDate"], "2026-09-10")
        self.assertEqual(out["lotSize"], 100)

    def test_validation_flags_exchange_disagreement(self):
        rec = {
            "sources": [
                {"name": "NSE current", "url": "nse"},
                {"name": "BSE public issue", "url": "bse"},
            ],
            "observations": {
                "NSE": {"openDate": "2026-09-10", "lotSize": 100},
                "BSE": {"openDate": "2026-09-10", "lotSize": 125},
            },
        }
        validation = mod.build_validation(rec)
        self.assertEqual(validation["status"], "conflict")
        self.assertTrue(any(c["field"] == "lotSize" and c["match"] is False for c in validation["checks"]))


if __name__ == "__main__":
    unittest.main()
