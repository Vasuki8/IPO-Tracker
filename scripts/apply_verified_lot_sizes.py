#!/usr/bin/env python3
"""Fill narrowly verified upcoming IPO lot sizes with strict identity guards.

This registry is intentionally small and temporary in scope: it is for public
issue terms that have been announced by the issuer but are not yet available
through the automated exchange-detail feed. Entries are fill-only and require
an exact record id, symbol and open date so they cannot cross-match another
issue. Each value carries an issuer IPO-document source page for provenance.
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

VERIFIED_LOT_SIZES: dict[str, dict[str, Any]] = {
    "jsipl": {
        "company": "Jindal Supreme (India) Limited",
        "symbol": "JSIPL",
        "openDate": "2026-09-16",
        "lotSize": 161,
        "sourceName": "Jindal Supreme IPO terms",
        "sourceUrl": "https://jindalsupreme.com/investor-relations/",
        "sourceKind": "issuer-filing",
    },
    "ssretail": {
        "company": "SS Retail Limited",
        "symbol": "SSRETAIL",
        "openDate": "2026-09-16",
        "lotSize": 35,
        "sourceName": "SS Retail IPO terms",
        "sourceUrl": "https://ssmobile.com/aboutus/investor/keyDocuments.php",
        "sourceKind": "issuer-filing",
    },
}


def apply_verified_lot_size(record: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    """Apply one verified lot size only when all identity guards match."""
    if str(record.get("id") or "") not in VERIFIED_LOT_SIZES:
        return []
    if str(record.get("symbol") or "").upper() != str(entry.get("symbol") or "").upper():
        return []
    if core.iso_date(record.get("openDate")) != entry.get("openDate"):
        return []
    if core.canonical_company(record.get("company")) != core.canonical_company(entry.get("company")):
        return []
    if record.get("lotSize") not in (None, ""):
        return []

    lot = core.integer(entry.get("lotSize"))
    if not lot or lot <= 0:
        return []

    record["lotSize"] = lot
    band = record.get("priceBand") if isinstance(record.get("priceBand"), dict) else {}
    cap = core.number(band.get("max"))
    if cap:
        record["minInvestment"] = round(lot * cap, 2)

    source = core.source_stamp(
        str(entry.get("sourceName") or "Issuer IPO terms"),
        str(entry.get("sourceUrl") or ""),
        str(entry.get("sourceKind") or "issuer-filing"),
    )
    sources = [s for s in (record.get("sources") or []) if isinstance(s, dict)]
    sources = [s for s in sources if str(s.get("name") or "") != source["name"]]
    sources.append(source)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    obs = dict((record.get("observations") or {}).get("IssuerTerms") or {})
    obs.update({"lotSize": lot, "openDate": entry.get("openDate"), "sourceUrl": entry.get("sourceUrl")})
    record.setdefault("observations", {})["IssuerTerms"] = obs
    record["validation"] = core.build_validation(record)
    return ["lotSize"]


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [r for r in payload.get("ipos") or [] if isinstance(r, dict)]
    by_id = {str(r.get("id") or ""): r for r in records}

    updated = 0
    for record_id, entry in VERIFIED_LOT_SIZES.items():
        record = by_id.get(record_id)
        if not record:
            print(f"Verified lot registry: missing record {record_id}")
            continue
        changed = apply_verified_lot_size(record, entry)
        if changed:
            updated += 1
            print(f"Verified lot registry: {record_id} lotSize={record.get('lotSize')}")

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["verified-upcoming-lot-sizes"] = {
        "ok": True,
        "entries": len(VERIFIED_LOT_SIZES),
        "updated": updated,
        "checkedAt": core.now_ist().isoformat(timespec="seconds"),
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Verified lot registry: entries={len(VERIFIED_LOT_SIZES)}, updated={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
