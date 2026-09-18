import copy
import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import apply_corrections as corrections
import build_company_pages as pages
import build_missing_queue as queue
import enforce_final_prospectus_policy as enforcement
import final_prospectus_policy as policy
import p4_offer_parser as parser
import publish_transaction as publication
import run_offer_documents as documents


REGISTRY = json.loads((ROOT / 'data/verified_corrections.json').read_text())
ENTRIES = REGISTRY['reviewedObjects']
PREVIOUS = json.loads((ROOT / 'tests/fixtures/objects-source-review/previous-values.json').read_text())
CURRENT_CI = {
    row['id']: row for row in json.loads(
        (ROOT / 'tests/fixtures/objects-source-review/new-document-ci-records.json').read_text()
    )['records']
}


def record(entry):
    value = copy.deepcopy(PREVIOUS[entry['identity']['id']])
    source = entry['source']
    proof = {'value': copy.deepcopy(value), 'sourceUrl': source['url'],
             'sha256': entry['evidence']['sha256'], 'documentType': 'PROSPECTUS',
             'parserVersion': 31, 'issueOpenDate': entry['identity']['openDate'],
             'evidence': {'retained': 'old source-table evidence'}}
    return {
        **entry['identity'], 'objectsOfIssue': value,
        'leadManagers': ['Previously Verified Manager Limited'], 'lotSize': 100,
        'documents': [copy.deepcopy(source)],
        'staticFieldProvenance': {'objectsOfIssue': proof, 'lotSize': {'value': 100}},
        'documentFieldProvenance': {'sourceUrl': source['url'], 'sha256': proof['sha256'],
                                    'evidence': {'objectsOfIssue': copy.deepcopy(proof['evidence']),
                                                 'leadManagers': {'page': 2}}},
        'offerDocumentExtraction': {'status': 'extracted', 'parserVersion': 31,
                                    'canonicalFields': ['objectsOfIssue', 'lotSize'],
                                    'extractedFields': ['objectsOfIssue', 'lotSize']},
        'dataCorrections': [{'field': 'lotSize', 'before': None, 'after': 100}],
    }


