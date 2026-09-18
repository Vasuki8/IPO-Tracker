"""A request-only PR invokes bounded repair, never the broad source collector."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reviewed_request import REQUEST_PATH, request_ids
import publication_mode


class ReviewedRequestTests(unittest.TestCase):
    def test_only_exact_request_path_selects_reviewed_mode(self):
        self.assertEqual(publication_mode.push_mode([REQUEST_PATH]), 'reviewed')
        for path in ('data/ipos.json', 'data/reviewed_publication_request.json.bak', '../'+REQUEST_PATH):
            self.assertEqual(publication_mode.push_mode([path]), 'repair')
        self.assertEqual(publication_mode.push_mode(['index.html']), 'presentation')

    def test_request_mixed_with_other_changes_fails_instead_of_collecting(self):
        for other in ('scripts/reviewed_request.py', 'data/ipos.json', 'docs/PROJECT_STATUS.md', 'index.html'):
            with self.subTest(other=other), self.assertRaises(RuntimeError):
                publication_mode.push_mode([REQUEST_PATH, other])

    def test_mixed_push_cannot_fall_back_to_broad_repair_in_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / 'event.json'
            event.write_text(json.dumps({'before':'a'*40}))
            result = subprocess.CompletedProcess([],0,REQUEST_PATH+'\0scripts/parser.py\0','')
            with patch.dict(os.environ,{'GITHUB_EVENT_PATH':str(event)}), patch.object(publication_mode.subprocess,'run',return_value=result):
                with self.assertRaises(RuntimeError): publication_mode.main()

    def test_valid_request_retains_explicit_order(self):
        self.assertEqual(request_ids({'schemaVersion':1,'requestId':'emmvee-proof-repair-1','ids':['emmvee']},['emmvee']), 'emmvee')

    def test_invalid_request_or_unreviewed_issuer_is_rejected(self):
        valid={'schemaVersion':1,'requestId':'emmvee-proof-repair-1','ids':['emmvee']}
        for key,value in [('schemaVersion',True),('requestId','bad\noutput=anything'),('ids',[]),('ids',['all']),('ids',['teamtech']),('ids',['emmvee','emmvee']),('ids',['emmvee\nother']),('ids','emmvee')]:
            with self.subTest(key=key,value=value):
                request=copy.deepcopy(valid);request[key]=value
                with self.assertRaises(ValueError): request_ids(request,['emmvee'])
        request={**valid,'override':True}
        with self.assertRaises(ValueError): request_ids(request,['emmvee'])


if __name__=='__main__':
    unittest.main()
