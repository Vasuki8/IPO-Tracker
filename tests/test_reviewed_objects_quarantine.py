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


REGISTRY = json.loads((ROOT / 'data/verified_corrections.json').read_text())
ENTRIES = REGISTRY['reviewedObjects']
PREVIOUS = json.loads((ROOT / 'tests/fixtures/objects-source-review/previous-values.json').read_text())


def record(entry):
    value = copy.deepcopy(PREVIOUS[entry['identity']['id']])
    source = entry['source']
    proof = {'value': copy.deepcopy(value), 'sourceUrl': source['url'],
             'sha256': entry['evidence']['sha256'], 'documentType': 'PROSPECTUS',
             'parserVersion': 31, 'evidence': {'retained': 'old source-table evidence'}}
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
        entry = next(item for item in ENTRIES if item['identity']['id'] == 'genxai')
        row = record(entry)
        corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
        values, details = parser.extract_objects(
            '[PAGE 1]\nOBJECTS OF THE ISSUE\n(Rs. in Crores)\nParticulars Amount\n'
            'Working capital requirements 10.00\nGeneral corporate purposes 5.00\nTotal 15.00\n')
        parsed = {'objectsOfIssue': values, 'fieldEvidence': details}
        self.assertTrue(values)
        self.assertEqual(policy.apply_final_prospectus_static_fields(
            row, parsed, entry['source'], sha256=entry['evidence']['sha256']), [])
        self.assertIsNone(row['objectsOfIssue'])
        later_source = {**entry['source'], 'url': 'https://www.sebi.gov.in/corrected-final-prospectus.pdf'}
        policy.apply_final_prospectus_static_fields(
            row, parsed, later_source, sha256=entry['evidence']['sha256'])
        self.assertIsNone(row['objectsOfIssue'])
        policy.apply_final_prospectus_static_fields(row, parsed, later_source, sha256='a' * 64)
        self.assertEqual(row['objectsOfIssue'], values)
        self.assertEqual(row['objectsOfIssueReview']['status'], 'resolved')
        self.assertEqual(row['objectsOfIssueReview']['snapshot']['before'], PREVIOUS['genxai'])
        # An older rejected source cannot undo a later accepted replacement.
        policy.apply_final_prospectus_static_fields(row, parsed, entry['source'], sha256=entry['evidence']['sha256'])
        self.assertEqual(row['staticFieldProvenance']['objectsOfIssue']['sourceUrl'], later_source['url'])

    def test_value_scoped_layout_review_allows_corrected_allocations_from_same_document(self):
        entry = next(item for item in ENTRIES if item['identity']['id'] == 'teamtech')
        row = record(entry)
        corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
        values, details = parser.extract_objects((ROOT / 'tests/fixtures/objects-source-acceptance/teamtech.txt').read_text())
        self.assertEqual([item['amountCr'] for item in values], [11.9235, 15.5, 13.7688, 4.2936])
        policy.apply_final_prospectus_static_fields(
            row, {'objectsOfIssue': values, 'fieldEvidence': details}, entry['source'], sha256=entry['evidence']['sha256'])
        self.assertEqual(row['objectsOfIssue'], values)
        self.assertEqual(row['objectsOfIssueReview']['status'], 'resolved')

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
        before = copy.deepcopy(rows)
        self.assertEqual(corrections.apply({'ipos': rows}, self.registry()), (0, []))
        self.assertEqual(rows, before)

    def test_changed_issuer_offer_or_source_preserves_record(self):
        for key in ('company', 'symbol', 'openDate', 'sourceUrl', 'sha256', 'value'):
            with self.subTest(key=key):
                entry = ENTRIES[0]
                row = record(entry)
                if key in ('company', 'symbol', 'openDate'):
                    row[key] = 'different'
                else:
                    row['staticFieldProvenance']['objectsOfIssue'][key] = 'different'
                before = copy.deepcopy(row)
                applied, conflicts = corrections.apply({'ipos': [row]}, {'reviewedObjects': [entry]})
                self.assertEqual(applied, 0)
                self.assertEqual(len(conflicts), 1)
                self.assertEqual(row, before)

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
