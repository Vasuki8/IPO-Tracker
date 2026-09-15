"""Apply reviewed field corrections only to their exact prior values."""
import argparse
import copy
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from record_integrity import repair

ROOT = Path(__file__).resolve().parents[1]


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def record_evidence(row, entry, before, after):
    source = entry['source']
    row.setdefault('dataCorrections', []).append({
        'field': entry['field'], 'before': copy.deepcopy(before), 'after': copy.deepcopy(after),
        'reason': entry.get('reason', 'Filled from a reviewed final offer or listing notice'),
        'sourceUrl': source['url'], 'evidence': copy.deepcopy(entry['evidence']),
        'correctedAt': entry['reviewedAt'],
    })
    if not any(item.get('url') == source['url'] for item in row.get('sources', [])):
        row.setdefault('sources', []).append({**copy.deepcopy(source), 'asOf': entry['reviewedAt']})


def fill_reviewed_fields(rows, entries):
    """Fill final-notice gaps independently of earlier full-record migrations."""
    applied, conflicts = 0, []
    for entry in entries:
        identity, field, value = entry['identity'], entry['field'], entry['value']
        source = entry['source']
        if not all(identity.get(key) for key in ('id', 'company', 'symbol', 'openDate')):
            raise ValueError('A reviewed final notice requires the exact issuer and offer identity')
        if urlparse(source['url']).scheme != 'https' or not source.get('name') or not entry.get('evidence'):
            raise ValueError('A reviewed final notice requires HTTPS source evidence')
        if field == 'lotSize':
            if type(value) is not int or not 0 < value <= 100000:
                raise ValueError('Invalid reviewed lot size')
        elif field == 'listingDate':
            if date.fromisoformat(value) < date.fromisoformat(identity['openDate']):
                raise ValueError('Listing precedes this offer')
        elif field == 'issueComposition':
            if (not isinstance(value, dict) or set(value) != {'freshShares', 'ofsShares'}
                    or any(type(n) is not int or n < 0 for n in value.values())
                    or sum(value.values()) <= 0):
                raise ValueError('Reviewed composition requires explicit fresh and OFS share counts')
        else:
            raise ValueError('Unsupported reviewed final-notice field')
        row = rows.get(identity['id'])
        if row is None or any(row.get(key) != expected for key, expected in identity.items()):
            conflicts.append({'id': identity['id'], 'field': field, 'reason': 'Final-notice issuer or offer identity changed'})
            continue
        before = row.get(field)
        if before == value:
            continue
        if before not in (None, '', {}):
            conflicts.append({'id': identity['id'], 'field': field, 'reason': 'Preserved existing value instead of replacing it with a reviewed final notice'})
            continue
        row[field] = copy.deepcopy(value)
        record_evidence(row, entry, before, value)
        applied += 1
    return applied, conflicts


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
        if any(any(row.get(key) != expected for key, expected in entry.get('identity', {}).items()) for entry in corrections):
            conflicts.append({'id': identifier, 'reason': 'Reviewed issuer or offer identity changed'})
            continue
        changed = [entry['field'] for entry in corrections if row.get(entry['field']) != entry['after'] and fingerprint(row.get(entry['field'])) != entry['beforeHash']]
        if changed:
            conflicts.append({'id': identifier, 'fields': changed, 'reason': 'Value changed since source review; preserving this record and its matching provenance'})
            continue
        for correction in corrections:
            field = correction['field']
            if row.get(field) != correction['after']:
                if correction.get('source'):
                    record_evidence(row, correction, row.get(field), correction['after'])
                row[field] = copy.deepcopy(correction['after'])
                applied += 1
    filled, fill_conflicts = fill_reviewed_fields(rows, registry.get('fillMissing', []))
    applied += filled
    conflicts.extend(fill_conflicts)
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
