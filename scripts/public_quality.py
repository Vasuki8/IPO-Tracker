"""Display-only trust boundary. Never mutate canonical values or resolve reviews.

Public projections are deliberately more conservative than data-presence reports.
A retained verification label is not evidence; each published static field needs
its matching Final Prospectus proof, or a dated active-issue observation.
"""
from __future__ import annotations

import copy
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from final_prospectus_policy import STATIC_CANONICAL_FIELDS, field_value, is_final_prospectus
from final_prospectus_identity import known_non_final_document_url
from issue_composition_checks import COMPOSITION_FIELDS, quarantined_fields
from objects_of_issue_checks import objects_quarantined
from source_review_holds import display_holds, display_hold_matches as _display_hold_matches, value_digest
from validate_data import validate_record
from active_offer_terms import accepted_terms, field_source

VERSION = 1
ROOT = Path(__file__).resolve().parents[1]
FIELDS = (*STATIC_CANONICAL_FIELDS, 'marketLot', 'minimumBidQuantity',
          'openDate', 'closeDate', 'listingDate', 'allotmentDate', 'subscription', 'listing')
SUMMARY_FIELDS = ('priceBand', 'lotSize', 'marketLot', 'minimumBidQuantity', 'issueSizeCr', 'subscription', 'listing',
                  'openDate', 'closeDate', 'listingDate')
EXCHANGE_HOSTS = {'nseindia.com', 'www.nseindia.com', 'nsearchives.nseindia.com',
                  'archives.nseindia.com', 'bseindia.com', 'www.bseindia.com', 'beta.bseindia.com',
                  'bsesme.com', 'www.bsesme.com'}
DISPLAY_STATES = {'final_verified', 'provisional', 'reported'}


def present(value):
    return value is not None and value != '' and value != [] and value != {}


def safe_url(value):
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    return value if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password else None


def official_url(value):
    # Match the literal authority in both Python and the browser. Do not let
    # URL normalization promote credentials, encoded hosts or lookalike domains.
    match = re.fullmatch(r'https://([a-z0-9.-]+)(?::443)?(?:[/?#][^\s\\]*)?', value, re.I) if isinstance(value, str) else None
    return bool(match and match.group(1).lower() in EXCHANGE_HOSTS)


def _proof_source(proof):
    keys = ('sourceUrl', 'documentDate', 'publicationDate', 'sha256', 'parserVersion', 'checkedAt')
    if proof.get('activeOfferReceipt'):
        keys += ('observedAt', 'collectedAt', 'collectionTimeBasis', 'reviewUrl', 'authority')
    return {key: proof[key] for key in keys
            if proof.get(key) is not None or (key == 'observedAt' and key in proof)}


def _final_proof(record, field, value):
    proof = (record.get('staticFieldProvenance') or {}).get(field) or {}
    try:
        date.fromisoformat(record.get('openDate'))
    except (TypeError, ValueError):
        return None
    if (not present(value) or not isinstance(proof, dict) or proof.get('value') != value
            or not safe_url(proof.get('sourceUrl'))
            or not re.fullmatch(r'[a-f0-9]{64}', str(proof.get('sha256') or ''))
            or proof.get('issueOpenDate') != record.get('openDate')
            or not is_final_prospectus({'type': proof.get('documentType'), 'url': proof.get('sourceUrl')})
            or known_non_final_document_url(record, proof.get('sourceUrl'))
            or field in (record.get('staticSourcePolicy') or {}).get('pendingRevalidationFields', [])):
        return None
    detail = proof.get('evidence')
    # Older synthesized composition envelopes (only normalized values + a
    # "validated" label) have no physical source location. Do not elevate them.
    if not isinstance(detail, dict) or not detail:
        return None
    if field == 'financials' and detail.get('method') == 'reviewed-financial-grid-v1':
        from review_financial_tables import has_reviewed_financial_evidence
        return proof if has_reviewed_financial_evidence(record) else None
    pages = [row.get('page') for row in detail.values() if isinstance(row, dict)] if field == 'financials' else [detail.get('page')]
    if not pages or any(type(page) is not int or page < 1 for page in pages):
        return None
    return proof


def _active(record, today):
    try:
        opens, closes = date.fromisoformat(record['openDate']), date.fromisoformat(record['closeDate'])
    except (KeyError, TypeError, ValueError):
        return False
    return (opens <= closes and today <= closes
            and str(record.get('status') or '').lower() not in {'listed', 'withdrawn', 'cancelled'})


