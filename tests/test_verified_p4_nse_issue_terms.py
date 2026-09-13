import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "apply_verified_p4_nse_issue_terms.py"
spec = importlib.util.spec_from_file_location("apply_verified_p4_nse_issue_terms", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class VerifiedP4NSEIssueTermsTests(unittest.TestCase):
    def test_registry_values_and_nse_only_sources(self):
        expected = {
            "abhapower": (38.544, 31.044, 7.5),
            "agarwaltuf": (62.63568, 62.63568, 0.0),
            "apexeco": (25.5442, 25.5442, 0.0),
            "dhanlaxmi": (23.804, 23.804, 0.0),
            "etml": (49.2594, 47.367, 1.8924),
            "nmsteel": (41.76, 41.76, 0.0),
            "rajputana": (24.70, 24.70, 0.0),
            "ganeshin": (98.5774, 98.5774, 0.0),
            "purpleuted": (32.8104, 32.8104, 0.0),
            "c2c": (99.0694, 99.0694, 0.0),
            "sfml": (50.0019, 50.0019, 0.0),
        }
        self.assertEqual(set(mod.VERIFIED_P4_NSE_ISSUE_TERMS), set(expected))
        for record_id, values in expected.items():
            entry = mod.VERIFIED_P4_NSE_ISSUE_TERMS[record_id]
            self.assertEqual((entry["issueSizeCr"], entry["freshIssueCr"], entry["ofsCr"]), values)
            self.assertTrue(entry["sourceUrls"])
            for url in entry["sourceUrls"]:
                self.assertTrue(mod._nse_official_url(url))

    def test_batch4_exact_identities(self):
        identities = {
            "etml": ("Emerald Tyre Manufacturers Limited", "ETML", "2024-12-05"),
            "nmsteel": ("NewMalayalam Steel Limited", "NMSTEEL", "2024-12-19"),
            "rajputana": ("Rajputana Biodiesel Limited", "RAJPUTANA", "2024-11-26"),
            "ganeshin": ("Ganesh Infraworld Limited", "GANESHIN", "2024-11-29"),
            "purpleuted": ("Purple United Sales Limited", "PURPLEUTED", "2024-12-11"),
            "c2c": ("C2C Advanced Systems Limited", "C2C", "2024-11-22"),
            "sfml": ("Supreme Facility Management Limited", "SFML", "2024-12-11"),
        }
        for record_id, (company, symbol, open_date) in identities.items():
            entry = mod.VERIFIED_P4_NSE_ISSUE_TERMS[record_id]
            record = {
                "id": record_id,
                "company": company,
                "symbol": symbol,
                "openDate": open_date,
                "issueSizeCr": None,
                "freshIssueCr": None,
                "ofsCr": None,
                "issueComposition": None,
                "sources": [],
                "observations": {},
            }
            changed = mod.apply_entry(record_id, record, entry)
            self.assertIn("issueSizeCr", changed, record_id)
            self.assertIn("issueComposition", changed, record_id)
            self.assertEqual(record["sources"][0]["kind"], "exchange", record_id)

    def test_full_entry_fills_composition_with_exchange_provenance(self):
        entry = mod.VERIFIED_P4_NSE_ISSUE_TERMS["abhapower"]
        record = {
            "id": "abhapower",
            "company": "Abha Power and Steel Limited",
            "symbol": "ABHAPOWER",
            "openDate": "2024-11-27",
            "issueSizeCr": None,
            "freshIssueCr": None,
            "ofsCr": None,
            "issueComposition": None,
            "sources": [],
            "observations": {},
        }
        changed = mod.apply_entry("abhapower", record, entry)
        self.assertEqual(record["issueSizeCr"], 38.544)
        self.assertEqual(record["freshIssueCr"], 31.044)
        self.assertEqual(record["ofsCr"], 7.5)
        self.assertIn("issueComposition", changed)
        self.assertEqual(record["sources"][0]["kind"], "exchange")

    def test_agarwal_records_official_rounding_note(self):
        entry = mod.VERIFIED_P4_NSE_ISSUE_TERMS["agarwaltuf"]
        self.assertIn("6,263.56", entry["officialNote"])
        self.assertIn("share-count", entry["sourceBasis"])
        record = {
            "id": "agarwaltuf",
            "company": "Agarwal Toughened Glass India Limited",
            "symbol": "AGARWALTUF",
            "openDate": "2024-11-28",
            "issueSizeCr": None,
            "freshIssueCr": None,
            "ofsCr": None,
            "issueComposition": None,
            "sources": [],
            "observations": {},
        }
        mod.apply_entry("agarwaltuf", record, entry)
        self.assertEqual(record["issueSizeCr"], 62.63568)
        self.assertIn("officialNote", record["issueComposition"])
        self.assertEqual(len(record["sources"]), 2)

    def test_fill_only_and_wrong_identity_rejected(self):
        entry = mod.VERIFIED_P4_NSE_ISSUE_TERMS["apexeco"]
        record = {
            "id": "apexeco",
            "company": "Apex Ecotech Limited",
            "symbol": "APEXECO",
            "openDate": "2024-11-27",
            "issueSizeCr": 99.0,
            "freshIssueCr": 99.0,
            "ofsCr": 0.0,
            "issueComposition": {"freshIssueCr": 99.0, "ofsCr": 0.0},
            "sources": [],
            "observations": {},
        }
        self.assertEqual(mod.apply_entry("apexeco", record, entry), [])
        self.assertEqual(record["issueSizeCr"], 99.0)

        wrong = dict(record)
        wrong["issueSizeCr"] = None
        wrong["symbol"] = "WRONG"
        self.assertEqual(mod.apply_entry("apexeco", wrong, entry), [])


if __name__ == "__main__":
    unittest.main()
