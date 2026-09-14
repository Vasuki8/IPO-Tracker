"""Apply reviewed field corrections only to their exact prior values."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from record_integrity import repair

ROOT = Path(__file__).resolve().parents[1]


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def apply(payload, registry):
    repair(payload)
    rows = {row['id']: row for row in payload['ipos']}
    applied, conflicts = 0, []
    groups = defaultdict(list)
    for correction in registry.get('changes', []):
        groups[correction['id']].append(correction)
    for identifier, corrections in groups.items():
        row = rows.get(identifier)
        if row is None:
            conflicts.append({'id': identifier, 'reason': 'Issuer record no longer exists'})
            continue
        changed = [entry['field'] for entry in corrections if row.get(entry['field']) != entry['after'] and fingerprint(row.get(entry['field'])) != entry['beforeHash']]
        if changed:
            conflicts.append({'id': identifier, 'fields': changed, 'reason': 'Value changed since source review; preserving this record and its matching provenance'})
            continue
        for correction in corrections:
            field = correction['field']
            if row.get(field) != correction['after']:
                row[field] = correction['after']
                applied += 1
    payload.setdefault('meta', {})['schemaVersion'] = max(5, payload.get('meta', {}).get('schemaVersion', 0))
    payload.setdefault('meta', {})['reviewedCorrectionStatus'] = {'registryRevision': registry.get('revision'), 'appliedFields': applied, 'conflicts': conflicts}
    payload['meta']['initialSourceRepair'] = registry.get('summary', {})
    for stage, report in registry.get('stageReports', {}).items():
        payload['meta'].setdefault('pipelineStages', {}).setdefault(stage, report)
    return applied, conflicts


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--data', type=Path, default=ROOT / 'data/ipos.json')
    cli.add_argument('--registry', type=Path, default=ROOT / 'data/verified_corrections.json')
    args = cli.parse_args()
    if not args.registry.exists():
        return
    payload = json.loads(args.data.read_text())
    applied, conflicts = apply(payload, json.loads(args.registry.read_text()))
    args.data.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'appliedFields': applied, 'conflicts': conflicts}))


if __name__ == '__main__':
    main()
