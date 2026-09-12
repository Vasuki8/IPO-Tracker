#!/usr/bin/env python3
"""Build a lifecycle-aware priority queue of IPO records with missing fields.

This queue is intentionally actionable rather than a raw list of nulls. Fields are
only expected once the IPO has reached a lifecycle stage where the information
should normally be available from an official source.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import audit_data_completeness as audit

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"
OUTPUT_FILE = ROOT / "data" / "missing_queue.json"
IST = timezone(timedelta(hours=5, minutes=30))


def profile_path(record: dict[str, Any]) -> str | None:
    value = record.get("profilePath")
    if value:
        return str(value)
    return None


def expected_rules(record: dict[str, Any], today: date):
    """Return named predicates that are appropriate for this record's stage."""
    rules: list[tuple[str, Any]] = []
    stage = audit.lifecycle_stage(record, today)
    exchange_stage = audit.present(record.get("openDate")) or audit.present(record.get("symbol"))

    if exchange_stage:
        rules.extend((f"exchange.{name}", predicate) for name, predicate in audit.CORE_EXCHANGE_FIELDS)

    if audit.has_offer_document(record):
        rules.extend((f"offer.{name}", predicate) for name, predicate in audit.OFFER_DOC_FIELDS)

    if stage == "open":
        rules.extend((f"subscription.{name}", predicate) for name, predicate in audit.LIVE_SUBSCRIPTION_FIELDS)

    close_date = audit.parse_iso_date(record.get("closeDate"))
    if close_date and close_date <= today - timedelta(days=14):
        rules.extend(
            [
                ("lifecycle.allotmentDate", lambda r: audit.present(r.get("allotmentDate"))),
                ("lifecycle.listingDate", lambda r: audit.present(r.get("listingDate"))),
            ]
        )

    # Source and validation provenance should exist for every normalized record.
    rules.extend(
        [
            ("provenance.sources", audit.has_sources),
            ("provenance.validation", lambda r: audit.present(r.get("validation"))),
        ]
    )

    if stage == "filing-pipeline":
        rules.append(("provenance.documents", lambda r: audit.present(r.get("documents"))))

    return rules


def priority_band(record: dict[str, Any], today: date) -> tuple[int, str]:
    stage = audit.lifecycle_stage(record, today)
    opened = audit.parse_iso_date(record.get("openDate"))

    if stage == "open":
        return 0, "P0 open IPO"
    if stage == "upcoming":
        return 1, "P1 upcoming IPO"
    if opened and opened >= today - timedelta(days=30):
        return 2, "P2 recent IPO (30d)"
    if stage == "filing-pipeline":
        return 3, "P3 filing pipeline"
    if opened and opened >= today - timedelta(days=730):
        return 4, "P4 recent history (2y)"
    return 5, "P5 historical backfill"


def queue_entry(record: dict[str, Any], today: date) -> dict[str, Any] | None:
    rules = expected_rules(record, today)
    if not rules:
        return None
    missing = [name for name, predicate in rules if not predicate(record)]
    if not missing:
        return None
    priority, label = priority_band(record, today)
    present_count = len(rules) - len(missing)
    completeness = round(present_count / len(rules) * 100, 1) if rules else 100.0
    return {
        "id": record.get("id"),
        "company": record.get("company"),
        "symbol": record.get("symbol"),
        "stage": audit.lifecycle_stage(record, today),
        "openDate": record.get("openDate"),
        "closeDate": record.get("closeDate"),
        "listingDate": record.get("listingDate"),
        "priority": priority,
        "priorityLabel": label,
        "completenessPct": completeness,
        "expectedFieldCount": len(rules),
        "missingFieldCount": len(missing),
        "missingFields": missing,
        "profilePath": profile_path(record),
    }


def build_queue(records: list[dict[str, Any]], today: date) -> list[dict[str, Any]]:
    entries = [entry for record in records if (entry := queue_entry(record, today))]
    entries.sort(
        key=lambda row: (
            int(row["priority"]),
            -int(row["missingFieldCount"]),
            str(row.get("openDate") or "9999-99-99") if int(row["priority"]) <= 1 else "",
            str(row.get("company") or ""),
        )
    )
    return entries


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    now = datetime.now(IST)
    today = now.date()
    queue = build_queue(records, today)

    field_counts: Counter[str] = Counter()
    priority_counts: Counter[str] = Counter()
    for row in queue:
        field_counts.update(row["missingFields"])
        priority_counts.update([row["priorityLabel"]])

    output = {
        "generatedAt": now.isoformat(timespec="seconds"),
        "asOfDate": today.isoformat(),
        "recordCount": len(records),
        "queueCount": len(queue),
        "priorityCounts": dict(priority_counts),
        "fieldGapCounts": dict(field_counts.most_common()),
        "queue": queue[:300],
        "notes": [
            "P0/P1 records are repaired before historical records.",
            "Only lifecycle-appropriate missing fields enter the queue.",
            "Blank values are never guessed; backfill values must come from official sources.",
        ],
    }
    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Missing-data queue: records={len(records)}, queued={len(queue)}, "
        f"p0={priority_counts.get('P0 open IPO', 0)}, p1={priority_counts.get('P1 upcoming IPO', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
