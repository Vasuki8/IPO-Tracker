"""Source-column repairs remain opt-in, atomic and limited to the reviewed pair."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from apply_corrections import apply, fingerprint
from reviewed_corrections import prepare, validate_scope
from reviewed_evidence import digest, index_groups
from review_intermediary_columns import extract_intermediary_columns, PARSER_VERSION
from public_quality import project_record
from validate_data import validate_payload


class ReviewedIntermediaryPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((ROOT / 'tests/reviewed_intermediary_before.json').read_text(encoding='utf-8'))
        cls.sources = json.loads((ROOT / 'tests/fixtures/intermediary_columns_reviewed.json').read_text(encoding='utf-8'))

    def setUp(self):
        self.payload = copy.deepcopy(self.before)
        self.registry = {'changes': [], 'fillMissing': []}
        self.groups = []
        rows = {row['id']: row for row in self.payload['ipos']}
        for source in self.sources:
            identity = source['identity']; row = rows[identity['id']]
            parsed = extract_intermediary_columns(source['sourceText'], page=source['physicalPage'])
            proofs = {}
            for field in ('leadManagers', 'registrar'):
                proofs[field] = {'identity': identity, 'source': 'Final Prospectus', 'sourceUrl': source['sourceUrl'],
                    'documentType': 'PROSPECTUS', 'documentDate': source['documentDate'],
                    'sha256': source['sha256'], 'parserVersion': PARSER_VERSION,
                    'checkedAt': '2026-09-18T19:00:00Z', 'issueOpenDate': identity['openDate'],
                    'field': field, 'value': parsed[field], 'evidence': parsed['fieldEvidence'][field]}
                self.registry['changes'].append({'id': row['id'], 'identity': identity,
                    'field': field, 'beforeHash': fingerprint(row.get(field)), 'after': parsed[field],
                    'publicationScope': 'explicit-reviewed', 'reviewedAt': '2026-09-18T19:00:00Z',
                    'source': {'name': 'Final Prospectus', 'type': 'PROSPECTUS', 'url': source['sourceUrl']},
                    'evidence': {'sha256': source['sha256'], 'documentDate': source['documentDate']}})
            raw = (json.dumps(proofs, ensure_ascii=False, indent=2) + '\n').encode()
            self.groups.append({'kind': 'intermediaries', 'identity': identity, 'proofs': proofs,
                'beforeProofHashes': {field: digest(row.get('staticFieldProvenance', {}).get(field)) for field in proofs},
                'sourceProofsSha256': hashlib.sha256(raw).hexdigest(),
                'sourceReviewUrl': 'https://github.com/Vasuki8/IPO-Tracker/blob/' + 'a'*40 + '/docs/review.md',
                'reviewedAt': '2026-09-18T19:00:00Z'})
        self.ids = [group['identity']['id'] for group in self.groups]

    def candidate(self):
        return prepare(self.payload, self.registry, self.groups, self.ids)

    def test_ordinary_registry_apply_cannot_activate_explicit_repairs(self):
        before = copy.deepcopy(self.payload['ipos'])
        count, conflicts = apply(self.payload, self.registry, evidence_groups=self.groups)
        self.assertEqual(count, 0); self.assertEqual(conflicts, [])
        self.assertEqual(self.payload['ipos'], before)

    def test_four_real_fields_match_reviewed_roles_and_preserve_every_other_fact(self):
        before = copy.deepcopy(self.payload)
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Offline preparation')):
            candidate = self.candidate()
        validate_scope(before, candidate, self.ids, groups=self.groups)
        self.assertEqual(before, self.payload)
        for original, corrected, group in zip(before['ipos'], candidate['ipos'], self.groups):
            projected = project_record(corrected)
            for field, proof in group['proofs'].items():
                self.assertEqual(corrected[field], proof['value'])
                self.assertEqual(projected['publicQuality']['fields'][field]['state'], 'final_verified')
            for field in ('objectsOfIssue', 'financials', 'documentFieldProvenance', 'offerDocumentExtraction', 'subscription'):
                self.assertEqual(corrected.get(field), original.get(field))
            self.assertEqual(corrected['dataCorrections'][:len(original.get('dataCorrections', []))], original.get('dataCorrections', []))
        self.assertEqual(validate_payload(candidate)['errorCount'], 0)

    def test_source_reviews_reduce_by_three_without_removing_hold_registry(self):
        before = validate_payload(self.payload)
        after = validate_payload(self.candidate())
        self.assertEqual(before['reviewCount'] - after['reviewCount'], 3)

    def test_concurrent_value_proof_or_offer_change_blocks_the_whole_publication(self):
        for kind in ('value', 'proof', 'identity'):
            with self.subTest(kind=kind):
                original = copy.deepcopy(self.payload)
                row = self.payload['ipos'][0]
                if kind == 'value': row['registrar'] = 'Newer Registrar Private Limited'
                elif kind == 'proof': row.setdefault('staticFieldProvenance', {})['registrar'] = {'newer': True}
                else: row['openDate'] = '2025-08-28'
                unchanged = copy.deepcopy(self.payload)
                with self.assertRaises(ValueError): self.candidate()
                self.assertEqual(self.payload, unchanged)
                self.payload = original

    def test_tampered_column_or_pair_is_rejected_even_after_rehashing(self):
        for kind in ('span', 'role', 'pair', 'kind', 'scope'):
            with self.subTest(kind=kind):
                groups = copy.deepcopy(self.groups); registry = copy.deepcopy(self.registry)
                if kind == 'span': groups[0]['proofs']['registrar']['evidence']['columnStart'] += 1
                elif kind == 'role': groups[0]['proofs']['registrar']['evidence']['heading'] = 'LEAD MANAGER'
                elif kind == 'pair': groups[0]['proofs'].pop('registrar')
                elif kind == 'kind': groups[0]['kind'] = 'anything'
                else: registry['changes'][0].pop('publicationScope')
                raw = (json.dumps(groups[0]['proofs'], ensure_ascii=False, indent=2) + '\n').encode()
                groups[0]['sourceProofsSha256'] = hashlib.sha256(raw).hexdigest()
                with self.assertRaises(ValueError): index_groups(groups, registry)

    def test_composition_or_other_field_changes_are_outside_intermediary_scope(self):
        for field, value in [('issueSizeCr', 999), ('financials', {'changed': True}), ('subscription', {'total': 0}), ('newUnrelatedField', None)]:
            candidate = self.candidate(); candidate['ipos'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_scope(self.payload, candidate, self.ids, groups=self.groups)

    def test_scope_errors_and_missing_proofs_fail_before_mutating(self):
        for scope in ('unsupported', None):
            registry = copy.deepcopy(self.registry)
            registry['changes'][0]['publicationScope'] = scope
            original = copy.deepcopy(self.payload)
            with self.assertRaises(ValueError): apply(self.payload, registry, explicit_review=True)
            self.assertEqual(self.payload, original)
        with self.assertRaises(ValueError): apply(self.payload, self.registry, explicit_review=True)

    def test_reapplication_preserves_existing_correction_history(self):
        candidate = self.candidate()
        first = copy.deepcopy(candidate['ipos'])
        count, conflicts = apply(candidate, self.registry, evidence_groups=self.groups, explicit_review=True)
        self.assertEqual(count, 0); self.assertEqual(conflicts, [])
        self.assertEqual(candidate['ipos'], first)

    def test_old_same_pdf_extraction_and_quarantine_cannot_undo_reviewed_roles(self):
        from run_offer_documents import quarantine_intermediaries
        from final_prospectus_policy import apply_final_prospectus_static_fields
        candidate = self.candidate()
        for row, before, group in zip(candidate['ipos'], self.payload['ipos'], self.groups):
            expected = copy.deepcopy(row)
            quarantine_intermediaries(row)
            self.assertEqual(row, expected)
            source = group['proofs']['leadManagers']
            parsed = {field: before.get(field) for field in ('leadManagers', 'registrar')}
            for url in (source['sourceUrl'], 'https://nsearchives.nseindia.com/mirror.pdf'):
                changes = apply_final_prospectus_static_fields(row, parsed,
                    {'type': 'PROSPECTUS', 'url': url, 'filedDate': source['documentDate']},
                    sha256=source['sha256'], parser_version=31, checked_at='2026-09-19T00:00:00Z')
                self.assertFalse(changes)
                for field in ('leadManagers', 'registrar'):
                    self.assertEqual(row[field], expected[field])
                    self.assertEqual(row['staticFieldProvenance'][field], expected['staticFieldProvenance'][field])
                    self.assertEqual(project_record(row)['publicQuality']['fields'][field]['state'], 'final_verified')

    def test_different_authoritative_document_remains_eligible_and_bad_proof_is_not_privileged(self):
        from final_prospectus_policy import apply_final_prospectus_static_fields
        from review_intermediary_columns import has_reviewed_role_evidence
        row = self.candidate()['ipos'][0]
        self.assertTrue(has_reviewed_role_evidence(row, 'leadManagers'))
        for key in ('id', 'company', 'symbol', 'openDate'):
            wrong = copy.deepcopy(row); wrong[key] += '-other'
            self.assertFalse(has_reviewed_role_evidence(wrong, 'leadManagers'))
        bad = copy.deepcopy(row); bad['staticFieldProvenance']['leadManagers']['evidence']['nameSpans'][0]['start'] += 1
        self.assertFalse(has_reviewed_role_evidence(bad, 'leadManagers'))
        changes = apply_final_prospectus_static_fields(row, {'leadManagers': ['Other Capital Private Limited']},
            {'type': 'PROSPECTUS', 'url': 'https://nsearchives.nseindia.com/new.pdf'},
            sha256='b'*64, parser_version=31, checked_at='2026-09-19T00:00:00Z')
        self.assertTrue(changes)
        self.assertEqual(row['leadManagers'], ['Other Capital Private Limited'])

    def test_individually_replayable_proofs_cannot_mix_two_source_tables(self):
        group = copy.deepcopy(self.groups[0])
        original = group['proofs']['registrar']['evidence']
        lines = '\n'.join(original['rawLines']).replace('FAST TRACK FINSEC', 'OTHER CAPITAL CORP')
        parsed = extract_intermediary_columns(lines, page=original['page'])
        group['proofs']['registrar']['evidence'] = parsed['fieldEvidence']['registrar']
        raw = (json.dumps(group['proofs'], ensure_ascii=False, indent=2) + '\n').encode()
        group['sourceProofsSha256'] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, 'one physical source table'):
            index_groups([group, self.groups[1]], self.registry)

    def test_current_full_inventory_and_pending_proposals_survive_scoped_preparation(self):
        from reviewed_evidence import load_groups
        pending = (ROOT/'data/pending_updates.json').read_bytes()
        production = json.loads((ROOT/'data/ipos.json').read_text(encoding='utf-8'))
        registry = json.loads((ROOT/'data/verified_corrections.json').read_text(encoding='utf-8'))
        candidate = prepare(production, registry, load_groups(), self.ids)
        self.assertEqual(len(candidate['ipos']), len(production['ipos']))
        self.assertEqual([r for r in candidate['ipos'] if r['id'] not in self.ids],
                         [r for r in production['ipos'] if r['id'] not in self.ids])
        self.assertEqual((ROOT/'data/pending_updates.json').read_bytes(), pending)
        for row in candidate['ipos']:
            if row['id'] in ('teamtech', 'spectraa'):
                field = 'objectsOfIssue' if row['id'] == 'teamtech' else 'subscription'
                self.assertEqual(project_record(row)['publicQuality']['fields'][field]['state'], 'under_review')


if __name__ == '__main__':
    unittest.main()
