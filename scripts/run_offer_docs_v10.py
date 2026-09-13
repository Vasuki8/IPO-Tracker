#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v10.

v10 keeps v9's canonical-document selection and v8/v7 extraction behavior, and
adds one conservative ownership layout observed in the live Maharaja & Speedex
RHP: a pre-Offer Promoters table followed by Promoter Group rows and an explicit
``Total (A+B)`` combined percentage.

The new rule only accepts the combined row when a bounded surrounding window
contains explicit pre-Offer context plus both Promoter and Promoter Group labels.
It therefore reads the issuer's stated combined ownership directly instead of
loosening individual-row summation or inferring from promoter-contribution data.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_offer_docs_v9 as v9  # noqa: E402

base = v9.base
PARSER_VERSION = 10
_ORIGINAL_EXTRACT_PROMOTER_SHAREHOLDING = v9.extract_promoter_shareholding


def _valid_pct(value):
    pct = base.number(value)
    if pct is None:
        return None
    pct = float(pct)
    return pct if 0 <= pct <= 100 else None


def _explicit_ab_total(text: str):
    flat = re.sub(r"\s+", " ", base.norm_space(text)).strip()
    for match in re.finditer(
        r"Total\s*\(\s*A\s*\+\s*B\s*\)\s+[\d,]{2,}\s+"
        r"(100(?:\.0+)?|\d{1,2}(?:\.\d+)?)\s*%?",
        flat,
        re.I,
    ):
        block = flat[max(0, match.start() - 4200) : min(len(flat), match.end() + 500)]
        if not re.search(r"pre[-\s]?(?:offer|issue|ipo)", block, re.I):
            continue
        if not re.search(r"\bPromoters?\b", block, re.I):
            continue
        if not re.search(r"\bPromoter\s+Group\b", block, re.I):
            continue
        if re.search(r"minimum\s+promoters?['’]?\s+contribution", block[-1200:], re.I):
            continue
        pct = _valid_pct(match.group(1))
        if pct is not None:
            return pct
    return None


def extract_promoter_shareholding(text: str):
    combined = _explicit_ab_total(text)
    if combined is not None:
        return {"promoters": [], "promoterPreIssuePct": combined}
    return _ORIGINAL_EXTRACT_PROMOTER_SHAREHOLDING(text)


base.extract_promoter_shareholding = extract_promoter_shareholding
base.PARSER_VERSION = PARSER_VERSION

parse_document_text = base.parse_document_text
extract_financials = v9.extract_financials
extract_targeted_pdf_text = v9.extract_targeted_pdf_text
extract_pdf_text = v9.extract_pdf_text
choose_document = v9.choose_document
apply_enrichment = v9.apply_enrichment
download_pdf = v9.download_pdf


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
