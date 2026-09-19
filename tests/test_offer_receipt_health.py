"""The operator sees retained offer evidence without refreshing or accepting it."""
import copy
from datetime import date
import json
import unittest
from unittest.mock import patch

from active_offer_helpers import cohort
from test_update_health_report import health

AT = '2026-09-19T04:23:20Z'


class OfferReceiptHealthTests(unittest.TestCase):
    def setUp(self):
        self.payload, _, groups = cohort()
        for row, group in zip(self.payload['ipos'], groups):
            row['activeOfferTerms'] = copy.deepcopy(group['proofs']['activeOfferTerms']['value'])
        self.payload['meta'] = {'recordCount': 3, 'generatedAt': AT}

    def report(self, at=AT):
        before = copy.deepcopy(self.payload)
        with patch('requests.sessions.Session.request', side_effect=AssertionError('offline')):
            result = health.build_report(self.payload, {}, [], as_of=at)
        self.assertEqual(before, self.payload)
        return result

    def test_three_real_receipts_replay_without_freshness_or_publication_claim(self):
        report = self.report()
        self.assertEqual(report['summary']['retainedOfferReceipts'], 3)
        self.assertEqual(report['summary']['offerReceiptUnknownObservations'], 3)
        self.assertEqual(report['summary']['offerReceiptStates'], {'provisional': 3})
        for record, entry in zip(self.payload['ipos'], report['offerReceipts']):
            source = record['activeOfferTerms']['source']
            self.assertEqual(entry['source']['sha256'], source['sha256'])
            self.assertEqual(entry['receiptValidation'], 'replayed')
            self.assertEqual(entry['clocks']['observation']['state'], 'missing')
            self.assertEqual(entry['clocks']['collection']['stored'], source['collectedAt'])
            self.assertEqual(entry['clocks']['collection']['state'], 'recorded_only')
            self.assertIsNone(entry['acceptedAt'])
            self.assertIsNone(entry['publicationLag']['minutes'])
            self.assertEqual(entry['unresolved'], record['activeOfferTerms']['unresolved'])
            public = health.reconciliation.project_record(record, today=date(2026, 9, 19), holds=[])['publicQuality']
            for field, decision in entry['publicFields'].items():
                self.assertEqual(decision['state'], public['fields'][field]['state'])
            self.assertNotIn('responseText', json.dumps(entry))

    def test_collection_review_build_and_general_source_times_do_not_supply_observation(self):
        first = self.report()['offerReceipts']
        self.payload['meta'].update(generatedAt='2026-09-19T04:22:00Z',
            sourceHealth={'NSE-live': {'ok': True, 'checkedAt': AT, 'observedAt': AT}})
        for row in self.payload['ipos']:
            row['activeOfferTerms']['source']['collectedAt'] = '2026-09-19T04:20:00Z'
            row['activeOfferTerms']['review']['reviewedAt'] = '2026-09-19T04:21:00Z'
        for previous, entry in zip(first, self.report()['offerReceipts']):
            self.assertEqual(previous['clocks']['observation'], entry['clocks']['observation'])
            self.assertNotEqual(previous['clocks']['collection'], entry['clocks']['collection'])

    def test_expiry_is_at_ist_midnight_and_does_not_remove_receipts_or_unresolved_fields(self):
        before = self.report('2026-09-22T18:29:59Z')['offerReceipts']
        after = self.report('2026-09-22T18:30:00Z')['offerReceipts']
        self.assertEqual(before[0]['state'], 'provisional')
        self.assertEqual(after[0]['state'], 'expired')
        self.assertEqual(after[0]['provisionalFields'], [])
        self.assertEqual(before[0]['receiptSha256'], after[0]['receiptSha256'])
        self.assertEqual(before[0]['unresolved'], after[0]['unresolved'])
        self.assertEqual(after[1]['state'], 'provisional')
        expired = self.report('2026-09-26T00:00:00Z')
        self.assertEqual(expired['summary']['offerReceiptStates'], {'expired': 3})

    def test_holds_and_conflicts_override_replayed_fields(self):
        row = self.payload['ipos'][0]
        row['dataReview'] = {'lotSize': 'Awaiting official notice review'}
        entry = self.report()['offerReceipts'][0]
        self.assertEqual(entry['state'], 'partially_withheld')
        self.assertEqual(entry['publicFields']['lotSize']['state'], 'under_review')
        self.assertNotIn('lotSize', entry['provisionalFields'])
        row['observations']['BSE'] = {'openDate': row['openDate'], 'closeDate': row['closeDate'],
                                      'priceBand': {'min': 51, 'max': 55}}
        entry = self.report()['offerReceipts'][0]
        self.assertEqual(entry['state'], 'review_required')
        self.assertIn('priceBand', entry['issues'])
        self.assertNotIn('priceBand', entry['provisionalFields'])

    def test_invalid_null_and_tampered_receipts_are_retained_without_official_display_claims(self):
        original = copy.deepcopy(self.payload['ipos'][0]['activeOfferTerms'])
        for value in (None, [], 'bad', {}, {**original, 'source': {**original['source'], 'sha256': '0' * 64}}):
            with self.subTest(value=type(value).__name__):
                self.payload['ipos'][0]['activeOfferTerms'] = value
                entry = self.report()['offerReceipts'][0]
                self.assertEqual(entry['state'], 'invalid_receipt')
                self.assertEqual(entry['receiptValidation'], 'rejected')
                self.assertEqual(entry['provisionalFields'], [])
                self.assertIn('receipt', entry['issues'])

    def test_future_receipt_clocks_are_investigation_not_freshness(self):
        report = self.report('2026-09-19T02:00:00Z')
        for entry in report['offerReceipts']:
            self.assertEqual(entry['state'], 'review_required')
            self.assertEqual(entry['issues']['collectionClock'], 'future_timestamp')
            self.assertEqual(entry['issues']['reviewClock'], 'future_timestamp')
            self.assertEqual(entry['clocks']['observation']['state'], 'missing')

    def test_inactive_lifecycle_remains_visible(self):
        self.payload['ipos'][0]['status'] = 'withdrawn'
        entry = self.report()['offerReceipts'][0]
        self.assertEqual(entry['state'], 'inactive_lifecycle')
        self.assertEqual(entry['provisionalFields'], [])

    def test_markdown_lists_expired_evidence_and_unknown_clocks(self):
        output = health.markdown_report(self.report('2026-09-26T00:00:00Z'))
        self.assertIn('axiomgas / expired', output)
        self.assertIn('varmora / expired', output)
        self.assertIn('poojalogis / expired', output)
        self.assertIn('unknown (missing)', output)
        self.assertIn('disclosure-absent', output)
        self.assertIn('Review time is not accepted publication time', output)


if __name__ == '__main__':
    unittest.main()
