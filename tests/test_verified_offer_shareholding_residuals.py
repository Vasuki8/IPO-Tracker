import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "apply_verified_offer_shareholding_residuals.py"
spec = importlib.util.spec_from_file_location("apply_verified_offer_shareholding_residuals", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class VerifiedOfferShareholdingResidualTests(unittest.TestCase):
    def test_exact_official_shareholding_entries(self):
        expected = {
            "aastha": ("Aastha Spintex Limited", "AASTHA", "2026-06-29", 74.23),
            "innovision": ("Innovision Limited", "INNOVISION", "2026-03-10", 100.0),
            "jnpr": ("Juniper Green Energy Limited", "JNPR", "2026-07-30", 100.0),
            "shiprocket": ("Shiprocket Limited", "SHIPROCKET", "2026-08-12", 0.0),
        }
        self.assertEqual(set(mod.SHAREHOLDING_RESIDUALS), set(expected))
        for record_id, (company, symbol, open_date, pct) in expected.items():
            entry = mod.SHAREHOLDING_RESIDUALS[record_id]
            self.assertEqual((entry["company"], entry["symbol"], entry["openDate"]), (company, symbol, open_date))
            self.assertEqual(entry["fields"]["shareholding"]["promoterPreIssuePct"], pct)
            self.assertTrue(entry["sourceUrl"].startswith("https://"))

    def test_sources_are_official_or_issuer_owned(self):
        self.assertIn("aasthaspintex.com", mod.SHAREHOLDING_RESIDUALS["aastha"]["sourceUrl"])
        self.assertIn("nsearchives.nseindia.com", mod.SHAREHOLDING_RESIDUALS["innovision"]["sourceUrl"])
        self.assertIn("junipergreenenergy.com", mod.SHAREHOLDING_RESIDUALS["jnpr"]["sourceUrl"])
        self.assertIn("nsearchives.nseindia.com", mod.SHAREHOLDING_RESIDUALS["shiprocket"]["sourceUrl"])

    def test_zero_and_hundred_percent_are_valid_fill_only_values(self):
        for record_id in ("innovision", "jnpr", "shiprocket"):
            entry = mod.SHAREHOLDING_RESIDUALS[record_id]
            record = {
                "id": record_id,
                "company": entry["company"],
                "symbol": entry["symbol"],
                "openDate": entry["openDate"],
                "sources": [],
                "observations": {},
            }
            changed = mod.base.apply_verified_offer_fields(record, entry)
            self.assertEqual(changed, ["shareholding"])
            self.assertEqual(
                record["shareholding"]["promoterPreIssuePct"],
                entry["fields"]["shareholding"]["promoterPreIssuePct"],
            )

            record["shareholding"] = {"promoterPreIssuePct": 12.34}
            self.assertEqual(mod.base.apply_verified_offer_fields(record, entry), [])
            self.assertEqual(record["shareholding"]["promoterPreIssuePct"], 12.34)

    def test_wrong_identity_is_rejected(self):
        entry = mod.SHAREHOLDING_RESIDUALS["aastha"]
        base_record = {
            "id": "aastha",
            "company": "Aastha Spintex Limited",
            "symbol": "AASTHA",
            "openDate": "2026-06-29",
            "sources": [],
            "observations": {},
        }
        self.assertEqual(mod.base.apply_verified_offer_fields(dict(base_record, symbol="OTHER"), entry), [])
        self.assertEqual(mod.base.apply_verified_offer_fields(dict(base_record, openDate="2026-06-30"), entry), [])
        self.assertEqual(mod.base.apply_verified_offer_fields(dict(base_record, company="Other Limited"), entry), [])


if __name__ == "__main__":
    unittest.main()
