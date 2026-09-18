"""Review-policy releases rebuild derived gates, never source or proposal data."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from publication_mode import push_mode


class ReviewPublicationTests(unittest.TestCase):
    def test_current_hold_integration_has_a_bounded_release(self):
        paths = ['scripts/source_review_holds.py', 'scripts/source_review_queue.py',
                 'scripts/validate_data.py', 'scripts/public_quality.py',
                 'scripts/publication_mode.py', '.github/workflows/refresh.yml',
                 '.github/workflows/frontend.yml', 'data/public_display_holds.json',
                 'data/phase_status.json', 'tests/test_active_display_hold_routing.py',
                 'tests/public_intermediary_reviews_retained.json', 'public-quality.js',
                 'docs/PROJECT_STATUS.md']
        self.assertEqual(push_mode(paths), 'review')

    def test_future_registry_changes_cannot_leave_queue_gates_stale(self):
        self.assertEqual(push_mode(['data/public_display_holds.json']), 'review')
        self.assertEqual(push_mode(['scripts/validate_data.py']), 'review')
        self.assertEqual(push_mode(['scripts/public_quality.py']), 'presentation')
        for output in ('data/phase_status.json', 'data/missing_queue.json', 'data/validation.json'):
            self.assertEqual(push_mode([output]), 'repair')
            self.assertEqual(push_mode(['data/public_display_holds.json', output]), 'review')

    def test_mixed_collector_or_canonical_changes_still_require_source_guard(self):
        for path in ('scripts/final_prospectus_parser.py', 'scripts/track_subscriptions.py',
                     'scripts/phase_status.py', 'scripts/build_missing_queue.py',
                     'scripts/publish_transaction.py', 'scripts/publication_source_policy.py',
                     'data/ipos.json', 'data/pending_updates.json', 'data/verified_corrections.json',
                     'uv.lock', 'pyproject.toml', 'scripts/../public_quality.py', None, 0):
            with self.subTest(path=path):
                self.assertEqual(push_mode(['data/public_display_holds.json', path]), 'repair')
        with self.assertRaises(RuntimeError):
            push_mode(['data/public_display_holds.json', 'data/reviewed_publication_request.json'])

    def test_review_reuses_serialized_writer_with_exact_protected_boundaries(self):
        text = (ROOT / '.github/workflows/refresh.yml').read_text()
        block = text.split('if [[ "$MODE" == "review" ]]; then', 1)[1].split('              else', 1)[0]
        for required in ('validate_data.py --strict', 'build_missing_queue.py', 'phase_status.py',
                         'build_company_pages.py', 'git diff --exit-code -- data/ipos.json data/pending_updates.json',
                         'node --test tests/public_quality.test.cjs'):
            self.assertIn(required, block)
        self.assertIn('git add data/validation.json data/missing_queue.json data/phase_status.json data/ipos-summary.json ipo/', block)
        for forbidden in ('run_pipeline.py', 'publish_transaction.py', 'apply_corrections.py',
                          'enforce_final_prospectus_policy.py', 'build_performance_summary.py', '/tmp/ipo-bundle'):
            self.assertNotIn(forbidden, block)
        self.assertIn("steps.collection-mode.outputs.value != 'review'", text)
        self.assertIn('group: ipo-publication', text)
        self.assertEqual(text.count('contents: write'), 1)


if __name__ == '__main__':
    unittest.main()
