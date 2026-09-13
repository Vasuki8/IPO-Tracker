#!/usr/bin/env python3
"""Summarize the residual P4 recent-history repair backlog.

This audit is intentionally read-only. It makes the remaining two-year gaps
small enough to inspect in Actions logs without dumping the full IPO database.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"

# Audit-only heuristics. These never delete a record; they merely surface symbols
# that deserve security-type verification before being counted as an equity IPO.
COUPON_STYLE = re.compile(r"^\d{2,4}[A-Z][A-Z0-9]{1,14}\d{2}$")
MATURITY_SUFFIX = re.compile(r"^[A-Z][A-Z0-9]{2,14}\d{2}$")


def present(value: Any) -> bool:
    return value not in (None, "", [], {})


def recent_exchange(record: dict[str, Any], today: date) -> bool:
    raw = str(record.get("openDate") or "")[:10]
    try:
        opened = date.fromisoformat(raw)
    except ValueError:
        return False
    if not (today - timedelta(days=730) <= opened <= today + timedelta(days=90)):
        return False
    return all(present(record.get(key)) for key in ("symbol", "board", "exchange", "openDate", "closeDate"))


def has_composition(record: dict[str, Any]) -> bool:
    composition = record.get("issueComposition") or {}
    if not isinstance(composition, dict):
        composition = {}
    return any(
        present(value)
        for value in (
            record.get("freshIssueCr"),
            record.get("ofsCr"),
            composition.get("freshShares"),
            composition.get("ofsShares"),
            composition.get("freshValueCr"),
            composition.get("ofsValueCr"),
        )
    )


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
        "lotAttempt": lot_attempt.get("status") if isinstance(lot_attempt, dict) else None,
        "termAttempt": term_attempt.get("status") if isinstance(term_attempt, dict) else None,
    }


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    today = date.today()
    p4 = [row for row in records if recent_exchange(row, today)]

    price_gaps = [compact(row) for row in p4 if not present(row.get("priceBand"))]
    lot_gaps = [row for row in p4 if not present(row.get("lotSize"))]
    term_gaps = [
        compact(row)
        for row in p4
        if not present(row.get("issueSizeCr")) or not has_composition(row)
    ]

    lot_statuses = Counter()
    lot_identity_mismatch = []
    lot_no_lot = []
    for row in lot_gaps:
        attempt = row.get("nseIssueInfoLotBackfill") or {}
        status = attempt.get("status") if isinstance(attempt, dict) else None
        lot_statuses[str(status or "unattempted")] += 1
        if status == "identity-mismatch":
            lot_identity_mismatch.append(compact(row))
        elif status == "no-lot":
            lot_no_lot.append(compact(row))

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

    offer_fields = (
        "registrar",
        "leadManagers",
        "promoters",
        "objectsOfIssue",
        "financials",
        "promoterShareholding",
    )
    offer_gap_records = []
    for row in p4:
        missing = [field for field in offer_fields if not present(row.get(field))]
        # Only report records that already have document/offer intelligence or
        # are currently represented in the offer-document enrichment universe.
        if missing and (present(row.get("documents")) or present(row.get("offerDocumentExtraction"))):
            item = compact(row)
            item["missingOfferFields"] = missing
            offer_gap_records.append(item)

    report = {
        "asOf": today.isoformat(),
        "p4Records": len(p4),
        "priceGapCount": len(price_gaps),
        "priceGaps": price_gaps,
        "lotGapCount": len(lot_gaps),
        "lotStatusCounts": dict(sorted(lot_statuses.items())),
        "lotIdentityMismatchCount": len(lot_identity_mismatch),
        "lotIdentityMismatch": lot_identity_mismatch,
        "lotNoLotCount": len(lot_no_lot),
        "lotNoLotExamples": lot_no_lot[:40],
        "issueTermGapCount": len(term_gaps),
        "issueTermGaps": term_gaps,
        "suspiciousSymbolCount": len(suspicious),
        "suspiciousSymbols": suspicious,
        "offerGapRecordCount": len(offer_gap_records),
        "offerGapRecords": offer_gap_records,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
