import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import p4_offer_layouts as parser


DHANLAXMI_ROLES = """
[PAGE 1]
BOOK RUNNING LEAD MANAGER TO THE ISSUE                            REGISTRAR TO THE ISSUE
Name and Logo                                                     Name and Logo
FINSHORE MANAGEMENT SERVICES LIMITED                              BIGSHARE SERVICES PRIVATE LIMITED
Anand / Kunal                                                     Jibu John
BID/ISSUE PERIOD
"""

DHANLAXMI_PROMOTERS = """
NAMES OF PROMOTERS OF THE COMPANY
The Promoters of our Company are being Mr. Kamleshkumar Jayantilal Patel, Mr. Alpeshbhai Jayantilal Patel and Mr. Meet Kamleshkumar Patel.
DETAILS OF THE ISSUE
"""

APEX_PROMOTERS = """
OUR PROMOTERS
Promoters of Our Company are Mr. Anuj Dosajh, Mr. Ramakrishnan Balasundaram Aiyer, Mr. Ajay Raina and Mr. Lalit Mohan Datta. For details of our Promoters please see page 181.
DETAILS OF THE ISSUE
"""

C2C_PROMOTERS = """
OUR PROMOTERS: C2C INNOVATIONS PRIVATE LIMITED, PVR MULTIMEDIA PRIVATE LIMITED, LAKSHMI CHANDRA, MAYA CHANDRA, SUBRAHMANYA SRINIVASA NARENDRA LANKA, KURIYEDATH RAMESH AND MURTAZA ALI SOOMAR
DETAILS OF THE ISSUE
"""

DHANLAXMI_OBJECTS = """
[PAGE 73]
OBJECT OF THE ISSUE
The Net Proceeds from the Issue are proposed to be utilised for the following objects. Utilisation of Net Proceeds is set out below. (Rs. in Lakhs)
Sr. No. Particulars Amount
A. Working Capital Requirements 2,005.77
B. Issue Related Expenses 224.63
C. General Corporate Expenses 150.00
Total 2,380.40
BASIS FOR ISSUE PRICE
"""

TABLE_OF_CONTENTS = """
OBJECTS OF THE ISSUE
BASIS FOR ISSUE PRICE 97
STATEMENT OF POSSIBLE TAX BENEFITS 106
SECTION VIII – ABOUT THE COMPANY 109
INDUSTRY OVERVIEW 109
OUR BUSINESS 125
OUR MANAGEMENT 162
OUR PROMOTERS 181
"""

DHANLAXMI_FINANCIALS = """
RESTATED STATEMENT OF PROFIT AND LOSS
(Rs. in Lakhs)
Particulars 30-09-2024 31-03-2024 31-03-2023 31-03-2022
Revenue From Operations 11,995.01 6,371.03 4,661.07 3,543.06
Profit/(Loss) for the Year 820.81 465.36 299.55 58.28
Basic & Diluted Earnings Per Share 12.13 7.02 4.60 0.90
"""

GANESH_SHAREHOLDING = """
Aggregate Pre-Issue shareholding of our Promoters and Promoter Group
Name of shareholder No. of Equity Shares Percentage
Vibhoar Agrawal 31,544,000 44.49
Rachita Agrawal 26,488,000 37.36
Promoter Group Nil Nil
"""

APEX_SHAREHOLDING = """
As on the date of this Prospectus, our Promoters and members of our Promoter Group hold 94.32% of the pre-issue paid-up equity share capital of our Company.
"""


