"""Apply reviewed corrections without bypassing the Final Prospectus policy."""
import argparse
import copy
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import final_prospectus_policy as source_policy
from record_integrity import repair
from reviewed_evidence import attach_evidence, evidence_conflict, index_groups, load_groups

ROOT = Path(__file__).resolve().parents[1]
_STATIC_TOP_LEVEL = {
    field for field in source_policy.STATIC_CANONICAL_FIELDS if "." not in field
}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def record_evidence(row, entry, before, after):
    source = entry['source']
    row.setdefault('dataCorrections', []).append({
        'field': entry['field'], 'before': copy.deepcopy(before), 'after': copy.deepcopy(after),
        'reason': entry.get('reason', 'Filled from a reviewed final offer or listing notice'),
        'sourceUrl': source['url'], 'evidence': copy.deepcopy(entry['evidence']),
        'correctedAt': entry['reviewedAt'],
        **({'sourceReviewUrl': after['review']['url']} if entry['field'] == 'activeOfferTerms' else {}),
    })
    if not any(item.get('url') == source['url'] for item in row.get('sources', [])):
        row.setdefault('sources', []).append({**copy.deepcopy(source),
            **({'observedAt': None, 'collectedAt': after['source']['collectedAt']}
               if entry['field'] == 'activeOfferTerms' else {'asOf': entry['reviewedAt']})})


def _final_prospectus_source(entry):
    source = entry.get('source') if isinstance(entry, dict) else None
    if not isinstance(source, dict):
        return False
    if source_policy.is_final_prospectus(source):
        return True
    return source_policy.final_prospectus_from_source(source) is not None


def _static_write_allowed(entry):
    field = str(entry.get('field') or '')
    return field not in _STATIC_TOP_LEVEL or _final_prospectus_source(entry)


def fill_reviewed_fields(rows, entries):
    """Fill reviewed gaps without letting notices/exchanges create static terms."""
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
        if not _static_write_allowed(entry):
            conflicts.append({
                'id': identity['id'],
                'field': field,
                'reason': 'Static canonical field requires Final Prospectus evidence',
            })
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


def apply(payload, registry, *, evidence_groups=(), explicit_review=False):
    evidence_by_id = index_groups(evidence_groups, registry)
    groups = defaultdict(list)
    for correction in registry.get('changes', []):
        groups[correction['id']].append(correction)
    # Validate opt-in boundaries before even normalizing the input payload.
    for identifier, corrections in groups.items():
        if any(entry['field'] == 'activeOfferTerms' for entry in corrections):
            if (any(entry.get('publicationScope') != 'explicit-reviewed' for entry in corrections)
                    or (evidence_by_id.get(identifier) or {}).get('kind') != 'active-offer-terms'):
                raise ValueError('Active offer receipts require explicit reviewed source evidence')
        scopes = {entry.get('publicationScope') for entry in corrections}
        if scopes - {None, 'explicit-reviewed'}:
            raise ValueError('Unsupported correction publication scope')
        if 'explicit-reviewed' in scopes and len(scopes) != 1:
            group = evidence_by_id.get(identifier) or {}
            old_fields = {entry['field'] for entry in corrections if entry.get('publicationScope') is None}
            if group.get('kind') != 'financials' or 'financials' in old_fields:
                raise ValueError('Explicit reviewed corrections must cover the whole issuer group')
        if 'explicit-reviewed' in scopes and explicit_review and identifier not in evidence_by_id:
            raise ValueError('Explicit reviewed corrections require matching field proofs')
    repair(payload)
    rows = {row['id']: row for row in payload['ipos']}
    applied, conflicts = 0, []
    for identifier, corrections in groups.items():
        # These groups are prepared only by the bounded reviewed publisher.
        # A registry deployment or a scheduled repair cannot activate them.
        explicit = [entry.get('publicationScope') == 'explicit-reviewed' for entry in corrections]
        if any(explicit):
            if not explicit_review:
                continue
            corrections = [entry for entry in corrections if entry.get('publicationScope') == 'explicit-reviewed']
        row = rows.get(identifier)
        if row is None:
            conflicts.append({'id': identifier, 'reason': 'Issuer record no longer exists'})
            continue
        if any(any(row.get(key) != expected for key, expected in entry.get('identity', {}).items()) for entry in corrections):
            conflicts.append({'id': identifier, 'reason': 'Reviewed issuer or offer identity changed'})
            continue
        evidence_group = evidence_by_id.get(identifier)
        problem = evidence_conflict(row, evidence_group) if evidence_group else None
        if problem:
            conflicts.append({'id': identifier, 'fields': list(evidence_group['proofs']), 'reason': problem})
            continue
        prohibited = [
            entry['field']
            for entry in corrections
            if row.get(entry['field']) != entry['after'] and not _static_write_allowed(entry)
        ]
        if prohibited:
            conflicts.append({
                'id': identifier,
                'fields': prohibited,
                'reason': 'Static canonical fields require Final Prospectus evidence',
            })
        allowed = [entry for entry in corrections if _static_write_allowed(entry)]
        changed = [entry['field'] for entry in allowed if row.get(entry['field']) != entry['after'] and fingerprint(row.get(entry['field'])) != entry['beforeHash']]
        if changed:
            conflicts.append({'id': identifier, 'fields': changed, 'reason': 'Value changed since source review; preserving this record and its matching provenance'})
            continue
        for correction in allowed:
            field = correction['field']
            if row.get(field) != correction['after']:
                if correction.get('source'):
                    record_evidence(row, correction, row.get(field), correction['after'])
                row[field] = copy.deepcopy(correction['after'])
                applied += 1
        if evidence_group:
            attach_evidence(row, evidence_group)
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
    cli.add_argument('--evidence-registry', type=Path, help='Explicit evidence registry for an isolated custom-registry run')
    args = cli.parse_args()
    if not args.registry.exists():
        return
    payload = json.loads(args.data.read_text())
    # Production always uses the mandatory evidence registry. Isolated custom
    # registries preserve their previous API unless evidence is explicitly supplied.
    evidence_path = args.evidence_registry
    if evidence_path is None and args.registry.resolve() == (ROOT / 'data/verified_corrections.json').resolve():
        evidence_path = ROOT / 'data/reviewed_correction_evidence.json'
    groups = load_groups(evidence_path) if evidence_path is not None else ()
    applied, conflicts = apply(payload, json.loads(args.registry.read_text()), evidence_groups=groups)
    args.data.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'appliedFields': applied, 'conflicts': conflicts}))


if __name__ == '__main__':
    main()
