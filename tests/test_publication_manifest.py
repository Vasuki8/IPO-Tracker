"""A malformed or stale manifest must stop the CLI before any data writes."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import publish_transaction as publisher


class PublicationManifestTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.paths = {name: root / (name + '.json') for name in ('base', 'proposed', 'current', 'pending')}
        for name, path in self.paths.items():
            value = {'updates': []} if name == 'pending' else {'meta': {}, 'ipos': []}
            path.write_text(json.dumps(value) + '\n', encoding='utf-8')
        self.before = {name: path.read_bytes() for name, path in self.paths.items()}
        self.manifest = root / 'source-commit.txt'

    def invoke(self, *, manifest=True):
        arguments = ['publish_transaction.py']
        for name, path in self.paths.items():
            arguments.extend(['--' + name, str(path)])
        if manifest:
            arguments.extend(['--source-commit-file', str(self.manifest)])
        with patch.object(sys, 'argv', arguments), contextlib.redirect_stdout(io.StringIO()):
            publisher.main()

    def assert_unchanged(self):
        self.assertEqual(self.before, {name: path.read_bytes() for name, path in self.paths.items()})

    def test_empty_manifest_cannot_bypass_the_guard(self):
        for content in ('', ' ', '\n', '\r\n\t '):
            with self.subTest(content=repr(content)):
                self.manifest.write_text(content, encoding='utf-8')
                with patch.object(publisher, 'merge_payload') as merge:
                    with self.assertRaisesRegex(ValueError, 'Invalid collector commit SHA'):
                        self.invoke()
                    merge.assert_not_called()
                self.assert_unchanged()

    def test_malformed_manifest_is_rejected_without_writes(self):
        for content in ('HEAD', '--help', 'a' * 39, 'g' * 40, 'a' * 40 + '\n' + 'b' * 40):
            with self.subTest(content=content):
                self.manifest.write_text(content, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Invalid collector commit SHA'):
                    self.invoke()
                self.assert_unchanged()

    def test_missing_manifest_is_rejected_without_writes(self):
        with self.assertRaises(FileNotFoundError):
            self.invoke()
        self.assert_unchanged()

    def test_stale_source_stops_before_merge_or_writes(self):
        sha = 'a' * 40
        self.manifest.write_text(sha + '\n', encoding='utf-8')
        with patch.object(publisher, 'verify_source_commit', side_effect=ValueError('recollected')) as verify:
            with patch.object(publisher, 'merge_payload') as merge:
                with self.assertRaisesRegex(ValueError, 'recollected'):
                    self.invoke()
                verify.assert_called_once_with(sha)
                merge.assert_not_called()
        self.assert_unchanged()

    def test_valid_manifest_is_verified_and_retained_in_publication(self):
        sha = 'a' * 40
        self.manifest.write_text(sha + '\n', encoding='utf-8')
        with patch.object(publisher, 'verify_source_commit') as verify:
            self.invoke()
            verify.assert_called_once_with(sha)
        result = json.loads(self.paths['current'].read_text())
        self.assertEqual(result['meta']['publication']['collectorCommit'], sha)
        self.assertEqual(result['meta']['publication']['status'], 'published')
        self.assertEqual(json.loads(self.paths['pending'].read_text()), {'updates': []})

    def test_local_no_manifest_compatibility_is_explicit(self):
        with patch.object(publisher, 'verify_source_commit') as verify:
            self.invoke(manifest=False)
            verify.assert_not_called()
        result = json.loads(self.paths['current'].read_text())
        self.assertIsNone(result['meta']['publication']['collectorCommit'])


if __name__ == '__main__':
    unittest.main()
