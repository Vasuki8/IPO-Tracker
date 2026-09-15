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

IPODHAMAKA_HTML = """
<html><body>
<table>
  <thead>
    <tr>
      <th>IPO</th><th>Type</th><th>Total (X)</th><th>Status</th><th>Closing Date</th>
      <th>QIB (X)</th><th>sHNI (X)</th><th>bHNI (X)</th><th>NII (X)</th><th>Retail (X)</th>
      <th>Employee (X)</th><th>Updated</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Om Galaxy LtdBSE/SME</td><td>SME</td><td>0.95x</td><td>OPEN NOW</td><td>15 Sep 2026</td>
      <td>3.11</td><td>0.04</td><td>0.06</td><td>0.05</td><td>0.10</td><td>—</td><td>—</td>
    </tr>
    <tr>
      <td>Maharaja &amp; Speedex India LtdBSE/SME</td><td>SME</td><td>0.55x</td><td>OPEN NOW</td><td>15 Sep 2026</td>
      <td>0.10</td><td>0.80</td><td>1.34</td><td>1.16</td><td>0.56</td><td>—</td><td>—</td>
    </tr>
  </tbody>
</table>
</body></html>
"""

IPOPREMIUM_HTML = """
<html><body>
<section>
  <h3>Shakti Polytarp Ltd. (BSE SME)</h3>
  <p>Date: 15th to 17th Sep 2026</p>
  <p>Last updated on 15-Sep-2026 16:47:24</p>
  <h4>Subscription Details (No. of Shares)</h4>
  <table>
    <tr><th>Category</th><th>Offered</th><th>Applied</th><th>Times</th></tr>
    <tr><td>QIBs</td><td>564000</td><td>0</td><td>0</td></tr>
    <tr><td>HNIs</td><td>1368000</td><td>2066000</td><td>1.51</td></tr>
    <tr><td>bHNI</td><td>912000</td><td>1928000</td><td>2.11</td></tr>
    <tr><td>sHNI</td><td>456000</td><td>138000</td><td>0.30</td></tr>
    <tr><td>Individual</td><td>1580000</td><td>168000</td><td>0.11</td></tr>
    <tr><td>Total</td><td>3512000</td><td>2234000</td><td>0.64</td></tr>
  </table>
  <h4>Application-Wise Breakup</h4>
</section>
<section>
  <h3>Vama Wovenfab Ltd. (BSE SME)</h3>
  <p>Date: 15th to 17th Sep 2026</p>
  <p>Last updated on 15-Sep-2026 17:13:29</p>
  <h4>Subscription Details (No. of Shares)</h4>
  <table>
    <tr><th>Category</th><th>Offered</th><th>Applied</th><th>Times</th></tr>
    <tr><td>QIBs</td><td>14400</td><td>0</td><td>0</td></tr>
    <tr><td>HNIs</td><td>276000</td><td>2400</td><td>0.01</td></tr>
    <tr><td>bHNI</td><td>183600</td><td>0</td><td>0</td></tr>
    <tr><td>sHNI</td><td>92400</td><td>2400</td><td>0.03</td></tr>
    <tr><td>Individual</td><td>1089600</td><td>14400</td><td>0.01</td></tr>
    <tr><td>Total</td><td>1380000</td><td>16800</td><td>0.01</td></tr>
  </table>
  <h4>Application-Wise Breakup</h4>
</section>
</body></html>
"""


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, html=GROWW_HTML):
        self.html = html

    def get(self, url, timeout=None):
        return FakeResponse(self.html)


class FailingClient:
    source_name = "Broken secondary"
    last_observed_at = None

    def detail(self, company):
        raise ValueError("not available")


