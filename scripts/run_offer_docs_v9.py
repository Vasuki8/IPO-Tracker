#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v9.

v9 keeps v8's extraction and independent deep-page budgets, and hardens offer-
document selection. SEBI publishes addenda, corrigenda and public announcements
after an RHP; those supplemental PDFs can contain "RHP" in their title and a
newer filing date, but they are not substitutes for the actual offer document.

v9 excludes supplemental notices from primary offer-document selection. If a
record has only supplemental notices, no document is selected rather than
extracting incomplete facts from a notice. The SEBI link resolver separately
recovers the canonical RHP filing pages for known priority gaps, and those
canonical links are re-resolved safely from the latest data baseline.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from parser_loader import isolated_module
v8 = isolated_module("run_offer_docs_v8")

base = v8.base
PARSER_VERSION = 9

_SUPPLEMENTAL_TYPES = {"ADDENDUM", "CORRIGENDUM", "ANNOUNCEMENT", "ADVERTISEMENT"}
_SUPPLEMENTAL_MARKERS = (
    "ADDENDUM",
    "CORRIGENDUM",
    "PUBLIC ANNOUNCEMENT",
    "PRE-ISSUE ADVERTISEMENT",
    "PRE ISSUE ADVERTISEMENT",
    "PRICE BAND ADVERTISEMENT",
)


def is_supplemental_document(doc: dict) -> bool:
    typ = str(doc.get("type") or "").strip().upper()
    if typ in _SUPPLEMENTAL_TYPES:
        return True
    title = str(doc.get("title") or "").strip().upper()
    return any(marker in title for marker in _SUPPLEMENTAL_MARKERS)


def choose_document(record):
    """Select only a real offer document, never a supplemental notice."""
    primary_docs = [
        doc
        for doc in (record.get("documents") or [])
        if isinstance(doc, dict) and not is_supplemental_document(doc)
    ]
    if not primary_docs:
        return None
    shadow = dict(record)
    shadow["documents"] = primary_docs
    return v8.choose_document(shadow)


base.choose_document = choose_document
base.PARSER_VERSION = PARSER_VERSION

parse_document_text = base.parse_document_text
extract_promoter_shareholding = v8.extract_promoter_shareholding
extract_financials = v8.extract_financials
extract_targeted_pdf_text = v8.extract_targeted_pdf_text
extract_pdf_text = v8.extract_pdf_text
apply_enrichment = v8.apply_enrichment
download_pdf = v8.download_pdf


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
