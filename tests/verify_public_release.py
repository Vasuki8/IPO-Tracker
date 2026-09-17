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
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

STATIC_FILES = (
    'index.html', 'public-quality.js', 'public-quality.css', 'app.js',
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
    args = cli.parse_args()
    require(bool(re.fullmatch(r'[a-f0-9]{40}', args.expected_commit)), 'Expected commit must be a full SHA')
    receipt = {'expectedCommit': args.expected_commit, 'status': 'failed', 'scope': 'public-artifact-consistency-not-source-accuracy'}
    try:
        receipt.update(verify_local(args.root))
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
