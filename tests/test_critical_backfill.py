import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "critical_backfill.py"
spec = importlib.util.spec_from_file_location("critical_backfill", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


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

    def get(self, url, timeout=None, headers=None):
        value = self.pages.get(url)
        if isinstance(value, Exception):
            raise value
        if value is None:
            return FakeResponse("", 404)
        return FakeResponse(value)


class CriticalBackfillTests(unittest.TestCase):
    def test_priority_queue_selects_open_and_upcoming_only(self):
        payload = {
            "ipos": [
                {"id": "open", "company": "Open Limited"},
                {"id": "upcoming", "company": "Upcoming Limited"},
                {"id": "history", "company": "History Limited"},
            ]
        }
        queue = {
            "queue": [
                {"id": "open", "priority": 0},
                {"id": "upcoming", "priority": 1},
                {"id": "history", "priority": 4},
            ]
        }
        selected = mod.load_priority_targets(payload, queue, priority_max=1, limit=20)
        self.assertEqual([record["id"] for record, _ in selected], ["open", "upcoming"])

    def test_offer_document_selector_prefers_abridged_pdf(self):
        record = {
            "documents": [
                {
                    "type": "RHP",
                    "title": "Red Herring Prospectus",
                    "url": "https://www.sebi.gov.in/files/full-rhp.pdf",
                    "filedDate": "2026-09-10",
                },
                {
                    "type": "RHP",
                    "title": "Abridged Prospectus",
                    "url": "https://www.sebi.gov.in/files/AP_company.pdf",
                    "filedDate": "2026-09-10",
                },
            ]
        }
        chosen = mod.choose_fallback_document(record)
        self.assertIn("AP_company.pdf", chosen["url"])

    def test_offer_document_selector_can_fall_back_to_full_rhp(self):
        record = {
            "documents": [
                {
                    "type": "RHP",
                    "title": "Red Herring Prospectus",
                    "url": "https://www.sebi.gov.in/files/full-rhp.pdf",
                    "filedDate": "2026-09-10",
                }
            ]
        }
        chosen = mod.choose_fallback_document(record)
        self.assertEqual(chosen["type"], "RHP")

    def test_offer_document_selector_rejects_non_official_url(self):
        record = {
            "documents": [
                {
                    "type": "RHP",
                    "title": "Red Herring Prospectus",
                    "url": "https://example.com/rhp.pdf",
                }
            ]
        }
        self.assertIsNone(mod.choose_fallback_document(record))

    def test_bse_subscription_index_combines_mainboard_and_sme_pages(self):
        main = "https://main.example/index"
        sme = "https://sme.example/index"
        main_html = """
        <table><tr><td>Mainboard Limited</td><td>
          <a href="https://www.bseindia.com/markets/publicIssues/DisplayIPO.aspx?IPONo=100&type=IPO">Mainboard Limited</a>
        </td></tr></table>
        """
        sme_html = """
        <table><tr><td>SME Limited</td><td>
          <a href="https://www.bseindia.com/markets/publicIssues/DisplayIPO.aspx?IPONo=200&type=IPO">SME Limited</a>
        </td></tr></table>
        """
        index, health = mod.build_bse_subscription_index(
            FakeSession({main: main_html, sme: sme_html}),
            [main, sme],
        )
        self.assertEqual(len(index), 2)
        self.assertTrue(health[main]["ok"])
        self.assertTrue(health[sme]["ok"])
        self.assertTrue(any("ID=100" in url for _, url in index))
        self.assertTrue(any("ID=200" in url for _, url in index))

    def test_bse_subscription_index_survives_one_failed_official_page(self):
        main = "https://main.example/index"
        sme = "https://sme.example/index"
        sme_html = """
        <table><tr><td>SME Limited</td><td>
          <a href="CummDemandSchedule.aspx?ID=201&amp;status=L">Cumulative Demand</a>
        </td></tr></table>
        """
        index, health = mod.build_bse_subscription_index(
            FakeSession({main: RuntimeError("blocked"), sme: sme_html}),
            [main, sme],
        )
        self.assertEqual(len(index), 1)
        self.assertFalse(health[main]["ok"])
        self.assertTrue(health[sme]["ok"])


if __name__ == "__main__":
    unittest.main()
