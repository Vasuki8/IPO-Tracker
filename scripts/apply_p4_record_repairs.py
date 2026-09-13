#!/usr/bin/env python3
"""Apply narrow, source-backed P4 record repairs and availability resolutions.

This module handles two classes of residuals that generic exchange collectors
cannot safely infer:

1. IPO records whose equity symbol was overwritten by a later debt-security
   symbol.  These are repaired only with exact identity/date guards and official
   NSE evidence, and only the explicitly verified missing terms are filled.
2. Auxiliary corporate-action/event rows that are not distinct IPOs.  Their IPO-
   specific blanks remain visible in completeness coverage, but are marked
   ``not-applicable`` in ``dataAvailability`` so they no longer masquerade as
   actionable P4 work.

Nothing is resolved by heuristic alone.  Every registry entry carries an
official-source URL and requires exact record id, company, symbol and open date.
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


def _repair(
    company: str,
    symbol: str,
    open_date: str,
    corrected_symbol: str,
    price_min: float,
    price_max: float,
    lot_size: int,
    source_name: str,
    source_url: str,
) -> dict[str, Any]:
    return {
        "company": company,
        "symbol": symbol,
        "openDate": open_date,
        "correctedSymbol": corrected_symbol,
        "priceBand": {"min": price_min, "max": price_max},
        "lotSize": lot_size,
        "sourceName": source_name,
        "sourceUrl": source_url,
    }


VERIFIED_IDENTITY_REPAIRS: dict[str, dict[str, Any]] = {
    "avtl29": _repair(
        "Aegis Vopak Terminals Limited",
        "AVTL29",
        "2025-05-26",
        "AEGISVOPAK",
        223.0,
        235.0,
        63,
        "NSE Aegis Vopak IPO issue information",
        "https://www.nseindia.com/market-data/issue-information?series=EQ&symbol=AEGISVOPAK",
    ),
    "84ail28": _repair(
        "Afcons Infrastructure Limited",
        "84AIL28",
        "2024-10-25",
        "AFCONS",
        440.0,
        463.0,
        32,
        "NSE Afcons IPO basis of allotment",
        "https://nsearchives.nseindia.com/corporate/ADV_INE101I01011_31OCT2024.pdf",
    ),
}


def _resolution_entry(
    company: str,
    symbol: str,
    open_date: str,
    fields: tuple[str, ...],
    reason: str,
    source_name: str,
    source_url: str,
) -> dict[str, Any]:
    return {
        "company": company,
        "symbol": symbol,
        "openDate": open_date,
        "fields": fields,
        "reason": reason,
        "sourceName": source_name,
        "sourceUrl": source_url,
    }


_EVENT_IPO_FIELDS = (
    "exchange.lotSize",
    "exchange.issueSizeCr",
    "exchange.issueComposition",
    "lifecycle.listingDate",
)


AVAILABILITY_RESOLUTIONS: dict[str, dict[str, Any]] = {
    "adanienpp1": _resolution_entry(
        "Adani Enterprises Limited",
        "ADANIENPP1",
        "2026-01-06",
        ("exchange.lotSize", "exchange.issueSizeCr", "exchange.issueComposition"),
        "Auxiliary partly-paid further-issue security, not a distinct IPO application record.",
        "NSE listing circular NSE/CML/72630",
        "https://nsearchives.nseindia.com/content/circulars/CML72630.pdf",
    ),
    "rsl": _resolution_entry(
        "Rajputana Stainless Limited-Special Withdrawal Option",
        "RSL",
        "2026-03-12",
        _EVENT_IPO_FIELDS,
        "Auxiliary investor-withdrawal-option event row; the actual Rajputana Stainless IPO is a separate equity listing.",
        "NSE Rajputana Stainless withdrawal notice",
        "https://nsearchives.nseindia.com/corporate/IRMENERGY_13032026170101_Cover_SE_Intimation_signed.pdf",
    ),
    "c2cw": _resolution_entry(
        "C2C Advanced Systems Limited- Withdrawal Window",
        "C2CW",
        "2024-11-26",
        _EVENT_IPO_FIELDS,
        "Auxiliary withdrawal-window event row; the actual C2C Advanced Systems SME IPO listed under symbol C2C.",
        "NSE C2C Advanced Systems SME-IPO listing release",
        "https://nsearchives.nseindia.com/web/sites/default/files/2024-12/PR_List_02122024.pdf",
    ),
    "sampoorna": _resolution_entry(
        "NFP Sampoorna Foods Limited-Issue Withdrawn",
        "SAMPOORNA",
        "2026-02-04",
        _EVENT_IPO_FIELDS,
        "Withdrawn February event row; the later completed NFP Sampoorna Foods IPO is a separate issue under symbol NFPSAMPOOR.",
        "NSE NFP Sampoorna Foods completed IPO issue information",
        "https://www.nseindia.com/market-data/issue-information?series=SME&symbol=NFPSAMPOOR&type=Active",
    ),
    "icel": _resolution_entry(
        "IC Electricals Company Limited-Issue postponed",
        "ICEL",
        "2026-06-25",
        _EVENT_IPO_FIELDS,
        "Postponed June 2026 issue event row. IC Electricals later returned with a separate completed NSE SME issue, so this structural row must not inherit the later issue terms or listing date.",
        "NSE IC Electricals issue information",
        "https://www.nseindia.com/market-data/issue-information?series=SME&symbol=ICEL&type=Active",
    ),
    "spgcl": _resolution_entry(
        "Sri Priyanka Geo Commex Limited-Issue Withdrawn",
        "SPGCL",
        "2026-06-24",
        _EVENT_IPO_FIELDS,
        "Withdrawn June 2026 NSE SME issue event row; IPO-specific completion and listing fields are not actionable for this withdrawn event record.",
        "NSE Sri Priyanka Geo Commex issue information",
        "https://www.nseindia.com/market-data/issue-information?series=SME&symbol=SPGCL&type=Active",
    ),
}


def _identity_matches(record_id: str, record: dict[str, Any], entry: dict[str, Any]) -> bool:
    if str(record.get("id") or "") != record_id:
        return False
    if str(record.get("symbol") or "").upper() != str(entry.get("symbol") or "").upper():
        return False
    if core.iso_date(record.get("openDate")) != entry.get("openDate"):
        return False
    return core.canonical_company(record.get("company")) == core.canonical_company(entry.get("company"))


def _stamp_source(record: dict[str, Any], entry: dict[str, Any], kind: str) -> None:
    source = core.source_stamp(
        str(entry["sourceName"]),
        str(entry["sourceUrl"]),
        kind,
    )
    sources = [item for item in (record.get("sources") or []) if isinstance(item, dict)]
    sources = [item for item in sources if str(item.get("name") or "") != source["name"]]
    sources.append(source)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))


def apply_identity_repair(record_id: str, record: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    if not _identity_matches(record_id, record, entry):
        return []

    changed: list[str] = []
    corrected_symbol = str(entry["correctedSymbol"])
    if str(record.get("symbol") or "").upper() != corrected_symbol.upper():
        record["symbol"] = corrected_symbol
        changed.append("symbol")

    if record.get("priceBand") in (None, "", {}, []):
        record["priceBand"] = dict(entry["priceBand"])
        changed.append("priceBand")
    if record.get("lotSize") in (None, "", 0):
        record["lotSize"] = int(entry["lotSize"])
        changed.append("lotSize")

    if not changed:
        return []

    _stamp_source(record, entry, "official-exchange-record-repair")
    record.setdefault("observations", {})["P4VerifiedRecordRepair"] = {
        "previousSymbol": entry["symbol"],
        "symbol": corrected_symbol,
        "priceBand": dict(entry["priceBand"]),
        "lotSize": int(entry["lotSize"]),
        "openDate": entry["openDate"],
        "sourceUrl": entry["sourceUrl"],
    }
    record["validation"] = core.build_validation(record)
    return changed


def apply_availability_resolution(record_id: str, record: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    if not _identity_matches(record_id, record, entry):
        return []

    availability = record.setdefault("dataAvailability", {})
    if not isinstance(availability, dict):
        return []

    changed: list[str] = []
    checked_at = core.now_ist().isoformat(timespec="seconds")
    for field in entry["fields"]:
        existing = availability.get(field)
        if isinstance(existing, dict) and str(existing.get("status") or "").strip():
            continue
        if isinstance(existing, str) and existing.strip():
            continue
        availability[field] = {
            "status": "not-applicable",
            "reason": entry["reason"],
            "sourceName": entry["sourceName"],
            "sourceUrl": entry["sourceUrl"],
            "checkedAt": checked_at,
        }
        changed.append(field)

    if not changed:
        return []

    _stamp_source(record, entry, "availability-resolution")
    record.setdefault("observations", {})["P4AvailabilityResolution"] = {
        "fields": list(entry["fields"]),
        "status": "not-applicable",
        "reason": entry["reason"],
        "sourceUrl": entry["sourceUrl"],
    }
    record["validation"] = core.build_validation(record)
    return changed


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    by_id = {str(row.get("id") or ""): row for row in records}

    repaired = resolved = 0
    for record_id, entry in VERIFIED_IDENTITY_REPAIRS.items():
        record = by_id.get(record_id)
        if not record:
            print(f"P4 repair: missing record {record_id}")
            continue
        changed = apply_identity_repair(record_id, record, entry)
        if changed:
            repaired += 1
            print(f"P4 repair: {record_id} changed={','.join(changed)}")

    for record_id, entry in AVAILABILITY_RESOLUTIONS.items():
        record = by_id.get(record_id)
        if not record:
            print(f"P4 availability: missing record {record_id}")
            continue
        changed = apply_availability_resolution(record_id, record, entry)
        if changed:
            resolved += 1
            print(f"P4 availability: {record_id} resolved={','.join(changed)}")

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["P4-verified-record-repairs"] = {
        "ok": True,
        "identityRepairEntries": len(VERIFIED_IDENTITY_REPAIRS),
        "identityRecordsUpdated": repaired,
        "availabilityEntries": len(AVAILABILITY_RESOLUTIONS),
        "availabilityRecordsUpdated": resolved,
        "checkedAt": core.now_ist().isoformat(timespec="seconds"),
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"P4 verified repairs: repaired={repaired}, availability_resolved={resolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
