"""Regression cases for annual columns and distinct financial measures."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import offer_parser as parser


class SourceColumnTests(unittest.TestCase):
    def test_total_income_does_not_conflict_with_operating_revenue(self):
        text = """Summary of Financial Information
(₹ in crore)
Particulars Fiscal 2025 Fiscal 2024
Revenue from operations 120 100
Total income 125 105
Profit after tax 12 10
"""
        financials, evidence, conflicts = parser.extract_financials_with_evidence(text)
        self.assertEqual(conflicts, [])
        self.assertEqual(financials["periods"][0]["revenueCr"], 120)
        self.assertEqual(financials["periods"][0]["totalIncomeCr"], 125)

    def test_explicit_mixed_dates_preserve_duplicate_year_columns(self):
        text = """Summary of Restated Financial Information
(₹ in million)
Particulars September 30, 2025 September 30, 2024 Fiscal 2025 Fiscal 2024 Fiscal 2023
Net worth 17000 15000 16000 12000 7500
Revenue from operations 8600 7100 15000 10700 6400
"""
        rows = parser.extract_financials(text)["periods"]
        self.assertEqual([r["period"] for r in rows], ["FY2025", "FY2024", "FY2023"])
        self.assertEqual(rows[0]["netWorthCr"], 1600)
        self.assertEqual(rows[-1]["revenueCr"], 640)

    def test_split_mixed_date_headers_use_date_columns(self):
        text = """Summary of Restated Financial Information
(₹ in lakhs)
Particulars December 31, March 31, March 31, March 31,
2025 2025 2024 2023
Revenue from operations 31328.50 35116.02 30486.16 23926.50
Restated profit/(loss) for the year 500 600 400 (100)
"""
        rows = parser.extract_financials(text)["periods"]
        self.assertEqual(rows[0]["revenueCr"], 351.1602)
        self.assertEqual(rows[-1]["patCr"], -1)

    def test_unlabelled_extra_columns_are_rejected(self):
        text = """Summary of Financial Information
(₹ in crore)
Particulars Fiscal 2025 Fiscal 2024
Revenue from operations 999 120 100
Net worth 999 12 10
"""
        self.assertIsNone(parser.extract_financials(text))

    def test_leading_interim_cells_require_horizontal_alignment(self):
        header = "Particulars" + "Fiscal 2025".rjust(60) + "Fiscal 2024".rjust(20) + "Fiscal 2023".rjust(20)
        text = "\n".join(["Summary of Financial Information", "(₹ in crore)", "For six months ended September 30", header,
            "Revenue from operations".ljust(45) + "999".rjust(6) + "120".rjust(20) + "100".rjust(20) + "90".rjust(20),
            "Net worth".ljust(45) + "999".rjust(6) + "12".rjust(20) + "10".rjust(20) + "9".rjust(20)])
        rows = parser.extract_financials(text)["periods"]
        self.assertEqual(rows[0]["revenueCr"], 120)
        self.assertEqual(rows[0]["netWorthCr"], 12)
        self.assertIsNone(parser.extract_financials(text.replace(header, "Particulars Fiscal 2025 Fiscal 2024 Fiscal 2023")))

    def test_registrar_role_can_continue_on_next_page(self):
        text = "REGISTRAR TO THE OFFER\nNAME OF THE REGISTRAR                  CONTACT PERSON\n1\f[PAGE 2]\nKFin Technologies Limited             A Contact\nBID/OFFER PERIOD\n"
        self.assertEqual(parser.extract_intermediaries(text)[1], "KFin Technologies Limited")

    def test_repeated_bad_listing_observation_does_not_duplicate_audit(self):
        from record_integrity import repair
        row = {"id": "x", "openDate": "2025-01-01", "listingDate": "2024-01-01"}
        repair({"ipos": [row]})
        row["listingDate"] = "2024-01-01"
        repair({"ipos": [row]})
        self.assertEqual(len(row["dataCorrections"]), 1)


    def test_numbered_rows_and_shared_annual_date_header(self):
        text = """Summary of Restated Consolidated Financial Information
(in ₹ million)
Sr. no. Particulars As at and for the Financial Year ended March 31,
no. 2026 2025 2024
1 Equity share capital 400 300 200
2 Net Worth(1) 11053.78 6196.99 4050.51
3 Revenue from Operations(2) 13267.53 12560.71 12475.22
4 Basic earnings per equity share 11.53 13.65 12.05
5 Diluted earnings per equity share 11.26 13.41 12.03
"""
        rows = parser.extract_financials(text)["periods"]
        self.assertEqual(rows[0]["netWorthCr"], 1105.378)
        self.assertEqual(rows[0]["eps"], 11.53)
        self.assertEqual(rows[0]["dilutedEps"], 11.26)

    def test_consolidated_and_standalone_are_distinct_reporting_scopes(self):
        text = """Summary of Restated Consolidated Financial Information
(₹ in crore)
Particulars Fiscal 2025 Fiscal 2024
Revenue from operations 120 100
Net worth 50 40
\fSummary of Restated Standalone Financial Information
(₹ in crore)
Particulars Fiscal 2025 Fiscal 2024
Revenue from operations 70 60
Net worth 30 20
"""
        financials, _, conflicts = parser.extract_financials_with_evidence(text)
        self.assertEqual(conflicts, [])
        self.assertEqual(financials["periods"][0]["revenueCr"], 120)

    def test_issuer_hosted_registered_pdf_is_not_skipped(self):
        from run_offer_documents import document_for
        row = {"company": "Example Limited", "documents": [{"source": "Issuer website", "type": "RHP", "url": "https://issuer.example/official.pdf"}]}
        self.assertEqual(document_for(row)["url"], "https://issuer.example/official.pdf")


if __name__ == "__main__":
    unittest.main()
