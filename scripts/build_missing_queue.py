#!/usr/bin/env python3
"""Build a lifecycle-aware priority queue of IPO records with missing fields.

This queue is intentionally actionable rather than a raw list of nulls. Fields are
only expected once the IPO has reached a lifecycle/source stage where the
information should normally be recoverable from an official source.

A record may also carry a ``dataAvailability`` resolution for a genuinely blank
field after the official-source paths have been exhausted. Such blanks remain
visible in completeness coverage, but no longer masquerade as actionable work.
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
NON_ACTIONABLE_AVAILABILITY = {
    "source-unavailable",
    "not-applicable",
    "exhausted-official-sources",
}


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
        rules.extend(
            (f"exchange.{name}", predicate)
            for name, predicate in audit.expected_exchange_rules(record, today)
        )

    if audit.has_offer_document(record):
        rules.extend((f"offer.{name}", predicate) for name, predicate in audit.OFFER_DOC_FIELDS)

    if stage == "open":
        rules.extend((f"subscription.{name}", predicate) for name, predicate in audit.LIVE_SUBSCRIPTION_FIELDS)

    close_date = audit.parse_iso_date(record.get("closeDate"))
    if close_date and close_date <= today - timedelta(days=14):
        rules.extend(
            (f"lifecycle.{name}", predicate)
            for name, predicate in audit.MATURED_LIFECYCLE_FIELDS
        )

    rules.extend(
        (f"provenance.{name}", predicate)
        for name, predicate in audit.expected_provenance_rules(record, today)
    )
    return rules


def availability_resolution(record: dict[str, Any], field_name: str) -> dict[str, Any] | None:
    availability = record.get("dataAvailability") or {}
    if not isinstance(availability, dict):
        return None
    value = availability.get(field_name)
    if isinstance(value, str):
        value = {"status": value}
    if not isinstance(value, dict):
        return None
    status = str(value.get("status") or "").strip().lower()
    if status not in NON_ACTIONABLE_AVAILABILITY:
        return None
    return value


def missing_partition(record: dict[str, Any], today: date):
    rules = expected_rules(record, today)
    raw_missing = [name for name, predicate in rules if not predicate(record)]
    resolved = [name for name in raw_missing if availability_resolution(record, name)]
    actionable = [name for name in raw_missing if name not in set(resolved)]
    return rules, raw_missing, actionable, resolved


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
    if opened and opened >= today - timedelta(days=audit.RECENT_EXCHANGE_DAYS):
        return 4, "P4 recent history (2y)"
    return 5, "P5 historical backfill"


def queue_entry(record: dict[str, Any], today: date) -> dict[str, Any] | None:
    rules, raw_missing, missing, resolved = missing_partition(record, today)
    if not rules or not raw_missing or not missing:
        return None
    priority, label = priority_band(record, today)
    present_count = len(rules) - len(raw_missing)
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
        "resolvedUnavailableFieldCount": len(resolved),
        "resolvedUnavailableFields": resolved,
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


def resolved_availability_entries(records: list[dict[str, Any]], today: date) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for record in records:
        _rules, _raw, _actionable, resolved = missing_partition(record, today)
        if not resolved:
            continue
        priority, label = priority_band(record, today)
        details = {}
        for field in resolved:
            details[field] = availability_resolution(record, field) or {}
        out.append(
            {
                "id": record.get("id"),
                "company": record.get("company"),
                "symbol": record.get("symbol"),
                "priority": priority,
                "priorityLabel": label,
                "resolvedFields": resolved,
                "resolutions": details,
                "profilePath": profile_path(record),
            }
        )
    out.sort(key=lambda row: (int(row["priority"]), str(row.get("company") or "")))
    return out


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    now = datetime.now(IST)
    today = now.date()
    queue = build_queue(records, today)
    resolved = resolved_availability_entries(records, today)

    field_counts: Counter[str] = Counter()
    priority_counts: Counter[str] = Counter()
    for row in queue:
        field_counts.update(row["missingFields"])
        priority_counts.update([row["priorityLabel"]])

    resolved_field_counts: Counter[str] = Counter()
    resolved_priority_counts: Counter[str] = Counter()
    for row in resolved:
        resolved_field_counts.update(row["resolvedFields"])
        resolved_priority_counts.update([row["priorityLabel"]])

    output = {
        "generatedAt": now.isoformat(timespec="seconds"),
        "asOfDate": today.isoformat(),
        "recordCount": len(records),
        "queueCount": len(queue),
        "priorityCounts": dict(priority_counts),
        "fieldGapCounts": dict(field_counts.most_common()),
        "resolvedUnavailableRecordCount": len(resolved),
        "resolvedUnavailablePriorityCounts": dict(resolved_priority_counts),
        "resolvedUnavailableFieldCounts": dict(resolved_field_counts.most_common()),
        "queue": queue[:300],
        "resolvedUnavailable": resolved[:300],
        "notes": [
            "P0/P1 records are repaired before historical records.",
            "Only lifecycle- and source-appropriate missing fields enter the actionable queue.",
            "Fields marked source-unavailable/not-applicable/exhausted-official-sources remain blank in coverage but are tracked separately from actionable work.",
            "Older exchange-only records do not require Fresh/OFS composition when the official historical archive does not expose it.",
            "Allotment date is tracked as optional research coverage until a reliable official historical collector exists.",
            "Blank values are never guessed; backfill values must come from official sources.",
        ],
    }
    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Missing-data queue: records={len(records)}, queued={len(queue)}, "
        f"resolved-unavailable={len(resolved)}, "
        f"p0={priority_counts.get('P0 open IPO', 0)}, p1={priority_counts.get('P1 upcoming IPO', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
