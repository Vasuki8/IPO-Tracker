"""Rehearsal must not disguise stale live output or change accepted evidence."""
from pathlib import Path
import subprocess
import tempfile
import unittest

import review_release_candidate as candidate


class ReviewReleaseCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.destination = self.root / 'candidate'
        for name in ('data/ipos.json', 'data/pending_updates.json', 'data/public_display_holds.json'):
            self.write(name, '{"preserved":true}')
        self.write('ipo/example/index.html', 'stale')
        self.write('data/validation.json', 'stale')
        self.write('data/missing_queue.json', 'stale')
        self.write('data/phase_status.json', 'stale')
        outputs = ('data/validation.json', 'data/missing_queue.json', 'data/phase_status.json', 'ipo/example/index.html')
        for builder, output in zip(candidate.BUILDERS, outputs):
            self.write('scripts/' + builder,
                       'from pathlib import Path\nPath(' + repr(output) + ').write_text("candidate")\n')
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'fixture')
        self.sha = self.git('rev-parse', 'HEAD').strip()

    def write(self, name, text):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.source, text=True, stderr=subprocess.PIPE)

    def prepare(self, **kwargs):
        return candidate.prepare(self.source, self.destination, self.sha, **kwargs)

    def test_real_builds_change_only_isolated_candidate_not_stale_checkout(self):
        receipt = self.prepare()
        self.assertEqual(receipt['scope'], 'isolated-pr-review-rebuild-not-deployed')
        self.assertEqual(receipt['sourceCommit'], self.sha)
        self.assertTrue(receipt['protectedInputsUnchanged'])
        self.assertEqual(len(receipt['steps']), 4)
        self.assertEqual((self.source/'ipo/example/index.html').read_text(), 'stale')
        self.assertEqual((self.destination/'ipo/example/index.html').read_text(), 'candidate')
        for name in receipt['inputSha256']:
            self.assertEqual((self.destination/name).read_bytes(), (self.source/name).read_bytes())
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_dirty_checkout_is_not_silently_relabelled_as_commit(self):
        self.write('data/ipos.json', 'changed')
        with self.assertRaises(subprocess.CalledProcessError):
            self.prepare()
        self.assertFalse(self.destination.exists())

    def test_wrong_commit_or_existing_or_nested_destination_fails_before_writes(self):
        with self.assertRaises(ValueError):
            candidate.prepare(self.source, self.destination, 'a'*40)
        for destination in (self.source, self.source/'inside', self.root):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                candidate.prepare(self.source, destination, self.sha)
        self.destination.mkdir()
        sentinel = self.destination/'keep'
        sentinel.write_text('untouched')
        with self.assertRaises(ValueError): self.prepare()
        self.assertEqual(sentinel.read_text(), 'untouched')

    def test_arbitrary_writes_and_deletions_fail_after_first_builder(self):
        for target in ('data/ipos.json', 'data/pending_updates.json', 'data/public_display_holds.json',
                       'scripts/injected.py', 'ipo/example/arbitrary.json'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temporary:
                calls = []
                def mutation(command, **kwargs):
                    calls.append(command)
                    path = kwargs['cwd']/target
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if path.exists(): path.unlink()
                    else: path.write_text('not a review output')
                    return subprocess.CompletedProcess(command, 0, '', '')
                with self.assertRaisesRegex(ValueError, 'protected files'):
                    candidate.prepare(self.source, Path(temporary)/'site', self.sha, run=mutation)
                self.assertEqual(len(calls), 1)
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_builder_failure_cannot_produce_success_or_run_later_builders(self):
        calls=[]
        def failing(command, **kwargs):
            calls.append(command)
            raise subprocess.CalledProcessError(1, command)
        with self.assertRaises(subprocess.CalledProcessError): self.prepare(run=failing)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_symlink_archive_is_rejected_without_extraction(self):
        (self.source/'data/alias').symlink_to('ipos.json')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'link')
        self.sha=self.git('rev-parse', 'HEAD').strip()
        with self.assertRaisesRegex(ValueError, 'regular files'): self.prepare()
        self.assertFalse(self.destination.exists())

    def test_missing_proposal_input_is_not_an_empty_success(self):
        (self.source/'data/pending_updates.json').unlink()
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'missing')
        self.sha=self.git('rev-parse', 'HEAD').strip()
        with self.assertRaisesRegex(ValueError, 'missing protected'): self.prepare()

    def test_workflow_limits_rehearsal_to_pr_and_passes_actual_deployed_root(self):
        workflow=(Path(__file__).resolve().parents[1]/'.github/workflows/public-release.yml').read_text()
        step=workflow.split('      - name: Prepare isolated PR review output\n',1)[1].split('      - name:',1)[0]
        self.assertIn("if: github.event_name == 'pull_request'", step)
        self.assertIn('uv sync --frozen', step)
        self.assertIn('review_release_candidate.py', step)
        deployed=workflow.split('if [[ "$EVENT_NAME" == \'workflow_run\' ]]; then',1)[1].split('else',1)[0]
        self.assertIn('test "$root" = "$PWD"', deployed)
        self.assertIn('test "$sha" = "$DEPLOYED_SHA"', deployed)
        self.assertNotIn('candidate.py', deployed)
        self.assertIn('--root "$root" --expected-commit "$sha"', workflow)
        self.assertNotIn('contents: write', workflow)


if __name__ == '__main__': unittest.main()
