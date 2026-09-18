"""Deployment acceptance catches mixed/stale output without changing source data."""
import copy
import importlib.util
import hashlib
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


    def reviewed_fixture(self):
        """Independent delivered-data fixture, with an explicitly disclosed zero OFS."""
        identity = {'id': 'emmvee', 'company': 'Example Ltd', 'symbol': 'EXAMPLE', 'openDate': '2025-11-11'}
        values = {'issueSizeCr': 100, 'freshIssueCr': 100, 'ofsCr': 0,
                  'issueComposition': {'freshShares': 10000000, 'ofsShares': 0, 'valuationPriceUsed': 100,
                                       'freshIssueCr': 100, 'ofsCr': 0, 'totalIssueSizeCr': 100}}
        source = {'sourceUrl': 'https://example.test/final.pdf', 'documentDate': '2025-11-14',
                  'sha256': 'a' * 64, 'parserVersion': 33, 'checkedAt': '2026-09-18T00:37:05Z'}
        proofs = {field: {**source, 'field': field, 'issueOpenDate': identity['openDate'],
                          'documentType': 'PROSPECTUS', 'value': value,
                          'evidence': {'page': 3, 'unit': 'crore INR', 'row': 'Reviewed fixture disclosure'}}
                  for field, value in values.items()}
        raw = (json.dumps(proofs, ensure_ascii=False, indent=2) + '\n').encode()
        self.write('data/reviewed_correction_evidence/emmvee.json', raw.decode())
        self.index = {'schemaVersion': 1, 'groups': [{'identity': identity, 'proofsFile': 'emmvee.json',
            'sourceProofsSha256': verify.digest(raw),
            'sourceProofsGitBlob': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
            'sourceReviewUrl': 'https://github.com/owner/repo/blob/' + 'b' * 40 + '/review.md'}]}
        self.write_json('data/reviewed_correction_evidence.json', self.index)
        self.row.update(identity, issueSizeCr=100)
        self.row['publicQuality'] = {'version': 1, 'fields': {
            'issueSizeCr': {'state': 'final_verified', 'source': 0, 'page': 3}}, 'sources': [source]}
        self.profile = copy.deepcopy(self.row)
        self.profile.update(copy.deepcopy(values))
        self.profile['issueComposition'] = {k: values['issueComposition'][k]
                                           for k in ('freshShares', 'ofsShares', 'valuationPriceUsed')}
        self.profile['publicQuality']['fields'] = {
            field: {'state': 'final_verified', 'source': 0, 'page': 3} for field in values}
        self.canonical = {'meta': {'publication': {'mode': 'reviewed', 'status': 'published', 'reviewedIds': ['emmvee']}},
                          'ipos': [{**identity, **copy.deepcopy(values), 'staticFieldProvenance': copy.deepcopy(proofs)}]}
        self.write_json('data/ipos.json', self.canonical)
        self.save()

    def test_reviewed_delivery_checks_values_proofs_zero_and_does_not_write(self):
        self.reviewed_fixture()
        before = self.files()
        receipt = verify.verify_local(self.root)
        result = verify.verify_reviewed_publication(self.root, receipt)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['checked'][0]['proofsSha256'], self.index['groups'][0]['sourceProofsSha256'])
        self.assertEqual(result['checked'][0]['id'], 'emmvee')
        self.assertEqual(before, self.files())

    def test_consistent_but_still_withheld_repair_cannot_pass_reviewed_acceptance(self):
        self.reviewed_fixture()
        for record in (self.row, self.profile):
            for field, decision in record['publicQuality']['fields'].items():
                record[field] = None
                decision['state'] = 'under_review'
        self.save()
        # This is the actual historical gap: consistency alone is not repair delivery.
        receipt = verify.verify_local(self.root)
        before = self.files()
        with self.assertRaisesRegex(ValueError, 'not delivered'):
            verify.verify_reviewed_publication(self.root, receipt)
        self.assertEqual(before, self.files())

    def test_identical_wrong_public_amounts_or_provenance_cannot_pass(self):
        for defect in ('amount', 'pdf', 'time', 'page', 'zero_as_null', 'zero_as_false'):
            with self.subTest(defect=defect):
                self.reviewed_fixture()
                for record in (self.row, self.profile):
                    if defect == 'amount':
                        record['issueSizeCr'] = 101
                    elif defect == 'pdf':
                        record['publicQuality']['sources'][0]['sha256'] = 'c' * 64
                    elif defect == 'time':
                        record['publicQuality']['sources'][0]['checkedAt'] = '2026-09-18T01:00:00Z'
                    elif defect == 'page':
                        record['publicQuality']['fields']['issueSizeCr']['page'] = 4
                if defect.startswith('zero_as_'):
                    self.profile['ofsCr'] = None if defect.endswith('null') else False
                self.save()
                receipt = verify.verify_local(self.root)
                with self.assertRaisesRegex(ValueError, 'not delivered'):
                    verify.verify_reviewed_publication(self.root, receipt)

    def test_reviewed_canonical_value_and_complete_proof_must_match(self):
        for defect in ('amount', 'proof', 'identity', 'duplicate'):
            with self.subTest(defect=defect):
                self.reviewed_fixture()
                row = self.canonical['ipos'][0]
                if defect == 'amount':
                    row['freshIssueCr'] = 90
                elif defect == 'proof':
                    row['staticFieldProvenance']['issueSizeCr']['evidence']['row'] = 'Different evidence'
                elif defect == 'identity':
                    row['openDate'] = '2026-11-11'
                else:
                    self.canonical['ipos'].append(copy.deepcopy(row))
                self.write_json('data/ipos.json', self.canonical)
                with self.assertRaises(ValueError):
                    verify.verify_reviewed_publication(self.root, verify.verify_local(self.root))

    def test_invalid_reviewed_scope_is_failure_not_an_empty_success(self):
        for ids in (None, [], ['emmvee', 'emmvee'], ['unknown'], 'emmvee', [None], ['']):
            with self.subTest(ids=ids):
                self.reviewed_fixture()
                self.canonical['meta']['publication']['reviewedIds'] = ids
                self.write_json('data/ipos.json', self.canonical)
                with self.assertRaises(ValueError):
                    verify.verify_reviewed_publication(self.root, verify.verify_local(self.root))
        self.reviewed_fixture()
        self.canonical['meta']['publication']['status'] = 'published_with_pending_conflicts'
        self.write_json('data/ipos.json', self.canonical)
        with self.assertRaisesRegex(ValueError, 'not accepted'):
            verify.verify_reviewed_publication(self.root, verify.verify_local(self.root))

    def test_missing_tampered_unsafe_or_duplicate_reviewed_artifact_fails(self):
        for defect in ('missing', 'tampered', 'path', 'git_blob', 'duplicate'):
            with self.subTest(defect=defect):
                self.reviewed_fixture()
                path = self.root / 'data/reviewed_correction_evidence/emmvee.json'
                if defect == 'missing':
                    path.unlink()
                elif defect == 'tampered':
                    path.write_text('{}')
                elif defect == 'path':
                    self.index['groups'][0]['proofsFile'] = '../outside.json'
                elif defect == 'git_blob':
                    self.index['groups'][0]['sourceProofsGitBlob'] = 'c' * 40
                else:
                    self.index['groups'].append(copy.deepcopy(self.index['groups'][0]))
                self.write_json('data/reviewed_correction_evidence.json', self.index)
                with self.assertRaises((OSError, ValueError)):
                    verify.verify_reviewed_publication(self.root, verify.verify_local(self.root))

    def test_reviewed_profile_is_always_live_checked_without_fetching_master(self):
        self.reviewed_fixture()
        receipt = verify.verify_local(self.root)
        receipt['sampledProfiles'] = []
        receipt['expectedSha256'].pop('ipo/emmvee/index.html')
        verify.verify_reviewed_publication(self.root, receipt)
        self.assertEqual(receipt['sampledProfiles'], ['ipo/emmvee/'])
        urls = []
        def fetch(url, limit):
            urls.append(url)
            relative = url.removeprefix('https://example.test/')
            relative += 'index.html' if not relative or relative.endswith('/') else ''
            return (self.root / relative).read_bytes()[:limit]
        verify.verify_http(self.root, 'https://example.test/', receipt, fetch=fetch)
        self.assertIn('https://example.test/ipo/emmvee/', urls)
        self.assertFalse(any('ipos.json' in url or 'reviewed_correction_evidence' in url for url in urls))
        with self.assertRaisesRegex(ValueError, 'served bytes'):
            verify.verify_http(self.root, 'https://example.test/', receipt,
                               fetch=lambda url, limit: b'old profile' if '/ipo/emmvee/' in url else fetch(url, limit))

    def test_ordinary_release_does_not_claim_reviewed_acceptance(self):
        before = self.files()
        result = verify.verify_reviewed_publication(self.root, verify.verify_local(self.root))
        self.assertEqual(result['status'], 'not_requested')
        self.assertNotIn('checked', result)
        self.assertEqual(before, self.files())


if __name__ == '__main__':
    unittest.main()
