import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "apply_verified_lot_sizes.py"
spec = importlib.util.spec_from_file_location("apply_verified_lot_sizes", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


P2_IDS = {
    "abh", "annu", "ashutosh", "augmont", "deepa", "esds", "gaja", "horizonind", "htel",
    "kanohar", "lalithaa", "lumino", "madhurknit", "pranav", "priority", "perniaspop",
    "qualiance", "momsbelief", "shankesh", "shantiinor", "skytech", "skyways", "sumax",
    "sunshine", "symbiotec", "arcil", "glasswall", "karamtara", "lccproject", "mpimanipal",
    "prasolchem", "steamhouse", "tempsens", "rentomojo",
}


class VerifiedLotSizeTests(unittest.TestCase):
    def test_registry_contains_final_two_p1_lots(self):
        self.assertEqual(mod.VERIFIED_LOT_SIZES["jsipl"]["lotSize"], 161)
        self.assertEqual(mod.VERIFIED_LOT_SIZES["ssretail"]["lotSize"], 35)

    def test_registry_contains_all_p2_recent_lots(self):
        self.assertTrue(P2_IDS.issubset(mod.VERIFIED_LOT_SIZES))
        self.assertEqual(len(P2_IDS), 34)
        for record_id in P2_IDS:
            entry = mod.VERIFIED_LOT_SIZES[record_id]
            self.assertGreater(entry["lotSize"], 0, record_id)
            self.assertTrue(entry["symbol"], record_id)
            self.assertRegex(entry["openDate"], r"^2026-\d{2}-\d{2}$", record_id)
            self.assertTrue(entry["sourceUrl"].startswith("https://"), record_id)
            self.assertTrue(entry["sourceName"], record_id)
            self.assertTrue(entry["sourceKind"], record_id)

    def test_sme_registry_uses_base_bid_lot_not_two_lot_minimum(self):
        self.assertEqual(mod.VERIFIED_LOT_SIZES["ashutosh"]["lotSize"], 1200)
        self.assertEqual(mod.VERIFIED_LOT_SIZES["qualiance"]["lotSize"], 1000)
        self.assertEqual(mod.VERIFIED_LOT_SIZES["shantiinor"]["lotSize"], 1600)
        self.assertEqual(mod.VERIFIED_LOT_SIZES["skytech"]["lotSize"], 1600)

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
        self.assertEqual(record["observations"]["VerifiedTerms"]["lotSize"], 161)
        self.assertTrue(any(s.get("url") == entry["sourceUrl"] for s in record["sources"]))

        existing = dict(record)
        existing["lotSize"] = 200
        self.assertEqual(mod.apply_verified_lot_size(existing, entry), [])
        self.assertEqual(existing["lotSize"], 200)

    def test_wrong_symbol_date_or_company_is_rejected(self):
        entry = mod.VERIFIED_LOT_SIZES["ssretail"]
        base = {
            "id": "ssretail",
            "company": "SS Retail Limited",
            "symbol": "SSRETAIL",
            "openDate": "2026-09-16",
            "sources": [],
        }
        self.assertEqual(mod.apply_verified_lot_size(dict(base, symbol="OTHER"), entry), [])
        self.assertEqual(mod.apply_verified_lot_size(dict(base, openDate="2026-09-17"), entry), [])
        self.assertEqual(mod.apply_verified_lot_size(dict(base, company="Other Retail Limited"), entry), [])


if __name__ == "__main__":
    unittest.main()
