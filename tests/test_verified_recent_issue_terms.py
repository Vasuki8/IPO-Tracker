import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "apply_verified_recent_issue_terms.py"
spec = importlib.util.spec_from_file_location("apply_verified_recent_issue_terms", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


EXPECTED_IDS = {
    "spectraa", "sunshine", "symbiotec", "lumino", "abh", "ashutosh", "horizonind", "madhurknit",
    "perniaspop", "qualiance", "momsbelief", "shankesh", "shantiinor", "skytech", "sumax",
}


class VerifiedRecentIssueTermTests(unittest.TestCase):
    def test_registry_covers_all_reviewed_current_and_recent_issue_term_gaps(self):
        self.assertEqual(set(mod.VERIFIED_RECENT_ISSUE_TERMS), EXPECTED_IDS)
        for record_id, entry in mod.VERIFIED_RECENT_ISSUE_TERMS.items():
            self.assertTrue(entry["sourceUrl"].startswith("https://"), record_id)
            self.assertGreater(entry["issueSizeCr"], 0, record_id)
            self.assertGreaterEqual(entry["freshIssueCr"], 0, record_id)
            self.assertGreaterEqual(entry["ofsCr"], 0, record_id)
            self.assertAlmostEqual(
                entry["issueSizeCr"], entry["freshIssueCr"] + entry["ofsCr"], places=2, msg=record_id
            )

    def test_representative_fresh_only_and_fresh_plus_ofs_terms(self):
        self.assertEqual(mod.VERIFIED_RECENT_ISSUE_TERMS["abh"]["ofsCr"], 0.0)
        self.assertEqual(mod.VERIFIED_RECENT_ISSUE_TERMS["horizonind"]["freshIssueCr"], 2600.0)
        self.assertEqual(mod.VERIFIED_RECENT_ISSUE_TERMS["sunshine"]["freshIssueCr"], 172.8)
        self.assertEqual(mod.VERIFIED_RECENT_ISSUE_TERMS["sunshine"]["ofsCr"], 109.34)
        self.assertEqual(mod.VERIFIED_RECENT_ISSUE_TERMS["symbiotec"]["ofsCr"], 1607.0)
        self.assertEqual(mod.VERIFIED_RECENT_ISSUE_TERMS["sumax"]["issueSizeCr"], 53.4)
        self.assertEqual(mod.VERIFIED_RECENT_ISSUE_TERMS["spectraa"]["issueSizeCr"], 42.52)
        self.assertEqual(mod.VERIFIED_RECENT_ISSUE_TERMS["spectraa"]["freshIssueCr"], 38.42)
        self.assertEqual(mod.VERIFIED_RECENT_ISSUE_TERMS["spectraa"]["ofsCr"], 4.10)

    def test_fill_only_and_provenance(self):
        entry = mod.VERIFIED_RECENT_ISSUE_TERMS["sunshine"]
        record = {
            "id": "sunshine",
            "company": "Sunshine Pictures Limited",
            "symbol": "SUNSHINE",
            "openDate": "2026-08-18",
            "sources": [],
            "observations": {},
        }
        changed = mod.apply_verified_issue_terms(record, entry)
        self.assertIn("issueSizeCr", changed)
        self.assertIn("issueComposition", changed)
        self.assertEqual(record["issueSizeCr"], 282.14)
        self.assertEqual(record["freshIssueCr"], 172.8)
        self.assertEqual(record["ofsCr"], 109.34)
        self.assertEqual(record["issueComposition"]["totalIssueSizeCr"], 282.14)
        self.assertEqual(record["observations"]["VerifiedIssueTerms"]["ofsCr"], 109.34)
        self.assertTrue(any(s.get("url") == entry["sourceUrl"] for s in record["sources"]))

        before = dict(record)
        self.assertEqual(mod.apply_verified_issue_terms(record, entry), [])
        self.assertEqual(record["issueSizeCr"], before["issueSizeCr"])

    def test_spectraa_fills_missing_composition_without_overwriting_total(self):
        entry = mod.VERIFIED_RECENT_ISSUE_TERMS["spectraa"]
        record = {
            "id": "spectraa",
            "company": "SpectraA Technology Solutions Limited",
            "symbol": "SPECTRAA",
            "openDate": "2026-09-17",
            "issueSizeCr": 42.52,
            "sources": [],
            "observations": {},
        }

        changed = mod.apply_verified_issue_terms(record, entry)

        self.assertNotIn("issueSizeCr", changed)
        self.assertEqual(record["issueSizeCr"], 42.52)
        self.assertEqual(record["freshIssueCr"], 38.42)
        self.assertEqual(record["ofsCr"], 4.10)
        self.assertIn("issueComposition", changed)
        self.assertEqual(record["issueComposition"]["totalIssueSizeCr"], 42.52)
        self.assertEqual(record["issueComposition"]["freshIssueCr"], 38.42)
        self.assertEqual(record["issueComposition"]["ofsCr"], 4.10)

    def test_wrong_identity_is_rejected(self):
        entry = mod.VERIFIED_RECENT_ISSUE_TERMS["abh"]
        base = {
            "id": "abh",
            "company": "ABH Healthcare Limited",
            "symbol": "ABH",
            "openDate": "2026-08-24",
        }
        self.assertEqual(mod.apply_verified_issue_terms(dict(base, symbol="OTHER"), entry), [])
        self.assertEqual(mod.apply_verified_issue_terms(dict(base, openDate="2026-08-25"), entry), [])
        self.assertEqual(mod.apply_verified_issue_terms(dict(base, company="Other Healthcare Limited"), entry), [])

    def test_inconsistent_entry_is_rejected(self):
        entry = dict(mod.VERIFIED_RECENT_ISSUE_TERMS["abh"], issueSizeCr=999.0)
        record = {
            "id": "abh",
            "company": "ABH Healthcare Limited",
            "symbol": "ABH",
            "openDate": "2026-08-24",
        }
        self.assertEqual(mod.apply_verified_issue_terms(record, entry), [])
        self.assertNotIn("issueSizeCr", record)


if __name__ == "__main__":
    unittest.main()
