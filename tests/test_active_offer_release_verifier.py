"""The read-only release verifier checks the actual retained active source family."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verify_public_release as verify

ROOT = Path(__file__).resolve().parents[1]


class ActiveOfferReleaseVerifierTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        clock = self.enterContext(patch.object(verify, 'datetime', wraps=datetime))
        clock.now.return_value = datetime(2026, 9, 19, 14, tzinfo=timezone.utc)
        self.clock = clock
        for name in verify.STATIC_FILES: self.write(name, 'fixture')
        index = json.loads((ROOT / 'data/reviewed_correction_evidence.json').read_text(encoding='utf-8'))
        self.groups = [group for group in index['groups'] if group.get('kind') == 'active-offer-terms'
                       and group['identity']['id'] in {'axiomgas', 'varmora', 'poojalogis'}]
        self.assertEqual(len(self.groups), 3)
        before = json.loads((ROOT / 'tests/fixtures/active-offer-terms/before.json').read_text())
        self.stored, self.profiles, self.summaries = [], [], []
        for group in self.groups:
            raw = (ROOT / 'data/reviewed_correction_evidence' / group['proofsFile']).read_bytes()
            self.write('data/reviewed_correction_evidence/' + group['proofsFile'], raw.decode())
            active = json.loads(raw)['activeOfferTerms']['value']; identity = active['identity']; source = active['source']
            stored = copy.deepcopy(next(row for row in before if row['id'] == identity['id']))
            stored['activeOfferTerms'] = copy.deepcopy(active); self.stored.append(stored)
            profile = {**identity, 'profilePath': 'ipo/' + identity['id'] + '/',
                       'publicQuality': {'version': 1, 'sources': [{'sourceUrl': source['url'],
                           'sha256': source['sha256'], 'parserVersion': active['parserVersion'],
                           'checkedAt': active['review']['reviewedAt'], 'collectedAt': source['collectedAt'],
                           'reviewUrl': active['review']['url']}], 'fields': {'issueSizeCr': {'state': 'awaiting_disclosure'}}}}
            for field, proof in active['fields'].items():
                profile[field] = copy.deepcopy(proof['value'])
                if isinstance(profile[field], dict):
                    profile[field] = {key: value for key, value in profile[field].items() if value is not None}
                profile['publicQuality']['fields'][field] = {'state': 'provisional', 'until': identity['closeDate'],
                                                            'row': proof['row'], 'table': proof['table'], 'source': 0}
                if field == 'issueAmountScenarios':
                    amount = active['amountEvidence']; document = amount['source']
                    profile['publicQuality']['sources'].append({
                        'sourceUrl': document['url'], 'sha256': document['sha256'],
                        'documentDate': document['documentDate'], 'authority': document['authority'],
                        'collectionTimeBasis': document['collectionTimeBasis'],
                        'parserVersion': amount['parserVersion'], 'collectedAt': document['collectedAt'],
                        'checkedAt': amount['review']['reviewedAt'], 'reviewUrl': amount['review']['url'],
                        **({'publicationDate': document['publicationDate']} if document.get('publicationDate') else {})})
                    profile['publicQuality']['fields'][field].update(source=1, **{k: proof[k] for k in ('page','unit','sourceUnit')})
            summary = copy.deepcopy(profile)
            for field in ('issueComposition',):
                summary.pop(field, None); summary['publicQuality']['fields'].pop(field, None)
            self.profiles.append(profile); self.summaries.append(summary)
        self.save()

    def write(self, path, text):
        file = self.root / path; file.parent.mkdir(parents=True, exist_ok=True); file.write_bytes(text.encode())

    def save(self):
        self.write('data/ipos.json', json.dumps({'meta': {'publication': {'mode': 'reviewed', 'status': 'published',
                    'reviewedIds': [row['id'] for row in self.stored]}}, 'ipos': self.stored}))
        self.write('data/reviewed_correction_evidence.json', json.dumps({'schemaVersion': 1, 'groups': self.groups}))
        self.write('data/ipos-summary.json', json.dumps({'meta': {'recordCount': 3}, 'ipos': self.summaries}))
        self.write('ipo/routes.json', json.dumps({'recordCount': 3, 'routeCount': 3, 'routes': [row['id'] for row in self.stored]}))
        for profile in self.profiles:
            self.write(profile['profilePath'] + 'index.html', '<script type="application/json" id="ipo-profile-data">'
                       + json.dumps({'ipo': profile}) + '</script>')

    def verify(self):
        receipt = verify.verify_local(self.root)
        receipt['sampledProfiles'] = []
        result = verify.verify_reviewed_publication(self.root, receipt)
        self.assertEqual(len(receipt['sampledProfiles']), 3)
        return result

    def test_all_three_source_receipts_are_delivered_without_writes_or_final_promotion(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = self.verify()
        self.assertEqual(result['status'], 'passed')
        self.assertEqual([item['kind'] for item in result['checked']], ['active-offer-terms'] * 3)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_missing_or_mislabelled_values_sources_clocks_and_qualifiers_fail(self):
        original = copy.deepcopy(self.profiles)
        for defect in ('value', 'qualifier', 'state', 'source', 'observed', 'collected', 'until', 'row', 'missing'):
            self.profiles = copy.deepcopy(original); row = self.profiles[0]
            if defect == 'value': row['priceBand']['max'] = 53
            elif defect == 'qualifier': row['issueComposition'].pop('qualifiers')
            elif defect == 'state': row['publicQuality']['fields']['priceBand']['state'] = 'final_verified'
            elif defect == 'source': row['publicQuality']['sources'][0]['sourceUrl'] = 'https://example.test'
            elif defect == 'observed': row['publicQuality']['sources'][0]['observedAt'] = row['publicQuality']['sources'][0]['collectedAt']
            elif defect == 'collected': row['publicQuality']['sources'][0]['collectedAt'] = '2026-09-19T02:00:00Z'
            elif defect == 'until': row['publicQuality']['fields']['priceBand']['until'] = '2026-09-23'
            elif defect == 'row': row['publicQuality']['fields']['lotSize']['row'] += 1
            else:
                row['lotSize'] = None; row['publicQuality']['fields']['lotSize'] = {'state': 'awaiting_disclosure'}
            self.save()
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.verify()

    def test_receipt_or_git_identity_mismatch_is_rejected(self):
        original = copy.deepcopy(self.stored[0]['activeOfferTerms'])
        self.stored[0]['activeOfferTerms']['source']['sha256'] = 'a'*64; self.save()
        with self.assertRaisesRegex(ValueError, 'receipt differs'): self.verify()
        self.stored[0]['activeOfferTerms'] = original
        self.groups[0]['sourceProofsGitBlob'] = 'b'*40; self.save()
        with self.assertRaisesRegex(ValueError, 'Git identity'): self.verify()

    def test_expired_rebuilt_disclosures_can_be_withheld_but_not_populated_under_a_hold(self):
        self.clock.now.return_value = datetime(2026, 9, 26, 3, tzinfo=timezone.utc)
        for record in [*self.profiles, *self.summaries]:
            for field, decision in record['publicQuality']['fields'].items():
                if decision['state'] == 'provisional':
                    record.pop(field, None)
                    record['publicQuality']['fields'][field] = {'state': 'awaiting_disclosure'}
        self.save(); self.assertEqual(self.verify()['status'], 'passed')
        self.profiles[0]['lotSize'] = 2000; self.save()
        with self.assertRaises(ValueError): self.verify()


if __name__ == '__main__':
    unittest.main()
