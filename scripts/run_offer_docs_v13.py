#!/usr/bin/env python3
"""Compatibility alias for legacy offer parser version 13.

Version 13 introduced bounded deep-page offer-term discovery. The canonical
legacy parser owns that implementation now; this shim preserves the old patch
points used by regression tests and manual callers.
"""
import legacy_offer_parser as _canonical
from legacy_offer_parser import *  # noqa: F401,F403

PARSER_VERSION = 13
PdfReader = _canonical.PdfReader
_ORIGINAL_FIRST_PAGES = _canonical.base.extract_pdf_text
_offer_term_page_score = _canonical._offer_term_page_score


class _BaseProxy:
    PARSER_VERSION = PARSER_VERSION

    def __getattr__(self, name):
        return getattr(_canonical.base, name)


base = _BaseProxy()


def extract_targeted_pdf_text(data, base_text, **kwargs):
    previous = _canonical.PdfReader
    _canonical.PdfReader = PdfReader
    try:
        return _canonical.extract_targeted_pdf_text(data, base_text, **kwargs)
    finally:
        _canonical.PdfReader = previous


def extract_pdf_text(data):
    base_text, pages_read, page_count = _ORIGINAL_FIRST_PAGES(data)
    if page_count <= pages_read:
        return base_text, pages_read, page_count
    return extract_targeted_pdf_text(data, base_text)


def apply_enrichment(record, parsed, doc, pdf_hash, pages_read, page_count):
    _canonical.apply_enrichment(record, parsed, doc, pdf_hash, pages_read, page_count)
    extraction = record.get("offerDocumentExtraction")
    if isinstance(extraction, dict):
        extraction["parserVersion"] = PARSER_VERSION
    observation = (record.get("observations") or {}).get("SEBI-offer")
    if isinstance(observation, dict):
        observation["parserVersion"] = PARSER_VERSION


if __name__ == "__main__":
    raise SystemExit(main())
