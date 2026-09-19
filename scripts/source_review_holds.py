"""Shared bindings for unresolved public-source holds and operational reviews.

Matching never changes canonical values or resolves a review. Document conflicts
bind the issuer, offer and PDF bytes; layout holds bind the retained value too.
"""
from __future__ import annotations

import copy
from datetime import date, datetime
import math
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

from final_prospectus_policy import field_value

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = 'data/public_display_holds.json'
HOLD_REVIEW_TYPES = frozenset({'document_conflict', 'source_display_hold', 'subscription_snapshot_conflict'})
IDENTITY_KEYS = ('id', 'company', 'symbol', 'openDate')
COLLECTION_CLOCKS = frozenset({'subscriptionAsOf', 'subscriptionCollectedAt'})


def subscription_snapshot(record):
    """Exact attributed snapshot, including absent keys; history is separate."""
    return {key: copy.deepcopy(value) for key, value in record.items()
            if key.startswith('subscription') and key != 'subscriptionHistory'}


def snapshot_facts(snapshot):
    # Rechecking a mixed snapshot is not source reconciliation. Retain clocks in
    # the review binding, but a collection-only clock bump cannot release it.
    return {key: value for key, value in snapshot.items() if key not in COLLECTION_CLOCKS}


def _validate_subscription_hold(hold):
    identity = hold.get('identity')
    if (not isinstance(identity, dict)
            or set(identity) != {*IDENTITY_KEYS, 'closeDate'}
            or not all(isinstance(v, str) and v for v in identity.values())
            or identity['id'] != hold['id']):
        raise ValueError('Subscription hold requires exact issuer and offer identity')
    if date.fromisoformat(identity['openDate']) > date.fromisoformat(identity['closeDate']):
        raise ValueError('Subscription hold has reversed offer dates')
    if set(hold['fields']) != {'subscription'}:
        raise ValueError('Subscription snapshot hold cannot target static fields')
    binding = hold['fields']['subscription']
    if not isinstance(binding, dict) or set(binding) != {'snapshot', 'snapshotDigest'}:
        raise ValueError('Subscription hold requires a complete snapshot, not PDF evidence')
    snapshot = binding['snapshot']
    if (not isinstance(snapshot, dict) or 'subscription' not in snapshot
            or any(not key.startswith('subscription') or key == 'subscriptionHistory' for key in snapshot)):
        raise ValueError('Invalid subscription snapshot binding')
    values = snapshot['subscription']
    if (not isinstance(values, dict) or not values
            or any(v is not None and (type(v) not in (int, float) or not math.isfinite(v) or v < 0)
                   for v in values.values())):
        raise ValueError('Subscription hold must retain finite source multiples or nulls')
    if value_digest(snapshot) != binding['snapshotDigest']:
        raise ValueError('Subscription snapshot fingerprint mismatch')
    if (not isinstance(hold.get('review'), str) or not hold['review'].startswith('https://')
            or not isinstance(hold.get('reason'), str) or not hold['reason']
            or not isinstance(hold.get('reviewedAt'), str)
            or datetime.fromisoformat(hold['reviewedAt']).tzinfo is None):
        raise ValueError('Subscription hold requires dated review evidence')


def value_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _validate_hold(hold):
    if not isinstance(hold, dict) or not isinstance(hold.get('id'), str) or not hold['id']:
        raise ValueError('Public display hold requires an issue id')
    scope = hold.get('scope', 'value')
    if scope not in {'value', 'document', 'subscription_snapshot'}:
        raise ValueError('Unsupported public display hold scope')
    if not isinstance(hold.get('fields'), dict) or not hold['fields']:
        raise ValueError('Public display hold requires field bindings')
    if scope == 'subscription_snapshot':
        _validate_subscription_hold(hold)
        return
    for field, binding in hold['fields'].items():
        if (not isinstance(field, str) or not field or not isinstance(binding, dict)
                or not re.fullmatch(r'[a-f0-9]{64}', str(binding.get('sha256') or ''))):
            raise ValueError('Public display hold requires a field and exact PDF fingerprint')
        if scope == 'value' and not re.fullmatch(r'[a-f0-9]{64}', str(binding.get('valueDigest') or '')):
            raise ValueError('Value display hold requires an exact value fingerprint')
    # Old value-only reviews retain their original scope. An explicitly supplied
    # issuer/offer binding must never be silently ignored, including for layout holds.
    if scope == 'document' or 'identity' in hold:
        identity = hold.get('identity')
        if (not isinstance(identity, dict)
                or not all(isinstance(identity.get(key), str) and identity[key] for key in IDENTITY_KEYS)
                or identity['id'] != hold['id']):
            raise ValueError('Document display hold requires exact issuer and offer identity')


