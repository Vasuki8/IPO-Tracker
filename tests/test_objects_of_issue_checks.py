import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from objects_of_issue_checks import objects_problems, objects_quarantined


class ObjectsOfIssueChecksTests(unittest.TestCase):
    def test_actual_annu_and_veegaland_contents_rows_are_rejected(self):
        cases = {
            "annu": [
                ("BASIS FOR ISSUE PRICE", 117),
                ("STATEMENT OF POSSIBLE SPECIAL TAX BENEFITS", 127),
                ("SECTION IV: ABOUT OUR COMPANY", 130),
                ("INDUSTRY OVERVIEW", 130),
                ("OUR BUSINESS", 213),
                ("KEY REGULATIONS AND POLICIES IN INDIA", 246),
                ("HISTORY AND CERTAIN CORPORATE MATTERS", 253),
                ("OUR MANAGEMENT", 260),
                ("OUR PROMOTERS AND PROMOTER GROUP", 276),
                ("GROUP COMPANIES", 279),
                ("DIVIDEND POLICY", 282),
                ("SECTION V: FINANCIAL INFORMATION", 283),
            ],
            "veegaland": [
                ("BASIS FOR THE ISSUE PRICE", 150),
                ("STATEMENT OF SPECIAL TAX BENEFITS", 160),
                ("SECTION – IV ABOUT OUR COMPANY", 166),
                ("INDUSTRY OVERVIEW", 166),
                ("OUR BUSINESS", 226),
                ("KEY REGULATIONS AND POLICIES IN INDIA", 255),
                ("HISTORY AND CERTAIN CORPORATE MATTERS", 269),
                ("OUR MANAGEMENT", 275),
                ("OUR PROMOTERS AND PROMOTER GROUP", 297),
                ("DIVIDEND POLICY", 303),
                ("SECTION V – FINANCIAL INFORMATION", 304),
                ("RESTATED FINANCIAL INFORMATION", 304),
            ],
        }
        for issuer, rows in cases.items():
            for purpose, amount in rows:
                with self.subTest(issuer=issuer, purpose=purpose):
                    self.assertTrue(objects_problems([{"purpose": purpose, "amountCr": amount}]))

    def test_heading_spacing_case_numbering_and_dot_leaders_are_rejected(self):
        for purpose in (
            "  basis\nfor the OFFER price  ",
            "2. OUR MANAGEMENT",
            "A. INDUSTRY OVERVIEW",
            "TABLE OF CONTENTS",
            "OUR BUSINESS 213",
            "Working Capital Requirements ............",
            "Proposed utilisation . . . . 123",
            "Purpose … 123",
        ):
            with self.subTest(purpose=purpose):
                self.assertTrue(objects_problems([{"purpose": purpose, "amountCr": 123}]))

    def test_legitimate_source_purposes_need_no_keyword_whitelist(self):
        for purpose in (
            "Working Capital Requirements",
            "Funding capital expenditure for new manufacturing facilities",
            "Repayment or prepayment of identified borrowings",
            "General Corporate Purposes",
            "Issue Related Expenses",
            "Research and development of new formulations",
            "Brand promotion and customer outreach",
            "Employee training and certification",
            "Our business expansion",
            "Our subsidiaries' working capital requirements",
            "Investment in our subsidiary, Example Limited",
            "Acquisition of land for the proposed plant",
        ):
            with self.subTest(purpose=purpose):
                self.assertEqual(objects_problems([{"purpose": purpose, "amountCr": 12.5}]), [])

    def test_absent_undisclosed_zero_and_integer_amounts_are_allowed(self):
        self.assertEqual(objects_problems(None), [])
        self.assertEqual(objects_problems([]), [])
        self.assertEqual(objects_problems([{"purpose": "Research and development"}]), [])
        for amount in (None, 0, 0.0, 12, 12.5):
            with self.subTest(amount=amount):
                self.assertEqual(objects_problems([{"purpose": "Research and development", "amountCr": amount}]), [])

    def test_flattened_monetary_columns_and_page_reference_rows_are_rejected(self):
        cases = (
            ("Funding capital expenditure requirements of our Company for purchase of 154.08", 0.997),
            ("Funding working capital requirements of our Company 1,150.00", 7.44),
            ("General corporate purposes 241.60", 1.563),
            ("Funding working capital requirements of our 1,150.00 650.00", 50),
            ("Funding working capital requirements 1,150", 7.44),
            ("Funding working capital requirements 1,15,000", 7.44),
            ("ee “Issue Related Expenses” on page", 1.45),
            ("See the proposed capital expenditure on pages", 130),
        )
        for purpose, amount in cases:
            with self.subTest(purpose=purpose):
                self.assertTrue(objects_problems([{"purpose": purpose, "amountCr": amount}]))

    def test_legitimate_numeric_references_in_purposes_are_allowed(self):
        for purpose in (
            "Funding expansion under Phase 2",
            "Purchase of equipment for Unit 3",
            "Working capital requirements for FY2026",
            "General corporate purposes (1)",
            "Funding the proposed project (2.1)",
            "Acquisition of 154.08 acres of land",
            "Funding purchase of 1,150 machines",
            "Capital expenditure described on page 145",
        ):
            with self.subTest(purpose=purpose):
                self.assertEqual(objects_problems([{"purpose": purpose, "amountCr": 12.5}]), [])

    def test_malformed_rows_and_purposes_are_rejected(self):
        for value in ({}, "Working capital", 1, [{"amountCr": 10}], [None], ["Working capital"],
                      [{"purpose": None}], [{"purpose": "   "}], [{"purpose": 123}]):
            with self.subTest(value=value):
                self.assertTrue(objects_problems(value))

    def test_nonfinite_negative_boolean_and_text_amounts_are_rejected(self):
        for amount in (float("nan"), float("inf"), -float("inf"), -0.01, True, False, "12", {}, [], 10 ** 400):
            with self.subTest(amount=amount):
                self.assertTrue(objects_problems([{"purpose": "Working capital", "amountCr": amount}]))

    def test_one_bad_row_cannot_hide_in_a_valid_list(self):
        rows = [
            {"purpose": "Working capital", "amountCr": 10},
            {"purpose": "BASIS FOR ISSUE PRICE", "amountCr": 117},
        ]
        problems = objects_problems(rows)
        self.assertEqual(len(problems), 1)
        self.assertIn("row 2", problems[0])

    def test_only_explicit_active_quarantine_is_reported(self):
        for review in (None, {}, [], "quarantined", {"status": "resolved"}, {"status": "pending"}):
            with self.subTest(review=review):
                self.assertFalse(objects_quarantined({"objectsOfIssueReview": review}))
        self.assertFalse(objects_quarantined({}))
        self.assertTrue(objects_quarantined({"objectsOfIssueReview": {"status": "quarantined"}}))


if __name__ == "__main__":
    unittest.main()
