#!/usr/bin/env python3
"""Retry unresolved recent P4 lot sizes across both NSE equity series.

The primary collector chooses EQ/SME from stored board metadata. Some historical
records have incomplete board labels, so this fallback tries the expected series
first and the alternate series second. A value is accepted only when NSE returns
an exact symbol and canonical issuer identity; debt securities remain rejected;
merges remain fill-only.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_nse_issue_information as base  # noqa: E402
import update_data as core  # noqa: E402

DATA_FILE = core.DATA_FILE
ATTEMPT_KEY = "nseIssueInfoAlternateSeries"


def series_candidates(record: dict) -> list[str]:
    primary = base.series_for(record)
    alternate = "SME" if primary == "EQ" else "EQ"
    return [primary, alternate]


def is_candidate(record: dict, today, history_days: int) -> bool:
    return base.is_candidate(record, today, history_days, retry_days=0)


def mark_attempt(record: dict, *, status: str, tried: list[str], selected: str | None = None, error: str | None = None) -> None:
    record[ATTEMPT_KEY] = {
        "status": status,
        "lastAttemptAt": core.now_ist().isoformat(timespec="seconds"),
        "seriesTried": tried,
        "selectedSeries": selected,
        "error": str(error)[:300] if error else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history-days", type=int, default=730)
    parser.add_argument("--limit", type=int, default=250)
    parser.add_argument("--sleep", type=float, default=0.08)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    today = core.now_ist().date()
    candidates = [row for row in records if is_candidate(row, today, args.history_days)]
    candidates.sort(key=lambda row: str(row.get("openDate") or ""), reverse=True)
    if args.limit > 0:
        candidates = candidates[: args.limit]

    session = requests.Session()
    session.headers.update(core.HEADERS)

    attempted = updated = identity_mismatch = no_lot = failed = alternate_hits = 0
    errors: list[str] = []

    for record in candidates:
        symbol = str(record.get("symbol") or "").strip().upper()
        tried: list[str] = []
        found_identity = False
        found_lot = False
        selected: str | None = None
        last_error: str | None = None
        attempted += 1

        for index, series in enumerate(series_candidates(record)):
            tried.append(series)
            try:
                detail, page_url, _api_url = base.fetch_detail(session, symbol, series)
                if not base.identity_matches(record, detail):
                    continue
                found_identity = True
                terms = base.parse_lot_terms(detail)
                lot = terms.get("lotSize")
                if lot is None:
                    continue
                found_lot = True
                if base.merge_lot(record, detail, page_url=page_url):
                    updated += 1
                    selected = series
                    if index == 1:
                        alternate_hits += 1
                break
            except Exception as exc:
                last_error = str(exc)
            finally:
                if args.sleep > 0:
                    time.sleep(args.sleep)

        if selected is not None:
            mark_attempt(record, status="filled", tried=tried, selected=selected)
        elif found_identity and not found_lot:
            no_lot += 1
            mark_attempt(record, status="no-lot", tried=tried)
        elif last_error and len(tried) == 2:
            failed += 1
            errors.append(f"{record.get('company')} ({symbol}): {last_error}")
            mark_attempt(record, status="error", tried=tried, error=last_error)
        else:
            identity_mismatch += 1
            mark_attempt(record, status="identity-mismatch", tried=tried)

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["NSE-issue-info-alt-series"] = {
        "ok": failed == 0 if attempted else True,
        "candidates": len(candidates),
        "attempted": attempted,
        "updated": updated,
        "alternateSeriesHits": alternate_hits,
        "identityMismatches": identity_mismatch,
        "noLot": no_lot,
        "failed": failed,
        "historyDays": args.history_days,
        "errors": errors[:10],
        "checkedAt": core.now_ist().isoformat(timespec="seconds"),
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "NSE alternate-series lot backfill: "
        f"candidates={len(candidates)}, attempted={attempted}, updated={updated}, "
        f"alternate_hits={alternate_hits}, identity_mismatch={identity_mismatch}, "
        f"no_lot={no_lot}, failed={failed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
