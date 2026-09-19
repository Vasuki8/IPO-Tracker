"""Verify public review delivery, adding held profiles and repair reports.

Uses the existing release verifier and its complete-byte HTTPS contract. It does
not fetch canonical/proposal data or establish source-value accuracy.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

import verify_public_release as public
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from source_review_holds import active_hold_reviews
from source_review_queue import expand_review_items

REVIEW_PATHS = ('ipo/snehaa/index.html', 'ipo/sacheerome/index.html',
                'data/validation.json', 'data/missing_queue.json', 'data/phase_status.json')


def verify_subscription_holds(root, receipt):
    """Verify actual hold delivery and actionable reviews, not source accuracy."""
    registry = public.read_json((root / 'data/public_display_holds.json').read_bytes())
    public.require(isinstance(registry.get('holds'), list), 'Missing public hold registry')
    holds = [h for h in registry['holds'] if h.get('scope') == 'subscription_snapshot']
    if not holds:
        return []
    canonical = public.read_json((root / 'data/ipos.json').read_bytes())
    rows = {r['id']: r for r in canonical['ipos']}
    summary = public.read_json((root / 'data/ipos-summary.json').read_bytes())
    summaries = {r['id']: r for r in summary['ipos']}
    validation = public.read_json((root / 'data/validation.json').read_bytes())
    queue = public.read_json((root / 'data/missing_queue.json').read_bytes())
    queued = {r['id']: r for r in queue['queue']}
    checked = []
    for hold in holds:
        key = hold['id']
        issues = active_hold_reviews(rows.get(key, {}), [hold])
        checked.append({'id': key, 'active': bool(issues),
                        'snapshotDigest': hold['fields']['subscription']['snapshotDigest']})
        if not issues:
            continue  # A different snapshot is not an automatically resolved review.
        public.require(key in summaries and key in queued, key + ': held issuer missing from public inventory/queue')
        path = summaries[key]['profilePath']
        public.require(isinstance(path, str) and re.fullmatch(r'ipo/[a-z0-9][a-z0-9-]*/', path), 'Unsafe held profile path')
        profile = public.embedded_profile((root / path / 'index.html').read_bytes())
        for row in (summaries[key], profile):
            public.require(row.get('subscription') in (None, {}), key + ': held subscription leaked')
            decision = row['publicQuality']['fields']['subscription']
            public.require(decision.get('state') == 'under_review'
                           and decision.get('reason') == 'subscription_snapshot_conflict', key + ': missing subscription hold decision')
        public.require(not profile.get('subscriptionHistory'), key + ': held history leaked')
        tasks = expand_review_items(queued[key], queue.get('sourceReviewDefinitions', []))
        for issue in issues:
            public.require(issue in validation['issues'], key + ': active review missing from validation')
            public.require(any(t.get('reviewType') == issue['reviewType'] and t.get('displayHold') == issue['displayHold']
                               and t.get('route') == 'manual-source-review' and t.get('repairGap') is None
                               for t in tasks), key + ': active review missing from actionable queue')
        name = path + 'index.html'
        receipt['expectedSha256'][name] = public.digest((root / name).read_bytes())
        if path not in receipt['sampledProfiles']:
            receipt['sampledProfiles'].append(path)
    return checked


def prepare(root):
    root = Path(root)
    receipt = public.verify_local(root)
    receipt['reviewedPublication'] = public.verify_reviewed_publication(root, receipt)
    for name in REVIEW_PATHS:
        receipt['expectedSha256'][name] = public.digest((root / name).read_bytes())
        if name.endswith('/index.html'):
            profile = name[:-len('index.html')]
            if profile not in receipt['sampledProfiles']:
                receipt['sampledProfiles'].append(profile)
    receipt['subscriptionHolds'] = verify_subscription_holds(root, receipt)
    receipt['additionalReviewPaths'] = list(REVIEW_PATHS)
    return receipt


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    cli.add_argument('--base-url', required=True)
    cli.add_argument('--expected-commit', required=True)
    cli.add_argument('--accepted-baseline', type=Path)
    args = cli.parse_args()
    receipt = {'expectedCommit': args.expected_commit, 'status': 'failed',
               'scope': 'public-artifact-and-review-delivery-not-source-accuracy'}
    try:
        public.require(bool(re.fullmatch(r'[a-f0-9]{40}', args.expected_commit)), 'Expected commit must be a full SHA')
        receipt.update(prepare(args.root))
        if args.accepted_baseline:
            receipt['acceptedPreservation'] = public.verify_accepted_preservation(args.root, receipt, args.accepted_baseline)
        receipt['baseUrl'] = public.validate_base(args.base_url)
        receipt['httpChecked'] = public.verify_http(args.root, args.base_url, receipt)
        receipt['status'] = 'passed'
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        receipt['error'] = str(error)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
