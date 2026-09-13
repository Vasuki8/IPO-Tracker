import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "apply_p4_record_repairs_v2.py"
spec = importlib.util.spec_from_file_location("apply_p4_record_repairs_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class P4RecordRepairsV2Tests(unittest.TestCase):
    def test_duplicate_rsl_selects_only_withdrawal_event_for_resolution(self):
        entry = mod.base.AVAILABILITY_RESOLUTIONS["rsl"]
        listed = {
            "id": "rsl",
            "company": "Rajputana Stainless Limited",
            "symbol": "RSL",
            "openDate": "2026-03-12",
            "sources": [],
            "observations": {},
        }
        withdrawal = {
            "id": "rsl",
            "company": "Rajputana Stainless Limited-Special Withdrawal Option",
            "symbol": "RSL",
            "openDate": "2026-03-12",
            "sources": [],
            "observations": {},
        }

        selected = mod.select_unique_identity([listed, withdrawal], "rsl", entry)
        self.assertIs(selected, withdrawal)
        changed = mod.base.apply_availability_resolution("rsl", selected, entry)
        self.assertEqual(set(changed), set(entry["fields"]))
        self.assertNotIn("dataAvailability", listed)
        for field in entry["fields"]:
            self.assertEqual(withdrawal["dataAvailability"][field]["status"], "not-applicable")

    def test_selector_refuses_same_identity_duplicates(self):
        entry = mod.base.AVAILABILITY_RESOLUTIONS["c2cw"]
        row = {
            "id": "c2cw",
            "company": "C2C Advanced Systems Limited- Withdrawal Window",
            "symbol": "C2CW",
            "openDate": "2024-11-26",
        }
        self.assertIsNone(mod.select_unique_identity([dict(row), dict(row)], "c2cw", entry))

    def test_identity_repair_selection_still_uses_all_exact_guards(self):
        entry = mod.base.VERIFIED_IDENTITY_REPAIRS["avtl29"]
        wrong_date = {
            "id": "avtl29",
            "company": "Aegis Vopak Terminals Limited",
            "symbol": "AVTL29",
            "openDate": "2025-05-27",
        }
        exact = {
            "id": "avtl29",
            "company": "Aegis Vopak Terminals Limited",
            "symbol": "AVTL29",
            "openDate": "2025-05-26",
        }
        self.assertIs(mod.select_unique_identity([wrong_date, exact], "avtl29", entry), exact)


if __name__ == "__main__":
    unittest.main()
