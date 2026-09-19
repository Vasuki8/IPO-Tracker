"""Replay reviewed floor/cap monetary disclosures, never shares times a price.

These scanned-source transcriptions require an independent dated source review.
The parser only validates the bounded paragraph/table and unit conversion. It
cannot establish PDF authenticity, approve a transcription, or publish a value.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

VERSION = 'reviewed-floor-cap-amounts-v1'
FIELD = 'issueAmountScenarios'
IDENTITY = ('id', 'company', 'symbol', 'board', 'openDate', 'closeDate')
_NUM = r'(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})(?:\.\d+)?'
ROOT = Path(__file__).resolve().parents[1]
# These source transcriptions were reviewed independently and committed before
# implementation. Their Git blob identities are not supplied by a candidate.
# New evidence requires a new source review and an explicit protected-code change.
REVIEW_URL = 'https://github.com/Vasuki8/IPO-Tracker/blob/6e2df0a4d4c8b736d0c07d526b3b844eaecd0b49/docs/reviews/2026-09-19-qualified-offer-amount-source-review.md'
REVIEWED_BINDINGS = {
    'axiomgas': ('0e2b5a405884318c2ec71c6c07f90567ddf5d3d1',
                 '44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'),
    'varmora': ('c69c776536b69d595b32f9c49aae13e9dc3a9a67',
                '93c6e5207ccedc6c35d8659e58e0de8037421d4855f395f6e703c56b14622b24'),
}


def digest(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def number(token):
    if not isinstance(token, str) or not re.fullmatch(_NUM, token):
        raise ValueError('Ambiguous amount or share token')
    value = Decimal(token.replace(',', ''))
    if value <= 0:
        raise ValueError('Positive disclosed amount or share token required')
    return value


def _name(value):
    return re.sub('[^a-z0-9]', '', str(value).lower())


def amount_observation(observation):
    """Fingerprint the reviewed amount context, excluding collection clocks.

    This identifies already-reviewed derived observations only. It neither
    calculates an amount nor treats an unrecognised scalar as safe evidence.
    """
    summary = observation.get('subscriptionSummary') or {}
    return {'amount': observation.get('issueSizeCr'),
            'staticAmount': (observation.get('staticOfferTerms') or {}).get('issueSizeCr'),
            'sourceUrl': summary.get('sourceUrl'), 'issuer': summary.get('issuer'),
            'rawFields': summary.get('rawFields'),
            'priceBand': observation.get('priceBand')}


def extract(transcription, identity):
    """Read explicit whole-offer cells; qualifications travel with both values."""
    if (transcription.get('method') != 'independently-reviewed-visual-transcription'
            or _name(transcription.get('issuer')) != _name(identity['company'])
            or type(transcription.get('page')) is not int or transcription['page'] < 1
            or not transcription.get('locator')):
        raise ValueError('Reviewed issuer, physical page and source locator required')
    if transcription.get('layout') == 'qualified-issue-paragraph':
        # The complete monetary sentence binds both amounts to the same band.
        text = ' '.join(transcription['amountSentence'].split())
        match = re.fullmatch(
            rf'Based on the Price Band of ₹\s*({_NUM}) to ₹\s*({_NUM}) per Equity Share, '
            rf'the Issue size would aggregate to ₹\s*({_NUM}) lakhs at the Floor Price '
            rf'and ₹\s*({_NUM}) lakhs at the Cap Price\*\.', text)
        footnote = re.fullmatch(
            rf'\*Calculated on the basis of up to ({_NUM}) Equity Shares offered in the Issue '
            r'and subject to finalisation of the Basis of Allotment\.',
            ' '.join(transcription['qualificationText'].split()))
        revised = re.fullmatch(
            rf'the Price Band has been revised from ₹\s*({_NUM}) to ₹\s*({_NUM}) per Equity Share '
            rf'to ₹\s*({_NUM}) to ₹\s*({_NUM}) per Equity Share\.',
            ' '.join(transcription['supersessionText'].split()))
        if not match or not footnote or not revised:
            raise ValueError('Incomplete conditional paragraph or explicit supersession')
        low, high, floor, cap = map(number, match.groups())
        old_low, old_high, new_low, new_high = map(number, revised.groups())
        if (low, high) != (new_low, new_high) or old_low > old_high:
            raise ValueError('Conditional amounts disagree with the explicit revised band')
        number(footnote[1])
        factor, unit = Decimal('.01'), 'INR lakh'
        qualifier = 'subject_to_basis_of_allotment'
        qualification = 'Based on up to ' + footnote[1] + ' shares; subject to finalisation of the Basis of Allotment.'
        row = 'Issue size would aggregate'
    elif transcription.get('layout') == 'floor-cap-offer-table':
        columns = transcription['columns']
        if len(columns) != 2:
            raise ValueError('Exactly two complete floor/cap column groups required')
        prices, face_values = [], []
        for column, basis in zip(columns, ('Floor', 'Cap')):
            price = re.fullmatch(rf'At {basis} Price of ₹\s*({_NUM}) per Equity Share', column['priceHeader'])
            shares = re.fullmatch(rf'Up to no\. of Equity Shares of face value of ₹\s*({_NUM}) each', column['shareHeader'])
            if (not price or not shares
                    or column.get('amountHeader') != 'Up to amount (₹ in million)'):
                raise ValueError('Ambiguous price, monetary unit or qualification columns')
            prices.append(number(price[1]))
            face_values.append(number(shares[1]))
        if face_values[0] != face_values[1]:
            raise ValueError('Share column face values conflict')
        rows = transcription['rows']
        names = ['Fresh Issue', 'Offer for Sale', 'Total Offer Size', 'Post-Offer market capitalization of the Company']
        if not isinstance(rows, list) or [r.get('label') for r in rows] != names:
            raise ValueError('Complete explicitly labelled offer table required')
        cells = []
        for item in rows:
            if len(item.get('cells', [])) != 4:
                raise ValueError('Incomplete or extra source columns')
            values = list(map(number, item['cells']))
            if any(values[i] != values[i].to_integral_value() for i in (0, 2)):
                raise ValueError('Share column is not a whole share count')
            cells.append(values)
        # Reconcile explicit legs; never derive money from the share columns.
        for column in range(4):
            tolerance = Decimal('.02') if column % 2 else Decimal(0)
            if abs(cells[0][column] + cells[1][column] - cells[2][column]) > tolerance:
                raise ValueError('Contradictory whole-offer total and disclosed legs')
        low, high = prices
        floor, cap = cells[2][1], cells[2][3]
        factor, unit = Decimal('.1'), 'INR million'
        qualifier, qualification = 'up_to', 'Up to the disclosed amount at each price; final offer terms remain unknown.'
        row = 'Total Offer Size'
    else:
        raise ValueError('Unsupported conditional amount layout')
    if not 0 < low <= high or not 0 < floor <= cap:
        raise ValueError('Conflicting floor/cap amounts or price ordering')
    return {'value': {'floorPrice': float(low), 'capPrice': float(high),
                     'atFloorCr': float(floor * factor), 'atCapCr': float(cap * factor),
                     'qualifier': qualifier, 'qualification': qualification},
            'unit': 'INR crore', 'sourceUnit': unit, 'page': transcription['page'],
            'row': row, 'table': transcription['locator']}


def _time(value):
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError('Collection and review times require timezones')
    return result


def validate(evidence, identity, price_band):
    if (evidence.get('schemaVersion') != 1 or evidence.get('parserVersion') != VERSION
            or evidence.get('identity') != {key: identity[key] for key in IDENTITY}):
        raise ValueError('Conditional amount issuer/offer identity changed')
    source, review = evidence['source'], evidence['review']
    identifier = identity['id']
    if identifier not in REVIEWED_BINDINGS or review.get('url') != REVIEW_URL:
        raise ValueError('No independently pinned source acceptance for this offer')
    blob_sha, derived_sha = REVIEWED_BINDINGS[identifier]
    try:
        raw = (ROOT / 'tests/fixtures/qualified-offer-amounts' / (identifier + '.json')).read_bytes()
    except OSError as exc:
        raise ValueError('Pinned amount source transcription unavailable') from exc
    if hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() != blob_sha:
        raise ValueError('Pinned source transcription Git identity changed')
    fixture = json.loads(raw)
    if (fixture['identity'] != evidence['identity'] or fixture['source'] != source
            or fixture['transcription'] != evidence['transcription']
            or digest(evidence.get('reviewedDerivedObservations', {})) != derived_sha):
        raise ValueError('Candidate differs from the independent immutable source review')
    url = urlsplit(source['url'])
    if (url.scheme != 'https' or not url.hostname or url.username or url.password
            or source.get('authority') != 'issuer_disclosure'
            or source.get('documentType') not in {'Price Band Advertisement', 'Price Band Revision cum Corrigendum'}
            or not re.fullmatch('[a-f0-9]{64}', str(source.get('sha256') or ''))
            or source.get('observedAt') is not None or 'observedAt' not in source
            or not source.get('authorityEvidence')):
        raise ValueError('Exact issuer-disclosure document evidence required')
    document_day = date.fromisoformat(source['documentDate'])
    collected, reviewed = _time(source['collectedAt']), _time(review['reviewedAt'])
    if (document_day > collected.date() or document_day > date.fromisoformat(identity['closeDate'])
            or reviewed < collected or review.get('version') != 1 or review.get('status') != 'accepted'
            or not re.fullmatch(r'https://github\.com/Vasuki8/IPO-Tracker/blob/[a-f0-9]{40}/docs/reviews/[a-z0-9.-]+\.md', str(review.get('url') or ''))
            or review.get('sourceMetadataSha256') != digest(source)
            or review.get('derivedObservationSha256') != digest(evidence.get('reviewedDerivedObservations', {}))
            or review.get('transcriptionSha256') != digest(evidence['transcription'])):
        raise ValueError('Independent immutable review does not bind this transcription')
    result = extract(evidence['transcription'], identity)
    value = result['value']
    if price_band != {'min': value['floorPrice'], 'max': value['capPrice']}:
        raise ValueError('Conditional amounts conflict with the reviewed exchange band')
    return result
