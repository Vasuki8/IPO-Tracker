"""Exact source-column replay plus fail-closed role/evidence boundaries."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import review_intermediary_columns as parser

CASES = json.loads((Path(__file__).parent / 'fixtures/intermediary_columns_reviewed.json').read_text(encoding='utf-8'))


class ReviewedIntermediaryColumnsTests(unittest.TestCase):
    def parse(self, index=0):
        case = CASES[index]
        return parser.extract_intermediary_columns(case['sourceText'], page=case['physicalPage'])

    def assert_rejected(self, text):
        with self.assertRaises(parser.ReviewLayoutError):
            parser.extract_intermediary_columns(text, page=1)

    def test_two_exact_final_prospectus_layouts_and_all_name_spans(self):
        for case in CASES:
            with self.subTest(issuer=case['identity']['id']):
                self.assertEqual(hashlib.sha256(case['sourceText'].encode()).hexdigest(), case['sourceTextSha256'])
                self.assertEqual(case['documentType'], 'PROSPECTUS')
                result = parser.extract_intermediary_columns(case['sourceText'], page=case['physicalPage'])
                for field, expected in case['expected'].items():
                    self.assertEqual(result[field], expected)
                    detail = result['fieldEvidence'][field]
                    self.assertTrue(parser.validate_evidence(field, expected, detail))
                    for span in detail['nameSpans']:
                        self.assertEqual(detail['rawLines'][span['line']][span['start']:span['end']], span['text'])
                        self.assertGreaterEqual(span['start'], detail['columnStart'])
                        if detail['columnEnd'] is not None:
                            self.assertLessEqual(span['end'], detail['columnEnd'])

    def test_vertically_staggered_names_stay_in_their_own_roles(self):
        result = self.parse()
        left = result['fieldEvidence']['leadManagers']['nameSpans'][0]
        right = result['fieldEvidence']['registrar']['nameSpans'][0]
        self.assertNotEqual(left['line'], right['line'])
        self.assertNotIn('SKYLINE', result['leadManagers'][0])

    def test_current_legal_name_excludes_former_name_annotation(self):
        result = self.parse(1)
        self.assertEqual(result['registrar'], 'MUFG INTIME INDIA PRIVATE LIMITED')
        self.assertTrue(any('formerly known' in row for row in result['fieldEvidence']['registrar']['rawLines']))

    def test_flattened_column_text_is_not_source_evidence(self):
        self.assert_rejected('\n'.join(' '.join(line.split()) for line in CASES[0]['sourceText'].splitlines()))

    def test_adjacent_role_headings_without_wide_gutter_are_rejected(self):
        self.assert_rejected('LEAD MANAGER  REGISTRAR TO THE ISSUE\nExample Capital Limited  Example Registry Limited')

    def test_additional_unexplained_heading_is_rejected(self):
        text = CASES[0]['sourceText'].replace('REGISTRAR TO THE ISSUE', 'LEGAL ADVISOR REGISTRAR TO THE ISSUE')
        self.assert_rejected(text)

    def test_joined_legal_entities_in_one_column_are_rejected(self):
        text = CASES[0]['sourceText'].replace('FAST TRACK FINSEC PRIVATE LIMITED', 'Example Capital Limited Other Capital Limited')
        self.assert_rejected(text)

    def test_missing_current_registrar_cannot_use_former_name(self):
        text = CASES[1]['sourceText'].replace('MUFG INTIME INDIA PRIVATE LIMITED', ' ' * len('MUFG INTIME INDIA PRIVATE LIMITED'))
        self.assert_rejected(text)

    def test_contact_metadata_cannot_supply_a_legal_entity(self):
        text = CASES[0]['sourceText'].replace('FAST TRACK FINSEC PRIVATE LIMITED', 'Contact Person: Example Limited')
        self.assert_rejected(text)

    def test_divider_crossing_cannot_shift_a_name_into_another_role(self):
        lines = CASES[0]['sourceText'].splitlines()
        lines[5] = (' ' * 90) + 'SKYLINE FINANCIAL SERVICES PRIVATE LIMITED'
        self.assert_rejected('\n'.join(lines))

    def test_supported_wrapped_name_preserves_multiple_exact_spans(self):
        text = ('LEAD MANAGER' + ' ' * 70 + 'REGISTRAR TO THE ISSUE\n'
                + 'Example Capital'.ljust(70) + 'Example Registry\n'
                + 'Private Limited'.ljust(70) + 'Private Limited\n'
                + 'SEBI Registration'.ljust(70) + 'SEBI Registration\n')
        result = parser.extract_intermediary_columns(text, page=2)
        self.assertEqual(result['leadManagers'], ['Example Capital Private Limited'])
        self.assertEqual(len(result['fieldEvidence']['registrar']['nameSpans']), 2)
        self.assertTrue(parser.validate_evidence('registrar', result['registrar'], result['fieldEvidence']['registrar']))

    def test_conflicting_paired_tables_are_rejected(self):
        text = CASES[0]['sourceText']
        other = text.replace('FAST TRACK FINSEC PRIVATE LIMITED', 'OTHER CAPITAL SERVICES LIMITED')
        self.assert_rejected(text + '\nOFFER PROGRAMME\n' + other)

    def test_evidence_replay_rejects_shifted_offsets_columns_and_wrong_role(self):
        result = self.parse()
        original = result['fieldEvidence']['leadManagers']
        for mutate in (
            lambda d: d['nameSpans'][0].update(start=3),
            lambda d: d.update(columnEnd=d['columnEnd'] + 1),
            lambda d: d.update(heading='REGISTRAR TO THE ISSUE'),
            lambda d: d['headingSpan'].update(end=60),
            lambda d: d['nameSpans'][0].update(text='Wrong Capital Limited'),
        ):
            detail = copy.deepcopy(original)
            mutate(detail)
            with self.assertRaises(parser.ReviewLayoutError):
                parser.validate_evidence('leadManagers', result['leadManagers'], detail)
        with self.assertRaises(parser.ReviewLayoutError):
            parser.validate_evidence('registrar', result['registrar'], original)

    def test_evidence_replay_rejects_raw_line_or_value_changes(self):
        result = self.parse()
        detail = copy.deepcopy(result['fieldEvidence']['leadManagers'])
        detail['rawLines'][6] = detail['rawLines'][6].replace('FAST TRACK', 'WRONG NAME')
        with self.assertRaises(parser.ReviewLayoutError):
            parser.validate_evidence('leadManagers', result['leadManagers'], detail)
        with self.assertRaises(parser.ReviewLayoutError):
            parser.validate_evidence('leadManagers', ['Wrong Capital Limited'], result['fieldEvidence']['leadManagers'])

    def test_page_scope_and_engine_layout_are_explicit(self):
        for page in (None, 0, -1, True, '1'):
            with self.assertRaises(parser.ReviewLayoutError):
                parser.extract_intermediary_columns(CASES[0]['sourceText'], page=page)
        self.assert_rejected(CASES[0]['sourceText'] + '\f' + CASES[1]['sourceText'])
        self.assert_rejected(CASES[0]['sourceText'].replace('    ', '\t'))


if __name__ == '__main__':
    unittest.main()
