import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_update_v2.py"
spec = importlib.util.spec_from_file_location("run_update_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


SME_HTML = """
<table>
  <tr>
    <th>Company Name</th><th>Issue Open Date</th><th>Issue Close Date</th>
    <th>Issue Price</th><th>Lot Size</th><th>Type of Issue</th><th>Status</th>
  </tr>
  <tr>
    <td>Panchatv Bharat Limited</td><td>10 Sep 2026</td><td>15 Sep 2026</td>
    <td>140</td><td>1000</td><td>IPO</td><td>Open</td>
  </tr>
</table>
"""

MAIN_HTML = """
<table>
  <tr><td>Example Mainboard Limited</td><td>Mainboard</td><td>10 Sep 2026</td><td>15 Sep 2026</td><td>100 - 110</td><td></td><td>IPO</td><td>Open</td></tr>
</table>
"""


class FakeResponse:
    def __init__(self, text, status=200):
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, pages):
        self.pages = pages

    def get(self, url, timeout=None):
        value = self.pages.get(url)
        if isinstance(value, Exception):
            raise value
        if value is None:
            return FakeResponse("", 404)
        return FakeResponse(value)


class BSESMECoreCoverageTests(unittest.TestCase):
    def test_header_driven_sme_parser(self):
        rows = mod.parse_bse_sme_html(SME_HTML)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["company"], "Panchatv Bharat Limited")
        self.assertEqual(row["board"], "SME")
        self.assertEqual(row["exchange"], "BSE SME")
        self.assertEqual(row["openDate"], "2026-09-10")
        self.assertEqual(row["closeDate"], "2026-09-15")
        self.assertEqual(row["priceBand"], {"min": 140.0, "max": 140.0})
        self.assertEqual(row["lotSize"], 1000)

    def test_non_ipo_sme_row_is_rejected(self):
        html = SME_HTML.replace(">IPO<", ">FPO<")
        self.assertEqual(mod.parse_bse_sme_html(html), [])

    def test_current_sources_are_aggregated_not_first_nonempty(self):
        main = "https://www.bseindia.com/main"
        sme = mod.BSE_SME_CURRENT_URL
        session = FakeSession({main: MAIN_HTML, sme: SME_HTML})
        rows = mod.aggregate_bse_current_issues(session, [main, sme])
        names = {row["company"] for row in rows}
        self.assertIn("Example Mainboard Limited", names)
        self.assertIn("Panchatv Bharat Limited", names)

    def test_one_failed_source_does_not_hide_other_bse_source(self):
        main = "https://www.bseindia.com/main"
        sme = mod.BSE_SME_CURRENT_URL
        session = FakeSession({main: RuntimeError("blocked"), sme: SME_HTML})
        rows = mod.aggregate_bse_current_issues(session, [main, sme])
        self.assertEqual([row["company"] for row in rows], ["Panchatv Bharat Limited"])


if __name__ == "__main__":
    unittest.main()
