"""Reviewed transport preparation uses the existing source-free review writer."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from publication_mode import push_mode


SUPPORT_RELEASE = [
    'scripts/reviewed_evidence.py', 'scripts/reviewed_corrections.py',
    'scripts/apply_corrections.py', 'scripts/publication_mode.py',
    'scripts/publish_transaction.py',
    'scripts/validate_data.py', 'scripts/run_offer_documents.py',
    'scripts/final_prospectus_policy.py',
    'scripts/review_intermediary_columns.py',
    'scripts/review_financial_tables.py', 'scripts/enforce_final_prospectus_policy.py',
    'data/verified_corrections.json', 'data/reviewed_correction_evidence.json',
    'data/reviewed_correction_evidence/example-issuer.json',
    'tests/test_reviewed_support_routing.py', 'tests/verify_public_release.py',
    'docs/PROJECT_STATUS.md', '.github/workflows/public-release.yml',
]


class ReviewedSupportRoutingTests(unittest.TestCase):
    def test_complete_reviewed_support_release_rebuilds_without_collection(self):
        self.assertEqual(push_mode(SUPPORT_RELEASE), 'review')
        for discriminator in ('scripts/reviewed_evidence.py', 'scripts/reviewed_corrections.py'):
            with self.subTest(discriminator=discriminator):
                self.assertEqual(push_mode([discriminator, 'scripts/apply_corrections.py']), 'review')

    def test_registry_and_apply_changes_need_explicit_support_discriminator(self):
        for path in ('scripts/apply_corrections.py', 'scripts/publish_transaction.py',
                     'scripts/run_offer_documents.py', 'scripts/final_prospectus_policy.py',
                     'data/verified_corrections.json',
                     'data/reviewed_correction_evidence.json',
                     'data/reviewed_correction_evidence/example.json',
                     'scripts/review_intermediary_columns.py'):
            with self.subTest(path=path):
                self.assertEqual(push_mode([path, 'tests/example.py', 'docs/review.md']), 'repair')

    def test_mixed_collector_or_protected_changes_cannot_take_support_route(self):
        for path in ('scripts/track_subscriptions.py', 'scripts/final_prospectus_parser.py',
                     'scripts/offer_parser.py',
                     'scripts/p4_offer_parser.py', 'scripts/run_pipeline.py',
                     'scripts/publication_source_policy.py',
                     'scripts/phase_status.py', 'data/ipos.json', 'data/pending_updates.json',
                     'data/phase_status.json', 'uv.lock', 'pyproject.toml',
                     'tools/unknown.py', '.github/workflows/unknown.yml',
                     'data/reviewed_correction_evidence/../ipos.json',
                     'data/reviewed_correction_evidence/nested/example.json',
                     'data/reviewed_correction_evidence/Example.json',
                     'data/reviewed_correction_evidence/example.json.bak', None, 3):
            with self.subTest(path=path):
                self.assertEqual(push_mode(SUPPORT_RELEASE + [path]), 'repair')

    def test_request_is_still_separate_from_support_and_registry(self):
        request = 'data/reviewed_publication_request.json'
        self.assertEqual(push_mode([request]), 'reviewed')
        for path in SUPPORT_RELEASE:
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                push_mode([request, path])

    def test_existing_review_path_does_not_apply_staged_corrections(self):
        workflow = (ROOT / '.github/workflows/refresh.yml').read_text()
        block = workflow.split('if [[ "$MODE" == "review" ]]; then', 1)[1].split('              else', 1)[0]
        self.assertIn('git diff --exit-code -- data/ipos.json data/pending_updates.json', block)
        self.assertIn('build_missing_queue.py', block)
        self.assertIn('phase_status.py', block)
        for forbidden in ('apply_corrections.py', 'run_pipeline.py', 'publish_transaction.py'):
            self.assertNotIn(forbidden, block)


if __name__ == '__main__':
    unittest.main()
