"""Attach separately reviewed field proofs without overwriting newer evidence.

A source receipt is not a new extraction. Its source check time, physical rows,
units and parser lineage are retained unchanged. Publication still requires the
ordinary value, document-authority and public-display checks.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path

from final_prospectus_identity import known_non_final_document_url
from final_prospectus_policy import is_final_prospectus
from issue_composition_checks import COMPOSITION_FIELDS

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_FILE = ROOT / 'data/reviewed_correction_evidence.json'
INTERMEDIARY_FIELDS = ('leadManagers', 'registrar')


def group_fields(group):
    kind = group.get('kind', 'composition')
    if kind == 'composition':
        return set(COMPOSITION_FIELDS)
    if kind == 'intermediaries':
        return set(INTERMEDIARY_FIELDS)
    if kind == 'financials':
        return {'financials'}
    if kind == 'active-offer-terms':
        return {'activeOfferTerms'}
    raise ValueError('Unsupported reviewed field-evidence kind')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def load_groups(path=EVIDENCE_FILE):
    registry = json.loads(Path(path).read_text(encoding='utf-8'))
    if registry.get('schemaVersion') != 1 or not isinstance(registry.get('groups'), list):
        raise ValueError('Unsupported reviewed field-evidence registry')
    for group in registry['groups']:
        name = group.get('proofsFile')
        if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]*\.json', name):
            raise ValueError('Reviewed proof file must be a local issuer JSON basename')
        data = Path(path).with_suffix('').joinpath(name).read_bytes()
        if hashlib.sha256(data).hexdigest() != group.get('sourceProofsSha256'):
            raise ValueError('Reviewed source-proof file hash mismatch')
        group['proofs'] = json.loads(data)
    return registry['groups']


def index_groups(groups, registry):
    """Validate the entire supplied evidence registry before modifying any row."""
    result = {}
    for group in groups:
        identity = group.get('identity') or {}
        identifier = identity.get('id')
        if (not all(isinstance(identity.get(k), str) and identity[k]
                    for k in ('id', 'company', 'symbol', 'openDate'))
                or identifier in result):
            raise ValueError('Reviewed evidence needs a unique exact issuer/offer identity')
        date.fromisoformat(identity['openDate'])
        proofs = group.get('proofs') or {}
        hashes = group.get('beforeProofHashes') or {}
        if set(proofs) != group_fields(group) or set(hashes) != set(proofs):
            raise ValueError('Reviewed evidence must cover the complete value/proof group')
        # Bind the recovered artifact to its immutable source-review receipt.
        blob = (json.dumps(proofs, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
        if hashlib.sha256(blob).hexdigest() != group.get('sourceProofsSha256'):
            raise ValueError('Reviewed source-proof artifact hash mismatch')
        if not re.fullmatch(r'https://github\.com/[^/]+/[^/]+/blob/[a-f0-9]{40}/.+',
                            str(group.get('sourceReviewUrl') or '')):
            raise ValueError('Reviewed evidence needs an immutable source-review URL')
        corrections = [item for item in registry.get('changes', []) if item['id'] == identifier]
        if group.get('kind') == 'financials':
            # Retain historical nonfinancial repair entries without replaying
            # them as part of a newly reviewed financial-only transaction.
            corrections = [item for item in corrections if item.get('publicationScope') == 'explicit-reviewed']
        if len(corrections) != len(proofs) or {item['field'] for item in corrections} != set(proofs):
            raise ValueError('Reviewed evidence must match the complete correction-registry group')
        for item in corrections:
            field = item['field']
            proof = proofs[field]
            if group.get('kind') == 'active-offer-terms':
                from active_offer_terms import validate_receipt
                receipt = item['after']
                validate_receipt(receipt, identity)
                if (item.get('publicationScope') != 'explicit-reviewed'
                        or item.get('identity') != identity or proof.get('field') != field
                        or proof.get('value') != receipt or proof.get('sourceUrl') != receipt['source']['url']
                        or proof.get('sha256') != receipt['source']['sha256']
                        or item.get('source', {}).get('url') != proof['sourceUrl']
                        or item.get('evidence', {}).get('sha256') != proof['sha256']
                        or item.get('reviewedAt') != group['reviewedAt']
                        or receipt['review']['reviewedAt'] != group['reviewedAt']
                        or receipt['review']['url'] != group['sourceReviewUrl']
                        or not re.fullmatch('[a-f0-9]{64}', str(hashes[field]))):
                    raise ValueError('Active offer receipt does not match its explicit reviewed correction')
                continue
            detail = proof.get('evidence') or {}
            if (item.get('identity') != identity or proof.get('field') != field
                    or proof.get('value') != item['after']
                    or proof.get('issueOpenDate') != identity['openDate']
                    or proof.get('sourceUrl') != (item.get('source') or {}).get('url')
                    or proof.get('sha256') != (item.get('evidence') or {}).get('sha256')
                    or proof.get('documentDate') != (item.get('evidence') or {}).get('documentDate')
                    or not is_final_prospectus({'type': proof.get('documentType'), 'url': proof.get('sourceUrl')})
                    or not re.fullmatch(r'[a-f0-9]{64}', str(proof.get('sha256') or ''))
                    or not re.fullmatch(r'[a-f0-9]{64}', str(hashes[field]))
                    or type(detail.get('page')) is not int or detail['page'] < 1
                    or not proof.get('checkedAt')):
                raise ValueError('Reviewed field evidence does not match its accepted correction')
            if group.get('kind') == 'financials':
                from review_financial_tables import has_reviewed_financial_evidence
                if (item.get('publicationScope') != 'explicit-reviewed'
                        or proof.get('identity') != identity
                        or not has_reviewed_financial_evidence({**identity, 'financials': proof['value'],
                            'staticFieldProvenance': {'financials': proof}})
                        or datetime.fromisoformat(group['reviewedAt']).utcoffset() is None):
                    raise ValueError('Financial corrections require complete reviewed source grids')
            if group.get('kind') == 'intermediaries':
                if item.get('publicationScope') != 'explicit-reviewed':
                    raise ValueError('Intermediary corrections require explicit reviewed publication')
                entities = detail.get('entities')
                expected = proof['value'] if field == 'leadManagers' else [proof['value']]
                if (not isinstance(entities, list) or not entities or entities != expected
                        or any(not isinstance(name, str) or not name.strip() for name in entities)
                        or not detail.get('heading') or not detail.get('rawLines')):
                    raise ValueError('Reviewed intermediary evidence requires role-specific source rows')
                from review_intermediary_columns import validate_evidence, has_reviewed_role_evidence
                validate_evidence(field, proof['value'], detail)
                if (proof.get('identity') != identity
                        or not has_reviewed_role_evidence({**identity, field: proof['value'],
                            'staticFieldProvenance': {field: proof}}, field)
                        or datetime.fromisoformat(group['reviewedAt']).utcoffset() is None):
                    raise ValueError('Reviewed intermediary proof must bind exact issuer and dated review')
        if group.get('kind') == 'intermediaries':
            bindings = {(proof['sourceUrl'], proof['sha256'], proof['documentDate'],
                         proof.get('parserVersion'), proof['checkedAt']) for proof in proofs.values()}
            if len(bindings) != 1:
                raise ValueError('Reviewed intermediary roles must share one exact document review')
            left, right = [proofs[field]['evidence'] for field in INTERMEDIARY_FIELDS]
            if any(left.get(key) != right.get(key) for key in ('page', 'rawLines', 'headingLine')):
                raise ValueError('Reviewed intermediary roles must share one physical source table')
        result[identifier] = group
    return result


def evidence_conflict(row, group):
    if any(row.get(k) != value for k, value in group['identity'].items()):
        return 'Reviewed field-evidence issuer or offer identity changed'
    if group.get('kind') == 'active-offer-terms':
        current = row.get('activeOfferTerms')
        if current != group['proofs']['activeOfferTerms']['value'] and digest(current) != group['beforeProofHashes']['activeOfferTerms']:
            return 'Active offer receipt changed since source review'
        return None
    current = row.get('staticFieldProvenance') or {}
    for field, proof in group['proofs'].items():
        if known_non_final_document_url(row, proof['sourceUrl']):
            return 'Reviewed field evidence identifies a known non-final document'
        if current.get(field) != proof and digest(current.get(field)) != group['beforeProofHashes'][field]:
            return 'Field evidence changed since source review; preserving the complete value/proof group'
    return None


def attach_evidence(row, group):
    if group.get('kind') == 'active-offer-terms':
        # Source rows are inside the atomic receipt and its correction history.
        # They must never become Final Prospectus static-field provenance.
        return 0
    current = row.setdefault('staticFieldProvenance', {})
    proofs = group['proofs']
    if all(current.get(field) == proof for field, proof in proofs.items()):
        return 0
    before = {field: copy.deepcopy(current.get(field)) for field in proofs}
    current.update(copy.deepcopy(proofs))
    row.setdefault('dataCorrections', []).append({
        'field': 'staticFieldProvenance', 'fields': list(proofs),
        'before': before, 'after': copy.deepcopy(proofs),
        'reason': 'Attach the matching retained source-review proofs to reviewed values; preserve previous proofs',
        'sourceUrl': next(iter(proofs.values()))['sourceUrl'],
        'sourceReviewUrl': group['sourceReviewUrl'],
        'correctedAt': group['reviewedAt'],
    })
    return sum(before[field] != proof for field, proof in proofs.items())
