"""Reject retained collector artifacts after their source policy changes."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

# Reviewed corrections are executable publication policy, not ordinary output
# data. An edit, deletion, or newly introduced registry invalidates an old run.
SOURCE_DEPENDENCIES = (
    'scripts',
    'uv.lock',
    'pyproject.toml',
    'data/verified_corrections.json',
)


def verify_source_commit(sha: str, *, repo: str | Path | None = None) -> None:
    """Require an ancestor collected with the same code and correction policy.

    Data-only advances may still use the publisher's three-way merge. Git
    errors fail closed; they must never be interpreted as an unchanged source.
    """
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Invalid collector commit SHA')
    subprocess.run(
        ['git', 'merge-base', '--is-ancestor', sha, 'HEAD'],
        cwd=repo, check=True,
    )
    command = [
        'git', 'diff', '--quiet', sha, 'HEAD', '--',
        *(f':(top){path}' for path in SOURCE_DEPENDENCIES),
    ]
    result = subprocess.run(command, cwd=repo, check=False)
    if result.returncode == 1:
        raise ValueError(
            'Collector code or reviewed-correction policy changed after collection; '
            'retained artifact must be recollected with current code and policy'
        )
    result.check_returncode()
