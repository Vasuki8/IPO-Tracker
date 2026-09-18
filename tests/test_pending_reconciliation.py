"""Conservative triage must never become a publication or an implicit resolution."""
import contextlib
import copy
from datetime import date
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('pending_report', ROOT / 'tools/reconcile_pending_updates.py')
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)
TODAY = date(2026, 9, 18)


def proposal(base, proposed, identifier='example', path=None):
    item = {'path': path or ['ipos', identifier, 'documentFields'], 'baseExists': True,
            'base': copy.deepcopy(base), 'proposedExists': True, 'proposed': copy.deepcopy(proposed),
            'status': 'pending_conflict_review'}
    item['fingerprint'] = report.digest(json.dumps(item, sort_keys=True).encode())
    item['runId'] = '100'
    return item


class PendingReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.row = {'id': 'example', 'company': 'Example Limited', 'symbol': 'EXAMPLE',
                    'openDate': '2025-11-11', 'closeDate': '2025-11-13', 'status': 'listed',
                    'registrar': 'Example Registry Limited'}
        self.row['staticFieldProvenance'] = {'registrar': {
            'field': 'registrar', 'value': self.row['registrar'], 'documentType': 'PROSPECTUS',
            'sourceUrl': 'https://www.sebi.gov.in/files/final.pdf', 'documentDate': '2025-11-14',
            'sha256': 'a' * 64, 'issueOpenDate': self.row['openDate'], 'parserVersion': 32,
            'checkedAt': '2026-09-18T00:37:05Z',
            'evidence': {'page': 12, 'row': 'Registrar to the issue: Example Registry Limited'}}}
        self.group = {k: copy.deepcopy(v) for k, v in self.row.items() if k in report.DOCUMENT_FIELDS}
        self.base = {'registrar': 'Previous Registry Limited'}

    def build(self, items, rows=None, holds=None):
        canonical = {'ipos': rows if rows is not None else [self.row]}
        pending = {'updates': items}
        originals = copy.deepcopy((canonical, pending, holds))
        actual = report.build_report(canonical, pending, as_of=TODAY, holds=holds or [])
        self.assertEqual((canonical, pending, holds), originals)
        self.assertEqual(actual['resolutionsApplied'], 0)
        self.assertEqual(len(actual['entries']), len(items))
        self.assertTrue(all(not e['resolutionChanged'] for e in actual['entries']))
        return actual

    def test_exact_current_group_is_separate_from_source_acceptance(self):
        result = self.build([proposal(self.base, self.group)])['entries'][0]
        self.assertEqual(result['comparisonState'], 'already_applied_exact')
        self.assertEqual(result['currentEvidence']['fieldStates']['registrar'], 'final_verified')
        self.assertEqual(result['status'], 'pending_conflict_review')
        self.assertIn('before recording', result['nextAction'])

    def test_matching_unverified_or_held_data_never_closes_a_review(self):
        for defect in ('no_proof', 'rhp', 'document_hold'):
            with self.subTest(defect=defect):
                row = copy.deepcopy(self.row)
                holds = []
                if defect == 'no_proof':
                    row.pop('staticFieldProvenance')
                elif defect == 'rhp':
                    row['staticFieldProvenance']['registrar']['documentType'] = 'RHP'
                else:
                    holds = [{'id': row['id'], 'identity': {k: row[k] for k in ('id', 'company', 'symbol', 'openDate')},
                              'scope': 'document', 'fields': {'registrar': {'sha256': 'a' * 64}}}]
                group = {k: v for k, v in row.items() if k in report.DOCUMENT_FIELDS}
                e = self.build([proposal(self.base, group)], rows=[row], holds=holds)['entries'][0]
                self.assertEqual(e['comparisonState'], 'already_applied_exact')
                self.assertTrue(e['currentEvidence']['requiresSourceReview'])
                self.assertEqual(e['currentEvidence']['fieldStates']['registrar'], 'under_review')

    def test_same_amount_or_name_with_different_proof_remains_conflicting(self):
        for key, value in [('sha256', 'b' * 64), ('checkedAt', '2099-01-01T00:00:00Z'),
                           ('issueOpenDate', '2024-11-11')]:
            with self.subTest(field=key):
                proposed = copy.deepcopy(self.group)
                proposed['staticFieldProvenance']['registrar'][key] = value
                e = self.build([proposal(self.base, proposed)])['entries'][0]
                self.assertEqual(e['comparisonState'], 'still_conflicting')
                self.assertEqual(e['differingValueFields'], [])
                self.assertIn('staticFieldProvenance', e['differingEvidenceOrReviewFields'])

    def test_only_enforcement_clock_is_separately_identified(self):
        self.row['staticSourcePolicy'] = {'checkedAt': 'old', 'verifiedFields': ['registrar']}
        proposed = {**self.group, 'staticSourcePolicy': {'checkedAt': 'new', 'verifiedFields': ['registrar']}}
        e = self.build([proposal(self.base, proposed)])['entries'][0]
        self.assertEqual(e['comparisonState'], 'policy_clock_only')
        proposed['staticSourcePolicy']['verifiedFields'] = []
        self.assertEqual(self.build([proposal(self.base, proposed)])['entries'][0]['comparisonState'], 'still_conflicting')

    def test_review_and_source_clocks_are_not_ignored(self):
        self.row['objectsOfIssueReview'] = {'status': 'quarantined', 'checkedAt': 'old'}
        proposed = {**self.group, 'objectsOfIssueReview': {'status': 'quarantined', 'checkedAt': 'new'}}
        self.assertEqual(self.build([proposal(self.base, proposed)])['entries'][0]['comparisonState'], 'still_conflicting')

    def test_unchanged_base_requires_revalidation_not_newest_writer_wins(self):
        newer = {**copy.deepcopy(self.group), 'registrar': 'Other Registry Limited'}
        item = proposal(self.group, newer)
        item['runId'] = '99999999999'
        e = self.build([item])['entries'][0]
        self.assertEqual(e['comparisonState'], 'base_unchanged')
        self.assertTrue(e['proposedEvidence']['requiresSourceReview'])
        self.assertIn('Revalidate', e['nextAction'])

    def test_partial_legacy_group_cannot_match_by_common_values(self):
        partial = {'registrar': self.row['registrar']}
        e = self.build([proposal(self.base, partial)])['entries'][0]
        self.assertEqual(e['comparisonState'], 'still_conflicting')
        self.assertIn('staticFieldProvenance', e['currentOnlyFields'])
        unknown = {**partial, 'oldUndocumentedField': 12}
        e = self.build([proposal(self.base, unknown)])['entries'][0]
        self.assertEqual(e['comparisonState'], 'legacy_group_scope')

    def test_missing_null_zero_and_false_remain_distinct(self):
        for left, right in [(None, 0), (0, False), ({}, {'ofsCr': None}), ([], None)]:
            with self.subTest(left=left, right=right):
                self.assertFalse(report.equal(left, right))
        self.row['freshIssueCr'] = 0
        for value in (False, None):
            e = self.build([proposal(self.base, {**self.group, 'freshIssueCr': value})])['entries'][0]
            self.assertEqual(e['comparisonState'], 'still_conflicting')
            self.assertIn('freshIssueCr', e['differingValueFields'])

    def test_missing_or_duplicate_issuer_is_not_guessed(self):
        for rows, state in [([], 'missing_record'), ([self.row, copy.deepcopy(self.row)], 'ambiguous_record')]:
            e = self.build([proposal(self.base, self.group)], rows=rows)['entries'][0]
            self.assertEqual(e['comparisonState'], state)

    def test_duplicate_occurrences_and_out_of_scope_items_are_all_retained(self):
        doc = proposal(self.base, self.group)
        other = proposal({}, {'listing': {'gainPct': 0}}, path=['ipos', 'example', 'priceSnapshot'])
        result = self.build([doc, copy.deepcopy(doc), other])
        self.assertEqual([e['inputIndex'] for e in result['entries']], [0, 1, 2])
        self.assertEqual(result['summary']['duplicateFingerprintOccurrences'], 1)
        self.assertEqual(result['entries'][2]['comparisonState'], 'not_assessed')
        self.assertIn('official listing evidence', result['entries'][2]['nextAction'])

    def test_bad_envelopes_are_visible_not_dropped(self):
        malformed = [None, [], {}, {**proposal(self.base, self.group), 'baseExists': 1},
                     {**proposal(self.base, self.group), 'fingerprint': '0' * 64},
                     {**proposal(self.base, self.group), 'path': ['ipos', 'example']}]
        result = self.build(malformed)
        self.assertEqual(result['summary']['byComparisonState'], {'malformed_proposal': len(malformed)})
        with self.assertRaises(ValueError):
            report.build_report({'ipos': []}, {}, as_of=TODAY, holds=[])

    def test_unsupported_evidence_shape_is_explicit_failure_not_verification(self):
        broken = {**self.group, 'staticFieldProvenance': ['invalid']}
        e = self.build([proposal(self.base, broken)])['entries'][0]
        self.assertEqual(e['proposedEvidence']['status'], 'assessment_failed')
        self.assertTrue(e['proposedEvidence']['requiresSourceReview'])

    def test_real_backlog_read_is_deterministic_network_free_and_preserves_bytes(self):
        paths = [ROOT / 'data' / name for name in ('ipos.json', 'pending_updates.json', 'phase_status.json', 'missing_queue.json')]
        before = {p: p.read_bytes() for p in paths}
        with patch('requests.sessions.Session.request', side_effect=AssertionError('No source collection')):
            first = report.report_from_files(paths[0], paths[1])
            second = report.report_from_files(paths[0], paths[1])
        self.assertEqual(first, second)
        original = json.loads(before[paths[1]])['updates']
        self.assertEqual(len(first['entries']), len(original))
        for index, (item, entry) in enumerate(zip(original, first['entries'])):
            self.assertEqual(entry['inputIndex'], index)
            self.assertEqual(entry['fingerprint'], item['fingerprint'])
            self.assertEqual(entry['proposalSha256'], report.digest(report.encoded(item)))
        self.assertEqual(before, {p: p.read_bytes() for p in paths})

    def test_cli_checks_report_snapshot_and_does_not_rewrite_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            data, pending, output = [Path(d) / n for n in ('data.json', 'pending.json', 'report.json')]
            canonical = {'meta': {'generatedAt': '2026-09-17T20:00:00Z'}, 'ipos': [self.row]}
            data.write_text(json.dumps(canonical))
            pending.write_text(json.dumps({'updates': [proposal(self.base, self.group)]}))
            args = ['--data', str(data), '--pending', str(pending)]
            before = (data.read_bytes(), pending.read_bytes())
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                self.assertEqual(report.main(args), 0)
            actual = json.loads(stream.getvalue())
            self.assertEqual(actual['asOf'], '2026-09-18')  # Snapshot in India, not the wall clock.
            output.write_text(stream.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(report.main(args + ['--check-report', str(output)]), 0)
            self.assertEqual(before, (data.read_bytes(), pending.read_bytes()))
            for defect in ('input', 'report'):
                with self.subTest(defect=defect):
                    data.write_bytes(before[0])
                    if defect == 'input':
                        data.write_bytes(before[0] + b' ')
                    else:
                        actual['codePolicySha256'] = '0' * 64
                        output.write_text(json.dumps(actual))
                    with contextlib.redirect_stderr(io.StringIO()):
                        self.assertEqual(report.main(args + ['--check-report', str(output)]), 1)

    def test_duplicate_keys_nonfinite_numbers_and_missing_files_fail_closed(self):
        for raw in ('{"updates":[],"updates":[]}', '{"value":NaN}', '{"value":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                report.read_json(raw)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(report.main(['--pending', '/does-not-exist/pending.json']), 1)

    def test_reporting_runs_before_correction_rehearsal_without_another_writer(self):
        workflow = (ROOT / '.github/workflows/validate.yml').read_text()
        self.assertLess(workflow.index('tools/reconcile_pending_updates.py >'),
                        workflow.index('python scripts/apply_corrections.py'))
        self.assertIn('--check-report artifacts/proposal-reconciliation/report.json', workflow)
        self.assertIn('git diff --exit-code -- data/ipos.json data/pending_updates.json', workflow)
        self.assertNotIn('contents: write', workflow)
        self.assertNotIn('git push', workflow)
        refresh = (ROOT / '.github/workflows/refresh.yml').read_text()
        self.assertNotIn('tools/**', refresh)
        self.assertNotIn('reconcile_pending_updates.py', refresh)


if __name__ == '__main__':
    unittest.main()
