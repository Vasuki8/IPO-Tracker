"""Frozen source-review cohort used for offline transport and browser rehearsals."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from active_offer_terms import IDENTITY, VERSION, parse_response
from reviewed_evidence import digest

FIXTURES = ROOT / 'tests/fixtures/active-offer-terms'
REVIEW_URL = 'https://github.com/Vasuki8/IPO-Tracker/blob/1fb4c7d12e1a5eb616a4db16b304a0aeda32103f/docs/reviews/2026-09-19-active-offer-source-review.md'
REVIEWED_AT = '2026-09-19T02:44:41+00:00'


def cohort():
    rows = json.loads((FIXTURES / 'before.json').read_text(encoding='utf-8'))
    receipts = json.loads((FIXTURES / 'receipts.json').read_text(encoding='utf-8'))
    registry, groups = {'changes': [], 'fillMissing': []}, []
    for row in rows:
        identity = {key: row[key] for key in IDENTITY}
        raw = (FIXTURES / (row['id'] + '.json')).read_bytes()
        source = next(item for item in receipts if item['name'] == row['id'] + '-detail')
        assert hashlib.sha256(raw).hexdigest() == source['sha256']
        parsed = parse_response(raw.decode(), identity)
        receipt = {'schemaVersion': 1, 'parserVersion': VERSION, 'identity': identity,
                   'source': {'name': 'NSE', 'authority': 'official_exchange', 'url': source['url'],
                              'sha256': source['sha256'], 'responseText': raw.decode(),
                              'observedAt': None, 'collectedAt': source['collectedAt']},
                   'review': {'version': 1, 'status': 'accepted', 'reviewedAt': REVIEWED_AT, 'url': REVIEW_URL},
                   **parsed}
        proof = {'field': 'activeOfferTerms', 'value': receipt,
                 'sourceUrl': source['url'], 'sha256': source['sha256']}
        proofs = {'activeOfferTerms': proof}
        blob = (json.dumps(proofs, ensure_ascii=False, indent=2) + '\n').encode()
        groups.append({'kind': 'active-offer-terms', 'identity': identity,
                       'sourceReviewUrl': REVIEW_URL, 'reviewedAt': REVIEWED_AT,
                       'beforeProofHashes': {'activeOfferTerms': digest(row.get('activeOfferTerms'))},
                       'proofsFile': row['id'] + '.json', 'proofs': proofs,
                       'sourceProofsSha256': hashlib.sha256(blob).hexdigest()})
        registry['changes'].append({'id': row['id'], 'identity': identity, 'field': 'activeOfferTerms',
                                   'beforeHash': digest(row.get('activeOfferTerms')), 'after': copy.deepcopy(receipt),
                                   'publicationScope': 'explicit-reviewed', 'reviewedAt': REVIEWED_AT,
                                   'source': {'name': 'NSE active offer detail', 'url': source['url']},
                                   'evidence': {'sha256': source['sha256'], 'reviewUrl': REVIEW_URL},
                                   'reason': 'Accept source-reviewed active bidding terms separately from final static facts; preserve unknown totals and quantities'})
    return {'ipos': rows}, registry, groups
