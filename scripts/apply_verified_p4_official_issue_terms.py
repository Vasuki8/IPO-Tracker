#!/usr/bin/env python3
"""Apply deterministic P4 issue-size/composition facts from official SEBI sources.

This registry is intentionally separate from the older verified-term bridge because
that bridge contains third-party references. Every entry here points only to an
official SEBI filing/disclosure, uses exact record identity guards and is fill-only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402

DATA_FILE = core.DATA_FILE
SOURCE_HEALTH_KEY = "verified-p4-official-issue-terms"


def _entry(
    company: str,
    symbol: str,
    open_date: str,
    source_name: str,
    source_url: str,
    *,
    issue_size_cr: float,
    fresh_issue_cr: float | None = None,
    ofs_cr: float | None = None,
) -> dict[str, Any]:
    return {
        "company": company,
        "symbol": symbol,
        "openDate": open_date,
        "sourceName": source_name,
        "sourceUrl": source_url,
        "issueSizeCr": issue_size_cr,
        "freshIssueCr": fresh_issue_cr,
        "ofsCr": ofs_cr,
    }


VERIFIED_P4_OFFICIAL_ISSUE_TERMS: dict[str, dict[str, Any]] = {
    "carraro": _entry(
        "Carraro India Limited",
        "CARRARO",
        "2024-12-20",
        "SEBI Carraro India final Prospectus",
        "https://www.sebi.gov.in/filings/public-issues/dec-2024/carraro-india-limited-prospectus_91769.html",
        issue_size_cr=1250.0,
        fresh_issue_cr=0.0,
        ofs_cr=1250.0,
    ),
    "mamata": _entry(
        "Mamata Machinery Limited",
        "MAMATA",
        "2024-12-19",
        "SEBI Mamata Machinery final Prospectus",
        "https://www.sebi.gov.in/filings/public-issues/dec-2024/mamata-machinery-limited-prospectus_90144.html",
        issue_size_cr=179.349,
        fresh_issue_cr=0.0,
        ofs_cr=179.349,
    ),
    "senores": _entry(
        "Senores Pharmaceuticals Limited",
        "SENORES",
        "2024-12-20",
        "SEBI Senores Pharmaceuticals final Prospectus",
        "https://www.sebi.gov.in/filings/public-issues/dec-2024/senores-pharmaceuticals-limited-prospectus_90178.html",
        issue_size_cr=582.11,
        fresh_issue_cr=500.0,
        ofs_cr=82.11,
    ),
    "unimech": _entry(
        "Unimech Aerospace and Manufacturing Limited",
        "UNIMECH",
        "2024-12-23",
        "SEBI Unimech Aerospace and Manufacturing final Prospectus",
        "https://www.sebi.gov.in/filings/public-issues/dec-2024/unimech-aerospace-and-manufacturing-limited-prospectus_90272.html",
        issue_size_cr=500.0,
        fresh_issue_cr=250.0,
        ofs_cr=250.0,
    ),
    "sailife": _entry(
        "Sai Life Sciences Limited",
        "SAILIFE",
        "2024-12-11",
        "SEBI Sai Life Sciences final Prospectus",
        "https://www.sebi.gov.in/filings/public-issues/dec-2024/sai-life-sciences-limited-prospectus_91998.html",
        issue_size_cr=3042.62,
    ),
    "sanathan": _entry(
        "Sanathan Textiles Limited",
        "SANATHAN",
        "2024-12-19",
        "SEBI Sanathan Textiles final Prospectus",
        "https://www.sebi.gov.in/filings/public-issues/dec-2024/sanathan-textiles-limited-prospectus_90156.html",
        issue_size_cr=550.0,
    ),
    "transraill": _entry(
        "Transrail Lighting Limited",
        "TRANSRAILL",
        "2024-12-19",
        "SEBI-hosted BRLM disclosure citing Transrail Prospectus",
        "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1752651007576_865.pdf",
        issue_size_cr=838.912,
    ),
}


def identity_matches(record_id: str, record: dict[str, Any], entry: dict[str, Any]) -> bool:
    if record_id not in VERIFIED_P4_OFFICIAL_ISSUE_TERMS:
        return False
    if str(record.get("id") or "") != record_id:
        return False
    if str(record.get("symbol") or "").upper() != str(entry.get("symbol") or "").upper():
        return False
    if core.iso_date(record.get("openDate")) != str(entry.get("openDate") or ""):
        return False
    return core.canonical_company(record.get("company")) == core.canonical_company(entry.get("company"))


def apply_entry(record_id: str, record: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    if not identity_matches(record_id, record, entry):
        return []

    total = core.number(entry.get("issueSizeCr"))
    fresh = core.number(entry.get("freshIssueCr"))
    ofs = core.number(entry.get("ofsCr"))
    if total is None or total <= 0:
        return []
    if fresh is not None and fresh < 0:
        return []
    if ofs is not None and ofs < 0:
        return []
    has_full_composition = fresh is not None and ofs is not None
    if has_full_composition and abs((fresh + ofs) - total) > 0.05:
        return []

    changed: list[str] = []
    if record.get("issueSizeCr") in (None, ""):
        record["issueSizeCr"] = round(total, 4)
        changed.append("issueSizeCr")

    if has_full_composition:
        if record.get("freshIssueCr") in (None, ""):
            record["freshIssueCr"] = round(fresh, 4)
            changed.append("freshIssueCr")
        if record.get("ofsCr") in (None, ""):
            record["ofsCr"] = round(ofs, 4)
            changed.append("ofsCr")
        if record.get("issueComposition") in (None, {}, []):
            record["issueComposition"] = {
                "freshIssueCr": round(fresh, 4),
                "ofsCr": round(ofs, 4),
                "totalIssueSizeCr": round(total, 4),
                "sourceBasis": "official SEBI final offer terms",
            }
            changed.append("issueComposition")

    if not changed:
        return []

    source = core.source_stamp(
        str(entry.get("sourceName") or "SEBI final offer terms"),
        str(entry.get("sourceUrl") or ""),
        "regulator",
    )
    sources = [source_item for source_item in (record.get("sources") or []) if isinstance(source_item, dict)]
    sources = [source_item for source_item in sources if str(source_item.get("name") or "") != source["name"]]
    sources.append(source)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    observation = dict((record.get("observations") or {}).get("VerifiedP4OfficialIssueTerms") or {})
    observation.update(
        {
            "issueSizeCr": round(total, 4),
            "freshIssueCr": round(fresh, 4) if fresh is not None else None,
            "ofsCr": round(ofs, 4) if ofs is not None else None,
            "sourceUrl": entry.get("sourceUrl"),
            "sourceKind": "regulator",
            "openDate": entry.get("openDate"),
        }
    )
    record.setdefault("observations", {})["VerifiedP4OfficialIssueTerms"] = observation
    record["validation"] = core.build_validation(record)
    return changed


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [record for record in payload.get("ipos") or [] if isinstance(record, dict)]
    by_id = {str(record.get("id") or ""): record for record in records}

    updated = 0
    identity_rejected = 0
    field_counts: dict[str, int] = {}
    for record_id, entry in VERIFIED_P4_OFFICIAL_ISSUE_TERMS.items():
        record = by_id.get(record_id)
        if record is None:
            print(f"Verified P4 official issue terms: missing record {record_id}")
            continue
        if not identity_matches(record_id, record, entry):
            identity_rejected += 1
            print(f"Verified P4 official issue terms: identity mismatch {record_id}")
            continue
        changed = apply_entry(record_id, record, entry)
        if not changed:
            continue
        updated += 1
        for field in changed:
            field_counts[field] = field_counts.get(field, 0) + 1
        print(
            f"Verified P4 official issue terms: {record_id} "
            f"issueSizeCr={record.get('issueSizeCr')} freshIssueCr={record.get('freshIssueCr')} "
            f"ofsCr={record.get('ofsCr')} changed={','.join(changed)}"
        )

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})[SOURCE_HEALTH_KEY] = {
        "ok": identity_rejected == 0,
        "entries": len(VERIFIED_P4_OFFICIAL_ISSUE_TERMS),
        "updated": updated,
        "identityRejected": identity_rejected,
        "fields": field_counts,
        "checkedAt": core.now_ist().isoformat(timespec="seconds"),
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Verified P4 official issue terms: entries={len(VERIFIED_P4_OFFICIAL_ISSUE_TERMS)} "
        f"updated={updated} identity_rejected={identity_rejected} fields={field_counts}"
    )
    return 1 if identity_rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
