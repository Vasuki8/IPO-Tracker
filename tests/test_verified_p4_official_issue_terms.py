import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "apply_verified_p4_official_issue_terms.py"
spec = importlib.util.spec_from_file_location("apply_verified_p4_official_issue_terms", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class VerifiedP4OfficialIssueTermsTests(unittest.TestCase):
    def test_registry_is_official_only_and_has_expected_values(self):
        expected = {
            "carraro": (1250.0, 0.0, 1250.0),
            "mamata": (179.349, 0.0, 179.349),
            "senores": (582.11, 500.0, 82.11),
            "unimech": (500.0, 250.0, 250.0),
            "sailife": (3042.62, None, None),
            "sanathan": (550.0, None, None),
            "transraill": (838.912, None, None),
        }
        self.assertEqual(set(mod.VERIFIED_P4_OFFICIAL_ISSUE_TERMS), set(expected))
        for record_id, values in expected.items():
            entry = mod.VERIFIED_P4_OFFICIAL_ISSUE_TERMS[record_id]
            self.assertEqual(
                (entry["issueSizeCr"], entry["freshIssueCr"], entry["ofsCr"]),
                values,
            )
            self.assertIn("sebi.gov.in", entry["sourceUrl"])

    def test_full_entry_fills_composition_and_is_fill_only(self):
        entry = mod.VERIFIED_P4_OFFICIAL_ISSUE_TERMS["senores"]
        record = {
            "id": "senores",
            "company": "Senores Pharmaceuticals Limited",
            "symbol": "SENORES",
            "openDate": "2024-12-20",
            "issueSizeCr": None,
            "freshIssueCr": None,
            "ofsCr": None,
            "issueComposition": None,
            "sources": [],
            "observations": {},
        }
        changed = mod.apply_entry("senores", record, entry)
        self.assertEqual(record["issueSizeCr"], 582.11)
        self.assertEqual(record["freshIssueCr"], 500.0)
        self.assertEqual(record["ofsCr"], 82.11)
        self.assertIn("issueComposition", changed)
        self.assertEqual(record["issueComposition"]["totalIssueSizeCr"], 582.11)

        record["issueSizeCr"] = 999.0
        record["freshIssueCr"] = 888.0
        record["ofsCr"] = 111.0
        record["issueComposition"] = {"freshIssueCr": 888.0, "ofsCr": 111.0}
        self.assertEqual(mod.apply_entry("senores", record, entry), [])
        self.assertEqual(record["issueSizeCr"], 999.0)

    def test_size_only_entry_never_creates_composition(self):
        entry = mod.VERIFIED_P4_OFFICIAL_ISSUE_TERMS["transraill"]
        record = {
            "id": "transraill",
            "company": "Transrail Lighting Limited",
            "symbol": "TRANSRAILL",
            "openDate": "2024-12-19",
            "issueSizeCr": None,
            "freshIssueCr": None,
            "ofsCr": None,
            "issueComposition": None,
            "sources": [],
            "observations": {},
        }
        changed = mod.apply_entry("transraill", record, entry)
        self.assertEqual(changed, ["issueSizeCr"])
        self.assertEqual(record["issueSizeCr"], 838.912)
        self.assertIsNone(record["issueComposition"])
        self.assertIsNone(record["freshIssueCr"])
        self.assertIsNone(record["ofsCr"])

    def test_wrong_identity_is_rejected(self):
        entry = mod.VERIFIED_P4_OFFICIAL_ISSUE_TERMS["carraro"]
        record = {
            "id": "carraro",
            "company": "Carraro India Limited",
            "symbol": "WRONG",
            "openDate": "2024-12-20",
            "sources": [],
            "observations": {},
        }
        self.assertFalse(mod.identity_matches("carraro", record, entry))
        self.assertEqual(mod.apply_entry("carraro", record, entry), [])


if __name__ == "__main__":
    unittest.main()
