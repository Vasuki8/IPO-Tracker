import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "apply_verified_recent_offer_fields.py"
spec = importlib.util.spec_from_file_location("apply_verified_recent_offer_fields", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class VerifiedRecentOfferFieldTests(unittest.TestCase):
    def test_registry_covers_all_current_p2_offer_gap_records(self):
        expected = {
            "sunshine", "symbiotec", "pranav", "arcil", "augmont", "glasswall",
            "lccproject", "lumino", "mpimanipal", "prasolchem", "steamhouse", "tempsens",
            "rambhajo", "aastha",
        }
        self.assertEqual(set(mod.VERIFIED_RECENT_OFFER_FIELDS), expected)

    def test_fill_only_with_strict_identity_guards(self):
        entry = mod.VERIFIED_RECENT_OFFER_FIELDS["pranav"]
        record = {
            "id": "pranav",
            "company": "Pranav Constructions Limited",
            "symbol": "PRANAV",
            "openDate": "2026-09-07",
            "sources": [],
            "observations": {},
            "shareholding": {"promoters": ["Pranav Kiran Ashar", "Ravi Ramalingam"]},
        }
        changed = mod.apply_verified_offer_fields(record, entry)
        self.assertEqual(set(changed), {"registrar", "shareholding"})
        self.assertEqual(record["registrar"], "KFin Technologies Limited")
        self.assertEqual(record["shareholding"]["promoterPreIssuePct"], 63.35)
        self.assertEqual(record["shareholding"]["promoters"], ["Pranav Kiran Ashar", "Ravi Ramalingam"])

        existing = dict(record)
        existing["registrar"] = "Primary Registrar"
        existing["shareholding"] = {"promoterPreIssuePct": 60.0}
        self.assertEqual(mod.apply_verified_offer_fields(existing, entry), [])
        self.assertEqual(existing["registrar"], "Primary Registrar")
        self.assertEqual(existing["shareholding"]["promoterPreIssuePct"], 60.0)

    def test_wrong_symbol_date_or_company_is_rejected(self):
        entry = mod.VERIFIED_RECENT_OFFER_FIELDS["steamhouse"]
        base = {
            "id": "steamhouse",
            "company": "Steamhouse India Limited",
            "symbol": "STEAMHOUSE",
            "openDate": "2026-09-09",
            "sources": [],
        }
        self.assertEqual(mod.apply_verified_offer_fields(dict(base, symbol="OTHER"), entry), [])
        self.assertEqual(mod.apply_verified_offer_fields(dict(base, openDate="2026-09-10"), entry), [])
        self.assertEqual(mod.apply_verified_offer_fields(dict(base, company="Other Limited"), entry), [])

    def test_shareholding_values_are_bounded_and_exact_examples_are_retained(self):
        self.assertEqual(mod.VERIFIED_RECENT_OFFER_FIELDS["arcil"]["fields"]["shareholding"]["promoterPreIssuePct"], 89.68)
        self.assertEqual(mod.VERIFIED_RECENT_OFFER_FIELDS["glasswall"]["fields"]["shareholding"]["promoterPreIssuePct"], 61.53)
        self.assertEqual(mod.VERIFIED_RECENT_OFFER_FIELDS["tempsens"]["fields"]["shareholding"]["promoterPreIssuePct"], 80.52)
        for entry in mod.VERIFIED_RECENT_OFFER_FIELDS.values():
            shareholding = (entry.get("fields") or {}).get("shareholding") or {}
            if "promoterPreIssuePct" in shareholding:
                self.assertGreaterEqual(shareholding["promoterPreIssuePct"], 0)
                self.assertLessEqual(shareholding["promoterPreIssuePct"], 100)

    def test_sunshine_and_symbiotec_fallbacks_have_complete_offer_gap_payloads(self):
        required = {"registrar", "leadManagers", "promoters", "objectsOfIssue", "financials", "shareholding"}
        for record_id in ("sunshine", "symbiotec"):
            self.assertTrue(required.issubset(mod.VERIFIED_RECENT_OFFER_FIELDS[record_id]["fields"]))

    def test_advit_objects_are_from_official_sebi_abridged_prospectus(self):
        entry = mod.VERIFIED_RECENT_OFFER_FIELDS["rambhajo"]
        self.assertEqual(entry["company"], "Advit Jewels Limited")
        self.assertEqual(entry["symbol"], "RAMBHAJO")
        self.assertEqual(entry["openDate"], "2026-06-23")
        self.assertIn("sebi.gov.in/sebi_data/commondocs/", entry["sourceUrl"])
        objects = entry["fields"]["objectsOfIssue"]
        self.assertEqual(len(objects), 3)
        self.assertTrue(any("working capital" in item.lower() for item in objects))
        self.assertTrue(any("borrowings" in item.lower() for item in objects))
        self.assertTrue(any("general corporate" in item.lower() for item in objects))

    def test_aastha_registrar_is_official_and_fill_only(self):
        entry = mod.VERIFIED_RECENT_OFFER_FIELDS["aastha"]
        self.assertEqual(entry["company"], "Aastha Spintex Limited")
        self.assertEqual(entry["symbol"], "AASTHA")
        self.assertEqual(entry["openDate"], "2026-06-29")
        self.assertEqual(entry["fields"]["registrar"], "Bigshare Services Private Limited")
        self.assertIn("sebi.gov.in/sebi_data/attachdocs/", entry["sourceUrl"])

        record = {
            "id": "aastha",
            "company": "Aastha Spintex Limited",
            "symbol": "AASTHA",
            "openDate": "2026-06-29",
            "registrar": None,
            "sources": [],
            "observations": {},
        }
        self.assertEqual(mod.apply_verified_offer_fields(record, entry), ["registrar"])
        self.assertEqual(record["registrar"], "Bigshare Services Private Limited")

        record["registrar"] = "Existing Registrar"
        self.assertEqual(mod.apply_verified_offer_fields(record, entry), [])
        self.assertEqual(record["registrar"], "Existing Registrar")


if __name__ == "__main__":
    unittest.main()
