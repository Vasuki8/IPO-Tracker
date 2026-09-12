import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v2.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


MODERN = """
EXAMPLE TECHNOLOGIES LIMITED
OUR PROMOTERS
Our Promoters are ARUN KUMAR, BINA KUMAR and EXAMPLE HOLDINGS PRIVATE LIMITED.

ISSUE DETAILS
Fresh Issue: up to 2,000,000 Equity Shares aggregating up to ₹ 24.00 crore
Offer for Sale: up to 500,000 Equity Shares aggregating up to ₹ 6.00 crore
Total Issue Size aggregating up to ₹ 30.00 crore

BOOK RUNNING LEAD MANAGER TO THE OFFER
Alpha Capital Markets Private Limited
REGISTRAR TO THE OFFER
Bigshare Services Private Limited
ISSUE OPENS September 20, 2026

Objects of the Offer
(₹ in crore)
1. Funding working capital requirements 10.00
2. Repayment of identified borrowings 8.00
3. General corporate purposes [●]

Restated Standalone Financial Information
(₹ in crore except percentages and per share data)
Particulars March 31, 2026 March 31, 2025 March 31, 2024
Revenue from Operations 125.00 100.00 80.00
EBITDA 25.00 20.00 14.00
Profit for the year 12.50 10.00 7.00
Net Worth 60.00 45.00 35.00

Key Performance Indicators (KPIs)
Particulars March 31, 2026 March 31, 2025 March 31, 2024
Return on Equity 20.83% 22.22% 20.00%
Basic EPS 5.00 4.00 2.80
Risk Factors
"""


class OfferDocumentV2Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 2)
        self.assertEqual(mod.base.PARSER_VERSION, 2)

    def test_modern_issue_wording_and_direct_amounts(self):
        issue = mod.extract_issue_composition(MODERN, {"min": 10, "max": 12})
        self.assertEqual(issue["freshShares"], 2_000_000)
        self.assertEqual(issue["ofsShares"], 500_000)
        self.assertEqual(issue["freshIssueCr"], 24.0)
        self.assertEqual(issue["ofsCr"], 6.0)
        self.assertEqual(issue["totalIssueSizeCr"], 30.0)

    def test_registrar_to_offer_and_brlm_variant(self):
        leads, registrar = mod.extract_intermediaries(MODERN)
        self.assertIn("Alpha Capital Markets Private Limited", leads)
        self.assertEqual(registrar, "Bigshare Services Private Limited")

    def test_our_promoters_sentence_variant(self):
        promoters = mod.extract_promoters(MODERN)
        self.assertEqual(
            promoters,
            ["ARUN KUMAR", "BINA KUMAR", "EXAMPLE HOLDINGS PRIVATE LIMITED"],
        )

    def test_march_31_financial_headers_are_supported(self):
        financials = mod.extract_financials(MODERN)
        first = financials["periods"][0]
        self.assertEqual(first["period"], "FY2026")
        self.assertEqual(first["revenueCr"], 125.0)
        self.assertEqual(first["ebitdaCr"], 25.0)
        self.assertEqual(first["patCr"], 12.5)
        self.assertEqual(first["netWorthCr"], 60.0)
        self.assertEqual(first["roePct"], 20.83)
        self.assertEqual(first["eps"], 5.0)

    def test_objects_of_offer_variant(self):
        objects = mod.extract_objects(MODERN)
        self.assertEqual(objects[0]["amountCr"], 10.0)
        self.assertEqual(objects[1]["amountCr"], 8.0)
        self.assertIsNone(objects[2]["amountCr"])


if __name__ == "__main__":
    unittest.main()
