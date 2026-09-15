"""Expose performance coverage and dated observations without implied prices.

The report is a generated machine artifact, so it is written as compact JSON.
Every listed IPO remains represented; null fields are omitted from each row while
aggregate counters retain the full coverage denominators.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from validate_data import numeric

ROOT = Path(__file__).resolve().parents[1]


def performance_row(record):
    performance = record.get("performance") or {}
    latest = performance.get("latest") or {}
    price = (record.get("listing") or {}).get("issuePrice")
    row = {
        "id": record["id"],
        "company": record.get("company"),
        "symbol": record.get("symbol"),
        "listingDate": record["listingDate"],
    }
    if numeric(price) and price > 0:
        row["issuePrice"] = price
    if latest:
        row["latest"] = latest
    if performance.get("returnSinceIssuePct") is not None:
        row["returnSinceIssuePct"] = performance.get("returnSinceIssuePct")
    if performance.get("benchmarkExcessReturnPct") is not None:
        row["benchmarkExcessReturnPct"] = performance.get("benchmarkExcessReturnPct")
    status = performance.get("lastAttemptStatus")
    if status and status != "not_collected":
        row["lastAttemptStatus"] = status
    return row


def build_report(payload, *, generated_at=None):
    rows = []
    for record in payload.get("ipos", []):
        if not record.get("listingDate") or record.get("issueEventType"):
            continue
        rows.append(performance_row(record))
    return {
        "formatVersion": 2,
        "generatedAt": generated_at or datetime.now(timezone.utc).isoformat(),
        "returnBasis": "Unadjusted price returns; excludes dividends and corporate-action adjustments",
        "listedRecords": len(rows),
        "withFinalIssuePrice": sum(row.get("issuePrice") is not None for row in rows),
        "withPriceObservation": sum(row.get("latest") is not None for row in rows),
        "withBenchmarkComparison": sum(row.get("benchmarkExcessReturnPct") is not None for row in rows),
        "records": rows,
    }


def main():
    payload = json.loads((ROOT / "data/ipos.json").read_text(encoding="utf-8"))
    report = build_report(payload)
    (ROOT / "data/performance_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in report.items() if key != "records"}))


if __name__ == "__main__":
    main()
