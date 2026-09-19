import copy
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('universe_continuation', ROOT / 'tools/audit_ipo_universe.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class UniverseContinuationTests(unittest.TestCase):
    def test_month_windows_include_leap_day_and_stop_at_assessment_date(self):
        self.assertEqual(list(audit.sebi_windows('2024-03-02', 2024, 'month')),
                         [('2024-01', '2024-01-01', '2024-01-31'),
                          ('2024-02', '2024-02-01', '2024-02-29'),
                          ('2024-03', '2024-03-01', '2024-03-02')])

    def snapshot(self, root):
        raw = b'[{"companyName":"Example Limited","series":"SME","symbol":"EXAMPLE","issueStartDate":"01-Jan-2025","issueEndDate":"03-Jan-2025"}]'
        sha = audit.digest(raw)
        (root / 'responses').mkdir(parents=True)
        (root / 'responses' / (sha + '.gz')).write_bytes(gzip.compress(raw, mtime=0))
        receipt = {'key': 'NSE-2025', 'source': 'NSE', 'register': 'historical', 'asOf': '2026-09-18',
                   'fromDate': '2025-01-01', 'toDate': '2025-12-31', 'responseUrl': 'https://www.nseindia.com/api/public-past-issues',
                   'retrievedAt': '2026-09-18T10:00:00Z', 'httpStatus': 200, 'sha256': sha,
                   'rawFile': 'responses/' + sha + '.gz', 'status': 'verified_response'}
        rows, bounds = audit.parse_nse(raw, receipt)
        receipt.update(records=len(rows), bounds=bounds)
        audit.dump(root / 'capture.json', {'asOf': '2026-09-18', 'cohorts': {receipt['key']: receipt},
                   'accessAttempts': [{'key': 'old-failure', 'status': 'source_unavailable_not_verified', 'error': 'timeout'}]})
        return receipt

    def test_continuation_reuses_bytes_clocks_and_failures_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'old', Path(folder) / 'new'
            receipt = self.snapshot(source)
            original = (source / 'capture.json').read_bytes()
            with patch.object(audit.requests.Session, 'request', side_effect=AssertionError('network')):
                audit.fork_snapshot(source, target, '2026-09-19')
                capture = audit.Capture(target, '2026-09-19')
                reused = capture.fetch('NSE-2025', 'NSE', receipt['responseUrl'])
            self.assertEqual(capture.count, 0)
            self.assertEqual(reused['retrievedAt'], receipt['retrievedAt'])
            self.assertEqual(reused['asOf'], '2026-09-18')
            self.assertFalse((target / 'responses').exists())
            manifest, rows, gaps = audit.load_observations(target)
            self.assertEqual(len(rows), 1)
            self.assertEqual(manifest['accessAttempts'][0]['error'], 'timeout')
            self.assertEqual(original, (source / 'capture.json').read_bytes())
            with self.assertRaisesRegex(ValueError, 'new snapshot'):
                audit.fork_snapshot(source, target, '2026-09-19')
            (source / 'capture.json').write_bytes(original + b' ')
            with self.assertRaisesRegex(ValueError, 'Inherited capture'):
                audit.load_observations(target)

    def test_continuation_rejects_changed_response_and_older_date(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'old', Path(folder) / 'new'
            receipt = self.snapshot(source)
            with self.assertRaisesRegex(ValueError, 'precedes'):
                audit.fork_snapshot(source, target, '2026-09-17')
            (source / receipt['rawFile']).write_bytes(gzip.compress(b'[]'))
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                audit.fork_snapshot(source, target, '2026-09-19')
            self.assertFalse(target.exists())

    def test_sebi_date_filter_must_match_actual_rows(self):
        raw = b'<div>1 to 1 of 1 records</div><table><tr><td>Dec 31, 2025</td><td><a href="/filings/example_123.html">Example Limited - DRHP</a></td></tr></table>'
        receipt = {'key': 'draft-year', 'source': 'SEBI', 'page': 0, 'register': 'draft', 'asOf': '2026-09-19',
                   'fromDate': '2025-01-01', 'toDate': '2025-12-31', 'responseUrl': 'https://www.sebi.gov.in/register',
                   'sha256': audit.digest(raw), 'retrievedAt': '2026-09-19T04:00:00Z'}
        rows, bounds = audit.parse_sebi(raw, receipt)
        self.assertEqual(rows[0]['lifecycleStage'], 'draft')
        self.assertEqual(bounds['reportedTotal'], 1)
        with self.assertRaisesRegex(ValueError, 'outside the requested'):
            audit.parse_sebi(raw.replace(b'2025</td>', b'2026</td>'), receipt)

    def test_year_collection_is_bounded_and_preserves_exact_date_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            capture = audit.Capture(Path(folder), '2026-09-19', max_new=3)
            requests = []
            def fetch(key, source, url, **kwargs):
                requests.append((key, kwargs))
                capture.count += 1
                return {'status': 'verified_response', 'bounds': {'pages': 2}}
            with patch.object(capture, 'fetch', side_effect=fetch):
                capture.sebi(['draft'], 2020)
            self.assertEqual([x[0] for x in requests], ['SEBI-draft-2026-0000', 'SEBI-draft-2026-0001', 'SEBI-draft-2025-0000'])
            self.assertEqual(requests[0][1]['data']['toDate'], '19-09-2026')
            self.assertEqual(requests[2][1]['data']['fromDate'], '01-01-2025')
            self.assertEqual(requests[2][1]['data']['toDate'], '31-12-2025')

    def test_reviewed_bse_cohort_keeps_detail_clock_null_terms_and_prior_records(self):
        root = ROOT / 'docs/audits/official-universe/2026-09-19'
        rows = json.loads((root / 'missing-before-admissions.json').read_text(encoding='utf-8'))
        plan = json.loads((root / 'admissions.json').read_text(encoding='utf-8'))
        proofs = {r['recordId']: r for r in json.loads((root / 'admission-source-receipts.json').read_text(encoding='utf-8'))}
        with tempfile.TemporaryDirectory() as folder:
            tracker = Path(folder) / 'tracker.json'
            before = {'meta': {'keep': 'unchanged'}, 'ipos': [{'id': 'prior', 'company': 'Unrelated Industries Limited',
                       'financials': {'review': 'preserve'}, 'dataCorrections': [{'history': True}]}]}
            audit.dump(tracker, before)
            plan['baselineSha256'] = audit.digest(tracker.read_bytes())
            with patch.object(audit, 'load_observations', return_value=({'asOf': '2026-09-19'}, rows, [])):
                proposal = audit.prepare_admissions(root, tracker, plan, [])
                self.assertEqual(len(proposal['ipos']), 26)
                self.assertEqual(proposal['ipos'][0], before['ipos'][0])
                self.assertEqual(json.loads(tracker.read_text()), before)
                for new in proposal['ipos'][1:]:
                    receipt = proofs[new['universeAdmission']['recordId']]
                    identity = audit.bse_identity(audit.read_bound_response(root, receipt))
                    self.assertEqual(new['company'], identity['issuerName'])
                    self.assertEqual(new['symbol'], identity['symbol'])
                    self.assertEqual(new['sources'][0]['collectedAt'], receipt['retrievedAt'])
                    self.assertEqual(new['observations']['BSE']['collectedAt'], receipt['retrievedAt'])
                    self.assertIsNone(new['sources'][0]['asOf'])
                    self.assertIsNone(new['observations']['BSE']['observedAt'])
                    self.assertEqual(new['status'], 'closed')
                    for field in ('listingDate', 'priceBand', 'lotSize', 'issueSizeCr', 'financials', 'subscription'):
                        self.assertIsNone(new[field])
                before['ipos'][0]['symbol'] = proposal['ipos'][1]['symbol']
                audit.dump(tracker, before)
                plan['baselineSha256'] = audit.digest(tracker.read_bytes())
                with self.assertRaisesRegex(ValueError, 'Symbol already exists'):
                    audit.prepare_admissions(root, tracker, plan, [])

    def test_filtered_traversals_do_not_claim_unfiltered_register_completion(self):
        cohorts = {}
        rows = []
        for key, period in [('all', None), ('2025', '2025-01-01')]:
            receipt = {'key': key, 'source': 'SEBI', 'register': 'draft', 'status': 'verified_response',
                       'page': 0, 'bounds': {'reportedTotal': 1 if period else 26, 'pages': 1 if period else 2}}
            if period:
                receipt.update(fromDate=period, toDate='2025-12-31')
            cohorts[key] = receipt
            rows.append({'recordId': key + ':1', 'cohort': key, 'source': 'SEBI', 'register': 'draft',
                         'issuerName': 'Example Limited', 'normalizedName': 'example', 'url': 'https://www.sebi.gov.in/example_1.html',
                         'filingDate': '2025-03-01', 'lifecycleStage': 'draft', 'board': None, 'identityFlags': [],
                         'scope': 'equity_public_issue_candidate'})
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tracker = root / 'tracker.json'
            audit.dump(tracker, {'ipos': [{'id': 'example', 'company': 'Example Limited'}]})
            with patch.object(audit, 'load_observations', return_value=({'asOf': '2026-09-19', 'cohorts': cohorts}, rows, [])), patch('builtins.print'):
                report = audit.build(root, tracker, None, root / 'report')
            draft = [r for r in report['sebiTraversal'] if r['register'] == 'draft']
            self.assertFalse(draft[0]['completeRegisterTraversal'])
            self.assertEqual(draft[0]['missingPages'], [1])
            self.assertTrue(draft[1]['completeRegisterTraversal'])
            self.assertEqual(report['bySource'][0]['sourceRecords'], 2)
            self.assertEqual(report['eligibleDistinctBySource'][0]['sourceRecords'], 1)
            self.assertFalse(report['globalCompleteness'])


if __name__ == '__main__':
    unittest.main()
