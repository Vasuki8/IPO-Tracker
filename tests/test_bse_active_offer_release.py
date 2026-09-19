"""Stdlib release acceptance for BSE terms with no invented canonical symbol."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verify_public_release as verify

ROOT = Path(__file__).resolve().parents[1]


class BseActiveOfferReleaseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.clock = self.enterContext(patch.object(verify, 'datetime', wraps=datetime))
        self.clock.now.return_value = datetime(2026, 9, 19, 6, tzinfo=timezone.utc)
        index = json.loads((ROOT / 'data/reviewed_correction_evidence.json').read_text())
        before = json.loads((ROOT / 'tests/fixtures/bse-active-offer-terms/before.json').read_text())
        ids = {row['id'] for row in before}
        self.groups = [group for group in index['groups'] if group['identity']['id'] in ids]
        self.assertEqual(len(self.groups), 4)
        self.stored, self.profiles = [], []
        for group in self.groups:
            raw = (ROOT / 'data/reviewed_correction_evidence' / group['proofsFile']).read_bytes()
            self.write('data/reviewed_correction_evidence/' + group['proofsFile'], raw)
            active = json.loads(raw)['activeOfferTerms']['value']; source = active['source']
            row = copy.deepcopy(next(row for row in before if row['id'] == group['identity']['id']))
            row['activeOfferTerms'] = active; self.stored.append(row)
            profile = {**active['identity'], 'profilePath': row['profilePath'],
                       'publicQuality': {'version': 1, 'fields': {}, 'sources': [{'sourceUrl': source['url'],
                        'sha256': source['sha256'], 'parserVersion': active['parserVersion'],
                        'checkedAt': active['review']['reviewedAt'], 'collectedAt': source['collectedAt'],
                        'reviewUrl': active['review']['url']}]}}
            for field, proof in active['fields'].items():
                profile[field] = copy.deepcopy(proof['value'])
                profile['publicQuality']['fields'][field] = {'state': 'provisional', 'until': row['closeDate'],
                    'row': proof['row'], 'table': proof['table'], 'source': 0}
            self.profiles.append(profile)
        self.summary = copy.deepcopy(self.profiles)
        self.save()

    def write(self, path, value):
        file = self.root / path; file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(value if isinstance(value, bytes) else value.encode())

    def save(self):
        self.write('data/ipos.json', json.dumps({'meta': {'publication': {'mode': 'reviewed', 'status': 'published',
                    'reviewedIds': [row['id'] for row in self.stored]}}, 'ipos': self.stored}))
        self.write('data/reviewed_correction_evidence.json', json.dumps({'schemaVersion': 1, 'groups': self.groups}))
        self.write('data/ipos-summary.json', json.dumps({'ipos': self.summary}))
        for row in self.profiles:
            self.write(row['profilePath'] + 'index.html', '<script type="application/json" id="ipo-profile-data">'
                       + json.dumps({'ipo': row}) + '</script>')

    def verify(self):
        return verify.verify_reviewed_publication(self.root, {'sampledProfiles': [], 'expectedSha256': {}})

    def test_four_real_receipts_deliver_without_adding_canonical_symbols(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(len(self.verify()['checked']), 4)
        self.assertTrue(all('symbol' not in row for row in self.stored))
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_quantity_state_source_and_directory_omission_fail(self):
        profiles, summary = copy.deepcopy(self.profiles), copy.deepcopy(self.summary)
        for defect in ('quantity', 'state', 'source', 'clock', 'directory', 'directory_and_decision', 'row'):
            self.profiles, self.summary = copy.deepcopy(profiles), copy.deepcopy(summary)
            row = self.profiles[0]
            if defect == 'quantity': row['marketLot'] = row['minimumBidQuantity']
            elif defect == 'state': row['publicQuality']['fields']['marketLot']['state'] = 'final_verified'
            elif defect == 'source': row['publicQuality']['sources'][0]['sourceUrl'] = 'https://example.test'
            elif defect == 'clock': row['publicQuality']['sources'][0]['observedAt'] = row['publicQuality']['sources'][0]['collectedAt']
            elif defect == 'directory': self.summary[0].pop('minimumBidQuantity')
            elif defect == 'directory_and_decision':
                self.summary[0].pop('minimumBidQuantity')
                self.summary[0]['publicQuality']['fields'].pop('minimumBidQuantity')
            else: row['publicQuality']['fields']['minimumBidQuantity']['row'] += 1
            self.save()
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.verify()

    def test_a_new_conflicting_canonical_symbol_is_not_hidden_by_the_receipt(self):
        self.stored[0]['symbol'] = 'OTHER'; self.save()
        with self.assertRaises(ValueError): self.verify()

    def test_publication_cannot_invent_a_symbol_for_a_source_only_symbol(self):
        for row in (self.profiles[0], self.summary[0]):
            row['symbol'] = 'FXML'; self.save()
            with self.assertRaisesRegex(ValueError, 'canonical symbol'): self.verify()
            row.pop('symbol')

    def test_expired_quantities_must_be_withheld(self):
        self.clock.now.return_value = datetime(2026, 9, 26, 6, tzinfo=timezone.utc)
        for row in self.profiles + self.summary:
            for field in ('priceBand', 'marketLot', 'minimumBidQuantity'):
                row.pop(field)
                row['publicQuality']['fields'][field] = {'state': 'awaiting_disclosure'}
        self.save(); self.assertEqual(self.verify()['status'], 'passed')
        self.summary[0]['marketLot'] = 1200; self.save()
        with self.assertRaises(ValueError): self.verify()


if __name__ == '__main__': unittest.main()
