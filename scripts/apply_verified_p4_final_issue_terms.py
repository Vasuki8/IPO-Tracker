#!/usr/bin/env python3
"""Close the final two actionable P4 issue-size/composition gaps.

Anawil combines its issuer-hosted final RHP with the official NSE listing
circular. Fascinate combines its official NSE-hosted RHP package with the NSE
listing circular. Exact record identity guards, arithmetic checks and fill-only
writes are retained; unrelated exchange fields are never touched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402

DATA_FILE = core.DATA_FILE
SOURCE_HEALTH_KEY = "verified-p4-final-issue-terms"
ALLOWED_HOSTS = {"nsearchives.nseindia.com", "anawilvapi.in"}


def _entry(
    company: str,
    symbol: str,
    open_date: str,
    issue_price: float,
    fresh_shares: int,
    ofs_shares: int,
    sources: list[dict[str, str]],
    source_basis: str,
) -> dict[str, Any]:
    total_shares = fresh_shares + ofs_shares
    fresh_cr = fresh_shares * issue_price / 10_000_000
    ofs_cr = ofs_shares * issue_price / 10_000_000
    total_cr = total_shares * issue_price / 10_000_000
    return {
        "company": company,
        "symbol": symbol,
        "openDate": open_date,
        "issuePrice": issue_price,
        "freshShares": fresh_shares,
        "ofsShares": ofs_shares,
        "issueSizeCr": round(total_cr, 5),
        "freshIssueCr": round(fresh_cr, 5),
        "ofsCr": round(ofs_cr, 5),
        "sources": sources,
        "sourceBasis": source_basis,
    }


VERIFIED_P4_FINAL_ISSUE_TERMS: dict[str, dict[str, Any]] = {
    "anawil": _entry(
        "Anawil Wire and Engineering Limited",
        "ANAWIL",
        "2026-08-03",
        270.0,
        5_284_800,
        1_300_800,
        [
            {
                "name": "Anawil Wire and Engineering final RHP",
                "url": "https://anawilvapi.in/uploads/investors/RHP-Anawil%20Wire%20and%20Engineering%20Limited.pdf",
                "kind": "offer-document",
            },
            {
                "name": "NSE listing circular CML75648",
                "url": "https://nsearchives.nseindia.com/content/circulars/CML75648.zip",
                "kind": "exchange",
            },
        ],
        "Final RHP structure: 52,84,800 fresh shares plus 13,00,800 OFS shares; NSE listing circular fixes final issue price at Rs 270 per share.",
    ),
    "fascinate": _entry(
        "Fascinate Textiles Limited",
        "FASCINATE",
        "2026-08-11",
        151.0,
        3_457_600,
        836_000,
        [
            {
                "name": "NSE Fascinate Textiles final RHP package",
                "url": "https://nsearchives.nseindia.com/emerge/corporates/content/Fascinate%20Textiles%20Limited_RHP.zip",
                "kind": "offer-document",
            },
            {
                "name": "NSE listing circular CML75891",
                "url": "https://nsearchives.nseindia.com/content/circulars/CML75891.zip",
                "kind": "exchange",
            },
        ],
        "Final RHP structure: 34,57,600 fresh shares plus 8,36,000 OFS shares; NSE listing circular fixes final issue price at Rs 151 per share.",
    ),
}


def _official_source(source: dict[str, Any]) -> bool:
    url = str(source.get("url") or "")
    kind = str(source.get("kind") or "")
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host in ALLOWED_HOSTS and kind in {"offer-document", "exchange"}


def identity_matches(record_id: str, record: dict[str, Any], entry: dict[str, Any]) -> bool:
    if record_id not in VERIFIED_P4_FINAL_ISSUE_TERMS:
        return False
    if str(record.get("id") or "") != record_id:
        return False
    if str(record.get("symbol") or "").upper() != str(entry.get("symbol") or "").upper():
        return False
    if core.iso_date(record.get("openDate")) != str(entry.get("openDate") or ""):
        return False
    if core.canonical_company(record.get("company")) != core.canonical_company(entry.get("company")):
        return False
    sources = [source for source in entry.get("sources") or [] if isinstance(source, dict)]
    return len(sources) >= 2 and all(_official_source(source) for source in sources)


def apply_entry(record_id: str, record: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    if not identity_matches(record_id, record, entry):
        return []

    price = core.number(entry.get("issuePrice"))
    fresh_shares = core.number(entry.get("freshShares"))
    ofs_shares = core.number(entry.get("ofsShares"))
    total = core.number(entry.get("issueSizeCr"))
    fresh = core.number(entry.get("freshIssueCr"))
    ofs = core.number(entry.get("ofsCr"))
    if None in (price, fresh_shares, ofs_shares, total, fresh, ofs):
        return []
    if price <= 0 or fresh_shares < 0 or ofs_shares < 0 or total <= 0 or fresh < 0 or ofs < 0:
        return []

    arithmetic_total = (fresh_shares + ofs_shares) * price / 10_000_000
    arithmetic_fresh = fresh_shares * price / 10_000_000
    arithmetic_ofs = ofs_shares * price / 10_000_000
    if abs(arithmetic_total - total) > 0.0001:
        return []
    if abs(arithmetic_fresh - fresh) > 0.0001 or abs(arithmetic_ofs - ofs) > 0.0001:
        return []
    if abs((fresh + ofs) - total) > 0.0001:
        return []

    changed: list[str] = []
    if record.get("issueSizeCr") in (None, ""):
        record["issueSizeCr"] = round(total, 5)
        changed.append("issueSizeCr")
    if record.get("freshIssueCr") in (None, ""):
        record["freshIssueCr"] = round(fresh, 5)
        changed.append("freshIssueCr")
    if record.get("ofsCr") in (None, ""):
        record["ofsCr"] = round(ofs, 5)
        changed.append("ofsCr")
    if record.get("issueComposition") in (None, {}, []):
        record["issueComposition"] = {
            "freshIssueCr": round(fresh, 5),
            "ofsCr": round(ofs, 5),
            "totalIssueSizeCr": round(total, 5),
            "sourceBasis": str(entry.get("sourceBasis") or "official final offer terms"),
        }
        changed.append("issueComposition")

    if not changed:
        return []

    existing = [source for source in (record.get("sources") or []) if isinstance(source, dict)]
    source_names = {str(source.get("name") or "") for source in entry.get("sources") or []}
    existing = [source for source in existing if str(source.get("name") or "") not in source_names]
    for source in entry.get("sources") or []:
        existing.append(core.source_stamp(str(source["name"]), str(source["url"]), str(source["kind"])))
    record["sources"] = core.dedupe_dicts(existing, ("name", "url"))

    record.setdefault("observations", {})["VerifiedP4FinalIssueTerms"] = {
        "issuePrice": round(price, 2),
        "freshShares": int(fresh_shares),
        "ofsShares": int(ofs_shares),
        "issueSizeCr": round(total, 5),
        "freshIssueCr": round(fresh, 5),
        "ofsCr": round(ofs, 5),
        "openDate": entry.get("openDate"),
        "sourceBasis": entry.get("sourceBasis"),
        "sourceUrls": [str(source.get("url") or "") for source in entry.get("sources") or []],
    }
    record["validation"] = core.build_validation(record)
    return changed


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [record for record in payload.get("ipos") or [] if isinstance(record, dict)]
    by_id = {str(record.get("id") or ""): record for record in records}

    updated = 0
    rejected = 0
    field_counts: dict[str, int] = {}
    for record_id, entry in VERIFIED_P4_FINAL_ISSUE_TERMS.items():
        record = by_id.get(record_id)
        if record is None:
            print(f"Verified final issue terms: missing record {record_id}")
            continue
        if not identity_matches(record_id, record, entry):
            rejected += 1
            print(f"Verified final issue terms: identity/source mismatch {record_id}")
            continue
        changed = apply_entry(record_id, record, entry)
        if not changed:
            continue
        updated += 1
        for field in changed:
            field_counts[field] = field_counts.get(field, 0) + 1
        print(
            f"Verified final issue terms: {record_id} issueSizeCr={record.get('issueSizeCr')} "
            f"freshIssueCr={record.get('freshIssueCr')} ofsCr={record.get('ofsCr')} changed={','.join(changed)}"
        )

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})[SOURCE_HEALTH_KEY] = {
        "ok": rejected == 0,
        "entries": len(VERIFIED_P4_FINAL_ISSUE_TERMS),
        "updated": updated,
        "rejected": rejected,
        "fields": field_counts,
        "checkedAt": core.now_ist().isoformat(timespec="seconds"),
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Verified final issue terms: entries={len(VERIFIED_P4_FINAL_ISSUE_TERMS)} "
        f"updated={updated} rejected={rejected} fields={field_counts}"
    )
    return 1 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
