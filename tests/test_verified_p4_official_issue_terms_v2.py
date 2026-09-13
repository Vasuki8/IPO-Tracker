import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "apply_verified_p4_official_issue_terms_v2.py"
spec = importlib.util.spec_from_file_location("apply_verified_p4_official_issue_terms_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class VerifiedP4OfficialIssueTermsV2Tests(unittest.TestCase):
    def test_batch2_values_and_official_sources(self):
        expected = {
            "damcapital": (840.252, 0.0, 840.252),
            "suraksha": (846.249, 0.0, 846.249),
            "ventive": (1600.0, 1600.0, 0.0),
            "igil": (4225.0, None, None),
            "iks": (2497.923, None, None),
            "cewater": (500.326, None, None),
        }
        for record_id, values in expected.items():
            entry = mod.base.VERIFIED_P4_OFFICIAL_ISSUE_TERMS[record_id]
            self.assertEqual((entry["issueSizeCr"], entry["freshIssueCr"], entry["ofsCr"]), values)
            self.assertIn("sebi.gov.in", entry["sourceUrl"])

    def test_full_ofs_entry_creates_composition(self):
        entry = mod.base.VERIFIED_P4_OFFICIAL_ISSUE_TERMS["suraksha"]
        record = {
            "id": "suraksha",
            "company": "Suraksha Diagnostic Limited",
            "symbol": "SURAKSHA",
            "openDate": "2024-11-29",
            "issueSizeCr": None,
            "freshIssueCr": None,
            "ofsCr": None,
            "issueComposition": None,
            "sources": [],
            "observations": {},
        }
        changed = mod.base.apply_entry("suraksha", record, entry)
        self.assertEqual(record["issueSizeCr"], 846.249)
        self.assertEqual(record["freshIssueCr"], 0.0)
        self.assertEqual(record["ofsCr"], 846.249)
        self.assertIn("issueComposition", changed)

    def test_full_fresh_entry_creates_zero_ofs(self):
        entry = mod.base.VERIFIED_P4_OFFICIAL_ISSUE_TERMS["ventive"]
        record = {
            "id": "ventive",
            "company": "Ventive Hospitality Limited",
            "symbol": "VENTIVE",
            "openDate": "2024-12-20",
            "issueSizeCr": None,
            "freshIssueCr": None,
            "ofsCr": None,
            "issueComposition": None,
            "sources": [],
            "observations": {},
        }
        changed = mod.base.apply_entry("ventive", record, entry)
        self.assertEqual(record["freshIssueCr"], 1600.0)
        self.assertEqual(record["ofsCr"], 0.0)
        self.assertIn("issueComposition", changed)

    def test_size_only_entries_cannot_create_composition(self):
        for record_id in ("igil", "iks", "cewater"):
            entry = mod.base.VERIFIED_P4_OFFICIAL_ISSUE_TERMS[record_id]
            record = {
                "id": record_id,
                "company": entry["company"],
                "symbol": entry["symbol"],
                "openDate": entry["openDate"],
                "issueSizeCr": None,
                "freshIssueCr": None,
                "ofsCr": None,
                "issueComposition": None,
                "sources": [],
                "observations": {},
            }
            changed = mod.base.apply_entry(record_id, record, entry)
            self.assertEqual(changed, ["issueSizeCr"])
            self.assertIsNone(record["issueComposition"])
            self.assertIsNone(record["freshIssueCr"])
            self.assertIsNone(record["ofsCr"])

    def test_wrong_identity_rejected(self):
        entry = mod.base.VERIFIED_P4_OFFICIAL_ISSUE_TERMS["damcapital"]
        record = {
            "id": "damcapital",
            "company": "DAM Capital Advisors Limited",
            "symbol": "WRONG",
            "openDate": "2024-12-19",
            "sources": [],
            "observations": {},
        }
        self.assertEqual(mod.base.apply_entry("damcapital", record, entry), [])


if __name__ == "__main__":
    unittest.main()
