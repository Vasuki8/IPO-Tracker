import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "apply_verified_p4_nse_issue_terms_v3.py"
spec = importlib.util.spec_from_file_location("apply_verified_p4_nse_issue_terms_v3", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
base = mod.base


class VerifiedP4NSEIssueTermsV3Tests(unittest.TestCase):
    def test_values_and_nse_only_sources(self):
        expected = {
            "nsdl": (4010.954, 0.0, 4010.954),
            "optimystix": (108.5, 87.5, 21.0),
        }
        self.assertEqual(set(mod.EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS_V3), set(expected))
        for record_id, values in expected.items():
            entry = mod.EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS_V3[record_id]
            self.assertEqual((entry["issueSizeCr"], entry["freshIssueCr"], entry["ofsCr"]), values)
            for url in entry["sourceUrls"]:
                self.assertTrue(base._nse_official_url(url), record_id)

    def test_exact_identities_apply(self):
        identities = {
            "nsdl": ("National Securities Depository Limited", "NSDL", "2025-07-30"),
            "optimystix": ("Optimystix Entertainment India Limited", "OPTIMYSTIX", "2026-08-07"),
        }
        for record_id, (company, symbol, open_date) in identities.items():
            record = {
                "id": record_id,
                "company": company,
                "symbol": symbol,
                "openDate": open_date,
                "issueSizeCr": None,
                "freshIssueCr": None,
                "ofsCr": None,
                "issueComposition": None,
                "sources": [],
                "observations": {},
            }
            changed = base.apply_entry(record_id, record, mod.EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS_V3[record_id])
            self.assertIn("issueSizeCr", changed, record_id)
            self.assertIn("issueComposition", changed, record_id)
            self.assertEqual(record["sources"][0]["kind"], "exchange", record_id)

    def test_nsdl_is_pure_ofs_and_uses_official_aggregate(self):
        entry = mod.EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS_V3["nsdl"]
        self.assertEqual(entry["freshIssueCr"], 0.0)
        self.assertEqual(entry["ofsCr"], entry["issueSizeCr"])
        self.assertIn("employee discount", entry["sourceBasis"])
        self.assertIn("overstating", entry["officialNote"])

    def test_fill_only(self):
        entry = mod.EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS_V3["optimystix"]
        record = {
            "id": "optimystix",
            "company": "Optimystix Entertainment India Limited",
            "symbol": "OPTIMYSTIX",
            "openDate": "2026-08-07",
            "issueSizeCr": 1.0,
            "freshIssueCr": 1.0,
            "ofsCr": 0.0,
            "issueComposition": {"freshIssueCr": 1.0, "ofsCr": 0.0},
            "sources": [],
            "observations": {},
        }
        self.assertEqual(base.apply_entry("optimystix", record, entry), [])
        self.assertEqual(record["issueSizeCr"], 1.0)


if __name__ == "__main__":
    unittest.main()
