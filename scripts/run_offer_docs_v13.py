#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v13.

v12 added conservative lot-size and final price-band extraction, but the PDF
reader inherited v8's deep-page selector, which only ranked financial and
shareholding pages. In many RHPs the bid-lot language lives hundreds of pages
later in Issue Procedure / Terms of the Offer, so the correct extractor never
saw the relevant text.

v13 keeps every v12 extraction/merge rule unchanged and widens only page
selection. Financial, shareholding and finalized offer-term pages are ranked
independently inside the same bounded scan. The resulting text remains a small
subset of the PDF and exchange fields remain fill-only.
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

from pypdf import PdfReader

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_offer_docs_v8 as v8  # noqa: E402
import run_offer_docs_v12 as v12  # noqa: E402

base = v12.base
PARSER_VERSION = 13
_ORIGINAL_FIRST_PAGES = v8._ORIGINAL_EXTRACT_PDF_TEXT


def _offer_term_page_score(text: str) -> int:
    """Rank pages likely to contain finalized bid-lot / price-band terms."""
    if not text:
        return 0
    flat = re.sub(r"\s+", " ", text).strip()
    score = 0

    # Exact lot terminology is the strongest signal. The extractor still makes
    # the final decision; these patterns only decide which pages to expose to it.
    if re.search(r"\bminimum\s+bid\s+lot\b", flat, re.I):
        score += 80
    if re.search(r"\bminimum\s+bid\s+quantity\b", flat, re.I):
        score += 70
    if re.search(r"\bbid\s+lot\b", flat, re.I):
        score += 55
    if re.search(r"\bmarket\s+lot\b", flat, re.I):
        score += 50
    if re.search(
        r"\bbids?\s+(?:can|may)\s+be\s+made\s+for\s+(?:a\s+)?minimum\s+of\b",
        flat,
        re.I,
    ):
        score += 45

    # Finalized pricing often appears on the cover, but some prospectuses repeat
    # it later. These signals also help recover fixed-price issues.
    if re.search(r"\bprice\s+band\b", flat, re.I):
        score += 35
    if re.search(r"\bfloor\s+price\b", flat, re.I):
        score += 25
    if re.search(r"\bcap\s+price\b", flat, re.I):
        score += 25
    if re.search(r"\b(?:issue|offer)\s+price\b", flat, re.I):
        score += 15

    # Procedure/offer headings make a weak generic price hit much more useful.
    if re.search(
        r"\b(?:issue\s+procedure|terms?\s+of\s+the\s+offer|how\s+to\s+apply|bid(?:ding)?\s+process)\b",
        flat,
        re.I,
    ):
        score += 12
    return score


def extract_targeted_pdf_text(
    data: bytes,
    base_text: str,
    *,
    need_financials: bool = True,
    need_shareholding: bool = True,
    need_offer_terms: bool = True,
    max_scan_pages: int = 520,
    max_hits: int = 16,
    term_hits: int = 12,
    context_pages: int = 2,
):
    """Append independently ranked financial/shareholding/offer-term pages."""
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            pass

    page_count = len(reader.pages)
    first_pages = min(30, page_count)
    if page_count <= first_pages or not (need_financials or need_shareholding or need_offer_terms):
        return base_text, first_pages, page_count

    stop_at = min(page_count, max_scan_pages)
    financial_scores: list[tuple[int, int]] = []
    shareholding_scores: list[tuple[int, int]] = []
    term_scores: list[tuple[int, int]] = []
    cache: dict[int, str] = {}

    for idx in range(first_pages, stop_at):
        try:
            page_text = reader.pages[idx].extract_text() or ""
        except Exception:
            page_text = ""
        cache[idx] = page_text

        if need_financials:
            score = v8.v5._financial_page_score(page_text)
            if score > 0:
                financial_scores.append((score, idx))
        if need_shareholding:
            score = v8._shareholding_page_score(page_text)
            if score > 0:
                shareholding_scores.append((score, idx))
        if need_offer_terms:
            score = _offer_term_page_score(page_text)
            if score > 0:
                term_scores.append((score, idx))

    selected_centers: set[int] = set()
    if need_financials:
        financial_scores.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected_centers.update(idx for _score, idx in financial_scores[:max_hits])
    if need_shareholding:
        shareholding_scores.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected_centers.update(idx for _score, idx in shareholding_scores[:max_hits])
    if need_offer_terms:
        term_scores.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected_centers.update(idx for _score, idx in term_scores[:term_hits])

    if not selected_centers:
        return base_text, stop_at, page_count

    selected_pages: set[int] = set()
    before = 1 if context_pages > 0 else 0
    after = max(0, context_pages)
    for center in selected_centers:
        for idx in range(max(first_pages, center - before), min(stop_at, center + after + 1)):
            selected_pages.add(idx)

    collected = [base_text]
    for idx in sorted(selected_pages):
        page_text = cache.get(idx)
        if page_text is None:
            try:
                page_text = reader.pages[idx].extract_text() or ""
            except Exception:
                page_text = ""
        if page_text.strip():
            collected.append(page_text)

    return "\n".join(collected), stop_at, page_count


def extract_pdf_text(data: bytes):
    # Read the first 30 pages once, then make one bounded deep scan that ranks all
    # three families. This avoids the double full-PDF pass a wrapper approach
    # would otherwise introduce.
    first_text, pages_read, page_count = _ORIGINAL_FIRST_PAGES(data)
    if page_count <= pages_read:
        return first_text, pages_read, page_count
    return extract_targeted_pdf_text(
        data,
        first_text,
        need_financials=True,
        need_shareholding=True,
        need_offer_terms=True,
    )


base.extract_pdf_text = extract_pdf_text
base.extract_targeted_pdf_text = extract_targeted_pdf_text
base.PARSER_VERSION = PARSER_VERSION

# v12 remains authoritative for recognition and fill-only merge semantics.
parse_document_text = v12.parse_document_text
extract_lot_size = v12.extract_lot_size
extract_price_band = v12.extract_price_band
extract_promoter_shareholding = v12.extract_promoter_shareholding
extract_financials = v12.extract_financials
choose_document = v12.choose_document
apply_enrichment = v12.apply_enrichment
download_pdf = v12.download_pdf


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
