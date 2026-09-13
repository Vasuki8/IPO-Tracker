#!/usr/bin/env python3
"""Remove a tiny evidence-backed set of non-IPO rows from P4.

This is intentionally an exact-identity cleanup, not a heuristic security-symbol
filter. Each entry below has been independently verified against an official
exchange/issuer source. Exact symbol + open date + issuer identity is required,
so valid numeric tickers, year-suffixed equity symbols, and generic PP1 symbols
are never removed by this module.
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

# Evidence retained beside the rule so future maintainers can re-check why the
# row is outside an IPO-only tracker.
VERIFIED_NON_IPO = (
    {
        "company": "Aegis Vopak Terminals Limited",
        "symbol": "AVTL29",
        "openDate": "2025-05-26",
        "reason": "NSE identifies AVTL29 as Series N0, AVTL Floating Rate 2029 debt security.",
        "evidence": "https://nsearchives.nseindia.com/content/circulars/CML72192.pdf",
    },
    {
        "company": "Afcons Infrastructure Limited",
        "symbol": "84AIL28",
        "openDate": "2024-10-25",
        "reason": "NSE identifies the AIL 8.40% 2028 security as debt; AFCONS is the equity IPO symbol.",
        "evidence": "https://nsearchives.nseindia.com/content/circulars/CML70872.pdf",
    },
    {
        "company": "Adani Enterprises Limited",
        "symbol": "ADANIENPP1",
        "openDate": "2026-01-06",
        "reason": "ADANIENPP1 is a partly-paid rights equity security, while 6-Jan-2026 is the opening date of AEL's public NCD issue; the stored row is not an IPO identity.",
        "evidence": "https://nsearchives.nseindia.com/content/circulars/CML72630.pdf",
        "evidence2": "https://www.adani.com/newsroom/media-releases/adani-enterprises-launches-its-3rd-public-issue-of-ncds-of-rs1000-crore",
    },
)


def canonical_company(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()
    for suffix in (" limited", " ltd", " private limited", " pvt ltd"):
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()
            break
    return re.sub(r"\s+", " ", text)


def normalized_symbol(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


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
        text = " ".join(str(source.get(k) or "") for k in ("name", "url", "type")).upper()
        if "NSE" in text or "NSEINDIA.COM" in text:
            return True
    return False


def in_recent_window(record: dict[str, Any], *, today: date, history_days: int) -> bool:
    raw = str(record.get("openDate") or "")[:10]
    try:
        opened = date.fromisoformat(raw)
    except ValueError:
        return False
    return today - timedelta(days=max(history_days, 0)) <= opened <= today + timedelta(days=90)


def matched_rule(record: dict[str, Any]) -> dict[str, Any] | None:
    symbol = normalized_symbol(record.get("symbol"))
    opened = str(record.get("openDate") or "")[:10]
    company = canonical_company(record.get("company"))
    record_id = str(record.get("id") or "").lower()
    for rule in VERIFIED_NON_IPO:
        expected_id = normalized_symbol(rule["symbol"]).lower()
        id_ok = record_id == expected_id or company == canonical_company(rule["company"])
        if (
            id_ok
            and symbol == normalized_symbol(rule["symbol"])
            and opened == rule["openDate"]
            and company == canonical_company(rule["company"])
        ):
            return rule
    return None


def should_prune(record: dict[str, Any], *, today: date, history_days: int = 730) -> bool:
    return bool(
        has_nse_provenance(record)
        and in_recent_window(record, today=today, history_days=history_days)
        and matched_rule(record)
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
        rule = matched_rule(record) or {}
        removed.append(
            {
                "id": record.get("id"),
                "company": record.get("company"),
                "symbol": record.get("symbol"),
                "openDate": record.get("openDate"),
                "reason": rule.get("reason"),
                "evidence": rule.get("evidence"),
                "evidence2": rule.get("evidence2"),
            }
        )

    payload["ipos"] = kept
    meta = payload.setdefault("meta", {})
    meta["recordCount"] = len(kept)
    meta.setdefault("sourceHealth", {})["P4-verified-non-IPO-cleanup"] = {
        "ok": True,
        "historyDays": history_days,
        "checkedOn": today.isoformat(),
        "removedCount": len(removed),
        "removed": removed,
    }
    return payload, removed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-file", type=Path, default=DATA_FILE)
    parser.add_argument("--history-days", type=int, default=730)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = json.loads(args.data_file.read_text(encoding="utf-8"))
    payload, removed = prune_payload(payload, today=date.today(), history_days=args.history_days)
    print(f"P4 verified non-IPO cleanup: removed={len(removed)}")
    for row in removed:
        print(f"  remove {row.get('symbol')} | {row.get('company')} | {row.get('openDate')}")
    if not args.dry_run:
        args.data_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
