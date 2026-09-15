"""Collect dated NSE daily closes and a NIFTY 50 comparison baseline.

Daily reports provide dates, not intraday observation times. Return calculations
remain explicitly unadjusted; no dividend or corporate-action adjustment is
inferred. A listing-day daily open is accepted only for the exact listing date.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests
import update_data as core
from performance_tracking import IST
from performance_metrics import refresh_returns
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
    symbol = str(record.get("symbol") or "").upper()
    row = prices.get(symbol)
    if (not row or row.get("date") != day or row.get("symbol") != symbol
            or row.get("series") not in SERIES
            or any(not numeric(row.get(key)) or row[key] <= 0 for key in ("open", "close"))
            or not official_url(price_url)):
        return False
    if benchmark and (benchmark.get("symbol") != "NIFTY 50" or benchmark.get("date") != day
            or not numeric(benchmark.get("value")) or benchmark["value"] <= 0 or not official_url(index_url)):
        benchmark = None
    before = copy.deepcopy(record)
    listing = record.setdefault("listing", {})
    performance = record.setdefault("performance", {})
    if day == record["listingDate"]:
        conflicts = []
        for field, value in (("listPrice", row["open"]), ("closePrice", row["close"])):
            if listing.get(field) is not None and listing[field] != value:
                conflicts.append({"field": field, "accepted": listing[field], "proposed": value, "date": day, "sourceUrl": price_url, "sha256": digest})
        if conflicts:
            retained = listing.setdefault("priceConflicts", [])
            for conflict in conflicts:
                if conflict not in retained:
                    retained.append(conflict)
        else:
            listing.update(listPrice=row["open"], closePrice=row["close"], asOf=day, sourceUrl=price_url, priceSourceHash=digest, priceTimePrecision="date", basis="Official listing-day daily report")
            if benchmark:
                performance["benchmarkBaseline"] = {**benchmark, "sourceUrl": index_url}
    # Keep historical rows even when a more recent quote was collected first.
    history = performance.setdefault("observations", [])
    observation = next((item for item in history if item.get("observedAt") == day
                        and item.get("price") == row["close"] and item.get("priceType") == "official daily close"), None)
    if observation is None:
        observation = {"price": row["close"], "observedAt": day, "timePrecision": "date", "priceType": "official daily close", "collectedAt": datetime.now(IST).isoformat(timespec="seconds"), "source": "NSE daily equity report", "sourceUrl": price_url, "sha256": digest}
        history.append(observation)
        history.sort(key=lambda item: str(item.get("observedAt", "")))
    previous = performance.get("latest") or {}
    previous_day = str(previous.get("observedAt", ""))[:10]
    if not previous_day or previous_day < day or (previous_day == day and previous.get("priceType") != "official daily close"):
        performance["latest"] = observation
    latest = performance.get("latest") or {}
    if benchmark and latest.get("observedAt") == day and latest.get("priceType") == "official daily close":
        performance["benchmarkLatest"] = {**benchmark, "sourceUrl": index_url}
    refresh_returns(record)
    return before != record


def official_url(url):
    parsed = urlparse(str(url or ""))
    return parsed.scheme == "https" and parsed.hostname in {"nsearchives.nseindia.com", "archives.nseindia.com", "www.nseindia.com"}


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


def discard_cached_report(url):
    # An unpublished or wrong-date response must be retried on the next run.
    (CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".csv")).unlink(missing_ok=True)


def run(payload, limit=30):
    now = datetime.now(IST)
    candidates = [row for row in payload["ipos"] if row.get("symbol") and row.get("listingDate") and row["listingDate"] <= now.date().isoformat() and not row.get("issueEventType") and "NSE" in str(row.get("exchange", ""))]
    candidates.sort(key=lambda row: ((row.get("performance") or {}).get("historyAttemptAt", ""), -date.fromisoformat(row["listingDate"]).toordinal()))
    selected = candidates[:max(0, limit)]
    last_day = now.date() if now.hour >= 19 else now.date() - timedelta(days=1)
    recent_days = [(last_day - timedelta(days=i)).isoformat() for i in range(7) if (last_day - timedelta(days=i)).weekday() < 5]
    baseline_days = sorted({row["listingDate"] for row in selected if not (row.get("listing") or {}).get("closePrice") or not ((row.get("performance") or {}).get("benchmarkBaseline") or {}).get("sourceUrl")})
    session = requests.Session()
    session.headers.update(core.HEADERS)
    failures, updated, completed = [], 0, set()
    latest_found = False
    for day in list(dict.fromkeys(recent_days + baseline_days)) if selected else []:
        if day in recent_days and latest_found and day not in baseline_days:
            continue
        stamp = date.fromisoformat(day).strftime("%d%m%Y")
        price_url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{stamp}.csv"
        index_url = f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{stamp}.csv"
        try:
            raw, digest = download_csv(session, price_url)
            prices = price_rows(raw, day)
            if not prices:
                discard_cached_report(price_url)
                raise ValueError("Daily report has no matching dated equity rows")
            benchmark = None
            try:
                index_text, _ = download_csv(session, index_url)
                benchmark = index_row(index_text, day)
                if not benchmark:
                    discard_cached_report(index_url)
                    raise ValueError("Index report has no matching dated NIFTY 50 close")
            except Exception as exc:
                failures.append({"date": day, "source": index_url, "error": str(exc)[:200]})
            if day in recent_days:
                latest_found = True
            for record in selected:
                updated += int(apply_daily(record, prices, benchmark, day, price_url, index_url, digest))
                if record["listingDate"] <= day and str(record.get("symbol") or "").upper() in prices:
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
