"""Keep projection releases away from collector/phase mutations."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from publication_mode import push_mode

# Retain the actual PR #111 diff without requiring its history in shallow CI.
CONFLICT_EXPLANATION_RELEASE = [
    'ipo/blackbuck/index.html', 'ipo/genxai/index.html', 'ipo/mbel/index.html',
    'ipo/routes.json', 'ipo/shriahimsa/index.html', 'ipo/teamtech/index.html',
    'public-quality.js', 'scripts/public_quality.py',
    'tests/public_quality.test.cjs', 'tests/test_public_quality.py',
]

class PublicationModeTests(unittest.TestCase):
    def test_presentation_change_set_uses_bounded_rebuild(self):
        self.assertEqual(push_mode(['scripts/public_quality.py', 'app.js', 'index.html',
            'tests/fixtures/example.json.gz', 'docs/PROJECT_STATUS.md',
            '.github/workflows/frontend.yml', 'data/public_display_holds.json']), 'presentation')

    def test_generated_profiles_in_conflict_explanation_release_use_bounded_rebuild(self):
        self.assertEqual(push_mode(CONFLICT_EXPLANATION_RELEASE), 'presentation')
        self.assertEqual(push_mode(CONFLICT_EXPLANATION_RELEASE + [
            'data/ipos-summary.json', 'ipo/a/index.html', 'ipo/example-ipo/index.html',
            'ipo/example--deadbeef/index.html', 'ipo/example--deadbeef-2/index.html',
        ]), 'presentation')

    def test_mixed_or_unknown_source_change_cannot_skip_repair(self):
        for source in ['scripts/final_prospectus_parser.py', 'scripts/phase_status.py',
                       'scripts/run_pipeline.py', 'scripts/publication_source_policy.py',
                       'data/ipos.json', 'data/pending_updates.json',
                       'data/verified_corrections.json', 'data/phase_status.json',
                       'data/missing_queue.json', 'data/validation.json',
                       'data/completeness.json', 'data/performance_summary.json', 'uv.lock',
                       'pyproject.toml', '.github/workflows/unknown.yml']:
            with self.subTest(source=source):
                self.assertEqual(push_mode(CONFLICT_EXPLANATION_RELEASE + [source]), 'repair')
        self.assertEqual(push_mode([]), 'repair')

    def test_unrecognized_generated_path_shapes_cannot_skip_repair(self):
        for path in ['ipo/example/data.json', 'ipo/example/index.html.bak',
                     'ipo/example/nested/index.html', 'ipo/Example/index.html',
                     'ipo/example_ipo/index.html', 'ipo/example%2Fipo/index.html',
                     'ipo/-example/index.html', 'ipo/example-/index.html',
                     'ipo/éxample/index.html', 'ipo/index.html', 'ipo/routes.json.tmp',
                     'data/ipos-summary.json.tmp']:
            with self.subTest(path=path):
                self.assertEqual(push_mode(CONFLICT_EXPLANATION_RELEASE + [path]), 'repair')

    def test_malformed_paths_cannot_enter_any_presentation_rule(self):
        for path in [None, 3, '', '/ipo/example/index.html', './app.js', 'app.js/',
                     'ipo//example/index.html', 'ipo/./example/index.html',
                     'ipo/../index.html', 'docs/../scripts/final_prospectus_parser.py',
                     'docs//PROJECT_STATUS.md', 'assets/./app.js', 'tests/../app.js',
                     'ipo\\example\\index.html', 'docs/name\napp.js',
                     'docs/name\x00.js', 'docs/name\x7f.js']:
            with self.subTest(path=path):
                self.assertEqual(push_mode(['app.js', path]), 'repair')

    def test_projection_branch_preserves_existing_serialized_publisher(self):
        text = (ROOT/'.github/workflows/refresh.yml').read_text()
        self.assertIn('group: ipo-publication', text)
        self.assertIn("if: github.ref == 'refs/heads/main'", text)
        block = text.split('if [[ "$MODE" == "presentation" ]]; then', 1)[1].split('            else', 1)[0]
        self.assertIn('git diff --exit-code -- data/ipos.json', block)
        self.assertIn('git add data/ipos-summary.json ipo/', block)
        for forbidden in ('publish_transaction.py', 'apply_corrections.py', 'run_pipeline.py', 'phase_status.py'):
            self.assertNotIn(forbidden, block)
        self.assertEqual(text.count('contents: write'), 1)


class PublicationModeGitTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Publication test')
        self.git('config', 'commit.gpgsign', 'false')
        self.git('config', 'diff.renames', 'true')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.repo, check=True,
                              capture_output=True, text=True).stdout.strip()

    def write(self, path, content):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def commit(self):
        self.git('add', '--all')
        self.git('commit', '-qm', 'Test change')
        return self.git('rev-parse', 'HEAD')

    def mode(self, event):
        event_path = self.repo / 'event.json'
        event_path.write_text(json.dumps(event))
        return subprocess.run([sys.executable, str(ROOT / 'scripts/publication_mode.py')],
            cwd=self.repo, check=True, capture_output=True, text=True,
            env={**os.environ, 'GITHUB_EVENT_PATH': str(event_path)}).stdout.strip()

    def test_cli_classifies_actual_conflict_explanation_release_paths(self):
        for path in CONFLICT_EXPLANATION_RELEASE:
            self.write(path, 'Previous public projection\n')
        before = self.commit()
        for path in CONFLICT_EXPLANATION_RELEASE:
            self.write(path, 'Public projection with accurate conflict explanation\n')
        self.commit()
        self.assertEqual(self.mode({'before': before}), 'presentation')

    def test_canonical_rename_to_generated_profile_still_requires_repair(self):
        self.write('data/ipos.json', '{"ipos": []}\n')
        before = self.commit()
        (self.repo / 'ipo/example').mkdir(parents=True)
        self.git('mv', 'data/ipos.json', 'ipo/example/index.html')
        self.commit()
        # Git's default rename detection reports only the allowed destination.
        self.assertEqual(self.git('diff', '--name-only', before, 'HEAD', '--'),
                         'ipo/example/index.html')
        self.assertEqual(self.mode({'before': before}), 'repair')

    def test_control_character_filename_does_not_split_into_allowed_paths(self):
        self.write('app.js', 'Before\n')
        before = self.commit()
        self.write('docs/report\napp.js', 'Unexpected filename\n')
        self.commit()
        self.assertEqual(self.mode({'before': before}), 'repair')

    def test_unavailable_or_malformed_baseline_stays_repair(self):
        self.write('app.js', 'Before\n')
        before = self.commit()
        for event in [[], {}, {'before': None}, {'before': 'bad'},
                      {'before': '0' * 40}, {'before': 'f' * 40}, {'before': before}]:
            with self.subTest(event=event):
                self.assertEqual(self.mode(event), 'repair')