class P4OfferParserTests(unittest.TestCase):
    def test_two_column_intermediaries_are_split_by_role(self):
        leads, registrar, evidence = parser.extract_paired_intermediaries(DHANLAXMI_ROLES)
        self.assertEqual(leads, ["FINSHORE MANAGEMENT SERVICES LIMITED"])
        self.assertEqual(registrar, "BIGSHARE SERVICES PRIVATE LIMITED")
        self.assertIn("leadManagers", evidence)
        self.assertIn("registrar", evidence)

    def test_promoter_names_are_cleaned_and_fragments_rejected(self):
        names, _ = parser.extract_promoters(DHANLAXMI_PROMOTERS)
        self.assertEqual(
            names,
            [
                "Kamleshkumar Jayantilal Patel",
                "Alpeshbhai Jayantilal Patel",
                "Meet Kamleshkumar Patel",
            ],
        )
        self.assertTrue(parser.valid_promoters(names))
        self.assertFalse(parser.valid_promoters(["being Mr. Kamleshkumar Jayantilal Patel", "Mr"]))

    def test_apex_and_c2c_promoter_layouts(self):
        apex, _ = parser.extract_promoters(APEX_PROMOTERS)
        self.assertEqual(
            apex,
            [
                "Anuj Dosajh",
                "Ramakrishnan Balasundaram Aiyer",
                "Ajay Raina",
                "Lalit Mohan Datta",
            ],
        )
        c2c, _ = parser.extract_promoters(C2C_PROMOTERS)
        self.assertEqual(
            c2c,
            [
                "C2C INNOVATIONS PRIVATE LIMITED",
                "PVR MULTIMEDIA PRIVATE LIMITED",
                "LAKSHMI CHANDRA",
                "MAYA CHANDRA",
                "SUBRAHMANYA SRINIVASA NARENDRA LANKA",
                "KURIYEDATH RAMESH",
                "MURTAZA ALI SOOMAR",
            ],
        )

    def test_objects_require_real_use_of_proceeds_context(self):
        rows, evidence = parser.extract_objects(DHANLAXMI_OBJECTS)
        self.assertEqual(
            rows,
            [
                {"purpose": "Working Capital Requirements", "amountCr": 20.0577},
                {"purpose": "Issue Related Expenses", "amountCr": 2.2463},
                {"purpose": "General Corporate Expenses", "amountCr": 1.5},
            ],
        )
        self.assertTrue(parser.valid_objects(rows))
        self.assertIn("objectsOfIssue", evidence)
        toc_rows, _ = parser.extract_objects(TABLE_OF_CONTENTS)
        self.assertEqual(toc_rows, [])
        self.assertFalse(
            parser.valid_objects(
                [
                    {"purpose": "BASIS FOR ISSUE PRICE", "amountCr": 97.0},
                    {"purpose": "OUR MANAGEMENT", "amountCr": 162.0},
                ]
            )
        )

    def test_promoter_shareholding_narrative_and_aggregate_table(self):
        apex, _ = parser.extract_promoter_shareholding(APEX_SHAREHOLDING)
        self.assertEqual(apex["promoterPreIssuePct"], 94.32)
        ganesh, _ = parser.extract_promoter_shareholding(GANESH_SHAREHOLDING)
        self.assertEqual(ganesh["promoterPreIssuePct"], 81.85)

    def test_numeric_date_financials_keep_only_annual_columns(self):
        financials, evidence = parser.extract_numeric_date_financials(DHANLAXMI_FINANCIALS)
        rows = {row["period"]: row for row in financials["periods"]}
        self.assertNotIn("FY2024-interim", rows)
        self.assertEqual(rows["FY2024"]["revenueCr"], 63.7103)
        self.assertEqual(rows["FY2024"]["patCr"], 4.6536)
        self.assertEqual(rows["FY2023"]["revenueCr"], 46.6107)
        self.assertEqual(rows["FY2023"]["patCr"], 2.9955)
        self.assertEqual(rows["FY2022"]["revenueCr"], 35.4306)
        self.assertIn("FY2024.revenueCr", evidence["financials"])

    def test_merge_replaces_only_proven_invalid_residual_fields(self):
        primary = {
            "promoters": ["being Mr. Kamleshkumar Jayantilal Patel", "Mr"],
            "objectsOfIssue": [
                {"purpose": "BASIS FOR ISSUE PRICE", "amountCr": 97.0},
                {"purpose": "OUR MANAGEMENT", "amountCr": 162.0},
            ],
            "leadManagers": ["Existing Capital Limited"],
            "fieldEvidence": {},
        }
        objects, object_evidence = parser.extract_objects(DHANLAXMI_OBJECTS)
        supplement = {
            "promoters": ["Kamleshkumar Jayantilal Patel", "Alpeshbhai Jayantilal Patel"],
            "objectsOfIssue": objects,
            "leadManagers": ["Replacement Capital Limited"],
            "fieldEvidence": {"promoters": {"heading": "OUR PROMOTERS"}, **object_evidence},
            "residualParserVersion": 4,
        }
        merged = parser.merge_parsed(primary, supplement)
        self.assertEqual(merged["promoters"], supplement["promoters"])
        self.assertEqual(merged["objectsOfIssue"], supplement["objectsOfIssue"])
        self.assertEqual(merged["leadManagers"], primary["leadManagers"])

    def test_targeting_is_recent_and_gap_driven(self):
        recent = {"openDate": "2026-01-01", "promoters": ["Mr"], "objectsOfIssue": []}
        old = {"openDate": "2020-01-01", "promoters": ["Mr"], "objectsOfIssue": []}
        self.assertTrue(parser.needs_repair(recent, date(2026, 9, 16)))
        self.assertFalse(parser.needs_repair(old, date(2026, 9, 16)))


if __name__ == "__main__":
    unittest.main()
