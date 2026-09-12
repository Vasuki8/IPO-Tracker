#!/usr/bin/env python3
"""Build data/ipos.json from NSE current, upcoming and historical IPO endpoints.

The NSE endpoints used here are public web endpoints rather than a documented
commercial API. The collector therefore treats failures conservatively: it will
never replace a healthy dataset with an empty response.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"
IST = ZoneInfo("Asia/Kolkata")

NSE_HOME = "https://www.nseindia.com"
NSE_API = f"{NSE_HOME}/api"
SOURCE_URL = f"{NSE_HOME}/market-data/all-upcoming-issues-ipo"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": SOURCE_URL,
    "Connection": "keep-alive",
}


def now_ist() -> datetime:
    return datetime.now(IST)


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value or "ipo"


def first(obj: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = obj.get(key)
        if value not in (None, "", "-", "--", "NA", "N/A"):
            return value
    return default


def number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return float(value)
    text = str(value).replace(",", "").replace("₹", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def integer(value: Any) -> int | None:
    n = number(value)
    return int(n) if n is not None else None


def iso_date(value: Any) -> str | None:
    if value in (None, "", "-", "--"):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    candidates = (
        "%d-%b-%Y", "%d-%B-%Y", "%d/%m/%Y", "%d-%m-%Y",
        "%Y-%m-%d", "%d %b %Y", "%d %B %Y",
    )
    for fmt in candidates:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    match = re.search(r"(\d{1,2})[-/ ]([A-Za-z]{3,9}|\d{1,2})[-/ ](\d{4})", text)
    if match:
        d, m, y = match.groups()
        for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(f"{d}-{m}-{y}", fmt).date().isoformat()
            except ValueError:
                pass
    return None


def price_band(record: dict[str, Any]) -> dict[str, float | None] | None:
    low = number(first(record, "minPrice", "priceMin", "lowerPrice", "floorPrice"))
    high = number(first(record, "maxPrice", "priceMax", "upperPrice", "capPrice"))
    raw = first(record, "issuePrice", "priceBand", "priceRange")
    if (low is None or high is None) and raw is not None:
        nums = [float(x.replace(",", "")) for x in re.findall(r"\d+(?:\.\d+)?", str(raw).replace(",", ""))]
        if nums:
            low = low if low is not None else nums[0]
            high = high if high is not None else nums[-1]
    if low is None and high is None:
        return None
    if high is None:
        high = low
    if low is None:
        low = high
    return {"min": low, "max": high}


def normalize_board(record: dict[str, Any]) -> str:
    text = " ".join(str(first(record, k, default="")) for k in ("series", "category", "securityType", "issueType", "marketType")).upper()
    return "SME" if "SME" in text or "EMERGE" in text else "Mainboard"


def derive_status(open_date: str | None, close_date: str | None, listing_date: str | None, hint: str | None) -> str:
    today = now_ist().date()
    od = date.fromisoformat(open_date) if open_date else None
    cd = date.fromisoformat(close_date) if close_date else None
    ld = date.fromisoformat(listing_date) if listing_date else None
    if od and today < od:
        return "upcoming"
    if od and cd and od <= today <= cd:
        return "open"
    if ld and today >= ld:
        return "listed"
    if cd and today > cd:
        return "closed"
    h = (hint or "").lower()
    if "active" in h or "open" in h:
        return "open"
    if "upcoming" in h:
        return "upcoming"
    if "list" in h:
        return "listed"
    return "upcoming"


def map_subscription(record: dict[str, Any]) -> dict[str, float | None] | None:
    total = number(first(record, "noOfTime", "subscription", "timesSubscribed", "totalSubscription"))
    sub = {"qib": None, "nii": None, "retail": None, "total": total}
    for k, target in (
        ("qib", "qib"), ("qualifiedInstitutionalBuyers", "qib"),
        ("nii", "nii"), ("hni", "nii"), ("nonInstitutionalInvestors", "nii"),
        ("retail", "retail"), ("rii", "retail"), ("retailIndividualInvestors", "retail"),
    ):
        if k in record:
            sub[target] = number(record[k])
    return sub if any(v is not None for v in sub.values()) else None


def normalize_record(record: dict[str, Any], source_kind: str) -> dict[str, Any]:
    company = str(first(record, "companyName", "company", "issuerName", "name", "symbol", default="Unknown IPO")).strip()
    symbol = first(record, "symbol", "nseSymbol", "securitySymbol")
    open_date = iso_date(first(record, "issueStartDate", "openDate", "issueOpenDate", "biddingStartDate"))
    close_date = iso_date(first(record, "issueEndDate", "closeDate", "issueCloseDate", "biddingEndDate"))
    listing_date = iso_date(first(record, "listingDate", "dateOfListing", "listing_date"))
    issue_price = number(first(record, "issuePrice", "finalIssuePrice", "cutOffPrice"))
    list_price = number(first(record, "listingPrice", "listPrice", "openPrice"))
    gain = None
    if issue_price and list_price:
        gain = round((list_price / issue_price - 1) * 100, 2)
    band = price_band(record)
    board = normalize_board(record)
    hint = str(first(record, "status", "issueStatus", default=source_kind))
    status = derive_status(open_date, close_date, listing_date, hint)

    stable = str(symbol or company)
    out = {
        "id": slugify(stable),
        "symbol": str(symbol).strip() if symbol else None,
        "company": company,
        "board": board,
        "exchange": "NSE" if board == "Mainboard" else "NSE Emerge",
        "status": status,
        "openDate": open_date,
        "closeDate": close_date,
        "allotmentDate": iso_date(first(record, "allotmentDate", "basisOfAllotmentDate")),
        "listingDate": listing_date,
        "priceBand": band,
        "lotSize": integer(first(record, "lotSize", "marketLot", "minimumBidQuantity", "minBidQuantity")),
        "issueSizeCr": number(first(record, "issueSize", "issueSizeCr", "totalIssueSize")),
        "freshIssueCr": number(first(record, "freshIssue", "freshIssueCr")),
        "ofsCr": number(first(record, "offerForSale", "ofs", "ofsCr")),
        "sharesOffered": integer(first(record, "noOfSharesOffered", "sharesOffered", "offeredReserved")),
        "sharesBid": integer(first(record, "noOfsharesBid", "sharesBid", "bids")),
        "subscription": map_subscription(record),
        "listing": ({"issuePrice": issue_price, "listPrice": list_price, "gainPct": gain} if (issue_price is not None or list_price is not None) else None),
        "source": {
            "name": f"NSE {source_kind}",
            "url": SOURCE_URL,
            "asOf": now_ist().isoformat(timespec="seconds"),
        },
    }
    return out


def merge_non_null(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in incoming.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_non_null(result[key], value)
        else:
            result[key] = value
    return result


@dataclass
class NSEClient:
    timeout: int = 20

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.primed = False

    def prime(self) -> None:
        if self.primed:
            return
        # Cookie handshake. NSE frequently rejects direct API calls without it.
        for url in (f"{NSE_HOME}/option-chain", SOURCE_URL, NSE_HOME):
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code < 500:
                    self.primed = True
                    return
            except requests.RequestException:
                continue

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        self.prime()
        url = f"{NSE_API}/{path.lstrip('/')}"
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code in (401, 403):
                    self.primed = False
                    self.prime()
                    time.sleep(1.0 + attempt)
                    continue
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                time.sleep(1.0 + attempt)
        raise RuntimeError(f"NSE request failed for {url}: {last_error}")

    def current(self) -> list[dict[str, Any]]:
        payload = self.get("ipo-current-issue")
        return unwrap_records(payload)

    def upcoming(self) -> list[dict[str, Any]]:
        payload = self.get("all-upcoming-issues", {"category": "ipo"})
        return unwrap_records(payload)

    def details(self, symbol: str, series: str) -> list[dict[str, Any]]:
        payload = self.get("ipo-detail", {"symbol": symbol, "series": series})
        return unwrap_records(payload)

    def past(self, start: date, end: date) -> list[dict[str, Any]]:
        params = {"from_date": start.strftime("%d-%m-%Y"), "to_date": end.strftime("%d-%m-%Y")}
        payload = self.get("public-past-issues", params)
        return unwrap_records(payload)


def unwrap_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("data", "records", "results", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        # Sometimes a response is a dict keyed by rows/categories.
        if payload and all(isinstance(v, dict) for v in payload.values()):
            return list(payload.values())
    return []


def history_ranges(start: date, end: date, days: int = 90) -> Iterable[tuple[date, date]]:
    cursor = start
    while cursor <= end:
        chunk_end = min(end, cursor + timedelta(days=days - 1))
        yield cursor, chunk_end
        cursor = chunk_end + timedelta(days=1)


def load_existing() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return {"meta": {}, "ipos": []}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"meta": {}, "ipos": []}


def enrich_details(client: NSEClient, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for raw in records:
        normalized = normalize_record(raw, "current/upcoming")
        symbol = normalized.get("symbol")
        if symbol:
            series = "SME" if normalized.get("board") == "SME" else "EQ"
            try:
                details = client.details(symbol, series)
                for d in details:
                    normalized = merge_non_null(normalized, normalize_record(d, "detail"))
                time.sleep(0.25)
            except Exception as exc:
                print(f"WARN detail {symbol}: {exc}", file=sys.stderr)
        enriched.append(normalized)
    return enriched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history-days", type=int, default=365, help="How many recent days of historical IPOs to refresh")
    parser.add_argument("--bootstrap-history", action="store_true", help="Backfill historical IPOs from --history-from")
    parser.add_argument("--history-from", default="2000-01-01", help="Start date for bootstrap history YYYY-MM-DD")
    parser.add_argument("--skip-details", action="store_true", help="Skip /ipo-detail enrichment")
    args = parser.parse_args()

    client = NSEClient()
    existing = load_existing()
    old_by_id = {x.get("id"): x for x in existing.get("ipos", []) if isinstance(x, dict) and x.get("id")}

    errors: list[str] = []
    gathered: list[dict[str, Any]] = []

    try:
        current_raw = client.current()
        upcoming_raw = client.upcoming()
        live_raw = current_raw + upcoming_raw
        gathered.extend(
            [normalize_record(x, "current") for x in current_raw]
            + [normalize_record(x, "upcoming") for x in upcoming_raw]
            if args.skip_details
            else enrich_details(client, live_raw)
        )
        print(f"Fetched current={len(current_raw)} upcoming={len(upcoming_raw)}")
    except Exception as exc:
        errors.append(f"live/upcoming: {exc}")
        print(f"ERROR live/upcoming: {exc}", file=sys.stderr)

    hist_end = now_ist().date()
    hist_start = date.fromisoformat(args.history_from) if args.bootstrap_history else hist_end - timedelta(days=max(args.history_days, 1))
    historical_count = 0
    for start, end in history_ranges(hist_start, hist_end):
        try:
            rows = client.past(start, end)
            historical_count += len(rows)
            gathered.extend(normalize_record(x, "historical") for x in rows)
            time.sleep(0.25)
        except Exception as exc:
            errors.append(f"history {start}..{end}: {exc}")
            print(f"WARN history {start}..{end}: {exc}", file=sys.stderr)
            if args.bootstrap_history:
                continue
            break
    print(f"Fetched historical rows={historical_count}")

    if not gathered:
        print("No data fetched. Existing dataset preserved.", file=sys.stderr)
        return 2

    merged: dict[str, dict[str, Any]] = dict(old_by_id)
    for item in gathered:
        key = item["id"]
        merged[key] = merge_non_null(merged.get(key, {}), item)

    # Re-derive status from dates on every update so stale records migrate naturally.
    for item in merged.values():
        item["status"] = derive_status(item.get("openDate"), item.get("closeDate"), item.get("listingDate"), item.get("status"))

    def sort_key(item: dict[str, Any]) -> tuple[str, str]:
        return (item.get("openDate") or item.get("listingDate") or "0000-00-00", item.get("company") or "")

    rows = sorted(merged.values(), key=sort_key, reverse=True)
    out = {
        "meta": {
            "schemaVersion": 1,
            "generatedAt": now_ist().isoformat(timespec="seconds"),
            "timezone": "Asia/Kolkata",
            "source": "NSE India web data endpoints",
            "seed": False,
            "recordCount": len(rows),
            "historyStart": hist_start.isoformat(),
            "errors": errors,
        },
        "ipos": rows,
    }
    DATA_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} records to {DATA_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
