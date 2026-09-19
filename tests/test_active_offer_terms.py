import copy
from datetime import date, datetime, timezone
import hashlib
import json
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from active_offer_helpers import cohort, FIXTURES
from active_offer_terms import accepted_terms, parse_response, receipt_problems, validate_receipt
from apply_corrections import apply
from audit_data_completeness import expected_exchange_rules
from public_quality import project_record
from reviewed_corrections import prepare, validate_records, validate_scope
from reviewed_evidence import index_groups
from publish_transaction import merge_payload
from validate_data import validate_payload, validate_record
from source_review_queue import review_task

TODAY = date(2026, 9, 19)


class ActiveOfferTermsTests(unittest.TestCase):
    def setUp(self):
        self.payload, self.registry, self.groups = cohort()
        self.ids = [row['id'] for row in self.payload['ipos']]
        for module in ('active_offer_terms', 'public_quality'):
            clock = self.enterContext(patch(module + '.datetime', wraps=datetime))
            clock.now.return_value = datetime(2026, 9, 19, 3, tzinfo=timezone.utc)

    def candidate(self):
        return prepare(self.payload, self.registry, self.groups, self.ids)

    def test_three_real_tables_have_nine_supported_gaps_and_no_calculated_total(self):
        expected = [(51, 54, 2000, 9398000), (140, 148, 101, None), (109, 115, 1200, 3846000)]
        candidate = self.candidate()
        for row, values in zip(candidate['ipos'], expected):
            out = project_record(row, today=TODAY)
            low, high, lot, fresh = values
            self.assertEqual(out['priceBand'], {'min': low, 'max': high})
            self.assertEqual(out['lotSize'], lot)
            self.assertEqual(out['issueComposition']['freshShares'], fresh)
            self.assertIsNone(out['issueSizeCr'])
            self.assertIsNone(out['marketLot'])
            for field in ('priceBand', 'lotSize', 'issueComposition'):
                self.assertIsNone(row.get(field))
                self.assertEqual(out['publicQuality']['fields'][field]['state'], 'provisional')
            missing = [name for name, predicate in expected_exchange_rules(row, TODAY) if not predicate(row)]
            self.assertEqual(missing, ['issueSizeCr'])
        varmora = project_record(candidate['ipos'][1], today=TODAY)
        self.assertEqual(varmora['minimumBidQuantity'], 101)
        self.assertEqual(varmora['issueComposition']['freshValueCr'], 320)
        self.assertEqual(varmora['issueComposition']['qualifiers'], {'freshValueCr': 'up_to', 'ofsShares': 'up_to'})
        for row in (candidate['ipos'][0], candidate['ipos'][2]):
            self.assertIsNone(project_record(row, today=TODAY)['minimumBidQuantity'])
            self.assertIsNone(project_record(row, today=TODAY)['issueComposition']['ofsShares'])

    def test_exact_source_hashes_rows_and_unknown_observation_survive_projection(self):
        for row in self.candidate()['ipos']:
            receipt = row['activeOfferTerms']; source = receipt['source']
            self.assertEqual(hashlib.sha256((FIXTURES / (row['id'] + '.json')).read_bytes()).hexdigest(), source['sha256'])
            out = project_record(row, today=TODAY)
            for field, proof in receipt['fields'].items():
                decision = out['publicQuality']['fields'][field]
                evidence = out['publicQuality']['sources'][decision['source']]
                self.assertIsNone(evidence['observedAt'])
                self.assertEqual(evidence['collectedAt'], source['collectedAt'])
                self.assertEqual(decision['row'], proof['row'])
                self.assertEqual(evidence['reviewUrl'], receipt['review']['url'])

    def test_parser_rejects_conflicting_duplicate_labels_and_identity_metadata(self):
        row = self.payload['ipos'][1]
        original = json.loads((FIXTURES / 'varmora.json').read_text())
        mutations = [lambda obj: obj['issueInfo']['dataList'].append({'title': 'Price Range', 'value': 'Rs.140 to Rs.150 per equity share'}),
                     lambda obj: obj.update(metaInfo={'symbol': 'OTHER', 'companyName': 'Other Issuer Limited', 'isDebtSec': True}),
                     lambda obj: obj['issueInfo'].update(heading='Other Issuer Limited'),
                     lambda obj: obj.update(series='SME'),
                     lambda obj: obj['issueInfo']['dataList'].append({'title': 'Lot Size', 'value': '202 Equity Shares'})]
        for mutate in mutations:
            raw = copy.deepcopy(original); mutate(raw)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                parse_response(json.dumps(raw), row)
        identity = {**row, 'openDate': '2026-09-21'}
        with self.assertRaises(ValueError): parse_response(json.dumps(original), identity)

    def test_unknown_units_and_minimum_only_do_not_become_lot_or_total(self):
        row = self.payload['ipos'][1]
        raw = json.loads((FIXTURES / 'varmora.json').read_text())
        rows = raw['issueInfo']['dataList']
        rows[:] = [item for item in rows if item['title'] != 'Bid Lot']
        next(item for item in rows if item['title'] == 'Issue Size')['value'] = 'Fresh issue 3,200 and OFS 26,217,634'
        next(item for item in rows if item['title'] == 'Price Range')['value'] = '140 to 148'
        parsed = parse_response(json.dumps(raw), row)
        self.assertEqual(set(parsed['fields']), {'minimumBidQuantity'})
        self.assertEqual(parsed['fields']['minimumBidQuantity']['value'], 101)

    def test_receipt_tampering_does_not_get_review_privilege_after_rehashing_wrapper(self):
        for kind in ('unit', 'row', 'value', 'hash', 'clock', 'review', 'url', 'board', 'amount'):
            group = copy.deepcopy(self.groups[0]); registry = copy.deepcopy(self.registry)
            receipt = group['proofs']['activeOfferTerms']['value']
            if kind in ('unit', 'row', 'value'): receipt['fields']['lotSize'][kind] = 'changed'
            elif kind == 'hash': receipt['source']['sha256'] = 'a'*64
            elif kind == 'clock': receipt['source']['observedAt'] = receipt['source']['collectedAt']
            elif kind == 'review': receipt['review']['status'] = 'parsed'
            elif kind == 'url': receipt['source']['url'] += '&series=EQ'
            elif kind == 'board': receipt['identity']['board'] = 'Mainboard'
            else: receipt['fields']['issueSizeCr'] = {'value': 50.7492}
            registry['changes'][0]['after'] = copy.deepcopy(receipt)
            blob = (json.dumps(group['proofs'], ensure_ascii=False, indent=2) + '\n').encode()
            group['sourceProofsSha256'] = hashlib.sha256(blob).hexdigest()
            with self.subTest(kind=kind), self.assertRaises((ValueError, KeyError)):
                index_groups([group], registry)

    def test_unaccepted_receipts_and_changed_offer_are_withheld(self):
        row = self.candidate()['ipos'][0]
        for key in ('company', 'symbol', 'board', 'openDate', 'closeDate'):
            changed = copy.deepcopy(row); changed[key] += '-wrong'
            self.assertFalse(accepted_terms(changed, TODAY))
            self.assertTrue(receipt_problems(changed))

    def test_active_and_timezone_expiry_boundary_preserves_receipt(self):
        row = self.candidate()['ipos'][0]
        self.assertTrue(accepted_terms(row, date(2026, 9, 22)))
        for instant in ('2026-09-22T18:29:59+00:00', '2026-09-22T18:30:00+00:00'):
            with patch('active_offer_terms.datetime', wraps=datetime) as clock:
                clock.now.return_value = datetime.fromisoformat(instant).astimezone(ZoneInfo('Asia/Kolkata'))
                self.assertEqual(bool(accepted_terms(row)), '18:29' in instant)
        for status in ('listed', 'closed', 'cancelled', 'withdrawn', 'drhp', 'unknown'):
            self.assertFalse(accepted_terms({**row, 'status': status}, TODAY))
        expired = project_record(row, today=date(2026, 9, 23))
        self.assertIsNone(expired['priceBand'])
        self.assertEqual(expired['activeOfferTerms'], row['activeOfferTerms'])
        missing = [key for key, predicate in expected_exchange_rules(row, date(2026, 9, 23)) if not predicate(row)]
        self.assertEqual(len(missing), 4)

    def test_both_exchange_conflicts_remain_reviews_with_pointers_and_unaffected_lots(self):
        for family in ('NSE', 'BSE'):
            row = self.candidate()['ipos'][1]
            observation = {'openDate': row['openDate'], 'closeDate': row['closeDate'], 'priceBand': {'min': 140, 'max': 150}}
            row['observations'][family] = observation
            out = project_record(row, today=TODAY)
            self.assertIsNone(out['priceBand'])
            self.assertEqual(out['publicQuality']['fields']['priceBand']['state'], 'under_review')
            self.assertEqual(out['lotSize'], 101)
            review = next(item for item in validate_record(row) if item['field'] == 'priceBand')
            self.assertEqual(review['severity'], 'review')
            self.assertIn('/activeOfferTerms', review_task(row, review)['evidencePaths'])
            self.assertEqual(review_task(row, review)['route'], 'manual-source-review')

    def test_manual_review_keeps_supported_field_held(self):
        row = self.candidate()['ipos'][0]
        row['dataReview'] = {'lotSize': 'Awaiting contradictory notice review'}
        out = project_record(row, today=TODAY)
        self.assertIsNone(out['lotSize'])
        self.assertEqual(out['publicQuality']['fields']['lotSize']['state'], 'under_review')
        self.assertIn('lotSize', [key for key, predicate in expected_exchange_rules(row, TODAY) if not predicate(row)])

    def test_ordinary_apply_is_inert_and_unscoped_receipt_is_forbidden(self):
        original = copy.deepcopy(self.payload['ipos'])
        count, conflicts = apply(self.payload, self.registry, evidence_groups=self.groups)
        self.assertEqual((count, conflicts), (0, []))
        self.assertEqual(self.payload['ipos'], original)
        for entry in self.registry['changes']: entry.pop('publicationScope')
        with self.assertRaises(ValueError): apply(self.payload, self.registry)

    def test_offline_bounded_publication_preserves_all_other_values_and_histories(self):
        before = copy.deepcopy(self.payload)
        with patch('requests.sessions.Session.request', side_effect=AssertionError('offline only')):
            candidate = self.candidate()
        validate_scope(before, candidate, self.ids, groups=self.groups)
        self.assertEqual(before, self.payload)
        for old, new in zip(before['ipos'], candidate['ipos']):
            for key in set(old) | set(new):
                if key not in {'activeOfferTerms', 'sources', 'dataCorrections'}:
                    self.assertEqual(old.get(key), new.get(key), key)
        self.assertEqual(validate_payload(candidate)['errorCount'], 0)
        self.assertEqual(validate_payload(before)['reviewCount'], validate_payload(candidate)['reviewCount'])
        accepted = copy.deepcopy(candidate['ipos'])
        self.assertEqual(apply(candidate, self.registry, evidence_groups=self.groups, explicit_review=True), (0, []))
        self.assertEqual(candidate['ipos'], accepted)

    def test_scope_proof_and_display_mismatches_fail_publication(self):
        candidate = self.candidate()
        for field in ('staticFieldProvenance', 'staticSourcePolicy', 'priceBand', 'financials'):
            changed = copy.deepcopy(candidate); changed['ipos'][0][field] = {'changed': True}
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_scope(self.payload, changed, self.ids, groups=self.groups)
        candidate['ipos'][1]['priceBand'] = {'min': 140, 'max': 150}
        with self.assertRaises(ValueError): validate_records(candidate, self.registry, self.groups, self.ids)
        self.payload['ipos'][0]['activeOfferTerms'] = {'a': 'newer receipt'}
        with self.assertRaises(ValueError): self.candidate()

    def test_concurrent_receipt_is_atomic_and_unaccepted_receipt_remains_pending(self):
        candidate = self.candidate(); current = copy.deepcopy(self.payload)
        current['ipos'][0]['activeOfferTerms'] = {'review': 'concurrent', 'source': 'different'}
        merged, conflicts = merge_payload(self.payload, candidate, current)
        self.assertEqual(merged['ipos'][0]['activeOfferTerms'], current['ipos'][0]['activeOfferTerms'])
        conflict = next(item for item in conflicts if item['path'] == ['ipos', 'axiomgas', 'activeOfferTerms'])
        self.assertEqual(conflict['proposed'], candidate['ipos'][0]['activeOfferTerms'])

    def test_core_observation_refresh_preserves_receipt_and_static_nulls(self):
        from run_update_final_policy import merge_fill_only, strip_static_canonical
        row = self.candidate()['ipos'][0]
        original = copy.deepcopy(row['activeOfferTerms'])
        incoming = {key: row[key] for key in ('id', 'company', 'symbol', 'exchange', 'board', 'openDate', 'closeDate')}
        incoming.update(priceBand={'min': 51, 'max': 54}, lotSize=2000,
                        observations={'NSE': {'openDate': row['openDate'], 'closeDate': row['closeDate']}})
        merge_fill_only(row, strip_static_canonical(incoming))
        self.assertEqual(row['activeOfferTerms'], original)
        self.assertIsNone(row.get('priceBand')); self.assertIsNone(row.get('lotSize'))
        self.assertEqual(project_record(row, today=TODAY)['priceBand'], {'min': 51, 'max': 54})


if __name__ == '__main__':
    unittest.main()
