"""Real source-column failures must not appear as verified intermediaries."""
import copy
from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from build_company_pages import public_profile_record, public_summary_record
from public_quality import display_holds, project_record, value_digest
from source_review_queue import review_task
from validate_data import validate_record

TODAY = date(2026, 9, 18)
FIELDS = {'snehaa': ('leadManagers',), 'sacheerome': ('leadManagers', 'registrar')}


class IntermediarySourceHoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        retained = json.loads((ROOT / 'tests/public_intermediary_reviews_retained.json').read_text())
        cls.rows = {row['id']: row for row in retained['ipos']}
        cls.holds = {hold['id']: hold for hold in display_holds() if hold['id'] in FIELDS}

    def test_role_column_failures_are_withheld_without_mutating_retained_evidence(self):
        self.assertEqual(set(self.holds), set(FIELDS))
        for identifier, fields in FIELDS.items():
            row = copy.deepcopy(self.rows[identifier])
            before = copy.deepcopy(row)
            projected = project_record(row, today=TODAY)
            profile = public_profile_record(row)
            summary = public_summary_record(row)
            for field in fields:
                with self.subTest(identifier=identifier, field=field):
                    proof = row['staticFieldProvenance'][field]
                    binding = self.holds[identifier]['fields'][field]
                    self.assertEqual(self.holds[identifier]['scope'], 'value')
                    self.assertEqual(binding['sha256'], proof['sha256'])
                    self.assertEqual(binding['valueDigest'], value_digest(row[field]))
                    self.assertEqual(proof['value'], row[field])
                    self.assertIsNone(projected[field])
                    self.assertNotIn(field, profile)
                    self.assertNotIn(field, summary)
                    decision = profile['publicQuality']['fields'][field]
                    self.assertEqual(decision['state'], 'under_review')
                    self.assertEqual(decision['reason'], 'pending_source_repair')
                    source = profile['publicQuality']['sources'][decision['source']]
                    self.assertEqual(source['sha256'], proof['sha256'])
                    self.assertEqual(source['sourceUrl'], proof['sourceUrl'])
            self.assertEqual(row, before)
            self.assertEqual(projected['dataCorrections'], before['dataCorrections'])
            self.assertEqual(projected['staticFieldProvenance'], before['staticFieldProvenance'])
            self.assertEqual(profile['lotSize'], row['lotSize'])
        snehaa = project_record(self.rows['snehaa'], today=TODAY)
        self.assertIsNone(snehaa['registrar'])
        self.assertEqual(snehaa['publicQuality']['fields']['registrar']['state'], 'awaiting_disclosure')

    def test_recollection_or_mirror_does_not_release_the_same_unsupported_value(self):
        for identifier, fields in FIELDS.items():
            row = copy.deepcopy(self.rows[identifier])
            for field in fields:
                row['staticFieldProvenance'][field].update({
                    'sourceUrl': 'https://archives.nseindia.com/reviewed-source-mirror.pdf',
                    'checkedAt': '2026-09-19T01:00:00+00:00',
                    'parserVersion': 99,
                })
            projected = project_record(row, today=TODAY)
            for field in fields:
                self.assertIsNone(projected[field])
                self.assertEqual(projected['publicQuality']['fields'][field]['state'], 'under_review')

    def test_each_unsupported_role_remains_actionable_without_automatic_retry(self):
        for identifier, fields in FIELDS.items():
            row = self.rows[identifier]
            issues = [issue for issue in validate_record(row)
                      if issue.get('reviewType') == 'source_display_hold']
            self.assertEqual({issue['field'] for issue in issues}, set(fields))
            self.assertEqual(len(issues), len(fields))
            for issue in issues:
                self.assertEqual(issue['severity'], 'review')
                task = review_task(row, issue)
                self.assertEqual(task['route'], 'manual-source-review')
                self.assertIsNone(task['repairGap'])
                self.assertEqual(task['reason'], issue['reason'])
                self.assertIn('displayHold', task)


if __name__ == '__main__':
    unittest.main()
