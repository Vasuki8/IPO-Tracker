"""Apply reviewed corrections without bypassing the Final Prospectus policy."""
import argparse
import copy
import hashlib
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import final_prospectus_policy as source_policy
from record_integrity import repair

ROOT = Path(__file__).resolve().parents[1]
_STATIC_TOP_LEVEL = {
    field for field in source_policy.STATIC_CANONICAL_FIELDS if "." not in field
}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def _sha256(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _document_objects_proof_matches(proof, value, identity, evidence):
    if (not isinstance(proof, dict) or proof.get('value') != value
            or proof.get('sha256') != evidence['sha256']
            or proof.get('issueOpenDate') != identity['openDate']):
        return False
    try:
        return (source_policy.is_final_prospectus({'type': proof.get('documentType'),
                                                   'url': proof.get('sourceUrl')})
                and urlparse(str(proof.get('sourceUrl') or '')).scheme == 'https')
    except ValueError:
        return False


def _objects_review_source(entry):
    return {
        'reason': entry['reason'], 'findings': copy.deepcopy(entry['findings']),
        'source': copy.deepcopy(entry['source']), 'evidence': copy.deepcopy(entry['evidence']),
        'scope': entry.get('scope', 'value'),
    }


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


def quarantine_reviewed_objects(rows, entries):
    """Withdraw allocations within the exact source scope that a review rejected.

    Source-table syntax alone cannot prove a table's purpose or reconcile a
    prospectus contradiction. Preserve the reviewed source and previous proof
    using the normal quarantine path, without replacing unrelated evidence.
    """
    from enforce_final_prospectus_policy import _quarantine_invalid_objects

    applied, conflicts = 0, []
    for entry in entries:
        identity = entry.get('identity') or {}
        source = entry.get('source') or {}
        evidence = entry.get('evidence') or {}
        if (not all(identity.get(key) for key in ('id', 'company', 'symbol', 'openDate'))
                or not _final_prospectus_source(entry)
                or urlparse(source.get('url', '')).scheme != 'https'
                or not evidence.get('sha256') or not entry.get('beforeHash')
                or entry.get('scope', 'value') not in {'value', 'document'}
                or not entry.get('findings') or not entry.get('reason') or not entry.get('reviewedAt')):
            raise ValueError('An objects review requires exact identity, value hash and Final Prospectus evidence')
        document_review = entry.get('scope', 'value') == 'document'
        if document_review and (not _sha256(evidence['sha256']) or not _sha256(entry['beforeHash'])):
            raise ValueError('A document-scoped objects review requires lowercase SHA-256 document and value hashes')
        row = rows.get(identity['id'])
        if row is None or any(row.get(key) != value for key, value in identity.items()):
            conflicts.append({'id': identity['id'], 'field': 'objectsOfIssue',
                              'reason': 'Reviewed issuer or offer identity changed'})
            continue
        value = row.get('objectsOfIssue')
        if value in (None, []):
            review = row.get('objectsOfIssueReview') or {}
            if not document_review or not isinstance(review, dict) or review.get('status') != 'quarantined':
                continue
            snapshot = review.get('snapshot') or {}
            if not isinstance(snapshot, dict):
                snapshot = {}
            retained_value = snapshot.get('before')
            proof = snapshot.get('sourceEvidence') or {}
            if isinstance(proof, dict) and _sha256(proof.get('sha256')) and proof['sha256'] != evidence['sha256']:
                continue
            if (not isinstance(retained_value, list) or not retained_value
                    or not _document_objects_proof_matches(proof, retained_value, identity, evidence)):
                conflicts.append({'id': identity['id'], 'field': 'objectsOfIssue',
                                  'reason': 'Retained objects review source changed; preserving its snapshot and evidence'})
                continue
            previous = review.get('activeSourceReview') or snapshot.get('reviewedSource') or {}
            active = {**_objects_review_source(entry), 'identity': copy.deepcopy(identity),
                      'reviewedAt': entry['reviewedAt']}
            if previous == active or (not review.get('activeSourceReview') and isinstance(previous, dict)
                                      and previous.get('scope') == 'document'
                                      and (previous.get('evidence') or {}).get('sha256') == evidence['sha256']):
                continue
            # Keep the original withdrawal and its evidence immutable. This
            # separate revision expands the active hold without inventing a
            # second allocation withdrawal or rewriting correction history.
            review['activeSourceReview'] = copy.deepcopy(active)
            row.setdefault('dataCorrections', []).append({
                'field': 'objectsOfIssueReview.activeSourceReview',
                'before': copy.deepcopy(previous), 'after': copy.deepcopy(active),
                'reason': 'Expanded the retained objects review to the identified Final Prospectus document',
                'sourceUrl': source['url'], 'sha256': evidence['sha256'],
                'correctedAt': entry['reviewedAt'],
            })
            applied += 1
            continue
        # A layout review rejects one value; a document contradiction cannot
        # be resolved by a different extraction or a mirror of the same bytes.
        if not document_review and fingerprint(value) != entry['beforeHash']:
            continue
        proof = (row.get('staticFieldProvenance') or {}).get('objectsOfIssue') or {}
        if (document_review and isinstance(proof, dict)
                and _sha256(proof.get('sha256'))
                and proof['sha256'] != evidence['sha256']):
            # Different authoritative document bytes undergo ordinary policy;
            # an old document review must not become a recurring conflict.
            continue
        matched = (isinstance(proof, dict) and proof.get('value') == value
                   and proof.get('sha256') == evidence['sha256'])
        if document_review:
            matched = _document_objects_proof_matches(proof, value, identity, evidence)
        else:
            matched = matched and proof.get('sourceUrl') == source['url']
        if not matched:
            conflicts.append({'id': identity['id'], 'field': 'objectsOfIssue',
                              'reason': 'Reviewed objects source changed; preserving the current value and evidence'})
            continue
        _quarantine_invalid_objects(row, entry['reviewedAt'], reviewed_source=_objects_review_source(entry))
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
    filled, fill_conflicts = fill_reviewed_fields(rows, registry.get('fillMissing', []))
    applied += filled
    conflicts.extend(fill_conflicts)
    quarantined, review_conflicts = quarantine_reviewed_objects(rows, registry.get('reviewedObjects', []))
    applied += quarantined
    conflicts.extend(review_conflicts)
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
