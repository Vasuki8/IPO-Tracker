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
        parsed, url, _ = mod.fetch_demand(
            FakeSession({first: "<html>No data</html>", second: html}), [row]
        )
        self.assertEqual(url, second)
        self.assertEqual(parsed["qib"], 0.5)
        self.assertEqual(parsed["nii"], 0.75)
        self.assertEqual(parsed["retail"], 1.25)
        self.assertEqual(parsed["total"], 0.83)

    def test_priority_targets_refresh_all_open_issues_even_when_subscription_exists(self):
        payload = {
            "ipos": [
                {
                    "id": "populated",
                    "symbol": "POP",
                    "status": "open",
                    "company": "Already Populated Limited",
                    "subscription": {"total": 2.5},
                },
                {
                    "id": "missing",
                    "symbol": "MISS",
                    "status": "open",
                    "company": "Missing Subscription Limited",
                },
                {
                    "id": "future",
                    "symbol": "FUT",
                    "status": "upcoming",
                    "company": "Future Limited",
                },
                {
                    "id": "closed",
                    "symbol": "CLOSED",
                    "status": "closed",
                    "company": "Closed Limited",
                },
                {
                    "id": "no-symbol",
                    "status": "open",
                    "company": "No Symbol Limited",
                },
            ]
        }
        # The queue intentionally contains only the missing record. A populated
        # open IPO must still be refreshed because live demand changes over time.
        queue = {
            "queue": [
                {
                    "id": "missing",
                    "priority": 0,
                    "missingFields": ["subscription.qib"],
                }
            ]
        }
        rows = mod.priority_open_targets(payload, queue, 30)
        self.assertEqual([row["id"] for row in rows], ["populated", "missing"])

    def test_priority_target_limit_applies_after_open_issue_selection(self):
        payload = {
            "ipos": [
                {"id": "b", "symbol": "B", "status": "open", "company": "Beta Limited"},
                {"id": "a", "symbol": "A", "status": "open", "company": "Alpha Limited"},
            ]
        }
        rows = mod.priority_open_targets(payload, {"queue": []}, 1)
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
