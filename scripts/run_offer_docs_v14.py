#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v14.

v14 keeps v13's bounded deep-page selection and all existing conservative
recognition/fill-only rules. It adds one narrow cover-page normalization for
intermediary tables observed in official final prospectuses where the table
headers use abbreviated labels such as ``NAME AND LOGO OF BRLM`` or
``NAME AND LOGO OF THE REGISTRAR``.

The v1 intermediary extractor already requires a legal-entity suffix and bounded
BOOK RUNNING LEAD MANAGER / REGISTRAR sections. The abbreviated table header can
be captured as part of the same legal-entity candidate and is then rejected by
its safety filter. v14 strips only those exact table-header phrases before
re-running that established extractor; it does not relax issuer identity, legal
entity, source, or fill-only gates.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from parser_loader import isolated_module
v13 = isolated_module("run_offer_docs_v13")

base = v13.base
PARSER_VERSION = 14
_ORIGINAL_PARSE_DOCUMENT_TEXT = v13.parse_document_text

_COVER_INTERMEDIARY_HEADERS = (
    re.compile(
        r"NAME\s+AND\s+LOGO\s+OF\s+(?:THE\s+)?BRLM\s+"
        r"CONTACT\s+PERSON\s+EMAIL\s+AND\s+TELEPHONE",
        re.I,
    ),
    re.compile(
        r"NAME\s+AND\s+LOGO\s+OF\s+THE\s+REGISTRAR\s+"
        r"CONTACT\s+PERSON\s+EMAIL\s+AND\s+TELEPHONE",
        re.I,
    ),
)


def normalize_cover_intermediary_headers(text: str) -> str:
    """Remove only known cover-table labels that contaminate entity matching."""
    normalized = text or ""
    for pattern in _COVER_INTERMEDIARY_HEADERS:
        normalized = pattern.sub(" ", normalized)
    return normalized


def parse_document_text(text: str, price_band=None):
    parsed = dict(_ORIGINAL_PARSE_DOCUMENT_TEXT(text, price_band) or {})

    # Only invoke the fallback when v13 missed an intermediary. All other parsed
    # fields remain exactly as recognized by v13.
    if not parsed.get("leadManagers") or not parsed.get("registrar"):
        cleaned = normalize_cover_intermediary_headers(text)
        leads, registrar = base.extract_intermediaries(cleaned)
        fields = list(parsed.get("extractedFields") or [])

        if not parsed.get("leadManagers") and leads:
            parsed["leadManagers"] = leads
            if "leadManagers" not in fields:
                fields.append("leadManagers")

        if not parsed.get("registrar") and registrar:
            parsed["registrar"] = registrar
            if "registrar" not in fields:
                fields.append("registrar")

        parsed["extractedFields"] = fields

    return parsed


def apply_enrichment(record, parsed, doc, pdf_hash, pages_read, page_count):
    """Retain v13 fill-only semantics while recording parser v14 provenance."""
    v13.apply_enrichment(record, parsed, doc, pdf_hash, pages_read, page_count)
    extraction = record.get("offerDocumentExtraction")
    if isinstance(extraction, dict):
        extraction["parserVersion"] = PARSER_VERSION
    observation = (record.get("observations") or {}).get("SEBI-offer")
    if isinstance(observation, dict):
        observation["parserVersion"] = PARSER_VERSION


base.parse_document_text = parse_document_text
base.apply_enrichment = apply_enrichment
base.PARSER_VERSION = PARSER_VERSION

extract_targeted_pdf_text = v13.extract_targeted_pdf_text
extract_pdf_text = v13.extract_pdf_text
extract_lot_size = v13.extract_lot_size
extract_price_band = v13.extract_price_band
extract_promoter_shareholding = v13.extract_promoter_shareholding
extract_financials = v13.extract_financials
choose_document = v13.choose_document
download_pdf = v13.download_pdf


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
