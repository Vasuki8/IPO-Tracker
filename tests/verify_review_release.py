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

REVIEW_PATHS = ('ipo/snehaa/index.html', 'ipo/sacheerome/index.html',
                'data/validation.json', 'data/missing_queue.json', 'data/phase_status.json')


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
    receipt['additionalReviewPaths'] = list(REVIEW_PATHS)
    return receipt


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    cli.add_argument('--base-url', required=True)
    cli.add_argument('--expected-commit', required=True)
    args = cli.parse_args()
    receipt = {'expectedCommit': args.expected_commit, 'status': 'failed',
               'scope': 'public-artifact-and-review-delivery-not-source-accuracy'}
    try:
        public.require(bool(re.fullmatch(r'[a-f0-9]{40}', args.expected_commit)), 'Expected commit must be a full SHA')
        receipt.update(prepare(args.root))
        receipt['baseUrl'] = public.validate_base(args.base_url)
        receipt['httpChecked'] = public.verify_http(args.root, args.base_url, receipt)
        receipt['status'] = 'passed'
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        receipt['error'] = str(error)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
