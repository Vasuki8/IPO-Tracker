#!/usr/bin/env python3
"""Remove legacy NSE debt public-issue rows that predate the P4 history guard.

The normal P4 guard prevents new debt/NCD rows from entering through NSE's broad
`public-past-issues` feed. A few older rows can nevertheless remain when that
exact issue is no longer returned by the current 730-day reconciliation window.

This cleanup is intentionally narrow:
- symbol must match NSE's coupon + issuer + maturity debt convention;
- the stored record must have explicit NSE provenance;
- only records in the recent P4 history window are eligible;
- ordinary numeric equity tickers such as 3MINDIA and 360ONE do not match;
- no issuer-name-only deletion is ever performed.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"

# Examples: 935IIFL33, 790IHFL27, 975SCL35, 727NGEL36.
# Require both a 3/4 digit coupon prefix and a 2 digit maturity suffix.
DEBT_SYMBOL = re.compile(r"^\d{3,4}[A-Z][A-Z0-9]{1,14}\d{2}$")


def normalized_symbol(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def has_debt_symbol(record: dict[str, Any]) -> bool:
    symbol = normalized_symbol(record.get("symbol"))
    return bool(symbol and DEBT_SYMBOL.fullmatch(symbol))


def has_nse_provenance(record: dict[str, Any]) -> bool:
    exchange = str(record.get("exchange") or "").upper()
    if "NSE" in exchange:
        return True

    observations = record.get("observations") or {}
    if isinstance(observations, dict) and any("NSE" in str(key).upper() for key in observations):
        return True

    for source in record.get("sources") or []:
        if not isinstance(source, dict):
            continue
        text = " ".join(
            str(source.get(key) or "")
            for key in ("name", "url", "type")
        ).upper()
        if "NSE" in text or "NSEINDIA.COM" in text:
            return True
    return False


def in_recent_window(record: dict[str, Any], *, today: date, history_days: int) -> bool:
    raw = str(record.get("openDate") or "")[:10]
    try:
        opened = date.fromisoformat(raw)
    except ValueError:
        return False
    return today - timedelta(days=max(0, history_days)) <= opened <= today + timedelta(days=90)


def should_prune(record: dict[str, Any], *, today: date, history_days: int = 730) -> bool:
    return (
        has_debt_symbol(record)
        and has_nse_provenance(record)
        and in_recent_window(record, today=today, history_days=history_days)
    )


def prune_payload(
    payload: dict[str, Any],
    *,
    today: date,
    history_days: int = 730,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []

    for record in records:
        if not should_prune(record, today=today, history_days=history_days):
            kept.append(record)
            continue
        removed.append(
            {
                "id": record.get("id"),
                "company": record.get("company"),
                "symbol": record.get("symbol"),
                "openDate": record.get("openDate"),
                "exchange": record.get("exchange"),
            }
        )

    payload["ipos"] = kept
    meta = payload.setdefault("meta", {})
    meta["recordCount"] = len(kept)
    meta.setdefault("sourceHealth", {})["P4-legacy-debt-symbol-cleanup"] = {
        "ok": True,
        "historyDays": history_days,
        "removedCount": len(removed),
        "removed": removed[:50],
        "checkedOn": today.isoformat(),
    }
    return payload, removed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-file", type=Path, default=DATA_FILE)
    parser.add_argument("--history-days", type=int, default=730)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = json.loads(args.data_file.read_text(encoding="utf-8"))
    payload, removed = prune_payload(
        payload,
        today=date.today(),
        history_days=args.history_days,
    )

    print(f"P4 legacy debt-symbol cleanup: removed={len(removed)}")
    for row in removed:
        print(
            "  remove "
            f"{row.get('symbol')} | {row.get('company')} | {row.get('openDate')}"
        )

    if not args.dry_run:
        args.data_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
