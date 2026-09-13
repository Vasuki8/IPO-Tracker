import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "prune_p4_verified_non_ipo.py"
spec = importlib.util.spec_from_file_location("prune_p4_verified_non_ipo", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

TODAY = date(2026, 9, 13)


class P4VerifiedNonIPOCleanupTests(unittest.TestCase):
    def record(self, company, symbol, opened, exchange="NSE"):
        return {
            "id": symbol.lower(),
            "company": company,
            "symbol": symbol,
            "exchange": exchange,
            "openDate": opened,
        }

    def test_three_verified_exact_identities_are_pruned(self):
        rows = (
            self.record("Aegis Vopak Terminals Limited", "AVTL29", "2025-05-26"),
            self.record("Afcons Infrastructure Limited", "84AIL28", "2024-10-25"),
            self.record("Adani Enterprises Limited", "ADANIENPP1", "2026-01-06"),
        )
        for row in rows:
            with self.subTest(symbol=row["symbol"]):
                self.assertTrue(mod.should_prune(row, today=TODAY))

    def test_value360_and_numeric_equities_are_preserved(self):
        rows = (
            self.record("Value 360 Communications Limited", "VALUE360", "2026-05-04", "NSE Emerge"),
            self.record("3M India Limited", "3MINDIA", "2025-01-01"),
            self.record("360 ONE WAM Limited", "360ONE", "2025-01-01"),
        )
        for row in rows:
            with self.subTest(symbol=row["symbol"]):
                self.assertFalse(mod.should_prune(row, today=TODAY))

    def test_generic_partly_paid_symbol_is_not_pruned(self):
        row = self.record("Example Limited", "EXAMPLEPP1", "2026-01-06")
        self.assertFalse(mod.should_prune(row, today=TODAY))

    def test_adani_symbol_with_different_event_date_is_preserved(self):
        row = self.record("Adani Enterprises Limited", "ADANIENPP1", "2025-11-25")
        self.assertFalse(mod.should_prune(row, today=TODAY))

    def test_same_issuer_real_equity_ipo_symbol_is_preserved(self):
        rows = (
            self.record("Aegis Vopak Terminals Limited", "AEGISVOPAK", "2025-05-26"),
            self.record("Afcons Infrastructure Limited", "AFCONS", "2024-10-25"),
        )
        for row in rows:
            with self.subTest(symbol=row["symbol"]):
                self.assertFalse(mod.should_prune(row, today=TODAY))

    def test_non_nse_copy_is_not_pruned(self):
        row = self.record("Afcons Infrastructure Limited", "84AIL28", "2024-10-25", "BSE")
        self.assertFalse(mod.should_prune(row, today=TODAY))

    def test_payload_removes_only_verified_rows(self):
        payload = {
            "ipos": [
                self.record("Aegis Vopak Terminals Limited", "AVTL29", "2025-05-26"),
                self.record("Value 360 Communications Limited", "VALUE360", "2026-05-04", "NSE Emerge"),
                self.record("Afcons Infrastructure Limited", "AFCONS", "2024-10-25"),
                self.record("Adani Enterprises Limited", "ADANIENPP1", "2026-01-06"),
            ],
            "meta": {"recordCount": 4},
        }
        cleaned, removed = mod.prune_payload(payload, today=TODAY)
        self.assertEqual([r["symbol"] for r in cleaned["ipos"]], ["VALUE360", "AFCONS"])
        self.assertEqual([r["symbol"] for r in removed], ["AVTL29", "ADANIENPP1"])
        self.assertEqual(cleaned["meta"]["recordCount"], 2)


if __name__ == "__main__":
    unittest.main()
