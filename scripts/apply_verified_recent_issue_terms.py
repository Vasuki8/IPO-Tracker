#!/usr/bin/env python3
"""Fill narrowly verified recent IPO issue size/composition gaps.

This is a conservative bridge for finalized P2 offer terms while SEBI's PDF host
is intermittently presenting an incomplete TLS chain to GitHub-hosted runners.
It never disables TLS verification and never overwrites populated exchange data.

Each registry entry requires exact record id, symbol, company identity and open
date. Values are taken from final IPO/RHP-derived issue disclosures and retain
the verification page in record provenance. When official automated feeds later
publish the same terms they remain available for independent validation.
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


def _entry(
    company: str,
    symbol: str,
    open_date: str,
    total: float,
    fresh: float,
    ofs: float,
    source_name: str,
    source_url: str,
) -> dict[str, Any]:
    return {
        "company": company,
        "symbol": symbol,
        "openDate": open_date,
        "issueSizeCr": total,
        "freshIssueCr": fresh,
        "ofsCr": ofs,
        "sourceName": source_name,
        "sourceUrl": source_url,
        "sourceKind": "validated-final-ipo-terms",
    }


VERIFIED_RECENT_ISSUE_TERMS: dict[str, dict[str, Any]] = {
    "sunshine": _entry(
        "Sunshine Pictures Limited", "SUNSHINE", "2026-08-18", 282.14, 172.80, 109.34,
        "Sunshine Pictures final IPO terms",
        "https://economictimes.indiatimes.com/sunshine-pictures-ltd/ipos/companyid-2252698.cms",
    ),
    "symbiotec": _entry(
        "Symbiotec Pharmalab Limited", "SYMBIOTEC", "2026-08-24", 1757.00, 150.00, 1607.00,
        "Symbiotec Pharmalab final IPO terms",
        "https://www.equentis.com/ipos/symbiotec-pharma-ipo_36114",
    ),
    "lumino": _entry(
        "Lumino Industries Limited", "LUMINO", "2026-08-27", 700.00, 500.00, 200.00,
        "Lumino Industries final IPO terms",
        "https://economictimes.indiatimes.com/lumino-industries-ltd/ipos/companyid-2253079.cms",
    ),
    "abh": _entry(
        "ABH Healthcare Limited", "ABH", "2026-08-24", 34.98, 34.98, 0.00,
        "ABH Healthcare final IPO terms",
        "https://economictimes.indiatimes.com/abh-healthcare-ltd/ipos/companyid-2468180.cms",
    ),
    "ashutosh": _entry(
        "Ashutosh Fibre Limited", "ASHUTOSH", "2026-08-31", 56.35, 56.35, 0.00,
        "Ashutosh Fibre final IPO terms",
        "https://www.moneycontrol.com/ipo/ashutosh-fibre-ltd-ipo-afl05-ipodetail",
    ),
    "horizonind": _entry(
        "Horizon Industrial Parks Limited", "HORIZONIND", "2026-08-17", 2600.00, 2600.00, 0.00,
        "Horizon Industrial Parks RHP-derived IPO terms",
        "https://groww.in/blog/horizon-industrial-parks-ipo-to-open-on-august-17-2026",
    ),
    "madhurknit": _entry(
        "Madhur Knit Crafts Limited", "MADHURKNIT", "2026-08-24", 53.27, 53.27, 0.00,
        "Madhur Knit Crafts final IPO terms",
        "https://www.business-standard.com/markets/ipo/madhur-knit-crafts-ltd-ipo-96159",
    ),
    "perniaspop": _entry(
        "Purple Style Labs Limited", "PERNIASPOP", "2026-08-31", 680.00, 680.00, 0.00,
        "Purple Style Labs RHP-derived IPO terms",
        "https://www.merchantbanker.in/blog/ipo-details/purple-style-labs-limited-ipo-analysis",
    ),
    "qualiance": _entry(
        "Qualiance International Limited", "QUALIANCE", "2026-09-04", 45.11, 45.11, 0.00,
        "Qualiance International final IPO terms",
        "https://www.moneycontrol.com/ipo/qualiance-international-qil-ipodetail",
    ),
    "momsbelief": _entry(
        "Rays of Belief Limited- For Profit Social Enterprise (FPSE)", "MOMSBELIEF", "2026-09-01", 125.00, 125.00, 0.00,
        "Rays of Belief final IPO terms",
        "https://www.business-standard.com/markets/ipo/rays-of-belief-ltd-ipo-96457",
    ),
    "shankesh": _entry(
        "Shankesh Jewellers Limited", "SHANKESH", "2026-08-18", 367.18, 274.18, 93.00,
        "Shankesh Jewellers final IPO terms",
        "https://www.muthootsecurities.com/IPO/IPO-Synopsis/Shankesh-Jewellers-Ltd/2/96152",
    ),
    "shantiinor": _entry(
        "Shanti Inorganics Limited", "SHANTIINOR", "2026-08-31", 47.24, 47.24, 0.00,
        "Shanti Inorganics final IPO terms",
        "https://www.moneycontrol.com/ipo/shanti-inorganics-sil34-ipodetail/",
    ),
    "skytech": _entry(
        "Skytech Infinite Platform Limited", "SKYTECH", "2026-08-14", 22.68, 22.68, 0.00,
        "Skytech Infinite Platform final IPO terms",
        "https://economictimes.indiatimes.com/skytech-infinite-platform-ltd/ipos/companyid-2467594.cms",
    ),
    "sumax": _entry(
        "Sumax Engineering Limited", "SUMAX", "2026-08-25", 53.40, 43.34, 10.06,
        "Sumax Engineering RHP-derived IPO terms",
        "https://www.merchantbanker.in/blog/ipo-details/sumax-engineering-limited-ipo-details",
    ),
}


def _identity_matches(record: dict[str, Any], entry: dict[str, Any]) -> bool:
    record_id = str(record.get("id") or "")
    if record_id not in VERIFIED_RECENT_ISSUE_TERMS:
        return False
    if str(record.get("symbol") or "").upper() != str(entry.get("symbol") or "").upper():
        return False
    if core.iso_date(record.get("openDate")) != entry.get("openDate"):
        return False
    return core.canonical_company(record.get("company")) == core.canonical_company(entry.get("company"))


def apply_verified_issue_terms(record: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    """Fill missing finalized issue terms only after strict identity checks."""
    if not _identity_matches(record, entry):
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
        record["issueSizeCr"] = round(total, 4)
        changed.append("issueSizeCr")
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
            "sourceBasis": "finalized IPO terms",
        }
        changed.append("issueComposition")

    if not changed:
        return []

    source = core.source_stamp(
        str(entry.get("sourceName") or "Verified final IPO terms"),
        str(entry.get("sourceUrl") or ""),
        str(entry.get("sourceKind") or "validated-final-ipo-terms"),
    )
    sources = [s for s in (record.get("sources") or []) if isinstance(s, dict)]
    sources = [s for s in sources if str(s.get("name") or "") != source["name"]]
    sources.append(source)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    observation = dict((record.get("observations") or {}).get("VerifiedIssueTerms") or {})
    observation.update({
        "issueSizeCr": round(total, 4),
        "freshIssueCr": round(fresh, 4),
        "ofsCr": round(ofs, 4),
        "openDate": entry.get("openDate"),
        "sourceUrl": entry.get("sourceUrl"),
        "sourceKind": entry.get("sourceKind"),
    })
    record.setdefault("observations", {})["VerifiedIssueTerms"] = observation
    record["validation"] = core.build_validation(record)
    return changed


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [r for r in payload.get("ipos") or [] if isinstance(r, dict)]
    by_id = {str(r.get("id") or ""): r for r in records}

    updated = 0
    field_counts: dict[str, int] = {}
    for record_id, entry in VERIFIED_RECENT_ISSUE_TERMS.items():
        record = by_id.get(record_id)
        if not record:
            print(f"Verified issue terms: missing record {record_id}")
            continue
        changed = apply_verified_issue_terms(record, entry)
        if not changed:
            continue
        updated += 1
        for field in changed:
            field_counts[field] = field_counts.get(field, 0) + 1
        print(
            f"Verified issue terms: {record_id} issueSizeCr={record.get('issueSizeCr')} "
            f"freshIssueCr={record.get('freshIssueCr')} ofsCr={record.get('ofsCr')} "
            f"changed={','.join(changed)}"
        )

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["verified-recent-issue-terms"] = {
        "ok": True,
        "entries": len(VERIFIED_RECENT_ISSUE_TERMS),
        "updated": updated,
        "fields": field_counts,
        "checkedAt": core.now_ist().isoformat(timespec="seconds"),
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Verified issue terms: entries={len(VERIFIED_RECENT_ISSUE_TERMS)}, updated={updated}, fields={field_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
