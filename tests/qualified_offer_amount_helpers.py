"""Frozen, independently source-reviewed two-document conditional amount batch."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from qualified_offer_amounts import VERSION, FIELD, digest, validate, amount_observation

FIXTURES = ROOT / 'tests/fixtures/qualified-offer-amounts'
REVIEW_URL = 'https://github.com/Vasuki8/IPO-Tracker/blob/6e2df0a4d4c8b736d0c07d526b3b844eaecd0b49/docs/reviews/2026-09-19-qualified-offer-amount-source-review.md'
REVIEWED_AT = '2026-09-19T13:58:44.750002+00:00'


def cohort():
    rows = json.loads((FIXTURES / 'before.json').read_text())
    registry, groups = {'changes': [], 'fillMissing': []}, []
    for row in rows:
        fixture = json.loads((FIXTURES / (row['id'] + '.json')).read_text())
        identity = fixture['identity']
        receipt = copy.deepcopy(row['activeOfferTerms'])
        review = {'version': 1, 'status': 'accepted', 'reviewedAt': REVIEWED_AT, 'url': REVIEW_URL}
        amount = {'schemaVersion': 1, 'parserVersion': VERSION, 'identity': identity,
                  'source': fixture['source'], 'transcription': fixture['transcription'],
                  'review': {**review, 'transcriptionSha256': fixture['transcriptionSha256'],
                             'sourceMetadataSha256': digest(fixture['source'])}}
        # Exact source-reviewed Varmora context: the retained scalar was made
        # from floor shares times cap, not an observed monetary disclosure.
        derived = {'NSE': amount_observation(row['observations']['NSE'])} if row['id'] == 'varmora' else {}
        amount['reviewedDerivedObservations'] = derived
        amount['review']['derivedObservationSha256'] = digest(derived)
        receipt['amountEvidence'] = amount
        receipt['review'] = review
        receipt['fields'][FIELD] = validate(amount, identity, receipt['fields']['priceBand']['value'])
        proofs = {'activeOfferTerms': {'field': 'activeOfferTerms', 'value': receipt,
                  'sourceUrl': receipt['source']['url'], 'sha256': receipt['source']['sha256']}}
        blob = (json.dumps(proofs, ensure_ascii=False, indent=2) + '\n').encode()
        groups.append({'kind': 'active-offer-terms', 'identity': identity,
                       'sourceReviewUrl': REVIEW_URL, 'reviewedAt': REVIEWED_AT,
                       'beforeProofHashes': {'activeOfferTerms': digest(row['activeOfferTerms'])},
                       'proofsFile': row['id'] + '.json', 'proofs': proofs,
                       'sourceProofsGitBlob': hashlib.sha1(b'blob ' + str(len(blob)).encode() + b'\0' + blob).hexdigest(),
                       'sourceProofsSha256': hashlib.sha256(blob).hexdigest()})
        registry['changes'].append({'id': row['id'], 'identity': identity, 'field': 'activeOfferTerms',
            'beforeHash': digest(row['activeOfferTerms']), 'after': receipt,
            'publicationScope': 'explicit-reviewed', 'reviewedAt': REVIEWED_AT,
            'source': {'name': 'NSE active offer detail', 'url': receipt['source']['url']},
            'evidence': {'sha256': receipt['source']['sha256'], 'reviewUrl': REVIEW_URL,
                         'amountDocumentSha256': amount['source']['sha256'], 'amountDocumentUrl': amount['source']['url']},
            'reason': 'Add separately source-reviewed conditional whole-offer amounts; preserve original NSE terms, unknown final scalar and all history'})
    return {'ipos': rows}, registry, groups
