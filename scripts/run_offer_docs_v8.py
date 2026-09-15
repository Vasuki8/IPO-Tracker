#!/usr/bin/env python3
"""Compatibility alias for legacy offer parser version 8."""
import legacy_offer_parser as _canonical
from legacy_offer_parser import *  # noqa: F401,F403

PARSER_VERSION = 8
PdfReader = _canonical.PdfReader
_shareholding_page_score = _canonical._shareholding_page_score
_financial_page_score = _canonical._financial_page_score


class _BaseProxy:
    PARSER_VERSION = PARSER_VERSION

    def __getattr__(self, name):
        return getattr(_canonical.base, name)


base = _BaseProxy()


def extract_targeted_pdf_text(
    data,
    base_text,
    *,
    need_financials=True,
    need_shareholding=True,
    need_offer_terms=True,
    max_scan_pages=520,
    max_hits=16,
    term_hits=12,
    context_pages=2,
):
    previous = _canonical.PdfReader
    _canonical.PdfReader = PdfReader
    try:
        return _canonical.extract_targeted_pdf_text(
            data,
            base_text,
            need_financials=need_financials,
            need_shareholding=need_shareholding,
            need_offer_terms=need_offer_terms,
            max_scan_pages=max_scan_pages,
            max_hits=max_hits,
            term_hits=term_hits,
            context_pages=context_pages,
        )
    finally:
        _canonical.PdfReader = previous


if __name__ == "__main__":
    raise SystemExit(main())
