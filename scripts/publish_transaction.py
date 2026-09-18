"""Merge a collected snapshot without overwriting concurrent accepted data.

Independent fields merge; competing edits remain on the current branch and
the unaccepted proposals are retained as reviewable pending updates.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from publication_source_policy import verify_source_commit
from record_integrity import repair
from update_data import build_validation

MISSING = object()
FIELD_GROUPS = {
    # A composition, its amount aliases, and its quarantine/provenance state
    # must come from the same accepted document update. Otherwise concurrent
    # publication can reattach a rejected amount or detach its review marker.
    'documentFields': (
        'financials', 'leadManagers', 'registrar', 'documentFieldProvenance',
        'offerDocumentExtraction', 'issuerDocumentExtraction', 'documentRepair',
        'issueComposition', 'issueSizeCr', 'freshIssueCr', 'ofsCr',
        'issueCompositionReview', 'staticFieldProvenance', 'staticSourcePolicy',
        'objectsOfIssue', 'objectsOfIssueReview',
    ),
    'subscriptionSnapshot': ('subscription', 'subscriptionSource', 'subscriptionSourceUrl', 'subscriptionAsOf', 'subscriptionCollectedAt', 'subscriptionObservedAt', 'subscriptionTimeBasis', 'subscriptionDegraded'),
    'priceSnapshot': ('listing', 'performance', 'listingDate', 'listingDateEvidence'),
    'lotTerms': ('lotSize', 'marketLot', 'minimumBidQuantity', 'lotSizeEvidence'),
}
ATOMIC_FIELDS = {'financials', 'documentFieldProvenance', 'offerDocumentExtraction', 'performance', 'listing', *FIELD_GROUPS}


def clone(value):
    return MISSING if value is MISSING else copy.deepcopy(value)


def comparison_value(value, path):
    # Enforcement refreshes this clock without changing document facts. Ignore
    # it only for equality; return the selected group's complete original data.
    if len(path) == 3 and path[0] == 'ipos' and path[-1] == 'documentFields' and isinstance(value, dict):
        policy = value.get('staticSourcePolicy')
        if isinstance(policy, dict):
            return {**value, 'staticSourcePolicy': {key: item for key, item in policy.items() if key != 'checkedAt'}}
    return value


def merge_value(before, proposed, current, path, conflicts):
    before_comparison, proposed_comparison, current_comparison = [comparison_value(value, path) for value in (before, proposed, current)]
    if proposed_comparison == before_comparison or proposed_comparison == current_comparison:
        return clone(current)
    if current_comparison == before_comparison:
        return clone(proposed)
    if (not path or path[-1] not in ATOMIC_FIELDS) and all(isinstance(value, dict) for value in (before, proposed, current)):
        output = {}
        grouped = set()
        if len(path) == 2 and path[0] == 'ipos':
            for group, fields in FIELD_GROUPS.items():
                values = [{key: row[key] for key in fields if key in row} for row in (before, proposed, current)]
                output.update(merge_value(*values, path + [group], conflicts))
                grouped.update(fields)
        for key in sorted((set(before) | set(proposed) | set(current)) - grouped):
            merged = merge_value(before.get(key, MISSING), proposed.get(key, MISSING), current.get(key, MISSING), path + [key], conflicts)
            if merged is not MISSING:
                output[key] = merged
        return output
    # Append-only observations preserve both accepted event histories.
    if path and path[-1] in {'subscriptionHistory', 'dataCorrections'} and all(isinstance(value, list) for value in (before, proposed, current)) and proposed[:len(before)] == before and current[:len(before)] == before:
        output = copy.deepcopy(current)
        for value in proposed[len(before):]:
            if value not in output:
                output.append(copy.deepcopy(value))
        return output
    if path and path[0] == 'meta':
        return clone(current)
    conflicts.append({'path': path, 'baseExists': before is not MISSING, 'base': None if before is MISSING else before, 'proposedExists': proposed is not MISSING, 'proposed': None if proposed is MISSING else proposed, 'status': 'pending_conflict_review'})
    return clone(current)


def merge_payload(before, proposed, current):
    before, proposed, current = [copy.deepcopy(value) for value in (before, proposed, current)]
    for payload in (before, proposed, current):
        repair(payload)
    conflicts = []
    output = copy.deepcopy(current)
    maps = [{row['id']: row for row in payload.get('ipos', [])} for payload in (before, proposed, current)]
    records = []
    ids = list(dict.fromkeys([row['id'] for row in current.get('ipos', [])] + [row['id'] for row in proposed.get('ipos', [])]))
    for key in ids:
        values = [mapping.get(key, MISSING) for mapping in maps]
        # Exchange-comparison diagnostics are derived from accepted observations
        # and sources. Collector timestamps are not competing source facts.
        inputs = [{field: value for field, value in row.items() if field != 'validation'} if row is not MISSING else MISSING for row in values]
        merged = merge_value(*inputs, ['ipos', key], conflicts)
        if merged is not MISSING:
            accepted = values[2] if values[2] is not MISSING else {}
            if any(merged.get(field) != accepted.get(field) for field in ('observations', 'sources')) or ('validation' not in accepted and any(row is not MISSING and 'validation' in row for row in values)):
                merged['validation'] = build_validation(merged)
            elif 'validation' in accepted:
                merged['validation'] = copy.deepcopy(accepted['validation'])
            merged = {field: merged[field] for field in dict.fromkeys([*accepted, *merged]) if field in merged}
            records.append(merged)
    output['ipos'] = records
    output['meta'] = merge_value(before.get('meta', {}), proposed.get('meta', {}), current.get('meta', {}), ['meta'], conflicts)
    output['meta']['recordCount'] = len(records)
    output['meta']['schemaVersion'] = max(5, output['meta'].get('schemaVersion', 0))
    output['meta']['generatedAt'] = datetime.now(timezone.utc).isoformat()
    return output, conflicts


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--base', type=Path, required=True)
    cli.add_argument('--proposed', type=Path, required=True)
    cli.add_argument('--current', type=Path, default=Path('data/ipos.json'))
    cli.add_argument('--pending', type=Path, default=Path('data/pending_updates.json'))
    cli.add_argument('--run-id', default='local')
    cli.add_argument('--source-commit-file', type=Path)
    cli.add_argument('--reviewed-manifest', type=Path)
    args = cli.parse_args()
    if args.reviewed_manifest and args.source_commit_file is None:
        raise ValueError('Reviewed publication requires the original source-commit manifest')
    source_commit = args.source_commit_file.read_text().strip() if args.source_commit_file else None
    # A supplied but empty manifest is corrupt, not an opt-out from validation.
    if args.source_commit_file is not None:
        verify_source_commit(source_commit)
    values = [json.loads(path.read_text()) for path in (args.base, args.proposed, args.current)]
    reviewed = None
    if args.reviewed_manifest:
        from reviewed_corrections import verify_manifest, validate_records, validate_scope
        reviewed = verify_manifest(json.loads(args.reviewed_manifest.read_text()), args.base, args.proposed, *values[:2])
    output, conflicts = merge_payload(*values)
    if reviewed:
        registry, groups, ids = reviewed
        if conflicts:
            raise ValueError('Reviewed publication has concurrent conflicts; no accepted or pending files were changed')
        validate_scope(values[2], output, ids, allow_meta=True)
        validate_records(output, registry, groups, ids)
    pending = json.loads(args.pending.read_text()) if args.pending.exists() else {'updates': []}
    fingerprints = {item['fingerprint'] for item in pending['updates']}
    for conflict in conflicts:
        fingerprint = hashlib.sha256(json.dumps(conflict, sort_keys=True).encode()).hexdigest()
        if fingerprint not in fingerprints:
            pending['updates'].append({**conflict, 'fingerprint': fingerprint, 'runId': args.run_id})
            fingerprints.add(fingerprint)
    output['meta']['publication'] = {'runId': args.run_id, 'collectorCommit': source_commit, 'status': 'published_with_pending_conflicts' if conflicts else 'published', 'pendingConflictCount': len(pending['updates'])}
    if reviewed:
        output['meta']['publication'].update({'mode': 'reviewed', 'reviewedIds': ids})
    args.current.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    if not reviewed:
        args.pending.write_text(json.dumps(pending, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(output['meta']['publication']))


if __name__ == '__main__':
    main()
