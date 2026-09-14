#!/usr/bin/env python3
"""Run validated issuer/exchange offer-document fallbacks with parser v12.

The legacy runner owns the explicit document allow-list and provenance rewrites.
This wrapper only upgrades parsing to v12 and adds fill-only lot/price merging,
so the exact-host, PDF-magic and issuer-identity gates remain unchanged.
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
parser_v12 = isolated_module("run_offer_docs_v12")

base = legacy.base

base.parser_v4 = parser_v12
base.PARSER_VERSION = parser_v12.PARSER_VERSION
base._extract_targeted_full_text = parser_v12.extract_targeted_pdf_text

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
            "parserVersion": parser_v12.PARSER_VERSION,
            "source": source_name,
        }
        if lot_size is not None:
            observation["lotSize"] = lot_size
        if price_band:
            observation["priceBand"] = price_band
        record.setdefault("observations", {})["Offer-document"] = observation

    extraction = record.get("issuerDocumentExtraction")
    if isinstance(extraction, dict):
        extraction["parserVersion"] = parser_v12.PARSER_VERSION
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
