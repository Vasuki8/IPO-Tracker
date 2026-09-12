import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_nse_primary_market_reports_v2.py"
spec = importlib.util.spec_from_file_location("enrich_nse_primary_market_reports_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class NSEPrimaryMarketReportV2Tests(unittest.TestCase):
    def test_parser_version(self):
        self.assertEqual(mod.PARSER_VERSION, 2)

    def test_discovers_current_and_archive_xlsx_links(self):
        html = """
        <html><body>
          <a href="https://nsearchives.nseindia.com/web/mediaattachment/2026-08/Primary_Market_data__July26_20260814112232.xlsx">
            Primary Market Monthly Report - July 2026 (.xlsx)
          </a>
          <a href="https://nsearchives.nseindia.com/web/mediaattachment/2026-02/primary_market_january_2026.xlsx">
            Primary Market Monthly Report - January 2026 (.xlsx)
          </a>
          <a href="https://nsearchives.nseindia.com/web/mediaattachment/legacy/report_2024.xlsx">
            Primary Market Monthly Report - January 2024 (.xlsx)
          </a>
          <a href="https://nsearchives.nseindia.com/web/mediaattachment/other_report.xlsx">
            Equity Market Monthly Report
          </a>
          <a href="https://nsearchives.nseindia.com/web/mediaattachment/readme.pdf">
            Primary Market Monthly Report
          </a>
        </body></html>
        """
        urls = mod.extract_report_urls(html)
        self.assertEqual(len(urls), 3)
        self.assertTrue(urls[0].endswith("Primary_Market_data__July26_20260814112232.xlsx"))
        self.assertTrue(urls[1].endswith("primary_market_january_2026.xlsx"))
        self.assertTrue(urls[2].endswith("report_2024.xlsx"))

    def test_max_reports_preserves_page_order(self):
        html = """
        <a href="https://nsearchives.nseindia.com/Primary_Market_July.xlsx">July</a>
        <a href="https://nsearchives.nseindia.com/Primary_Market_June.xlsx">June</a>
        <a href="https://nsearchives.nseindia.com/Primary_Market_May.xlsx">May</a>
        """
        urls = mod.extract_report_urls(html, max_reports=2)
        self.assertEqual(len(urls), 2)
        self.assertTrue(urls[0].endswith("Primary_Market_July.xlsx"))
        self.assertTrue(urls[1].endswith("Primary_Market_June.xlsx"))

    def test_duplicate_links_are_deduplicated(self):
        html = """
        <a href="https://nsearchives.nseindia.com/Primary_Market_July.xlsx">Primary Market</a>
        <a href="https://nsearchives.nseindia.com/Primary_Market_July.xlsx">Download</a>
        """
        self.assertEqual(len(mod.extract_report_urls(html)), 1)


if __name__ == "__main__":
    unittest.main()
