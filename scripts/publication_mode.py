"""Select a projection-only rebuild only for an entirely presentation-only push.

Unknown paths, unavailable history and mixed parser/data pushes keep repair mode.
This changes no phase gate or source collector permission.
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
}

def push_mode(paths):
    def presentation(path):
        # Reject malformed paths rather than normalizing them into an allowlist.
        if not isinstance(path, str) or not path or not path.isprintable() or '\\' in path:
            return False
        pure = PurePosixPath(path)
        if pure.is_absolute() or pure.as_posix() != path or '..' in pure.parts:
            return False
        # The generator uses lowercase alphanumeric slugs, with hyphens (including
        # a double hyphen before a collision suffix). Other ipo/ files stay repair.
        profile = re.fullmatch(r'ipo/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?/index\.html', path)
        return (path in PRESENTATION_FILES or path.startswith(('docs/', 'tests/', 'assets/'))
                or profile is not None
                or (len(pure.parts) == 1 and (pure.suffix in {'.html', '.css', '.js'} or path == 'README.md')))
    return 'presentation' if paths and all(presentation(path) for path in paths) else 'repair'

def main():
    # A depth-two checkout includes the merge's first parent. A multi-commit push
    # with unknown earlier history conservatively runs repair instead.
    import json
    from pathlib import Path
    try:
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        before = event.get('before', '') if isinstance(event, dict) else ''
        if not isinstance(before, str) or not re.fullmatch('[a-f0-9]{40}', before) or before == '0' * 40:
            raise ValueError('No usable push baseline')
        # Include both sides of renames so a protected deletion cannot be hidden
        # by a presentation destination. NUL delimiters retain unusual filenames.
        result = subprocess.run(['git', 'diff', '--name-only', '--no-renames', '-z', before, 'HEAD', '--'],
                                check=True, capture_output=True, text=True)
        paths = result.stdout.rstrip('\0').split('\0') if result.stdout else []
        mode = push_mode(paths)
    except (OSError, KeyError, ValueError, subprocess.CalledProcessError):
        mode = 'repair'
    print(mode)

if __name__ == '__main__':
    main()
