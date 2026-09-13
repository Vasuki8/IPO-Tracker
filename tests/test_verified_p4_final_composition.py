import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "apply_verified_p4_final_composition.py"
spec = importlib.util.spec_from_file_location("apply_verified_p4_final_composition", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class VerifiedP4FinalCompositionTests(unittest.TestCase):
    def test_registry_is_exactly_the_seven_residuals(self):
        self.assertEqual(
            set(mod.VERIFIED_P4_FINAL_COMPOSITION),
            {"igil", "iks", "krt", "anantam", "citiusinvt", "riit", "cubeinvit"},
        )

    def test_sources_are_official_nse_only(self):
        for record_id, entry in mod.VERIFIED_P4_FINAL_COMPOSITION.items():
            self.assertTrue(entry["sources"], record_id)
            for source in entry["sources"]:
                self.assertTrue(mod._valid_source(source), (record_id, source))
        self.assertFalse(mod._valid_source({"url": "https://example.com/x", "kind": "exchange"}))

    def _record(self, record_id, total):
        entry = mod.VERIFIED_P4_FINAL_COMPOSITION[record_id]
        return {
            "id": record_id,
            "company": entry["company"],
            "symbol": entry["symbol"],
            "openDate": entry["openDate"],
            "issueSizeCr": total,
            "freshIssueCr": None,
            "ofsCr": None,
            "issueComposition": None,
            "lotSize": 777,
            "priceBand": {"min": 1, "max": 2},
            "listingDate": "2099-01-01",
            "sources": [],
            "observations": {},
        }

    def test_mixed_igil_uses_exact_official_split(self):
        record = self._record("igil", 4225.0)
        changed = mod.apply_entry("igil", record, mod.VERIFIED_P4_FINAL_COMPOSITION["igil"])
        self.assertIn("issueComposition", changed)
        self.assertEqual(record["freshIssueCr"], 1475.0)
        self.assertEqual(record["ofsCr"], 2750.0)
        self.assertEqual(record["issueSizeCr"], 4225.0)

    def test_pure_ofs_rows_use_existing_source_backed_total(self):
        for record_id, total in (("iks", 2497.923), ("cubeinvit", 5000.0)):
            record = self._record(record_id, total)
            changed = mod.apply_entry(record_id, record, mod.VERIFIED_P4_FINAL_COMPOSITION[record_id])
            self.assertIn("issueComposition", changed, record_id)
            self.assertEqual(record["freshIssueCr"], 0.0, record_id)
            self.assertEqual(record["ofsCr"], total, record_id)
            self.assertEqual(record["issueSizeCr"], total, record_id)

    def test_pure_fresh_rows_use_existing_source_backed_total(self):
        totals = {"krt": 4800.0, "anantam": 400.0, "citiusinvt": 1105.0, "riit": 6000.0}
        for record_id, total in totals.items():
            record = self._record(record_id, total)
            changed = mod.apply_entry(record_id, record, mod.VERIFIED_P4_FINAL_COMPOSITION[record_id])
            self.assertIn("issueComposition", changed, record_id)
            self.assertEqual(record["freshIssueCr"], total, record_id)
            self.assertEqual(record["ofsCr"], 0.0, record_id)
            self.assertEqual(record["issueSizeCr"], total, record_id)

    def test_wrong_identity_missing_total_and_wrong_total_are_rejected(self):
        entry = mod.VERIFIED_P4_FINAL_COMPOSITION["igil"]
        wrong = self._record("igil", 4225.0)
        wrong["symbol"] = "WRONG"
        self.assertEqual(mod.apply_entry("igil", wrong, entry), [])

        no_total = self._record("igil", None)
        self.assertEqual(mod.apply_entry("igil", no_total, entry), [])

        wrong_total = self._record("igil", 4000.0)
        self.assertEqual(mod.apply_entry("igil", wrong_total, entry), [])

    def test_fill_only_and_unrelated_fields_are_untouched(self):
        entry = mod.VERIFIED_P4_FINAL_COMPOSITION["anantam"]
        record = self._record("anantam", 400.0)
        record.update({
            "freshIssueCr": 111.0,
            "ofsCr": 222.0,
            "issueComposition": {"freshIssueCr": 111.0, "ofsCr": 222.0},
        })
        before = (record["issueSizeCr"], record["lotSize"], record["priceBand"], record["listingDate"])
        self.assertEqual(mod.apply_entry("anantam", record, entry), [])
        self.assertEqual(record["freshIssueCr"], 111.0)
        self.assertEqual(record["ofsCr"], 222.0)
        self.assertEqual((record["issueSizeCr"], record["lotSize"], record["priceBand"], record["listingDate"]), before)


if __name__ == "__main__":
    unittest.main()
