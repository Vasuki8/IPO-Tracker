#!/usr/bin/env python3
"""Summarize the full residual P4 recent-history repair backlog.

This audit is read-only. It uses the same lifecycle/source rules as the real
missing-data queue, so its field counts are authoritative for *actionable* P4
work rather than an independent approximation of completeness.

The report deliberately separates observations from decisions. Structural
flags (withdrawn/postponed/non-equity/partly-paid) are *classification
candidates* only; records are removed from the actionable queue only after a
source-backed ``dataAvailability`` resolution is written to the dataset.
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
NON_EQUITY_WORDS = ("debt", "ncd", "bond", "debenture", "preference share", "preference shares")
WITHDRAWN_WORDS = ("withdrawn", "withdraw", "cancelled", "canceled")
POSTPONED_WORDS = ("postponed", "deferred", "rescheduled")


def _attempt_status(record: dict[str, Any], key: str) -> str | None:
    attempt = record.get(key) or {}
    return attempt.get("status") if isinstance(attempt, dict) else None


def compact(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record.get("id"),
        "company": record.get("company"),
        "symbol": record.get("symbol"),
        "exchange": record.get("exchange"),
        "board": record.get("board"),
        "stage": record.get("stage"),
        "status": record.get("status"),
        "issueType": record.get("issueType"),
        "openDate": record.get("openDate"),
        "closeDate": record.get("closeDate"),
        "listingDate": record.get("listingDate"),
        "nseLotAttempt": _attempt_status(record, "nseIssueInfoLotBackfill"),
        "bseLotAttempt": _attempt_status(record, "p4LotSizeBackfill"),
        "termAttempt": _attempt_status(record, "nseIssueInfoTermsBackfill"),
    }


def structural_flags(record: dict[str, Any]) -> list[str]:
    """Return evidence hints that deserve manual/source-backed classification."""
    symbol = re.sub(r"[^A-Z0-9]", "", str(record.get("symbol") or "").upper())
    searchable = " ".join(
        str(record.get(key) or "")
        for key in (
            "stage",
            "status",
            "issueStatus",
            "issueType",
            "securityType",
            "instrument",
            "company",
            "notes",
        )
    ).lower()

    flags: list[str] = []
    if any(word in searchable for word in WITHDRAWN_WORDS):
        flags.append("withdrawn-or-cancelled")
    if any(word in searchable for word in POSTPONED_WORDS):
        flags.append("postponed-or-deferred")
    if any(word in searchable for word in NON_EQUITY_WORDS):
        flags.append("non-equity-instrument")
    if symbol.endswith("PP1"):
        flags.append("partly-paid-symbol")
    if COUPON_STYLE.fullmatch(symbol):
        flags.append("coupon/maturity-style-symbol")
    elif MATURITY_SUFFIX.fullmatch(symbol):
        flags.append("maturity-suffix-symbol")
    return flags


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    today = date.today()

    p4 = [row for row in records if queue_rules.priority_band(row, today)[0] == 4]
    field_counts: Counter[str] = Counter()
    gaps_by_field: dict[str, list[dict[str, Any]]] = defaultdict(list)
    actionable_records: list[dict[str, Any]] = []
    resolved_records: list[dict[str, Any]] = []

    exchange_counts: Counter[str] = Counter()
    board_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    classification_flag_counts: Counter[str] = Counter()
    classification_candidates: list[dict[str, Any]] = []

    for row in p4:
        _rules, _raw, actionable, resolved = queue_rules.missing_partition(row, today)
        if actionable:
            item = compact(row)
            item["actionableMissing"] = actionable
            flags = structural_flags(row)
            if flags:
                item["classificationFlags"] = flags
                classification_candidates.append(item)
                classification_flag_counts.update(flags)
            actionable_records.append(item)
            field_counts.update(actionable)
            exchange_counts.update([str(row.get("exchange") or "unknown")])
            board_counts.update([str(row.get("board") or "unknown")])
            stage_counts.update([str(row.get("stage") or "unknown")])
            for field in actionable:
                gaps_by_field[field].append(compact(row))
        if resolved:
            item = compact(row)
            item["resolvedUnavailable"] = resolved
            item["resolutions"] = {
                field: queue_rules.availability_resolution(row, field) or {}
                for field in resolved
            }
            resolved_records.append(item)

    lot_gaps = [
        row
        for row in p4
        if "exchange.lotSize" in dict(queue_rules.expected_rules(row, today))
        and not queue_rules.audit.present(row.get("lotSize"))
        and not queue_rules.availability_resolution(row, "exchange.lotSize")
    ]
    nse_lot_statuses: Counter[str] = Counter()
    bse_lot_statuses: Counter[str] = Counter()
    lot_exchange_counts: Counter[str] = Counter()
    lot_board_counts: Counter[str] = Counter()
    for row in lot_gaps:
        nse_lot_statuses[str(_attempt_status(row, "nseIssueInfoLotBackfill") or "unattempted")] += 1
        bse_lot_statuses[str(_attempt_status(row, "p4LotSizeBackfill") or "unattempted")] += 1
        lot_exchange_counts[str(row.get("exchange") or "unknown")] += 1
        lot_board_counts[str(row.get("board") or "unknown")] += 1

    term_statuses: Counter[str] = Counter()
    term_gap_records = 0
    for row in p4:
        _rules, _raw, actionable, _resolved = queue_rules.missing_partition(row, today)
        if "exchange.issueSizeCr" not in actionable and "exchange.issueComposition" not in actionable:
            continue
        term_gap_records += 1
        term_statuses[str(_attempt_status(row, "nseIssueInfoTermsBackfill") or "unattempted")] += 1

    report = {
        "asOf": today.isoformat(),
        "p4Records": len(p4),
        "actionableRecordCount": len(actionable_records),
        "actionableFieldGapCounts": dict(field_counts.most_common()),
        "actionableRecordDistribution": {
            "exchange": dict(exchange_counts.most_common()),
            "board": dict(board_counts.most_common()),
            "stage": dict(stage_counts.most_common()),
        },
        "actionableRecords": actionable_records,
        "gapsByField": dict(gaps_by_field),
        "lotGapRecordCount": len(lot_gaps),
        "lotAttemptStatusCountsForMissingLots": {
            "nseIssueInfoLotBackfill": dict(sorted(nse_lot_statuses.items())),
            "p4LotSizeBackfill": dict(sorted(bse_lot_statuses.items())),
        },
        "lotGapDistribution": {
            "exchange": dict(lot_exchange_counts.most_common()),
            "board": dict(lot_board_counts.most_common()),
        },
        "termGapRecordCount": term_gap_records,
        "termAttemptStatusCountsForTermGaps": dict(sorted(term_statuses.items())),
        "classificationCandidateCount": len(classification_candidates),
        "classificationFlagCounts": dict(classification_flag_counts.most_common()),
        "classificationCandidates": classification_candidates,
        "resolvedUnavailableRecordCount": len(resolved_records),
        "resolvedUnavailableRecords": resolved_records,
        "notes": [
            "Classification flags are diagnostic hints only and never suppress a queue gap by themselves.",
            "A blank becomes non-actionable only through a source-backed dataAvailability resolution accepted by build_missing_queue.py.",
            "NSE and BSE lot-attempt status counts are reported separately so endpoint/matcher failures are distinguishable from genuinely unattempted records.",
        ],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
