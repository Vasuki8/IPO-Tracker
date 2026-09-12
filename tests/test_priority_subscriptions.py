import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "priority_subscriptions.py"
spec = importlib.util.spec_from_file_location("priority_subscriptions", MODULE)
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


class PrioritySubscriptionTests(unittest.TestCase):
    def test_display_page_real_demand_link_is_preferred_candidate(self):
        display = "https://beta.bseindia.com/markets/publicIssues/DisplayIPO.aspx?IPONo=200&type=IPO"
        real = "https://www.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID=999&status=L"
        row = mod.IssueLink("EXAMPLE", display, None, "https://beta.bseindia.com/index")
        session = FakeSession({display: f'<a href="{real}">Cumulative Demand</a>'})
        urls, _ = mod.demand_candidates(session, [row])
        self.assertIn(real, urls)
        # The constructed IPONo route remains a fallback, not the only choice.
        self.assertTrue(any("ID=200" in url for url in urls))

    def test_fetch_demand_skips_empty_candidate_and_uses_next_official_host(self):
        first = "https://beta.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID=9&status=L"
        second = "https://www.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID=9&status=L"
        html = """
        <table>
          <tr><td>1</td><td>Qualified Institutional Buyers (QIBs)</td><td>100</td><td>50</td><td>0.50</td></tr>
          <tr><td>2</td><td>Non Institutional Investors (NIIS)</td><td>100</td><td>75</td><td>0.75</td></tr>
          <tr><td>3</td><td>Retail Individual Investors (RIIs)</td><td>100</td><td>125</td><td>1.25</td></tr>
          <tr><td></td><td>Total</td><td>300</td><td>250</td><td>0.83</td></tr>
        </table>
        """
        row = mod.IssueLink("EXAMPLE", None, first, "https://beta.bseindia.com/index")
        parsed, url, _ = mod.fetch_demand(FakeSession({first: "<html>No data</html>", second: html}), [row])
        self.assertEqual(url, second)
        self.assertEqual(parsed["qib"], 0.5)
        self.assertEqual(parsed["nii"], 0.75)
        self.assertEqual(parsed["retail"], 1.25)
        self.assertEqual(parsed["total"], 0.83)

    def test_priority_targets_only_include_missing_subscription_open_issues(self):
        payload = {"ipos": [{"id": "a"}, {"id": "b"}, {"id": "c"}]}
        queue = {"queue": [
            {"id": "a", "priority": 0, "missingFields": ["subscription.qib"]},
            {"id": "b", "priority": 0, "missingFields": ["exchange.issueComposition"]},
            {"id": "c", "priority": 1, "missingFields": ["subscription.qib"]},
        ]}
        rows = mod.priority_open_targets(payload, queue, 30)
        self.assertEqual([r["id"] for r in rows], ["a"])


if __name__ == "__main__":
    unittest.main()