class ReviewedObjectsQuarantineTests(unittest.TestCase):
    def registry(self):
        return {'revision': REGISTRY['revision'], 'reviewedObjects': copy.deepcopy(ENTRIES)}

    def old_teamtech_quarantine(self, *, mirrored=False):
        entry = copy.deepcopy(next(item for item in ENTRIES if item['identity']['id'] == 'teamtech'))
        old_entry = copy.deepcopy(entry)
        old_entry['scope'] = 'value'
        old_entry['reviewedAt'] = '2026-09-17T18:54:04+00:00'
        old_entry['findings'] = old_entry['findings'][:1]
        old_entry['evidence'].pop('sourceUnitReview', None)
        if mirrored:
            old_entry['source']['url'] = 'https://www.sebi.gov.in/mirrored-teamtech-prospectus.pdf'
        row = record(old_entry)
        self.assertEqual(corrections.apply({'ipos': [row]}, {'reviewedObjects': [old_entry]}), (1, []))
        self.assertIsNone(row['objectsOfIssue'])
        return row, entry

    def test_source_review_overrides_a_structurally_valid_legacy_proof(self):
        entry = next(item for item in ENTRIES if item['identity']['id'] == 'blackbuck')
        row = record(entry)
        proof = json.loads((ROOT / 'tests/fixtures/objects-source-review/blackbuck-previous-proof.json').read_text())
        row['staticFieldProvenance']['objectsOfIssue'] = proof
        self.assertTrue(enforcement._retained_objects_proof(row))
        ordinary = copy.deepcopy(row)
        enforcement._quarantine_invalid_objects(ordinary, entry['reviewedAt'])
        self.assertEqual(ordinary['objectsOfIssue'], row['objectsOfIssue'])
        self.assertEqual(corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]}), (1, []))
        self.assertIsNone(row['objectsOfIssue'])
        self.assertEqual(row['objectsOfIssueReview']['snapshot']['sourceEvidence'], proof)

    def test_consistent_table_does_not_resolve_a_reviewed_document_contradiction(self):
        entry = next(item for item in ENTRIES if item['identity']['id'] == 'genxai')
        row = record(entry)
        proof = json.loads((ROOT / 'tests/fixtures/objects-source-review/genxai-previous-proof.json').read_text())
        row['staticFieldProvenance']['objectsOfIssue'] = proof
        corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
        parsed = {'objectsOfIssue': copy.deepcopy(proof['value']),
                  'fieldEvidence': {'objectsOfIssue': copy.deepcopy(proof['evidence'])}}
        self.assertIn('objectsOfIssue', policy._static_values(row, parsed))
        self.assertEqual(policy.apply_final_prospectus_static_fields(
            row, parsed, entry['source'], sha256=entry['evidence']['sha256']), [])
        self.assertIsNone(row['objectsOfIssue'])
        self.assertEqual(row['objectsOfIssueReview']['status'], 'quarantined')
        self.assertNotIn('objectsOfIssue', row['staticFieldProvenance'])

    def test_changed_table_in_same_reviewed_document_remains_blocked_but_new_document_can_resolve(self):
        values, details = parser.extract_objects(
            '[PAGE 1]\nOBJECTS OF THE ISSUE\n(Rs. in Crores)\nParticulars Amount\n'
            'Working capital requirements 10.00\nGeneral corporate purposes 5.00\nTotal 15.00\n')
        parsed = {'objectsOfIssue': values, 'fieldEvidence': details}
        self.assertTrue(values)
        for entry in ENTRIES:
            if entry['scope'] != 'document':
                continue
            identifier = entry['identity']['id']
            with self.subTest(id=identifier):
                row = copy.deepcopy(CURRENT_CI[identifier]) if identifier in CURRENT_CI else record(entry)
                corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
                snapshot = copy.deepcopy(row['objectsOfIssueReview']['snapshot'])
                history = copy.deepcopy(row['dataCorrections'])
                self.assertEqual(policy.apply_final_prospectus_static_fields(
                    row, parsed, entry['source'], sha256=entry['evidence']['sha256']), [])
                self.assertIsNone(row['objectsOfIssue'])
                later_source = {**entry['source'], 'url': 'https://www.sebi.gov.in/corrected-final-prospectus.pdf'}
                policy.apply_final_prospectus_static_fields(
                    row, parsed, later_source, sha256=entry['evidence']['sha256'])
                self.assertIsNone(row['objectsOfIssue'])
                self.assertNotIn('objectsOfIssue', row['staticFieldProvenance'])
                self.assertEqual(row['objectsOfIssueReview']['status'], 'quarantined')
                policy.apply_final_prospectus_static_fields(row, parsed, later_source, sha256='a' * 64)
                self.assertEqual(row['objectsOfIssue'], values)
                self.assertEqual(row['objectsOfIssueReview']['status'], 'resolved')
                self.assertEqual(row['objectsOfIssueReview']['snapshot'], snapshot)
                self.assertEqual(snapshot['before'], PREVIOUS[identifier])
                self.assertEqual(row['dataCorrections'], history)
                # An older rejected source cannot undo a later accepted replacement.
                policy.apply_final_prospectus_static_fields(
                    row, parsed, entry['source'], sha256=entry['evidence']['sha256'])
                self.assertEqual(row['staticFieldProvenance']['objectsOfIssue']['sourceUrl'], later_source['url'])

    def test_current_ci_allocations_preserve_complete_proofs_and_correction_history_when_withheld(self):
        for identifier, original in CURRENT_CI.items():
            with self.subTest(id=identifier):
                entry = next(item for item in ENTRIES if item['identity']['id'] == identifier)
                row = copy.deepcopy(original)
                self.assertTrue(enforcement._retained_objects_proof(row))
                self.assertEqual(corrections.fingerprint(row['objectsOfIssue']), entry['beforeHash'])
                self.assertEqual(corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]}), (1, []))
                self.assertIsNone(row['objectsOfIssue'])
                snapshot = row['objectsOfIssueReview']['snapshot']
                self.assertEqual(snapshot['before'], original['objectsOfIssue'])
                self.assertEqual(snapshot['sourceEvidence'], original['staticFieldProvenance']['objectsOfIssue'])
                self.assertEqual(snapshot['documentProvenance'], original['documentFieldProvenance'])
                self.assertEqual(snapshot['documentEvidence'], original['documentFieldProvenance']['evidence']['objectsOfIssue'])
                self.assertEqual(snapshot['extractionEvidence'], {'offerDocumentExtraction': original['offerDocumentExtraction']})
                self.assertEqual(snapshot['reviewedSource']['scope'], 'document')
                self.assertEqual(snapshot['reviewedSource']['evidence'], entry['evidence'])
                self.assertEqual(row['dataCorrections'], original['dataCorrections'] + [snapshot])
                self.assertEqual(row['staticFieldProvenance'], {
                    key: value for key, value in original['staticFieldProvenance'].items() if key != 'objectsOfIssue'
                })
                expected_document = copy.deepcopy(original['documentFieldProvenance'])
                expected_document['evidence'].pop('objectsOfIssue')
                self.assertEqual(row['documentFieldProvenance'], expected_document)
                expected_extraction = copy.deepcopy(original['offerDocumentExtraction'])
                for key in ('canonicalFields', 'extractedFields'):
                    expected_extraction[key].remove('objectsOfIssue')
                self.assertEqual(row['offerDocumentExtraction'], expected_extraction)
                affected = {'objectsOfIssue', 'objectsOfIssueReview', 'staticFieldProvenance',
                            'documentFieldProvenance', 'offerDocumentExtraction', 'dataCorrections'}
                self.assertEqual({key: value for key, value in row.items() if key not in affected},
                                 {key: value for key, value in original.items() if key not in affected})
                once = copy.deepcopy(row)
                self.assertEqual(corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]}), (0, []))
                self.assertEqual(row, once)

    def test_publication_reviews_matching_new_allocations_collected_from_initially_null_fields(self):
        for identifier, original in CURRENT_CI.items():
            with self.subTest(id=identifier):
                entry = next(item for item in ENTRIES if item['identity']['id'] == identifier)
                registry = {'reviewedObjects': [entry]}
                base = {'ipos': [{**entry['identity'], 'objectsOfIssue': None,
                                 'documents': copy.deepcopy(original['documents']),
                                 'dataCorrections': copy.deepcopy(original['dataCorrections'][:-1])}]}
                self.assertEqual(original['dataCorrections'][-1]['field'], 'objectsOfIssue')
                self.assertEqual(corrections.apply(base, registry), (0, []))
                self.assertNotIn('objectsOfIssueReview', base['ipos'][0])
                proposed = copy.deepcopy(base)
                proof = original['staticFieldProvenance']['objectsOfIssue']
                parsed = {'objectsOfIssue': copy.deepcopy(proof['value']),
                          'fieldEvidence': {'objectsOfIssue': copy.deepcopy(proof['evidence'])}}
                extraction = original['offerDocumentExtraction']
                documents.correct_record(proposed['ipos'][0], parsed, entry['source'], proof['sha256'],
                                         extraction['pagesRead'], extraction['pageCount'])
                self.assertEqual(proposed['ipos'][0]['objectsOfIssue'], original['objectsOfIssue'])
                # The initial null field had no snapshot. Ordinary table policy
                # alone cannot discover the externally reviewed contradiction.
                enforcement.apply_policy(proposed)
                self.assertEqual(proposed['ipos'][0]['objectsOfIssue'], original['objectsOfIssue'])
                current = copy.deepcopy(base)
                current['ipos'][0]['subscription'] = {'total': 2.5}
                concurrent_audit = {'field': 'subscription', 'before': None, 'after': {'total': 2.5}}
                current['ipos'][0]['dataCorrections'].append(concurrent_audit)
                merged, conflicts = publication.merge_payload(base, proposed, current)
                self.assertEqual(conflicts, [])
                history = copy.deepcopy(merged['ipos'][0]['dataCorrections'])
                collected_proof = copy.deepcopy(merged['ipos'][0]['staticFieldProvenance']['objectsOfIssue'])
                self.assertEqual(corrections.apply(merged, registry), (1, []))
                enforcement.apply_policy(merged)
                row = merged['ipos'][0]
                self.assertIsNone(row['objectsOfIssue'])
                self.assertEqual(row['objectsOfIssueReview']['status'], 'quarantined')
                self.assertEqual(row['objectsOfIssueReview']['snapshot']['sourceEvidence'], collected_proof)
                self.assertEqual(row['dataCorrections'][:-1], history)
                self.assertIn(concurrent_audit, row['dataCorrections'])
                self.assertEqual(row['subscription'], {'total': 2.5})
                self.assertIn('offer.objectsOfIssue', queue.queue_entry(row, date(2026, 9, 17))['missingFields'])
                self.assertFalse(pages.public_profile_record(row).get('objectsOfIssue'))

    def test_teamtech_complete_table_cannot_resolve_the_document_unit_conflict(self):
        entry = next(item for item in ENTRIES if item['identity']['id'] == 'teamtech')
        row = record(entry)
        corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
        values, details = parser.extract_objects((ROOT / 'tests/fixtures/objects-source-acceptance/teamtech.txt').read_text())
        self.assertEqual([item['amountCr'] for item in values], [11.9235, 15.5, 13.7688, 4.2936])
        policy.apply_final_prospectus_static_fields(
            row, {'objectsOfIssue': values, 'fieldEvidence': details}, entry['source'], sha256=entry['evidence']['sha256'])
        self.assertIsNone(row['objectsOfIssue'])
        self.assertEqual(row['objectsOfIssueReview']['status'], 'quarantined')
        self.assertEqual(row['objectsOfIssueReview']['snapshot']['reviewedSource']['scope'], 'document')

    def test_document_scope_upgrade_preserves_retained_snapshot_and_blocks_same_pdf_repair(self):
        values, details = parser.extract_objects((ROOT / 'tests/fixtures/objects-source-acceptance/teamtech.txt').read_text())
        self.assertEqual([item['amountCr'] for item in values], [11.9235, 15.5, 13.7688, 4.2936])
        for mirrored in (False, True):
            with self.subTest(mirrored=mirrored):
                row, entry = self.old_teamtech_quarantine(mirrored=mirrored)
                old_review = copy.deepcopy(row['objectsOfIssueReview'])
                snapshot_bytes = json.dumps(old_review['snapshot'], ensure_ascii=False)
                history_bytes = json.dumps(row['dataCorrections'], ensure_ascii=False)
                self.assertEqual(corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]}), (1, []))
                active = row['objectsOfIssueReview']['activeSourceReview']
                self.assertEqual(active['scope'], 'document')
                self.assertEqual(active['identity'], entry['identity'])
                self.assertEqual(active['evidence'], entry['evidence'])
                self.assertEqual({key: value for key, value in row['objectsOfIssueReview'].items()
                                  if key != 'activeSourceReview'}, old_review)
                self.assertEqual(json.dumps(row['dataCorrections'][:-1], ensure_ascii=False), history_bytes)
                revision = row['dataCorrections'][-1]
                self.assertEqual(revision['field'], 'objectsOfIssueReview.activeSourceReview')
                self.assertEqual(revision['before'], old_review['snapshot']['reviewedSource'])
                self.assertEqual(revision['after'], active)
                self.assertEqual(revision['correctedAt'], entry['reviewedAt'])
                once = copy.deepcopy(row)
                self.assertEqual(corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]}), (0, []))
                self.assertEqual(row, once)
                parsed = {'objectsOfIssue': values, 'fieldEvidence': details}
                self.assertEqual(policy.apply_final_prospectus_static_fields(
                    row, parsed, entry['source'], sha256=entry['evidence']['sha256']), [])
                self.assertIsNone(row['objectsOfIssue'])
                self.assertEqual(row['objectsOfIssueReview']['status'], 'quarantined')
                self.assertNotIn('objectsOfIssue', row['staticFieldProvenance'])
                self.assertEqual(row['dataCorrections'], once['dataCorrections'])
                self.assertEqual(json.dumps(row['objectsOfIssueReview']['snapshot'], ensure_ascii=False), snapshot_bytes)
                later_source = {**entry['source'], 'url': 'https://www.sebi.gov.in/corrected-teamtech-final.pdf'}
                policy.apply_final_prospectus_static_fields(row, parsed, later_source, sha256='a' * 64)
                self.assertEqual(row['objectsOfIssue'], values)
                self.assertEqual(row['objectsOfIssueReview']['status'], 'resolved')
                self.assertEqual(corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]}), (0, []))
                self.assertEqual(row['dataCorrections'], once['dataCorrections'])
                self.assertEqual(json.dumps(row['objectsOfIssueReview']['snapshot'], ensure_ascii=False), snapshot_bytes)
                policy.apply_final_prospectus_static_fields(row, parsed, entry['source'], sha256=entry['evidence']['sha256'])
                self.assertEqual(row['staticFieldProvenance']['objectsOfIssue']['sha256'], 'a' * 64)

    def test_null_scope_upgrade_requires_retained_allocation_and_exact_source_binding(self):
        mutations = (
            ('issueOpenDate', None), ('issueOpenDate', '2020-01-01'),
            ('documentType', 'RHP'), ('sourceUrl', 'http://example.test/source.pdf'),
            ('sha256', 'unknown'), ('sha256', 'b' * 64), ('value', []),
        )
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                row, entry = self.old_teamtech_quarantine()
                row['objectsOfIssueReview']['snapshot']['sourceEvidence'][key] = value
                before = copy.deepcopy(row)
                applied, conflicts = corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
                self.assertEqual(applied, 0)
                self.assertEqual(len(conflicts), 0 if key == 'sha256' and value == 'b' * 64 else 1)
                self.assertEqual(row, before)
        for retained in (None, []):
            with self.subTest(retained=retained):
                row, entry = self.old_teamtech_quarantine()
                row['objectsOfIssueReview']['snapshot']['before'] = retained
                row['objectsOfIssueReview']['snapshot']['sourceEvidence']['value'] = retained
                before = copy.deepcopy(row)
                applied, conflicts = corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
                self.assertEqual((applied, len(conflicts)), (0, 1))
                self.assertEqual(row, before)

    def test_stale_active_identity_cannot_prevent_correct_scope_upgrade(self):
        row, entry = self.old_teamtech_quarantine()
        stale = {**copy.deepcopy(row['objectsOfIssueReview']['snapshot']['reviewedSource']),
                 'scope': 'document', 'identity': {**entry['identity'], 'openDate': '2020-01-01'}}
        row['objectsOfIssueReview']['activeSourceReview'] = copy.deepcopy(stale)
        snapshot = copy.deepcopy(row['objectsOfIssueReview']['snapshot'])
        history = copy.deepcopy(row['dataCorrections'])
        self.assertEqual(corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]}), (1, []))
        self.assertEqual(row['objectsOfIssueReview']['activeSourceReview']['identity'], entry['identity'])
        self.assertEqual(row['objectsOfIssueReview']['snapshot'], snapshot)
        self.assertEqual(row['dataCorrections'][:-1], history)
        self.assertEqual(row['dataCorrections'][-1]['before'], stale)
        values, details = parser.extract_objects((ROOT / 'tests/fixtures/objects-source-acceptance/teamtech.txt').read_text())
        policy.apply_final_prospectus_static_fields(
            row, {'objectsOfIssue': values, 'fieldEvidence': details}, entry['source'], sha256=entry['evidence']['sha256'])
        self.assertIsNone(row['objectsOfIssue'])

    def test_malformed_active_overlay_cannot_shadow_existing_document_hold(self):
        entry = next(item for item in ENTRIES if item['identity']['id'] == 'teamtech')
        values, details = parser.extract_objects((ROOT / 'tests/fixtures/objects-source-acceptance/teamtech.txt').read_text())
        active = {'scope': 'document', 'identity': copy.deepcopy(entry['identity']),
                  'evidence': copy.deepcopy(entry['evidence'])}
        overlays = (
            {**active, 'scope': 'value'}, {**active, 'evidence': {'sha256': 'b' * 64}},
            {**active, 'evidence': {'sha256': 'unknown'}}, {**active, 'evidence': []},
            {**active, 'identity': {**entry['identity'], 'company': 'Another Issuer Limited'}},
            {**active, 'identity': []}, ['malformed overlay'],
        )
        for overlay in overlays:
            with self.subTest(overlay=overlay):
                row = record(entry)
                corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
                row['objectsOfIssueReview']['activeSourceReview'] = copy.deepcopy(overlay)
                policy.apply_final_prospectus_static_fields(
                    row, {'objectsOfIssue': values, 'fieldEvidence': details}, entry['source'], sha256=entry['evidence']['sha256'])
                self.assertIsNone(row['objectsOfIssue'])
                self.assertEqual(row['objectsOfIssueReview']['status'], 'quarantined')

    def test_document_review_requires_real_document_and_value_digest_shapes(self):
        for key in ('sha256', 'beforeHash'):
            for value in (None, 'unknown', 'a' * 63, 'A' * 64, 123):
                with self.subTest(key=key, value=value):
                    entry = copy.deepcopy(next(item for item in ENTRIES if item['identity']['id'] == 'teamtech'))
                    row = record(entry)
                    if key == 'sha256':
                        entry['evidence'][key] = value
                    else:
                        entry[key] = value
                    before = copy.deepcopy(row)
                    with self.assertRaises(ValueError):
                        corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
                    self.assertEqual(row, before)

    def test_exact_reviewed_values_are_withheld_with_complete_previous_proofs(self):
        rows = [record(entry) for entry in ENTRIES]
        before = copy.deepcopy(rows)
        self.assertEqual(corrections.apply({'ipos': rows}, self.registry()), (len(ENTRIES), []))
        for old, row, entry in zip(before, rows, ENTRIES):
            with self.subTest(id=row['id']):
                self.assertEqual(corrections.fingerprint(old['objectsOfIssue']), entry['beforeHash'])
                self.assertIsNone(row['objectsOfIssue'])
                review = row['objectsOfIssueReview']
                self.assertEqual(review['status'], 'quarantined')
                self.assertEqual(review['reviewKind'], 'source-review')
                snapshot = review['snapshot']
                self.assertEqual(snapshot['before'], old['objectsOfIssue'])
                self.assertEqual(snapshot['sourceEvidence'], old['staticFieldProvenance']['objectsOfIssue'])
                self.assertEqual(snapshot['documentProvenance'], old['documentFieldProvenance'])
                self.assertEqual(snapshot['reviewedSource']['evidence'], entry['evidence'])
                self.assertEqual(snapshot['findings'], entry['findings'])
                self.assertEqual(row['dataCorrections'][:-1], old['dataCorrections'])
                self.assertNotIn('objectsOfIssue', row['staticFieldProvenance'])
                self.assertNotIn('objectsOfIssue', row['documentFieldProvenance']['evidence'])
                self.assertEqual(row['documentFieldProvenance']['evidence']['leadManagers'], {'page': 2})
                self.assertEqual(row['offerDocumentExtraction']['canonicalFields'], ['lotSize'])
                self.assertEqual(row['offerDocumentExtraction']['extractedFields'], ['lotSize'])
                self.assertEqual(row['leadManagers'], old['leadManagers'])
                self.assertEqual(row['staticFieldProvenance']['lotSize'], {'value': 100})

    def test_repeated_application_preserves_one_audit_snapshot(self):
        payload = {'ipos': [record(entry) for entry in ENTRIES]}
        corrections.apply(payload, self.registry())
        once = copy.deepcopy(payload['ipos'])
        self.assertEqual(corrections.apply(payload, self.registry()), (0, []))
        self.assertEqual(payload['ipos'], once)
        enforcement.apply_policy(payload)
        for before, after in zip(once, payload['ipos']):
            self.assertEqual(after['dataCorrections'], before['dataCorrections'])
            self.assertEqual(after['objectsOfIssueReview'], before['objectsOfIssueReview'])

    def test_newer_allocation_repair_is_preserved(self):
        rows = [record(entry) for entry in ENTRIES]
        for row in rows:
            row['objectsOfIssue'] = [{'purpose': 'Reviewed later allocation', 'amountCr': 1.0}]
            row['staticFieldProvenance']['objectsOfIssue']['value'] = copy.deepcopy(row['objectsOfIssue'])
            if next(e for e in ENTRIES if e['identity']['id'] == row['id'])['scope'] == 'document':
                row['staticFieldProvenance']['objectsOfIssue']['sha256'] = 'b' * 64
        before = copy.deepcopy(rows)
        self.assertEqual(corrections.apply({'ipos': rows}, self.registry()), (0, []))
        self.assertEqual(rows, before)

    def test_changed_issuer_offer_or_source_preserves_record(self):
        for entry in ENTRIES:
            for key in ('id', 'company', 'symbol', 'openDate', 'sourceUrl', 'sha256', 'value'):
                with self.subTest(id=entry['identity']['id'], key=key):
                    row = record(entry)
                    if key in ('id', 'company', 'symbol', 'openDate'):
                        row[key] = 'different'
                    else:
                        row['staticFieldProvenance']['objectsOfIssue'][key] = 'different'
                    before = copy.deepcopy(row)
                    applied, conflicts = corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
                    self.assertEqual(applied, 0)
                    self.assertEqual(len(conflicts), 1)
                    self.assertEqual(row, before)

    def test_document_review_withholds_initial_changed_allocation_and_mirror_without_snapshot(self):
        for entry in ENTRIES:
            if entry['scope'] != 'document':
                continue
            for mirrored in (False, True):
                with self.subTest(id=entry['identity']['id'], mirrored=mirrored):
                    row = record(entry)
                    row['objectsOfIssue'] = [{'purpose': 'A different extraction from the reviewed document', 'amountCr': 10.0}]
                    proof = row['staticFieldProvenance']['objectsOfIssue']
                    proof['value'] = copy.deepcopy(row['objectsOfIssue'])
                    if mirrored:
                        proof['sourceUrl'] = 'https://www.sebi.gov.in/mirrored-prospectus.pdf'
                    before = copy.deepcopy(row)
                    self.assertNotIn('objectsOfIssueReview', row)
                    self.assertEqual(corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]}), (1, []))
                    self.assertIsNone(row['objectsOfIssue'])
                    snapshot = row['objectsOfIssueReview']['snapshot']
                    self.assertEqual(snapshot['before'], before['objectsOfIssue'])
                    self.assertEqual(snapshot['sourceEvidence'], before['staticFieldProvenance']['objectsOfIssue'])
                    self.assertEqual(row['dataCorrections'], before['dataCorrections'] + [snapshot])

    def test_document_review_requires_matching_field_offer_date_and_final_document(self):
        entry = next(item for item in ENTRIES if item['identity']['id'] == 'teamtech')
        for key, value in (('issueOpenDate', None), ('issueOpenDate', '2020-01-01'),
                           ('documentType', 'RHP'), ('sourceUrl', 'http://example.test/source.pdf')):
            with self.subTest(key=key, value=value):
                row = record(entry)
                row['staticFieldProvenance']['objectsOfIssue'][key] = value
                before = copy.deepcopy(row)
                applied, conflicts = corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
                self.assertEqual(applied, 0)
                self.assertEqual(len(conflicts), 1)
                self.assertEqual(row, before)

    def test_value_review_preserves_new_allocation_and_does_not_inherit_document_scope(self):
        entry = next(item for item in ENTRIES if item['identity']['id'] == 'unimech')
        row = record(entry)
        corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
        values, details = parser.extract_objects(
            '[PAGE 1]\nOBJECTS OF THE ISSUE\n(Rs. in Crores)\nParticulars Amount\n'
            'Working capital requirements 10.00\nGeneral corporate purposes 5.00\nTotal 15.00\n')
        policy.apply_final_prospectus_static_fields(
            row, {'objectsOfIssue': values, 'fieldEvidence': details}, entry['source'], sha256=entry['evidence']['sha256'])
        self.assertEqual(row['objectsOfIssue'], values)
        self.assertEqual(row['objectsOfIssueReview']['status'], 'resolved')
        self.assertEqual(corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]}), (0, []))
        self.assertEqual(row['objectsOfIssue'], values)

    def test_missing_identity_or_non_final_source_cannot_trigger_review(self):
        for mutation in ('identity', 'source'):
            entry = copy.deepcopy(ENTRIES[0])
            row = record(entry)
            if mutation == 'identity':
                entry['identity'].pop('openDate')
            else:
                entry['source']['type'] = 'RHP'
                entry['source']['title'] = 'Red Herring Prospectus'
                entry['source']['url'] = 'https://example.com/rhp.pdf'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})

    def test_withheld_objects_remain_queued_and_are_absent_from_public_profile(self):
        payload = {'ipos': [record(entry) for entry in ENTRIES]}
        corrections.apply(payload, self.registry())
        enforcement.apply_policy(payload)
        for row in payload['ipos']:
            with self.subTest(id=row['id']):
                self.assertIn('offer.objectsOfIssue', queue.queue_entry(row, date(2026, 9, 17))['missingFields'])
                self.assertFalse(pages.public_profile_record(row).get('objectsOfIssue'))
                self.assertNotIn('dataCorrections', pages.public_profile_record(row))


if __name__ == '__main__':
    unittest.main()
