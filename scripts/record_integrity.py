"""Preserve distinct issue events and quarantine impossible issue dates."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def issue_id(base, company, opened):
    name = str(company or '').lower()
    kind = 'withdrawal-option' if 'withdrawal option' in name else 'withdrawn' if 'issue withdrawn' in name else None
    if kind:
        suffix = '-' + kind + '-' + str(opened or 'undated')
        return base if str(base).endswith(suffix) else str(base) + suffix
    return base


def repair(payload):
    changes = []
    for row in payload.get('ipos', []):
        before = row.get('id')
        after = issue_id(before, row.get('company'), row.get('openDate'))
        if before != after:
            row['id'] = after
            row.setdefault('legacyId', before)
            row['issueEventType'] = 'withdrawal-option' if 'withdrawal option' in str(row.get('company')).lower() else 'withdrawn-issue'
            changes.append({'field': 'id', 'before': before, 'after': after, 'reason': 'Distinct withdrawal event identified by the source company label and issue date'})
        opened, listed = row.get('openDate'), row.get('listingDate')
        if opened and listed and listed < opened:
            row.setdefault('unverifiedObservations', {})['listingDate'] = {'value': listed, 'reason': 'Source listing date precedes this issue opening; it may belong to an earlier security listing', 'source': row.get('source')}
            row['listingDate'] = None
            row.setdefault('dataReview', {})['listingDate'] = 'Issue-specific listing date needs verification'
            change = {'field': 'listingDate', 'before': listed, 'after': None, 'reason': 'Quarantined date that predates this issue opening; original source observation retained'}
            row.setdefault('dataCorrections', []).append(change)
            changes.append(change)
    payload.setdefault('meta', {})['recordIntegrity'] = {'checkedAt': datetime.now(timezone.utc).isoformat(), 'changedFields': len(changes)}
    return changes


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--data', type=Path, default=ROOT / 'data/ipos.json')
    args = cli.parse_args()
    payload = json.loads(args.data.read_text())
    changes = repair(payload)
    args.data.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'integrityRepairs': len(changes)}))


if __name__ == '__main__':
    main()
