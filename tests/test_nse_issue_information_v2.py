import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "enrich_nse_issue_information_v2.py"
spec = importlib.util.spec_from_file_location("enrich_nse_issue_information_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class NSEIssueInformationV2Tests(unittest.TestCase):
    def record(self, *, board="Mainboard", exchange="NSE"):
        return {
            "id": "demo",
            "company": "Demo Limited",
            "symbol": "DEMO",
            "board": board,
            "exchange": exchange,
            "openDate": "2026-01-01",
            "lotSize": None,
            "sources": [],
            "observations": {},
        }

    def test_primary_then_alternate_series(self):
        self.assertEqual(mod.series_candidates(self.record()), ["EQ", "SME"])
        self.assertEqual(
            mod.series_candidates(self.record(board="SME", exchange="NSE Emerge")),
            ["SME", "EQ"],
        )

    def test_candidate_is_fill_only(self):
        today = mod.core.now_ist().date()
        record = self.record()
        self.assertTrue(mod.is_candidate(record, today, 730))
        record["lotSize"] = 50
        self.assertFalse(mod.is_candidate(record, today, 730))

    def test_base_identity_guard_still_rejects_wrong_company_and_debt(self):
        record = self.record()
        good = {
            "companyName": "Demo Limited",
            "metaInfo": {"symbol": "DEMO", "companyName": "Demo Limited", "isDebtSec": False},
            "issueInfo": {"dataList": [{"title": "Bid Lot", "value": "100 Equity Shares"}]},
        }
        wrong_company = dict(good, companyName="Other Limited", metaInfo={"symbol": "DEMO", "companyName": "Other Limited", "isDebtSec": False})
        debt = dict(good, metaInfo={"symbol": "DEMO", "companyName": "Demo Limited", "isDebtSec": True})
        self.assertTrue(mod.base.identity_matches(record, good))
        self.assertFalse(mod.base.identity_matches(record, wrong_company))
        self.assertFalse(mod.base.identity_matches(record, debt))


if __name__ == "__main__":
    unittest.main()
