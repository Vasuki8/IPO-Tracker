"""Read-only public-release acceptance, not canonical/PDF source verification.

Check every local profile against the directory contract, then compare bounded
live samples with those exact published bytes. Never rebuild or fetch the master
dataset from the public site. Run against an immutable deployed checkout.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

STATIC_FILES = (
    'index.html', 'public-quality.js', 'public-quality.css', 'app.js', 'source-health.js',
    'company-page.js', 'company.js', 'phase4.js', 'methodology.html',
    'data/ipos-summary.json', 'ipo/routes.json',
)
CLOCKS = ('subscriptionObservedAt', 'subscriptionCollectedAt', 'subscriptionTimeBasis',
          'subscriptionSource', 'subscriptionSourceUrl', 'subscriptionAuthority')
SHARED = ('id', 'company', 'profilePath', 'openDate', 'closeDate', 'listingDate',
          'priceBand', 'lotSize', 'issueSizeCr', *CLOCKS)
STATES = {'final_verified', 'provisional', 'reported', 'under_review',
          'awaiting_disclosure', 'source_unavailable'}
DISPLAY = {'final_verified', 'provisional', 'reported'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def invalid(_):
        raise ValueError('Non-finite JSON number')
    return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)


class ProfileParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.active = False
        self.count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('id') == 'ipo-profile-data':
            require(attrs.get('type') == 'application/json', 'Wrong profile script type')
            self.count += 1
            self.active = True

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False


def embedded_profile(data):
    parser = ProfileParser()
    parser.feed(data.decode('utf-8'))
    require(parser.count == 1 and not parser.active, 'Expected one complete profile payload')
    value = read_json(''.join(parser.parts))
    require(isinstance(value, dict) and isinstance(value.get('ipo'), dict), 'Missing profile object')
    return value['ipo']


def field_value(record, field):
    value = record
    for key in field.split('.'):
        value = value.get(key) if isinstance(value, dict) else None
    return value


def decisions(record):
    quality = record.get('publicQuality') or {}
    require(quality.get('version') == 1, 'Missing or unsupported public quality contract')
    fields, sources = quality.get('fields'), quality.get('sources', [])
    require(isinstance(fields, dict) and fields and isinstance(sources, list), 'Malformed field decisions')
    result = {}
    for field, decision in fields.items():
        require(isinstance(decision, dict) and decision.get('state') in STATES, 'Unknown field state')
        normalized = dict(decision)
        if 'source' in normalized:
            index = normalized.pop('source')
            require(type(index) is int and 0 <= index < len(sources), 'Invalid field source reference')
            normalized['sourceEvidence'] = sources[index]
        if decision['state'] not in DISPLAY:
            require(field_value(record, field) in (None, '', [], {}), f'Withheld field is populated: {field}')
        result[field] = normalized
    return result


def verify_local(root):
    """Check all generated routes; no writes, network, clock changes or repairs."""
    root = Path(root)
    summary = read_json((root / 'data/ipos-summary.json').read_bytes())
    manifest = read_json((root / 'ipo/routes.json').read_bytes())
    rows = summary.get('ipos')
    routes = manifest.get('routes')
    require(isinstance(rows, list) and rows and isinstance(routes, list), 'Missing public inventory')
    require(len(rows) == len(routes) == len(set(routes)) == manifest.get('routeCount')
            == manifest.get('recordCount') == summary.get('meta', {}).get('recordCount'), 'Public inventory counts differ')
    require(all(isinstance(route, str) and re.fullmatch(r'[a-z0-9][a-z0-9-]*', route)
                for route in routes), 'Unsafe profile route')
    by_path = {}
    for row in rows:
        require(isinstance(row, dict) and row.get('profilePath') not in by_path, 'Duplicate directory profile path')
        by_path[row.get('profilePath')] = row
    require(set(by_path) == {f'ipo/{route}/' for route in routes}, 'Directory and route inventory differ')
    for route in routes:
        path = f'ipo/{route}/'
        row = by_path[path]
        profile = embedded_profile((root / path / 'index.html').read_bytes())
        for field in SHARED:
            require(profile.get(field) == row.get(field), f'{path}: directory/profile mismatch: {field}')
        require(field_value(row, 'subscription.total') == field_value(profile, 'subscription.total'), f'{path}: subscription mismatch')
        require(field_value(row, 'listing.gainPct') == field_value(profile, 'listing.gainPct'), f'{path}: return mismatch')
        expected, actual = decisions(row), decisions(profile)
        for field, decision in expected.items():
            require(actual.get(field) == decision, f'{path}: field/source decision mismatch: {field}')
    hashes = {path: digest((root / path).read_bytes()) for path in STATIC_FILES}
    # Select meaningful boundary examples without assuming a fixed inventory.
    selected = []
    def choose(predicate):
        match = next((row['profilePath'] for row in rows if predicate(row)), None)
        if match and match not in selected:
            selected.append(match)
    for key in ('emmvee', 'teamtech', 'shakti-polytarp-limited', 'kheriaauto'):
        choose(lambda row, key=key: row.get('id') == key)
    choose(lambda row: row.get('subscriptionAuthority') == 'secondary' and row.get('subscriptionObservedAt'))
    choose(lambda row: row.get('subscription') and not row.get('subscriptionObservedAt'))
    choose(lambda row: any(d.get('state') == 'final_verified' for d in row['publicQuality']['fields'].values()))
    choose(lambda row: True)
    for path in selected:
        hashes[path + 'index.html'] = digest((root / path / 'index.html').read_bytes())
    return {'routeCount': len(routes), 'sampledProfiles': selected, 'expectedSha256': hashes}



def verify_active_offer_delivery(stored, profile, summary, group, proofs):
    """Check receipt delivery without treating provisional rows as final proofs."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
    from active_offer_terms import validate_receipt
    proof = proofs['activeOfferTerms']
    active = proof['value']
    fields = validate_receipt(active, group['identity'])
    require(proof.get('field') == 'activeOfferTerms'
            and proof.get('sourceUrl') == active['source']['url']
            and proof.get('sha256') == active['source']['sha256']
            and group.get('sourceReviewUrl') == active['review']['url']
            and group.get('reviewedAt') == active['review']['reviewedAt']
            and stored.get('activeOfferTerms') == active,
            'Accepted active offer receipt differs from reviewed evidence')

    def compact(value):
        if isinstance(value, dict):
            return {key: compact(item) for key, item in value.items() if item is not None and item != '' and item != [] and item != {}}
        if isinstance(value, list):
            return [compact(item) for item in value]
        return value

    source = active['source']
    expected_source = {'sourceUrl': source['url'], 'sha256': source['sha256'],
                       'parserVersion': active['parserVersion'], 'checkedAt': active['review']['reviewedAt'],
                       'collectedAt': source['collectedAt'], 'reviewUrl': active['review']['url']}
    expired = datetime.now(ZoneInfo('Asia/Kolkata')).date().isoformat() > active['identity']['closeDate']
    for field, term in fields.items():
        for record in (profile, summary):
            quality = decisions(record)
            if record is summary and field not in quality and field not in record:
                continue
            decision = quality.get(field) or {}
            # A rebuilt expired disclosure is withheld; an older immutable
            # artifact may still carry its exact until date for browser expiry.
            if expired and decision.get('state') in {'awaiting_disclosure', 'under_review'}:
                require(record.get(field) is None, 'Expired active term remains populated')
                continue
            require(compact(record.get(field)) == compact(term['value']), f'{field}: active offer value not delivered')
            require(decision.get('state') == 'provisional' and decision.get('until') == active['identity']['closeDate']
                    and decision.get('row') == term['row'] and decision.get('table') == term['table']
                    and compact(decision.get('sourceEvidence')) == expected_source,
                    f'{field}: active offer evidence not delivered')


