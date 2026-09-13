#!/usr/bin/env python3
"""Fill narrowly verified IPO lot sizes with strict identity guards.

This registry is a conservative bridge for final public-issue terms that are not
currently exposed by the automated exchange-detail feeds. Entries are fill-only
and require an exact record id, symbol, open date and company identity, so a term
cannot cross-match another issue. Every entry keeps the page used to verify the
announced/final lot for provenance.

Primary exchange/SEBI automation still gets first chance to populate the field;
this script only fills records whose lotSize is still missing.
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


def _entry(company: str, symbol: str, open_date: str, lot: int, source_name: str, source_url: str, source_kind: str = "validated-market-terms") -> dict[str, Any]:
    return {
        "company": company,
        "symbol": symbol,
        "openDate": open_date,
        "lotSize": lot,
        "sourceName": source_name,
        "sourceUrl": source_url,
        "sourceKind": source_kind,
    }


VERIFIED_LOT_SIZES: dict[str, dict[str, Any]] = {
    # P1 upcoming issues: issuer-hosted verification.
    "jsipl": _entry("Jindal Supreme (India) Limited", "JSIPL", "2026-09-16", 161, "Jindal Supreme IPO terms", "https://jindalsupreme.com/investor-relations/", "issuer-filing"),
    "ssretail": _entry("SS Retail Limited", "SSRETAIL", "2026-09-16", 35, "SS Retail IPO terms", "https://ssmobile.com/aboutus/investor/keyDocuments.php", "issuer-filing"),

    # P2 recent issues. These final bid lots are cross-checked against the
    # announced issue terms / final RHP-derived market pages. The source URL is
    # retained explicitly rather than presenting the value as exchange-derived.
    "abh": _entry("ABH Healthcare Limited", "ABH", "2026-08-24", 1200, "ABH Healthcare final IPO terms", "https://www.business-standard.com/markets/ipo/abh-healthcare-ltd-ipo-95591"),
    "annu": _entry("Annu Projects Limited", "ANNU", "2026-08-25", 151, "Annu Projects final IPO terms", "https://www.finsso.co.in/ipo_detail.php?ipo=Mzg1"),
    "ashutosh": _entry("Ashutosh Fibre Limited", "ASHUTOSH", "2026-08-31", 1200, "Ashutosh Fibre final IPO terms", "https://www.plindia.com/ipo/ashutosh-fibre-limited-ipo/"),
    "augmont": _entry("Augmont Enterprises Limited", "AUGMONT", "2026-08-21", 19, "Augmont Enterprises final IPO terms", "https://www.rrfinance.com/OurProducts/PublicIssues/Ongoing-Public-Issue-Details.aspx?sch_code=SCH-1457"),
    "deepa": _entry("Deepa Jewellers Limited", "DEEPA", "2026-09-01", 84, "Deepa Jewellers price-band announcement", "https://www.orientpublication.com/2026/08/deepa-jewellers-limiteds-initial-public.html"),
    "esds": _entry("ESDS Software Solution Limited", "ESDS", "2026-08-28", 34, "ESDS final IPO terms", "https://www.plindia.com/ipo/esds-software-solution-limited-ipo/"),
    "gaja": _entry("Gaja Alternative Asset Management Limited", "GAJA", "2026-08-19", 93, "Gaja Alternative final IPO terms", "https://mtinews.in/gaja-alternative-asset-management-limiteds-initial-public-offer-to-open-on-wednesday-august-19-2026/?amp=1"),
    "horizonind": _entry("Horizon Industrial Parks Limited", "HORIZONIND", "2026-08-17", 250, "Horizon Industrial Parks IPO terms", "https://www.hiparks.com/press-release/horizon-industrial-parks-limiteds-initial-public-offer-to-open-on-monday-august-17-2026", "issuer-announcement"),
    "htel": _entry("Hy-Tech Engineers Limited", "HTEL", "2026-08-24", 283, "Hy-Tech Engineers final IPO terms", "https://www.merchantbanker.in/blog/ipo-details/hy-tech-engineers-limited-ipo-details"),
    "kanohar": _entry("Kanohar Electricals Limited", "KANOHAR", "2026-09-08", 23, "Kanohar Electricals final IPO terms", "https://www.finsso.co.in/ipo_detail.php?ipo=Mzkz"),
    "lalithaa": _entry("Lalithaa Jewellery Mart Limited", "LALITHAA", "2026-08-17", 74, "Lalithaa Jewellery Mart price-band announcement", "https://www.artofjewellery.com/NewsMore?id=1328"),
    "lumino": _entry("Lumino Industries Limited", "LUMINO", "2026-08-27", 182, "Lumino Industries price-band announcement", "https://www.orientpublication.com/2026/08/lumino-industries-limiteds-initial.html?m=1"),
    "madhurknit": _entry("Madhur Knit Crafts Limited", "MADHURKNIT", "2026-08-24", 1200, "Madhur Knit Crafts final IPO terms", "https://www.business-standard.com/markets/ipo/madhur-knit-crafts-ltd-ipo-96159"),
    "pranav": _entry("Pranav Constructions Limited", "PRANAV", "2026-09-07", 120, "Pranav Constructions price-band announcement", "https://english.metrovaartha.com/economy/market/pranav-constructions-limiteds-initial-public-offering-to-open-on-monday-september-07-2026-price-band-set-at-118-to-124-per-equity-share"),
    "priority": _entry("Priority Jewels Limited", "PRIORITY", "2026-08-28", 75, "Priority Jewels price-band announcement", "https://mtinews.in/priority-jewels-limiteds-initial-public-offering-to-open-on-friday-august-28-2026-price-band-set-at-rs-190-rs-200-per-equity-shares-of-face-value-of-rs-10-each/?amp=1"),
    "perniaspop": _entry("Purple Style Labs Limited", "PERNIASPOP", "2026-08-31", 26, "Purple Style Labs price-band announcement", "https://www.pninews.com/purple-style-labs-limiteds-initial-public-offering-ipo-opens-on-monday-august-31-2026-price-band-has-been-fixed-at-rs-546-to-rs-575-per-equity-share/"),
    "qualiance": _entry("Qualiance International Limited", "QUALIANCE", "2026-09-04", 1000, "Qualiance International final IPO terms", "https://www.finsso.co.in/sme_ipo_detail.php?ipo=MTgwNA%3D%3D"),
    "momsbelief": _entry("Rays of Belief Limited- For Profit Social Enterprise (FPSE)", "MOMSBELIEF", "2026-09-01", 62, "Rays of Belief final IPO terms", "https://www.rrfinance.com/OurProducts/PublicIssues/Ongoing-Public-Issue-Details.aspx?sch_code=SCH-1471"),
    "shankesh": _entry("Shankesh Jewellers Limited", "SHANKESH", "2026-08-18", 160, "Shankesh Jewellers final IPO terms", "https://anandrathi.com/blog/shankesh-jewellers-ipo-details"),
    "shantiinor": _entry("Shanti Inorganics Limited", "SHANTIINOR", "2026-08-31", 1600, "Shanti Inorganics final IPO terms", "https://idbidirect.in/Markets/ipo/Iposynopsis.aspx?code=95929&compname=Shanti-Inorganics-Ltd&pagename=ForthComing-Issues"),
    "skytech": _entry("Skytech Infinite Platform Limited", "SKYTECH", "2026-08-14", 1600, "Skytech Infinite Platform final IPO terms", "https://www.vocartsecurities.com/ipo-details?id=219"),
    "skyways": _entry("Skyways Air Services Limited", "SKYWAYS", "2026-08-24", 100, "Skyways Air Services final IPO terms", "https://www.rrfinance.com/OurProducts/PublicIssues/Ongoing-Public-Issue-Details.aspx?Pname=Skyways+Air+Services+Limited&sch_code=SCH-1458"),
    "sumax": _entry("Sumax Engineering Limited", "SUMAX", "2026-08-25", 1200, "Sumax Engineering final IPO terms", "https://www.livemint.com/market/ipo/sumax-engineering-ltd-ipo-ipo1292"),
    "sunshine": _entry("Sunshine Pictures Limited", "SUNSHINE", "2026-08-18", 41, "Sunshine Pictures final IPO terms", "https://zerodha.com/ipo/413196/sunshine-pictures/"),
    "symbiotec": _entry("Symbiotec Pharmalab Limited", "SYMBIOTEC", "2026-08-24", 15, "Symbiotec Pharmalab final IPO terms", "https://www.rrfinance.com/OurProducts/PublicIssues/Ongoing-Public-Issue-Details.aspx?Pname=Symbiotec+Pharmalab+Limited&sch_code=SCH-1460"),
    "arcil": _entry("Asset Reconstruction Company (India) Limited", "ARCIL", "2026-09-09", 107, "ARCIL final IPO terms", "https://www.ifinltd.in/ipo/new-issue-details/1731103/47"),
    "glasswall": _entry("Glass Wall Systems (India) Limited", "GLASSWALL", "2026-09-08", 82, "Glass Wall Systems price-band announcement", "https://mtinews.in/glass-wall-systems-india-limiteds-initial-public-offering-to-open-on-tuesday-september-8-2026-price-band-of-%E2%82%B9172-%E2%82%B9182-per-equity-share-of-face-value-of/"),
    "karamtara": _entry("Karamtara Engineering Limited", "KARAMTARA", "2026-09-09", 59, "Karamtara Engineering final IPO terms", "https://www.plindia.com/ipo/karamtara-engineering-limited-ipo/"),
    "lccproject": _entry("LCC Projects Limited", "LCCPROJECT", "2026-09-09", 102, "LCC Projects final IPO terms", "https://www.idbidirect.in/Markets/ipo/Iposynopsis.aspx?code=85600&compname=LCC-Projects-Ltd&pagename=ForthComing-Issues"),
    "mpimanipal": _entry("Manipal Payment and Identity Solutions Limited", "MPIMANIPAL", "2026-09-09", 44, "Manipal Payment and Identity Solutions final IPO terms", "https://www.acml.in/market/IPO/NewIssueDetail/1731106"),
    "prasolchem": _entry("Prasol Chemicals Limited", "PRASOLCHEM", "2026-09-08", 22, "Prasol Chemicals final IPO terms", "https://www.finsso.co.in/ipo_detail.php?ipo=Mzk3"),
    "steamhouse": _entry("Steamhouse India Limited", "STEAMHOUSE", "2026-09-09", 185, "Steamhouse India final IPO terms", "https://ipocentral.in/steamhouse-india-ipo-gmp-price-date-allotment/"),
    "tempsens": _entry("Tempsens Instruments (India) Limited", "TEMPSENS", "2026-08-20", 50, "Tempsens Instruments final IPO terms", "https://www.sushilfinance.com/blogs/IPO-Note/Tempsens-Instruments-India-Limited-IPO"),
    "rentomojo": _entry("Rentomojo Limited", "RENTOMOJO", "2026-09-09", 37, "Rentomojo price-band announcement", "https://english.metrovaartha.com/economy/market/rentomojo-limiteds-initial-public-offer-to-open-on-september-09-2026"),
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
        str(entry.get("sourceName") or "Verified IPO terms"),
        str(entry.get("sourceUrl") or ""),
        str(entry.get("sourceKind") or "validated-market-terms"),
    )
    sources = [s for s in (record.get("sources") or []) if isinstance(s, dict)]
    sources = [s for s in sources if str(s.get("name") or "") != source["name"]]
    sources.append(source)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    obs = dict((record.get("observations") or {}).get("VerifiedTerms") or {})
    obs.update({
        "lotSize": lot,
        "openDate": entry.get("openDate"),
        "sourceUrl": entry.get("sourceUrl"),
        "sourceKind": entry.get("sourceKind"),
    })
    record.setdefault("observations", {})["VerifiedTerms"] = obs
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

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["verified-lot-sizes"] = {
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
