import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_update.py"
spec = importlib.util.spec_from_file_location("run_update", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class NormalizerTests(unittest.TestCase):
    def test_company_key_ignores_legal_suffix_and_filing_words(self):
        self.assertEqual(mod.canonical_company("Example Limited - RHP"), "EXAMPLE")
        self.assertEqual(mod.canonical_company("Example Ltd DRHP"), "EXAMPLE")

    def test_period_parser_text_month(self):
        self.assertEqual(
            mod.parse_period("13 Oct 2026 to 17 Oct 2026"),
            ("2026-10-13", "2026-10-17"),
        )

    def test_period_parser_numeric_bse_dates(self):
        self.assertEqual(
            mod.parse_period("17-09-2026 | 21-09-2026"),
            ("2026-09-17", "2026-09-21"),
        )

    def test_price_band_parser(self):
        self.assertEqual(
            mod.parse_price_band_text("Rs 100 - Rs 110"),
            {"min": 100.0, "max": 110.0},
        )
        self.assertEqual(
            mod.parse_price_band_text("₹99"),
            {"min": 99.0, "max": 99.0},
        )

    def test_issue_size_tolerance(self):
        self.assertTrue(mod.field_equal("issueSizeCr", 500.0, 501.0))
        self.assertFalse(mod.field_equal("issueSizeCr", 500.0, 510.0))

    def test_nse_share_count_is_converted_to_crore(self):
        size, shares = mod.nse_issue_metrics(
            {"issueSize": 14_300_000},
            {"min": 94.0, "max": 99.0},
        )
        self.assertEqual(shares, 14_300_000)
        self.assertEqual(size, 141.57)

    def test_nse_explicit_crore_value_wins(self):
        size, shares = mod.nse_issue_metrics(
            {"issueSizeCr": 500.0, "issueSize": 20_000_000},
            {"min": 100.0, "max": 110.0},
        )
        self.assertEqual(size, 500.0)
        self.assertEqual(shares, 20_000_000)

    def test_nse_historical_aliases_are_retained(self):
        record = mod.normalize_nse_record(
            {
                "smSymbol": "EXAMPLE",
                "companyName": "Example Limited",
                "ipoStartDate": "10-Sep-2025",
                "ipoEndDate": "12-Sep-2025",
                "listingDate": "18-Sep-2025",
                "priceRange": "Rs.100 to Rs.110",
                "bidLot": "125",
                "issueSize": "10000000",
                "securityType": "EQ",
            },
            "historical",
        )
        self.assertEqual(record["symbol"], "EXAMPLE")
        self.assertEqual(record["openDate"], "2025-09-10")
        self.assertEqual(record["closeDate"], "2025-09-12")
        self.assertEqual(record["listingDate"], "2025-09-18")
        self.assertEqual(record["lotSize"], 125)
        self.assertEqual(record["priceBand"], {"min": 100.0, "max": 110.0})
        self.assertEqual(record["issueSizeCr"], 110.0)

    def test_bse_html_parser_handles_numeric_dates(self):
        html = """
        <table>
          <tr>
            <th>Security Name</th><th>Exchange Platform</th><th>Start Date</th>
            <th>End Date</th><th>Offer Price</th><th>Face Value</th>
            <th>Type of Issue</th><th>Issue Status</th>
          </tr>
          <tr>
            <td>Example Limited</td><td>MainBoard</td><td>17-09-2026</td>
            <td>21-09-2026</td><td>Rs 94 - Rs 99</td><td>10</td>
            <td>IPO</td><td>Forthcoming</td>
          </tr>
        </table>
        """
        rows = mod.BSEClient.parse_html(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "Example Limited")
        self.assertEqual(rows[0]["board"], "Mainboard")
        self.assertEqual(rows[0]["openDate"], "2026-09-17")
        self.assertEqual(rows[0]["closeDate"], "2026-09-21")
        self.assertEqual(rows[0]["priceBand"], {"min": 94.0, "max": 99.0})

    def test_bse_parser_keeps_only_ipos_and_ignores_outer_nested_row(self):
        html = """
        <table>
          <tr><td>
            <table>
              <tr>
                <th>Security Name</th><th>Exchange Platform</th><th>Start Date</th>
                <th>End Date</th><th>Offer Price</th><th>Face Value</th>
                <th>Type of Issue</th><th>Issue Status</th>
              </tr>
              <tr>
                <td>Good IPO Limited</td><td>SME</td><td>17-09-2026</td>
                <td>21-09-2026</td><td>94.00 - 99.00</td><td>10</td>
                <td>IPO</td><td>Forthcoming</td>
              </tr>
              <tr>
                <td>Not An IPO Limited</td><td>MainBoard</td><td>17-09-2026</td>
                <td>21-09-2026</td><td>50.00</td><td>10</td>
                <td>FPO</td><td>Forthcoming</td>
              </tr>
            </table>
          </td></tr>
        </table>
        """
        rows = mod.BSEClient.parse_html(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "Good IPO Limited")
        self.assertEqual(rows[0]["board"], "SME")
        self.assertEqual(rows[0]["issueType"], "IPO")

    def test_legacy_seed_fields_are_removed_before_live_merge(self):
        rec = {
            "company": "Example Limited",
            "symbol": "FAKE",
            "openDate": "2026-09-01",
            "closeDate": "2026-09-03",
            "priceBand": {"min": 1, "max": 2},
            "issueSizeCr": 999,
            "subscription": {"total": 42},
            "source": {"name": "Seed snapshot", "url": "seed"},
            "sources": [
                {"name": "Seed snapshot", "url": "seed"},
                {"name": "SEBI public issues", "url": "sebi"},
            ],
            "observations": {"SEBI": {"stage": "drhp"}},
        }
        out = mod.clean_existing_record(rec)
        self.assertIsNotNone(out)
        self.assertIsNone(out["symbol"])
        self.assertIsNone(out["openDate"])
        self.assertIsNone(out["priceBand"])
        self.assertIsNone(out["issueSizeCr"])
        self.assertIsNone(out["subscription"])
        self.assertEqual([s["name"] for s in out["sources"]], ["SEBI public issues"])

    def test_old_bse_only_rows_are_dropped_and_refetched(self):
        rec = {
            "company": "Old FPO Limited",
            "sources": [{"name": "BSE public issue", "url": "bse"}],
            "observations": {"BSE": {"openDate": "2026-09-01"}},
        }
        self.assertIsNone(mod.clean_existing_record(rec))

    def test_conflict_is_not_overwritten(self):
        base = {"openDate": "2026-09-10", "lotSize": 100, "company": "Example Limited"}
        incoming = {"openDate": "2026-09-11", "lotSize": 125, "company": "Example Limited"}
        out = mod.merge_fill_only(
            base,
            incoming,
            protected={"openDate", "lotSize", "company"},
        )
        self.assertEqual(out["openDate"], "2026-09-10")
        self.assertEqual(out["lotSize"], 100)

    def test_validation_flags_exchange_disagreement(self):
        rec = {
            "sources": [
                {"name": "NSE current", "url": "nse"},
                {"name": "BSE public issue", "url": "bse"},
            ],
            "observations": {
                "NSE": {"openDate": "2026-09-10", "lotSize": 100},
                "BSE": {"openDate": "2026-09-10", "lotSize": 125},
            },
        }
        validation = mod.build_validation(rec)
        self.assertEqual(validation["status"], "conflict")
        self.assertTrue(
            any(
                c["field"] == "lotSize" and c["match"] is False
                for c in validation["checks"]
            )
        )


if __name__ == "__main__":
    unittest.main()
