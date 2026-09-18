"""Prepare and verify a bounded, offline reviewed-field publication.

Uses the existing correction registry and policy; never collects sources,
resolves pending proposals, or authorizes an unreviewed parser rollout.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from apply_corrections import apply
from enforce_final_prospectus_policy import apply_policy
from issue_composition_checks import COMPOSITION_FIELDS
from public_quality import project_record
from reviewed_evidence import ROOT, group_fields, index_groups, load_groups
from validate_data import validate_payload

REGISTRY_FILE = ROOT / 'data/verified_corrections.json'


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record_map(payload):
    rows = payload['ipos']
    result = {row['id']: row for row in rows}
    if len(result) != len(rows):
        raise ValueError('Reviewed publication cannot use duplicate issuer IDs')
    return result


def selected_groups(registry, groups, ids):
    indexed = index_groups(groups, registry)
    if (not isinstance(ids, list) or not ids or len(ids) != len(set(ids))
            or any(identifier not in indexed for identifier in ids)):
        raise ValueError('Select unique IDs with complete reviewed field evidence')
    return [indexed[identifier] for identifier in ids]


def validate_records(payload, registry, groups, ids):
    rows = record_map(payload)
    for group in selected_groups(registry, groups, ids):
        identifier = group['identity']['id']
        row = rows[identifier]
        if any(row.get(k) != value for k, value in group['identity'].items()):
            raise ValueError('Reviewed publication identity changed')
        quality = project_record(row)['publicQuality']['fields']
        for field, proof in group['proofs'].items():
            if (row.get(field) != proof['value']
                    or (row.get('staticFieldProvenance') or {}).get(field) != proof
                    or quality[field]['state'] != 'final_verified'):
                raise ValueError(f'{identifier}.{field}: reviewed value and public source proof must agree')
    report = validate_payload(payload)
    if report['errorCount']:
        raise ValueError('Reviewed publication has strict semantic errors')


def validate_scope(before, after, ids, *, allow_meta=False, groups=None):
    """Reject unrelated records/fields and any loss of evidence or history."""
    a, b = record_map(before), record_map(after)
    if list(a) != list(b) or set(ids) - set(a):
        raise ValueError('Reviewed publication changed the issuer inventory/order')
    for key in set(before) | set(after):
        if key != 'ipos' and not (allow_meta and key == 'meta') and before.get(key) != after.get(key):
            raise ValueError('Reviewed preparation changed unrelated payload metadata')
    selected_fields = {group['identity']['id']: group_fields(group) for group in (groups or [])}
    missing = object()
    for identifier, original in a.items():
        updated = b[identifier]
        if identifier not in ids:
            if original != updated:
                raise ValueError('Reviewed publication changed an unselected issuer')
            continue
        fields = selected_fields.get(identifier, set(COMPOSITION_FIELDS))
        allowed = fields | {'staticFieldProvenance', 'staticSourcePolicy', 'dataCorrections', 'sources'}
        if allow_meta:
            allowed.add('validation')
        for field in (set(original) | set(updated)) - allowed:
            if original.get(field, missing) != updated.get(field, missing):
                raise ValueError('Reviewed publication changed an unrelated issuer field')
        if allow_meta and original.get('validation') != updated.get('validation'):
            from update_data import build_validation
            expected = build_validation(updated)
            actual = updated.get('validation') or {}
            if ({k:v for k,v in actual.items() if k != 'checkedAt'}
                    != {k:v for k,v in expected.items() if k != 'checkedAt'}):
                raise ValueError('Reviewed publication changed non-derived exchange diagnostics')
        old_proof, new_proof = [row.get('staticFieldProvenance') or {} for row in (original, updated)]
        if ({k:v for k,v in old_proof.items() if k not in fields}
                != {k:v for k,v in new_proof.items() if k not in fields}):
            raise ValueError('Reviewed publication changed unrelated field proofs')
        for key in ('sources', 'dataCorrections'):
            old_list, new_list = original.get(key) or [], updated.get(key) or []
            if not isinstance(new_list, list) or new_list[:len(old_list)] != old_list:
                raise ValueError('Reviewed publication must preserve source and correction history')
        for event in (updated.get('dataCorrections') or [])[len(original.get('dataCorrections') or []):]:
            if event.get('field') not in fields | {'staticFieldProvenance'}:
                raise ValueError('Reviewed publication appended unrelated correction history')
        # Only the selected composition group's policy classification may change.
        old_policy, new_policy = [row.get('staticSourcePolicy') or {} for row in (original, updated)]
        for key in ('verifiedFields', 'pendingRevalidationFields'):
            if (set(old_policy.get(key) or []) ^ set(new_policy.get(key) or [])) - fields:
                raise ValueError('Reviewed publication changed unrelated policy classifications')


def prepare(payload, registry, groups, ids):
    selected = selected_groups(registry, groups, ids)
    original = record_map(payload)
    if set(ids) - set(original):
        raise ValueError('Reviewed issuer is absent from the accepted baseline')
    subset = {'ipos': [copy.deepcopy(original[identifier]) for identifier in ids]}
    scoped_registry = {**registry, 'changes': [entry for entry in registry['changes'] if entry['id'] in ids],
                       'fillMissing': []}
    _, conflicts = apply(subset, scoped_registry, evidence_groups=selected, explicit_review=True)
    if conflicts:
        raise ValueError('Reviewed correction preconditions failed: ' + json.dumps(conflicts))
    apply_policy(subset)
    replacements = record_map(subset)
    output = copy.deepcopy(payload)
    output['ipos'] = [replacements.get(row['id'], row) for row in output['ipos']]
    validate_scope(payload, output, ids, groups=selected)
    validate_records(output, registry, groups, ids)
    return output


def verify_manifest(manifest, base_path, proposed_path, before, proposed):
    if (manifest.get('schemaVersion') != 1
            or manifest.get('baseSha256') != file_hash(base_path)
            or manifest.get('proposedSha256') != file_hash(proposed_path)):
        raise ValueError('Reviewed publication manifest does not match the retained snapshots')
    registry = json.loads(REGISTRY_FILE.read_text(encoding='utf-8'))
    groups = load_groups()
    ids = manifest.get('ids')
    selected = selected_groups(registry, groups, ids)
    validate_scope(before, proposed, ids, groups=selected)
    validate_records(proposed, registry, groups, ids)
    # Re-run the reviewed before-value/proof preconditions at the write boundary.
    # A newly hashed manifest cannot authorize a different starting record or
    # arbitrary additional history, even when final values happen to match.
    expected = record_map(prepare(before, registry, groups, ids))
    actual = record_map(proposed)
    for identifier in ids:
        left, right = copy.deepcopy(expected[identifier]), copy.deepcopy(actual[identifier])
        for row in (left, right):
            row.get('staticSourcePolicy', {}).pop('checkedAt', None)
        if left != right:
            raise ValueError('Reviewed proposal differs from the approved value/proof transition')
    return registry, groups, ids


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--data', type=Path, default=ROOT / 'data/ipos.json')
    cli.add_argument('--bundle', type=Path, required=True)
    cli.add_argument('--ids', required=True, help='Comma-separated reviewed issuer IDs; no implicit all-record batch')
    args = cli.parse_args()
    ids = [value.strip() for value in args.ids.split(',')]
    base = args.bundle / 'base.json'
    output = args.bundle / 'proposed.json'
    manifest_path = args.bundle / 'reviewed.json'
    if any(path.resolve() == args.data.resolve() for path in (base, output, manifest_path)):
        raise ValueError('A reviewed bundle cannot overwrite the accepted input')
    registry = json.loads(REGISTRY_FILE.read_text(encoding='utf-8'))
    before = json.loads(args.data.read_text(encoding='utf-8'))
    proposed = prepare(before, registry, load_groups(), ids)
    args.bundle.mkdir(parents=True, exist_ok=True)
    base.write_bytes(args.data.read_bytes())
    output.write_text(json.dumps(proposed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    manifest = {'schemaVersion':1, 'ids':ids, 'baseSha256':file_hash(base),
                'proposedSha256':file_hash(output), 'scope':'reviewed-fields-only-no-source-collection'}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