class PrioritySubscriptionV3Tests(unittest.TestCase):
    def test_groww_table_is_parsed_by_named_columns(self):
        rows = mod.parse_groww_subscription_html(GROWW_HTML)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["key"], "RAKSANTRANSFORMERS")
        self.assertEqual(
            rows[0]["subscription"],
            {"qib": 3.87, "nii": 0.38, "retail": 0.35, "total": 1.29},
        )

    def test_ipodhamaka_table_uses_aggregate_nii_named_column(self):
        rows = mod.parse_ipodhamaka_subscription_html(IPODHAMAKA_HTML)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["company"], "Om Galaxy Ltd")
        self.assertEqual(rows[0]["key"], "OMGALAXY")
        self.assertEqual(
            rows[0]["subscription"],
            {"qib": 3.11, "nii": 0.05, "retail": 0.10, "total": 0.95},
        )
        self.assertEqual(rows[1]["subscription"]["nii"], 1.16)

    def test_ipopremium_cards_use_aggregate_rows_and_source_timestamp(self):
        rows = mod.parse_ipopremium_subscription_html(IPOPREMIUM_HTML)
        self.assertEqual(len(rows), 2)
        shakti = rows[0]
        self.assertEqual(shakti["key"], "SHAKTIPOLYTARP")
        self.assertEqual(
            shakti["subscription"],
            {"qib": 0.0, "nii": 1.51, "retail": 0.11, "total": 0.64},
        )
        self.assertEqual(shakti["observedAt"], "2026-09-15T16:47:24+05:30")
        self.assertEqual(
            rows[1]["subscription"],
            {"qib": 0.0, "nii": 0.01, "retail": 0.01, "total": 0.01},
        )
        self.assertEqual(rows[1]["observedAt"], "2026-09-15T17:13:29+05:30")

    def test_ipopremium_parser_fails_closed_without_explicit_total(self):
        html = IPOPREMIUM_HTML.replace(
            "<tr><td>Total</td><td>3512000</td><td>2234000</td><td>0.64</td></tr>",
            "",
        )
        rows = mod.parse_ipopremium_subscription_html(html)
        self.assertEqual([row["key"] for row in rows], ["VAMAWOVENFAB"])

    def test_ipodhamaka_exchange_badge_is_not_part_of_company_match(self):
        rows = mod.parse_ipodhamaka_subscription_html(IPODHAMAKA_HTML)
        self.assertEqual(rows[1]["company"], "Maharaja & Speedex India Ltd")
        self.assertNotIn("BSE", rows[1]["key"])
        self.assertNotIn("SME", rows[1]["key"])

    def test_missing_values_do_not_become_zero(self):
        html = GROWW_HTML.replace("3.87x", "--").replace("0.38x", "--")
        rows = mod.parse_groww_subscription_html(html)
        self.assertIsNone(rows[0]["subscription"]["qib"])
        self.assertIsNone(rows[0]["subscription"]["nii"])
        self.assertEqual(rows[0]["subscription"]["retail"], 0.35)

    def test_parser_fails_closed_without_named_headers(self):
        html = "<table><tr><td>Example IPO</td><td>1.2x</td><td>2.3x</td></tr></table>"
        self.assertEqual(mod.parse_groww_subscription_html(html), [])
        self.assertEqual(mod.parse_ipodhamaka_subscription_html(html), [])
        self.assertEqual(mod.parse_ipopremium_subscription_html(html), [])

    def test_client_matches_short_secondary_company_name(self):
        client = mod.GrowwSubscriptionClient()
        client.s = FakeSession()
        parsed, url = client.detail("CENTURY BUSINESS MEDIA LIMITED")
        self.assertEqual(parsed["qib"], 3.51)
        self.assertEqual(parsed["total"], 1.06)
        self.assertEqual(url, mod.GROWW_SUBSCRIPTION_URL)

    def test_ipodhamaka_client_matches_full_tracker_company_name(self):
        client = mod.IPODhamakaSubscriptionClient()
        client.s = FakeSession(IPODHAMAKA_HTML)
        parsed, url = client.detail("OM GALAXY LIMITED")
        self.assertEqual(parsed["qib"], 3.11)
        self.assertEqual(parsed["total"], 0.95)
        self.assertEqual(url, mod.IPODHAMAKA_SUBSCRIPTION_URL)

    def test_ipopremium_client_matches_tracker_company_and_keeps_observation_time(self):
        client = mod.IPOPremiumSubscriptionClient()
        client.s = FakeSession(IPOPREMIUM_HTML)
        parsed, url = client.detail("SHAKTI POLYTARP LIMITED")
        self.assertEqual(parsed["nii"], 1.51)
        self.assertEqual(parsed["total"], 0.64)
        self.assertEqual(url, mod.IPOPREMIUM_SUBSCRIPTION_URL)
        self.assertEqual(client.last_observed_at, "2026-09-15T16:47:24+05:30")

    def test_secondary_chain_moves_to_next_provider_after_failure(self):
        client = mod.IPODhamakaSubscriptionClient()
        client.s = FakeSession(IPODHAMAKA_HTML)
        parsed, url, source_name, observed_at = mod._secondary_detail(
            [FailingClient(), client], "OM GALAXY LIMITED"
        )
        self.assertEqual(parsed["retail"], 0.10)
        self.assertEqual(url, mod.IPODHAMAKA_SUBSCRIPTION_URL)
        self.assertEqual(source_name, mod.IPODHAMAKA_SOURCE_NAME)
        self.assertIsNone(observed_at)

    def test_secondary_source_is_explicitly_marked_non_exchange(self):
        record = {
            "sources": [
                {
                    "name": mod.IPODHAMAKA_SOURCE_NAME,
                    "kind": "exchange",
                    "url": mod.IPODHAMAKA_SUBSCRIPTION_URL,
                }
            ]
        }
        mod._mark_secondary_provenance(record, mod.IPODHAMAKA_SOURCE_NAME)
        self.assertEqual(record["sources"][0]["kind"], "secondary-market-data")


if __name__ == "__main__":
    unittest.main()
