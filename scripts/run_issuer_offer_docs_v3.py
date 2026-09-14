#!/usr/bin/env python3
"""Run validated issuer/exchange offer-document fallbacks with parser v13.

This keeps the exact-host, PDF-magic and issuer-identity gates from the legacy
validated-document runner, while using v13's bounded deep-page selection for bid
lot and finalized price terms. All normalized exchange fields remain fill-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from parser_loader import isolated_module
legacy = isolated_module("run_issuer_offer_docs")
from parser_loader import isolated_module
parser_v13 = isolated_module("run_offer_docs_v13")

base = legacy.base

base.parser_v4 = parser_v13
base.PARSER_VERSION = parser_v13.PARSER_VERSION
base._extract_targeted_full_text = parser_v13.extract_targeted_pdf_text

# Current P4 residuals that already have regulator-hosted final prospectuses.
# Keep these registrations explicit so every fallback still passes the base
# runner's exact-host, PDF-magic, issuer-identity and fill-only merge gates.
base.ISSUER_DOCUMENTS.update(
    {
        "leap": {
            "company": "Leap India Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786535192735.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/aug-2026/leap-india-limited-prospectus_103511.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "propshop": {
            "company": "Propshop Events and Exhibitions Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1785404948142.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/jul-2026/propshop-events-and-exhibitions-limited-prospectus_103111.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "alpinetex": {
            "company": "Alpine Texworld Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786621533716.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/aug-2026/alpine-texworld-limited-prospectus_103604.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "aastha": {
            "company": "Aastha Spintex Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1785320834804.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/jul-2026/aastha-spintex-limited-prospectus_103092.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "rambhajo": {
            "company": "Advit Jewels Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jun-2026/1782728190936.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/jun-2026/advit-jewels-limited-prospectus_102425.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "csm": {
            "company": "CSM Technologies Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1782884582544.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/jun-2026/csm-technologies-limited-prospectus_102473.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "cleanmax": {
            "company": "Clean Max Enviro Energy Solutions Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1772097780247.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/feb-2026/clean-max-enviro-energy-solutions-limited-prospectus_99987.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "gspcrop": {
            "company": "GSP Crop Science Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/apr-2026/1776851251292.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/mar-2026/gsp-crop-science-limited-prospectus_101040.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "hexagon": {
            "company": "Hexagon Nutrition Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jun-2026/1781074175044.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/jun-2026/hexagon-nutrition-limited-prospectus_101991.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "cmpdi": {
            "company": "Central Mine Planning & Design Institute Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/apr-2026/1775128471900.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/apr-2026/central-mine-planning-and-design-institute-limited-prospectus_100707.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "innovision": {
            "company": "Innovision Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/mar-2026/1774008043195.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/mar-2026/innovision-limited-prospectus_100489.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "jnpr": {
            "company": "Juniper Green Energy Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787054356074.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/aug-2026/juniper-green-energy-limited-prospectus_103747.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "aye": {
            "company": "Aye Finance Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1770879625663.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/feb-2026/aye-finance-limited-prospectus_99708.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "cmll": {
            "company": "Caliber Mining and Logistics Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1784698849378.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/jul-2026/caliber-mining-and-logistics-limited-prospectus_102990.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "lcl": {
            "company": "Lohia Corp Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1785231911524.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/jul-2026/lohia-corp-limited-prospectus_103075.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "mvelectro": {
            "company": "MV Electrosystems Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785823205427.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/aug-2026/mv-electrosystems-limited-prospectus_103331.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "manipalhos": {
            "company": "Manipal Health Enterprises Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785732646843.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/aug-2026/manipal-health-enterprises-limited-prospectus_103300.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "ompower": {
            "company": "Om Power Transmission Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/apr-2026/1776237369286.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/apr-2026/om-power-transmission-limited-prospectus_100928.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "kissht": {
            "company": "Onemi Technology Solutions Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jun-2026/1781763357383.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/may-2026/onemi-technology-solutions-limited-prospectus_102192.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "kusumgar": {
            "company": "Kusumgar Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1784001026291.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/jul-2026/kusumgar-limited-prospectus_102792.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "knack": {
            "company": "Knack Packaging Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1783319397647.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/jul-2026/knack-packaging-limited-prospectus_102599.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "pngsreva": {
            "company": "PNGS Reva Diamond Jewellery Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/mar-2026/1772433551022.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/feb-2026/pngs-reva-diamond-jewellery-limited_100068.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
    }
)

_ORIGINAL_MERGE = base.merge_issuer_enrichment


def merge_validated_terms(
    record,
    parsed,
    doc,
    *,
    pdf_hash,
    pages_read,
    page_count,
):
    changed = _ORIGINAL_MERGE(
        record,
        parsed,
        doc,
        pdf_hash=pdf_hash,
        pages_read=pages_read,
        page_count=page_count,
    )

    lot_size = parsed.get("lotSize")
    price_band = parsed.get("priceBand")
    term_changes = []
    if record.get("lotSize") is None and lot_size is not None:
        record["lotSize"] = lot_size
        term_changes.append("lotSize")
    if record.get("priceBand") in (None, {}, []) and price_band:
        record["priceBand"] = price_band
        term_changes.append("priceBand")

    if lot_size is not None or price_band:
        source_name = str(
            doc.get("extractionSource")
            or doc.get("documentSource")
            or "Issuer website"
        )
        observation = {
            "documentUrl": doc.get("url"),
            "documentType": doc.get("type"),
            "documentFiledDate": doc.get("filedDate"),
            "parserVersion": parser_v13.PARSER_VERSION,
            "source": source_name,
        }
        if lot_size is not None:
            observation["lotSize"] = lot_size
        if price_band:
            observation["priceBand"] = price_band
        record.setdefault("observations", {})["Offer-document"] = observation

    extraction = record.get("issuerDocumentExtraction")
    if isinstance(extraction, dict):
        extraction["parserVersion"] = parser_v13.PARSER_VERSION
        extraction["extractedFields"] = parsed.get("extractedFields") or []
        if term_changes:
            existing = list(extraction.get("changedFields") or [])
            extraction["changedFields"] = list(dict.fromkeys(existing + term_changes))

    return list(dict.fromkeys(list(changed or []) + term_changes))


base.merge_issuer_enrichment = merge_validated_terms


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
