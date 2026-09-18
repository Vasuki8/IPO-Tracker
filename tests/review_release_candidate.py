"""Rehearse review-only output in a separate immutable-Git export, never live.

The deployed verifier must NOT call this builder. Candidate receipts identify the
source commit separately from the generated output; they are not deployments.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

BUILDERS = ('validate_data.py', 'build_missing_queue.py', 'phase_status.py', 'build_company_pages.py')
REPORTS = frozenset({'data/validation.json', 'data/missing_queue.json',
                     'data/phase_status.json', 'data/ipos-summary.json', 'ipo/routes.json'})


def output_path(name):
    return name in REPORTS or bool(re.fullmatch(r'ipo/[a-z0-9][a-z0-9-]*/index\.html', name))


def hashes(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Candidate contains a symlink: ' + str(path.relative_to(root)))
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def changed(before, after):
    return sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))


def prepare(source, destination, expected_commit, *, run=subprocess.run):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not re.fullmatch(r'[a-f0-9]{40}', expected_commit):
        raise ValueError('Expected source commit must be a full SHA')
    if (destination.exists() or destination == source or source in destination.parents
            or destination in source.parents):
        raise ValueError('Candidate must be a new directory outside the checkout')
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if actual != expected_commit:
        raise ValueError('Checkout does not match the expected source commit')
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD'], cwd=source, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with tempfile.TemporaryDirectory() as temporary:
        archive = Path(temporary) / 'source.tar'
        subprocess.run(['git', 'archive', '--format=tar', '-o', str(archive), expected_commit],
                       cwd=source, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        with tarfile.open(archive) as tar:
            if any(not (member.isfile() or member.isdir()) for member in tar.getmembers()):
                raise ValueError('Candidate archive must contain only regular files and directories')
            destination.mkdir(parents=True)
            tar.extractall(destination, filter='data')
    before = hashes(destination)
    protected = ('data/ipos.json', 'data/pending_updates.json', 'data/public_display_holds.json')
    if any(name not in before for name in protected):
        raise ValueError('Candidate archive is missing protected inputs')
    steps = []
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    for builder in BUILDERS:
        command = [sys.executable, str(destination / 'scripts' / builder)]
        if builder == 'validate_data.py':
            command.append('--strict')
        result = run(command, cwd=destination, env=env, check=True,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        # Check after EVERY builder. A later stage cannot mask an earlier write.
        after = hashes(destination)
        unexpected = [name for name in changed(before, after) if not output_path(name)]
        if unexpected:
            raise ValueError('Review rehearsal changed protected files: ' + ', '.join(unexpected))
        steps.append({'script': builder, 'stdout': result.stdout, 'stderr': result.stderr})
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD'], cwd=source, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'status': 'prepared', 'scope': 'isolated-pr-review-rebuild-not-deployed',
            'sourceCommit': expected_commit, 'inputSha256': {n: before[n] for n in protected},
            'changedOutputSha256': {n: after.get(n) for n in changed(before, after)},
            'protectedInputsUnchanged': True, 'steps': steps}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
    cli.add_argument('--destination', required=True, type=Path)
    cli.add_argument('--expected-commit', required=True)
    args = cli.parse_args()
    try:
        receipt = prepare(args.source, args.destination, args.expected_commit)
    except (OSError, ValueError, subprocess.SubprocessError, tarfile.TarError) as error:
        print(json.dumps({'status': 'failed', 'scope': 'isolated-pr-review-rebuild-not-deployed',
                          'error': str(error)}))
        return 1
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
