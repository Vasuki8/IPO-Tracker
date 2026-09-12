#!/usr/bin/env python3
"""Capture timestamped NSE category-wise IPO subscription snapshots.

The core updater already stores NSE's overall subscription multiple from
``/api/ipo-current-issue``. This companion step calls ``/api/ipo-detail`` for
issues whose bidding window is open and preserves QIB / NII / Retail / Total
multiples over time instead of overwriting the previous observation.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402

DATA_FILE = core.DATA_FILE
NSE_HOME = core.NSE_HOME
NSE_API = core.NSE_API
NSE_DETAIL_PAGE = f"{NSE_HOME}/market-data/issue-information"
SNAPSHOT_KEYS = ("qib", "nii", "retail", "total")
MAX_HISTORY = 500


def _first(d: dict[str, Any], *keys, default=None):
    for key in keys:
        value = d.get(key)
        if value not in (None, "", "-", "--", "NA", "N/A"):
            return value
    return default


def _category_text(row: dict[str, Any]) -> str:
    parts = [
        _first(row, "category", "categoryName", "investorCategory", "bidCategory"),
        _first(row, "categoryCode", "code", "caCode"),
    ]
    return " ".join(str(x).strip() for x in parts if x not in (None, "")).lower()


def _classify_category(text: str):
    """Return (field, score) for a headline NSE subscription row.

    NSE occasionally includes NII amount sub-buckets alongside the aggregate NII
    row. The score keeps the aggregate row when both are present.
    """
    t = " ".join(text.replace("-", " ").replace("_", " ").split())
    words = set(t.split())

    if "total" in words or t in {"overall", "grand total"}:
        return "total", 120
    if "qualified institutional" in t or "qib" in words:
        return "qib", 110
    if "retail" in t or "rii" in words:
        return "retail", 110
    if "individual investor" in t and "non institutional" not in t:
        # NSE's 2026 SME terminology uses Individual Investor instead of Retail.
        return "retail", 90
    if "non institutional" in t or "nii" in words or "nib" in words:
        score = 105
        split_markers = (
            "bid amount",
            "above",
            "below",
            "more than",
            "less than",
            "10 lakh",
            "10 lac",
            "2 lakh",
            "2 lac",
            "snii",
            "bnii",
            "small nii",
            "big nii",
        )
        if any(marker in t for marker in split_markers):
            return None, 0
        return "nii", score
    return None, 0


def parse_bid_details(payload: Any) -> dict[str, float | None]:
    """Map NSE ``ipo-detail`` bid rows to qib/nii/retail/total multiples."""
    rows = payload.get("bidDetails") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        rows = []

    best: dict[str, tuple[int, float]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = core.number(
            _first(
                row,
                "noOfTime",
                "subscription",
                "timesSubscribed",
                "subscriptionTimes",
            )
        )
        if value is None or value < 0:
            continue
        field, score = _classify_category(_category_text(row))
        if not field:
            continue
        current = best.get(field)
        if current is None or score > current[0]:
            best[field] = (score, value)

    # Some NSE responses expose the overall multiple at the payload root.
    if "total" not in best and isinstance(payload, dict):
        root_total = core.number(
            _first(payload, "noOfTime", "subscription", "timesSubscribed", "totalSubscription")
        )
        if root_total is not None and root_total >= 0:
            best["total"] = (80, root_total)

    return {key: (best[key][1] if key in best else None) for key in SNAPSHOT_KEYS}


def _same_values(a: dict[str, Any], b: dict[str, Any]) -> bool:
    for key in SNAPSHOT_KEYS:
        av = core.number(a.get(key))
        bv = core.number(b.get(key))
        if av is None and bv is None:
            continue
        if av is None or bv is None or abs(av - bv) > 1e-9:
            return False
    return True


def append_snapshot(record: dict[str, Any], snapshot: dict[str, Any], *, force=False) -> bool:
    """Append a changed snapshot; preserve a bounded, chronological history."""
    history = [x for x in (record.get("subscriptionHistory") or []) if isinstance(x, dict)]
    history.sort(key=lambda x: str(x.get("capturedAt") or ""))
    if history and not force and _same_values(history[-1], snapshot):
        record["subscriptionHistory"] = history[-MAX_HISTORY:]
        return False
    history.append(snapshot)
    record["subscriptionHistory"] = history[-MAX_HISTORY:]
    return True


def _is_open_record(record: dict[str, Any], today) -> bool:
    if not record.get("symbol"):
        return False
    try:
        opened = datetime.fromisoformat(record["openDate"]).date() if record.get("openDate") else None
        closed = datetime.fromisoformat(record["closeDate"]).date() if record.get("closeDate") else None
    except (TypeError, ValueError):
        opened = closed = None

    if opened and closed:
        return opened <= today <= closed
    return str(record.get("status") or "").lower() == "open"


def candidate_records(payload: dict[str, Any], *, company=None, limit=30):
    today = core.now_ist().date()
    rows = []
    needle = (company or "").strip().lower()
    for record in payload.get("ipos") or []:
        if not isinstance(record, dict) or not _is_open_record(record, today):
            continue
        if needle and needle not in str(record.get("company") or "").lower():
            continue
        rows.append(record)
    rows.sort(key=lambda x: (x.get("closeDate") or "", x.get("company") or ""))
    return rows[:limit] if limit > 0 else rows


class NSESubscriptionClient:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(core.HEADERS)
        self.primed = False

    def _prime(self):
        if self.primed:
            return
        r = self.s.get(NSE_HOME, timeout=20)
        r.raise_for_status()
        self.primed = True

    def detail(self, symbol: str, board: str | None = None):
        self._prime()
        series_options = ["EQ", "SME"] if str(board or "").upper() == "SME" else ["EQ"]
        last_payload = None
        last_error = None
        for series in series_options:
            try:
                r = self.s.get(
                    f"{NSE_API}/ipo-detail",
                    params={"symbol": symbol, "series": series},
                    timeout=25,
                    headers={"Referer": NSE_DETAIL_PAGE},
                )
                r.raise_for_status()
                payload = r.json()
                last_payload = payload
                if isinstance(payload, dict) and isinstance(payload.get("bidDetails"), list):
                    return payload, series
            except Exception as exc:  # noqa: BLE001 - try the next supported series
                last_error = exc
        if last_payload is not None:
            return last_payload, series_options[-1]
        if last_error:
            raise last_error
        return {}, series_options[-1]


def _source_url(symbol: str, series: str):
    return f"{NSE_DETAIL_PAGE}?{urlencode({'symbol': symbol, 'series': series})}"


def _replace_subscription_source(record: dict[str, Any], source: dict[str, Any]):
    sources = list(record.get("sources") or [])
    sources = [s for s in sources if str((s or {}).get("name") or "") != "NSE subscription detail"]
    sources.append(source)
    record["sources"] = sources


def update_record(record: dict[str, Any], detail: Any, *, series="EQ", force_snapshot=False):
    parsed = parse_bid_details(detail)
    if not any(value is not None for value in parsed.values()):
        raise ValueError("NSE ipo-detail returned no headline subscription rows")

    captured_at = core.now_ist().isoformat(timespec="seconds")
    current = dict(record.get("subscription") or {})
    for key, value in parsed.items():
        if value is not None:
            current[key] = value
    record["subscription"] = current
    record["subscriptionAsOf"] = captured_at

    snapshot = {"capturedAt": captured_at, "source": "NSE ipo-detail"}
    snapshot.update({key: core.number(current.get(key)) for key in SNAPSHOT_KEYS})
    added = append_snapshot(record, snapshot, force=force_snapshot)

    symbol = str(record.get("symbol") or "").strip()
    source = core.source_stamp(
        "NSE subscription detail",
        _source_url(symbol, series),
        "exchange",
        captured_at,
    )
    _replace_subscription_source(record, source)
    return added


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--company", default=None)
    parser.add_argument("--force-snapshot", action="store_true")
    args = parser.parse_args()

    try:
        payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"Cannot load {DATA_FILE}: {exc}", file=sys.stderr)
        return 2

    records = candidate_records(payload, company=args.company, limit=args.limit)
    client = NSESubscriptionClient()
    attempted = updated = snapshots_added = failed = 0
    errors = []

    for record in records:
        attempted += 1
        try:
            detail, series = client.detail(str(record.get("symbol") or "").strip(), record.get("board"))
            added = update_record(record, detail, series=series, force_snapshot=args.force_snapshot)
            updated += 1
            snapshots_added += int(added)
            print(
                f"Subscription {record.get('company')}: "
                f"QIB={record.get('subscription', {}).get('qib')} "
                f"NII={record.get('subscription', {}).get('nii')} "
                f"Retail={record.get('subscription', {}).get('retail')} "
                f"Total={record.get('subscription', {}).get('total')}"
            )
        except Exception as exc:  # noqa: BLE001 - one issue must not block the refresh
            failed += 1
            msg = f"{record.get('company')}: {exc}"
            errors.append(msg)
            print(f"Subscription refresh failed: {msg}", file=sys.stderr)

    meta = payload.setdefault("meta", {})
    meta["schemaVersion"] = max(int(meta.get("schemaVersion") or 1), 4)
    meta["subscriptionHealth"] = {
        "ok": failed == 0 if attempted else True,
        "attempted": attempted,
        "updated": updated,
        "snapshotsAdded": snapshots_added,
        "failed": failed,
        "asOf": core.now_ist().isoformat(timespec="seconds"),
        "errors": errors[:10],
    }
    meta.setdefault("sourceHealth", {})["NSE-subscription"] = {
        "ok": failed == 0 if attempted else True,
        "records": updated,
        "attempted": attempted,
        "snapshotsAdded": snapshots_added,
        "failed": failed,
    }

    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Subscription tracking: attempted={attempted}, updated={updated}, "
        f"snapshots_added={snapshots_added}, failed={failed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
