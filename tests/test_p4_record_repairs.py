import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "apply_p4_record_repairs.py"
spec = importlib.util.spec_from_file_location("apply_p4_record_repairs", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class P4RecordRepairsTests(unittest.TestCase):
    def test_repairs_aegis_corrupted_debt_symbol_and_missing_terms(self):
        entry = mod.VERIFIED_IDENTITY_REPAIRS["avtl29"]
        record = {
            "id": "avtl29",
            "company": "Aegis Vopak Terminals Limited",
            "symbol": "AVTL29",
            "openDate": "2025-05-26",
            "priceBand": None,
            "lotSize": None,
            "sources": [],
            "observations": {},
        }
        changed = mod.apply_identity_repair("avtl29", record, entry)
        self.assertEqual(record["symbol"], "AEGISVOPAK")
        self.assertEqual(record["priceBand"], {"min": 223.0, "max": 235.0})
        self.assertEqual(record["lotSize"], 63)
        self.assertEqual(set(changed), {"symbol", "priceBand", "lotSize"})
        self.assertTrue(any(s.get("name") == entry["sourceName"] for s in record["sources"]))

    def test_identity_repair_never_overwrites_existing_terms(self):
        entry = mod.VERIFIED_IDENTITY_REPAIRS["84ail28"]
        record = {
            "id": "84ail28",
            "company": "Afcons Infrastructure Limited",
            "symbol": "84AIL28",
            "openDate": "2024-10-25",
            "priceBand": {"min": 441.0, "max": 463.0},
            "lotSize": 99,
            "sources": [],
            "observations": {},
        }
        changed = mod.apply_identity_repair("84ail28", record, entry)
        self.assertEqual(record["symbol"], "AFCONS")
        self.assertEqual(record["priceBand"], {"min": 441.0, "max": 463.0})
        self.assertEqual(record["lotSize"], 99)
        self.assertEqual(changed, ["symbol"])

    def test_wrong_identity_is_rejected(self):
        entry = mod.VERIFIED_IDENTITY_REPAIRS["avtl29"]
        record = {
            "id": "avtl29",
            "company": "Aegis Vopak Terminals Limited",
            "symbol": "AVTL29",
            "openDate": "2025-05-27",
            "priceBand": None,
            "lotSize": None,
        }
        self.assertEqual(mod.apply_identity_repair("avtl29", record, entry), [])
        self.assertEqual(record["symbol"], "AVTL29")

    def test_auxiliary_event_gets_source_backed_not_applicable_resolution(self):
        entry = mod.AVAILABILITY_RESOLUTIONS["c2cw"]
        record = {
            "id": "c2cw",
            "company": "C2C Advanced Systems Limited- Withdrawal Window",
            "symbol": "C2CW",
            "openDate": "2024-11-26",
            "sources": [],
            "observations": {},
        }
        with patch.object(mod.core, "now_ist") as now_ist:
            now_ist.return_value.isoformat.return_value = "2026-09-13T22:30:00+05:30"
            changed = mod.apply_availability_resolution("c2cw", record, entry)
        self.assertEqual(set(changed), set(entry["fields"]))
        for field in entry["fields"]:
            resolution = record["dataAvailability"][field]
            self.assertEqual(resolution["status"], "not-applicable")
            self.assertEqual(resolution["sourceUrl"], entry["sourceUrl"])
            self.assertTrue(resolution["reason"])
        self.assertTrue(any(s.get("name") == entry["sourceName"] for s in record["sources"]))

    def test_current_postponed_and_withdrawn_rows_are_registered(self):
        expected = {
            "icel": {
                "company": "IC Electricals Company Limited-Issue postponed",
                "symbol": "ICEL",
                "openDate": "2026-06-25",
                "sourceUrl": "https://www.nseindia.com/market-data/issue-information?series=SME&symbol=ICEL&type=Active",
            },
            "spgcl": {
                "company": "Sri Priyanka Geo Commex Limited-Issue Withdrawn",
                "symbol": "SPGCL",
                "openDate": "2026-06-24",
                "sourceUrl": "https://www.nseindia.com/market-data/issue-information?series=SME&symbol=SPGCL&type=Active",
            },
        }
        for record_id, values in expected.items():
            entry = mod.AVAILABILITY_RESOLUTIONS[record_id]
            for key, value in values.items():
                self.assertEqual(entry[key], value)
            self.assertEqual(entry["fields"], mod._EVENT_IPO_FIELDS)

    def test_postponed_and_withdrawn_rows_resolve_all_structural_gaps(self):
        rows = (
            (
                "icel",
                "IC Electricals Company Limited-Issue postponed",
                "ICEL",
                "2026-06-25",
            ),
            (
                "spgcl",
                "Sri Priyanka Geo Commex Limited-Issue Withdrawn",
                "SPGCL",
                "2026-06-24",
            ),
        )
        for record_id, company, symbol, open_date in rows:
            record = {
                "id": record_id,
                "company": company,
                "symbol": symbol,
                "openDate": open_date,
                "sources": [],
                "observations": {},
            }
            entry = mod.AVAILABILITY_RESOLUTIONS[record_id]
            changed = mod.apply_availability_resolution(record_id, record, entry)
            self.assertEqual(set(changed), set(mod._EVENT_IPO_FIELDS))
            self.assertTrue(all(
                record["dataAvailability"][field]["status"] == "not-applicable"
                for field in mod._EVENT_IPO_FIELDS
            ))

    def test_postponed_icel_registry_does_not_match_later_canonical_issue(self):
        entry = mod.AVAILABILITY_RESOLUTIONS["icel"]
        later_issue = {
            "id": "icel",
            "company": "IC Electricals Company Limited",
            "symbol": "ICEL",
            "openDate": "2026-07-03",
            "sources": [],
            "observations": {},
        }
        self.assertEqual(mod.apply_availability_resolution("icel", later_issue, entry), [])
        self.assertNotIn("dataAvailability", later_issue)

    def test_existing_availability_decision_is_not_overwritten(self):
        entry = mod.AVAILABILITY_RESOLUTIONS["adanienpp1"]
        record = {
            "id": "adanienpp1",
            "company": "Adani Enterprises Limited",
            "symbol": "ADANIENPP1",
            "openDate": "2026-01-06",
            "dataAvailability": {
                "exchange.lotSize": {
                    "status": "source-unavailable",
                    "reason": "existing decision",
                }
            },
            "sources": [],
            "observations": {},
        }
        changed = mod.apply_availability_resolution("adanienpp1", record, entry)
        self.assertNotIn("exchange.lotSize", changed)
        self.assertEqual(
            record["dataAvailability"]["exchange.lotSize"]["reason"],
            "existing decision",
        )
        self.assertEqual(
            record["dataAvailability"]["exchange.issueSizeCr"]["status"],
            "not-applicable",
        )


if __name__ == "__main__":
    unittest.main()
