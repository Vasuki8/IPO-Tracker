"""Adding the read-only release rehearsal must not start broad collection."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from publication_mode import push_mode


class ReviewReleaseRoutingTests(unittest.TestCase):
    def test_review_and_verifier_change_uses_existing_review_publisher_only(self):
        paths = ['scripts/source_review_holds.py', 'scripts/source_review_queue.py',
                 'scripts/public_quality.py', 'scripts/publication_mode.py',
                 'data/public_display_holds.json', 'public-quality.js',
                 '.github/workflows/public-release.yml', 'tests/review_release_candidate.py',
                 'tests/test_review_release_candidate.py', 'docs/PROJECT_STATUS.md']
        self.assertEqual(push_mode(paths), 'review')
        for protected in ('scripts/update_data.py', 'scripts/publish_transaction.py',
                          'data/ipos.json', 'data/pending_updates.json', 'uv.lock',
                          '.github/workflows/unreviewed.yml'):
            with self.subTest(path=protected):
                self.assertEqual(push_mode(paths + [protected]), 'repair')


if __name__ == '__main__': unittest.main()
