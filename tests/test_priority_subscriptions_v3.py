import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_priority_subscriptions_v3.py"
spec = importlib.util.spec_from_file_location("run_priority_subscriptions_v3", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


GROWW_HTML = """
<html><body>
<table>
  <thead>
    <tr>
      <th>Company Name</th><th>Type</th><th>Close Date</th><th>Issue Size</th>
      <th>Issue Price</th><th>QIB</th><th>NII</th><th>Retail</th><th>Employee</th><th>Total</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Raksan Transformers</td><td>SME</td><td>15 Sep 2026</td><td>150.50 Cr</td>
      <td>₹258 - ₹273</td><td>3.87x</td><td>0.38x</td><td>0.35x</td><td>--</td><td>1.29x</td>
    </tr>
    <tr>
      <td>Century Business</td><td>SME</td><td>16 Sep 2026</td><td>17.11 Cr</td>
      <td>₹70 - ₹74</td><td>3.51x</td><td>0.30x</td><td>0.12x</td><td>--</td><td>1.06x</td>
    </tr>
  </tbody>
</table>
</body></html>
"""


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        return None


class FakeSession:
    def get(self, url, timeout=None):
        return FakeResponse(GROWW_HTML)


class PrioritySubscriptionV3Tests(unittest.TestCase):
    def test_groww_table_is_parsed_by_named_columns(self):
        rows = mod.parse_groww_subscription_html(GROWW_HTML)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["key"], "RAKSANTRANSFORMERS")
        self.assertEqual(
            rows[0]["subscription"],
            {"qib": 3.87, "nii": 0.38, "retail": 0.35, "total": 1.29},
        )

    def test_missing_values_do_not_become_zero(self):
        html = GROWW_HTML.replace("3.87x", "--").replace("0.38x", "--")
        rows = mod.parse_groww_subscription_html(html)
        self.assertIsNone(rows[0]["subscription"]["qib"])
        self.assertIsNone(rows[0]["subscription"]["nii"])
        self.assertEqual(rows[0]["subscription"]["retail"], 0.35)

    def test_parser_fails_closed_without_named_headers(self):
        html = "<table><tr><td>Example IPO</td><td>1.2x</td><td>2.3x</td></tr></table>"
        self.assertEqual(mod.parse_groww_subscription_html(html), [])

    def test_client_matches_short_secondary_company_name(self):
        client = mod.GrowwSubscriptionClient()
        client.s = FakeSession()
        parsed, url = client.detail("CENTURY BUSINESS MEDIA LIMITED")
        self.assertEqual(parsed["qib"], 3.51)
        self.assertEqual(parsed["total"], 1.06)
        self.assertEqual(url, mod.GROWW_SUBSCRIPTION_URL)

    def test_secondary_source_is_explicitly_marked_non_exchange(self):
        record = {
            "sources": [
                {"name": mod.SECONDARY_SOURCE_NAME, "kind": "exchange", "url": "https://groww.in/ipo/subscription"}
            ]
        }
        mod._mark_secondary_provenance(record)
        self.assertEqual(record["sources"][0]["kind"], "secondary-market-data")


if __name__ == "__main__":
    unittest.main()