def verify_reviewed_publication(root, receipt):
    """Require delivery of the last reviewed repair, not just matching pages.

    Read canonical data and retained proofs locally only. This is a delivery
    check against already reviewed evidence, never a new source/PDF audit.
    Ordinary collection releases do not inherit this reviewed-only assertion.
    """
    root = Path(root)
    canonical_bytes = (root / 'data/ipos.json').read_bytes()
    canonical = read_json(canonical_bytes)
    publication = canonical.get('meta', {}).get('publication', {})
    require(isinstance(publication, dict), 'Malformed publication metadata')
    if publication.get('mode') != 'reviewed':
        return {'status': 'not_requested', 'scope': 'retained-reviewed-evidence-delivery'}
    ids = publication.get('reviewedIds')
    require(isinstance(ids, list) and ids
            and all(isinstance(key, str) and key for key in ids)
            and len(ids) == len(set(ids)), 'Reviewed publication needs unique nonempty issuer IDs')
    require(publication.get('status') == 'published', 'Reviewed publication is not accepted')
    field_groups = {
        'composition': ('issueComposition', 'issueSizeCr', 'freshIssueCr', 'ofsCr'),
        'intermediaries': ('leadManagers', 'registrar'),
        'financials': ('financials',),
        'active-offer-terms': ('activeOfferTerms',),
    }
    public_composition = ('freshShares', 'ofsShares', 'valuationPriceUsed')
    source_keys = ('sourceUrl', 'documentDate', 'sha256', 'parserVersion', 'checkedAt')
    index = read_json((root / 'data/reviewed_correction_evidence.json').read_bytes())
    require(index.get('schemaVersion') == 1 and isinstance(index.get('groups'), list),
            'Unsupported reviewed evidence index')
    groups = {}
    for group in index['groups']:
        key = group['identity']['id']
        require(isinstance(key, str) and key not in groups, 'Duplicate reviewed evidence identity')
        groups[key] = group
    require(set(ids) <= set(groups), 'Reviewed publication has no retained evidence for an issuer')

    def by_id(rows):
        require(isinstance(rows, list), 'Missing reviewed issuer inventory')
        result = {}
        for row in rows:
            key = row['id']
            require(isinstance(key, str) and key not in result, 'Duplicate reviewed issuer ID')
            result[key] = row
        return result

    # JSON numbers may differ in int/float representation, never bool/number.
    def equal(actual, expected):
        if isinstance(expected, dict):
            return (isinstance(actual, dict) and actual.keys() == expected.keys()
                    and all(equal(actual[k], v) for k, v in expected.items()))
        if isinstance(expected, list):
            return (isinstance(actual, list) and len(actual) == len(expected)
                    and all(equal(a, b) for a, b in zip(actual, expected)))
        if type(expected) in (int, float):
            return type(actual) in (int, float) and actual == expected
        return type(actual) is type(expected) and actual == expected

    stored = by_id(canonical['ipos'])
    summary = by_id(read_json((root / 'data/ipos-summary.json').read_bytes())['ipos'])
    checked = []
    for key in ids:
        group = groups[key]
        kind = group.get('kind', 'composition')
        require(isinstance(kind, str) and kind in field_groups, 'Unsupported reviewed evidence kind')
        fields = field_groups[kind]
        name = group.get('proofsFile')
        require(isinstance(name, str) and re.fullmatch(r'[a-z0-9][a-z0-9-]*\.json', name),
                'Unsafe reviewed proof filename')
        proof_dir = root / 'data/reviewed_correction_evidence'
        proof_path = proof_dir / name
        require(proof_path.resolve().parent == proof_dir.resolve(), 'Reviewed proof escaped its directory')
        raw = proof_path.read_bytes()
        require(digest(raw) == group.get('sourceProofsSha256'), 'Reviewed proof artifact hash mismatch')
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        require(blob == group.get('sourceProofsGitBlob'), 'Reviewed proof Git identity mismatch')
        proofs = read_json(raw)
        require(isinstance(proofs, dict) and set(proofs) == set(fields), 'Incomplete reviewed field-group proofs')
        identity = group['identity']
        require(all(isinstance(identity.get(k), str) and identity[k]
                    for k in ('id', 'company', 'symbol', 'openDate')), 'Incomplete reviewed offer identity')
        require(key in stored and key in summary, 'Reviewed issuer missing from accepted/public data')
        path = summary[key]['profilePath']
        require(isinstance(path, str) and re.fullmatch(r'ipo/[a-z0-9][a-z0-9-]*/', path),
                'Unsafe reviewed profile path')
        profile = embedded_profile((root / path / 'index.html').read_bytes())
        for record in (stored[key], summary[key], profile):
            require(all(record.get(k) == value for k, value in identity.items()), 'Reviewed offer identity mismatch')
        projected = decisions(profile)
        directory = decisions(summary[key])
        if kind == 'active-offer-terms':
            verify_active_offer_delivery(stored[key], profile, summary[key], group, proofs)
        for field in (() if kind == 'active-offer-terms' else fields):
            proof = proofs[field]
            require(proof.get('field') == field and proof.get('issueOpenDate') == identity['openDate'],
                    'Reviewed field/offer evidence mismatch')
            require(equal(stored[key].get(field), proof['value'])
                    and equal(stored[key].get('staticFieldProvenance', {}).get(field), proof),
                    f'{key}.{field}: accepted value/proof differs from the reviewed evidence')
            expected = proof['value']
            if field == 'issueComposition':
                expected = {k: expected[k] for k in public_composition if k in expected}
            if field == 'financials':
                require(expected.get('unit') == '₹ crore', 'Reviewed financial unit differs from the public table contract')
                expected = {'periods': expected['periods']}
            require(equal(profile.get(field), expected), f'{key}.{field}: reviewed profile value not delivered')
            expected_source = {k: proof[k] for k in source_keys if k in proof}
            delivered_decisions = [projected.get(field)]
            if field == 'issueSizeCr' or field in directory or field in summary[key]:
                # The compact directory currently omits intermediary names. If a
                # surface carries a reviewed field, its value and proof must agree.
                require(equal(summary[key].get(field), expected),
                        f'{key}.{field}: reviewed directory value not delivered')
                delivered_decisions.append(directory.get(field))
            for decision in delivered_decisions:
                require(isinstance(decision, dict) and decision.get('state') == 'final_verified'
                        and decision.get('sourceEvidence') == expected_source
                        and decision.get('page') == proof['evidence']['page'],
                        f'{key}.{field}: reviewed public evidence not delivered')
        # The ordinary sampler is not guaranteed to include future reviewed IDs.
        if path not in receipt['sampledProfiles']:
            receipt['sampledProfiles'].append(path)
        receipt['expectedSha256'][path + 'index.html'] = digest((root / path / 'index.html').read_bytes())
        checked.append({'id': key, 'kind': kind, 'fields': list(fields), 'proofsSha256': digest(raw),
                        'proofsGitBlob': blob, 'sourceReviewUrl': group.get('sourceReviewUrl')})
    return {'status': 'passed', 'scope': 'retained-reviewed-evidence-delivery-not-new-source-audit',
            'canonicalSha256': digest(canonical_bytes), 'checked': checked}

