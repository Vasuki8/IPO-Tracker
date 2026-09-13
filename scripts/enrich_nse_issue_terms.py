#!/usr/bin/env python3
"""Backfill recent P4 issue size and Fresh/OFS split from NSE Issue Information.

NSE's official `/api/ipo-detail` payload includes an `Issue Size` narrative in
`issueInfo.dataList`. For many IPOs this states the fresh issue and offer-for-sale
amounts explicitly (for example in Rs million). This collector converts those
amounts to crore and fills only missing fields after exact symbol + issuer
identity validation using the existing NSE issue-information collector.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core
import enrich_nse_issue_information as issue_info

DATA_FILE = core.DATA_FILE
SOURCE_NAME = "NSE issue information"
ATTEMPT_KEY = "nseIssueInfoTermsBackfill"

_AMOUNT = re.compile(
    r"(?:RS\.?|INR|₹)\s*([0-9][0-9,]*(?:\.\d+)?)\s*"
    r"(CRORES?|CR\.?|MILLION|MN|LAKHS?|LACS?|BILLION|BN)?",
    re.I,
)


def to_crore(number: str, unit: str | None) -> float | None:
    try:
        value = float(number.replace(",", ""))
    except (TypeError, ValueError):
        return None
    normalized = re.sub(r"[^A-Z]", "", str(unit or "").upper())
    if normalized in {"CRORE", "CRORES", "CR"}:
        factor = 1.0
    elif normalized in {"MILLION", "MN"}:
        factor = 0.1
    elif normalized in {"LAKH", "LAKHS", "LAC", "LACS"}:
        factor = 0.01
    elif normalized in {"BILLION", "BN"}:
        factor = 100.0
    else:
        # Do not guess the scale of a bare rupee amount in narrative text.
        return None
    result = round(value * factor, 4)
    return result if 0 < result < 1_000_000 else None


def _first_amount(text: str) -> float | None:
    match = _AMOUNT.search(text or "")
    if not match:
        return None
    return to_crore(match.group(1), match.group(2))


def _segment(text: str, start_pattern: str, stop_pattern: str | None = None) -> str:
    start = re.search(start_pattern, text, re.I)
    if not start:
        return ""
    tail = text[start.start():]
    if stop_pattern:
        stop = re.search(stop_pattern, tail[start.end() - start.start():], re.I)
        if stop:
            return tail[: start.end() - start.start() + stop.start()]
    return tail


def parse_issue_terms(payload: dict[str, Any]) -> dict[str, float | None]:
    fields = issue_info.issue_fields(payload)
    raw = fields.get("issue size") or ""
    text = " ".join(raw.replace('\\"', ' ').replace('"', ' ').split())
    if not text:
        return {"freshIssueCr": None, "ofsCr": None, "issueSizeCr": None}

    fresh_segment = _segment(text, r"\bFRESH\s+ISSUE\b", r"\bOFFER\s+FOR\s+SALE\b")
    ofs_segment = _segment(text, r"\bOFFER\s+FOR\s+SALE\b")

    fresh = _first_amount(fresh_segment)
    ofs = _first_amount(ofs_segment)

    # If both legs are disclosed, their sum is the authoritative total. For a
    # clearly single-leg issue, that one disclosed amount is also the total.
    total: float | None = None
    if fresh is not None and ofs is not None:
        total = round(fresh + ofs, 4)
    elif fresh is not None and not re.search(r"\bOFFER\s+FOR\s+SALE\b", text, re.I):
        total = fresh
    elif ofs is not None and not re.search(r"\bFRESH\s+ISSUE\b", text, re.I):
        total = ofs

    # Some payloads state only a direct total, e.g. "Issue Size Rs. 500 crore".
    if total is None and not re.search(r"\bFRESH\s+ISSUE\b|\bOFFER\s+FOR\s+SALE\b", text, re.I):
        total = _first_amount(text)

    return {"freshIssueCr": fresh, "ofsCr": ofs, "issueSizeCr": total}


def has_composition(record: dict[str, Any]) -> bool:
    composition = record.get("issueComposition") or {}
    return any(
        value not in (None, "", [], {})
        for value in (
            record.get("freshIssueCr"),
            record.get("ofsCr"),
            composition.get("freshShares") if isinstance(composition, dict) else None,
            composition.get("ofsShares") if isinstance(composition, dict) else None,
            composition.get("freshValueCr") if isinstance(composition, dict) else None,
            composition.get("ofsValueCr") if isinstance(composition, dict) else None,
        )
    )


def is_candidate(record: dict[str, Any], today: date, history_days: int) -> bool:
    if record.get("issueSizeCr") not in (None, "", [], {}) and has_composition(record):
        return False
    if "NSE" not in str(record.get("exchange") or "").upper():
        return False
    if not str(record.get("symbol") or "").strip():
        return False
    raw = str(record.get("openDate") or "")[:10]
    try:
        opened = date.fromisoformat(raw)
    except ValueError:
        return False
    return today - timedelta(days=max(0, history_days)) <= opened <= today + timedelta(days=90)


def merge_terms(record: dict[str, Any], payload: dict[str, Any], *, page_url: str) -> bool:
    if not issue_info.identity_matches(record, payload):
        return False
    terms = parse_issue_terms(payload)
    changed = False

    if record.get("freshIssueCr") in (None, "", [], {}) and terms["freshIssueCr"] is not None:
        record["freshIssueCr"] = terms["freshIssueCr"]
        changed = True
    if record.get("ofsCr") in (None, "", [], {}) and terms["ofsCr"] is not None:
        record["ofsCr"] = terms["ofsCr"]
        changed = True
    if record.get("issueSizeCr") in (None, "", [], {}) and terms["issueSizeCr"] is not None:
        record["issueSizeCr"] = terms["issueSizeCr"]
        changed = True

    if not changed:
        return False

    sources = list(record.get("sources") or [])
    stamp = core.source_stamp(SOURCE_NAME, page_url, "exchange")
    sources = [s for s in sources if str((s or {}).get("name") or "") != SOURCE_NAME]
    sources.append(stamp)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))
    record.setdefault("observations", {})["NSE-issue-info-terms"] = {
        "symbol": str(record.get("symbol") or "").upper(),
        "freshIssueCr": terms["freshIssueCr"],
        "ofsCr": terms["ofsCr"],
        "issueSizeCr": terms["issueSizeCr"],
        "url": page_url,
    }
    record["validation"] = core.build_validation(record)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history-days", type=int, default=730)
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--sleep", type=float, default=0.08)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    today = core.now_ist().date()
    candidates = [row for row in records if is_candidate(row, today, args.history_days)]
    candidates.sort(key=lambda row: str(row.get("openDate") or ""), reverse=True)
    if args.limit > 0:
        candidates = candidates[: args.limit]

    session = __import__("requests").Session()
    session.headers.update(core.HEADERS)
    attempted = updated = unmatched = no_terms = failed = 0
    errors: list[str] = []

    for record in candidates:
        symbol = str(record.get("symbol") or "").strip().upper()
        series = issue_info.series_for(record)
        page_url = issue_info.issue_page_url(symbol, series)
        attempted += 1
        try:
            detail, page_url, _ = issue_info.fetch_detail(session, symbol, series)
            if not issue_info.identity_matches(record, detail):
                unmatched += 1
            else:
                terms = parse_issue_terms(detail)
                if not any(value is not None for value in terms.values()):
                    no_terms += 1
                elif merge_terms(record, detail, page_url=page_url):
                    updated += 1
            if args.sleep > 0:
                time.sleep(args.sleep)
        except Exception as exc:
            failed += 1
            errors.append(f"{record.get('company')} ({symbol}/{series}): {exc}")

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["NSE-issue-info-terms"] = {
        "ok": failed == 0 if attempted else True,
        "candidates": len(candidates),
        "attempted": attempted,
        "updated": updated,
        "identityMismatches": unmatched,
        "noTerms": no_terms,
        "failed": failed,
        "historyDays": args.history_days,
        "errors": errors[:10],
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "NSE issue-information terms backfill: "
        f"candidates={len(candidates)}, attempted={attempted}, updated={updated}, "
        f"identity_mismatch={unmatched}, no_terms={no_terms}, failed={failed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
