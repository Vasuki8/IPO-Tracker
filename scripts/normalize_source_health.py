#!/usr/bin/env python3
"""Normalize source-health semantics after a core IPO refresh.

A successful NSE history request can legitimately return zero rows. That means
"checked, no new rows", not "refresh failed". Actual request/parser failures are
identified from the updater's error list and remain red failures.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"


def normalize_source_health(payload: dict) -> dict:
    meta = payload.setdefault("meta", {})
    health = meta.setdefault("sourceHealth", {})
    history = health.get("NSE-history")
    if not isinstance(history, dict):
        return payload

    errors = [str(item) for item in (meta.get("errors") or [])]
    history_errors = [item for item in errors if item.startswith("NSE history ")]
    records = int(history.get("records") or 0)

    if history_errors:
        history["ok"] = False
        history["status"] = "failed"
        history["error"] = history_errors[-1]
        history.pop("note", None)
        return payload

    history["ok"] = True
    history.pop("error", None)
    if records > 0:
        history["status"] = "refreshed"
        history["note"] = f"{records} rows"
    else:
        history["status"] = "checked"
        history["note"] = "checked · 0 new rows"
    return payload


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    normalize_source_health(payload)
    DATA_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    history = (payload.get("meta") or {}).get("sourceHealth", {}).get("NSE-history", {})
    print(
        "NSE-history health: "
        f"status={history.get('status', 'unknown')} "
        f"records={history.get('records', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
