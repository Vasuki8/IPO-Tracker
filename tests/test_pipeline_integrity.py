import copy
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from publish_transaction import merge_payload
from phase_status import status
import build_missing_queue as queue


class PipelineIntegrityTests(unittest.TestCase):
    def test_concurrent_independent_changes_both_survive(self):
        base = {'meta': {}, 'ipos': [{'id': 'a', 'lotSize': None, 'registrar': None}]}
        proposed, current = copy.deepcopy(base), copy.deepcopy(base)
        proposed['ipos'][0]['lotSize'] = 100
        current['ipos'][0]['registrar'] = 'Official Registrar Limited'
        merged, conflicts = merge_payload(base, proposed, current)
        self.assertEqual(merged['ipos'][0]['lotSize'], 100)
        self.assertEqual(merged['ipos'][0]['registrar'], 'Official Registrar Limited')
        self.assertEqual(conflicts, [])

    def test_competing_value_is_retained_for_review_not_overwritten(self):
        base = {'ipos': [{'id': 'a', 'lotSize': None}]}
        proposed = {'ipos': [{'id': 'a', 'lotSize': 100}]}
        current = {'ipos': [{'id': 'a', 'lotSize': 200}]}
        result, conflicts = merge_payload(base, proposed, current)
        self.assertEqual(result['ipos'][0]['lotSize'], 200)
        self.assertEqual(conflicts[0]['proposed'], 100)
        self.assertEqual(conflicts[0]['status'], 'pending_conflict_review')

    def test_append_only_subscription_history_preserves_both_updates(self):
        base = {'ipos': [{'id': 'a', 'subscriptionHistory': [{'total': 1}]}]}
        proposed, current = copy.deepcopy(base), copy.deepcopy(base)
        proposed['ipos'][0]['subscriptionHistory'].append({'total': 2})
        current['ipos'][0]['subscriptionHistory'].append({'total': 3})
        result, conflicts = merge_payload(base, proposed, current)
        self.assertEqual(len(result['ipos'][0]['subscriptionHistory']), 3)
        self.assertFalse(conflicts)

    def test_deletion_does_not_delete_concurrent_changes(self):
        base = {'ipos': [{'id': 'a', 'lotSize': None}]}
        result, conflicts = merge_payload(base, {'ipos': []}, {'ipos': [{'id': 'a', 'lotSize': 200}]})
        self.assertEqual(result['ipos'][0]['lotSize'], 200)
        self.assertTrue(conflicts)

    def test_full_queue_is_persisted_beyond_300(self):
        with tempfile.TemporaryDirectory() as directory:
            data, output = Path(directory) / 'ipos.json', Path(directory) / 'queue.json'
            data.write_text(json.dumps({'ipos': [{'id': str(i), 'company': str(i), 'symbol': str(i), 'openDate': '2025-01-01'} for i in range(420)]}))
            with patch.object(queue, 'DATA_FILE', data), patch.object(queue, 'OUTPUT_FILE', output):
                queue.main()
            saved = json.loads(output.read_text())
            self.assertEqual(saved['queueCount'], 420)
            self.assertEqual(len(saved['queue']), 420)
            self.assertTrue(saved['queueIsComplete'])

    def test_document_values_and_evidence_merge_as_one_group(self):
        base = {'ipos': [{'id': 'a', 'financials': {'periods': []}, 'registrar': 'Before Limited'}]}
        proposed, current = copy.deepcopy(base), copy.deepcopy(base)
        proposed['ipos'][0].update(financials={'periods': [{'period': 'FY2025', 'patCr': 8}]}, documentFieldProvenance={'sha256': 'new'})
        current['ipos'][0]['registrar'] = 'Accepted Registrar Limited'
        merged, conflicts = merge_payload(base, proposed, current)
        self.assertEqual(merged['ipos'][0]['financials'], base['ipos'][0]['financials'])
        self.assertNotIn('documentFieldProvenance', merged['ipos'][0])
        self.assertEqual(conflicts[0]['path'][-1], 'documentFields')

    def test_reviewed_migration_preserves_concurrent_changes(self):
        from apply_corrections import apply, fingerprint
        payload = {'ipos': [{'id': 'a', 'lotSize': 50}]}
        registry = {'changes': [{'id': 'a', 'field': 'lotSize', 'beforeHash': fingerprint(None), 'after': 100}]}
        applied, conflicts = apply(payload, registry)
        self.assertEqual(applied, 0)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(payload['ipos'][0]['lotSize'], 50)

    def test_distinct_issue_events_cannot_collapse_during_publication(self):
        from record_integrity import repair
        payload = {'ipos': [{'id': 'rsl', 'company': 'Rajputana Stainless Limited-Special Withdrawal Option', 'openDate': '2026-03-12'}, {'id': 'rsl', 'company': 'Rajputana Stainless Limited', 'openDate': '2026-03-09'}]}
        repair(payload)
        self.assertEqual(len({row['id'] for row in payload['ipos']}), 2)
        once = copy.deepcopy(payload['ipos'])
        repair(payload)
        self.assertEqual(payload['ipos'], once)
        merged, conflicts = merge_payload(payload, payload, payload)
        self.assertEqual(len(merged['ipos']), 2)

    def test_impossible_listing_date_is_retained_outside_accepted_field(self):
        from record_integrity import repair
        payload = {'ipos': [{'id': 'x', 'company': 'Example FPO', 'openDate': '2024-01-01', 'listingDate': '2023-01-01'}]}
        repair(payload)
        row = payload['ipos'][0]
        self.assertIsNone(row['listingDate'])
        self.assertEqual(row['unverifiedObservations']['listingDate']['value'], '2023-01-01')
        self.assertIn('listingDate', row['dataReview'])

    def test_missing_zero_does_not_close_p4_with_unverified_values(self):
        output = status({'queue': [], 'resolvedUnavailableRecordCount': 0}, {'errorCount': 0, 'reviewCount': 1})
        self.assertEqual(output['p4']['status'], 'incomplete')
        self.assertEqual(output['p5']['status'], 'waiting_for_p4')


if __name__ == '__main__':
    unittest.main()
