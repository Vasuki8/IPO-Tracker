import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MODULE = SCRIPT_DIR / "enrich_nse_issue_terms.py"
spec = importlib.util.spec_from_file_location("enrich_nse_issue_terms", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class NSEIssueTermsTests(unittest.TestCase):
    def payload(self, value):
        return {
            "companyName": "Senco Gold Limited",
            "metaInfo": {
                "symbol": "SENCO",
                "companyName": "Senco Gold Limited",
                "isDebtSec": False,
            },
            "issueInfo": {"dataList": [{"title": "Issue Size", "value": value}]},
        }

    def record(self):
        return {
            "company": "Senco Gold Limited",
            "matchKey": "SENCOGOLD",
            "symbol": "SENCO",
            "exchange": "NSE",
            "board": "Mainboard",
            "openDate": "2026-08-01",
            "sources": [],
            "observations": {},
            "issueSizeCr": None,
        }

    def test_senco_style_million_text_parses_fresh_ofs_and_total(self):
        value = (
            'Initial Public Offer comprising of Fresh issue of up to [.] Equity Shares '
            'aggregating up to Rs. 2,700.00 million and Offer for sale of up to [.] '
            'equity Shares aggregating up to Rs. 1,350.00 million'
        )
        terms = mod.parse_issue_terms(self.payload(value))
        self.assertEqual(terms["freshIssueCr"], 270.0)
        self.assertEqual(terms["ofsCr"], 135.0)
        self.assertEqual(terms["issueSizeCr"], 405.0)

    def test_crore_and_lakh_units_are_normalized(self):
        value = (
            'Fresh Issue aggregating up to Rs. 125 crore and Offer for Sale '
            'aggregating up to Rs. 2,500 lakh'
        )
        terms = mod.parse_issue_terms(self.payload(value))
        self.assertEqual(terms["freshIssueCr"], 125.0)
        self.assertEqual(terms["ofsCr"], 25.0)
        self.assertEqual(terms["issueSizeCr"], 150.0)

    def test_single_fresh_issue_can_supply_total(self):
        terms = mod.parse_issue_terms(
            self.payload('Fresh Issue of equity shares aggregating up to Rs. 500 crore')
        )
        self.assertEqual(terms["freshIssueCr"], 500.0)
        self.assertIsNone(terms["ofsCr"])
        self.assertEqual(terms["issueSizeCr"], 500.0)

    def test_bare_rupee_amount_is_not_guessed(self):
        terms = mod.parse_issue_terms(
            self.payload('Fresh Issue aggregating up to Rs. 500000000')
        )
        self.assertIsNone(terms["freshIssueCr"])
        self.assertIsNone(terms["issueSizeCr"])

    def test_candidate_targets_only_recent_nse_term_gaps(self):
        record = self.record()
        self.assertTrue(mod.is_candidate(record, date(2026, 9, 13), 730))
        record["issueSizeCr"] = 405.0
        record["freshIssueCr"] = 270.0
        self.assertFalse(mod.is_candidate(record, date(2026, 9, 13), 730))

    def test_recent_attempt_obeys_retry_cooldown(self):
        record = self.record()
        record[mod.ATTEMPT_KEY] = {
            "status": "no-terms",
            "lastAttemptAt": "2026-09-13T12:00:00+05:30",
        }
        self.assertFalse(mod.is_candidate(record, date(2026, 9, 13), 730, 14))
        self.assertTrue(mod.is_candidate(record, date(2026, 9, 13), 730, 0))

    def test_mark_attempt_persists_status_and_parsed_terms(self):
        record = self.record()
        terms = {"freshIssueCr": 270.0, "ofsCr": 135.0, "issueSizeCr": 405.0}
        with patch.object(mod.core, "now_ist") as now_ist:
            now_ist.return_value.isoformat.return_value = "2026-09-13T12:00:00+05:30"
            mod.mark_attempt(
                record,
                status="filled",
                page_url="https://www.nseindia.com/issue",
                api_url="https://www.nseindia.com/api/ipo-detail",
                parsed_terms=terms,
            )
        attempt = record[mod.ATTEMPT_KEY]
        self.assertEqual(attempt["status"], "filled")
        self.assertEqual(attempt["issueSizeCr"], 405.0)
        self.assertEqual(attempt["freshIssueCr"], 270.0)

    def test_merge_is_fill_only_and_keeps_provenance(self):
        value = (
            'Fresh issue aggregating up to Rs. 2700 million and Offer for sale '
            'aggregating up to Rs. 1350 million'
        )
        record = self.record()
        self.assertTrue(
            mod.merge_terms(
                record,
                self.payload(value),
                page_url='https://www.nseindia.com/market-data/issue-information?series=EQ&symbol=SENCO&type=Past',
            )
        )
        self.assertEqual(record["freshIssueCr"], 270.0)
        self.assertEqual(record["ofsCr"], 135.0)
        self.assertEqual(record["issueSizeCr"], 405.0)
        self.assertIn("NSE-issue-info-terms", record["observations"])
        self.assertTrue(any(s.get("name") == mod.SOURCE_NAME for s in record["sources"]))

        record["issueSizeCr"] = 999.0
        mod.merge_terms(
            record,
            self.payload(value),
            page_url='https://www.nseindia.com/market-data/issue-information?series=EQ&symbol=SENCO&type=Past',
        )
        self.assertEqual(record["issueSizeCr"], 999.0)


if __name__ == "__main__":
    unittest.main()
