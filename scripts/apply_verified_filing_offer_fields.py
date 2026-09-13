#!/usr/bin/env python3
"""Fill narrowly verified P3 filing-pipeline offer-document gaps.

Official SEBI discovery/parsing remains the preferred source. This registry is a
fill-only bridge for current filing-pipeline disclosures that remain missing when
SEBI's PDF transport is unavailable or a document layout evades the parser.

Every entry requires an exact record id, canonical company identity and current
filing-pipeline lifecycle stage. Existing values are never overwritten. The
record keeps both the official SEBI filing page and the independent verification
page used to cross-check the extracted disclosure.
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

import audit_data_completeness as audit  # noqa: E402
import update_data as core  # noqa: E402

DATA_FILE = core.DATA_FILE


def _entry(
    company: str,
    filing_url: str,
    verification_url: str,
    source_name: str,
    **fields: Any,
) -> dict[str, Any]:
    return {
        "company": company,
        "filingUrl": filing_url,
        "verificationUrl": verification_url,
        "sourceName": source_name,
        "sourceKind": "validated-offer-document-term",
        "fields": fields,
    }


NSE_BRLMs = [
    "Kotak Mahindra Capital Company Limited",
    "JM Financial Limited",
    "Morgan Stanley India Company Private Limited",
    "Citigroup Global Markets India Private Limited",
    "HSBC Securities & Capital Markets (India) Private Limited",
    "J.P. Morgan India Private Limited",
    "SBI Capital Markets Limited",
    "Anand Rathi Advisors Limited",
    "Avendus Capital Private Limited",
    "Axis Capital Limited",
    "DAM Capital Advisors Limited",
    "Equirus Capital Limited",
    "HDFC Bank Limited",
    "ICICI Securities Limited",
    "IDBI Capital Markets & Securities Limited",
    "IIFL Capital Services Limited",
    "Motilal Oswal Investment Advisors Limited",
    "Nuvama Wealth Management Limited",
    "Pantomath Capital Advisors Private Limited",
    "360 ONE WAM Limited",
]


VERIFIED_FILING_OFFER_FIELDS: dict[str, dict[str, Any]] = {
    "national-stock-exchange-of-india-limited": _entry(
        "National Stock Exchange of India Limited",
        "https://www.sebi.gov.in/filings/public-issues/sep-2026/national-stock-exchange-of-india-limited-rhp_104428.html",
        "https://timesglobalnews.com/2026/09/11/national-stock-exchange-of-india-limiteds-initial-public-offering-to-open-on-17th-september-2026-price-band-set-at-rs-1700-rs-1785-per-equity-share-of-face-value-of-rs-1-each/",
        "NSE RHP filing disclosures",
        leadManagers=NSE_BRLMs,
        shareholding={
            "promoterPreIssuePct": 0.0,
            "promoterStatus": "No identifiable promoter",
        },
    ),
    "m-k-c-agro-fresh-limited": _entry(
        "M K C AGRO FRESH LIMITED",
        "https://www.sebi.gov.in/filings/public-issues/sep-2026/m-k-c-agro-fresh-limited-drhp_104430.html",
        "https://www.ipoplatform.com/ipo/mkc-agro-fresh-ipo/4803",
        "M K C Agro Fresh DRHP shareholding disclosure",
        shareholding={"promoterPreIssuePct": 28.54},
    ),
    "nopaperforms-solutions-limited": _entry(
        "NOPAPERFORMS SOLUTIONS LIMITED",
        "https://www.sebi.gov.in/filings/public-issues/sep-2026/nopaperforms-solutions-limited-udrhp-1_104427.html",
        "https://ipobarta.ai/ipo/upcoming-ipos/company/nopaperforms-solutions-ipo/2796",
        "NoPaperForms Solutions UDRHP shareholding disclosure",
        shareholding={"promoterPreIssuePct": 30.19},
    ),
    "torrent-gas-limited": _entry(
        "Torrent Gas Limited",
        "https://www.sebi.gov.in/filings/public-issues/sep-2026/torrent-gas-limited-udrhp-i_104350.html",
        "https://www.mfnewsdaily.in/torrent-gas-files-updated-drhp-for-public-issue-promoter-torrent-investments-to-offload-up-to-33-5-crore-shares-via-pure-ofs/",
        "Torrent Gas UDRHP shareholding disclosure",
        shareholding={"promoterPreIssuePct": 100.0},
    ),
}


def _is_filing_pipeline(record: dict[str, Any]) -> bool:
    return audit.lifecycle_stage(record, core.now_ist().date()) == "filing-pipeline"


def _identity_matches(record: dict[str, Any], entry: dict[str, Any]) -> bool:
    record_id = str(record.get("id") or "")
    if record_id not in VERIFIED_FILING_OFFER_FIELDS:
        return False
    if core.canonical_company(record.get("company")) != core.canonical_company(entry.get("company")):
        return False
    return _is_filing_pipeline(record)


def _fill_shareholding(record: dict[str, Any], value: Any) -> bool:
    incoming = value if isinstance(value, dict) else {}
    pct = core.number(incoming.get("promoterPreIssuePct"))
    if pct is None or pct < 0 or pct > 100:
        return False

    current = record.get("shareholding") if isinstance(record.get("shareholding"), dict) else {}
    if core.number(current.get("promoterPreIssuePct")) is not None:
        return False

    merged = dict(current)
    merged["promoterPreIssuePct"] = round(pct, 4)
    promoter_status = str(incoming.get("promoterStatus") or "").strip()
    if promoter_status and not merged.get("promoterStatus"):
        merged["promoterStatus"] = promoter_status
    record["shareholding"] = merged
    return True


def _fill_field(record: dict[str, Any], field: str, value: Any) -> bool:
    if field == "shareholding":
        return _fill_shareholding(record, value)
    if record.get(field) not in (None, "", [], {}):
        return False
    if value in (None, "", [], {}):
        return False
    record[field] = copy.deepcopy(value)
    return True


def apply_verified_filing_offer_fields(record: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    """Fill only missing P3 fields after strict filing-pipeline identity checks."""
    if not _identity_matches(record, entry):
        return []

    changed: list[str] = []
    for field, value in (entry.get("fields") or {}).items():
        if _fill_field(record, str(field), value):
            changed.append(str(field))
    if not changed:
        return []

    source = core.source_stamp(
        str(entry.get("sourceName") or "Verified filing offer-document terms"),
        str(entry.get("filingUrl") or ""),
        str(entry.get("sourceKind") or "validated-offer-document-term"),
    )
    sources = [s for s in (record.get("sources") or []) if isinstance(s, dict)]
    sources = [s for s in sources if str(s.get("name") or "") != source["name"]]
    sources.append(source)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    observation = dict((record.get("observations") or {}).get("VerifiedFilingOfferFields") or {})
    observation.update(
        {
            "filingUrl": entry.get("filingUrl"),
            "verificationUrl": entry.get("verificationUrl"),
            "sourceKind": entry.get("sourceKind"),
            "fields": sorted(set((observation.get("fields") or []) + changed)),
        }
    )
    record.setdefault("observations", {})["VerifiedFilingOfferFields"] = observation
    record["validation"] = core.build_validation(record)
    return changed


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [r for r in payload.get("ipos") or [] if isinstance(r, dict)]
    by_id = {str(r.get("id") or ""): r for r in records}

    updated = 0
    field_counts: dict[str, int] = {}
    for record_id, entry in VERIFIED_FILING_OFFER_FIELDS.items():
        record = by_id.get(record_id)
        if not record:
            print(f"Verified filing offer fields: missing record {record_id}")
            continue
        changed = apply_verified_filing_offer_fields(record, entry)
        if not changed:
            continue
        updated += 1
        for field in changed:
            field_counts[field] = field_counts.get(field, 0) + 1
        print(f"Verified filing offer fields: {record_id} changed={','.join(changed)}")

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["verified-filing-offer-fields"] = {
        "ok": True,
        "entries": len(VERIFIED_FILING_OFFER_FIELDS),
        "updated": updated,
        "fields": field_counts,
        "checkedAt": core.now_ist().isoformat(timespec="seconds"),
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Verified filing offer fields: "
        f"entries={len(VERIFIED_FILING_OFFER_FIELDS)}, updated={updated}, fields={field_counts}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
