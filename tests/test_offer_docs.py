import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_offer_docs.py"
spec = importlib.util.spec_from_file_location("enrich_offer_docs", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


SAMPLE = """
EXAMPLE INDIA LIMITED
THE PROMOTERS OF OUR COMPANY
ALPHA SHAH, BETA SHAH AND EXAMPLE HOLDINGS PRIVATE LIMITED
DETAILS OF THE ISSUE
Fresh issue of up to 14,300,000 Equity Shares of face value of ₹ 10/- each.
DETAILS OF THE OFFER FOR SALE
NOT APPLICABLE

BOOK RUNNING LEAD MANAGER
Name and Logo of the Book Running Lead Manager Contact Person E-mail and Telephone
Choice Capital Advisors
Private Limited
Contact Person Example
REGISTRAR TO THE ISSUE
Name of the Registrar Contact Person E-mail and Telephone
Kfin Technologies Limited M Murali Krishna E-mail: ipo@example.com
BID/ ISSUE PERIOD

4. Objects of the Issue
The Net Proceeds are proposed to be utilised in the following manner:
(₹ in million)
Particulars Amount
Repayment and/or pre-payment of certain borrowings 800.00
Funding of capital expenditure towards plant and machinery 506.11
General Corporate Purposes (1) [●]
Grand Total(1) [●]
5. Pre and Post-Issue shareholding of our Promoters and additional top 10 Shareholders
Promoters and Promoter Group (1)
1. Alpha Shah 7,259,627 17.07 [●] [●]
2. Beta Shah 17,642,335 41.48 [●] [●]
3. Example Holdings Private Limited 11,765,000 27.66 [●] [●]
Promoter Group
1. Other Person 13 Negligible
6. Summary of Restated Consolidated Financial Information
(₹ in million except for percentages)
Particulars Fiscal 2026 Fiscal 2025 Fiscal 2024
Revenue from Operations(1) 5,169.49 3,159.52 1,209.79
EBITDA(2) 847.74 581.19 284.87
Profit after Tax (PAT)(4) 340.23 185.63 130.95
7. Summary of Key Performance Indicators
Key Performance Indicators (KPIs) Unit Fiscal 2026 Fiscal 2025 Fiscal 2024
Return on Net Worth(6) in % 39.05% 34.08% 40.46%
8. Risk Factors
"""


class OfferDocumentTests(unittest.TestCase):
    def test_parses_intermediaries_and_promoters(self):
        parsed = mod.parse_document_text(SAMPLE, {"min": 94, "max": 99})
        self.assertEqual(parsed["leadManagers"], ["Choice Capital Advisors Private Limited"])
        self.assertEqual(parsed["registrar"], "Kfin Technologies Limited")
        self.assertEqual(
            parsed["promoters"],
            ["ALPHA SHAH", "BETA SHAH", "EXAMPLE HOLDINGS PRIVATE LIMITED"],
        )

    def test_issue_share_count_is_valued_at_cap_price(self):
        issue = mod.extract_issue_composition(SAMPLE, {"min": 94, "max": 99})
        self.assertEqual(issue["freshShares"], 14_300_000)
        self.assertEqual(issue["ofsShares"], 0)
        self.assertEqual(issue["freshIssueCr"], 141.57)
        self.assertEqual(issue["totalIssueSizeCr"], 141.57)

    def test_financials_convert_million_to_crore(self):
        financials = mod.extract_financials(SAMPLE)
        self.assertEqual(financials["periods"][0]["period"], "FY2026")
        self.assertAlmostEqual(financials["periods"][0]["revenueCr"], 516.949)
        self.assertAlmostEqual(financials["periods"][0]["ebitdaCr"], 84.774)
        self.assertAlmostEqual(financials["periods"][0]["patCr"], 34.023)
        self.assertEqual(financials["periods"][0]["ronwPct"], 39.05)
        self.assertNotIn("netWorthCr", financials["periods"][0])

    def test_objects_and_promoter_shareholding(self):
        objects = mod.extract_objects(SAMPLE)
        self.assertEqual(objects[0]["amountCr"], 80.0)
        self.assertEqual(objects[1]["amountCr"], 50.611)
        self.assertIsNone(objects[2]["amountCr"])
        shareholding = mod.extract_promoter_shareholding(SAMPLE)
        self.assertAlmostEqual(shareholding["promoterPreIssuePct"], 86.21)
        self.assertEqual(len(shareholding["promoters"]), 3)

    def test_prefers_latest_highest_stage_abridged_pdf(self):
        rec = {
            "documents": [
                {"type": "DRHP", "title": "Example - Draft Abridged Prospectus", "url": "https://x/old_AP_p.pdf", "filedDate": "2026-01-01"},
                {"type": "RHP", "title": "Example - Abridged Prospectus", "url": "https://x/new_AP_p.pdf", "filedDate": "2026-09-01"},
                {"type": "RHP", "title": "Example full RHP", "url": "https://x/full.pdf", "filedDate": "2026-09-02"},
            ]
        }
        self.assertEqual(mod.choose_document(rec)["url"], "https://x/new_AP_p.pdf")


if __name__ == "__main__":
    unittest.main()