def _provisional_source(record, field, value, today):
    # Narrow initial permission: equal-valued, issue-bound official exchange
    # observations for bidding terms. An attached RHP alone proves no field.
    if field not in {'priceBand', 'lotSize', 'issueSizeCr', 'marketLot', 'minimumBidQuantity'} or not _active(record, today):
        return None
    for family in ('NSE', 'BSE'):
        observation = (record.get('observations') or {}).get(family) or {}
        if observation.get('openDate') != record.get('openDate') or observation.get('closeDate') != record.get('closeDate'):
            continue
        observed = (observation.get('staticOfferTerms') or {}).get(field, observation.get(field))
        if observed != value:
            continue
        for source in record.get('sources') or []:
            if (str(source.get('name', '')).split(' ')[0] == family
                    and official_url(source.get('url')) and source.get('asOf')):
                return {'sourceUrl': source['url'], 'checkedAt': source['asOf'],
                        'provisionalUntil': record['closeDate']}
    return None


def _review_field(path):
    return 'listing.issuePrice' if path == 'listing.issuePrice' else path.split('.')[0]


def _set(record, field, value):
    if field == 'listing.issuePrice':
        if isinstance(record.get('listing'), dict):
            record['listing']['issuePrice'] = value
    else:
        record[field] = value


def _subscription_metadata(record):
    observed = None if record.get('subscriptionTimeBasis') == 'collection-only' else record.get('subscriptionObservedAt')
    collected = record.get('subscriptionCollectedAt') or record.get('subscriptionAsOf')
    source = record.get('subscriptionSource')
    url = safe_url(record.get('subscriptionSourceUrl'))
    # A historical URL belongs to the current snapshot only when values, source
    # and observation time all agree; never pair the first attached exchange URL
    # with a later secondary-source snapshot.
    if not url:
        for row in reversed(record.get('subscriptionHistory') or []):
            if (row.get('source') == source and row.get('observedAt') == observed
                    and all(row.get(k) == (record.get('subscription') or {}).get(k)
                            for k in ('qib', 'nii', 'retail', 'total'))):
                url = safe_url(row.get('sourceUrl'))
                if url:
                    break
    if not url:
        for item in record.get('sources') or []:
            if item.get('name') == source and safe_url(item.get('url')):
                url = item['url']
                break
    authority = ('secondary' if 'secondary' in str(source or '').lower()
                 else 'official_exchange' if official_url(url) else 'unknown')
    return {'subscriptionObservedAt': observed, 'subscriptionCollectedAt': collected,
            'subscriptionTimeBasis': 'source-observation' if observed else 'collection-only',
            'subscriptionSource': source, 'subscriptionSourceUrl': url,
            'subscriptionAuthority': authority}


