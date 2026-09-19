"""Audit accuracy: never turn a reference or hidden proof into a displayed fact."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'docs/audits/commercial/2026-09-19-publication-scope/exposure.py'
SPEC = importlib.util.spec_from_file_location('commercial_publication_scope', PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class CommercialPublicationScopeTests(unittest.TestCase):
    def test_provider_requires_exact_host_not_lookalike_or_credentials(self):
        self.assertEqual(audit.provider('https://WWW.IPOPREMIUM.IN/view'), 'IPO Premium')
        for url in (None, '', 'https://ipopremium.in.evil.test/',
                    'https://ipopremium.in@evil.test/', 'https://user@ipopremium.in/',
                    'javascript:https://ipopremium.in/', 'https://[bad'):
            with self.subTest(url=url):
                self.assertIsNone(audit.provider(url))

    def test_reference_pointers_escape_keys_and_preserve_history_location(self):
        refs = audit.references({'a/b~c': [{'url': 'https://ipowatch.in/one'}]})
        self.assertEqual(refs[0]['pointer'], '/a~1b~0c/0/url')

    def test_source_reference_is_not_field_provenance(self):
        row = {'id': 'issuer', 'sources': [{'url': 'https://ipocentral.in/issuer'}],
               'priceBand': {'min': 10}}
        result = audit.record_scope(row, {'id': 'issuer'}, {'id': 'issuer'})
        self.assertEqual(len(result['canonicalReferences']), 1)
        self.assertEqual(result['fieldProofBindings'], [])

    def test_missing_subscription_url_and_observation_not_inferred_from_history(self):
        row = {'id': 'issuer', 'subscriptionSource': 'IPO Premium (secondary)',
               'subscription': {'total': 0, 'qib': None},
               'subscriptionHistory': [{'sourceUrl': 'https://ipopremium.in/view',
                                        'observedAt': '2026-09-18T10:00:00Z'}]}
        result = audit.record_scope(row, {'id': 'issuer'}, {'id': 'issuer'})['secondarySubscription']
        self.assertIsNone(result['sourceUrl'])
        self.assertIsNone(result['sourceObservedAt'])
        self.assertEqual(result['canonicalFields'], ['total'])
        self.assertEqual(result['profileFields'], [])
        self.assertFalse(result['summaryTotalPresent'])
        self.assertEqual(result['canonicalHistoryCount'], 1)
        self.assertEqual(result['publicProfileHistoryCount'], 0)

    def test_held_proof_text_is_retained_without_claiming_public_value(self):
        row = {'id': 'issuer', 'financials': {'revenue': 0}, 'staticFieldProvenance': {
            'financials': {'sourceUrl': 'https://sunshinepictures.in/prospectus.pdf',
                          'sha256': 'document-hash', 'evidence': {
                              'FY2026': {'page': 188, 'header': 'Revenue table', 'row': 'Revenue 0'}}}}}
        public = {'id': 'issuer', 'financials': None,
                  'publicQuality': {'fields': {'financials': {'state': 'under_review'}}}}
        proof = audit.record_scope(row, public, public)['fieldProofBindings'][0]
        self.assertTrue(proof['canonicalValuePresent'])
        self.assertFalse(proof['profileValuePresent'])
        self.assertEqual(proof['profileState'], 'under_review')
        self.assertEqual(len(proof['retainedProofTextCandidates']), 2)
        self.assertNotIn('Revenue table', str(proof))
        self.assertEqual(proof['retainedProofTextCandidates'][0]['sha256'], audit.sha(b'Revenue table'))

    def test_identity_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            audit.record_scope({'id': 'one'}, {'id': 'two'}, {'id': 'one'})

    def test_profile_requires_single_named_identity_payload(self):
        payload = b'<script id="ipo-profile-data" type="application/json">{"ipo":{"id":"issuer"}}</script>'
        self.assertEqual(audit.profile_record(payload)['id'], 'issuer')
        for raw in (b'<html></html>', payload + payload,
                    b'<script id="ipo-profile-data">{"ipo":{}}</script>'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                audit.profile_record(raw)


if __name__ == '__main__':
    unittest.main()
