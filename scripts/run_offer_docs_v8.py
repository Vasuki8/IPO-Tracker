#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v8.

v8 keeps v7's real-world Promoter + Promoter Group ownership parsing and fixes
long-document page selection.  v5-v7 ranked financial and shareholding pages in
one shared pool, so a large RHP could spend the entire deep-page budget on
financial pages and never pass the strongest ownership page to the parser.

v8 ranks financial and shareholding pages independently and gives each section
its own bounded quota.  High-confidence ownership layouts observed in official
prospectuses receive a page-selection bonus, while the actual extraction rules
remain the conservative v7 rules.
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

from parser_loader import isolated_module
v7 = isolated_module("run_offer_docs_v7")

base = v7.base
PARSER_VERSION = 8
v5 = v7.v6.v5

_ORIGINAL_EXTRACT_PDF_TEXT = v5._ORIGINAL_EXTRACT_PDF_TEXT


def _shareholding_page_score(text: str) -> int:
    """Score ownership pages, strongly preferring explicit combined evidence."""
    score = v5._shareholding_page_score(text)
    if not text:
        return score

    flat = re.sub(r"\s+", " ", text).strip()
    if re.search(
        r"(?:\(\s*A\s*\)|\bA\b)\s*Promoters?\s+(?:and|&|/)\s+Promoter\s+Group",
        flat,
        re.I,
    ):
        score += 40

    if re.search(
        r"(?:Sub[-\s]*total|Total)\s*\(\s*A\s*\).{0,2600}?"
        r"(?:Sub[-\s]*total|Total)\s*\(\s*B\s*\)",
        flat,
        re.I,
    ):
        score += 35

    if re.search(
        r"Promoters?.{0,800}?Promoter\s+Group",
        flat,
        re.I,
    ) and re.search(r"pre[-\s]?(?:offer|issue|ipo)", flat, re.I):
        score += 18

    if re.search(
        r"Promoters?.{0,260}?Promoter\s+Group.{0,260}?collectively\s+(?:hold|holds|held)",
        flat,
        re.I,
    ):
        score += 25
    return score


def extract_targeted_pdf_text(
    data: bytes,
    base_text: str,
    *,
    need_financials: bool = True,
    need_shareholding: bool = True,
    max_scan_pages: int = 520,
    max_hits: int = 16,
    context_pages: int = 2,
):
    """Append deep pages using independent financial/shareholding quotas."""
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            pass

    page_count = len(reader.pages)
    first_pages = min(30, page_count)
    if page_count <= first_pages or not (need_financials or need_shareholding):
        return base_text, first_pages, page_count

    stop_at = min(page_count, max_scan_pages)
    financial_scores: list[tuple[int, int]] = []
    shareholding_scores: list[tuple[int, int]] = []
    cache: dict[int, str] = {}

    for idx in range(first_pages, stop_at):
        try:
            page_text = reader.pages[idx].extract_text() or ""
        except Exception:
            page_text = ""
        cache[idx] = page_text

        if need_financials:
            score = v5._financial_page_score(page_text)
            if score > 0:
                financial_scores.append((score, idx))
        if need_shareholding:
            score = _shareholding_page_score(page_text)
            if score > 0:
                shareholding_scores.append((score, idx))

    selected_centers: set[int] = set()
    if need_financials:
        financial_scores.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected_centers.update(idx for _score, idx in financial_scores[:max_hits])
    if need_shareholding:
        shareholding_scores.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected_centers.update(idx for _score, idx in shareholding_scores[:max_hits])

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
    base_text, pages_read, page_count = _ORIGINAL_EXTRACT_PDF_TEXT(data)
    if page_count <= pages_read:
        return base_text, pages_read, page_count
    return extract_targeted_pdf_text(
        data,
        base_text,
        need_financials=True,
        need_shareholding=True,
    )


# Preserve v7's extraction semantics and replace only the deep-page selector.
base.extract_promoter_shareholding = v7.extract_promoter_shareholding
base.extract_financials = v7.extract_financials
base.extract_pdf_text = extract_pdf_text
base.extract_targeted_pdf_text = extract_targeted_pdf_text
base.PARSER_VERSION = PARSER_VERSION

parse_document_text = base.parse_document_text
extract_promoter_shareholding = v7.extract_promoter_shareholding
extract_financials = v7.extract_financials
choose_document = v7.choose_document
apply_enrichment = v7.apply_enrichment
download_pdf = v7.download_pdf


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
