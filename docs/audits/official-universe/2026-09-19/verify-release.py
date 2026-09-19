"""Read-only exact-byte public delivery check for this historical admission batch."""
import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests'))
import verify_review_release as review
import verify_public_release as public


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--base-url', default='https://vasuki8.github.io/IPO-Tracker/')
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    receipt = {'expectedCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'checkedAt': dt.datetime.now(dt.timezone.utc).isoformat(), 'status': 'failed',
               'scope': 'Public delivery and identity-only null contract; official source identity reviewed separately'}
    try:
        receipt.update(review.prepare(ROOT))
        receipt['baseUrl'] = public.validate_base(args.base_url)
        audit_dir = Path(__file__).resolve().parent
        expected = json.loads((audit_dir / 'admission-review.json').read_text(encoding='utf-8'))['records']
        canonical = {r['id']: r for r in json.loads((ROOT / 'data/ipos.json').read_bytes())['ipos']}
        summaries = {r['id']: r for r in json.loads((ROOT / 'data/ipos-summary.json').read_bytes())['ipos']}
        checked = []
        for want in expected:
            key = want['id']
            record = canonical[key]
            name = record['profilePath'] + 'index.html'
            profile = public.embedded_profile((ROOT / name).read_bytes())
            for row in (summaries[key], profile):
                for field in ('id', 'company', 'symbol', 'board', 'status', 'openDate', 'closeDate', 'listingDate'):
                    public.require(row.get(field) == record.get(field), key + ': identity differs in ' + field)
                for field in ('priceBand', 'lotSize', 'marketLot', 'minimumBidQuantity', 'minimumApplicationAmount', 'issueSizeCr', 'financials', 'subscription', 'listingDate'):
                    public.require(row.get(field) is None, key + ': unknown value invented in ' + field)
            public.require(record['company'] == want['issuerName'] and record['symbol'] == want['identity']['symbol'], key + ': reviewed identity mismatch')
            public.require(record['status'] == 'closed', key + ': listing inferred')
            public.require(record['source']['asOf'] is None and record['source']['collectedAt'] == want['retrievedAt'], key + ': source clock differs')
            public.require(want['sourceUrl'] in (ROOT / name).read_text(encoding='utf-8'), key + ': source link absent')
            receipt['expectedSha256'][name] = public.digest((ROOT / name).read_bytes())
            checked.append({'id': key, 'sourceUrl': want['sourceUrl'], 'profilePath': name})
        receipt['admissions'] = checked
        receipt['httpChecked'] = public.verify_http(ROOT, args.base_url, receipt)
        receipt['status'] = 'passed'
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        receipt['error'] = str(exc)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: receipt.get(k) for k in ('expectedCommit', 'status', 'error')}))
    return int(receipt['status'] != 'passed')


if __name__ == '__main__':
    raise SystemExit(main())
