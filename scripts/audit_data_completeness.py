#!/usr/bin/env python3
"""Audit IPO dataset completeness using lifecycle-specific expectations.

Outputs:
- data/completeness.json: machine-readable coverage, gap counts, and examples
- docs/DATA_QUALITY.md: concise human-readable report

A DRHP-stage company is not penalized for having no price band or listing date
because those may not be disclosed yet. Once an issue reaches the exchange stage,
missing core terms are treated as actionable collector/backfill gaps.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"
OUTPUT_FILE = ROOT / "data" / "completeness.json"
REPORT_FILE = ROOT / "docs" / "DATA_QUALITY.md"
IST = timezone(timedelta(hours=5, minutes=30))

FILING_STAGES = {"drhp", "udrhp", "rhp", "prospectus"}
OFFER_DOC_TYPES = ("RHP", "RED HERRING", "PROSPECTUS", "ABRIDGED PROSPECTUS")


def present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"—", "-", "na", "n/a", "null"}
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def nested(record: dict[str, Any], path: str) -> Any:
    value: Any = record
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def any_present(record: dict[str, Any], paths: tuple[str, ...]) -> bool:
    return any(present(nested(record, path)) for path in paths)


def parse_iso_date(value: Any) -> date | None:
    if not present(value):
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def lifecycle_stage(record: dict[str, Any], today: date) -> str:
    opened = parse_iso_date(record.get("openDate"))
    closed = parse_iso_date(record.get("closeDate"))
    listed = parse_iso_date(record.get("listingDate"))
    lifecycle = str(nested(record, "lifecycle.stage") or "").lower()

    if listed and listed <= today:
        return "listed"
    if opened and closed and opened <= today <= closed:
        return "open"
    if opened and opened > today:
        return "upcoming"
    if closed and closed < today:
        return "closed"
    if lifecycle in FILING_STAGES or record.get("documents"):
        return "filing-pipeline"
    return "unknown"


def has_offer_document(record: dict[str, Any]) -> bool:
    for document in record.get("documents") or []:
        doc_type = str((document or {}).get("type") or "").upper()
        if any(token in doc_type for token in OFFER_DOC_TYPES):
            return True
    extraction = record.get("offerDocumentExtraction") or {}
    return present(extraction.get("documentUrl")) or extraction.get("status") == "extracted"


def has_issue_composition(record: dict[str, Any]) -> bool:
    return any_present(
        record,
        (
            "freshIssueCr",
            "ofsCr",
            "issueComposition.freshShares",
            "issueComposition.ofsShares",
            "issueComposition.freshValueCr",
            "issueComposition.ofsValueCr",
        ),
    )


def has_price_band(record: dict[str, Any]) -> bool:
    return any_present(record, ("priceBand.min", "priceBand.max"))


def has_financials(record: dict[str, Any]) -> bool:
    periods = nested(record, "financials.periods")
    return isinstance(periods, list) and any(
        isinstance(row, dict)
        and any(
            present(row.get(key))
            for key in ("revenueCr", "ebitdaCr", "patCr", "netWorthCr", "eps", "ronwPct", "roePct")
        )
        for row in periods
    )


def has_sources(record: dict[str, Any]) -> bool:
    return present(record.get("sources")) or present(record.get("source"))


def has_subscription_category(record: dict[str, Any], key: str) -> bool:
    return present(nested(record, f"subscription.{key}"))


FieldRule = tuple[str, Callable[[dict[str, Any]], bool]]

CORE_EXCHANGE_FIELDS: list[FieldRule] = [
    ("symbol", lambda r: present(r.get("symbol"))),
    ("board", lambda r: present(r.get("board"))),
    ("exchange", lambda r: present(r.get("exchange"))),
    ("openDate", lambda r: present(r.get("openDate"))),
    ("closeDate", lambda r: present(r.get("closeDate"))),
    ("priceBand", has_price_band),
    ("lotSize", lambda r: present(r.get("lotSize"))),
    ("issueSizeCr", lambda r: present(r.get("issueSizeCr"))),
    ("issueComposition", has_issue_composition),
]

OFFER_DOC_FIELDS: list[FieldRule] = [
    ("registrar", lambda r: present(r.get("registrar"))),
    ("leadManagers", lambda r: present(r.get("leadManagers"))),
    ("promoters", lambda r: present(r.get("promoters"))),
    ("objectsOfIssue", lambda r: present(r.get("objectsOfIssue"))),
    ("financials", has_financials),
    ("promoterShareholding", lambda r: present(nested(r, "shareholding.promoterPreIssuePct"))),
]

LIVE_SUBSCRIPTION_FIELDS: list[FieldRule] = [
    ("qib", lambda r: has_subscription_category(r, "qib")),
    ("nii", lambda r: has_subscription_category(r, "nii")),
    ("retail", lambda r: has_subscription_category(r, "retail")),
    ("total", lambda r: has_subscription_category(r, "total")),
]

PROVENANCE_FIELDS: list[FieldRule] = [
    ("sources", has_sources),
    ("validation", lambda r: present(r.get("validation"))),
    ("documents", lambda r: present(r.get("documents"))),
]


def coverage(records: list[dict[str, Any]], rules: list[FieldRule]) -> dict[str, dict[str, Any]]:
    total = len(records)
    result: dict[str, dict[str, Any]] = {}
    for name, predicate in rules:
        count = sum(1 for record in records if predicate(record))
        result[name] = {
            "present": count,
            "expected": total,
            "missing": total - count,
            "pct": round((count / total * 100) if total else 100.0, 1),
        }
    return result


def record_gap_count(record: dict[str, Any], rules: list[FieldRule]) -> int:
    return sum(1 for _, predicate in rules if not predicate(record))


def examples_for_gap(
    records: list[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
    limit: int = 15,
) -> list[dict[str, Any]]:
    missing = [record for record in records if not predicate(record)]
    missing.sort(
        key=lambda r: (
            str(r.get("openDate") or ""),
            str(r.get("listingDate") or ""),
            str(r.get("company") or ""),
        ),
        reverse=True,
    )
    return [
        {
            "id": record.get("id"),
            "company": record.get("company"),
            "openDate": record.get("openDate"),
            "stage": record.get("_auditStage"),
        }
        for record in missing[:limit]
    ]


def group_gap_examples(records: list[dict[str, Any]], rules: list[FieldRule]) -> dict[str, list[dict[str, Any]]]:
    return {name: examples_for_gap(records, predicate) for name, predicate in rules}


def average_group_score(records: list[dict[str, Any]], rules: list[FieldRule]) -> float:
    if not records or not rules:
        return 100.0
    possible = len(records) * len(rules)
    complete = sum(len(rules) - record_gap_count(record, rules) for record in records)
    return round(complete / possible * 100, 1)


def markdown_table(rows: dict[str, dict[str, Any]]) -> str:
    lines = ["| Field | Present | Missing | Coverage |", "| --- | ---: | ---: | ---: |"]
    for field, stat in rows.items():
        lines.append(f"| {field} | {stat['present']:,} | {stat['missing']:,} | {stat['pct']:.1f}% |")
    return "\n".join(lines)


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [record for record in payload.get("ipos") or [] if isinstance(record, dict)]
    today = datetime.now(IST).date()

    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        audit_stage = lifecycle_stage(record, today)
        record["_auditStage"] = audit_stage
        by_stage[audit_stage].append(record)

    exchange_records = [r for r in records if present(r.get("openDate")) or present(r.get("symbol"))]
    recent_cutoff = today - timedelta(days=730)
    recent_exchange = [
        r for r in exchange_records
        if (parse_iso_date(r.get("openDate")) or date.min) >= recent_cutoff
    ]
    historical_exchange = [
        r for r in exchange_records
        if (parse_iso_date(r.get("openDate")) or date.min) < recent_cutoff
    ]
    offer_doc_records = [r for r in records if has_offer_document(r)]
    open_records = by_stage.get("open", [])

    matured_closed = [
        r for r in exchange_records
        if parse_iso_date(r.get("closeDate")) is not None
        and parse_iso_date(r.get("closeDate")) <= today - timedelta(days=14)
    ]
    lifecycle_rules: list[FieldRule] = [
        ("allotmentDate", lambda r: present(r.get("allotmentDate"))),
        ("listingDate", lambda r: present(r.get("listingDate"))),
    ]

    segments = {
        "allRecords": records,
        "exchangeStage": exchange_records,
        "recentExchange2Y": recent_exchange,
        "historicalExchange": historical_exchange,
        "offerDocumentEligible": offer_doc_records,
        "openNow": open_records,
        "maturedClosed": matured_closed,
    }

    audit = {
        "generatedAt": datetime.now(IST).isoformat(timespec="seconds"),
        "asOfDate": today.isoformat(),
        "recordCount": len(records),
        "stageCounts": dict(sorted(Counter(r["_auditStage"] for r in records).items())),
        "segmentCounts": {name: len(rows) for name, rows in segments.items()},
        "scores": {
            "exchangeStage": average_group_score(exchange_records, CORE_EXCHANGE_FIELDS),
            "recentExchange2Y": average_group_score(recent_exchange, CORE_EXCHANGE_FIELDS),
            "offerDocumentEligible": average_group_score(offer_doc_records, OFFER_DOC_FIELDS),
            "openSubscription": average_group_score(open_records, LIVE_SUBSCRIPTION_FIELDS),
            "maturedLifecycle": average_group_score(matured_closed, lifecycle_rules),
            "provenance": average_group_score(records, PROVENANCE_FIELDS),
        },
        "coverage": {
            "exchangeStage": coverage(exchange_records, CORE_EXCHANGE_FIELDS),
            "recentExchange2Y": coverage(recent_exchange, CORE_EXCHANGE_FIELDS),
            "historicalExchange": coverage(historical_exchange, CORE_EXCHANGE_FIELDS),
            "offerDocumentEligible": coverage(offer_doc_records, OFFER_DOC_FIELDS),
            "openSubscription": coverage(open_records, LIVE_SUBSCRIPTION_FIELDS),
            "maturedLifecycle": coverage(matured_closed, lifecycle_rules),
            "provenance": coverage(records, PROVENANCE_FIELDS),
        },
        "gapExamples": {
            "recentExchange2Y": group_gap_examples(recent_exchange, CORE_EXCHANGE_FIELDS),
            "offerDocumentEligible": group_gap_examples(offer_doc_records, OFFER_DOC_FIELDS),
            "openSubscription": group_gap_examples(open_records, LIVE_SUBSCRIPTION_FIELDS),
            "maturedLifecycle": group_gap_examples(matured_closed, lifecycle_rules),
        },
        "notes": [
            "Coverage uses lifecycle-specific denominators; pre-exchange DRHP records are not penalized for undisclosed exchange terms.",
            "recentExchange2Y isolates current collector quality from sparse older historical records.",
            "offerDocumentEligible only expects structured research fields when an RHP/Prospectus-like official document is attached.",
            "openSubscription only expects category-wise subscription data while bidding is currently open.",
            "maturedLifecycle only flags allotment/listing dates when the IPO closed at least 14 days ago.",
        ],
    }

    for record in records:
        record.pop("_auditStage", None)

    OUTPUT_FILE.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    score = audit["scores"]
    report = "# IPO Tracker Data Quality\n\n"
    report += f"Generated: **{audit['generatedAt']}**  \n"
    report += f"Records audited: **{len(records):,}**\n\n"
    report += "## Completeness scores\n\n"
    report += "| Area | Score | Records in denominator |\n| --- | ---: | ---: |\n"
    report += f"| Core exchange terms | {score['exchangeStage']:.1f}% | {len(exchange_records):,} |\n"
    report += f"| Recent exchange terms (2Y) | {score['recentExchange2Y']:.1f}% | {len(recent_exchange):,} |\n"
    report += f"| Offer-document intelligence | {score['offerDocumentEligible']:.1f}% | {len(offer_doc_records):,} |\n"
    report += f"| Live subscription categories | {score['openSubscription']:.1f}% | {len(open_records):,} |\n"
    report += f"| Matured lifecycle dates | {score['maturedLifecycle']:.1f}% | {len(matured_closed):,} |\n"
    report += f"| Source/provenance trail | {score['provenance']:.1f}% | {len(records):,} |\n\n"

    report += "## Core exchange fields\n\n" + markdown_table(audit["coverage"]["exchangeStage"]) + "\n\n"
    report += "## Recent exchange fields — last 2 years\n\n" + markdown_table(audit["coverage"]["recentExchange2Y"]) + "\n\n"
    report += "## Offer-document fields\n\n" + markdown_table(audit["coverage"]["offerDocumentEligible"]) + "\n\n"
    report += "## Open IPO subscription fields\n\n" + markdown_table(audit["coverage"]["openSubscription"]) + "\n\n"
    report += "## Matured lifecycle fields\n\n" + markdown_table(audit["coverage"]["maturedLifecycle"]) + "\n\n"
    report += "## Interpretation\n\n"
    report += "- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.\n"
    report += "- **Collector gap** means a field is expected for that lifecycle stage but remains missing.\n"
    report += "- Recent exchange coverage is the best measure of whether the live collectors are working well today.\n"
    report += "- Historical coverage is tracked separately because older exchange/SEBI pages expose fewer structured fields.\n"

    REPORT_FILE.write_text(report, encoding="utf-8")
    print(json.dumps(audit["scores"], indent=2))
    print(f"Wrote {OUTPUT_FILE.relative_to(ROOT)} and {REPORT_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
