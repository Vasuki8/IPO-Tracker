import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from publish_transaction import FIELD_GROUPS, merge_payload


class PublicationPolicyTimestampTests(unittest.TestCase):
    @staticmethod
    def record(fresh=60, source='baseline', checked_at='2026-09-16T10:00:00Z'):
        composition = {
            'freshShares': fresh * 100000,
            'ofsShares': 4000000,
            'freshIssueCr': fresh,
            'ofsCr': 40,
            'totalIssueSizeCr': fresh + 40,
            'valuationPriceUsed': 100,
        }
        values = {
            'issueComposition': composition,
            'freshIssueCr': fresh,
            'ofsCr': 40,
            'issueSizeCr': fresh + 40,
        }
        url = f'https://example.test/{source}-prospectus.pdf'
        return {
            'id': 'issuer',
            'company': 'Issuer Limited',
            'status': 'closed',
            **values,
            'staticFieldProvenance': {
                field: {'documentType': 'PROSPECTUS', 'sourceUrl': url,
                        'sha256': source, 'value': copy.deepcopy(value)}
                for field, value in values.items()
            },
            'documentFieldProvenance': {
                'sourceUrl': url, 'sha256': source,
                'evidence': {'issueComposition': copy.deepcopy(composition)},
            },
            'offerDocumentExtraction': {
                'documentUrl': url, 'sha256': source, 'canonicalFields': sorted(values),
            },
            'staticSourcePolicy': {
                'policy': 'final-prospectus-only', 'status': 'verified',
                'documentUrl': url, 'checkedAt': checked_at,
                'verifiedFields': sorted(values), 'pendingRevalidationFields': [],
            },
        }

    def merge(self, before, proposed, current):
        payloads = [{'ipos': [row]} for row in (before, proposed, current)]
        originals = copy.deepcopy(payloads)
        merged, conflicts = merge_payload(*payloads)
        self.assertEqual(payloads, originals, 'Publication must not mutate its inputs')
        return merged['ipos'][0], conflicts

    def assert_document_group_equal(self, actual, expected):
        for field in FIELD_GROUPS['documentFields']:
            self.assertEqual(field in actual, field in expected, field)
            if field in expected:
                self.assertEqual(actual[field], expected[field], field)

    def test_current_clock_does_not_block_proposed_repair_or_independent_status(self):
        before = self.record()
        proposed = self.record(fresh=80, source='repair', checked_at='2026-09-16T11:00:00Z')
        current = copy.deepcopy(before)
        current['staticSourcePolicy']['checkedAt'] = '2026-09-16T12:00:00Z'
        current['status'] = 'listed'

        record, conflicts = self.merge(before, proposed, current)

        self.assertEqual(conflicts, [])
        self.assert_document_group_equal(record, proposed)
        self.assertEqual(record['issueSizeCr'], 120)
        self.assertEqual(record['staticFieldProvenance']['issueComposition']['sha256'], 'repair')
        self.assertEqual(record['staticSourcePolicy']['checkedAt'], '2026-09-16T11:00:00Z')
        self.assertEqual(record['status'], 'listed')

    def test_proposed_clock_keeps_complete_current_repair(self):
        before = self.record()
        proposed = copy.deepcopy(before)
        proposed['staticSourcePolicy']['checkedAt'] = '2026-09-16T12:00:00Z'
        current = self.record(fresh=80, source='accepted', checked_at='2026-09-16T11:00:00Z')

        record, conflicts = self.merge(before, proposed, current)

        self.assertEqual(conflicts, [])
        self.assert_document_group_equal(record, current)
        self.assertEqual(record['staticFieldProvenance']['issueComposition']['sha256'], 'accepted')

    def test_identical_repairs_with_different_clocks_keep_current_metadata(self):
        before = self.record()
        proposed = self.record(fresh=80, source='repair', checked_at='2026-09-16T11:00:00Z')
        current = copy.deepcopy(proposed)
        current['staticSourcePolicy']['checkedAt'] = '2026-09-16T12:00:00Z'

        record, conflicts = self.merge(before, proposed, current)

        self.assertEqual(conflicts, [])
        self.assert_document_group_equal(record, current)
        self.assertEqual(record['staticSourcePolicy']['checkedAt'], '2026-09-16T12:00:00Z')

    def test_competing_policy_change_retains_complete_proposed_repair_for_review(self):
        before = self.record()
        proposed = self.record(fresh=80, source='repair', checked_at='2026-09-16T11:00:00Z')
        current = copy.deepcopy(before)
        current['staticSourcePolicy'].update(
            checkedAt='2026-09-16T12:00:00Z', status='pending-revalidation',
            pendingRevalidationFields=['issueComposition'],
        )

        record, conflicts = self.merge(before, proposed, current)

        self.assert_document_group_equal(record, current)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['path'], ['ipos', 'issuer', 'documentFields'])
        self.assertEqual(conflicts[0]['status'], 'pending_conflict_review')
        self.assert_document_group_equal(conflicts[0]['proposed'], proposed)
        self.assert_document_group_equal(conflicts[0]['base'], before)

    def test_competing_source_proofs_still_conflict_when_values_match(self):
        before = self.record()
        proposed = self.record(source='proposed', checked_at='2026-09-16T11:00:00Z')
        current = self.record(source='accepted', checked_at='2026-09-16T12:00:00Z')

        record, conflicts = self.merge(before, proposed, current)

        self.assert_document_group_equal(record, current)
        self.assertEqual(len(conflicts), 1)
        self.assert_document_group_equal(conflicts[0]['proposed'], proposed)

    def test_competing_amounts_still_conflict_with_matching_source_and_policy(self):
        before = self.record()
        proposed = self.record(fresh=80, checked_at='2026-09-16T11:00:00Z')
        current = self.record(fresh=90, checked_at='2026-09-16T12:00:00Z')

        record, conflicts = self.merge(before, proposed, current)

        self.assert_document_group_equal(record, current)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['proposed']['issueSizeCr'], 120)
        self.assertEqual(record['issueSizeCr'], 130)

    def test_quarantine_clock_remains_part_of_document_evidence(self):
        before = self.record()
        before['issueCompositionReview'] = {'status': 'resolved', 'checkedAt': 'original-review'}
        proposed = copy.deepcopy(before)
        proposed['staticSourcePolicy']['checkedAt'] = '2026-09-16T11:00:00Z'
        proposed['issueCompositionReview']['checkedAt'] = 'proposed-review'
        current = copy.deepcopy(before)
        current['staticSourcePolicy']['checkedAt'] = '2026-09-16T12:00:00Z'
        current['issueCompositionReview']['checkedAt'] = 'accepted-review'

        record, conflicts = self.merge(before, proposed, current)

        self.assert_document_group_equal(record, current)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['proposed']['issueCompositionReview']['checkedAt'], 'proposed-review')

    def test_same_named_clock_outside_document_group_still_conflicts(self):
        before = self.record()
        before['audit'] = {'staticSourcePolicy': {'checkedAt': 'original-audit'}}
        proposed = copy.deepcopy(before)
        proposed['audit']['staticSourcePolicy']['checkedAt'] = 'proposed-audit'
        current = copy.deepcopy(before)
        current['audit']['staticSourcePolicy']['checkedAt'] = 'accepted-audit'

        record, conflicts = self.merge(before, proposed, current)

        self.assertEqual(record['audit'], current['audit'])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['path'], ['ipos', 'issuer', 'audit', 'staticSourcePolicy', 'checkedAt'])
        self.assertEqual(conflicts[0]['proposed'], 'proposed-audit')


if __name__ == '__main__':
    unittest.main()
