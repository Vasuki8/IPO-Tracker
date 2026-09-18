"""Exact source-host parity and immutable observations; not a numeric source audit."""
import copy
from datetime import date
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from public_quality import official_url, project_record
from publication_mode import push_mode
SPEC = importlib.util.spec_from_file_location('bse_probe', Path(__file__).with_name('verify_bse_host_evidence.py'))
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)

URL = 'https://beta.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID=7971&status=L'
CASES = [
    (URL, True), (URL.upper(), True), ('https://beta.bseindia.com:443/', True),
    ('https://www.bseindia.com/', True), ('https://www.nseindia.com/api/ipo-detail', True),
    ('https://beta.bseindia.com.evil.test/', False), ('https://notbeta.bseindia.com/', False),
    ('https://evil.test/beta.bseindia.com', False), ('https://beta.bseindia.com@evil.test/', False),
    ('https://evil.test@beta.bseindia.com/', False), ('https://user:pass@beta.bseindia.com/', False),
    ('http://beta.bseindia.com/', False), ('//beta.bseindia.com/', False),
    ('https://beta.bseindia.com:8443/', False), ('https://beta.bseindia.com:invalid/', False),
    ('https://%62eta.bseindia.com/', False), ('https://beta.bseindia。com/', False),
    ('https://beta.bseindia.com./', False), ('https://beta.bseindia.com\\evil', False),
    (URL + '\n', False), ('https://beta.bseindia.com\t/', False),
    ('https://[invalid/', False), ('', False), (None, False), (7, False),
]


