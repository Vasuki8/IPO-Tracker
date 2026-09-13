#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v11.

v11 keeps v10's conservative extraction and adds two explicit combined promoter
ownership layouts observed in the remaining priority official RHPs:

* Injecto: ``Total (A) Promoter and Promoter Group ... 88.14``
* Manika: ``Total – C (A+B) ... 100.00``

Both rules require an explicit pre-Issue/pre-Offer ownership context and a
Promoter Group marker in the same bounded window. They therefore read stated
combined ownership directly and do not infer from promoter-contribution,
lock-in, director shareholding or risk-factor percentages.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_offer_docs_v10 as v10  # noqa: E402

base = v10.base
PARSER_VERSION = 11
_ORIGINAL_EXTRACT_PROMOTER_SHAREHOLDING = v10.extract_promoter_shareholding

_PRE_CONTEXT = re.compile(r"pre[-\s]?(?:issue|offer|ipo)", re.I)
_GROUP_CONTEXT = re.compile(r"promoter\s+group", re.I)


def _valid_pct(value):
    pct = base.number(value)
    if pct is None:
        return None
    pct = float(pct)
    return pct if 0 <= pct <= 100 else None


def _safe_context(flat: str, start: int, end: int) -> str | None:
    block = flat[max(0, start - 4200) : min(len(flat), end + 700)]
    if not _PRE_CONTEXT.search(block):
        return None
    if not _GROUP_CONTEXT.search(block):
        return None
    # Never accept contribution / lock-in rows as ownership percentages.
    tail = block[max(0, len(block) - 1400) :]
    if re.search(r"minimum\s+promoters?['’]?\s+contribution", tail, re.I):
        return None
    return block


def _explicit_combined_ownership(text: str):
    flat = re.sub(r"\s+", " ", base.norm_space(text)).strip()

    # Manika-style full combined row:
    # Total – C (A+B) 95,000,000 100.00 [●] [●]
    for match in re.finditer(
        r"Total\s*(?:[-–—]\s*)?C\s*\(\s*A\s*\+\s*B\s*\)\s+"
        r"[\d,]{2,}\s+(100(?:\.0+)?|\d{1,2}(?:\.\d+)?)\s*%?",
        flat,
        re.I,
    ):
        if _safe_context(flat, match.start(), match.end()) is None:
            continue
        pct = _valid_pct(match.group(1))
        if pct is not None:
            return pct

    # Injecto-style shareholding-pattern aggregate row:
    # Total (A) Promoter and Promoter Group 15 1,33,77,200 ... 88.14 ...
    # Allow a bounded set of numeric columns before the first stated percentage.
    for match in re.finditer(
        r"Total\s*\(\s*A\s*\)\s+Promoter\s+and\s+Promoter\s+Group"
        r".{0,260}?\b(100(?:\.0+)?|\d{1,2}(?:\.\d+)?)\b",
        flat,
        re.I,
    ):
        if _safe_context(flat, match.start(), match.end()) is None:
            continue
        # The first decimal/percentage-looking value after the combined label is
        # the pre-issue shareholding percentage in the SEBI shareholding schema.
        pct = _valid_pct(match.group(1))
        if pct is not None:
            return pct

    return None


def extract_promoter_shareholding(text: str):
    combined = _explicit_combined_ownership(text)
    if combined is not None:
        return {"promoters": [], "promoterPreIssuePct": combined}
    return _ORIGINAL_EXTRACT_PROMOTER_SHAREHOLDING(text)


base.extract_promoter_shareholding = extract_promoter_shareholding
base.PARSER_VERSION = PARSER_VERSION

parse_document_text = base.parse_document_text
extract_financials = v10.extract_financials
extract_targeted_pdf_text = v10.extract_targeted_pdf_text
extract_pdf_text = v10.extract_pdf_text
choose_document = v10.choose_document
apply_enrichment = v10.apply_enrichment
download_pdf = v10.download_pdf


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
