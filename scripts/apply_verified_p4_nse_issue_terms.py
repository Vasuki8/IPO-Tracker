#!/usr/bin/env python3
"""Apply deterministic P4 issue-size/composition facts from official NSE sources.

Every entry is exact-identity guarded, fill-only and sourced only to
nsearchives.nseindia.com. Provenance is stamped as exchange data. This registry
is separate from the SEBI registry so source type remains accurate.
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
SOURCE_HEALTH_KEY = "verified-p4-nse-issue-terms"


def _entry(
    company: str,
    symbol: str,
    open_date: str,
    total: float,
    fresh: float,
    ofs: float,
    source_name: str,
    source_urls: str | list[str],
    *,
    source_basis: str = "official NSE finalized IPO terms",
    official_note: str | None = None,
) -> dict[str, Any]:
    urls = [source_urls] if isinstance(source_urls, str) else list(source_urls)
    return {
        "company": company,
        "symbol": symbol,
        "openDate": open_date,
        "issueSizeCr": total,
        "freshIssueCr": fresh,
        "ofsCr": ofs,
        "sourceName": source_name,
        "sourceUrls": urls,
        "sourceBasis": source_basis,
        "officialNote": official_note,
    }


VERIFIED_P4_NSE_ISSUE_TERMS: dict[str, dict[str, Any]] = {
    "abhapower": _entry(
        "Abha Power and Steel Limited",
        "ABHAPOWER",
        "2024-11-27",
        38.544,
        31.044,
        7.5,
        "NSE Emerge Abha Power and Steel Prospectus",
        "https://nsearchives.nseindia.com/emerge/corporates/content/AbhaPowerandSteelLimited_PROSP.pdf",
    ),
    "agarwaltuf": _entry(
        "Agarwal Toughened Glass India Limited",
        "AGARWALTUF",
        "2024-11-28",
        62.63568,
        62.63568,
        0.0,
        "NSE Agarwal Toughened Glass official IPO disclosures",
        [
            "https://nsearchives.nseindia.com/corporate/AGARWALTOUGHENED_06092025172834_tuff_covering_Annualreport_notice_FY2025_se_signed.pdf",
            "https://nsearchives.nseindia.com/corporate/ixbrl/INTEGRATED_FILING_NONINDAS_125947_11112025155716_iXBRL_WEB.html",
        ],
        source_basis="57,99,600 fresh shares at Rs 108 per share",
        official_note=(
            "Exact share-count times issue-price equals Rs 6,263.568 lakh; "
            "the later NSE integrated filing displays Rs 6,263.56 lakh. "
            "Stored value follows the exact official share-count and issue-price product."
        ),
    ),
    "apexeco": _entry(
        "Apex Ecotech Limited",
        "APEXECO",
        "2024-11-27",
        25.5442,
        25.5442,
        0.0,
        "NSE Emerge Apex Ecotech Prospectus",
        "https://nsearchives.nseindia.com/emerge/corporates/content/ApexEcotechLimited_PROSP.pdf",
    ),
    "dhanlaxmi": _entry(
        "Dhanlaxmi Crop Science Limited",
        "DHANLAXMI",
        "2024-12-09",
        23.804,
        23.804,
        0.0,
        "NSE Emerge Dhanlaxmi Crop Science Prospectus",
        "https://nsearchives.nseindia.com/emerge/corporates/content/DhanlaxmiCropScienceLimited_PROSP.pdf",
    ),
}


def _nse_official_url(url: str) -> bool:
    try:
        host = (urlparse(str(url or "")).hostname or "").lower()
        return host == "nsearchives.nseindia.com"
    except Exception:
        return False


def identity_matches(record_id: str, record: dict[str, Any], entry: dict[str, Any]) -> bool:
    if record_id not in VERIFIED_P4_NSE_ISSUE_TERMS:
        return False
    if str(record.get("id") or "") != record_id:
        return False
    if str(record.get("symbol") or "").upper() != str(entry.get("symbol") or "").upper():
        return False
    if core.iso_date(record.get("openDate")) != str(entry.get("openDate") or ""):
        return False
    if core.canonical_company(record.get("company")) != core.canonical_company(entry.get("company")):
        return False
    urls = [str(url) for url in entry.get("sourceUrls") or []]
    return bool(urls) and all(_nse_official_url(url) for url in urls)


def apply_entry(record_id: str, record: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    if not identity_matches(record_id, record, entry):
        return []

    total = core.number(entry.get("issueSizeCr"))
    fresh = core.number(entry.get("freshIssueCr"))
    ofs = core.number(entry.get("ofsCr"))
    if total is None or fresh is None or ofs is None or total <= 0 or fresh < 0 or ofs < 0:
        return []
    if abs((fresh + ofs) - total) > 0.05:
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
            "sourceBasis": str(entry.get("sourceBasis") or "official NSE finalized IPO terms"),
        }
        if entry.get("officialNote"):
            record["issueComposition"]["officialNote"] = str(entry["officialNote"])
        changed.append("issueComposition")

    if not changed:
        return []

    urls = [str(url) for url in entry.get("sourceUrls") or []]
    sources = [source for source in (record.get("sources") or []) if isinstance(source, dict)]
    prefix = str(entry.get("sourceName") or "NSE finalized IPO terms")
    sources = [source for source in sources if not str(source.get("name") or "").startswith(prefix)]
    for index, url in enumerate(urls, start=1):
        name = prefix if len(urls) == 1 else f"{prefix} ({index})"
        sources.append(core.source_stamp(name, url, "exchange"))
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    observation = dict((record.get("observations") or {}).get("VerifiedP4NSEIssueTerms") or {})
    observation.update(
        {
            "issueSizeCr": round(total, 5),
            "freshIssueCr": round(fresh, 5),
            "ofsCr": round(ofs, 5),
            "openDate": entry.get("openDate"),
            "sourceUrls": urls,
            "sourceKind": "exchange",
            "sourceBasis": entry.get("sourceBasis"),
        }
    )
    if entry.get("officialNote"):
        observation["officialNote"] = entry.get("officialNote")
    record.setdefault("observations", {})["VerifiedP4NSEIssueTerms"] = observation
    record["validation"] = core.build_validation(record)
    return changed


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [record for record in payload.get("ipos") or [] if isinstance(record, dict)]
    by_id = {str(record.get("id") or ""): record for record in records}

    updated = 0
    rejected = 0
    field_counts: dict[str, int] = {}
    for record_id, entry in VERIFIED_P4_NSE_ISSUE_TERMS.items():
        record = by_id.get(record_id)
        if record is None:
            print(f"Verified P4 NSE issue terms: missing record {record_id}")
            continue
        if not identity_matches(record_id, record, entry):
            rejected += 1
            print(f"Verified P4 NSE issue terms: identity/source mismatch {record_id}")
            continue
        changed = apply_entry(record_id, record, entry)
        if not changed:
            continue
        updated += 1
        for field in changed:
            field_counts[field] = field_counts.get(field, 0) + 1
        print(
            f"Verified P4 NSE issue terms: {record_id} issueSizeCr={record.get('issueSizeCr')} "
            f"freshIssueCr={record.get('freshIssueCr')} ofsCr={record.get('ofsCr')} "
            f"changed={','.join(changed)}"
        )

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})[SOURCE_HEALTH_KEY] = {
        "ok": rejected == 0,
        "entries": len(VERIFIED_P4_NSE_ISSUE_TERMS),
        "updated": updated,
        "rejected": rejected,
        "fields": field_counts,
        "checkedAt": core.now_ist().isoformat(timespec="seconds"),
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Verified P4 NSE issue terms: entries={len(VERIFIED_P4_NSE_ISSUE_TERMS)} "
        f"updated={updated} rejected={rejected} fields={field_counts}"
    )
    return 1 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
