"""Regressions from the six September 2026 P1/P2 source-document gaps."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import offer_parser as parser


class IntermediaryLayoutTests(unittest.TestCase):
    def test_official_role_tables_and_evidence_pages(self):
        # Fixed Poppler layout excerpts, with official URLs and PDF hashes.
        cases = json.loads((Path(__file__).parent / 'fixtures/intermediary_role_layouts.json').read_text(encoding='utf-8'))
        for case in cases:
            with self.subTest(issuer=case['id']):
                leads, registrar, evidence = parser.extract_intermediaries(case['text'])
                self.assertEqual(leads, case['leadManagers'])
                self.assertEqual(registrar, case['registrar'])
                self.assertEqual(evidence['leadManagers']['page'], case['leadPage'])
                self.assertEqual(evidence['registrar']['page'], case['registrarPage'])

    def test_details_in_prose_are_not_role_headings(self):
        text = 'For details of the book running lead managers see page 12.\nExample Capital Limited\n'
        self.assertEqual(parser.extract_intermediaries(text), ([], None, {}))

    def test_page_continuation_stops_at_another_section(self):
        text = 'REGISTRAR TO THE OFFER\nName and Logo\n\nSUMMARY\n\n\n\n\n1\fExample Registry Services Limited'
        self.assertEqual(parser.extract_intermediaries(text), ([], None, {}))

    def test_contact_column_cannot_supply_entity(self):
        text = ('BOOK RUNNING LEAD MANAGERS\n'
                'Name and Logo                                        Contact Person          Email and Telephone\n'
                '                                                     Example Capital Limited\n'
                'BID/OFFER PERIOD\n')
        self.assertEqual(parser.extract_intermediaries(text), ([], None, {}))


if __name__ == '__main__':
    unittest.main()
