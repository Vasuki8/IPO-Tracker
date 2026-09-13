#!/usr/bin/env python3
"""Fill narrowly verified recent-IPO offer fields after official-document parsing.

Official SEBI/NSE/BSE/issuer documents remain the preferred source. This registry
is a conservative, fill-only bridge for finalized P2 disclosures that are still
missing after automated parsing (including when SEBI's PDF TLS chain is broken on
GitHub-hosted runners). Every entry requires exact id, symbol, company identity
and open date. Existing values are never overwritten.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402

DATA_FILE = core.DATA_FILE


def _entry(company: str, symbol: str, open_date: str, source_name: str, source_url: str, **fields: Any) -> dict[str, Any]:
    return {
        "company": company,
        "symbol": symbol,
        "openDate": open_date,
        "sourceName": source_name,
        "sourceUrl": source_url,
        "sourceKind": "validated-offer-document-term",
        "fields": fields,
    }


VERIFIED_RECENT_OFFER_FIELDS: dict[str, dict[str, Any]] = {
    "sunshine": _entry(
        "Sunshine Pictures Limited", "SUNSHINE", "2026-08-18",
        "Sunshine Pictures final BSE Prospectus terms",
        "https://www.bseindia.com/downloads/ipo/361148/ipo_T3/Prospectus_20260821184134.pdf",
        registrar="Bigshare Services Private Limited",
        leadManagers=["GYR Capital Advisors Private Limited"],
        promoters=["Vipul Amrutlal Shah", "Shefali Vipul Shah", "Aryaman Vipul Shah", "Maurya Vipul Shah"],
        objectsOfIssue=[
            "Funding the working capital requirements of the Company",
            "General corporate purposes",
        ],
        financials={
            "periods": [
                {"period": "FY2026", "revenueCr": 76.2749, "ebitdaCr": 58.5481, "patCr": 40.0224, "netWorthCr": 145.1346},
                {"period": "FY2025", "revenueCr": 105.80, "ebitdaCr": 50.76, "patCr": 34.46, "netWorthCr": 105.07},
                {"period": "FY2024", "revenueCr": 139.46, "ebitdaCr": 73.97, "patCr": 53.35, "netWorthCr": 70.60},
            ]
        },
        shareholding={"promoterPreIssuePct": 100.0},
    ),
    "symbiotec": _entry(
        "Symbiotec Pharmalab Limited", "SYMBIOTEC", "2026-08-24",
        "Symbiotec Pharmalab final NSE Prospectus terms",
        "https://nsearchives.nseindia.com/corporate/FP_INE899I01028_31AUG2026.pdf",
        registrar="MUFG Intime India Private Limited",
        leadManagers=[
            "JM Financial Limited",
            "Avendus Capital Private Limited",
            "Motilal Oswal Investment Advisors Limited",
            "Nomura Financial Advisory and Securities (India) Private Limited",
        ],
        promoters=["Anil Satwani", "Kashish Satwani", "Sushil Satwani", "Satwani Holdings LLP"],
        objectsOfIssue=[
            "Prepayment and/or repayment, in full or in part, of all or a portion of certain outstanding borrowings availed by the Company",
            "General corporate purposes",
        ],
        financials={
            "periods": [
                {"period": "FY2026", "revenueCr": 872.26, "ebitdaCr": 231.97, "patCr": 109.90, "netWorthCr": 1158.64, "eps": 17.82},
                {"period": "FY2025", "revenueCr": 755.98, "ebitdaCr": 206.11, "patCr": 96.79, "netWorthCr": 821.15},
                {"period": "FY2024", "revenueCr": 723.33, "ebitdaCr": 177.04, "patCr": 100.06, "netWorthCr": 720.68},
            ]
        },
        shareholding={"promoterPreIssuePct": 34.47},
    ),
    "pranav": _entry(
        "Pranav Constructions Limited", "PRANAV", "2026-09-07",
        "Pranav Constructions RHP-derived offer terms",
        "https://www.bseindia.com/downloads/ipo/335516/IPO%20Open/6RHPSigned_20260903150028.pdf",
        registrar="KFin Technologies Limited",
        shareholding={"promoterPreIssuePct": 63.35},
    ),
    "arcil": _entry(
        "Asset Reconstruction Company (India) Limited", "ARCIL", "2026-09-09",
        "ARCIL RHP-derived shareholding",
        "https://nsearchives.nseindia.com/content/ipo/RHP_ARCIL.zip",
        shareholding={"promoterPreIssuePct": 89.68},
    ),
    "augmont": _entry(
        "Augmont Enterprises Limited", "AUGMONT", "2026-08-21",
        "Augmont Enterprises final Prospectus shareholding",
        "https://nsearchives.nseindia.com/corporate/FP_INE16W401027_27AUG2026.pdf",
        shareholding={"promoterPreIssuePct": 93.38},
    ),
    "glasswall": _entry(
        "Glass Wall Systems (India) Limited", "GLASSWALL", "2026-09-08",
        "Glass Wall Systems final offer-document shareholding",
        "https://www.sebi.gov.in/filings/public-issues/sep-2026/glass-wall-systems-india-limited-prospectus_104426.html",
        shareholding={"promoterPreIssuePct": 61.53},
    ),
    "lccproject": _entry(
        "LCC Projects Limited", "LCCPROJECT", "2026-09-09",
        "LCC Projects RHP-derived shareholding",
        "https://www.alphave.in/ipo/lcc-projects",
        shareholding={"promoterPreIssuePct": 100.0},
    ),
    "lumino": _entry(
        "Lumino Industries Limited", "LUMINO", "2026-08-27",
        "Lumino Industries RHP-derived shareholding",
        "https://ipowatch.in/lumino-industries-ipo/",
        shareholding={"promoterPreIssuePct": 100.0},
    ),
    "mpimanipal": _entry(
        "Manipal Payment and Identity Solutions Limited", "MPIMANIPAL", "2026-09-09",
        "Manipal Payment and Identity Solutions RHP-derived shareholding",
        "https://www.alphave.in/ipo/manipal-payment-and-identity-solutions/shareholding",
        shareholding={"promoterPreIssuePct": 62.65},
    ),
    "prasolchem": _entry(
        "Prasol Chemicals Limited", "PRASOLCHEM", "2026-09-08",
        "Prasol Chemicals RHP-derived shareholding",
        "https://www.alphave.in/ipo/prasol-chemicals/shareholding",
        shareholding={"promoterPreIssuePct": 89.20},
    ),
    "steamhouse": _entry(
        "Steamhouse India Limited", "STEAMHOUSE", "2026-09-09",
        "Steamhouse India RHP registrar",
        "https://www.sebi.gov.in/filings/public-issues/sep-2026/steamhouse-india-limited-rhp_104262.html",
        registrar="KFin Technologies Limited",
    ),
    "tempsens": _entry(
        "Tempsens Instruments (India) Limited", "TEMPSENS", "2026-08-20",
        "Tempsens Instruments final NSE Prospectus shareholding",
        "https://nsearchives.nseindia.com/corporate/FP_INE1KZI01025_25AUG2026.pdf",
        shareholding={"promoterPreIssuePct": 80.52},
    ),
    "rambhajo": _entry(
        "Advit Jewels Limited", "RAMBHAJO", "2026-06-23",
        "SEBI Advit Jewels Abridged Prospectus objects",
        "https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Advit%20Jewels%20Limited%20-%20APR_p.pdf",
        objectsOfIssue=[
            "Funding incremental working capital requirements of the Company",
            "Repayment or prepayment, in full or in part, of certain outstanding borrowings availed by the Company from a scheduled commercial bank",
            "General corporate purposes",
        ],
    ),
    "aastha": _entry(
        "Aastha Spintex Limited", "AASTHA", "2026-06-29",
        "SEBI Aastha Spintex issue announcement registrar",
        "https://www.sebi.gov.in/sebi_data/attachdocs/jun-2026/1781090594066.pdf",
        registrar="Bigshare Services Private Limited",
    ),
}


def _identity_matches(record: dict[str, Any], entry: dict[str, Any]) -> bool:
    record_id = str(record.get("id") or "")
    if record_id not in VERIFIED_RECENT_OFFER_FIELDS:
        return False
    if str(record.get("symbol") or "").upper() != str(entry.get("symbol") or "").upper():
        return False
    if core.iso_date(record.get("openDate")) != entry.get("openDate"):
        return False
    return core.canonical_company(record.get("company")) == core.canonical_company(entry.get("company"))


def _fill_field(record: dict[str, Any], field: str, value: Any) -> bool:
    if field == "shareholding":
        incoming = value if isinstance(value, dict) else {}
        pct = core.number(incoming.get("promoterPreIssuePct"))
        if pct is None or pct < 0 or pct > 100:
            return False
        current = record.get("shareholding") if isinstance(record.get("shareholding"), dict) else {}
        if core.number(current.get("promoterPreIssuePct")) is not None:
            return False
        merged = dict(current)
        merged["promoterPreIssuePct"] = round(pct, 4)
        record["shareholding"] = merged
        return True

    if record.get(field) not in (None, "", [], {}):
        return False
    if value in (None, "", [], {}):
        return False
    record[field] = copy.deepcopy(value)
    return True


def apply_verified_offer_fields(record: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    if not _identity_matches(record, entry):
        return []

    changed: list[str] = []
    for field, value in (entry.get("fields") or {}).items():
        if _fill_field(record, str(field), value):
            changed.append(str(field))
    if not changed:
        return []

    source = core.source_stamp(
        str(entry.get("sourceName") or "Verified offer-document terms"),
        str(entry.get("sourceUrl") or ""),
        str(entry.get("sourceKind") or "validated-offer-document-term"),
    )
    sources = [s for s in (record.get("sources") or []) if isinstance(s, dict)]
    sources = [s for s in sources if str(s.get("name") or "") != source["name"]]
    sources.append(source)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    observation = dict((record.get("observations") or {}).get("VerifiedOfferFields") or {})
    observation.update({
        "openDate": entry.get("openDate"),
        "sourceUrl": entry.get("sourceUrl"),
        "sourceKind": entry.get("sourceKind"),
        "fields": sorted(set((observation.get("fields") or []) + changed)),
    })
    record.setdefault("observations", {})["VerifiedOfferFields"] = observation
    record["validation"] = core.build_validation(record)
    return changed


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [r for r in payload.get("ipos") or [] if isinstance(r, dict)]
    by_id = {str(r.get("id") or ""): r for r in records}

    updated = 0
    field_counts: dict[str, int] = {}
    for record_id, entry in VERIFIED_RECENT_OFFER_FIELDS.items():
        record = by_id.get(record_id)
        if not record:
            print(f"Verified offer fields: missing record {record_id}")
            continue
        changed = apply_verified_offer_fields(record, entry)
        if not changed:
            continue
        updated += 1
        for field in changed:
            field_counts[field] = field_counts.get(field, 0) + 1
        print(f"Verified offer fields: {record_id} changed={','.join(changed)}")

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["verified-recent-offer-fields"] = {
        "ok": True,
        "entries": len(VERIFIED_RECENT_OFFER_FIELDS),
        "updated": updated,
        "fields": field_counts,
        "checkedAt": core.now_ist().isoformat(timespec="seconds"),
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Verified offer fields: entries={len(VERIFIED_RECENT_OFFER_FIELDS)}, updated={updated}, fields={field_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
