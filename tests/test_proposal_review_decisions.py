"""A historical review can guide an operator, but never clear or apply a proposal."""
import copy
from datetime import date
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('decision_report', ROOT / 'tools/reconcile_pending_updates.py')
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


class ProposalReviewDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        identity = {'id': 'example', 'company': 'Example Limited', 'symbol': 'EXAMPLE', 'openDate': '2025-11-11'}
        cls.accepted = {**identity, 'status': 'listed', 'closeDate': '2025-11-13',
                        'registrar': 'Example Registry Limited', 'staticSourcePolicy': {'checkedAt': 'original'}}
        cls.accepted['staticFieldProvenance'] = {'registrar': {
            'field': 'registrar', 'value': cls.accepted['registrar'], 'documentType': 'PROSPECTUS',
            'sourceUrl': 'https://www.sebi.gov.in/files/final.pdf', 'documentDate': '2025-11-14',
            'sha256': 'a' * 64, 'issueOpenDate': identity['openDate'], 'parserVersion': 32,
            'checkedAt': '2026-09-18T00:37:05Z', 'evidence': {'page': 12, 'row': 'Registrar: Example Registry Limited'}}}
        cls.original = {'path': ['ipos', identity['id'], 'documentFields'], 'baseExists': True,
                        'base': {'registrar': 'Previous Registry Limited'}, 'proposedExists': True,
                        'proposed': {'registrar': None}, 'status': 'pending_conflict_review'}
        cls.original['fingerprint'] = report.digest(json.dumps(cls.original, sort_keys=True).encode())
        cls.original['runId'] = '123'
        cls.holds, cls.holds_hash = [], report.digest(b'[]')
        group = {k: v for k, v in cls.accepted.items() if k in report.DOCUMENT_FIELDS}
        cls.note = b'Reviewed fixture: do not replay the old source withdrawal.\n'
        cls.decisions = [{'reviewId': 'example-review', 'reviewedAt': '2026-09-18T04:49:59Z',
                          'decision': 'do_not_apply_as_proposed', 'fingerprint': cls.original['fingerprint'],
                          'proposalSha256': report.digest(report.encoded(cls.original)), 'runId': '123',
                          'path': cls.original['path'], 'identity': identity, 'acceptedCommit': 'a' * 40,
                          'acceptedGroupSha256': report.digest(report.encoded(report.without_policy_clock(group))),
                          'displayHoldsSha256': cls.holds_hash, 'reviewedFields': ['registrar'],
                          'evidenceFile': 'review.md', 'evidenceSha256': report.digest(cls.note),
                          'reason': 'The old withdrawal is not the current supported evidence.',
                          'nextAction': 'Do not apply the old proposal as proposed; retain the review.'}]

    def build(self, row=None, items=None, decisions=None, holds_hash=None):
        canonical = {'ipos': [copy.deepcopy(self.accepted if row is None else row)]}
        pending = {'updates': copy.deepcopy([self.original] if items is None else items)}
        decisions = copy.deepcopy(self.decisions if decisions is None else decisions)
        before = copy.deepcopy((canonical, pending, decisions))
        result = report.build_report(canonical, pending, as_of=date(2026, 9, 18), holds=self.holds)
        original_entries = copy.deepcopy(result['entries'])
        original_summary = copy.deepcopy(result['summary'])
        report.annotate_decisions(result, canonical, decisions,
                                  holds_sha256=self.holds_hash if holds_hash is None else holds_hash)
        self.assertEqual(before, (canonical, pending, decisions))
        self.assertEqual(result['summary'], original_summary)
        self.assertEqual(result['resolutionsApplied'], 0)
        self.assertEqual(result['reviewDecisionAudit']['resolutionsApplied'], 0)
        for original, annotated in zip(original_entries, result['entries']):
            self.assertEqual(original, {k: v for k, v in annotated.items() if k != 'reviewDecisions'})
        return result

    def test_exact_review_guides_operator_without_reclassifying_or_resolving(self):
        result = self.build()
        item = result['entries'][0]
        self.assertEqual(item['comparisonState'], 'still_conflicting')
        self.assertEqual(item['status'], 'pending_conflict_review')
        self.assertFalse(item['resolutionChanged'])
        advice = item['reviewDecisions'][0]
        self.assertEqual(advice['bindingStatus'], 'applicable')
        self.assertEqual(advice['decision'], 'do_not_apply_as_proposed')
        self.assertIn('Do not apply', advice['nextAction'])
        self.assertIsNone(self.original['proposed']['registrar'])
        self.assertNotEqual(self.original['proposed']['registrar'], self.accepted['registrar'])

    def test_review_follows_exact_proposal_not_array_position_and_keeps_duplicates(self):
        unrelated = copy.deepcopy(self.original)
        unrelated['fingerprint'] = '0' * 64
        result = self.build(items=[unrelated, self.original, self.original])
        self.assertNotIn('reviewDecisions', result['entries'][0])
        self.assertEqual([e['inputIndex'] for e in result['reviewDecisionAudit']['events'][0]['occurrences']], [1, 2])
        self.assertEqual(len(result['entries']), 3)

    def test_same_fingerprint_cannot_authorize_changed_payload_or_run(self):
        for field, value in [('runId', 'future-run'), ('proposed', {}), ('path', ['ipos', 'other', 'documentFields'])]:
            with self.subTest(field=field):
                item = copy.deepcopy(self.original)
                item[field] = value
                decision = self.build(items=[item])['entries'][0]['reviewDecisions'][0]
                self.assertEqual(decision['bindingStatus'], 'proposal_mismatch')
                self.assertNotIn('reason', decision)

    def test_changed_issuer_or_offer_date_invalidates_advice(self):
        for field, value in [('company', 'Another Limited'), ('symbol', 'OTHER'), ('openDate', '2024-11-11')]:
            with self.subTest(field=field):
                row = copy.deepcopy(self.accepted)
                row[field] = value
                advice = self.build(row=row)['entries'][0]['reviewDecisions'][0]
                self.assertEqual(advice['bindingStatus'], 'identity_mismatch')

    def test_new_values_proofs_source_clocks_or_reviews_require_another_review(self):
        for defect in ('value', 'source_clock', 'pdf', 'review'):
            with self.subTest(defect=defect):
                row = copy.deepcopy(self.accepted)
                if defect == 'value':
                    row['registrar'] = 'Different Registry Limited'
                elif defect == 'source_clock':
                    row['staticFieldProvenance']['registrar']['checkedAt'] = '2026-09-19T00:00:00Z'
                elif defect == 'pdf':
                    row['staticFieldProvenance']['registrar']['sha256'] = 'b' * 64
                else:
                    row['staticSourcePolicy']['pendingRevalidationFields'] = ['registrar']
                advice = self.build(row=row)['entries'][0]['reviewDecisions'][0]
                self.assertEqual(advice['bindingStatus'], 'stale_evidence')
                self.assertNotIn('reason', advice)

    def test_hold_changes_invalidate_review_even_when_stored_group_is_unchanged(self):
        advice = self.build(holds_hash='b' * 64)['entries'][0]['reviewDecisions'][0]
        self.assertEqual(advice['bindingStatus'], 'stale_evidence')

    def test_changed_public_validation_cannot_inherit_applicable_advice(self):
        canonical = {'ipos': [copy.deepcopy(self.accepted)]}
        data = report.build_report(canonical, {'updates': [self.original]}, as_of=date(2026, 9, 18), holds=self.holds)
        data['entries'][0]['currentEvidence']['fieldStates']['registrar'] = 'under_review'
        report.annotate_decisions(data, canonical, self.decisions, holds_sha256=self.holds_hash)
        self.assertEqual(data['entries'][0]['reviewDecisions'][0]['bindingStatus'], 'stale_evidence')

    def test_independent_subscription_and_enforcement_clock_preserve_binding(self):
        row = copy.deepcopy(self.accepted)
        row['subscription'] = {'total': 0}
        row['staticSourcePolicy']['checkedAt'] = '2026-09-19T00:00:00Z'
        advice = self.build(row=row)['entries'][0]['reviewDecisions'][0]
        self.assertEqual(advice['bindingStatus'], 'applicable')

    def test_unmatched_and_multiple_review_events_are_never_discarded_or_time_selected(self):
        other = copy.deepcopy(self.decisions[0])
        other['reviewId'] = 'another-review'
        other['acceptedGroupSha256'] = '0' * 64
        events = self.build(decisions=[self.decisions[0], other])['reviewDecisionAudit']['events']
        self.assertEqual([e['bindingStatus'] for e in events], ['applicable', 'needs_revalidation'])
        unmatched = self.build(items=[])['reviewDecisionAudit']['events']
        self.assertEqual(len(unmatched), 1)
        self.assertEqual(unmatched[0]['bindingStatus'], 'unmatched')

    def test_ledger_schema_and_evidence_fail_closed(self):
        evidence = self.decisions[0]['evidenceFile']
        text = self.note
        for defect in ('accept', 'duplicate', 'path', 'missing_note', 'changed_note', 'hash', 'identity', 'time', 'version', 'commit'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                ledger = {'schemaVersion': 1, 'decisions': copy.deepcopy(self.decisions)}
                d = ledger['decisions'][0]
                (root / evidence).write_bytes(text)
                if defect == 'accept': d['decision'] = 'accepted'
                elif defect == 'duplicate': ledger['decisions'].append(copy.deepcopy(d))
                elif defect == 'path': d['evidenceFile'] = '../escaped.md'
                elif defect == 'missing_note': (root / evidence).unlink()
                elif defect == 'changed_note': (root / evidence).write_bytes(text + b'\n')
                elif defect == 'hash': d['proposalSha256'] = 'not-a-hash'
                elif defect == 'identity': d['identity'].pop('symbol')
                elif defect == 'time': d['reviewedAt'] = '2026-09-18'
                elif defect == 'version': ledger['schemaVersion'] = True
                else: d['acceptedCommit'] = 'main'
                path = root / 'ledger.json'
                path.write_text(json.dumps(ledger))
                with self.assertRaises((ValueError, OSError)):
                    report.load_decisions(path)

    def test_real_backlog_has_one_applicable_review_and_all_original_work(self):
        paths = [ROOT / 'data' / name for name in ('ipos.json', 'pending_updates.json', 'phase_status.json')]
        before = {p: p.read_bytes() for p in paths}
        with patch('requests.sessions.Session.request', side_effect=AssertionError('No network allowed')):
            result = report.report_from_files(paths[0], paths[1])
        self.assertEqual(result['summary']['retainedProposals'], len(json.loads(before[paths[1]])['updates']))
        decisions, inputs = report.load_decisions(ROOT / 'docs/reviews/pending-proposal-decisions.json')
        self.assertEqual(result['reviewDecisionAudit']['decisionsRecorded'], len(decisions))
        for event in result['reviewDecisionAudit']['events']:
            self.assertIn(event['bindingStatus'], {'applicable', 'needs_revalidation', 'unmatched'})
        self.assertEqual([e['reviewId'] for e in result['reviewDecisionAudit']['events']],
                         [d['reviewId'] for d in decisions])
        self.assertEqual(before, {p: p.read_bytes() for p in paths})
        self.assertEqual(result['reviewDecisionInputs'], inputs)


if __name__ == '__main__':
    unittest.main()
