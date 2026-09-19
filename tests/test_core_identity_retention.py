"""Reviewed BSE admissions survive the actual core wrapper and a failed refetch."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/core_reviewed_identities.json'


class CoreIdentityRetentionTests(unittest.TestCase):
    def test_successful_nse_refresh_and_failed_bse_keeps_all_seven_reviewed_identities(self):
        payload = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.assertEqual(len(payload['ipos']), 7)
        code = '''
import json, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, 'scripts')
import run_update_final_policy as entry
core = entry.core
target = Path(sys.argv[1])
sys.argv = ['core', '--history-days', '1', '--sebi-pages', '1']
with patch.object(core, 'DATA_FILE', target), \
     patch.object(core.NSEClient, 'current', return_value=[{'companyName': 'Independent NSE Limited', 'symbol':'NEWNSE'}]), \
     patch.object(core.NSEClient, 'upcoming', return_value=[]), \
     patch.object(core.NSEClient, 'past', return_value=[]), \
     patch.object(core.SEBIClient, 'fetch_recent_filings', return_value=[]), \
     patch.object(core.BSEClient, 'current_issues', side_effect=RuntimeError('HTTP 403')), \
     patch.object(core.time, 'sleep'):
    assert entry.main() == 0
'''
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'ipos.json'
            target.write_text(json.dumps({'meta': {'schemaVersion': 5}, 'ipos': payload['ipos']}), encoding='utf-8')
            subprocess.run([sys.executable, '-c', code, str(target)], cwd=ROOT,
                           env={**os.environ, 'PYTHONUTF8': '1'}, capture_output=True, text=True, check=True)
            result = json.loads(target.read_text(encoding='utf-8'))
        rows = {row['id']: row for row in result['ipos']}
        self.assertEqual(len(rows), 8)
        for before in payload['ipos']:
            after = rows[before['id']]
            for field in ('company', 'symbol', 'board', 'exchange', 'openDate', 'closeDate',
                          'universeAdmission', 'sources', 'source', 'observations',
                          'priceBand', 'issueSizeCr', 'lotSize', 'subscription', 'financials'):
                self.assertEqual(after.get(field), before.get(field), (before['id'], field))
        self.assertFalse(result['meta']['sourceHealth']['BSE']['ok'])


if __name__ == '__main__':
    unittest.main()
