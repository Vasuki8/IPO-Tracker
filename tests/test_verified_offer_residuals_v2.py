import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "apply_verified_offer_residuals_v2.py"
spec = importlib.util.spec_from_file_location("apply_verified_offer_residuals_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class VerifiedOfferResidualsV2Tests(unittest.TestCase):
    def test_exact_residual_entries_are_registered(self):
        expected = {
            "rambhajo": ("Advit Jewels Limited", "RAMBHAJO", "2026-06-23"),
            "aastha": ("Aastha Spintex Limited", "AASTHA", "2026-06-29"),
            "aye": ("Aye Finance Limited", "AYE", "2026-02-09"),
            "csm": ("CSM Technologies Limited", "CSM", "2026-06-24"),
            "innovision": ("Innovision Limited", "INNOVISION", "2026-03-10"),
            "jnpr": ("Juniper Green Energy Limited", "JNPR", "2026-07-30"),
        }
        for record_id, identity in expected.items():
            entry = mod.base.VERIFIED_RECENT_OFFER_FIELDS[record_id]
            self.assertEqual(
                (entry["company"], entry["symbol"], entry["openDate"]),
                identity,
            )
            self.assertTrue(entry["sourceUrl"].startswith("https://"))

    def test_aye_zero_promoter_shareholding_is_valid_and_fill_only(self):
        entry = mod.base.VERIFIED_RECENT_OFFER_FIELDS["aye"]
        self.assertEqual(entry["fields"]["shareholding"]["promoterPreIssuePct"], 0.0)
        self.assertIn("nsearchives.nseindia.com", entry["sourceUrl"])

        record = {
            "id": "aye",
            "company": "Aye Finance Limited",
            "symbol": "AYE",
            "openDate": "2026-02-09",
            "sources": [],
            "observations": {},
        }
        changed = mod.base.apply_verified_offer_fields(record, entry)
        self.assertEqual(changed, ["shareholding"])
        self.assertEqual(record["shareholding"]["promoterPreIssuePct"], 0.0)

        record["shareholding"] = {"promoterPreIssuePct": 1.0}
        self.assertEqual(mod.base.apply_verified_offer_fields(record, entry), [])
        self.assertEqual(record["shareholding"]["promoterPreIssuePct"], 1.0)

    def test_csm_and_juniper_intermediaries_are_exact(self):
        csm = mod.base.VERIFIED_RECENT_OFFER_FIELDS["csm"]["fields"]
        self.assertEqual(csm["registrar"], "KFin Technologies Limited")
        self.assertEqual(csm["leadManagers"], ["Keynote Financial Services Limited"])
        jnpr = mod.base.VERIFIED_RECENT_OFFER_FIELDS["jnpr"]["fields"]
        self.assertEqual(jnpr["registrar"], "KFin Technologies Limited")

    def test_advit_and_innovision_objects_remain_structured_lists(self):
        advit = mod.base.VERIFIED_RECENT_OFFER_FIELDS["rambhajo"]["fields"]["objectsOfIssue"]
        innovision = mod.base.VERIFIED_RECENT_OFFER_FIELDS["innovision"]["fields"]["objectsOfIssue"]
        self.assertEqual(len(advit), 3)
        self.assertEqual(len(innovision), 3)
        self.assertTrue(any("working capital" in item.lower() for item in advit))
        self.assertTrue(any("working capital" in item.lower() for item in innovision))
        self.assertTrue(any("general corporate" in item.lower() for item in innovision))

    def test_wrong_identity_is_rejected(self):
        entry = mod.base.VERIFIED_RECENT_OFFER_FIELDS["jnpr"]
        record = {
            "id": "jnpr",
            "company": "Juniper Green Energy Limited",
            "symbol": "OTHER",
            "openDate": "2026-07-30",
            "sources": [],
            "observations": {},
        }
        self.assertEqual(mod.base.apply_verified_offer_fields(record, entry), [])


if __name__ == "__main__":
    unittest.main()