@lru_cache(maxsize=1)
def display_holds():
    # Missing or malformed evidence must fail the build, never restore a value
    # or remove its operational review silently.
    registry = json.loads((ROOT / REGISTRY_PATH).read_text(encoding='utf-8'))
    holds = registry.get('holds') if isinstance(registry, dict) else None
    if not isinstance(holds, list):
        raise ValueError('Public display hold registry requires a holds list')
    for hold in holds:
        _validate_hold(hold)
    return holds


def display_hold_matches(record, field, hold):
    _validate_hold(hold)
    if hold['id'] != record.get('id'):
        return False
    binding = hold['fields'][field]
    if hold.get('scope') == 'subscription_snapshot':
        return (all(record.get(key) == value for key, value in hold['identity'].items())
                and value_digest(snapshot_facts(subscription_snapshot(record)))
                    == value_digest(snapshot_facts(binding['snapshot'])))
    proof, value = _held_field_evidence(record, field)
    if not isinstance(proof, dict):
        return False
    identity = hold.get('identity')
    if identity is not None and (any(record.get(key) != identity[key] for key in IDENTITY_KEYS)
                                 or proof.get('issueOpenDate') != identity['openDate']):
        return False
    if hold.get('scope', 'value') == 'document':
        return proof.get('sha256') == binding['sha256']
    return (proof.get('sha256') == binding['sha256']
            and value_digest(value) == binding['valueDigest'])


def _held_field_evidence(record, field):
    """Read an amount receipt for a hold without creating static provenance.

    Holds bind retained evidence even when it no longer passes parsing or has
    expired; parser success must never be required to retain an existing review.
    """
    if field == 'issueAmountScenarios':
        receipt = record.get('activeOfferTerms')
        amount = receipt.get('amountEvidence') if isinstance(receipt, dict) else None
        if not isinstance(amount, dict):
            return None, None
        identity, source = amount.get('identity') or {}, amount.get('source') or {}
        if any(identity.get(key) != record.get(key) for key in (*IDENTITY_KEYS, 'board', 'closeDate')):
            return None, None
        proof = {'sourceUrl': source.get('url'), 'sha256': source.get('sha256'),
                 'documentDate': source.get('documentDate'), 'documentType': source.get('documentType'),
                 'issueOpenDate': identity.get('openDate'), 'parserVersion': amount.get('parserVersion'),
                 'checkedAt': (amount.get('review') or {}).get('reviewedAt')}
        return proof, ((receipt.get('fields') or {}).get(field) or {}).get('value')
    provenance = record.get('staticFieldProvenance') or {}
    return (provenance.get(field) if isinstance(provenance, dict) else None), field_value(record, field)


def active_hold_reviews(record, holds=None):
    """Return one review per exact active hold, preserving distinct findings."""
    issues = []
    for hold in display_holds() if holds is None else holds:
        _validate_hold(hold)
        if hold['id'] != record.get('id'):
            continue
        for field, binding in hold['fields'].items():
            if not display_hold_matches(record, field, hold):
                continue
            scope = hold.get('scope', 'value')
            proof = _held_field_evidence(record, field)[0] or {}
            source = {key: copy.deepcopy(proof[key]) for key in
                      ('sourceUrl', 'documentType', 'documentDate', 'sha256', 'parserVersion', 'issueOpenDate', 'checkedAt')
                      if proof.get(key) is not None}
            if scope == 'subscription_snapshot':
                source = {key: copy.deepcopy(value) for key, value in binding['snapshot'].items()
                          if key != 'subscription'}
            metadata = {'registryPath': REGISTRY_PATH, 'holdId': hold['id'], 'scope': scope,
                        'source': source, 'binding': copy.deepcopy(binding)}
            for key, target in (('identity', 'identity'), ('review', 'reviewUrl'), ('reviewedAt', 'reviewedAt')):
                if hold.get(key) is not None:
                    metadata[target] = copy.deepcopy(hold[key])
            issue = {
                'id': record.get('id'), 'field': field, 'severity': 'review',
                'reason': hold.get('reason') or 'Published value remains withheld pending resolution of the retained source review.',
                'reviewType': ('subscription_snapshot_conflict' if scope == 'subscription_snapshot'
                               else 'document_conflict' if scope == 'document' else 'source_display_hold'),
                'displayHold': metadata,
            }
            if issue not in issues:
                issues.append(issue)
    return issues
