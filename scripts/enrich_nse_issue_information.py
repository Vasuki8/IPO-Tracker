#!/usr/bin/env python3
"""Backfill recent P4 IPO lot sizes from NSE Issue Information.

NSE's official Issue Information page is backed by `/api/ipo-detail`, whose
`issueInfo.dataList` exposes finalized `Bid Lot` and `Minimum Order Quantity`
values for both current and past IPOs. This source is a better primary lot-size
source than repeatedly scraping historical BSE pages because it is keyed by the
exact NSE symbol and series.

Safety rules:
- recent P4 window only;
- exact symbol plus canonical issuer identity must match;
- explicit NSE debt securities are rejected;
- existing lotSize values are never overwritten;
- every value retains its official NSE page URL and an independent observation;
- per-record cooldown lets scheduled runs progress through a large backlog.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

import update_data as core

DATA_FILE = core.DATA_FILE
ATTEMPT_KEY = "nseIssueInfoLotBackfill"
SOURCE_NAME = "NSE issue information"
API_PATH = "/api/ipo-detail"


def series_for(record: dict[str, Any]) -> str:
    board = str(record.get("board") or "").upper()
    exchange = str(record.get("exchange") or "").upper()
    return "SME" if "SME" in board or "EMERGE" in exchange else "EQ"


def issue_page_url(symbol: str, series: str) -> str:
    return (
        f"{core.NSE_HOME}/market-data/issue-information"
        f"?series={quote(series)}&symbol={quote(symbol)}&type=Past"
    )


def issue_api_url(symbol: str, series: str) -> str:
    return (
        f"{core.NSE_API}/ipo-detail"
        f"?symbol={quote(symbol)}&series={quote(series)}"
    )


def _normalized_symbol(value: Any) -> str:
    return str(value or "").strip().upper()


def _data_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    issue_info = payload.get("issueInfo") or {}
    rows = issue_info.get("dataList") if isinstance(issue_info, dict) else None
    return [row for row in (rows or []) if isinstance(row, dict)]


def issue_fields(payload: dict[str, Any]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for row in _data_list(payload):
        title = " ".join(str(row.get("title") or "").split()).strip()
        value = " ".join(str(row.get("value") or "").split()).strip()
        if title and value:
            fields[title.lower()] = value
    return fields


def parse_lot_terms(payload: dict[str, Any]) -> dict[str, int | None]:
    fields = issue_fields(payload)
    bid_lot = core.integer(fields.get("bid lot"))
    minimum_order = core.integer(fields.get("minimum order quantity"))

    def valid(value: int | None) -> int | None:
        return value if value is not None and 0 < value <= 100_000 else None

    bid_lot = valid(bid_lot)
    minimum_order = valid(minimum_order)
    return {
        "bidLot": bid_lot,
        "minimumOrderQuantity": minimum_order,
        "lotSize": minimum_order or bid_lot,
    }


def identity_matches(record: dict[str, Any], payload: dict[str, Any]) -> bool:
    meta = payload.get("metaInfo") or {}
    if not isinstance(meta, dict):
        return False
    if bool(meta.get("isDebtSec")):
        return False

    expected_symbol = _normalized_symbol(record.get("symbol"))
    returned_symbol = _normalized_symbol(meta.get("symbol"))
    if not expected_symbol or returned_symbol != expected_symbol:
        return False

    expected_company = core.canonical_company(str(record.get("company") or ""))
    returned_company = core.canonical_company(
        str(payload.get("companyName") or meta.get("companyName") or "")
    )
    return bool(expected_company and returned_company and expected_company == returned_company)


def _attempt_date(record: dict[str, Any]) -> date | None:
    raw = (record.get(ATTEMPT_KEY) or {}).get("lastAttemptAt")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def attempted_recently(record: dict[str, Any], today: date, retry_days: int) -> bool:
    if retry_days <= 0:
        return False
    attempted = _attempt_date(record)
    return bool(attempted and attempted >= today - timedelta(days=retry_days))


def is_candidate(
    record: dict[str, Any],
    today: date,
    history_days: int,
    retry_days: int = 0,
) -> bool:
    if record.get("lotSize") not in (None, "", [], {}):
        return False
    symbol = _normalized_symbol(record.get("symbol"))
    if not symbol:
        return False
    exchange = str(record.get("exchange") or "").upper()
    if "NSE" not in exchange:
        return False

    open_date = core.iso_date(record.get("openDate"))
    if not open_date:
        return False
    try:
        opened = date.fromisoformat(open_date)
    except ValueError:
        return False
    if opened < today - timedelta(days=max(0, history_days)) or opened > today + timedelta(days=90):
        return False
    return not attempted_recently(record, today, retry_days)


def mark_attempt(
    record: dict[str, Any],
    *,
    status: str,
    page_url: str,
    api_url: str,
    lot_size: int | None = None,
    error: str | None = None,
) -> None:
    record[ATTEMPT_KEY] = {
        "status": status,
        "lastAttemptAt": core.now_ist().isoformat(timespec="seconds"),
        "pageUrl": page_url,
        "apiUrl": api_url,
        "lotSize": lot_size,
        "error": str(error)[:300] if error else None,
    }


def merge_lot(
    record: dict[str, Any],
    payload: dict[str, Any],
    *,
    page_url: str,
) -> bool:
    if not identity_matches(record, payload):
        return False
    terms = parse_lot_terms(payload)
    lot = terms.get("lotSize")
    if lot is None or record.get("lotSize") not in (None, "", [], {}):
        return False

    record["lotSize"] = lot
    if terms.get("minimumOrderQuantity") is not None:
        record["minimumBidQuantity"] = terms["minimumOrderQuantity"]
    if terms.get("bidLot") is not None:
        record["marketLot"] = terms["bidLot"]

    stamp = core.source_stamp(SOURCE_NAME, page_url, "exchange")
    sources = list(record.get("sources") or [])
    sources = [s for s in sources if str((s or {}).get("name") or "") != SOURCE_NAME]
    sources.append(stamp)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    observation = {
        "symbol": _normalized_symbol(record.get("symbol")),
        "series": series_for(record),
        "lotSize": lot,
        "bidLot": terms.get("bidLot"),
        "minimumOrderQuantity": terms.get("minimumOrderQuantity"),
        "url": page_url,
    }
    record.setdefault("observations", {})["NSE-issue-info"] = observation
    record.setdefault("observations", {}).setdefault("NSE", {})["lotSize"] = lot
    record["validation"] = core.build_validation(record)
    return True


def fetch_detail(
    session: requests.Session,
    symbol: str,
    series: str,
) -> tuple[dict[str, Any], str, str]:
    page_url = issue_page_url(symbol, series)
    api_url = issue_api_url(symbol, series)

    # Issue Information itself is a reliable cookie/bootstrap endpoint on cloud
    # runners, even when the NSE home page returns 403.
    page = session.get(page_url, timeout=30, headers={"Referer": f"{core.NSE_HOME}/"})
    page.raise_for_status()
    response = session.get(api_url, timeout=30, headers={"Referer": page_url})
    if response.status_code in (401, 403):
        # Refresh the issue page and retry once with the new cookies.
        page = session.get(page_url, timeout=30, headers={"Referer": f"{core.NSE_HOME}/"})
        page.raise_for_status()
        response = session.get(api_url, timeout=30, headers={"Referer": page_url})
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("NSE ipo-detail returned a non-object payload")
    return payload, page_url, api_url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history-days", type=int, default=730)
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--retry-days", type=int, default=14)
    parser.add_argument("--sleep", type=float, default=0.08)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    today = core.now_ist().date()
    candidates = [
        row
        for row in records
        if is_candidate(row, today, args.history_days, args.retry_days)
    ]
    candidates.sort(key=lambda row: str(row.get("openDate") or ""), reverse=True)
    if args.limit > 0:
        candidates = candidates[: args.limit]

    session = requests.Session()
    session.headers.update(core.HEADERS)

    attempted = updated = failed = unmatched = no_lot = 0
    errors: list[str] = []

    for record in candidates:
        symbol = _normalized_symbol(record.get("symbol"))
        series = series_for(record)
        page_url = issue_page_url(symbol, series)
        api_url = issue_api_url(symbol, series)
        attempted += 1
        try:
            detail, page_url, api_url = fetch_detail(session, symbol, series)
            if not identity_matches(record, detail):
                unmatched += 1
                mark_attempt(
                    record,
                    status="identity-mismatch",
                    page_url=page_url,
                    api_url=api_url,
                )
            else:
                terms = parse_lot_terms(detail)
                lot = terms.get("lotSize")
                if lot is None:
                    no_lot += 1
                    mark_attempt(
                        record,
                        status="no-lot",
                        page_url=page_url,
                        api_url=api_url,
                    )
                elif merge_lot(record, detail, page_url=page_url):
                    updated += 1
                    mark_attempt(
                        record,
                        status="filled",
                        page_url=page_url,
                        api_url=api_url,
                        lot_size=lot,
                    )
            if args.sleep > 0:
                time.sleep(args.sleep)
        except Exception as exc:
            failed += 1
            errors.append(f"{record.get('company')} ({symbol}/{series}): {exc}")
            mark_attempt(
                record,
                status="error",
                page_url=page_url,
                api_url=api_url,
                error=str(exc),
            )

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["NSE-issue-info"] = {
        "ok": failed == 0 if attempted else True,
        "candidates": len(candidates),
        "attempted": attempted,
        "updated": updated,
        "identityMismatches": unmatched,
        "noLot": no_lot,
        "failed": failed,
        "historyDays": args.history_days,
        "retryDays": args.retry_days,
        "errors": errors[:10],
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "NSE issue-information lot backfill: "
        f"candidates={len(candidates)}, attempted={attempted}, updated={updated}, "
        f"identity_mismatch={unmatched}, no_lot={no_lot}, failed={failed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
