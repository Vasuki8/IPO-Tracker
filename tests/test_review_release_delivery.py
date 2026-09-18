"""A matching home page cannot excuse a stale held profile or review queue."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import verify_review_release as review


class ReviewReleaseDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in (*review.REVIEW_PATHS, 'index.html', 'data/ipos.json', 'data/pending_updates.json'):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({'path': name}))
        (self.root/'data/public_display_holds.json').write_text(json.dumps({'holds': []}))
        self.initial = {'expectedSha256': {'index.html': review.public.digest((self.root/'index.html').read_bytes())},
                        'sampledProfiles': ['ipo/snehaa/'], 'routeCount': 2}

    def prepare(self):
        with patch.object(review.public, 'verify_local', return_value=copy.deepcopy(self.initial)) as local, \
             patch.object(review.public, 'verify_reviewed_publication', return_value={'status':'not_requested'}) as evidence:
            receipt = review.prepare(self.root)
            local.assert_called_once_with(self.root)
            evidence.assert_called_once()
            return receipt

    def fetch(self, url, limit):
        path = url.removeprefix('https://example.test/')
        if not path or path.endswith('/'):
            path += 'index.html'
        self.assertNotIn(path, ('data/ipos.json', 'data/pending_updates.json'))
        return (self.root/path).read_bytes()[:limit]

    def test_both_profiles_and_review_reports_are_verified_without_writes(self):
        before = {p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        receipt = self.prepare()
        checked = review.public.verify_http(self.root, 'https://example.test/', receipt, fetch=self.fetch)
        self.assertEqual(set(checked), {'index.html', *review.REVIEW_PATHS})
        self.assertEqual(receipt['sampledProfiles'], ['ipo/snehaa/', 'ipo/sacheerome/'])
        self.assertEqual(receipt['reviewedPublication'], {'status':'not_requested'})
        self.assertEqual(before, {p:p.read_bytes() for p in before})

    def test_each_stale_review_asset_fails_even_with_matching_other_public_bytes(self):
        receipt = self.prepare()
        for name in review.REVIEW_PATHS:
            with self.subTest(path=name):
                target_url = 'https://example.test/' + (name[:-len('index.html')] if name.endswith('index.html') else name)
                def stale(url, limit):
                    return b'previous release' if url == target_url else self.fetch(url, limit)
                with self.assertRaisesRegex(ValueError, 'served bytes'):
                    review.public.verify_http(self.root, 'https://example.test/', receipt, fetch=stale)

    def test_missing_review_asset_is_not_silently_removed_from_acceptance(self):
        (self.root/'data/missing_queue.json').unlink()
        with self.assertRaises(OSError):
            self.prepare()


if __name__ == '__main__':
    unittest.main()
