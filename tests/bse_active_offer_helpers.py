"""Frozen BSE source cohort; no network, accepted-data writes or clock refresh."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from bse_active_offer_terms import IDENTITY, VERSION, parse_response
from reviewed_evidence import digest

FIXTURES = ROOT / 'tests/fixtures/bse-active-offer-terms'
REVIEW_URL = 'https://github.com/Vasuki8/IPO-Tracker/blob/f16287080613b57b000a227fca9d90eab1b72b25/docs/reviews/2026-09-19-bse-active-offer-source-review.md'
REVIEW = json.loads((ROOT / 'docs/reviews/2026-09-19-bse-active-offer-source-review.json').read_text())
EXPECTED = {
    'fx-multitech-limited': (110, 116, 1200, 2400),
    'robokidz-eduventures-limited': (100, 106, 1200, 2400),
    'himalaya-nutravedics-india-limited': (100, 106, 1200, 2400),
    's-k-offset-limited': (119, 125, 1000, 2000),
}


def sources():
    receipts = json.loads((FIXTURES / 'receipts.json').read_text())
    def bound(receipt, name):
        raw = gzip.decompress((FIXTURES / name).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == receipt['sha256']
        return {'url': receipt['url'], 'responseText': raw.decode(), 'sha256': receipt['sha256'],
                'observedAt': None, 'collectedAt': receipt['collectedAt']}
    index = bound(receipts['index'], 'index.html.gz')
    return {r['id']: {'name': 'BSE', 'authority': 'official_exchange',
                     **bound(r, r['id'] + '.html.gz'), 'index': copy.deepcopy(index)}
            for r in receipts['details']}


def cohort():
    rows = json.loads((FIXTURES / 'before.json').read_text())
    source_map = sources()
    registry, groups = {'changes': [], 'fillMissing': []}, []
    for row in rows:
        if row['id'] not in EXPECTED:
            continue
        identity = {key: row[key] for key in IDENTITY}
        source = source_map[row['id']]
        receipt = {'schemaVersion': 1, 'parserVersion': VERSION, 'identity': identity,
                   'source': source, 'review': {'version': 1, 'status': 'accepted',
                   'reviewedAt': REVIEW['reviewedAt'], 'url': REVIEW_URL}, **parse_response(source, row)}
        proof = {'field': 'activeOfferTerms', 'value': receipt, 'sourceUrl': source['url'], 'sha256': source['sha256']}
        proofs = {'activeOfferTerms': proof}
        blob = (json.dumps(proofs, ensure_ascii=False, indent=2) + '\n').encode()
        groups.append({'kind': 'active-offer-terms', 'identity': identity, 'sourceReviewUrl': REVIEW_URL,
                       'reviewedAt': REVIEW['reviewedAt'], 'beforeProofHashes': {'activeOfferTerms': digest(row.get('activeOfferTerms'))},
                       'proofsFile': row['id'] + '.json', 'proofs': proofs,
                       'sourceProofsGitBlob': hashlib.sha1(b'blob ' + str(len(blob)).encode() + b'\0' + blob).hexdigest(),
                       'sourceProofsSha256': hashlib.sha256(blob).hexdigest()})
        registry['changes'].append({'id': row['id'], 'identity': identity, 'field': 'activeOfferTerms',
            'beforeHash': digest(row.get('activeOfferTerms')), 'after': copy.deepcopy(receipt),
            'publicationScope': 'explicit-reviewed', 'reviewedAt': REVIEW['reviewedAt'],
            'source': {'name': 'BSE active offer detail', 'url': source['url']},
            'evidence': {'sha256': source['sha256'], 'reviewUrl': REVIEW_URL},
            'reason': 'Accept reviewed provisional price, market lot and minimum bid quantity from matching BSE index/detail rows; preserve bid-lot, total, composition and canonical-symbol gaps'})
    return {'ipos': rows}, registry, groups
