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

import run_issuer_offer_docs as legacy  # noqa: E402
import run_offer_docs_v13 as parser_v13  # noqa: E402

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
