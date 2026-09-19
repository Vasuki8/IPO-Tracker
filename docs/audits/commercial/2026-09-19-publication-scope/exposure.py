"""Frozen, read-only commercial publication-scope appendix. No rights decisions.

Run from any directory with uv run --frozen python <this file>; stdout JSON only.
All named source/public inputs must match BASE. Source references are not grants
or field attribution. No copied evidence text or new source values are emitted.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[4]
BASE = '1e86840856525db2ee2b436ed64f2b6e60374ee0'
HOSTS = {
    'ipopremium.in': 'IPO Premium', 'www.ipopremium.in': 'IPO Premium',
    'ipodhamaka.in': 'IPO Dhamaka', 'www.ipodhamaka.in': 'IPO Dhamaka',
    'orklaindia.com': 'Orkla', 'www.orklaindia.com': 'Orkla',
    'sunshinepictures.in': 'Sunshine', 'www.sunshinepictures.in': 'Sunshine',
    'ipostatus.integratedregistry.in': 'Integrated Registry',
    'ipowatch.in': 'IPO Watch', 'www.ipowatch.in': 'IPO Watch',
    'ipocentral.in': 'IPO Central', 'www.ipocentral.in': 'IPO Central',
}
URL = re.compile(r'https?://[^\s"\'<>]+')
CSV_FIELDS = {'priceBand': ['Price minimum INR', 'Price maximum INR'],
              'lotSize': ['Lot size shares', 'One lot at cap INR'],
              'issueSizeCr': ['Issue size crore INR'],
              'subscription': ['Subscription multiple', 'Subscription source observation time',
                               'Subscription collection time', 'Subscription source authority', 'Subscription source']}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pointer(key):
    return str(key).replace('~', '~0').replace('/', '~1')


def strings(value, path=''):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from strings(item, path + '/' + pointer(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from strings(item, path + '/' + str(index))
    elif isinstance(value, str):
        yield path, value


def provider(url):
    try:
        parsed = urlsplit(url)
        return HOSTS.get(parsed.hostname) if parsed.scheme in {'https', 'http'} and not parsed.username else None
    except (TypeError, ValueError):
        return None


def references(value):
    result = []
    for path, text in strings(value):
        for url in URL.findall(text):
            name = provider(url)
            if name:
                result.append({'pointer': path, 'url': url, 'provider': name})
    return result


def present(value):
    if isinstance(value, dict):
        return any(present(v) for v in value.values())
    if isinstance(value, list):
        return any(present(v) for v in value)
    return value is not None and value != ''


def field_value(row, field):
    value = row
    for part in field.split('.'):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def field_state(row, field):
    return row.get('publicQuality', {}).get('fields', {}).get(field, {}).get('state', 'not_in_payload')


def profile_record(raw):
    matches = re.findall(r'<script\b(?=[^>]*\bid="ipo-profile-data")[^>]*>(.*?)</script>', raw.decode('utf-8'), re.S)
    if len(matches) != 1:
        raise ValueError('Expected one embedded public profile payload')
    value = json.loads(matches[0])['ipo']
    if not isinstance(value, dict) or not value.get('id'):
        raise ValueError('Missing public profile identity')
    return value


def record_scope(row, profile, summary):
    if row['id'] != profile['id'] or row['id'] != summary['id']:
        raise ValueError('Public identity mismatch')
    proofs = []
    for field, proof in (row.get('staticFieldProvenance') or {}).items():
        name = provider(proof.get('sourceUrl'))
        if not name:
            continue
        text_locations = [{'pointer': '/staticFieldProvenance/' + pointer(field) + path,
                           'characters': len(text), 'sha256': sha(text.encode())}
                          for path, text in strings(proof)
                          if path.startswith('/evidence/') and not provider(text)]
        proofs.append({'field': field, 'provider': name, 'sourceUrl': proof.get('sourceUrl'),
            'sourceSha256': proof.get('sha256'), 'canonicalPointer': '/staticFieldProvenance/' + pointer(field),
            'canonicalValuePresent': present(field_value(row, field)),
            'profileValuePresent': present(field_value(profile, field)), 'profileState': field_state(profile, field),
            'summaryValuePresent': present(field_value(summary, field)), 'summaryState': field_state(summary, field),
            'csvColumns': CSV_FIELDS.get(field, []), 'retainedProofTextCandidates': text_locations})
    subscription = None
    if 'secondary' in str(row.get('subscriptionSource') or '').lower():
        subscription = {'label': row.get('subscriptionSource'), 'sourceUrl': row.get('subscriptionSourceUrl'),
            'sourceUrlBinding': 'stored' if row.get('subscriptionSourceUrl') else 'missing_not_inferred_from_history',
            'canonicalFields': sorted(k for k,v in (row.get('subscription') or {}).items() if v is not None),
            'profileFields': sorted(k for k,v in (profile.get('subscription') or {}).items() if v is not None),
            'profileState': field_state(profile, 'subscription'),
            'summaryTotalPresent': field_value(summary, 'subscription.total') is not None,
            'summaryState': field_state(summary, 'subscription'), 'csvColumns': CSV_FIELDS['subscription'],
            'sourceObservedAt': row.get('subscriptionObservedAt'), 'collectedAt': row.get('subscriptionCollectedAt'),
            'canonicalHistoryCount': len(row.get('subscriptionHistory') or []),
            'publicProfileHistoryCount': len(profile.get('subscriptionHistory') or [])}
    return {'id': row['id'], 'company': row.get('company'), 'status': row.get('status'),
        'profilePath': row.get('profilePath'), 'secondarySubscription': subscription,
        'canonicalReferences': references(row), 'profileReferences': references(profile),
        'summaryReferences': references(summary), 'fieldProofBindings': proofs,
        'historyLocations': ['/subscriptionHistory'] if row.get('subscriptionHistory') else [],
        'correctionCount': len(row.get('dataCorrections') or []),
        'extractionMetadata': {k: {'sourceUrl': (row.get(k) or {}).get('documentUrl'),
                                   'status': (row.get(k) or {}).get('status')}
                               for k in ('offerDocumentExtraction', 'issuerDocumentExtraction') if isinstance(row.get(k), dict)}}


def main():
    bindings = []
    def read(name):
        path = ROOT / name
        raw = path.read_bytes()
        expected = subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=ROOT)
        if raw != expected:
            raise ValueError('Input changed since assessed commit: ' + name)
        bindings.append({'path': name, 'sha256': sha(raw), 'bytes': len(raw)})
        return raw
    canonical = json.loads(read('data/ipos.json'))
    summary_rows = json.loads(read('data/ipos-summary.json'))['ipos']
    summaries = {row['id']: row for row in summary_rows}
    if len(summaries) != len(summary_rows):
        raise ValueError('Ambiguous summary identity')
    pending = json.loads(read('data/pending_updates.json'))['updates']
    for name in ('app.js', 'public-quality.js', 'scripts/build_company_pages.py', 'uv.lock',
                 'data/public_display_holds.json', 'data/phase_status.json'):
        read(name)
    cohort = []
    for index, row in enumerate(canonical['ipos']):
        if not references(row) and 'secondary' not in str(row.get('subscriptionSource') or '').lower():
            continue
        route = PurePosixPath(row['profilePath'])
        if route.is_absolute() or '..' in route.parts or route.parts[0] != 'ipo':
            raise ValueError('Invalid public route')
        path = (route / 'index.html').as_posix()
        profile = profile_record(read(path))
        result = record_scope(row, profile, summaries[row['id']])
        result['canonicalPointer'] = '/ipos/' + str(index)
        result['profileFile'] = path
        cohort.append(result)
    ids = {row['id'] for row in cohort}
    proposal_rows = []
    for index, entry in enumerate(pending):
        refs = references(entry)
        path = entry.get('path') or []
        issuer = path[1] if len(path) > 1 and path[0] == 'ipos' else None
        if issuer in ids or refs:
            proposal_rows.append({'index': index, 'pointer': '/updates/' + str(index), 'id': issuer,
                'path': path, 'status': entry.get('status'), 'fingerprint': entry.get('fingerprint'),
                'runId': entry.get('runId'), 'providerReferences': refs,
                'meaning': 'Unresolved proposal, not accepted field provenance.'})
    output = {'schemaVersion': 1, 'baseCommit': BASE, 'assessedDateUtc': '2026-09-19',
        'scope': 'Seven exact provider/issuer host families plus all canonical secondary subscription labels; static committed public artifacts, not a new source/legal review.',
        'inputs': bindings, 'cohort': cohort, 'pendingProposals': proposal_rows,
        'summary': {'canonicalRecords': len(canonical['ipos']), 'cohortRecords': len(cohort),
            'secondaryLabelRecords': sum(r['secondarySubscription'] is not None for r in cohort),
            'secondaryProfileValueRecords': sum(bool((r['secondarySubscription'] or {}).get('profileFields')) for r in cohort),
            'secondarySummaryTotalRecords': sum(bool((r['secondarySubscription'] or {}).get('summaryTotalPresent')) for r in cohort),
            'secondaryPublicHistoryRows': sum((r['secondarySubscription'] or {}).get('publicProfileHistoryCount', 0) for r in cohort),
            'directStaticProofFields': sum(len(r['fieldProofBindings']) for r in cohort),
            'publicDirectStaticProofFields': sum(f['profileValuePresent'] for r in cohort for f in r['fieldProofBindings']),
            'pendingProposalDenominator': len(pending), 'cohortOrProviderLinkedProposals': len(proposal_rows),
            'providerCanonicalReferences': dict(sorted(Counter(ref['provider'] for r in cohort for ref in r['canonicalReferences']).items()))},
        'csvEvidence': {'path': 'app.js', 'function': 'exportCsv', 'fields': CSV_FIELDS,
            'meaning': 'Source inspection: filtered sanitized summary, with latestSubscription calling IPOQuality.snapshot. No CSV was executed or downloaded by this appendix.'},
        'limitations': ['References/labels do not establish exact upstream attribution, copyright ownership or permission.',
            'Missing top-level secondary source URLs stay missing; source/history links cannot supply them.',
            'Source holds affect public values, not access to raw data, history, repository commits or artifacts.',
            'Only selected current profiles and named input files are enumerated; all Git history and remote workflow artifacts are not exhaustively scanned.',
            'Proof text is represented by pointers, lengths and hashes, not duplicated excerpts.',
            'No collection, canonical/proposal/review changes or permission decisions.']}
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
