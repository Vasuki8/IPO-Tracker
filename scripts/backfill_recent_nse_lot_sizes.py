#!/usr/bin/env python3
"""Backfill recent P4 IPO lot sizes from NSE's official issue-detail endpoint.

This pass exists because NSE's current/upcoming/history spine does not always
retain the final bid lot after an issue closes, while the issue-detail payload
can still expose it.

Safety rules:
- only P4 recent-history records already present in data/missing_queue.json;
- only records whose lotSize is still missing;
- official NSE endpoint only;
- fill-only merge; existing values are never overwritten;
- SME issues require an explicit lot field (minimum application quantity may be
  two lots under newer SME rules and is therefore not treated as one lot);
- conflicting explicit lot values are rejected rather than guessed;
- endpoint/WAF failures are non-fatal and do not corrupt the dataset.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = core.DATA_FILE
QUEUE_FILE = ROOT / "data" / "missing_queue.json"
NSE_DETAIL_PAGE = f"{core.NSE_HOME}/market-data/issue-information"
EXPLICIT_LOT_KEYS = {
    "lotsize",
    "marketlot",
    "bidlot",
    "bidlotsize",
    "applicationlot",
    "applicationlotsize",
}
MAINBOARD_FALLBACK_KEYS = {
    "minimumbidquantity",
    "minbidquantity",
    "minimumquantity",
}
SAFE_METADATA_KEYS = {
    "issuedetail",
    "issuedetails",
    "issueinfo",
    "ipodetail",
    "ipodetails",
    "details",
    "data",
}
SYMBOL_KEYS = {"symbol", "nsesymbol", "securitysymbol"}


def _normal_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _valid_lot(value: Any) -> int | None:
    lot = core.integer(value)
    if lot is None or not 1 <= lot <= 20_000:
        return None
    return lot


def _collect_explicit_lots(value: Any, out: list[int]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if _normal_key(key) in EXPLICIT_LOT_KEYS:
                lot = _valid_lot(child)
                if lot is not None:
                    out.append(lot)
            if isinstance(child, (dict, list)):
                _collect_explicit_lots(child, out)
    elif isinstance(value, list):
        for child in value:
            _collect_explicit_lots(child, out)


def _safe_metadata_dicts(payload: Any) -> list[dict[str, Any]]:
    """Return root + named metadata dicts, excluding investor/category rows."""
    if not isinstance(payload, dict):
        return []
    rows = [payload]
    for key, value in payload.items():
        if _normal_key(key) in SAFE_METADATA_KEYS and isinstance(value, dict):
            rows.append(value)
    return rows


def extract_lot_size(payload: Any, board: str | None = None) -> int | None:
    """Extract one unambiguous lot size from an NSE issue-detail payload.

    Explicit lot fields are safe on both Mainboard and SME. Generic minimum-bid
    quantity is accepted only for Mainboard, because newer SME minimum
    applications can represent multiple lots.
    """
    explicit: list[int] = []
    _collect_explicit_lots(payload, explicit)
    unique_explicit = sorted(set(explicit))
    if len(unique_explicit) == 1:
        return unique_explicit[0]
    if len(unique_explicit) > 1:
        return None

    if str(board or "").upper() == "SME":
        return None

    fallback: list[int] = []
    for row in _safe_metadata_dicts(payload):
        for key, value in row.items():
            if _normal_key(key) in MAINBOARD_FALLBACK_KEYS:
                lot = _valid_lot(value)
                if lot is not None:
                    fallback.append(lot)
    unique_fallback = sorted(set(fallback))
    return unique_fallback[0] if len(unique_fallback) == 1 else None


def payload_symbol(payload: Any) -> str | None:
    """Read a top-level/safe-metadata response symbol when NSE supplies one."""
    for row in _safe_metadata_dicts(payload):
        for key, value in row.items():
            if _normal_key(key) in SYMBOL_KEYS and value not in (None, ""):
                return str(value).strip().upper()
    return None


def queue_targets(queue_payload: dict[str, Any]) -> set[str]:
    targets: set[str] = set()
    for row in queue_payload.get("queue") or []:
        if not isinstance(row, dict):
            continue
        if row.get("priorityLabel") != "P4 recent history (2y)":
            continue
        if "exchange.lotSize" not in (row.get("missingFields") or []):
            continue
        record_id = str(row.get("id") or "").strip()
        if record_id:
            targets.add(record_id)
    return targets


def apply_lot_size(record: dict[str, Any], payload: Any, *, series: str) -> list[str]:
    """Fill a missing lot size after strict symbol/board validation."""
    if record.get("lotSize") not in (None, ""):
        return []
    expected_symbol = str(record.get("symbol") or "").strip().upper()
    if not expected_symbol:
        return []

    observed_symbol = payload_symbol(payload)
    if observed_symbol and observed_symbol != expected_symbol:
        return []

    lot = extract_lot_size(payload, record.get("board"))
    if lot is None:
        return []

    record["lotSize"] = lot
    changed = ["lotSize"]
    band = record.get("priceBand") if isinstance(record.get("priceBand"), dict) else {}
    cap = core.number((band or {}).get("max"))
    if record.get("minInvestment") in (None, "") and cap:
        record["minInvestment"] = round(float(cap) * lot, 2)
        changed.append("minInvestment")

    checked_at = core.now_ist().isoformat(timespec="seconds")
    source = core.source_stamp("NSE issue detail lot size", NSE_DETAIL_PAGE, "exchange", checked_at)
    sources = [s for s in (record.get("sources") or []) if isinstance(s, dict)]
    sources = [s for s in sources if str(s.get("name") or "") != source["name"]]
    sources.append(source)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    observations = record.setdefault("observations", {})
    nse = dict(observations.get("NSE") or {})
    if nse.get("lotSize") in (None, ""):
        nse["lotSize"] = lot
    nse["lotSeries"] = series
    nse["lotCheckedAt"] = checked_at
    observations["NSE"] = nse
    record["recentNseLotBackfill"] = {
        "source": NSE_DETAIL_PAGE,
        "series": series,
        "lotSize": lot,
        "asOf": checked_at,
    }
    record["validation"] = core.build_validation(record)
    return changed


class NSEIssueDetailClient:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(core.HEADERS)
        self.primed = False
        self.prime_error: Exception | None = None
        self.blocked_error: Exception | None = None

    def _prime(self) -> None:
        if self.primed:
            return
        if self.prime_error is not None:
            raise self.prime_error
        try:
            response = self.s.get(core.NSE_HOME, timeout=20)
            response.raise_for_status()
            self.primed = True
        except Exception as exc:  # remember a WAF/network failure once
            self.prime_error = exc
            raise

    def detail(self, symbol: str, board: str | None = None) -> tuple[Any, str]:
        self._prime()
        series_options = ["SME", "EQ"] if str(board or "").upper() == "SME" else ["EQ"]
        last_error: Exception | None = None
        last_payload: Any = None
        last_series = series_options[-1]
        for series in series_options:
            last_series = series
            try:
                response = self.s.get(
                    f"{core.NSE_API}/ipo-detail",
                    params={"symbol": symbol, "series": series},
                    timeout=25,
                    headers={"Referer": NSE_DETAIL_PAGE},
                )
                if response.status_code in {401, 403, 429}:
                    error = requests.HTTPError(
                        f"NSE issue-detail blocked with HTTP {response.status_code}",
                        response=response,
                    )
                    self.blocked_error = error
                    raise error
                response.raise_for_status()
                payload = response.json()
                last_payload = payload
                if isinstance(payload, dict) and payload:
                    return payload, series
                if isinstance(payload, list) and payload:
                    return payload, series
            except Exception as exc:  # try the alternate supported series
                last_error = exc
                if self.blocked_error is not None:
                    raise
        if last_payload not in (None, {}, []):
            return last_payload, last_series
        if last_error is not None:
            raise last_error
        return {}, last_series


def backfill(payload: dict[str, Any], client: NSEIssueDetailClient, *, limit: int = 250, pause: float = 0.15) -> dict[str, Any]:
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    targets = queue_targets(queue)
    records = [
        row
        for row in (payload.get("ipos") or [])
        if isinstance(row, dict)
        and str(row.get("id") or "") in targets
        and row.get("lotSize") in (None, "")
        and row.get("symbol")
    ]
    records.sort(key=lambda row: str(row.get("openDate") or ""), reverse=True)
    records.sort(key=lambda row: (row.get('nseLotSizeAttempt') or {}).get('checkedAt', ''))
    if limit > 0:
        records = records[:limit]

    attempted = updated = failed = blocked = 0
    updated_ids: list[str] = []
    errors: list[str] = []

    for record in records:
        attempted += 1
        record['nseLotSizeAttempt'] = {'checkedAt': core.now_ist().isoformat(timespec='seconds'), 'status': 'attempted', 'sourceUrl': NSE_DETAIL_PAGE, 'symbol': record.get('symbol')}
        try:
            detail, series = client.detail(str(record.get("symbol")), record.get("board"))
            changed = apply_lot_size(record, detail, series=series)
            record['nseLotSizeAttempt']['status'] = 'updated' if changed else 'no_usable_lot_size'
            if changed:
                updated += 1
                updated_ids.append(str(record.get("id") or ""))
                print(
                    f"NSE lot backfill {record.get('company')}: "
                    f"lotSize={record.get('lotSize')} series={series}"
                )
        except Exception as exc:  # one bad/blocked symbol must not corrupt data
            record['nseLotSizeAttempt'].update(status='source_blocked', error=str(exc)[:250])
            failed += 1
            errors.append(f"{record.get('company')}: {exc}")
            print(f"NSE lot backfill failed {record.get('company')}: {exc}")
            if client.blocked_error is not None or client.prime_error is not None:
                blocked = len(records) - attempted + 1
                print("NSE lot backfill stopped early after persistent NSE access failure")
                break
        if pause > 0:
            time.sleep(pause)

    health = {
        "ok": updated > 0 or failed == 0,
        "targets": len(targets),
        "selected": len(records),
        "attempted": attempted,
        "updated": updated,
        "failed": failed,
        "blockedRemaining": blocked,
        "updatedIds": updated_ids,
        "errors": errors[:10],
        "asOf": core.now_ist().isoformat(timespec="seconds"),
    }
    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["NSE-lot-size-backfill"] = health
    return health


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=250)
    parser.add_argument("--pause", type=float, default=0.15)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    health = backfill(payload, NSEIssueDetailClient(), limit=args.limit, pause=max(0.0, args.pause))
    if health["attempted"]:
        DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "NSE recent lot backfill: "
        f"targets={health['targets']} selected={health['selected']} attempted={health['attempted']} "
        f"updated={health['updated']} failed={health['failed']} blockedRemaining={health['blockedRemaining']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
