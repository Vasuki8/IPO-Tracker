"""Read-only proposal triage. Matching a stored group is NOT source acceptance.

Print a deterministic report to stdout; never change canonical data, proposals,
review states or the P4 gate. Only documentFields are assessed in this first pass.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from publish_transaction import FIELD_GROUPS  # noqa: E402
from public_quality import project_record  # noqa: E402
from final_prospectus_policy import STATIC_CANONICAL_FIELDS  # noqa: E402

DOCUMENT_FIELDS = FIELD_GROUPS['documentFields']
VALUE_FIELDS = tuple(field for field in DOCUMENT_FIELDS if field in STATIC_CANONICAL_FIELDS)
CONFLICT_KEYS = ('path', 'baseExists', 'base', 'proposedExists', 'proposed', 'status')
ACTIONS = {
    'already_applied_exact': 'Confirm the matching group and source review before recording an audited resolution.',
    'policy_clock_only': 'Review the matching facts and proofs; only the enforcement check clock differs.',
    'base_unchanged': 'Revalidate the retained proposal and source lineage against current main before retrying.',
    'still_conflicting': 'Compare the complete group and source evidence; prepare a bounded reviewed repair.',
    'no_change_proposal': 'Inspect the retained no-change proposal; do not count it as a source repair.',
    'legacy_group_scope': 'Recover the original group/code context or recollect; do not equate a partial group with current data.',
    'missing_record': 'Resolve the issuer/offer identity from retained evidence; do not match by name alone.',
    'ambiguous_record': 'Resolve duplicate issuer IDs before comparing or applying the proposal.',
    'malformed_proposal': 'Inspect the original occurrence and integrity finding; retain it unchanged.',
    'not_assessed': 'Triage this proposal family in a separate reconciliation pass.',
}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError('Non-finite JSON number: ' + value)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def equal(left, right):
    """Compare JSON facts without conflating false, zero, null or absent keys."""
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(equal(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(equal(a, b) for a, b in zip(left, right))
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    return type(left) is type(right) and left == right


def without_policy_clock(group):
    result = copy.deepcopy(group)
    if isinstance(result.get('staticSourcePolicy'), dict):
        result['staticSourcePolicy'].pop('checkedAt', None)
    return result


def assess(record, group, *, as_of, holds):
    """Use the existing public boundary, but never promote or publish the copy."""
    candidate = {k: copy.deepcopy(v) for k, v in record.items() if k not in DOCUMENT_FIELDS}
    candidate.update(copy.deepcopy(group))
    try:
        public = project_record(candidate, today=as_of, holds=holds)
        states = {field: public['publicQuality']['fields'][field]['state']
                  for field in VALUE_FIELDS if field in group}
        return {'status': 'assessed', 'fieldStates': states,
                'requiresSourceReview': any(state in {'under_review', 'source_unavailable'} for state in states.values())}
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, OverflowError) as error:
        return {'status': 'assessment_failed', 'requiresSourceReview': True,
                'errorType': type(error).__name__}


def entry_report(item, index, rows, *, as_of, holds):
    entry = {'inputIndex': index, 'proposalSha256': digest(encoded(item)), 'resolutionChanged': False}
    def finish(state, reason=None):
        entry['comparisonState'] = state
        entry['nextAction'] = ACTIONS[state]
        if reason:
            entry['reason'] = reason
        return entry
    if not isinstance(item, dict):
        return finish('malformed_proposal', 'Occurrence is not an object')
    entry.update({k: copy.deepcopy(item[k]) for k in ('fingerprint', 'runId', 'path', 'status') if k in item})
    path = item.get('path')
    if (not isinstance(path, list) or len(path) < 3 or path[0] != 'ipos'
            or not all(isinstance(part, str) and part for part in path)):
        return finish('malformed_proposal', 'Unsupported or incomplete issuer path')
    entry['id'] = path[1]
    if (not all(k in item for k in (*CONFLICT_KEYS, 'fingerprint', 'runId'))
            or type(item['baseExists']) is not bool or type(item['proposedExists']) is not bool
            or item['status'] != 'pending_conflict_review'
            or not isinstance(item['runId'], str) or not item['runId']):
        return finish('malformed_proposal', 'Missing or invalid conflict envelope')
    # This is the publisher's original fingerprint encoding, not a new identity.
    original = {k: item[k] for k in CONFLICT_KEYS}
    expected = digest(json.dumps(original, sort_keys=True, allow_nan=False).encode('utf-8'))
    if item['fingerprint'] != expected:
        return finish('malformed_proposal', 'Retained fingerprint does not match the original envelope')
    if any(not item[k + 'Exists'] and item[k] is not None for k in ('base', 'proposed')):
        return finish('malformed_proposal', 'Absent snapshot has a non-null payload')
    if path[2:] != ['documentFields']:
        result = finish('not_assessed', 'Only complete documentFields proposals are assessed in this version')
        if path[2] == 'subscriptionSnapshot':
            result['nextAction'] = 'Review the complete subscription snapshot, official/secondary authority and source versus collection clocks.'
        elif path[2] == 'lotTerms':
            result['nextAction'] = 'Review issue-specific lot evidence; keep market lot and minimum bid quantity distinct.'
        elif path[2] == 'priceSnapshot':
            result['nextAction'] = 'Review existing official listing evidence without enabling performance expansion.'
        return result
    matches = rows.get(path[1], [])
    if not matches:
        return finish('missing_record')
    if len(matches) != 1:
        return finish('ambiguous_record')
    record = matches[0]
    entry['currentIdentity'] = {k: record.get(k) for k in ('company', 'symbol', 'openDate')}
    entry['identityBasis'] = 'retained-path-id-not-new-issuer-verification'
    if (not item['baseExists'] or not item['proposedExists']
            or not isinstance(item['base'], dict) or not isinstance(item['proposed'], dict)):
        return finish('malformed_proposal', 'Atomic document snapshots must be present objects')
    base, proposed = item['base'], item['proposed']
    unknown = sorted((set(base) | set(proposed)) - set(DOCUMENT_FIELDS))
    if unknown:
        entry['unsupportedFields'] = unknown
        return finish('legacy_group_scope', 'Snapshot contains fields outside the current atomic group')
    current = {k: record[k] for k in DOCUMENT_FIELDS if k in record}
    entry['groupHashes'] = {k: digest(encoded(v)) for k, v in
                           (('base', base), ('proposed', proposed), ('current', current))}
    different = sorted(k for k in set(current) | set(proposed)
                       if k not in current or k not in proposed or not equal(current[k], proposed[k]))
    entry['differingValueFields'] = [k for k in different if k in VALUE_FIELDS]
    entry['differingEvidenceOrReviewFields'] = [k for k in different if k not in VALUE_FIELDS]
    entry['currentOnlyFields'] = sorted(set(current) - set(proposed))
    entry['proposedOnlyFields'] = sorted(set(proposed) - set(current))
    entry['currentEvidence'] = assess(record, current, as_of=as_of, holds=holds)
    entry['proposedEvidence'] = assess(record, proposed, as_of=as_of, holds=holds)
    # Equality is kept separate from source acceptance, including equal bad data.
    if equal(current, proposed):
        state = 'already_applied_exact'
    elif equal(without_policy_clock(current), without_policy_clock(proposed)):
        state = 'policy_clock_only'
    elif equal(base, proposed):
        state = 'no_change_proposal'
    elif equal(current, base):
        state = 'base_unchanged'
    else:
        state = 'still_conflicting'
    return finish(state)


def build_report(canonical, pending, *, as_of, holds):
    if not isinstance(canonical, dict) or not isinstance(canonical.get('ipos'), list):
        raise ValueError('Missing canonical IPO inventory')
    if not isinstance(pending, dict) or not isinstance(pending.get('updates'), list):
        raise ValueError('Missing retained updates; an absent backlog is not an empty backlog')
    rows = defaultdict(list)
    for row in canonical['ipos']:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id']:
            raise ValueError('Malformed canonical issuer identity')
        rows[row['id']].append(row)
    entries = [entry_report(item, index, rows, as_of=as_of, holds=holds)
               for index, item in enumerate(pending['updates'])]
    return {
        'schemaVersion': 1, 'scope': 'read-only-document-proposal-triage-not-source-acceptance',
        'asOf': as_of.isoformat(), 'resolutionsApplied': 0,
        'comparisonRules': {'completeAtomicGroup': list(DOCUMENT_FIELDS),
                            'clockOnlyException': 'staticSourcePolicy.checkedAt',
                            'allOccurrencesRetained': True, 'newestWriterWins': False},
        'summary': {'retainedProposals': len(entries),
                    'documentFieldProposals': sum(isinstance(e.get('path'), list) and e['path'][2:] == ['documentFields'] for e in entries),
                    'byComparisonState': dict(sorted(Counter(e['comparisonState'] for e in entries).items())),
                    'documentWithValueDifferences': sum(bool(e.get('differingValueFields')) for e in entries),
                    'documentWithEvidenceOrReviewDifferences': sum(bool(e.get('differingEvidenceOrReviewFields')) for e in entries),
                    'duplicateFingerprintOccurrences': sum(n - 1 for n in Counter(
                        e['fingerprint'] for e in entries if isinstance(e.get('fingerprint'), str)).values())},
        'entries': entries,
    }


def report_from_files(data_path, pending_path, *, as_of=None):
    paths = {'canonical': Path(data_path), 'pending': Path(pending_path),
             'displayHolds': ROOT / 'data/public_display_holds.json'}
    raw = {key: path.read_bytes() for key, path in paths.items()}
    canonical, pending, holds = [read_json(raw[k]) for k in ('canonical', 'pending', 'displayHolds')]
    if as_of is None:
        stamp = datetime.fromisoformat(canonical.get('meta', {}).get('generatedAt', ''))
        if stamp.tzinfo is None:
            raise ValueError('Snapshot time needs a timezone, or supply --as-of')
        as_of = stamp.astimezone(ZoneInfo('Asia/Kolkata')).date()
    report = build_report(canonical, pending, as_of=as_of, holds=holds['holds'])
    report['inputSha256'] = {k: digest(value) for k, value in raw.items()}
    # A changed validator/hold must not make an old report look current. No
    # mutable Git ref or wall-clock freshness claim substitutes for these bytes.
    dependencies = sorted((ROOT / 'scripts').rglob('*.py')) + [Path(__file__), ROOT / 'pyproject.toml', ROOT / 'uv.lock']
    report['codePolicySha256'] = digest(encoded({p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in dependencies}))
    return report


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--data', type=Path, default=ROOT / 'data/ipos.json')
    cli.add_argument('--pending', type=Path, default=ROOT / 'data/pending_updates.json')
    cli.add_argument('--as-of', type=date.fromisoformat, help='Assessment date; default is the snapshot date in India')
    cli.add_argument('--check-report', type=Path, help='Fail if a retained report no longer matches these exact inputs and policy')
    args = cli.parse_args(argv)
    try:
        old = read_json(args.check_report.read_bytes()) if args.check_report else None
        as_of = args.as_of or (date.fromisoformat(old['asOf']) if old is not None else None)
        report = report_from_files(args.data, args.pending, as_of=as_of)
        if old is not None:
            if not equal(old, report):
                raise ValueError('Retained report is stale or modified; regenerate from current accepted inputs')
            print(json.dumps({'status': 'current', 'inputSha256': report['inputSha256']}))
        else:
            print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
