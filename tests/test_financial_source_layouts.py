import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import offer_parser as parser

FIXTURES = Path(__file__).parent / "fixtures/financials"


class FinancialSourceLayoutsTests(unittest.TestCase):
    def source(self, name):
        return parser.extract_financials_with_evidence((FIXTURES / (name + "-annual-table.txt")).read_text())

    def test_jindal_annual_columns_and_explicit_lakh_unit_across_page_break(self):
        financials, evidence, conflicts = self.source("jsipl")
        self.assertFalse(conflicts)
        self.assertEqual([row["period"] for row in financials["periods"]], ["FY2026", "FY2025", "FY2024"])
        row = financials["periods"][0]
        self.assertEqual(row["revenueCr"], 675.3872)
        self.assertEqual(row["netWorthCr"], 96.8248)
        self.assertEqual(row["patCr"], 22.5291)
        self.assertEqual(evidence["FY2026.revenueCr"]["sourceColumns"], [1, 2, 3])

    def test_nse_selected_financial_heading_retains_only_annual_periods(self):
        financials, evidence, conflicts = self.source("nse")
        self.assertFalse(conflicts)
        self.assertEqual(financials["periods"][0]["revenueCr"], 16601.309)
        self.assertEqual(financials["periods"][0]["dilutedEps"], 41.62)
        self.assertEqual(evidence["FY2026.patCr"]["sourceColumns"], [2, 3, 4])
        self.assertEqual(evidence["FY2026.revenueCr"]["scope"], "consolidated")

    def test_esds_staggered_annual_dates_form_three_columns(self):
        financials, evidence, conflicts = self.source("esds")
        self.assertFalse(conflicts)
        self.assertEqual([row["revenueCr"] for row in financials["periods"]], [472.21, 361.335, 286.518])
        self.assertEqual(financials["periods"][0]["patCr"], 120.823)
        self.assertEqual(evidence["FY2024.revenueCr"]["sourceColumns"], [0, 1, 2])

    def test_shared_kpi_header_respects_new_scope_and_explicit_million_abbreviation(self):
        text = """Summary of Key Performance Indicators
Particulars Units Fiscal 2026 Fiscal 2025 Fiscal 2024
Restated Standalone Financial Information
Total Revenue from operations ₹ Mn 7530.42 5964.23 5701.41
Net worth ₹ Mn 30793.93 27677.98 24625.11
Restated Consolidated Financial Information
Total Revenue from operations ₹ Mn 7216.92 5817.57 6058.24
Net worth ₹ Mn 29552.14 26631.40 24265.14
"""
        financials, evidence, conflicts = parser.extract_financials_with_evidence(text)
        self.assertFalse(conflicts)
        self.assertEqual(financials["periods"][0]["revenueCr"], 721.692)
        self.assertEqual(financials["periods"][0]["netWorthCr"], 2955.214)
        self.assertEqual(evidence["FY2026.netWorthCr"]["scope"], "consolidated")

    def test_source_declaration_scope_survives_continued_table(self):
        text = """Summary of Restated Consolidated Financial Information and Restated Standalone Financial Information
The following details are derived from the Restated Consolidated Financial Information
(in ₹ million)
Particulars Fiscal 2026 Fiscal 2025
Net worth 29552.14 26631.40
\fParticulars Fiscal 2026 Fiscal 2025
Total Income 7499.16 6078.39
Restated Standalone Financial Information
(in ₹ million)
Particulars Fiscal 2026 Fiscal 2025
Net worth 30793.93 27677.98
Total Income 7850.77 6233.99
"""
        financials, evidence, conflicts = parser.extract_financials_with_evidence(text)
        self.assertFalse(conflicts)
        self.assertEqual(financials["periods"][0]["totalIncomeCr"], 749.916)
        self.assertEqual(evidence["FY2026.totalIncomeCr"]["scope"], "consolidated")

    def test_currency_is_not_assumed_without_explicit_unit(self):
        text = "Summary of Financial Information\nParticulars Fiscal 2026 Fiscal 2025\nRevenue from operations 100 90\nNet worth 20 10"
        self.assertIsNone(parser.extract_financials(text))

    def test_explicit_maashitla_registrar_table_is_accepted(self):
        text = """REGISTRAR TO THE OFFER
Name and Logo                         Contact Person           Telephone and Email
Maashitla Securities
                                      Mukul Agrawal
Private Limited
BID/OFFER PERIOD
"""
        self.assertEqual(parser.extract_intermediaries(text)[1], "Maashitla Securities Private Limited")

    def test_contact_rows_above_registrar_do_not_contaminate_legal_name(self):
        text = "REGISTRAR TO THE ISSUE\n        Mr. M Murali Krishna\n        Tel. No: +91 40 6716 2222\nKFIN TECHNOLOGIES LIMITED\nBID/ISSUE PERIOD"
        self.assertEqual(parser.extract_intermediaries(text)[1], "KFIN TECHNOLOGIES LIMITED")


if __name__ == "__main__":
    unittest.main()
