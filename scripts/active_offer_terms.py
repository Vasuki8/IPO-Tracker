"""Reviewed active exchange disclosures; never Final Prospectus facts.

Parsing produces candidates only. Selection requires a separately reviewed,
source-byte-bound receipt and the same active issuer/offer. No network or writes.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
from bse_active_offer_terms import VERSION as BSE_VERSION, FIELDS as BSE_FIELDS, IDENTITY as BSE_IDENTITY

VERSION = 'nse-labelled-active-terms-v1'
NSE_FIELDS = {'priceBand', 'lotSize', 'minimumBidQuantity', 'issueComposition'}
FIELDS = NSE_FIELDS | BSE_FIELDS
IDENTITY = ('id', 'company', 'symbol', 'board', 'openDate', 'closeDate')


def identity_fields(receipt):
    return BSE_IDENTITY if receipt.get('parserVersion') == BSE_VERSION else IDENTITY


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _text(value):
    return ' '.join(str(value or '').strip('"').split())


def _name(value):
    return re.sub(r'[^a-z0-9]', '', re.sub(r'\bltd\.?\b', 'limited', _text(value).lower()))


def _number(value):
    # Accept ungrouped, Western and Indian separators, never malformed commas.
    if not re.fullmatch(r'(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})(?:\.\d+)?', value):
        raise ValueError('Ambiguous numeric grouping')
    return Decimal(value.replace(',', ''))


def parse_response(response_text, identity):
    """Replay only the issueInfo label/value family, excluding demand tables."""
    source = json.loads(response_text)
    meta = source.get('metaInfo') or {}
    for container in (source, meta):
        if (container.get('symbol') not in (None, identity['symbol'])
                or container.get('series') not in (None, 'SME' if identity['board'] == 'SME' else 'EQ')
                or container.get('board') not in (None, identity['board'])
                or container.get('isDebtSec') not in (None, False)):
            raise ValueError('Conflicting official identity/category metadata')
    if meta.get('companyName') and _name(meta['companyName']) != _name(identity['company']):
        raise ValueError('Conflicting official issuer name')
    info = source['issueInfo']
    rows = info['dataList']
    if not isinstance(rows, list):
        raise ValueError('Missing labelled source table')
    labels = {}
    for index, row in enumerate(rows):
        label = _text(row.get('title')).lower()
        if not label:
            continue
        value = _text(row.get('value'))
        if label in labels and labels[label]['text'] != value:
            raise ValueError('Conflicting duplicate source label: ' + label)
        labels.setdefault(label, {'text': value, 'row': index, 'title': row['title'], 'raw': row.get('value')})
    names = [info.get('heading')]
    names += [r.get('title') for r in rows if r.get('title') and not _text(r.get('value'))]
    names = [name for name in names if name]
    if (not names or any(_name(name) != _name(identity['company']) for name in names)
            or source.get('companyName') != identity['symbol']
            or labels['symbol']['text'] != identity['symbol']
            or (info.get('symbol') and info['symbol'] != identity['symbol'])):
        raise ValueError('Conflicting issuer identity')
    period = labels['issue period']['text'].split(' to ')
    dates = [datetime.strptime(value, '%d-%b-%Y').date().isoformat() for value in period]
    if dates != [identity['openDate'], identity['closeDate']] or dates[0] > dates[1]:
        raise ValueError('Conflicting offer period')
    fields, unresolved = {}, {}

    def accept(field, value, label, unit):
        item = labels[label]
        fields[field] = {'value': value, 'unit': unit, 'row': item['row'],
                         'title': item['title'], 'raw': item['raw'],
                         'table': '/issueInfo/dataList'}

    price = labels.get('price range', {}).get('text', '')
    match = re.fullmatch(r'Rs\.\s*(\d+(?:\.\d+)?) to Rs\.\s*(\d+(?:\.\d+)?) per equity share', price, re.I)
    if match and 0 < Decimal(match[1]) <= Decimal(match[2]):
        accept('priceBand', {'min': float(match[1]), 'max': float(match[2])}, 'price range', 'INR/share')
    else:
        unresolved['priceBand'] = 'parser-unsupported: expected explicit INR price range'
    for field, names in [('lotSize', ('bid lot', 'lot size')), ('minimumBidQuantity', ('minimum order quantity',))]:
        found = [name for name in names if name in labels]
        values = []
        for name in found:
            match = re.fullmatch(r'(\d+) equity shares(?: and in multiples thereof)?', labels[name]['text'], re.I)
            if not match or not 0 < int(match[1]) <= 100000:
                values.append(None)
            else:
                values.append(int(match[1]))
        if values and None not in values and len(set(values)) == 1:
            accept(field, values[0], found[0], 'shares')
        elif len(set(values)) > 1:
            raise ValueError('Conflicting lot labels')
        else:
            unresolved[field] = 'disclosure-absent' if not found else 'parser-unsupported'
    size = labels.get('issue size', {}).get('text', '')
    composition = dict.fromkeys(('freshShares', 'ofsShares', 'freshValueCr', 'ofsValueCr'))
    qualifiers = {}
    # Complete gross fresh offering with parenthetical reservations. The market
    # maker/anchor/employee allocation is not a separate fresh/OFS leg.
    fresh = re.fullmatch(r'Initial Public (?:Offer|Offering) comprising of Fresh (?:Issue|offer) (up to )?([\d,]+) Equity Shares(?: \(including [^()]+\))?', size, re.I)
    mixed = re.fullmatch(r'Initial Public offering comprising of fresh issue of aggregating up to Rs\. ([\d,.]+) million and Offer for sale up to ([\d,]+) Equity shares\.', size, re.I)
    if fresh:
        composition['freshShares'] = int(_number(fresh[2]))
        qualifiers['freshShares'] = 'up_to' if fresh[1] else 'reported'
    elif mixed:
        composition['freshValueCr'] = float(_number(mixed[1]) / 10)
        composition['ofsShares'] = int(_number(mixed[2]))
        qualifiers = {'freshValueCr': 'up_to', 'ofsShares': 'up_to'}
    if qualifiers and all(value is None or value > 0 for value in composition.values()):
        composition['qualifiers'] = qualifiers
        accept('issueComposition', composition, 'issue size', 'shares; INR crore (million / 10)')
    else:
        unresolved['issueComposition'] = 'parser-unsupported: incomplete or ambiguous offer composition'
    # Shares multiplied by a cap price are never an observed total amount.
    unresolved['issueSizeCr'] = ('disclosure-absent: no explicit total INR amount in the supported source table'
                                 if qualifiers else 'parser-unsupported: total amount not established by this layout')
    return {'fields': fields, 'unresolved': unresolved}


def _timestamp(value):
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() is None:
        raise ValueError('Timestamp requires a timezone')
    return parsed


def validate_receipt(receipt, identity):
    """Validate an approved receipt without giving parser success review status."""
    bse = receipt.get('parserVersion') == BSE_VERSION
    if (receipt.get('schemaVersion') != 1 or receipt.get('parserVersion') not in {VERSION, BSE_VERSION}
            or receipt.get('identity') != {key: identity[key] for key in identity_fields(receipt)}
            or set(receipt.get('fields') or {}) - (BSE_FIELDS if bse else NSE_FIELDS) or not receipt.get('fields')):
        raise ValueError('Invalid reviewed active offer identity/schema')
    board = identity['board']
    if board not in {'SME', 'Mainboard'}:
        raise ValueError('Unsupported offer board')
    source = receipt['source']
    if (source.get('authority') != 'official_exchange'
            or source.get('name') != ('BSE' if bse else 'NSE') or source.get('observedAt') is not None
            or 'observedAt' not in source
            or hashlib.sha256(source['responseText'].encode()).hexdigest() != source.get('sha256')):
        raise ValueError('Active terms need exact official response bytes and an unknown source clock')
    collected = _timestamp(source['collectedAt'])
    if bse:
        index = source['index']
        if (index.get('observedAt') is not None or 'observedAt' not in index
                or hashlib.sha256(index['responseText'].encode()).hexdigest() != index.get('sha256')):
            raise ValueError('BSE terms need exact current-index bytes and an unknown observation clock')
        collected = max(collected, _timestamp(index['collectedAt']))
    else:
        series = 'SME' if board == 'SME' else 'EQ'
        expected = f"https://www.nseindia.com/api/ipo-detail?symbol={identity['symbol']}&series={series}"
        if source.get('url') != expected:
            raise ValueError('Active NSE terms need the exact official symbol/series URL')
    review = receipt['review']
    if (review.get('version') != 1 or review.get('status') != 'accepted'
            or _timestamp(review['reviewedAt']) < collected
            or not re.fullmatch(r'https://github\.com/Vasuki8/IPO-Tracker/blob/[a-f0-9]{40}/docs/reviews/[a-z0-9.-]+\.md', str(review.get('url') or ''))):
        raise ValueError('Active terms require an immutable, dated source review')
    expected = {'fields': receipt['fields'], 'unresolved': receipt.get('unresolved')}
    if bse:
        from bse_active_offer_terms import parse_response as parse_bse_response
        parsed = parse_bse_response(source, identity)
        expected['sourceIdentity'] = receipt.get('sourceIdentity')
    else:
        parsed = parse_response(source['responseText'], identity)
    if parsed != expected:
        raise ValueError('Reviewed terms do not replay from exact source rows')
    return receipt['fields']


def receipt_problems(record):
    """Expose contradictions as retained review tasks, never as missing data."""
    receipt = record.get('activeOfferTerms')
    if receipt is None:
        return {}
    try:
        fields = validate_receipt(receipt, record)
    except (KeyError, ValueError, TypeError, AttributeError, OverflowError) as exc:
        return {field: 'Invalid active offer receipt: ' + str(exc) for field in sorted(FIELDS)}
    problems = {}
    for family in ('NSE', 'BSE'):
        observation = (record.get('observations') or {}).get(family)
        if not isinstance(observation, dict):
            continue
        if observation.get('openDate') == record['openDate'] and observation.get('closeDate') == record['closeDate']:
            for field, proof in fields.items():
                # Compare both retained locations, so one cannot mask a conflict
                # in the other. Do not compare derived total issue amounts.
                values = [observation.get(field), (observation.get('staticOfferTerms') or {}).get(field)]
                if any(value is not None and value != proof['value'] for value in values):
                    problems[field] = f'Active offer receipt conflicts with same-offer {family} {field}; source review required'
    return problems


def accepted_terms(record, today=None):
    """Expire after the IST close date; preserve conflicting and held evidence."""
    today = today or datetime.now(ZoneInfo('Asia/Kolkata')).date()
    receipt = record.get('activeOfferTerms')
    if not isinstance(receipt, dict):
        return {}
    try:
        fields = validate_receipt(receipt, record)
        opens, closes = [date.fromisoformat(record[k]) for k in ('openDate', 'closeDate')]
        collected_day = _timestamp(receipt['source']['collectedAt']).astimezone(ZoneInfo('Asia/Kolkata')).date()
        if (opens > closes or not collected_day <= today <= closes
                or str(record.get('status') or '').lower() not in {'open', 'upcoming'}
                or (record.get('listingDate') and date.fromisoformat(record['listingDate']) <= today)):
            return {}
        problems = receipt_problems(record)
        return {field: proof for field, proof in fields.items() if field not in problems}
    except (KeyError, ValueError, TypeError, AttributeError, OverflowError):
        return {}
