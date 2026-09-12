import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "backfill_bse_history.py"
spec = importlib.util.spec_from_file_location("backfill_bse_history", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class BSEHistoricalBackfillTests(unittest.TestCase):
    def test_history_form_payload_selects_book_building(self):
        html = """
        <form method="post">
          <input type="hidden" name="__VIEWSTATE" value="abc" />
          <input type="hidden" name="__EVENTVALIDATION" value="xyz" />
          <select id="ctl00_ContentPlaceHolder1_ddlIssueType" name="ctl00$ContentPlaceHolder1$ddlIssueType">
            <option value="FP">Fixed Price</option>
            <option value="BB">Public Issue-Book Building</option>
          </select>
          <input type="submit" id="ctl00_ContentPlaceHolder1_btnSubmit" name="ctl00$ContentPlaceHolder1$btnSubmit" value="Submit" />
        </form>
        """
        payload = mod.history_form_payload(html)
        self.assertEqual(payload["__VIEWSTATE"], "abc")
        self.assertEqual(payload["__EVENTVALIDATION"], "xyz")
        self.assertEqual(payload["ctl00$ContentPlaceHolder1$ddlIssueType"], "BB")
        self.assertEqual(payload["ctl00$ContentPlaceHolder1$btnSubmit"], "Submit")

    def test_history_index_extracts_company_date_and_ipo_link(self):
        html = """
        <table>
          <tr><td><a href="DisplayIPO.aspx?id=567&amp;type=IPO&amp;idtype=2&amp;status=H&amp;IPONo=612&amp;startdt=01/02/2013">Example Limited</a></td></tr>
          <tr><td><a href="DisplayIPO.aspx?id=568&amp;type=FPO&amp;idtype=2&amp;status=H&amp;IPONo=613&amp;startdt=02/02/2013">Ignore FPO Limited</a></td></tr>
        </table>
        """
        index = mod.history_index(html)
        self.assertEqual(len(index), 1)
        self.assertEqual(index[0]["key"], "EXAMPLE")
        self.assertEqual(index[0]["openDate"], "2013-02-01")
        self.assertIn("type=IPO", index[0]["url"])

    def test_core_only_ignores_registrar_only_gap(self):
        record = {
            "openDate": "2013-02-01",
            "lotSize": 100,
            "issueSizeCr": 250.0,
            "registrar": None,
            "leadManagers": ["Example Capital Limited"],
        }
        today = date(2026, 9, 13)
        self.assertFalse(mod.is_candidate(record, today, 10000, core_only=True))
        self.assertTrue(mod.is_candidate(record, today, 10000, core_only=False))

    def test_archival_core_gap_is_candidate(self):
        record = {
            "openDate": "2013-02-01",
            "lotSize": None,
            "issueSizeCr": 250.0,
        }
        self.assertTrue(
            mod.is_candidate(record, date(2026, 9, 13), 10000, core_only=True)
        )

    def test_retry_cooldown_skips_recently_considered_record(self):
        record = {
            "openDate": "2013-02-01",
            "lotSize": None,
            "issueSizeCr": None,
            mod.ATTEMPT_KEY: {"lastAttemptAt": "2026-09-01T19:00:00+05:30"},
        }
        today = date(2026, 9, 13)
        self.assertTrue(mod.attempted_recently(record, today, 30))
        self.assertFalse(
            mod.is_candidate(record, today, 10000, core_only=True, retry_days=30)
        )
        self.assertTrue(
            mod.is_candidate(record, today, 10000, core_only=True, retry_days=0)
        )

    def test_attempt_marker_records_validation_provenance(self):
        record = {}
        mod.mark_attempt(
            record,
            status="validated",
            archive_url="https://www.bseindia.com/history",
            detail_url="https://www.bseindia.com/detail",
            changed_fields=[],
        )
        marker = record[mod.ATTEMPT_KEY]
        self.assertEqual(marker["status"], "validated")
        self.assertEqual(marker["detailUrl"], "https://www.bseindia.com/detail")
        self.assertIn("lastAttemptAt", marker)


if __name__ == "__main__":
    unittest.main()
