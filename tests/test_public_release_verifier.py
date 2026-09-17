"""Deployment acceptance catches mixed/stale output without changing source data."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError

SPEC = importlib.util.spec_from_file_location('release_verifier', Path(__file__).with_name('verify_public_release.py'))
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


class PublicReleaseVerifierTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.row = {
            'id': 'emmvee', 'company': 'Example Ltd', 'profilePath': 'ipo/emmvee/',
            'subscription': {'total': 0}, 'subscriptionAuthority': 'secondary',
            'subscriptionObservedAt': '2026-09-17T10:00:00+05:30',
            'subscriptionCollectedAt': '2026-09-17T12:00:00+05:30',
            'publicQuality': {'version': 1, 'fields': {
                'issueSizeCr': {'state': 'under_review'}, 'subscription': {'state': 'reported'}}, 'sources': []},
        }
        self.profile = copy.deepcopy(self.row)
        for path in verify.STATIC_FILES:
            self.write(path, '<html>test fixture</html>')
        self.write_json('ipo/routes.json', {'routes': ['emmvee'], 'routeCount': 1, 'recordCount': 1})
        self.save()
        self.write_json('data/ipos.json', {'ipos': [{'id': 'emmvee', 'issueSizeCr': 123}]})
        self.write_json('data/pending_updates.json', {'updates': [{'status': 'pending_conflict_review'}]})
        self.write_json('data/phase_status.json', {'p4': {'status': 'incomplete'}, 'p5': {'status': 'waiting_for_p4'}})

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def write_json(self, path, data):
        self.write(path, json.dumps(data))

    def save(self):
        self.write_json('data/ipos-summary.json', {'meta': {'recordCount': 1}, 'ipos': [self.row]})
        self.write('ipo/emmvee/index.html', '<script type="application/json" id="ipo-profile-data">'
                   + json.dumps({'ipo': self.profile}) + '</script>')

    def files(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_accepts_consistent_output_and_zero_without_any_writes(self):
        before = self.files()
        receipt = verify.verify_local(self.root)
        calls = []
        def fetch(url, limit):
            calls.append(url)
            path = url.removeprefix('https://example.test/IPO-Tracker/')
            path = path + 'index.html' if not path or path.endswith('/') else path
            return (self.root / path).read_bytes()[:limit]
        checked = verify.verify_http(self.root, 'https://example.test/IPO-Tracker/', receipt, fetch=fetch)
        self.assertEqual(len(checked), len(receipt['expectedSha256']))
        self.assertEqual(receipt['routeCount'], 1)
        self.assertFalse(any('ipos.json' in url or 'pending_updates' in url or 'phase_status' in url for url in calls))
        self.assertEqual(before, self.files())

    def test_stale_summary_or_missing_profile_cannot_pass(self):
        for field, value in [('company', 'Old issuer'), ('subscriptionObservedAt', self.row['subscriptionCollectedAt']),
                             ('subscriptionAuthority', 'official_exchange')]:
            with self.subTest(field=field):
                self.profile = copy.deepcopy(self.row)
                self.profile[field] = value
                self.save()
                with self.assertRaisesRegex(ValueError, 'mismatch'):
                    verify.verify_local(self.root)
        (self.root / 'ipo/emmvee/index.html').unlink()
        with self.assertRaises(OSError):
            verify.verify_local(self.root)

    def test_reintroduced_held_values_fail_even_when_both_surfaces_agree(self):
        self.row['issueSizeCr'] = self.profile['issueSizeCr'] = 123
        self.save()
        with self.assertRaisesRegex(ValueError, 'Withheld field'):
            verify.verify_local(self.root)

    def test_source_references_compare_evidence_not_compacted_index(self):
        evidence = {'sourceUrl': 'https://example.test/prospectus.pdf', 'sha256': 'a' * 64}
        self.row['publicQuality']['sources'] = [evidence]
        self.profile['publicQuality']['sources'] = [{'sourceUrl': 'https://example.test/other.pdf'}, evidence]
        self.row['publicQuality']['fields']['issueSizeCr']['source'] = 0
        self.profile['publicQuality']['fields']['issueSizeCr']['source'] = 1
        self.save()
        verify.verify_local(self.root)
        self.profile['publicQuality']['sources'][1] = {'sourceUrl': 'https://example.test/wrong.pdf'}
        self.save()
        with self.assertRaisesRegex(ValueError, 'decision mismatch'):
            verify.verify_local(self.root)

    def test_duplicate_unsafe_and_incomplete_inventory_fail(self):
        for routes in [['../outside'], ['emmvee', 'emmvee'], []]:
            with self.subTest(routes=routes):
                self.write_json('ipo/routes.json', {'routes': routes, 'routeCount': len(routes), 'recordCount': len(routes)})
                with self.assertRaises(ValueError):
                    verify.verify_local(self.root)

    def test_duplicate_payload_unknown_contract_and_source_reference_fail(self):
        page = (self.root / 'ipo/emmvee/index.html').read_text()
        self.write('ipo/emmvee/index.html', page + page)
        with self.assertRaisesRegex(ValueError, 'one complete'):
            verify.verify_local(self.root)
        for change in ('version', 'reference'):
            self.profile = copy.deepcopy(self.row)
            if change == 'version':
                self.profile['publicQuality']['version'] = 999
            else:
                self.profile['publicQuality']['fields']['issueSizeCr']['source'] = True
            self.save()
            with self.assertRaises(ValueError):
                verify.verify_local(self.root)
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON'):
            verify.read_json('{"ipos": [], "ipos": []}')
        with self.assertRaisesRegex(ValueError, 'Non-finite'):
            verify.read_json('{"total": NaN}')

    def test_http_success_with_stale_or_oversized_content_is_failure(self):
        receipt = verify.verify_local(self.root)
        before = self.files()
        for content in (b'old public summary', b'x' * 100000):
            with self.subTest(content=len(content)), self.assertRaisesRegex(ValueError, 'served bytes'):
                verify.verify_http(self.root, 'https://example.test/', receipt, fetch=lambda url, limit: content[:limit])
        self.assertEqual(before, self.files())

    def test_source_failure_is_not_a_successful_release_check(self):
        receipt = verify.verify_local(self.root)
        def missing(url, limit):
            raise HTTPError(url, 404, 'not found', {}, None)
        with self.assertRaises(HTTPError):
            verify.verify_http(self.root, 'https://example.test/', receipt, fetch=missing)
        for base in ('http://example.test/', 'file:///tmp/', 'https://user:pass@example.test/', 'https://example.test/?x=1'):
            with self.subTest(base=base), self.assertRaises(ValueError):
                verify.verify_http(self.root, base, receipt, fetch=missing)


if __name__ == '__main__':
    unittest.main()
