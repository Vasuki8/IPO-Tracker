import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "apply_verified_p4_final_issue_terms.py"
spec = importlib.util.spec_from_file_location("apply_verified_p4_final_issue_terms", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class VerifiedP4FinalIssueTermsTests(unittest.TestCase):
    def test_exact_values_and_arithmetic(self):
        expected = {
            "anawil": (270.0, 5_284_800, 1_300_800, 177.8112, 142.6896, 35.1216),
            "fascinate": (151.0, 3_457_600, 836_000, 64.83336, 52.20976, 12.6236),
        }
        self.assertEqual(set(mod.VERIFIED_P4_FINAL_ISSUE_TERMS), set(expected))
        for record_id, values in expected.items():
            entry = mod.VERIFIED_P4_FINAL_ISSUE_TERMS[record_id]
            actual = (
                entry["issuePrice"], entry["freshShares"], entry["ofsShares"],
                entry["issueSizeCr"], entry["freshIssueCr"], entry["ofsCr"],
            )
            self.assertEqual(actual, values, record_id)
            self.assertAlmostEqual(entry["freshIssueCr"] + entry["ofsCr"], entry["issueSizeCr"], places=5)

    def test_sources_are_official_and_multi_source(self):
        for record_id, entry in mod.VERIFIED_P4_FINAL_ISSUE_TERMS.items():
            self.assertGreaterEqual(len(entry["sources"]), 2, record_id)
            for source in entry["sources"]:
                self.assertTrue(mod._official_source(source), (record_id, source))

        fake = {"name": "fake", "url": "https://example.com/file.pdf", "kind": "offer-document"}
        self.assertFalse(mod._official_source(fake))

    def test_exact_identities_apply_and_fill_composition(self):
        identities = {
            "anawil": ("Anawil Wire and Engineering Limited", "ANAWIL", "2026-08-03"),
            "fascinate": ("Fascinate Textiles Limited", "FASCINATE", "2026-08-11"),
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
            changed = mod.apply_entry(record_id, record, mod.VERIFIED_P4_FINAL_ISSUE_TERMS[record_id])
            self.assertIn("issueSizeCr", changed, record_id)
            self.assertIn("issueComposition", changed, record_id)
            self.assertEqual(len(record["sources"]), 2, record_id)

    def test_wrong_identity_and_populated_terms_are_not_overwritten(self):
        entry = mod.VERIFIED_P4_FINAL_ISSUE_TERMS["anawil"]
        wrong = {
            "id": "anawil",
            "company": "Anawil Wire and Engineering Limited",
            "symbol": "WRONG",
            "openDate": "2026-08-03",
            "issueSizeCr": None,
            "freshIssueCr": None,
            "ofsCr": None,
            "issueComposition": None,
            "sources": [],
            "observations": {},
        }
        self.assertEqual(mod.apply_entry("anawil", wrong, entry), [])

        populated = dict(wrong)
        populated["symbol"] = "ANAWIL"
        populated.update({
            "issueSizeCr": 1.0,
            "freshIssueCr": 1.0,
            "ofsCr": 0.0,
            "issueComposition": {"freshIssueCr": 1.0, "ofsCr": 0.0},
        })
        self.assertEqual(mod.apply_entry("anawil", populated, entry), [])
        self.assertEqual(populated["issueSizeCr"], 1.0)


if __name__ == "__main__":
    unittest.main()
