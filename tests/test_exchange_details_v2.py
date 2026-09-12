import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_exchange_details_v2.py"
spec = importlib.util.spec_from_file_location("enrich_exchange_details_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class ExchangeDetailV2Tests(unittest.TestCase):
    def test_parser_version(self):
        self.assertEqual(mod.PARSER_VERSION, 2)

    def test_alternate_lot_labels_are_parsed(self):
        html = """
        <table>
          <tr><td>Security Type</td><td>Equity</td></tr>
          <tr><td>Price Band</td><td>Rs. 95 to Rs. 100</td></tr>
          <tr><td>Market Lot Size</td><td>800</td></tr>
          <tr><td>Minimum Order Quantity</td><td>1600</td></tr>
        </table>
        """
        detail = mod.parse_detail_html(html)
        self.assertEqual(detail["marketLot"], 800)
        self.assertEqual(detail["minimumBidQuantity"], 1600)
        self.assertEqual(detail["lotSize"], 1600)
        self.assertEqual(detail["minInvestment"], 160000.0)

    def test_direct_issue_size_crore_outranks_share_price_estimate(self):
        html = """
        <table>
          <tr><td>Security Type</td><td>Equity</td></tr>
          <tr><td>Price Band</td><td>Rs. 100 to Rs. 110</td></tr>
          <tr><td>Issue Size - No. of Shares</td><td>10,00,000</td></tr>
          <tr><td>Issue Size (Rs. Cr.)</td><td>12.50</td></tr>
        </table>
        """
        detail = mod.parse_detail_html(html)
        self.assertEqual(detail["sharesOffered"], 1_000_000)
        self.assertEqual(detail["issueSizeCr"], 12.5)

    def test_lakh_issue_amount_converts_to_crore(self):
        html = """
        <table>
          <tr><td>Security Type</td><td>Equity</td></tr>
          <tr><td>Issue Size (Rs. Lakhs)</td><td>8,904.00</td></tr>
        </table>
        """
        detail = mod.parse_detail_html(html)
        self.assertEqual(detail["issueSizeCr"], 89.04)

    def test_plain_share_count_is_not_treated_as_money(self):
        self.assertIsNone(mod.parse_money_crore("1,248,000", label="Issue Size"))

    def test_explicit_rupees_without_scale_converts_to_crore(self):
        self.assertEqual(
            mod.parse_money_crore("Rs. 1,250,000,000", label="Issue Amount"),
            125.0,
        )

    def test_alternate_share_label_can_derive_issue_size(self):
        html = """
        <table>
          <tr><td>Security Type</td><td>Equity</td></tr>
          <tr><td>Issue Price</td><td>Rs. 200</td></tr>
          <tr><td>No. of Equity Shares Offered</td><td>25,00,000</td></tr>
        </table>
        """
        detail = mod.parse_detail_html(html)
        self.assertEqual(detail["sharesOffered"], 2_500_000)
        self.assertEqual(detail["issueSizeCr"], 50.0)


if __name__ == "__main__":
    unittest.main()
