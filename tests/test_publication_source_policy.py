"""Exercise collector freshness against real, isolated Git histories."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from publication_source_policy import SOURCE_DEPENDENCIES, verify_source_commit


class PublicationSourcePolicyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Publication guard test')
        self.git('config', 'user.email', 'guard@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        for name in SOURCE_DEPENDENCIES:
            self.write('scripts/collector.py' if name == 'scripts' else name, 'before\n')
        self.write('data/ipos.json', '{"ipos": []}\n')
        self.base = self.commit('Collection baseline')

    def git(self, *arguments):
        return subprocess.run(
            ['git', *arguments], cwd=self.repo, check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-qm', message)
        return self.git('rev-parse', 'HEAD')

    def verify(self, sha=None, **options):
        verify_source_commit(self.base if sha is None else sha, repo=options.get('repo', self.repo))

    def test_unchanged_source_is_accepted(self):
        self.verify()

    def test_data_only_publication_is_accepted(self):
        self.write('data/ipos.json', '{"ipos": [{"id": "new"}]}\n')
        self.write('data/pending_updates.json', '{"updates": []}\n')
        self.write('data/source_review.json', '{"status": "reviewed"}\n')
        self.commit('Independent accepted data update')
        self.verify()

    def test_documentation_only_change_is_accepted(self):
        self.write('docs/OPERATIONS.md', 'Documentation update\n')
        self.commit('Document operations')
        self.verify()

    def test_each_source_dependency_change_is_rejected(self):
        for name in SOURCE_DEPENDENCIES:
            with self.subTest(path=name):
                self.git('reset', '--hard', self.base)
                self.write('scripts/collector.py' if name == 'scripts' else name, 'changed\n')
                self.commit('Change source dependency')
                with self.assertRaisesRegex(ValueError, 'recollected'):
                    self.verify()

    def test_registry_deletion_is_rejected(self):
        (self.repo / 'data/verified_corrections.json').unlink()
        self.commit('Remove reviewed correction registry')
        with self.assertRaisesRegex(ValueError, 'reviewed-correction policy'):
            self.verify()

    def test_new_registry_after_collection_is_rejected(self):
        (self.repo / 'data/verified_corrections.json').unlink()
        source = self.commit('Legacy source without correction registry')
        self.write('data/verified_corrections.json', '{"corrections": []}\n')
        self.commit('Introduce reviewed correction policy')
        with self.assertRaisesRegex(ValueError, 'reviewed-correction policy'):
            self.verify(source)

    def test_recollection_after_registry_change_is_accepted(self):
        self.write('data/verified_corrections.json', '{"corrections": []}\n')
        current = self.commit('Review corrections before recollecting')
        self.verify(current)

    def test_subdirectory_cannot_hide_registry_change(self):
        self.write('data/verified_corrections.json', 'changed\n')
        self.commit('Change reviewed correction policy')
        with self.assertRaisesRegex(ValueError, 'recollected'):
            self.verify(repo=self.repo / 'scripts')

    def test_non_ancestor_is_rejected(self):
        self.write('data/ipos.json', 'side branch data\n')
        side = self.commit('Divergent collector source')
        self.git('reset', '--hard', self.base)
        self.write('data/ipos.json', 'current branch data\n')
        self.commit('Current publication branch')
        with self.assertRaises(subprocess.CalledProcessError):
            self.verify(side)

    def test_invalid_sha_is_rejected_before_running_git(self):
        for sha in ('', 'HEAD', '--help', 'a' * 39, 'g' * 40, 'A' * 40, 'a' * 40 + '\n', None, 42):
            with self.subTest(sha=sha), patch('publication_source_policy.subprocess.run') as run:
                with self.assertRaisesRegex(ValueError, 'Invalid collector commit SHA'):
                    verify_source_commit(sha, repo=self.repo)
                run.assert_not_called()

    def test_git_error_is_not_treated_as_unchanged_source(self):
        ancestor = subprocess.CompletedProcess(['git', 'merge-base'], 0)
        failed_diff = subprocess.CompletedProcess(['git', 'diff'], 128)
        with patch('publication_source_policy.subprocess.run', side_effect=[ancestor, failed_diff]):
            with self.assertRaises(subprocess.CalledProcessError):
                self.verify()


if __name__ == '__main__':
    unittest.main()
