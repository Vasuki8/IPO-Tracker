"""Retained real publication regression; a parser success is not source approval."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from public_quality import project_record
from build_company_pages import public_profile_record, public_summary_record
from source_review_holds import active_hold_reviews, display_holds, display_hold_matches
from source_review_queue import review_task, compact_review_items, expand_review_items


class VinodShareholdingHoldTests(unittest.TestCase):
    def setUp(self):
        self.row = json.loads((ROOT / 'tests/vinod_shareholding_retained.json').read_text(encoding='utf-8'))['ipos'][0]
        self.hold = next(h for h in display_holds() if h['id'] == 'vinod')

    def test_public_projection_withholds_derived_percentage_preserving_other_reviewed_fields_and_history(self):
        before = copy.deepcopy(self.row)
        self.assertTrue(display_hold_matches(self.row, 'shareholding', self.hold))
        self.assertEqual(self.row['shareholding']['promoterPreIssuePct'], 93.11)
        for projection in (project_record, public_profile_record, public_summary_record):
            with self.subTest(projection=projection.__name__):
                output = projection(self.row)
                self.assertIsNone(output.get('shareholding'))
                if projection is not public_summary_record:  # Directory has no shareholding column.
                    decision = output['publicQuality']['fields']['shareholding']
                    self.assertEqual((decision['state'], decision['reason']), ('under_review', 'pending_source_repair'))
        profile = public_profile_record(self.row)
        self.assertEqual(profile['financials']['periods'], self.row['financials']['periods'])
        self.assertEqual(profile['objectsOfIssue'], self.row['objectsOfIssue'])
        self.assertEqual(self.row, before)

    def test_clock_refresh_cannot_resolve_hold_but_a_different_issuer_or_source_does_not_borrow_it(self):
        proof = self.row['staticFieldProvenance']['shareholding']
        proof['checkedAt'] = '2026-09-20T01:00:00Z'
        proof['parserVersion'] = 32
        self.assertTrue(display_hold_matches(self.row, 'shareholding', self.hold))
        for field, value in (('company', 'Another Limited'), ('openDate', '2026-10-01')):
            changed = copy.deepcopy(self.row)
            changed[field] = value
            self.assertFalse(display_hold_matches(changed, 'shareholding', self.hold))
        proof['sha256'] = 'f' * 64
        self.assertFalse(display_hold_matches(self.row, 'shareholding', self.hold))

    def test_hold_is_an_actionable_review_without_inventing_a_numeric_repair(self):
        issues = active_hold_reviews(self.row, [self.hold])
        self.assertEqual(len(issues), 1)
        issue = issues[0]
        self.assertEqual((issue['reviewType'], issue['field']), ('source_display_hold', 'shareholding'))
        self.assertEqual(issue['displayHold']['source']['parserVersion'], 31)
        self.assertIn('93.10%', issue['reason'])
        task = review_task(self.row, issue)
        self.assertEqual(task['route'], 'manual-source-review')
        self.assertIsNone(task['repairGap'])
        definitions = []
        queued = {'sourceReviewItems': [task]}
        compact = compact_review_items(queued, definitions)
        self.assertEqual(expand_review_items({'sourceReviewItems': compact}, definitions), [task])


if __name__ == '__main__':
    unittest.main()
