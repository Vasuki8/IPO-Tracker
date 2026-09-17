"""Select a projection-only rebuild only for an entirely presentation-only push.

Unknown paths, unavailable history and mixed parser/data pushes keep repair mode.
This changes no phase gate or source collector permission.
"""
from __future__ import annotations
import os
from pathlib import PurePosixPath
import subprocess

PRESENTATION_FILES = {
    'scripts/build_company_pages.py', 'scripts/public_quality.py',
    'scripts/publication_mode.py', 'data/public_display_holds.json',
    '.github/workflows/refresh.yml', '.github/workflows/frontend.yml',
}

def push_mode(paths):
    def presentation(path):
        pure = PurePosixPath(path)
        return (path in PRESENTATION_FILES or path.startswith(('docs/', 'tests/', 'assets/'))
                or (len(pure.parts) == 1 and (pure.suffix in {'.html', '.css', '.js'} or path == 'README.md')))
    return 'presentation' if paths and all(presentation(path) for path in paths) else 'repair'

def main():
    # A depth-two checkout includes the merge's first parent. A multi-commit push
    # with unknown earlier history conservatively runs repair instead.
    import json
    import re
    from pathlib import Path
    try:
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        before = event.get('before', '')
        if not re.fullmatch('[a-f0-9]{40}', before) or before == '0' * 40:
            raise ValueError('No usable push baseline')
        result = subprocess.run(['git', 'diff', '--name-only', before, 'HEAD', '--'],
                                check=True, capture_output=True, text=True)
        mode = push_mode(result.stdout.splitlines())
    except (OSError, KeyError, ValueError, subprocess.CalledProcessError):
        mode = 'repair'
    print(mode)

if __name__ == '__main__':
    main()
