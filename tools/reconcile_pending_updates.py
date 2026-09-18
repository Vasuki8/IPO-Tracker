"""Read-only proposal triage. Matching a stored group is NOT source acceptance.

Print a deterministic report to stdout; never change canonical data, proposals,
review states or the P4 gate. Assess documentFields and subscriptionSnapshot only.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
from datetime import date, datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from publish_transaction import FIELD_GROUPS  # noqa: E402
from public_quality import project_record, safe_url  # noqa: E402
from final_prospectus_policy import STATIC_CANONICAL_FIELDS  # noqa: E402

DOCUMENT_FIELDS = FIELD_GROUPS['documentFields']
SUBSCRIPTION_FIELDS = FIELD_GROUPS['subscriptionSnapshot']
SUBSCRIPTION_CLOCKS = ('subscriptionObservedAt', 'subscriptionCollectedAt', 'subscriptionAsOf')
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


def clock(value):
    """Read an explicit zoned timestamp; never invent a timezone or source time."""
    if value is None:
        return {'status': 'missing'}
    if not isinstance(value, str) or not re.fullmatch(
            r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})', value):
        return {'status': 'invalid'}
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.utcoffset() is None:
            raise ValueError('Timezone missing')
        return {'status': 'valid', 'utc': parsed.astimezone(timezone.utc).isoformat()}
    except (ValueError, OverflowError):
        return {'status': 'invalid'}


def subscription_evidence(record, group, *, as_of, holds):
    """Assess the stored snapshot, not a splice with today's source/history.

    Use shared public rules on an isolated copy, retaining current review context.
    Host-based authority is diagnostic classification, not source/issuer acceptance.
    """
    candidate = {k: copy.deepcopy(record[k]) for k in
                 ('id', 'company', 'symbol', 'openDate', 'closeDate', 'status',
                  'dataReview', 'dataAvailability') if k in record}
    candidate.update(copy.deepcopy(group))
    clocks = {key: clock(group.get(key)) for key in SUBSCRIPTION_CLOCKS}
    issues = [key + '_invalid' for key, value in clocks.items() if value['status'] == 'invalid']
    if not isinstance(group.get('subscriptionSource'), str) or not group['subscriptionSource'].strip():
        issues.append('source_label_missing_or_invalid')
    try:
        url = safe_url(group.get('subscriptionSourceUrl'))
    except ValueError:
        url = None
    if not url:
        issues.append('snapshot_source_url_missing_or_invalid')
    basis = group.get('subscriptionTimeBasis')
    if basis not in ('source-observation', 'collection-only'):
        issues.append('time_basis_missing_or_invalid')
    observed = clocks['subscriptionObservedAt']
    if basis == 'collection-only':
        issues.append('source_observation_unavailable')
        if group.get('subscriptionObservedAt') is not None:
            issues.append('observation_present_but_basis_collection_only')
        observed = {'status': 'unavailable_collection_only'}
    elif basis != 'source-observation':
        observed = {'status': 'unavailable_time_basis'}
    elif observed['status'] == 'missing':
        issues.append('source_observation_missing')
    # Legacy AsOf is only a collection alias. An invalid explicit clock does
    # not become acceptable merely because a different alias is well formed.
    collection_key = ('subscriptionCollectedAt' if group.get('subscriptionCollectedAt') is not None
                      else 'subscriptionAsOf')
    collected = clocks[collection_key]
    if collected['status'] == 'missing':
        issues.append('collection_time_missing')
    explicit, legacy = clocks['subscriptionCollectedAt'], clocks['subscriptionAsOf']
    if (explicit['status'] == legacy['status'] == 'valid' and explicit['utc'] != legacy['utc']):
        issues.append('collection_alias_disagrees')
    if (observed['status'] == collected['status'] == 'valid'
            and datetime.fromisoformat(observed['utc']) > datetime.fromisoformat(collected['utc'])):
        issues.append('source_observation_after_collection')
    degraded = group.get('subscriptionDegraded')
    if degraded is not None and type(degraded) is not bool:
        issues.append('degraded_state_invalid')
    elif degraded:
        issues.append('degraded_source_state_retained')
    values = group.get('subscription')
    missing = [key for key in ('qib', 'nii', 'retail', 'total')
               if not isinstance(values, dict) or values.get(key) is None]
    if missing:
        issues.append('headline_categories_missing')
    try:
        public = project_record(candidate, today=as_of, holds=holds)
        decision = public['publicQuality']['fields']['subscription']
        if decision['state'] not in ('reported', 'provisional', 'final_verified'):
            issues.append('public_subscription_not_displayable')
        result = {'status': 'assessed', 'publicState': decision['state'],
                  'authority': public['subscriptionAuthority']}
        if result['authority'] == 'unknown':
            issues.append('source_authority_unknown')
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, OverflowError) as error:
        result = {'status': 'assessment_failed', 'authority': 'unknown', 'errorType': type(error).__name__}
        issues.append('public_projection_failed')
    result.update(sourceLabel=copy.deepcopy(group.get('subscriptionSource')), sourceUrl=url,
                  sourceBinding='snapshot_fields_only_no_current_history_fallback',
                  storedClocks={k: copy.deepcopy(group[k]) for k in SUBSCRIPTION_CLOCKS if k in group},
                  clockChecks=clocks, timeBasis=copy.deepcopy(basis),
                  observed=observed, collected={**collected, 'field': collection_key},
                  missingCategories=missing, issues=issues, requiresSourceReview=bool(issues),
                  finality='not_established_by_snapshot')
    return result


def clock_relation(current, proposed):
    if current['status'] != 'valid' or proposed['status'] != 'valid':
        return 'not_comparable'
    current_time, proposed_time = [datetime.fromisoformat(v['utc']) for v in (current, proposed)]
    return ('same_instant' if current_time == proposed_time else
            'proposed_older' if proposed_time < current_time else 'proposed_newer')


def subscription_comparison(record, base, proposed, current, *, as_of, holds):
    snapshots = {key: subscription_evidence(record, group, as_of=as_of, holds=holds)
                 for key, group in (('base', base), ('proposed', proposed), ('current', current))}
    now, candidate = snapshots['current'], snapshots['proposed']
    source_relation = 'not_bound'
    if (now['sourceUrl'] and candidate['sourceUrl']
            and all(isinstance(x['sourceLabel'], str) and x['sourceLabel'].strip() for x in (now, candidate))):
        source_relation = ('same_label_and_url' if
                           (now['sourceLabel'], now['sourceUrl']) == (candidate['sourceLabel'], candidate['sourceUrl'])
                           else 'different_source')
    return {**snapshots, 'sourceRelation': source_relation,
            'observationRelation': clock_relation(now['observed'], candidate['observed']),
            'collectionRelation': clock_relation(now['collected'], candidate['collected']),
            'orderingIsResolution': False}


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
    family = path[2]
    if path[2:] not in (['documentFields'], ['subscriptionSnapshot']):
        result = finish('not_assessed', 'Only complete documentFields and subscriptionSnapshot proposals are assessed')
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
    fields = DOCUMENT_FIELDS if family == 'documentFields' else SUBSCRIPTION_FIELDS
    value_fields = VALUE_FIELDS if family == 'documentFields' else ('subscription',)
    entry['currentIdentity'] = {k: record.get(k) for k in ('company', 'symbol', 'openDate')}
    entry['identityBasis'] = 'retained-path-id-not-new-issuer-verification'
    if (not item['baseExists'] or not item['proposedExists']
            or not isinstance(item['base'], dict) or not isinstance(item['proposed'], dict)):
        return finish('malformed_proposal', 'Atomic snapshots must be present objects')
    base, proposed = item['base'], item['proposed']
    unknown = sorted((set(base) | set(proposed)) - set(fields))
    if unknown:
        entry['unsupportedFields'] = unknown
        return finish('legacy_group_scope', 'Snapshot contains fields outside the current atomic group')
    current = {k: record[k] for k in fields if k in record}
    entry['groupHashes'] = {k: digest(encoded(v)) for k, v in
                           (('base', base), ('proposed', proposed), ('current', current))}
    different = sorted(k for k in set(current) | set(proposed)
                       if k not in current or k not in proposed or not equal(current[k], proposed[k]))
    entry['differingValueFields'] = [k for k in different if k in value_fields]
    entry['differingEvidenceOrReviewFields'] = [k for k in different if k not in value_fields]
    entry['currentOnlyFields'] = sorted(set(current) - set(proposed))
    entry['proposedOnlyFields'] = sorted(set(proposed) - set(current))
    if family == 'documentFields':
        entry['currentEvidence'] = assess(record, current, as_of=as_of, holds=holds)
        entry['proposedEvidence'] = assess(record, proposed, as_of=as_of, holds=holds)
    else:
        entry['subscriptionComparison'] = subscription_comparison(
            record, base, proposed, current, as_of=as_of, holds=holds)
    # Equality is kept separate from source acceptance, including equal bad data.
    if equal(current, proposed):
        state = 'already_applied_exact'
    elif family == 'documentFields' and equal(without_policy_clock(current), without_policy_clock(proposed)):
        state = 'policy_clock_only'
    elif equal(base, proposed):
        state = 'no_change_proposal'
    elif equal(current, base):
        state = 'base_unchanged'
    else:
        state = 'still_conflicting'
    result = finish(state)
    if family == 'subscriptionSnapshot':
        result['nextAction'] = ('Review the full retained snapshot and original source URL/issuer binding; compare source versus collection clocks. '
                                'Do not accept, supersede or infer final subscription from recency or equality alone.')
    return result


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
    documents = [e for e in entries if (e['path'][2:] if isinstance(e.get('path'), list) else []) == ['documentFields']]
    subscriptions = [e for e in entries if (e['path'][2:] if isinstance(e.get('path'), list) else []) == ['subscriptionSnapshot']]
    return {
        'schemaVersion': 2, 'scope': 'read-only-document-and-subscription-triage-not-source-acceptance',
        'asOf': as_of.isoformat(), 'resolutionsApplied': 0,
        'comparisonRules': {'completeAtomicGroup': list(DOCUMENT_FIELDS),
                            'subscriptionAtomicGroup': list(SUBSCRIPTION_FIELDS),
                            'subscriptionClockException': None,
                            'clockOnlyException': 'staticSourcePolicy.checkedAt',
                            'allOccurrencesRetained': True, 'newestWriterWins': False},
        'summary': {'retainedProposals': len(entries),
                    'documentFieldProposals': len(documents),
                    'subscriptionSnapshotProposals': len(subscriptions),
                    'subscriptionByComparisonState': dict(sorted(Counter(e['comparisonState'] for e in subscriptions).items())),
                    'subscriptionObservationRelations': dict(sorted(Counter(e['subscriptionComparison']['observationRelation']
                        for e in subscriptions if 'subscriptionComparison' in e).items())),
                    'byComparisonState': dict(sorted(Counter(e['comparisonState'] for e in entries).items())),
                    'documentWithValueDifferences': sum(bool(e.get('differingValueFields')) for e in documents),
                    'documentWithEvidenceOrReviewDifferences': sum(bool(e.get('differingEvidenceOrReviewFields')) for e in documents),
                    'duplicateFingerprintOccurrences': sum(n - 1 for n in Counter(
                        e['fingerprint'] for e in entries if isinstance(e.get('fingerprint'), str)).values())},
        'entries': entries,
    }


def load_decisions(path):
    """Load review notes as evidence-bound advice, never publication authority."""
    raw = Path(path).read_bytes()
    ledger = read_json(raw)
    if (not isinstance(ledger, dict) or type(ledger.get('schemaVersion')) is not int
            or ledger['schemaVersion'] != 1
            or not isinstance(ledger.get('decisions'), list)):
        raise ValueError('Invalid proposal-decision ledger')
    seen, evidence_hashes = set(), {}
    for decision in ledger['decisions']:
        if not isinstance(decision, dict):
            raise ValueError('Invalid proposal-decision event')
        key = decision.get('reviewId')
        if (not isinstance(key, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', key)
                or key in seen):
            raise ValueError('Invalid or duplicate proposal review ID')
        seen.add(key)
        if decision.get('decision') != 'do_not_apply_as_proposed':
            raise ValueError('Review advice cannot accept, resolve or delete a proposal')
        for field in ('fingerprint', 'proposalSha256', 'acceptedGroupSha256',
                      'displayHoldsSha256', 'evidenceSha256'):
            if not isinstance(decision.get(field), str) or not re.fullmatch(r'[a-f0-9]{64}', decision[field]):
                raise ValueError('Invalid decision hash: ' + field)
        if not isinstance(decision.get('acceptedCommit'), str) or not re.fullmatch(r'[a-f0-9]{40}', decision['acceptedCommit']):
            raise ValueError('Decision needs an immutable accepted commit')
        identity = decision.get('identity')
        if (not isinstance(identity, dict)
                or set(identity) != {'id', 'company', 'symbol', 'openDate'}
                or not all(isinstance(v, str) and v for v in identity.values())
                or decision.get('path') != ['ipos', identity['id'], 'documentFields']):
            raise ValueError('Decision requires exact issuer and offer identity')
        date.fromisoformat(identity['openDate'])
        for field in ('reviewedAt', 'runId', 'reason', 'nextAction'):
            if not isinstance(decision.get(field), str) or not decision[field].strip():
                raise ValueError('Missing decision ' + field)
        if datetime.fromisoformat(decision['reviewedAt']).tzinfo is None:
            raise ValueError('Decision review time needs a timezone')
        fields = decision.get('reviewedFields')
        if (not isinstance(fields, list) or not fields
                or not all(isinstance(f, str) and f in VALUE_FIELDS for f in fields)
                or len(fields) != len(set(fields))):
            raise ValueError('Decision needs explicit supported reviewed fields')
        name = decision.get('evidenceFile')
        if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]*\.md', name):
            raise ValueError('Unsafe review evidence filename')
        target = Path(path).parent / name
        if target.resolve().parent != Path(path).parent.resolve():
            raise ValueError('Review evidence escaped its directory')
        actual = digest(target.read_bytes())
        if actual != decision['evidenceSha256']:
            raise ValueError('Review evidence changed; retain the original and add a new review')
        evidence_hashes[name] = actual
    return ledger['decisions'], {'ledger': digest(raw), 'evidence': evidence_hashes}


def annotate_decisions(report, canonical, decisions, *, holds_sha256):
    """Expose every review event; changed evidence invalidates advice, not history.

    Never select a newest review, suppress an occurrence, change its comparison
    state, or write a disposition into pending_updates. All bindings must match.
    """
    records = defaultdict(list)
    for row in canonical['ipos']:
        records[row['id']].append(row)
    audits = []
    for decision in decisions:
        matches = [entry for entry in report['entries']
                   if entry.get('fingerprint') == decision['fingerprint']]
        event = {'reviewId': decision['reviewId'], 'fingerprint': decision['fingerprint'],
                 'decision': decision['decision'], 'reviewedAt': decision['reviewedAt'],
                 'evidenceFile': decision['evidenceFile'], 'evidenceSha256': decision['evidenceSha256'],
                 'occurrences': []}
        for entry in matches:
            rows = records.get(decision['identity']['id'], [])
            state = 'applicable'
            if (entry.get('path') != decision['path'] or entry.get('runId') != decision['runId']
                    or entry['proposalSha256'] != decision['proposalSha256']
                    or entry['comparisonState'] == 'malformed_proposal'):
                state = 'proposal_mismatch'
            elif len(rows) != 1 or not all(rows[0].get(k) == v for k, v in decision['identity'].items()):
                state = 'identity_mismatch'
            else:
                group = {k: rows[0][k] for k in DOCUMENT_FIELDS if k in rows[0]}
                current = digest(encoded(without_policy_clock(group)))
                evidence = entry.get('currentEvidence', {})
                if (current != decision['acceptedGroupSha256']
                        or holds_sha256 != decision['displayHoldsSha256']
                        or evidence.get('status') != 'assessed'
                        or any(evidence.get('fieldStates', {}).get(f) != 'final_verified'
                               for f in decision['reviewedFields'])):
                    state = 'stale_evidence'
            advice = {'reviewId': decision['reviewId'], 'bindingStatus': state,
                      'decision': decision['decision'], 'evidenceFile': decision['evidenceFile']}
            if state == 'applicable':
                advice.update(reason=decision['reason'], nextAction=decision['nextAction'])
            else:
                advice['nextAction'] = 'Re-review this decision against the changed proposal, identity or source evidence.'
            entry.setdefault('reviewDecisions', []).append(advice)
            event['occurrences'].append({'inputIndex': entry['inputIndex'], 'bindingStatus': state})
        # Preserve events even if the matching proposal is absent from this input.
        event['bindingStatus'] = 'unmatched' if not matches else (
            'applicable' if all(o['bindingStatus'] == 'applicable' for o in event['occurrences']) else 'needs_revalidation')
        audits.append(event)
    report['reviewDecisionAudit'] = {'decisionsRecorded': len(audits), 'resolutionsApplied': 0,
                                    'events': audits}


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
    decisions, review_hashes = load_decisions(ROOT / 'docs/reviews/pending-proposal-decisions.json')
    annotate_decisions(report, canonical, decisions, holds_sha256=digest(raw['displayHolds']))
    report['reviewDecisionInputs'] = review_hashes
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
