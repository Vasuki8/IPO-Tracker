import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "prune_p4_legacy_debt_symbols.py"
spec = importlib.util.spec_from_file_location("prune_p4_legacy_debt_symbols", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

TODAY = date(2026, 9, 13)


class P4LegacyDebtCleanupTests(unittest.TestCase):
    def test_known_coupon_maturity_symbols_are_pruned_with_nse_provenance(self):
        for symbol in ("935IIFL33", "790IHFL27", "975SCL35", "727NGEL36"):
            with self.subTest(symbol=symbol):
                record = {
                    "company": "Example Finance Limited",
                    "symbol": symbol,
                    "exchange": "NSE",
                    "openDate": "2026-02-17",
                }
                self.assertTrue(mod.should_prune(record, today=TODAY))

    def test_numeric_equity_tickers_are_preserved(self):
        for symbol in ("3MINDIA", "360ONE"):
            with self.subTest(symbol=symbol):
                record = {
                    "company": "Example Equity Limited",
                    "symbol": symbol,
                    "exchange": "NSE",
                    "openDate": "2026-02-17",
                }
                self.assertFalse(mod.should_prune(record, today=TODAY))

    def test_debt_like_symbol_without_nse_provenance_is_preserved(self):
        record = {
            "company": "Example Limited",
            "symbol": "935EXAMPLE33",
            "exchange": "BSE",
            "openDate": "2026-02-17",
            "sources": [{"name": "BSE", "url": "https://www.bseindia.com/example"}],
        }
        self.assertFalse(mod.should_prune(record, today=TODAY))

    def test_old_record_outside_p4_window_is_preserved(self):
        record = {
            "company": "Old Finance Limited",
            "symbol": "935OLD33",
            "exchange": "NSE",
            "openDate": "2023-01-01",
        }
        self.assertFalse(mod.should_prune(record, today=TODAY, history_days=730))

    def test_nse_source_provenance_is_enough_when_exchange_label_is_generic(self):
        record = {
            "company": "Example Finance Limited",
            "symbol": "935EXAMPLE33",
            "exchange": "Public Issue",
            "openDate": "2026-02-17",
            "sources": [
                {
                    "name": "NSE past issues",
                    "url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
                }
            ],
        }
        self.assertTrue(mod.should_prune(record, today=TODAY))

    def test_payload_cleanup_only_removes_narrow_matches(self):
        payload = {
            "ipos": [
                {
                    "id": "debt",
                    "company": "Debt Finance Limited",
                    "symbol": "935DEBT33",
                    "exchange": "NSE",
                    "openDate": "2026-02-17",
                },
                {
                    "id": "equity",
                    "company": "Equity Limited",
                    "symbol": "360ONE",
                    "exchange": "NSE",
                    "openDate": "2026-02-17",
                },
            ],
            "meta": {"recordCount": 2},
        }
        cleaned, removed = mod.prune_payload(payload, today=TODAY)
        self.assertEqual([row["id"] for row in cleaned["ipos"]], ["equity"])
        self.assertEqual(cleaned["meta"]["recordCount"], 1)
        self.assertEqual([row["symbol"] for row in removed], ["935DEBT33"])


if __name__ == "__main__":
    unittest.main()
