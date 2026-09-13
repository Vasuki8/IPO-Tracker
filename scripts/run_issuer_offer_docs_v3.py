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