def project_record(record, *, today=None, holds=None):
    """Return a sanitized copy and compact per-field decisions for every surface."""
    today = today or datetime.now(ZoneInfo('Asia/Kolkata')).date()
    output = copy.deepcopy(record)
    holds = display_holds() if holds is None else list(holds)
    reviews = {}
    for item in validate_record(record, holds=holds):
        reviews.setdefault(_review_field(item['field']), 'source_review')
    for field in (record.get('dataReview') or {}):
        reviews.setdefault(_review_field(field), 'source_review')
    for field in quarantined_fields(record):
        reviews[field] = 'quarantined'
    if objects_quarantined(record):
        reviews['objectsOfIssue'] = 'quarantined'
    for hold in holds:
        if hold['id'] != record.get('id'):
            continue
        for field in hold['fields']:
            if _display_hold_matches(record, field, hold):
                reviews[field] = ('subscription_snapshot_conflict' if hold.get('scope') == 'subscription_snapshot'
                                 else 'document_conflict' if hold.get('scope') == 'document' else 'pending_source_repair')
    if set(COMPOSITION_FIELDS) & set(reviews):
        reviews.update({f: 'composition_review' for f in COMPOSITION_FIELDS})
    if (set(COMPOSITION_FIELDS) | {'priceBand'}) & set(reviews):
        reviews['issueAmountScenarios'] = 'composition_review'

    quality = {}
    active = accepted_terms(record, today)
    sources = []
    def attach_source(decision, proof):
        source = _proof_source(proof)
        if source:
            if source not in sources:
                sources.append(source)
            decision['source'] = sources.index(source)

    # Only records with the supplement need the extra public decision. This
    # preserves existing public payloads and every unrelated issuer exactly.
    receipt = record.get('activeOfferTerms')
    has_scenarios = ('issueAmountScenarios' in record or (isinstance(receipt, dict)
                     and ('amountEvidence' in receipt or 'issueAmountScenarios' in (receipt.get('fields') or {}))))
    fields = (*FIELDS, 'issueAmountScenarios') if has_scenarios else FIELDS
    output.pop('issueAmountScenarios', None)
    for field in fields:
        value = None if field == 'issueAmountScenarios' else field_value(record, field)
        decision = {'state': 'awaiting_disclosure'}
        proof = None
        if field == 'issueAmountScenarios' and field in active:
            # This field is evaluated after the ordinary terms. Their final
            # decisions can discover missing authority even without a retained
            # review item; those withheld inputs must also withhold the pair.
            pair = active[field]['value']
            dependencies = (*COMPOSITION_FIELDS, 'priceBand')
            if (any(quality[name]['state'] == 'under_review' for name in dependencies)
                    or output.get('priceBand') != {'min': pair['floorPrice'], 'max': pair['capPrice']}):
                reviews[field] = 'composition_review'
        if field in reviews:
            decision = {'state': 'under_review', 'reason': reviews[field]}
        elif not present(value) and field in active:
            receipt = record['activeOfferTerms']
            decision = {'state': 'provisional', 'until': record['closeDate'],
                        'row': active[field]['row'], 'table': active[field]['table']}
            if field == 'issueAmountScenarios':
                decision.update({key: active[field][key] for key in ('page', 'unit', 'sourceUnit')})
            attach_source(decision, field_source(receipt, field))
            _set(output, field, copy.deepcopy(active[field]['value']))
        elif not present(value):
            availability = next((v for k, v in (record.get('dataAvailability') or {}).items()
                                 if k.split('.')[-1] == field and isinstance(v, dict)), {})
            if availability.get('status') == 'source-unavailable':
                decision = {'state': 'source_unavailable'}
        elif field in STATIC_CANONICAL_FIELDS or field in {'marketLot', 'minimumBidQuantity'}:
            proof = _final_proof(record, field, value)
            provisional = _provisional_source(record, field, value, today)
            if proof:
                decision = {'state': 'final_verified'}
                attach_source(decision, proof)
                if proof['evidence'].get('page'):
                    decision['page'] = proof['evidence']['page']
            elif provisional:
                decision = {'state': 'provisional', 'until': provisional['provisionalUntil']}
                attach_source(decision, provisional)
            else:
                decision = {'state': 'under_review', 'reason': 'final_evidence_required'}
        else:
            # Market/lifecycle observations are outside Final Prospectus static
            # authority. "Reported" is not a whole-record verification badge.
            decision = {'state': 'reported'}
        if decision['state'] == 'under_review':
            held_proof = (record.get('staticFieldProvenance') or {}).get(field) or {}
            if safe_url(held_proof.get('sourceUrl')):
                attach_source(decision, held_proof)
        quality[field] = decision
        if decision['state'] not in DISPLAY_STATES:
            _set(output, field, None)

    # Dependent amounts/returns must not survive a withheld input. Never infer
    # minimum quantity or minimum application amount from a market/bid lot.
    output.pop('minimumInvestment', None)
    output.pop('minimumApplicationAmount', None)
    if quality['listing.issuePrice']['state'] not in DISPLAY_STATES:
        if isinstance(output.get('listing'), dict):
            output['listing'].pop('gainPct', None)
    output.update(_subscription_metadata(record))
    # No fallback to historical multiples when current subscription is held.
    if quality['subscription']['state'] == 'under_review':
        output['subscriptionHistory'] = []
    output['publicQuality'] = {'version': VERSION, 'fields': quality, 'sources': sources}
    return output


def summary_quality(quality):
    """Keep only directory decisions and their referenced deduplicated sources."""
    out = {'version': VERSION, 'fields': {}, 'sources': []}
    fields = (*SUMMARY_FIELDS, 'issueAmountScenarios') if 'issueAmountScenarios' in quality['fields'] else SUMMARY_FIELDS
    for field in fields:
        decision = dict(quality['fields'][field])
        if 'source' in decision:
            source = quality['sources'][decision['source']]
            if source not in out['sources']:
                out['sources'].append(source)
            decision['source'] = out['sources'].index(source)
        out['fields'][field] = decision
    return out
