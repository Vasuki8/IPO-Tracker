import copy
from datetime import date, datetime, timezone
import gzip
import hashlib
import json
import re
import unittest
from unittest.mock import patch

from bse_active_offer_helpers import cohort, EXPECTED, FIXTURES, sources
from bse_active_offer_terms import parse_response, VERSION
from active_offer_terms import accepted_terms, validate_receipt, receipt_problems
from apply_corrections import apply
from audit_data_completeness import expected_exchange_rules
from build_company_pages import public_profile_record, public_summary_record
from public_quality import project_record
from reviewed_corrections import prepare, validate_scope, validate_records
from reviewed_evidence import index_groups
from publish_transaction import merge_payload
from validate_data import validate_payload
from publication_mode import push_mode, source_preview_mode

TODAY = date(2026, 9, 19)


class BseActiveOfferTermsTests(unittest.TestCase):
    def setUp(self):
        self.payload, self.registry, self.groups = cohort()
        self.ids = [group['identity']['id'] for group in self.groups]
        self.source = sources()
        self.rows = {row['id']: row for row in self.payload['ipos']}
        for module in ('active_offer_terms', 'public_quality'):
            clock = self.enterContext(patch(module + '.datetime', wraps=datetime))
            clock.now.return_value = datetime(2026, 9, 19, 6, tzinfo=timezone.utc)

    def candidate(self):
        return prepare(self.payload, self.registry, self.groups, self.ids)

    def test_four_real_pairs_supply_twelve_distinct_values_and_only_four_core_gaps(self):
        def gaps(rows):
            return sum(not predicate(row) for row in rows for _, predicate in expected_exchange_rules(row, TODAY))
        candidate = self.candidate()
        self.assertEqual((gaps(self.payload['ipos']), gaps(candidate['ipos'])), (25, 21))
        for row in candidate['ipos']:
            if row['id'] not in EXPECTED:
                self.assertEqual(row, self.rows[row['id']]); continue
            low, high, market, minimum = EXPECTED[row['id']]
            fields = {'priceBand': {'min': low, 'max': high}, 'marketLot': market, 'minimumBidQuantity': minimum}
            for output in (project_record(row, today=TODAY), public_summary_record(row), public_profile_record(row)):
                for field, value in fields.items():
                    self.assertEqual(output[field], value)
                    self.assertEqual(output['publicQuality']['fields'][field]['state'], 'provisional')
                for field in ('symbol', 'lotSize', 'issueSizeCr', 'issueComposition', 'minimumApplicationAmount'):
                    self.assertIsNone(output.get(field))
            for field in fields:
                self.assertIsNone(row.get(field))
        self.assertEqual(validate_payload(self.payload)['reviewCount'], validate_payload(candidate)['reviewCount'])
        self.assertEqual(validate_payload(candidate)['errorCount'], 0)

    def test_source_bytes_clocks_index_identity_and_currency_are_retained(self):
        for row in self.candidate()['ipos']:
            if row['id'] not in EXPECTED: continue
            receipt = row['activeOfferTerms']; source = receipt['source']
            self.assertIsNone(source['observedAt']); self.assertIsNone(source['index']['observedAt'])
            self.assertNotEqual(source['collectedAt'], source['index']['collectedAt'])
            self.assertEqual(hashlib.sha256(gzip.decompress((FIXTURES / (row['id'] + '.html.gz')).read_bytes())).hexdigest(), source['sha256'])
            self.assertEqual(receipt['sourceIdentity']['board'], 'SME')
            self.assertTrue(receipt['sourceIdentity']['symbol'])
            self.assertNotIn('symbol', receipt['identity'])
            for field, proof in receipt['fields'].items():
                self.assertEqual(proof['row'], {'priceBand': 9, 'marketLot': 15, 'minimumBidQuantity': 16}[field])
                self.assertEqual(proof['table'], '/html/tables/2')
        self.assertEqual(hashlib.sha256(gzip.decompress((FIXTURES / 'rupee.gif.gz').read_bytes())).hexdigest(),
                         '780cc4f5c88a8c41047804b4fa764872b6648ed1df2927225996c5d1bca6a4bc')

    def test_empty_vivekanand_response_and_changed_band_remain_rejected(self):
        key = 'vivekanand-cotspin-limited'
        self.assertEqual(self.rows[key]['observations']['BSE']['priceBand'], {'min': 32, 'max': 37})
        self.assertIn('35.00 - 37.00', self.source[key]['index']['responseText'])
        with self.assertRaises(ValueError): parse_response(self.source[key], self.rows[key])
        self.assertNotIn(key, self.ids)

    def test_official_url_identity_and_page_conflicts_fail(self):
        key = self.ids[0]; original = self.source[key]; row = self.rows[key]
        mutations = [
            lambda s: s.update(url=s['url'].replace('beta.bseindia.com', 'beta.bseindia.com.evil.test')),
            lambda s: s.update(url=s['url'] + '&id=9999'),
            lambda s: s.update(url=s['url'].replace('id=4831', 'id=9999')),
            lambda s: s.update(url=s['url'].replace('type=IPO', 'type=FPO')),
            lambda s: s.update(responseText=s['responseText'].replace('>Equity<', '>Debt<')),
            lambda s: s.update(responseText=s['responseText'].replace('>FXML<', '>OTHER<')),
            lambda s: s.update(responseText=s['responseText'].replace('>FX MULTITECH LIMITED<', '>Another Company Limited<')),
            lambda s: s.update(responseText=s['responseText'].replace('21 Sep 2026 to 23 Sep 2026', '21 Sep 2026 to 24 Sep 2026')),
            lambda s: s.update(responseText=s['responseText'].replace('110.00-116.00', '110.00-117.00')),
            lambda s: s.update(responseText=s['responseText'].replace('rs_b.gif', 'usd.gif')),
            lambda s: s.update(responseText=s['responseText'].replace('All Prices in', 'Estimated Price')),
            lambda s: s['index'].update(responseText=s['index']['responseText'].replace('>SME<', '>Mainboard<')),
            lambda s: s['index'].update(responseText=s['index']['responseText'].replace('>IPO<', '>FPO<')),
        ]
        # A changed source symbol can be valid when canonical symbol is absent;
        # the immutable receipt's sourceIdentity still binds the accepted symbol.
        for index, mutate in enumerate(mutations):
            source = copy.deepcopy(original); mutate(source)
            with self.subTest(index=index):
                if index == 5:
                    self.assertEqual(parse_response(source, row)['sourceIdentity']['symbol'], 'OTHER')
                else:
                    with self.assertRaises((ValueError, KeyError)): parse_response(source, row)

    def test_duplicate_term_and_index_rows_cannot_silently_choose_one(self):
        key = self.ids[0]
        for target, pattern in [('responseText', r'<tr>\s*<td[^>]*>Market Lot</td>.*?</tr>'),
                                ('index', r'<tr>\s*<td[^>]*><a[^>]*>FX MULTITECH LIMITED</a>.*?</tr>')]:
            source = copy.deepcopy(self.source[key]); container = source if target == 'responseText' else source['index']
            text = container['responseText']; match = re.search(pattern, text, re.S)
            self.assertIsNotNone(match)
            container['responseText'] = text[:match.end()] + match[0] + text[match.end():]
            with self.assertRaises(ValueError): parse_response(source, self.rows[key])

    def test_missing_or_ambiguous_quantities_do_not_become_bid_lots_or_amounts(self):
        source = copy.deepcopy(self.source[self.ids[0]])
        source['responseText'] = source['responseText'].replace('>Market Lot<', '>Minimum Application Lot<')
        parsed = parse_response(source, self.rows[self.ids[0]])
        self.assertNotIn('marketLot', parsed['fields'])
        self.assertEqual(parsed['fields']['minimumBidQuantity']['value'], 2400)
        for field in ('lotSize', 'issueSizeCr', 'issueComposition', 'minimumApplicationAmount'):
            self.assertNotIn(field, parsed['fields'])
        source['responseText'] = source['responseText'].replace('>2400<', '>2,4,00<')
        self.assertNotIn('minimumBidQuantity', parse_response(source, self.rows[self.ids[0]])['fields'])

    def test_receipt_tampering_stays_rejected_after_rehashing_outer_proofs(self):
        for kind in ('price', 'row', 'unit', 'source_symbol', 'index_hash', 'observed', 'index_observed', 'version', 'canonical_symbol', 'bid_lot', 'review_clock'):
            groups, registry = copy.deepcopy(self.groups), copy.deepcopy(self.registry)
            group = groups[0]; receipt = group['proofs']['activeOfferTerms']['value']
            if kind == 'price': receipt['fields']['priceBand']['value']['max'] += 1
            elif kind == 'row': receipt['fields']['marketLot']['row'] += 1
            elif kind == 'unit': receipt['fields']['marketLot']['unit'] = 'INR'
            elif kind == 'source_symbol': receipt['sourceIdentity']['symbol'] = 'OTHER'
            elif kind == 'index_hash': receipt['source']['index']['sha256'] = 'a'*64
            elif kind == 'observed': receipt['source']['observedAt'] = receipt['source']['collectedAt']
            elif kind == 'index_observed': receipt['source']['index']['observedAt'] = receipt['source']['index']['collectedAt']
            elif kind == 'version': receipt['parserVersion'] = 'nse-labelled-active-terms-v1'
            elif kind == 'canonical_symbol': receipt['identity']['symbol'] = 'FXML'
            elif kind == 'bid_lot': receipt['fields']['lotSize'] = copy.deepcopy(receipt['fields']['marketLot'])
            else: receipt['review']['reviewedAt'] = '2026-09-19T05:34:00+00:00'
            registry['changes'][0]['after'] = copy.deepcopy(receipt)
            blob = (json.dumps(group['proofs'], ensure_ascii=False, indent=2) + '\n').encode()
            group['sourceProofsSha256'] = hashlib.sha256(blob).hexdigest()
            group['sourceProofsGitBlob'] = hashlib.sha1(b'blob ' + str(len(blob)).encode() + b'\0' + blob).hexdigest()
            with self.subTest(kind=kind), self.assertRaises((ValueError, KeyError)): index_groups(groups, registry)

    def test_later_canonical_symbol_conflict_and_changed_offer_fail(self):
        row = next(r for r in self.candidate()['ipos'] if r['id'] == self.ids[0])
        self.assertTrue(accepted_terms({**row, 'symbol': 'FXML'}, TODAY))
        for key, value in [('symbol', 'OTHER'), ('company', 'Different Company'), ('board', 'Mainboard'), ('closeDate', '2026-09-24')]:
            changed = {**row, key: value}
            self.assertFalse(accepted_terms(changed, TODAY)); self.assertTrue(receipt_problems(changed))

    def test_same_offer_conflicts_and_holds_win_without_erasing_receipt(self):
        row = next(r for r in self.candidate()['ipos'] if r['id'] == self.ids[0])
        for family in ('NSE', 'BSE'):
            changed = copy.deepcopy(row)
            changed['observations'][family] = {'openDate': row['openDate'], 'closeDate': row['closeDate'], 'marketLot': 2400}
            projected = project_record(changed, today=TODAY)
            self.assertIsNone(projected['marketLot']); self.assertEqual(projected['minimumBidQuantity'], 2400)
            self.assertEqual(projected['publicQuality']['fields']['marketLot']['state'], 'under_review')
        row['dataReview'] = {'minimumBidQuantity': 'Independent quantity evidence requires review'}
        out = project_record(row, today=TODAY)
        self.assertIsNone(out['minimumBidQuantity']); self.assertEqual(out['marketLot'], 1200)
        self.assertEqual(out['activeOfferTerms'], row['activeOfferTerms'])

    def test_ist_close_expiry_restores_the_price_gap_and_preserves_history(self):
        row = next(r for r in self.candidate()['ipos'] if r['id'] == self.ids[0])
        self.assertTrue(accepted_terms(row, date(2026, 9, 23)))
        expired = project_record(row, today=date(2026, 9, 24))
        for field in ('priceBand', 'marketLot', 'minimumBidQuantity'): self.assertIsNone(expired[field])
        self.assertEqual(expired['activeOfferTerms'], row['activeOfferTerms'])
        self.assertIn('priceBand', [key for key, predicate in expected_exchange_rules(row, date(2026, 9, 24)) if not predicate(row)])
        for status in ('closed', 'listed', 'withdrawn', 'cancelled'):
            self.assertFalse(accepted_terms({**row, 'status': status}, TODAY))

    def test_offline_bounded_transport_and_ordinary_apply_preserve_every_other_field(self):
        original = copy.deepcopy(self.payload)
        self.assertEqual(apply(self.payload, self.registry, evidence_groups=self.groups), (0, []))
        self.assertEqual(self.payload['ipos'], original['ipos'])
        with patch('requests.sessions.Session.request', side_effect=AssertionError('No collection')):
            candidate = self.candidate()
        validate_scope(self.payload, candidate, self.ids, groups=self.groups)
        for before, after in zip(original['ipos'], candidate['ipos']):
            for field in set(before) | set(after):
                if field not in {'activeOfferTerms', 'sources', 'dataCorrections'}:
                    self.assertEqual(before.get(field), after.get(field), field)
        bad = copy.deepcopy(candidate); row = next(r for r in bad['ipos'] if r['id'] == self.ids[0]); row['symbol'] = 'FXML'
        with self.assertRaises(ValueError): validate_scope(self.payload, bad, self.ids, groups=self.groups)
        row['symbol'] = 'OTHER'
        with self.assertRaises(ValueError): validate_records(bad, self.registry, self.groups, self.ids)

    def test_concurrent_receipt_stays_pending_as_a_whole(self):
        current = copy.deepcopy(self.payload)
        row = next(r for r in current['ipos'] if r['id'] == self.ids[0]); row['activeOfferTerms'] = {'different': 'evidence'}
        merged, conflicts = merge_payload(self.payload, self.candidate(), current)
        self.assertEqual(next(r for r in merged['ipos'] if r['id'] == self.ids[0])['activeOfferTerms'], row['activeOfferTerms'])
        self.assertTrue(any(c['path'] == ['ipos', self.ids[0], 'activeOfferTerms'] for c in conflicts))

    def test_support_and_request_routes_keep_collection_separate(self):
        files = ['scripts/bse_active_offer_terms.py', 'scripts/active_offer_terms.py', 'scripts/reviewed_evidence.py',
                 'scripts/public_quality.py', 'scripts/build_company_pages.py', 'scripts/publication_mode.py',
                 'company.js', 'app.js', 'data/verified_corrections.json', 'tests/fixtures/bse-active-offer-terms/index.html.gz']
        self.assertEqual(push_mode(files), 'review'); self.assertEqual(source_preview_mode(files), 'review')
        self.assertEqual(push_mode(files + ['scripts/update_data.py']), 'repair')
        with self.assertRaises(RuntimeError): push_mode(files + ['data/reviewed_publication_request.json'])


if __name__ == '__main__': unittest.main()
