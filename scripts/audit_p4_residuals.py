#!/usr/bin/env python3
"""Summarize the full residual P4 recent-history repair backlog.

This audit is read-only. It uses the same lifecycle/source rules as the real
missing-data queue, so its field counts are authoritative for *actionable* P4
work rather than an independent approximation of completeness.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_missing_queue as queue_rules  # noqa: E402

DATA_FILE = ROOT / "data" / "ipos.json"
COUPON_STYLE = re.compile(r"^\d{2,4}[A-Z][A-Z0-9]{1,14}\d{2}$")
MATURITY_SUFFIX = re.compile(r"^[A-Z][A-Z0-9]{2,14}\d{2}$")


def compact(record: dict[str, Any]) -> dict[str, Any]:
    lot_attempt = record.get("nseIssueInfoLotBackfill") or {}
    term_attempt = record.get("nseIssueInfoTermsBackfill") or {}
    return {
        "id": record.get("id"),
        "company": record.get("company"),
        "symbol": record.get("symbol"),
        "exchange": record.get("exchange"),
        "board": record.get("board"),
        "stage": record.get("stage"),
        "openDate": record.get("openDate"),
        "closeDate": record.get("closeDate"),
        "listingDate": record.get("listingDate"),
        "lotAttempt": lot_attempt.get("status") if isinstance(lot_attempt, dict) else None,
        "termAttempt": term_attempt.get("status") if isinstance(term_attempt, dict) else None,
    }


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    today = date.today()

    p4 = [row for row in records if queue_rules.priority_band(row, today)[0] == 4]
    field_counts: Counter[str] = Counter()
    gaps_by_field: dict[str, list[dict[str, Any]]] = defaultdict(list)
    actionable_records = []
    resolved_records = []

    for row in p4:
        rules, _raw, actionable, resolved = queue_rules.missing_partition(row, today)
        if actionable:
            item = compact(row)
            item["actionableMissing"] = actionable
            actionable_records.append(item)
            field_counts.update(actionable)
            for field in actionable:
                gaps_by_field[field].append(compact(row))
        if resolved:
            item = compact(row)
            item["resolvedUnavailable"] = resolved
            resolved_records.append(item)

    lot_gaps = [row for row in p4 if "exchange.lotSize" in dict(queue_rules.expected_rules(row, today)) and not queue_rules.audit.present(row.get("lotSize"))]
    lot_statuses = Counter()
    for row in lot_gaps:
        attempt = row.get("nseIssueInfoLotBackfill") or {}
        status = attempt.get("status") if isinstance(attempt, dict) else None
        lot_statuses[str(status or "unattempted")] += 1

    term_statuses = Counter()
    for row in p4:
        entry_fields = [name for name, predicate in queue_rules.expected_rules(row, today) if not predicate(row)]
        if "exchange.issueSizeCr" not in entry_fields and "exchange.issueComposition" not in entry_fields:
            continue
        attempt = row.get("nseIssueInfoTermsBackfill") or {}
        status = attempt.get("status") if isinstance(attempt, dict) else None
        term_statuses[str(status or "unattempted")] += 1

    suspicious = []
    for row in p4:
        symbol = re.sub(r"[^A-Z0-9]", "", str(row.get("symbol") or "").upper())
        reasons = []
        if COUPON_STYLE.fullmatch(symbol):
            reasons.append("coupon/maturity-style-symbol")
        elif MATURITY_SUFFIX.fullmatch(symbol):
            reasons.append("maturity-suffix-symbol")
        if symbol.endswith("PP1"):
            reasons.append("partly-paid-symbol")
        if reasons:
            item = compact(row)
            item["reasons"] = reasons
            suspicious.append(item)

    report = {
        "asOf": today.isoformat(),
        "p4Records": len(p4),
        "actionableRecordCount": len(actionable_records),
        "actionableFieldGapCounts": dict(field_counts.most_common()),
        "actionableRecords": actionable_records,
        "gapsByField": dict(gaps_by_field),
        "lotAttemptStatusCountsForMissingLots": dict(sorted(lot_statuses.items())),
        "termAttemptStatusCountsForTermGaps": dict(sorted(term_statuses.items())),
        "resolvedUnavailableRecordCount": len(resolved_records),
        "resolvedUnavailableRecords": resolved_records,
        "suspiciousSymbolCount": len(suspicious),
        "suspiciousSymbols": suspicious,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
