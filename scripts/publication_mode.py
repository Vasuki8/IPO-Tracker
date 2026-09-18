"""Classify a push without turning reviewed-only requests into source collection.

Unknown paths and unavailable history retain the existing repair behavior.
A request mixed with other changes fails closed instead of collecting sources.
"""
from __future__ import annotations
import os
from pathlib import PurePosixPath
import re
import subprocess

PRESENTATION_FILES = {
    'scripts/build_company_pages.py', 'scripts/public_quality.py',
    'scripts/publication_mode.py', 'data/public_display_holds.json',
    'ipo/routes.json', 'data/ipos-summary.json',
    '.github/workflows/refresh.yml', '.github/workflows/frontend.yml',
    '.github/workflows/source-hold-evidence.yml',
    '.github/workflows/source-authority.yml',
}
# Review policy changes need fresh queue/gate artifacts, not new source values.
# Unknown or mixed collector paths still require the normal repair workflow.
REVIEW_GATE_FILES = {
    'scripts/source_review_holds.py', 'scripts/source_review_queue.py',
    'scripts/validate_data.py', 'data/public_display_holds.json',
}
REVIEW_SUPPORT_FILES = {'.github/workflows/source-review.yml', '.github/workflows/public-release.yml'}
REVIEW_OUTPUT_FILES = {'data/validation.json', 'data/missing_queue.json', 'data/phase_status.json'}
# A change to this leaf collector can use the existing subscription-only stage.
# Policy/other collector/dependency changes still require ordinary repair.
SUBSCRIPTION_FILES = {'scripts/track_subscriptions.py'}
REVIEWED_REQUEST = 'data/reviewed_publication_request.json'


def push_mode(paths):
    if paths and REVIEWED_REQUEST in paths:
        if paths == [REVIEWED_REQUEST]:
            return 'reviewed'
        # Not caught by the unavailable-history fallback below. This is an
        # explicit but invalid request, never permission for broad collection.
        raise RuntimeError('A reviewed publication request must be the only changed file')
    def presentation(path):
        if not isinstance(path, str) or not path or not path.isprintable() or '\\' in path:
            return False
        pure = PurePosixPath(path)
        if pure.is_absolute() or pure.as_posix() != path or '..' in pure.parts:
            return False
        profile = re.fullmatch(r'ipo/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?/index\.html', path)
        return (path in PRESENTATION_FILES or path.startswith(('docs/', 'tests/', 'assets/'))
                or profile is not None
                or (len(pure.parts) == 1 and (pure.suffix in {'.html', '.css', '.js'} or path == 'README.md')))
    if (any(isinstance(path, str) and path in SUBSCRIPTION_FILES for path in paths)
            and all(isinstance(path, str) and (path in SUBSCRIPTION_FILES
                    or (presentation(path) and (path.startswith(('docs/', 'tests/'))
                        or path in {'README.md', 'scripts/publication_mode.py'}))) for path in paths)):
        return 'subscriptions'
    review_change = any(isinstance(path, str) and path in REVIEW_GATE_FILES for path in paths)
    if review_change and all(presentation(path) or (isinstance(path, str) and
                            path in REVIEW_GATE_FILES | REVIEW_OUTPUT_FILES | REVIEW_SUPPORT_FILES) for path in paths):
        return 'review'
    return 'presentation' if paths and all(presentation(path) for path in paths) else 'repair'


def main():
    import json
    from pathlib import Path
    try:
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        before = event.get('before', '') if isinstance(event, dict) else ''
        if not isinstance(before, str) or not re.fullmatch('[a-f0-9]{40}', before) or before == '0' * 40:
            raise ValueError('No usable push baseline')
        # Both sides of renames are included; protected deletions cannot be hidden.
        result = subprocess.run(['git', 'diff', '--name-only', '--no-renames', '-z', before, 'HEAD', '--'],
                                check=True, capture_output=True, text=True)
        paths = result.stdout.rstrip('\0').split('\0') if result.stdout else []
        mode = push_mode(paths)
    except (OSError, KeyError, ValueError, subprocess.CalledProcessError):
        mode = 'repair'
    print(mode)


if __name__ == '__main__':
    main()
