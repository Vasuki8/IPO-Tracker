"""Collect dated NSE daily closes and a NIFTY 50 comparison baseline.

Daily reports provide dates, not intraday observation times. Return calculations
remain explicitly unadjusted; no dividend or corporate-action adjustment is
inferred. A listing-day daily open is accepted only for the exact listing date.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
import update_data as core
from performance_tracking import IST, percentage
from validate_data import numeric

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/daily-reports"
SERIES = {"EQ", "BE", "BZ", "SM", "ST"}


def report_date(value):
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return None


def csv_rows(text):
    for row in csv.DictReader(io.StringIO(text.lstrip("\ufeff"))):
        yield {str(key).strip().upper().replace(" ", ""): str(value or "").strip() for key, value in row.items() if key is not None}


def price_rows(text, day):
    output = {}
    duplicates = set()
    for row in csv_rows(text):
        if report_date(row.get("DATE1")) != day or row.get("SERIES") not in SERIES:
            continue
        symbol = row.get("SYMBOL")
        opening, close = core.number(row.get("OPEN_PRICE")), core.number(row.get("CLOSE_PRICE"))
        if not symbol or not numeric(close) or close <= 0 or not numeric(opening) or opening <= 0:
            continue
        value = {"symbol": symbol, "series": row["SERIES"], "date": day, "open": opening, "close": close}
        if symbol in output and output[symbol] != value:
            duplicates.add(symbol)
        output[symbol] = value
    return {key: value for key, value in output.items() if key not in duplicates}


def index_row(text, day):
    rows = []
    for row in csv_rows(text):
        if row.get("INDEXNAME", "").upper() != "NIFTY 50" or report_date(row.get("INDEXDATE")) != day:
            continue
        value = core.number(row.get("CLOSINGINDEXVALUE"))
        if numeric(value) and value > 0:
            rows.append(value)
    if rows and len(set(rows)) == 1:
        return {"symbol": "NIFTY 50", "date": day, "value": rows[0]}
    return None


def apply_daily(record, prices, benchmark, day, price_url, index_url, digest):
    if record.get("issueEventType") or not record.get("listingDate") or day < record["listingDate"] or day > datetime.now(IST).date().isoformat():
        return False
    row = prices.get(str(record.get("symbol") or "").upper())
    if not row or row["date"] != day:
        return False
    listing = record.setdefault("listing", {})
    performance = record.setdefault("performance", {})
    changed = False
    if day == record["listingDate"]:
        for field, value in (("listPrice", row["open"]), ("closePrice", row["close"])):
            if listing.get(field) is None:
                listing[field] = value
                changed = True
        listing.update(asOf=day, sourceUrl=price_url, priceSourceHash=digest, priceTimePrecision="date", basis="Official listing-day daily report")
        listing["gainPct"] = percentage(listing.get("issuePrice"), listing.get("listPrice"))
        if benchmark:
            performance["benchmarkBaseline"] = {**benchmark, "sourceUrl": index_url}
    previous = performance.get("latest") or {}
    if not previous.get("observedAt") or str(previous["observedAt"])[:10] < day:
        observation = {"price": row["close"], "observedAt": day, "timePrecision": "date", "priceType": "official daily close", "collectedAt": datetime.now(IST).isoformat(timespec="seconds"), "source": "NSE daily equity report", "sourceUrl": price_url, "sha256": digest}
        history = performance.setdefault("observations", [])
        if not any(item.get("observedAt") == day and item.get("price") == row["close"] for item in history):
            history.append(observation)
        performance.update(latest=observation, issuePrice=listing.get("issuePrice"), returnSinceIssuePct=percentage(listing.get("issuePrice"), row["close"]), returnBasis="Unadjusted price return; excludes dividends and corporate-action adjustments", benchmarkExcessReturnPct=None)
        if benchmark:
            performance["benchmarkLatest"] = {**benchmark, "sourceUrl": index_url}
        changed = True
    baseline = performance.get("benchmarkBaseline") or {}
    latest_index = performance.get("benchmarkLatest") or {}
    latest = performance.get("latest") or {}
    if baseline.get("symbol") == latest_index.get("symbol") == "NIFTY 50" and baseline.get("date") == record["listingDate"] and latest_index.get("date") == str(latest.get("observedAt", ""))[:10] and str(listing.get("asOf", ""))[:10] == record["listingDate"] and baseline.get("sourceUrl") and latest_index.get("sourceUrl"):
        own_return = percentage(listing.get("closePrice"), latest.get("price"))
        index_return = percentage(baseline.get("value"), latest_index.get("value"))
        if own_return is not None and index_return is not None:
            performance["benchmarkExcessReturnPct"] = round(own_return - index_return, 4)
            performance["benchmarkReturnBasis"] = "Listing-day close to matched-date close; NIFTY 50 price index"
    return changed


def download_csv(session, url):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".csv")
    if path.exists():
        data = path.read_bytes()
    else:
        with session.get(url, timeout=(10, 35), stream=True) as response:
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_content(131072):
                size += len(chunk)
                if size > 16 * 1024 * 1024:
                    raise ValueError("Daily CSV exceeds 16 MiB")
                chunks.append(chunk)
            data = b"".join(chunks)
        if b"<html" in data[:500].lower():
            raise ValueError("Daily report returned HTML")
        path.write_bytes(data)
    return data.decode("utf-8-sig"), hashlib.sha256(data).hexdigest()


def run(payload, limit=30):
    candidates = [row for row in payload["ipos"] if row.get("symbol") and row.get("listingDate") and not row.get("issueEventType") and "NSE" in str(row.get("exchange", ""))]
    candidates.sort(key=lambda row: ((row.get("performance") or {}).get("historyAttemptAt", ""), -date.fromisoformat(row["listingDate"]).toordinal()))
    selected = candidates[:max(0, limit)]
    now = datetime.now(IST)
    last_day = now.date() if now.hour >= 19 else now.date() - timedelta(days=1)
    recent_days = [(last_day - timedelta(days=i)).isoformat() for i in range(7) if (last_day - timedelta(days=i)).weekday() < 5]
    baseline_days = sorted({row["listingDate"] for row in selected if not (row.get("listing") or {}).get("closePrice")})
    session = requests.Session()
    session.headers.update(core.HEADERS)
    failures, updated, completed = [], 0, set()
    latest_found = False
    for day in list(dict.fromkeys(recent_days + baseline_days)):
        if day in recent_days and latest_found and day not in baseline_days:
            continue
        stamp = date.fromisoformat(day).strftime("%d%m%Y")
        price_url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{stamp}.csv"
        index_url = f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{stamp}.csv"
        try:
            raw, digest = download_csv(session, price_url)
            prices = price_rows(raw, day)
            if not prices:
                raise ValueError("Daily report has no matching dated equity rows")
            benchmark = None
            try:
                index_text, _ = download_csv(session, index_url)
                benchmark = index_row(index_text, day)
            except Exception as exc:
                failures.append({"date": day, "source": index_url, "error": str(exc)[:200]})
            if day in recent_days:
                latest_found = True
            for record in selected:
                updated += int(apply_daily(record, prices, benchmark, day, price_url, index_url, digest))
                if record.get("symbol") in prices:
                    completed.add(record["id"])
        except requests.HTTPError as exc:
            failures.append({"date": day, "source": price_url, "error": str(exc)[:200]})
            if exc.response is not None and exc.response.status_code in {401, 403, 429}:
                break
        except Exception as exc:
            failures.append({"date": day, "source": price_url, "error": str(exc)[:200]})
    for record in selected:
        record.setdefault("performance", {}).update(historyAttemptAt=now.isoformat(timespec="seconds"), historyAttemptStatus="updated" if record["id"] in completed else "source_unavailable")
    health = {"selected": len(selected), "updatedObservations": updated, "recordsObserved": len(completed), "failed": len(failures), "errors": failures, "checkedAt": now.isoformat(timespec="seconds")}
    payload.setdefault("meta", {})["priceHistoryHealth"] = health
    return health


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--limit", type=int, default=30)
    args = cli.parse_args()
    path = ROOT / "data/ipos.json"
    payload = json.loads(path.read_text())
    print(json.dumps(run(payload, args.limit)))
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


if __name__ == "__main__":
    main()
