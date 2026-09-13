import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "apply_verified_lot_sizes.py"
spec = importlib.util.spec_from_file_location("apply_verified_lot_sizes", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class VerifiedLotSizeTests(unittest.TestCase):
    def test_registry_contains_final_two_p1_lots(self):
        self.assertEqual(mod.VERIFIED_LOT_SIZES["jsipl"]["lotSize"], 161)
        self.assertEqual(mod.VERIFIED_LOT_SIZES["ssretail"]["lotSize"], 35)

    def test_fill_only_with_strict_identity_guards(self):
        entry = mod.VERIFIED_LOT_SIZES["jsipl"]
        record = {
            "id": "jsipl",
            "company": "Jindal Supreme (India) Limited",
            "symbol": "JSIPL",
            "openDate": "2026-09-16",
            "priceBand": {"min": 88, "max": 93},
            "sources": [],
            "observations": {},
        }
        changed = mod.apply_verified_lot_size(record, entry)
        self.assertEqual(changed, ["lotSize"])
        self.assertEqual(record["lotSize"], 161)
        self.assertEqual(record["minInvestment"], 14973.0)
        self.assertEqual(record["observations"]["IssuerTerms"]["lotSize"], 161)
        self.assertTrue(any(s.get("url") == entry["sourceUrl"] for s in record["sources"]))

        existing = dict(record)
        existing["lotSize"] = 200
        self.assertEqual(mod.apply_verified_lot_size(existing, entry), [])
        self.assertEqual(existing["lotSize"], 200)

    def test_wrong_symbol_or_date_is_rejected(self):
        entry = mod.VERIFIED_LOT_SIZES["ssretail"]
        base = {
            "id": "ssretail",
            "company": "SS Retail Limited",
            "symbol": "SSRETAIL",
            "openDate": "2026-09-16",
            "sources": [],
        }
        wrong_symbol = dict(base, symbol="OTHER")
        wrong_date = dict(base, openDate="2026-09-17")
        self.assertEqual(mod.apply_verified_lot_size(wrong_symbol, entry), [])
        self.assertEqual(mod.apply_verified_lot_size(wrong_date, entry), [])


if __name__ == "__main__":
    unittest.main()
