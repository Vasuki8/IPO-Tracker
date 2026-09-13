#!/usr/bin/env python3
"""Close the final actionable P4 issue-composition gaps from official sources only.

This pass is deliberately composition-only. It requires an already populated,
source-backed issueSizeCr, never writes issueSizeCr/lotSize/priceBand/listingDate,
and fills fresh/OFS values only after exact identity and source validation.
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
SOURCE_HEALTH_KEY = "verified-p4-final-composition"
ALLOWED_HOSTS = {"nsearchives.nseindia.com", "www.nseindia.com"}


def _entry(
    company: str,
    symbol: str,
    open_date: str,
    mode: str,
    sources: list[dict[str, str]],
    *,
    expected_total: float | None = None,
    fresh: float | None = None,
    ofs: float | None = None,
    basis: str,
) -> dict[str, Any]:
    return {
        "company": company,
        "symbol": symbol,
        "openDate": open_date,
        "mode": mode,
        "sources": sources,
        "expectedTotal": expected_total,
        "freshIssueCr": fresh,
        "ofsCr": ofs,
        "sourceBasis": basis,
    }


def _nse(name: str, url: str) -> dict[str, str]:
    return {"name": name, "url": url, "kind": "exchange"}


VERIFIED_P4_FINAL_COMPOSITION: dict[str, dict[str, Any]] = {
    "igil": _entry(
        "International Gemmological Institute (India) Limited",
        "IGIL",
        "2024-12-13",
        "mixed",
        [_nse("NSE IGI Basis of Allotment", "https://nsearchives.nseindia.com/web/sites/default/files/inline-files/BasisofAllotment_international.pdf")],
        expected_total=4225.0,
        fresh=1475.0,
        ofs=2750.0,
        basis="NSE Basis of Allotment: Rs 42,250 million offer = Rs 14,750 million fresh issue + Rs 27,500 million OFS.",
    ),
    "iks": _entry(
        "Inventurus Knowledge Solutions Limited",
        "IKS",
        "2024-12-12",
        "pure-ofs",
        [_nse("NSE IKS Basis of Allotment", "https://nsearchives.nseindia.com/corporate/ADV_INE115Q01022_18DEC2024.pdf")],
        expected_total=2497.923,
        basis="NSE Basis of Allotment states the entire Rs 24,979.23 million offer is through an offer for sale.",
    ),
    "krt": _entry(
        "Knowledge Realty Trust",
        "KRT",
        "2025-08-05",
        "pure-fresh",
        [_nse("NSE Knowledge Realty Trust audited annual filing", "https://nsearchives.nseindia.com/corporate/KRT_17062026122333_Outcome_of_BM_17_June_2026_1.pdf")],
        expected_total=4800.0,
        basis="NSE-hosted audited filing records 480,000,000 IPO units, issued/subscribed/fully paid in cash, amount Rs 48,000 million.",
    ),
    "anantam": _entry(
        "Anantam Highways Trust",
        "ANANTAM",
        "2025-10-07",
        "pure-fresh",
        [_nse("NSE Anantam audited filing", "https://nsearchives.nseindia.com/corporate/ixbrl/INTEGRATED_FILING_RESULTIR_125924_11112025151939_iXBRL_WEB.html")],
        expected_total=400.0,
        basis="NSE filing records 40,000,000 units at Rs 100 each and explicitly identifies the IPO allotment as Fresh Issue.",
    ),
    "citiusinvt": _entry(
        "Citius Transnet Investment Trust",
        "CITIUSINVT",
        "2026-04-17",
        "pure-fresh",
        [
            _nse("NSE Citius Issue Information", "https://www.nseindia.com/market-data/issue-information?series=IV&symbol=CITIUSINVT&type=Forthcoming"),
            _nse("NSE Citius post-listing financial filing", "https://nsearchives.nseindia.com/corporate/ixbrl/INTEGRATED_FILING_RESULTIR_187641_14082026191348_iXBRL_WEB.html"),
        ],
        expected_total=1105.0,
        basis="NSE Issue Information fixes the IPO at Rs 11,050 million; post-listing filing records 110,500,000 units issued at Rs 100 for the IPO.",
    ),
    "riit": _entry(
        "Raajmarg Infra Investment Trust",
        "RIIT",
        "2026-03-11",
        "pure-fresh",
        [_nse("NSE Raajmarg audited financial filing", "https://nsearchives.nseindia.com/corporate/ixbrl/INTEGRATED_FILING_RESULTIR_167138_15062026123648_iXBRL_WEB.html")],
        expected_total=6000.0,
        basis="NSE audited filing records 600,000,000 units and Rs 600,000 lakh proceeds from issuing units for the IPO fresh issue.",
    ),
    "cubeinvit": _entry(
        "Cube Highways Trust",
        "CUBEINVIT",
        "2026-07-22",
        "pure-ofs",
        [_nse("NSE Cube Highways Trust offer filing", "https://nsearchives.nseindia.com/corporate/CUBEINVIT_18032026004707_IntimationCHTDOD.pdf")],
        basis="NSE filing explicitly defines the public conversion offer as an offer for sale of existing units by Selling Unitholders; the already source-backed issueSizeCr is retained as the OFS amount.",
    ),
}


def _valid_source(source: dict[str, Any]) -> bool:
    try:
        host = (urlparse(str(source.get("url") or "")).hostname or "").lower()
    except Exception:
        return False
    return host in ALLOWED_HOSTS and str(source.get("kind") or "") == "exchange"


def identity_matches(record_id: str, record: dict[str, Any], entry: dict[str, Any]) -> bool:
    if record_id not in VERIFIED_P4_FINAL_COMPOSITION or str(record.get("id") or "") != record_id:
        return False
    if str(record.get("symbol") or "").upper() != str(entry.get("symbol") or "").upper():
        return False
    if core.iso_date(record.get("openDate")) != str(entry.get("openDate") or ""):
        return False
    if core.canonical_company(record.get("company")) != core.canonical_company(entry.get("company")):
        return False
    sources = [source for source in entry.get("sources") or [] if isinstance(source, dict)]
    return bool(sources) and all(_valid_source(source) for source in sources)


def _composition(record: dict[str, Any], entry: dict[str, Any]) -> tuple[float, float, float] | None:
    total = core.number(record.get("issueSizeCr"))
    if total is None or total <= 0:
        return None
    expected = core.number(entry.get("expectedTotal"))
    if expected is not None and abs(total - expected) > 0.05:
        return None

    mode = str(entry.get("mode") or "")
    if mode == "pure-fresh":
        return total, 0.0, total
    if mode == "pure-ofs":
        return 0.0, total, total
    if mode == "mixed":
        fresh = core.number(entry.get("freshIssueCr"))
        ofs = core.number(entry.get("ofsCr"))
        if fresh is None or ofs is None or fresh < 0 or ofs < 0 or abs((fresh + ofs) - total) > 0.05:
            return None
        return fresh, ofs, total
    return None


def apply_entry(record_id: str, record: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    if not identity_matches(record_id, record, entry):
        return []
    values = _composition(record, entry)
    if values is None:
        return []
    fresh, ofs, total = values

    changed: list[str] = []
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
            "sourceBasis": str(entry.get("sourceBasis") or "official NSE offer structure"),
        }
        changed.append("issueComposition")
    if not changed:
        return []

    existing = [source for source in (record.get("sources") or []) if isinstance(source, dict)]
    source_names = {str(source.get("name") or "") for source in entry.get("sources") or []}
    existing = [source for source in existing if str(source.get("name") or "") not in source_names]
    for source in entry.get("sources") or []:
        existing.append(core.source_stamp(str(source["name"]), str(source["url"]), "exchange"))
    record["sources"] = core.dedupe_dicts(existing, ("name", "url"))

    record.setdefault("observations", {})["VerifiedP4FinalComposition"] = {
        "issueSizeCr": round(total, 4),
        "freshIssueCr": round(fresh, 4),
        "ofsCr": round(ofs, 4),
        "mode": entry.get("mode"),
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
    for record_id, entry in VERIFIED_P4_FINAL_COMPOSITION.items():
        record = by_id.get(record_id)
        if record is None or not identity_matches(record_id, record, entry) or _composition(record, entry) is None:
            rejected += 1
            print(f"Verified P4 final composition: identity/source/total mismatch {record_id}")
            continue
        changed = apply_entry(record_id, record, entry)
        if not changed:
            continue
        updated += 1
        for field in changed:
            field_counts[field] = field_counts.get(field, 0) + 1
        print(
            f"Verified P4 final composition: {record_id} fresh={record.get('freshIssueCr')} "
            f"ofs={record.get('ofsCr')} changed={','.join(changed)}"
        )

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})[SOURCE_HEALTH_KEY] = {
        "ok": rejected == 0,
        "entries": len(VERIFIED_P4_FINAL_COMPOSITION),
        "updated": updated,
        "rejected": rejected,
        "fields": field_counts,
        "checkedAt": core.now_ist().isoformat(timespec="seconds"),
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Verified P4 final composition: entries={len(VERIFIED_P4_FINAL_COMPOSITION)} "
        f"updated={updated} rejected={rejected} fields={field_counts}"
    )
    return 1 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
