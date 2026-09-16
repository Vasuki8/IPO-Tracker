import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import offer_parser as parser
from run_offer_documents import correct_record
from validate_data import validate_payload

# Factual rows transcribed from SEBI Sonaselection AP, printed pp. 4, 7-8.
# Source SHA-256: 7a3439da4e2f477a43add07c56e2e0b3f9c6a1bd250f78d18a80000ef91d22d3
SOURCE_ROWS = """
[PAGE 2]
                                                                          BOOK      RUNNING        LEAD      MANAGER
               Name    and   Logo    of the  Book    Running     Lead   Manager                     Contact    Person                            E-mail    and   Telephone
                                                   Choice    Capital Advisors            Nimisha    Joshi/   Nishant   Baghmar             E-mail:    ssil.ipo@choiceindia.com
                                                         Private   Limited                                                                  Tel:  +91-022-6707      9999   (7919)
                                                                                    REGISTRAR          TO   THE    ISSUE
                                   Name    of  the  Registrar                                              Contact    Person                          E-mail   and   Telephone
                                                  Kfin  Technologies     Limited                  M   Murali    Krishna                     E-mail:    sona.ipo@kfintech.com
                                                                                                                                                 Tel:  +91   40  6716   2222
\f[PAGE 5]
Summary of Restated Consolidated Financial Information
Fiscal 2026, Fiscals 2025 and Fiscal 2024
(₹ in million)
Particulars Fiscal 2026 Fiscal 2025 Fiscal 2024
Revenue from Operations(1) 5,169.49 3,159.52 1,209.79
EBITDA(2) 847.74 581.19 284.87
Profit after Tax (PAT)(4) 340.23 185.63 130.95
\f[PAGE 6]
Summary of Key Performance Indicators
(₹ in million)
Particulars Fiscal 2026 Fiscal 2025 Fiscal 2024
Return on Net Worth(6) in % 39.05% 34.08% 40.46%
"""


