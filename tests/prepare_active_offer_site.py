"""Rehearse the frozen, reviewed active cohort in a separate static site."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from unittest.mock import patch

from active_offer_helpers import cohort, ROOT
from reviewed_corrections import prepare
import build_company_pages as pages


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--family', choices=('nse', 'bse', 'amounts'), default='nse')
    args = cli.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT.is_relative_to(output):
        raise ValueError('Rehearsal must not overwrite the accepted project')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new empty rehearsal directory')
    output.mkdir(parents=True, exist_ok=True)
    for pattern in ('*.js', '*.css', '*.html'):
        for file in ROOT.glob(pattern):
            shutil.copy2(file, output / file.name)
    if (ROOT / 'assets').is_dir():
        shutil.copytree(ROOT / 'assets', output / 'assets', dirs_exist_ok=True)
    shutil.copytree(ROOT / 'data', output / 'data', dirs_exist_ok=True)
    selected_cohort = cohort
    if args.family == 'bse':
        from bse_active_offer_helpers import cohort as selected_cohort
    elif args.family == 'amounts':
        from qualified_offer_amount_helpers import cohort as selected_cohort
    frozen, registry, groups = selected_cohort()
    payload = json.loads((ROOT / 'data/ipos.json').read_text(encoding='utf-8'))
    replacements = {row['id']: row for row in frozen['ipos']}
    payload['ipos'] = [replacements.get(row['id'], row) for row in payload['ipos']]
    with ExitStack() as stack:
        for module in ('active_offer_terms', 'public_quality'):
            clock = stack.enter_context(patch(module + '.datetime', wraps=datetime))
            clock.now.return_value = datetime(2026, 9, 19, 14 if args.family == 'amounts' else 6 if args.family == 'bse' else 3, tzinfo=timezone.utc)
        candidate = prepare(payload, registry, groups, [group['identity']['id'] for group in groups])
        target = output / 'data/ipos.json'
        target.write_bytes((json.dumps(candidate, ensure_ascii=False, indent=2) + '\n').encode())
        for key, value in {'ROOT': output, 'DATA_FILE': target, 'SUMMARY_FILE': output / 'data/ipos-summary.json',
                           'OUT_DIR': output / 'ipo', 'MANIFEST': output / 'ipo/routes.json'}.items():
            stack.enter_context(patch.object(pages, key, value))
        pages.main()
    print('Isolated active-offer rehearsal: ' + str(output))


if __name__ == '__main__':
    main()