class BseSourceAuthorityTests(unittest.TestCase):
    def test_python_and_browser_use_the_same_exact_host_boundary(self):
        urls = [u for u, _ in CASES]
        js = "const q=require('./public-quality.js');const fs=require('fs');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(u=>q.sourceAuthority('BSE',u,'official_exchange')==='Official exchange')));"
        result = subprocess.run(['node', '-e', js], input=json.dumps(urls), text=True,
                                capture_output=True, cwd=ROOT, check=True)
        browser = json.loads(result.stdout)
        for (url, expected), actual in zip(CASES, browser, strict=True):
            with self.subTest(url=url):
                self.assertEqual(official_url(url), expected)
                self.assertEqual(actual, expected)

    def test_secondary_label_overrides_an_official_host(self):
        row = {'id': 'example', 'subscription': {'total': 0}, 'subscriptionSource': 'BSE copy (secondary)',
               'subscriptionSourceUrl': URL, 'subscriptionObservedAt': None, 'subscriptionTimeBasis': 'collection-only'}
        self.assertEqual(project_record(row)['subscriptionAuthority'], 'secondary')
        js = "const q=require('./public-quality.js');console.log(JSON.stringify([q.sourceAuthority('secondary',process.argv[1]),q.sourceAuthority('BSE',process.argv[1],'secondary')]));"
        output = subprocess.check_output(['node', '-e', js, URL], cwd=ROOT, text=True)
        self.assertEqual(json.loads(output), ['Secondary source', 'Secondary source'])

    def test_host_does_not_supply_a_missing_url_or_source_time(self):
        row = {'id': 'example', 'subscription': {'total': 0}, 'subscriptionSource': 'BSE',
               'subscriptionSourceUrl': URL, 'subscriptionObservedAt': None,
               'subscriptionCollectedAt': '2026-09-18T15:58:45Z', 'subscriptionTimeBasis': 'collection-only'}
        before = copy.deepcopy(row)
        projected = project_record(row)
        self.assertEqual(projected['subscriptionAuthority'], 'official_exchange')
        self.assertIsNone(projected['subscriptionObservedAt'])
        self.assertEqual(projected['subscriptionCollectedAt'], row['subscriptionCollectedAt'])
        self.assertEqual(projected['publicQuality']['fields']['subscription']['state'], 'reported')
        self.assertEqual(projected['subscription']['total'], 0)
        self.assertEqual(row, before)
        row.pop('subscriptionSourceUrl')
        self.assertEqual(project_record(row)['subscriptionAuthority'], 'unknown')

    def test_known_observation_is_preserved_not_replaced_with_collection(self):
        row = {'id': 'example', 'subscription': {'total': 0}, 'subscriptionSource': 'BSE',
               'subscriptionSourceUrl': URL, 'subscriptionObservedAt': '2026-09-18T10:00:00Z',
               'subscriptionCollectedAt': '2026-09-18T15:58:45Z', 'subscriptionTimeBasis': 'source-observation'}
        p = project_record(row)
        for key in ('subscription', 'subscriptionObservedAt', 'subscriptionCollectedAt', 'subscriptionTimeBasis'):
            self.assertEqual(row[key], p[key])

    def test_real_host_projections_keep_every_record_and_clock(self):
        raw = (ROOT / 'data/ipos.json').read_bytes()
        rows = json.loads(raw)['ipos']
        selected = [r for r in rows if str(r.get('subscriptionSourceUrl', '')).startswith('https://beta.bseindia.com/')]
        self.assertTrue(selected, 'Real-host regression requires a retained BSE beta snapshot')
        for row in selected:
            before = copy.deepcopy(row)
            p = project_record(row, today=date(2026, 9, 18))
            self.assertEqual(p['subscriptionAuthority'], 'official_exchange')
            # Host identity never overrides an independent snapshot review.
            if p['publicQuality']['fields']['subscription']['state'] == 'under_review':
                self.assertIsNone(p['subscription'])
                self.assertFalse(p['subscriptionHistory'])
            else:
                self.assertEqual(p['subscription'], row['subscription'])
            isolated = project_record(row, today=date(2026, 9, 18), holds=[])
            self.assertEqual(isolated['subscription'], row['subscription'])
            for key in ('subscriptionObservedAt', 'subscriptionCollectedAt', 'subscriptionSourceUrl', 'subscriptionTimeBasis'):
                self.assertEqual(p[key], row.get(key))
            self.assertEqual(row, before)
        self.assertEqual((ROOT / 'data/ipos.json').read_bytes(), raw)

    def test_source_review_workflow_keeps_the_presentation_path_narrow(self):
        files = ['scripts/public_quality.py', 'public-quality.js', 'scripts/publication_mode.py',
                 '.github/workflows/source-authority.yml', 'tests/test_bse_source_authority.py']
        self.assertEqual(push_mode(files), 'presentation')
        for protected in ('scripts/track_subscriptions.py', 'data/ipos.json', 'uv.lock', 'scripts/final_prospectus_parser.py'):
            self.assertNotEqual(push_mode(files + [protected]), 'presentation')

    def test_direct_link_and_healthy_beta_are_both_required(self):
        beta = {'requestedUrl': URL, 'finalUrl': URL, 'chain': [], 'title': 'BSE Public Issues', 'bytes': 2000}
        primary = {'requestedUrl': 'https://www.bseindia.com/', 'finalUrl': 'https://www.bseindia.com/',
                   'chain': [], 'sameOrganisationLinks': [{'url': URL, 'text': 'Public Issues'}]}
        self.assertTrue(probe.verify_binding([primary, beta])[1])
        self.assertFalse(probe.verify_binding([beta])[1])
        self.assertFalse(probe.verify_binding([primary, {**beta, 'error': '403'}])[1])

    def test_only_a_referenced_healthy_primary_bundle_can_bind_beta(self):
        script_url = 'https://www.bseindia.com/assets/main-ABC.js'
        primary = {'requestedUrl': 'https://www.bseindia.com/', 'finalUrl': 'https://www.bseindia.com/',
                   'chain': [], 'referencedScripts': [script_url]}
        beta = {'requestedUrl': URL, 'finalUrl': URL, 'chain': [], 'title': 'BSE Public Issues', 'bytes': 2000}
        script = {'url': script_url, 'betaNavigation': [{'url': URL, 'context': 'href'}]}
        self.assertTrue(probe.verify_binding([primary, beta], [script])[1])
        for broken in ({**script, 'error': '403'}, {**script, 'url': 'https://evil.test/main.js'},
                       {**script, 'betaNavigation': [{'url': URL.replace('beta.bseindia.com', 'beta.bseindia.com.evil.test')}]}):
            self.assertFalse(probe.verify_binding([primary, beta], [broken])[1])

    def test_probe_refuses_untrusted_redirects_before_request(self):
        session = MagicMock()
        response = session.get.return_value.__enter__.return_value
        response.status_code = 301
        response.headers = {'Location': 'https://evil.test/'}
        result = probe.inspect(session, 'https://www.bseindia.com/')
        self.assertIn('outside', result['error'])
        self.assertEqual(session.get.call_count, 1)

    def test_probe_does_not_confuse_host_substrings_with_navigation(self):
        session = MagicMock()
        response = session.get.return_value.__enter__.return_value
        response.status_code = 200
        response.iter_content.return_value = [b'const urls=["https://beta.bseindia.com.evil.test/", "https://beta.bseindia.com/register/AuditorRegisteration.aspx"];']
        result = probe.inspect_navigation_script(session, 'https://www.bseindia.com/main-ABC.js')
        self.assertEqual([r['url'] for r in result['betaNavigation']],
                         ['https://beta.bseindia.com/register/AuditorRegisteration.aspx'])


if __name__ == '__main__':
    unittest.main()
