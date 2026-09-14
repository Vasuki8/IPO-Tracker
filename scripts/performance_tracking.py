"""Official NSE price observations and explicitly unadjusted IPO returns.

Listing-day gains require a quote from the confirmed listing date. A later
opening price is never substituted. Benchmark excess returns require matching
dated baselines; absent baselines remain null.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import update_data as core
from validate_data import numeric
from performance_metrics import percentage, refresh_returns

ROOT = Path(__file__).resolve().parents[1]
IST = timezone(timedelta(hours=5, minutes=30))


def observed_time(value):
    for fmt in ('%d-%b-%Y %H:%M:%S', '%d-%m-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(str(value), fmt).replace(tzinfo=IST).isoformat()
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed.isoformat() if parsed.tzinfo else parsed.replace(tzinfo=IST).isoformat()
    except ValueError:
        return None


def apply_quote(record, quote):
    if record.get('issueEventType'):
        return False
    symbol = str(record.get('symbol') or '').upper()
    actual = str((quote.get('info') or {}).get('symbol') or '').upper()
    if not symbol or actual != symbol:
        raise ValueError('Quote identity does not match IPO symbol')
    price_info, metadata = quote.get('priceInfo') or {}, quote.get('metadata') or {}
    last = core.number(price_info.get('lastPrice'))
    when = observed_time(metadata.get('lastUpdateTime'))
    if not numeric(last) or last <= 0 or not when:
        raise ValueError('Quote lacks a valid official price or observation timestamp')
    url = 'https://www.nseindia.com/api/quote-equity?' + urlencode({'symbol': symbol})
    issue_price = (record.get('listing') or {}).get('issuePrice')
    # A price-band cap is not automatically the final issue price.
    issue_price = issue_price if numeric(issue_price) and issue_price > 0 else None
    performance = record.setdefault('performance', {})
    previous = performance.get('latest') or {}
    observed = datetime.fromisoformat(when)
    if observed > datetime.now(IST) + timedelta(minutes=5):
        raise ValueError('Quote observation is in the future')
    if record.get('listingDate') and when[:10] < record['listingDate']:
        raise ValueError('Quote observation precedes this IPO listing')
    if previous.get('priceType') == 'official daily close' and str(previous.get('observedAt', ''))[:10] >= when[:10]:
        return False
    if previous.get('observedAt') and datetime.fromisoformat(observed_time(previous['observedAt'])) > observed:
        return False
    if previous.get('observedAt') == when and previous.get('price') == last:
        refresh_returns(record)
        return False
    observation = {'price': last, 'observedAt': when, 'collectedAt': datetime.now(IST).isoformat(timespec='seconds'), 'source': 'NSE equity quote', 'sourceUrl': url}
    history = performance.setdefault('observations', [])
    if not any(row.get('observedAt') == when and row.get('price') == last for row in history):
        history.append(observation)
    performance.update(latest=observation, issuePrice=issue_price, returnSinceIssuePct=percentage(issue_price, last), returnBasis='Unadjusted price return; excludes dividends and corporate-action adjustments', benchmarkExcessReturnPct=None)
    listed = record.get('listingDate')
    if listed and when[:10] == listed and issue_price:
        opening = core.number(price_info.get('open'))
        if opening and opening > 0:
            listing = record.setdefault('listing', {})
            if listing.get('listPrice') is None:
                listing.update(listPrice=opening, sourceUrl=url, asOf=when, basis='Listing-day opening price versus final issue price')
    refresh_returns(record)
    return True


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--limit', type=int, default=20)
    args = cli.parse_args()
    path = ROOT / 'data/ipos.json'
    payload = json.loads(path.read_text())
    candidates = [row for row in payload['ipos'] if row.get('symbol') and row.get('listingDate') and 'NSE' in str(row.get('exchange', ''))]
    candidates.sort(key=lambda row: ((row.get('performance') or {}).get('lastAttemptAt', ''), -datetime.fromisoformat(row['listingDate']).toordinal()))
    client, updated, failures = core.NSEClient(), 0, []
    for record in candidates[:max(0, args.limit)]:
        try:
            if not client.primed:
                client.s.get(core.NSE_HOME, timeout=20).raise_for_status()
                client.primed = True
            response = client.s.get(core.NSE_API + '/quote-equity', params={'symbol': record['symbol']}, timeout=25)
            response.raise_for_status()
            quote = response.json()
            accepted = apply_quote(record, quote)
            updated += int(accepted)
            record.setdefault('performance', {})['lastAttemptStatus'] = 'updated' if accepted else 'no_change'
        except Exception as exc:
            failures.append({'id': record['id'], 'error': str(exc)[:250]})
            record.setdefault('performance', {})['lastAttemptStatus'] = 'source_blocked'
        record['performance']['lastAttemptAt'] = datetime.now(IST).isoformat(timespec='seconds')
        if len(failures) >= 3 and not updated:
            break
    payload.setdefault('meta', {})['performanceHealth'] = {'updated': updated, 'failed': len(failures), 'outcomes': failures, 'checkedAt': datetime.now(IST).isoformat(timespec='seconds')}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(payload['meta']['performanceHealth']))


if __name__ == '__main__':
    main()
