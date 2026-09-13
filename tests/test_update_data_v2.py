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


class P4NSEHistoryGuardTests(unittest.TestCase):
    def test_equity_history_row_is_accepted(self):
        row = {
            "companyName": "Example Limited",
            "securityType": "EQ",
            "issueType": "IPO",
        }
        self.assertEqual(mod.classify_nse_historical_issue(row), "equity-ipo")

    def test_explicit_ncd_row_is_rejected_even_when_issue_type_says_ipo(self):
        row = {
            "companyName": "Example Finance Limited",
            "securityType": "NCD",
            "issueType": "IPO",
        }
        self.assertEqual(mod.classify_nse_historical_issue(row), "non-equity")

    def test_zero_coupon_debt_descriptor_is_rejected(self):
        row = {
            "companyName": "Example Finance Limited (Zero Coupon NCD)",
            "issueType": "Public Issue",
        }
        self.assertEqual(mod.classify_nse_historical_issue(row), "non-equity")

    def test_coupon_maturity_debt_symbols_are_rejected_even_when_labeled_ipo(self):
        for symbol in ("935IIFL33", "790IHFL27", "975SCL35"):
            with self.subTest(symbol=symbol):
                row = {
                    "companyName": "Example Finance Limited",
                    "smSymbol": symbol,
                    "issueType": "IPO",
                }
                self.assertEqual(mod.classify_nse_historical_issue(row), "non-equity")

    def test_legitimate_numeric_equity_tickers_are_not_treated_as_debt(self):
        for symbol in ("3MINDIA", "360ONE"):
            with self.subTest(symbol=symbol):
                row = {
                    "companyName": "Example Equity Limited",
                    "smSymbol": symbol,
                    "securityType": "EQ",
                    "issueType": "IPO",
                }
                self.assertEqual(mod.classify_nse_historical_issue(row), "equity-ipo")

    def test_unknown_history_row_is_kept_for_conservative_validation(self):
        row = {"companyName": "Unclassified Example Limited"}
        self.assertEqual(mod.classify_nse_historical_issue(row), "unknown")

    def test_history_client_has_p4_guard_installed(self):
        self.assertTrue(getattr(mod.core.NSEClient.past, "_p4_ipo_guard", False))

    def test_exact_debt_symbol_matches_legacy_row(self):
        raw = {
            "companyName": "Example Finance Limited",
            "smSymbol": "935EXAMPLE33",
            "ipoStartDate": "17-Feb-2026",
            "ipoEndDate": "04-Mar-2026",
            "securityType": "NCD",
        }
        identity = mod.excluded_identity(raw, mod.core)
        stored = {
            "company": "Example Finance Limited",
            "matchKey": mod.canonical_company("Example Finance Limited"),
            "symbol": "935EXAMPLE33",
            "openDate": "2026-02-17",
            "closeDate": "2026-03-04",
        }
        self.assertTrue(mod.record_matches_excluded(stored, identity, mod.core))

    def test_same_issuer_equity_ipo_is_not_removed_by_debt_identity(self):
        raw = {
            "companyName": "Example Energy Limited",
            "smSymbol": "727EXAMPLE36",
            "ipoStartDate": "01-Jul-2026",
            "ipoEndDate": "10-Jul-2026",
            "securityType": "NCD",
        }
        identity = mod.excluded_identity(raw, mod.core)
        stored_equity = {
            "company": "Example Energy Limited",
            "matchKey": mod.canonical_company("Example Energy Limited"),
            "symbol": "EXAMPLE",
            "openDate": "2024-11-19",
            "closeDate": "2024-11-22",
        }
        self.assertFalse(mod.record_matches_excluded(stored_equity, identity, mod.core))


if __name__ == "__main__":
    unittest.main()
