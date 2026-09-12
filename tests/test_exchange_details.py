import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_exchange_details.py"
spec = importlib.util.spec_from_file_location("enrich_exchange_details", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class ExchangeDetailParserTests(unittest.TestCase):
    def test_parse_bse_display_ipo_fields(self):
        html = """
        <table>
          <tr><td>Security Type</td><td>Equity</td></tr>
          <tr><td>Symbol</td><td>EXAMPLE</td></tr>
          <tr><td>Issue Period</td><td>10 Sep 2026 to 12 Sep 2026</td></tr>
          <tr><td>Issue Size – No. of Shares</td><td>10,00,000</td></tr>
          <tr><td>Price Band</td><td>100.00-110.00</td></tr>
          <tr><td>Face Value</td><td>10.00</td></tr>
          <tr><td>Market Lot</td><td>100</td></tr>
          <tr><td>Minimum Bid Quantity</td><td>200</td></tr>
          <tr><td>Book Running Lead Manager</td><td>1) Alpha Capital Limited<br/>2) Beta Securities Limited</td></tr>
          <tr><td>Registrar</td><td>Example Registry Limited</td></tr>
          <tr><td>Prospectus &amp; GID</td><td><a href="/corporates/download/123/IPO/PROSPECTUS_EXAMPLE.pdf">Click Here</a></td></tr>
        </table>
        """
        detail = mod.parse_detail_html(html)
        self.assertTrue(detail["isEquity"])
        self.assertEqual(detail["symbol"], "EXAMPLE")
        self.assertEqual(detail["openDate"], "2026-09-10")
        self.assertEqual(detail["closeDate"], "2026-09-12")
        self.assertEqual(detail["priceBand"], {"min": 100.0, "max": 110.0})
        self.assertEqual(detail["marketLot"], 100)
        self.assertEqual(detail["minimumBidQuantity"], 200)
        self.assertEqual(detail["lotSize"], 200)
        self.assertEqual(detail["sharesOffered"], 1_000_000)
        self.assertEqual(detail["issueSizeCr"], 11.0)
        self.assertEqual(detail["faceValue"], 10.0)
        self.assertEqual(detail["minInvestment"], 22_000.0)
        self.assertEqual(
            detail["leadManagers"],
            ["Alpha Capital Limited", "Beta Securities Limited"],
        )
        self.assertEqual(detail["registrar"], "Example Registry Limited")
        self.assertEqual(len(detail["documents"]), 1)
        self.assertEqual(detail["documents"][0]["type"], "PROSPECTUS")
        self.assertEqual(detail["documents"][0]["source"], "BSE")
        self.assertTrue(detail["documents"][0]["url"].endswith("PROSPECTUS_EXAMPLE.pdf"))

    def test_non_bse_prospectus_link_is_rejected(self):
        html = """
        <table>
          <tr><td>Security Type</td><td>Equity</td></tr>
          <tr><td>Prospectus &amp; GID</td><td><a href="https://example.com/prospectus.pdf">Click Here</a></td></tr>
        </table>
        """
        detail = mod.parse_detail_html(html)
        self.assertEqual(detail["documents"], [])

    def test_minimum_bid_quantity_wins_over_market_lot(self):
        html = """
        <table>
          <tr><td>Security Type</td><td>Equity</td></tr>
          <tr><td>Market Lot</td><td>600</td></tr>
          <tr><td>Minimum Bid Quantity</td><td>1200</td></tr>
        </table>
        """
        detail = mod.parse_detail_html(html)
        self.assertEqual(detail["marketLot"], 600)
        self.assertEqual(detail["minimumBidQuantity"], 1200)
        self.assertEqual(detail["lotSize"], 1200)

    def test_historical_start_date_from_display_url(self):
        url = (
            "https://www.bseindia.com/markets/publicIssues/DisplayIPO.aspx?"
            "id=567&type=IPO&idtype=2&status=H&IPONo=612&startdt=01/02/2013"
        )
        self.assertEqual(mod._start_date_from_display_url(url), "2013-02-01")

    def test_best_url_uses_issue_date_for_repeated_issuer(self):
        index = [
            {
                "key": "EXAMPLE",
                "url": "https://bse.example/old?type=IPO&startdt=01/02/2013",
                "openDate": "2013-02-01",
                "indexUrl": mod.BSE_HISTORY_URL,
            },
            {
                "key": "EXAMPLE",
                "url": "https://bse.example/new?type=IPO&startdt=10/09/2026",
                "openDate": "2026-09-10",
                "indexUrl": mod.BSE_HISTORY_URL,
            },
        ]
        self.assertEqual(
            mod.best_url(index, "Example Limited", "2026-09-10"),
            "https://bse.example/new?type=IPO&startdt=10/09/2026",
        )

    def test_best_url_refuses_distant_repeated_issue(self):
        index = [
            {
                "key": "EXAMPLE",
                "url": "https://bse.example/old1",
                "openDate": "2013-02-01",
                "indexUrl": mod.BSE_HISTORY_URL,
            },
            {
                "key": "EXAMPLE",
                "url": "https://bse.example/old2",
                "openDate": "2015-03-01",
                "indexUrl": mod.BSE_HISTORY_URL,
            },
        ]
        self.assertIsNone(mod.best_url(index, "Example Limited", "2026-09-10"))

    def test_merge_detail_is_fill_only_but_keeps_bse_observation(self):
        record = {
            "company": "Example Limited",
            "symbol": "NSEEX",
            "priceBand": {"min": 105.0, "max": 115.0},
            "lotSize": 150,
            "issueSizeCr": None,
            "registrar": None,
            "leadManagers": [],
            "documents": [],
            "sources": [{"name": "NSE current", "url": "https://nse.example"}],
            "observations": {
                "NSE": {
                    "openDate": "2026-09-10",
                    "closeDate": "2026-09-12",
                    "priceBand": {"min": 105.0, "max": 115.0},
                    "lotSize": 150,
                    "issueSizeCr": None,
                }
            },
        }
        detail = {
            "isEquity": True,
            "symbol": "BSEEX",
            "openDate": "2026-09-10",
            "closeDate": "2026-09-12",
            "priceBand": {"min": 100.0, "max": 110.0},
            "lotSize": 200,
            "minimumBidQuantity": 200,
            "marketLot": 100,
            "sharesOffered": 1_000_000,
            "issueSizeCr": 11.0,
            "faceValue": 10.0,
            "minInvestment": 22_000.0,
            "registrar": "Registry Limited",
            "leadManagers": ["Alpha Capital Limited"],
            "documents": [
                {
                    "type": "PROSPECTUS",
                    "title": "Prospectus & GID",
                    "url": "https://www.bseindia.com/corporates/download/123/example.pdf",
                    "source": "BSE",
                }
            ],
        }
        changed = mod.merge_detail(record, detail, "https://bse.example/detail")
        self.assertEqual(record["symbol"], "NSEEX")
        self.assertEqual(record["priceBand"], {"min": 105.0, "max": 115.0})
        self.assertEqual(record["lotSize"], 150)
        self.assertEqual(record["issueSizeCr"], 11.0)
        self.assertEqual(record["registrar"], "Registry Limited")
        self.assertEqual(record["leadManagers"], ["Alpha Capital Limited"])
        self.assertIn("issueSizeCr", changed)
        self.assertIn("documents", changed)
        self.assertEqual(record["documents"][0]["source"], "BSE")
        self.assertEqual(record["observations"]["BSE"]["lotSize"], 200)
        self.assertEqual(record["validation"]["status"], "conflict")
        self.assertTrue(any(s["name"] == "BSE issue detail" for s in record["sources"]))

    def test_non_equity_detail_is_ignored(self):
        record = {"company": "Debt Issue", "sources": [], "observations": {}}
        detail = {"isEquity": False, "symbol": "DEBT"}
        changed = mod.merge_detail(record, detail, "https://bse.example/debt")
        self.assertEqual(changed, [])
        self.assertNotIn("symbol", record)


if __name__ == "__main__":
    unittest.main()
