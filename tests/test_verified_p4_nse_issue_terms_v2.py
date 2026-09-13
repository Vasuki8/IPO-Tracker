import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "apply_verified_p4_nse_issue_terms_v2.py"
spec = importlib.util.spec_from_file_location("apply_verified_p4_nse_issue_terms_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
base = mod.base


class VerifiedP4NSEIssueTermsV2Tests(unittest.TestCase):
    def test_closeout_values_and_official_sources(self):
        expected = {
            "credent": (93.8952, 93.8952, 0.0),
            "pramodini": (69.0442, 63.1394, 5.9047),
            "identical": (19.9476, 19.9476, 0.0),
            "capinvit": (1578.0, 1077.0, 501.0),
        }
        self.assertEqual(set(mod.EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS), set(expected))
        for record_id, values in expected.items():
            entry = mod.EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS[record_id]
            self.assertEqual((entry["issueSizeCr"], entry["freshIssueCr"], entry["ofsCr"]), values)
            self.assertTrue(entry["sourceUrls"])
            for url in entry["sourceUrls"]:
                self.assertTrue(base._nse_official_url(url), record_id)

    def test_exact_identities_apply_and_create_composition(self):
        identities = {
            "credent": ("Credent Connect N Care Limited", "CREDENT", "2026-08-13"),
            "pramodini": ("Pramodini Medicare Limited", "PRAMODINI", "2026-08-12"),
            "identical": ("Identical Brains Studios Limited", "IDENTICAL", "2024-12-18"),
            "capinvit": ("Capital Infra Trust", "CAPINVIT", "2025-01-07"),
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
            changed = base.apply_entry(record_id, record, mod.EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS[record_id])
            self.assertIn("issueSizeCr", changed, record_id)
            self.assertIn("issueComposition", changed, record_id)
            self.assertEqual(record["sources"][0]["kind"], "exchange", record_id)

    def test_fill_only_and_wrong_identity_rejected(self):
        entry = mod.EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS["credent"]
        populated = {
            "id": "credent",
            "company": "Credent Connect N Care Limited",
            "symbol": "CREDENT",
            "openDate": "2026-08-13",
            "issueSizeCr": 1.0,
            "freshIssueCr": 1.0,
            "ofsCr": 0.0,
            "issueComposition": {"freshIssueCr": 1.0, "ofsCr": 0.0},
            "sources": [],
            "observations": {},
        }
        self.assertEqual(base.apply_entry("credent", populated, entry), [])
        self.assertEqual(populated["issueSizeCr"], 1.0)

        wrong = dict(populated)
        wrong["issueSizeCr"] = None
        wrong["freshIssueCr"] = None
        wrong["issueComposition"] = None
        wrong["symbol"] = "WRONG"
        self.assertEqual(base.apply_entry("credent", wrong, entry), [])

    def test_capinvit_rounded_terms_balance(self):
        entry = mod.EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS["capinvit"]
        self.assertEqual(entry["freshIssueCr"] + entry["ofsCr"], entry["issueSizeCr"])
        self.assertIn("rounded", entry["officialNote"])


if __name__ == "__main__":
    unittest.main()