def validate_base(base):
    parsed = urlsplit(base)
    require(parsed.scheme == 'https' or (parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost', '::1'}), 'Use HTTPS, or HTTP on loopback only')
    require(parsed.hostname and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment, 'Invalid release base URL')
    return base.rstrip('/') + '/'


def verify_http(root, base, receipt, *, fetch=None):
    """Compare complete bytes, not HTTP 200 or a version label alone."""
    base = validate_base(base)
    checked = []
    for path, expected in receipt['expectedSha256'].items():
        relative = path[:-len('index.html')] if path.endswith('index.html') else path
        url = urljoin(base, relative)
        size = (Path(root) / path).stat().st_size
        if fetch is None:
            request = Request(url, headers={'User-Agent': 'IPO-Tracker-release-check', 'Cache-Control': 'no-cache'})
            with urlopen(request, timeout=15) as response:
                require(response.status == 200, f'{path}: unexpected HTTP status')
                require(response.url == url, f'{path}: unexpected redirect')
                data = response.read(size + 1)
        else:
            data = fetch(url, size + 1)
        require(digest(data) == expected, f'{path}: served bytes do not match the expected release')
        checked.append(path)
    return checked


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    cli.add_argument('--base-url', help='Optional deployed or loopback site; never rebuilds it')
    cli.add_argument('--expected-commit', required=True, help='Immutable checkout/deployment SHA for this receipt')
    cli.add_argument('--check-reviewed-publication', action='store_true',
                     help='Check delivery of the last reviewed value/proof repair, using local evidence only')
    args = cli.parse_args()
    require(bool(re.fullmatch(r'[a-f0-9]{40}', args.expected_commit)), 'Expected commit must be a full SHA')
    receipt = {'expectedCommit': args.expected_commit, 'status': 'failed', 'scope': 'public-artifact-consistency-not-source-accuracy'}
    try:
        receipt.update(verify_local(args.root))
        if args.check_reviewed_publication:
            receipt['reviewedPublication'] = verify_reviewed_publication(args.root, receipt)
        if args.base_url:
            receipt['baseUrl'] = validate_base(args.base_url)
            receipt['httpChecked'] = verify_http(args.root, args.base_url, receipt)
        receipt['status'] = 'passed'
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        receipt['error'] = str(error)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
