"""Conserve accepted records independently of collector/publication mode.

A new source attempt is not permission to delete a receipt or its audit trail.
Corrections must bind the exact previous and replacement values. Public expiry
and holds are projection decisions and never justify deleting stored evidence.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

HISTORIES = ('dataCorrections', 'subscriptionHistory', 'sourceObservationHistory')
PROOFS = ('activeOfferTerms', 'staticFieldProvenance', 'documentFieldProvenance',
          'universeAdmission', 'lotSizeEvidence', 'listingDateEvidence')
VALUES = ('priceBand', 'lotSize', 'marketLot', 'minimumBidQuantity', 'issueSizeCr',
          'freshIssueCr', 'ofsCr', 'issueComposition', 'financials', 'leadManagers',
          'registrar', 'promoters', 'objectsOfIssue', 'shareholding', 'listing.issuePrice',
          'listingDate', 'subscription', 'subscriptionSource', 'subscriptionSourceUrl',
          'subscriptionObservedAt', 'subscriptionCollectedAt')
REVIEWS = ('issueCompositionReview', 'objectsOfIssueReview')


def present(value):
    return value not in (None, '', [], {})


def durable_record(row):
    return any(present(row.get(k)) for k in (*PROOFS, *HISTORIES, *REVIEWS))


def value_at(row, path):
    if path.startswith('staticFieldProvenance.'):
        return (row.get('staticFieldProvenance') or {}).get(path[len('staticFieldProvenance.'):])
    for key in path.split('.'):
        row = row.get(key) if isinstance(row, dict) else None
    return row


def _incomplete_observation(old, new, receipt):
    if not isinstance(old, dict):
        return False
    if not isinstance(new, dict):
        return True
    fields = ('openDate', 'closeDate', *receipt.get('fields', {}))
    paths = (*fields, *('staticOfferTerms.' + f for f in receipt.get('fields', {})))
    return any(present(value_at(old, p)) and not present(value_at(new, p)) for p in paths)


def merge_observations_for_receipt(base, incoming):
    observations = copy.deepcopy(base.get('observations') or {})
    history = copy.deepcopy(base.get('sourceObservationHistory') or [])
    receipt = base.get('activeOfferTerms') or {}
    for family, observation in (incoming.get('observations') or {}).items():
        old = observations.get(family)
        if receipt and _incomplete_observation(old, observation, receipt):
            # Keep the whole old observation with its original clock. Never
            # combine a new check timestamp with borrowed values.
            continue
        if receipt and old and old != observation:
            event = {'source': family, 'observation': copy.deepcopy(old),
                     'reason': 'Superseded by a complete source observation'}
            if event not in history:
                history.append(event)
        observations[family] = copy.deepcopy(observation)
    result = {'observations': observations}
    if history:
        result['sourceObservationHistory'] = history
    return result


def _events(row, previous=None):
    old = (previous or {}).get('dataCorrections') or []
    events = row.get('dataCorrections') or []
    # Identical source corrections can legitimately be appended again after a
    # later reversal. Count occurrences; an old event alone is never authority.
    if events[:len(old)] != old:
        return []
    return [e for e in events[len(old):] if isinstance(e, dict)]


def _transition(row, field, old, new, previous=None):
    # Unrelated correction reasons, old events or an unbound hold cannot excuse
    # a different loss. Compound quarantine events bind each component exactly.
    for event in _events(row, previous):
        if not event.get('reason'):
            continue
        if event.get('field') == field and event.get('before') == old and event.get('after') == new:
            typed = (event.get('kind') == 'retained-provenance-transition'
                     and event.get('policy') == 'final-prospectus-only'
                     and field.startswith(('staticFieldProvenance.', 'documentFieldProvenance', 'lotSizeEvidence')))
            sourced = bool(event.get('sourceUrl') and (event.get('sha256') or event.get('evidence')))
            quarantine = any((row.get(k) or {}).get('snapshot') == event for k in REVIEWS)
            if event.get('correctedAt') and (typed or sourced or quarantine):
                return True
        if field in ('issueComposition', 'issueSizeCr', 'freshIssueCr', 'ofsCr'):
            snapshot = (row.get('issueCompositionReview') or {}).get('snapshot')
            if (snapshot == event and isinstance(event.get('before'), dict)
                    and isinstance(event.get('after'), dict)
                    and event['before'].get(field) == old and event['after'].get(field) == new):
                return True
    return False


def _retained_proof(row, field, old, new, previous=None):
    if _transition(row, field, old, new, previous):
        return True
    for event in _events(row, previous):
        if not event.get('reason'):
            continue
        if field.startswith('staticFieldProvenance.'):
            key = field[len('staticFieldProvenance.'):]
            source = event.get('sourceEvidence')
            if (event.get('field') == 'staticFieldProvenance'
                    and key in event.get('fields', [])
                    and isinstance(event.get('before'), dict) and isinstance(event.get('after'), dict)
                    and event['before'].get(key) == old and event['after'].get(key) == new
                    and event.get('sourceReviewUrl') and event.get('correctedAt')):
                return True
            if (event.get('field') == key and source == old
                    and event.get('after') == value_at(row, key)):
                return True
            if ((row.get('issueCompositionReview') or {}).get('snapshot') == event
                    and isinstance(source, dict) and source.get(key) == old):
                return True
        if (field == 'documentFieldProvenance' and event.get('documentProvenance') == old
                and (row.get('objectsOfIssueReview') or {}).get('snapshot') == event):
            return True
    return False


def preservation_problems(before, after):
    old_rows = before.get('ipos')
    new_rows = after.get('ipos')
    if not isinstance(old_rows, list) or not isinstance(new_rows, list):
        return ['Missing accepted issuer inventory']
    rows = {r.get('id'): r for r in new_rows if isinstance(r, dict)}
    if len(rows) != len(new_rows):
        return ['Duplicate or invalid candidate issuer inventory']
    problems = []
    for old in old_rows:
        key = old.get('id')
        new = rows.get(key)
        if new is None:
            problems.append(f'{key}: accepted issuer removed')
            continue
        for field in HISTORIES:
            history = old.get(field) or []
            candidate = new.get(field) or []
            # Preserve every event, its order and duplicate multiplicity.
            pos = 0
            for event in history:
                while pos < len(candidate) and candidate[pos] != event:
                    pos += 1
                if pos == len(candidate):
                    problems.append(f'{key}.{field}: accepted history removed or rewritten')
                    break
                pos += 1
        paths = [p for p in PROOFS if p != 'staticFieldProvenance']
        paths += ['staticFieldProvenance.' + p for p in (old.get('staticFieldProvenance') or {})]
        for field in paths:
            previous, current = value_at(old, field), value_at(new, field)
            if present(previous) and previous != current and not _retained_proof(new, field, previous, current, old):
                problems.append(f'{key}.{field}: accepted evidence removed or replaced without exact history')
        for field in set(VALUES) | set(old.get('staticFieldProvenance') or {}):
            previous, current = value_at(old, field), value_at(new, field)
            proof = (old.get('staticFieldProvenance') or {}).get(field)
            if present(previous) and (not present(current) or (proof and previous != current)):
                if not _transition(new, field, previous, current, old):
                    problems.append(f'{key}.{field}: unexplained accepted value loss/change')
        for field in REVIEWS:
            previous, current = old.get(field), new.get(field)
            if not present(previous) or previous == current:
                continue
            # Resolution may narrow fields/status, never erase the audit snapshot.
            if not isinstance(current, dict) or current.get('snapshot') != previous.get('snapshot'):
                problems.append(f'{key}.{field}: review history removed')
        receipt = old.get('activeOfferTerms') or {}
        source_receipt = receipt.get('source') or {}
        urls = {v.get('url') for v in (source_receipt, source_receipt.get('index') or {}) if isinstance(v, dict)}
        if receipt:
            for family, observation in (old.get('observations') or {}).items():
                candidate = (new.get('observations') or {}).get(family)
                if _incomplete_observation(observation, candidate, receipt):
                    problems.append(f'{key}.observations.{family}: incomplete recollection erased accepted comparison evidence')
        for source in old.get('sources') or []:
            if source.get('url') in urls and source not in (new.get('sources') or []):
                problems.append(f'{key}.sources: accepted receipt source removed or restamped')
    return problems


def assert_preserved(before, after):
    problems = preservation_problems(before, after)
    from source_review_holds import display_holds, display_hold_matches
    old_rows = {r['id']: r for r in before.get('ipos', [])}
    new_rows = {r['id']: r for r in after.get('ipos', [])}
    for hold in display_holds():
        old, new = old_rows.get(hold['id']), new_rows.get(hold['id'])
        if not old or not new:
            continue
        for field, binding in hold['fields'].items():
            if display_hold_matches(old, field, hold) and not display_hold_matches(new, field, hold):
                proof = (new.get('staticFieldProvenance') or {}).get(field) or {}
                # A different accepted Final Prospectus may supersede a held
                # source. Merely deleting/archiving its proof cannot clear it.
                replacement = (proof.get('sha256') and proof.get('sha256') != binding.get('sha256')
                    and proof.get('value') == value_at(new, field) and proof.get('documentType') == 'PROSPECTUS'
                    and proof.get('issueOpenDate') == new.get('openDate') and proof.get('evidence'))
                if not replacement and hold.get('scope', 'value') == 'value' and proof:
                    from reviewed_evidence import load_groups
                    replacement = any(
                        group.get('proofs', {}).get(field) == proof
                        and all(new.get(k) == v for k, v in group['identity'].items())
                        and proof.get('value') == value_at(new, field)
                        and any(e.get('field') == 'staticFieldProvenance'
                                and e.get('sourceReviewUrl') == group.get('sourceReviewUrl')
                                and (e.get('after') or {}).get(field) == proof for e in _events(new, old))
                        for group in load_groups())
                if hold.get('scope') == 'subscription_snapshot':
                    replacement = present(new.get('subscription')) and present(new.get('subscriptionSourceUrl'))
                if not replacement:
                    problems.append(f"{hold['id']}.{field}: applicable hold lost without replacement evidence")
    for key, old in old_rows.items():
        new = new_rows.get(key, {})
        for field, review in (old.get('dataReview') or {}).items():
            if (new.get('dataReview') or {}).get(field) != review:
                problems.append(f'{key}.dataReview.{field}: unresolved review changed without retained resolution')
    if problems:
        raise ValueError('Accepted-data preservation failed: ' + '; '.join(problems[:20]))
    return {'status': 'passed', 'comparedRecords': len(before['ipos']),
            'protectedRecords': sum(durable_record(r) for r in before['ipos'])}


def retain_provenance_changes(before, after, *, reason, checked_at):
    """Called only by the existing Final Prospectus policy, never collectors.

    Archive exact proof transitions, including same-value re-extraction and
    policy withdrawal. A collection check alone leaves old proof bytes intact.
    """
    paths = ['documentFieldProvenance', 'lotSizeEvidence']
    paths += ['staticFieldProvenance.' + p for p in (before.get('staticFieldProvenance') or {})]
    for path in paths:
        old, new = value_at(before, path), value_at(after, path)
        if not present(old) or old == new:
            continue
        def without_check(v):
            return {k: v for k, v in v.items() if k != 'checkedAt'} if isinstance(v, dict) else v
        if without_check(old) == without_check(new):
            if path.startswith('staticFieldProvenance.'):
                after.setdefault('staticFieldProvenance', {})[path[len('staticFieldProvenance.'):]] = copy.deepcopy(old)
                continue
            target = after
            parts = path.split('.')
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = copy.deepcopy(old)
            continue
        if _retained_proof(after, path, old, new):
            continue
        after.setdefault('dataCorrections', []).append({
            'field': path, 'before': copy.deepcopy(old), 'after': copy.deepcopy(new),
            'reason': reason, 'correctedAt': checked_at,
            'kind': 'retained-provenance-transition', 'policy': 'final-prospectus-only',
        })


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--base', type=Path, required=True)
    cli.add_argument('--candidate', type=Path, default=Path('data/ipos.json'))
    args = cli.parse_args()
    print(json.dumps(assert_preserved(json.loads(args.base.read_text()), json.loads(args.candidate.read_text()))))


if __name__ == '__main__':
    main()
