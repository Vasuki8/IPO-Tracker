"""Expose performance coverage and dated observations without implied prices."""
import json
from datetime import datetime, timezone
from pathlib import Path
from validate_data import numeric

ROOT = Path(__file__).resolve().parents[1]


def main():
    payload = json.loads((ROOT / 'data/ipos.json').read_text())
    rows = []
    for record in payload.get('ipos', []):
        if not record.get('listingDate') or record.get('issueEventType'):
            continue
        performance = record.get('performance') or {}
        latest = performance.get('latest') or {}
        price = (record.get('listing') or {}).get('issuePrice')
        rows.append({'id': record['id'], 'company': record.get('company'), 'symbol': record.get('symbol'), 'listingDate': record['listingDate'], 'issuePrice': price if numeric(price) and price > 0 else None, 'latest': latest or None, 'returnSinceIssuePct': performance.get('returnSinceIssuePct'), 'benchmarkExcessReturnPct': performance.get('benchmarkExcessReturnPct'), 'lastAttemptStatus': performance.get('lastAttemptStatus', 'not_collected')})
    report = {'generatedAt': datetime.now(timezone.utc).isoformat(), 'returnBasis': 'Unadjusted price returns; excludes dividends and corporate-action adjustments', 'listedRecords': len(rows), 'withFinalIssuePrice': sum(row['issuePrice'] is not None for row in rows), 'withPriceObservation': sum(row['latest'] is not None for row in rows), 'withBenchmarkComparison': sum(row['benchmarkExcessReturnPct'] is not None for row in rows), 'records': rows}
    (ROOT / 'data/performance_summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'records'}))


if __name__ == '__main__':
    main()