class CurrentParserTests(unittest.TestCase):
    def test_real_table_year_alignment_and_roles(self):
        result = parser.parse_document_text(SOURCE_ROWS)
        years = {row['period']: row for row in result['financials']['periods']}
        self.assertEqual(years['FY2025']['revenueCr'], 315.952)
        self.assertEqual(years['FY2024']['revenueCr'], 120.979)
        self.assertEqual(years['FY2025']['patCr'], 18.563)
        self.assertEqual(result['leadManagers'], ['Choice Capital Advisors Private Limited'])
        self.assertEqual(result['registrar'], 'Kfin Technologies Limited')
        self.assertTrue(all('netWorthCr' not in row for row in years.values()))
        self.assertEqual(result['fieldEvidence']['financials']['FY2025.revenueCr']['page'], 5)

    def test_year_order_comes_from_header_not_narrative(self):
        sample = SOURCE_ROWS.replace('Fiscal 2026, Fiscals 2025 and Fiscal 2024', 'Fiscal 2024 and Fiscal 2026 were discussed before Fiscal 2025')
        self.assertEqual(parser.extract_financials(sample)['periods'][1]['revenueCr'], 315.952)

    def test_negative_and_missing_cells_do_not_shift_years(self):
        sample = 'Summary of Financial Information\n(₹ in crore)\nParticulars Fiscal 2024 Fiscal 2025 Fiscal 2026\nRevenue from Operations 10 - 30\nProfit after Tax (12) 3 4\n'
        rows = parser.extract_financials(sample)['periods']
        self.assertEqual(rows[0]['patCr'], -12)
        self.assertNotIn('revenueCr', rows[1])
        self.assertEqual(rows[2]['revenueCr'], 30)

    def test_conflicting_tables_quarantine_cell(self):
        sample = SOURCE_ROWS + '\fSummary of Financial Information\n(₹ in million)\nParticulars Fiscal 2026 Fiscal 2025 Fiscal 2024\nRevenue from Operations 5000 3159.52 1209.79\n'
        financials, evidence, conflicts = parser.extract_financials_with_evidence(sample)
        self.assertIn('FY2026.revenueCr', conflicts)
        self.assertNotIn('revenueCr', financials['periods'][0])

    def test_narrative_numbers_are_not_financial_rows(self):
        self.assertIsNone(parser.extract_financials('In Fiscal 2026 and Fiscal 2025 revenue was reported. See page 2026. Net worth ratios are discussed on page 31.'))

    def test_final_prospectus_repair_is_audited_idempotent_and_authoritative(self):
        record = {'id': 'sona', 'company': 'Sonaselection India Limited', 'lotSize': 150, 'financials': {'unit': '₹ crore', 'periods': [{'period': 'FY2025', 'revenueCr': 120.979}]}, 'leadManagers': ['BSE Limited']}
        result = parser.parse_document_text(SOURCE_ROWS)
        result['lotSize'] = 999
        doc = {'url': 'https://www.sebi.gov.in/official.pdf', 'source': 'SEBI', 'type': 'PROSPECTUS', 'title': 'Final Prospectus'}
        self.assertTrue(correct_record(record, result, doc, 'hash', 3, 8))
        self.assertEqual(record['lotSize'], 999)
        self.assertEqual(record['staticFieldProvenance']['lotSize']['documentType'], 'PROSPECTUS')
        count = len(record['dataCorrections'])
        self.assertEqual(correct_record(record, result, doc, 'hash', 3, 8), [])
        self.assertEqual(len(record['dataCorrections']), count)
        self.assertEqual(validate_payload({'ipos': [record]})['errorCount'], 0)

    def test_unsupported_final_layout_preserves_values_for_review(self):
        record = {'id': 'x', 'financials': {'periods': [{'period': 'FY2025', 'patCr': 10}]}}
        before = copy.deepcopy(record['financials'])
        correct_record(
            record,
            {},
            {'url': 'https://www.sebi.gov.in/a.pdf', 'type': 'PROSPECTUS', 'title': 'Final Prospectus'},
            'hash',
            1,
            1,
        )
        self.assertEqual(record['financials'], before)
        self.assertEqual(record['documentRepair']['financialStatus'], 'needs_review')
        self.assertIn('financials', record['staticSourcePolicy']['pendingRevalidationFields'])

    def test_split_annual_header_and_interim_rejection(self):
        text = 'Summary of Financial Information\n(₹ in lakhs)\nParticulars March 31, March 31, March 31,\n2026 2025 2024\nNet worth (1) 64754.31 48929.71 29593.38\nRevenue from operations 167766.09 143040.38 95311.60\n'
        rows = parser.extract_financials(text)['periods']
        self.assertEqual(rows[1]['netWorthCr'], 489.2971)
        self.assertEqual(rows[1]['revenueCr'], 1430.4038)
        self.assertIsNone(parser.extract_financials(text.replace('Particulars March', 'For six months ended September 30 and March')))

    def test_contact_rows_and_former_names_cannot_become_managers(self):
        text = """BOOK RUNNING LEAD MANAGERS
Name and Logo                                                     Contact Person                  Email and Telephone
Lead Managers
                                                                                  Mr Contact
          IIFL Capital Services Limited (formerly known as
          IIFL Securities Limited)
          JM Financial Limited
REGISTRAR TO THE OFFER
Name and Logo                                                     Contact Person
          MUFG Intime India Private Limited (formerly Link
          Intime India Private Limited)
BID/OFFER PERIOD
"""
        leads, registrar, evidence = parser.extract_intermediaries(text)
        self.assertEqual(leads, ['IIFL Capital Services Limited', 'JM Financial Limited'])
        self.assertEqual(registrar, 'MUFG Intime India Private Limited')

    def test_validity_flags_populated_bad_data(self):
        record = {'id': 'x', 'leadManagers': ['BSE Limited'], 'lotSize': -5, 'priceBand': {'min': 110, 'max': 100}}
        self.assertEqual(validate_payload({'ipos': [record]})['errorCount'], 4)


if __name__ == '__main__':
    unittest.main()
