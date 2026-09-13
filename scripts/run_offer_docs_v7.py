#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v7.

v7 builds on v6 and closes promoter pre-Offer ownership layouts observed in
current official offer documents.  In particular, abridged prospectuses often
split ownership into a Promoter subtotal and a Promoter Group subtotal instead
of printing one combined row.  Other documents list only individual rows for
those two sections, while full prospectuses may expose a direct `(A) Promoter
and Promoter Group` shareholding-pattern row.

The Phase 4.5B field is the combined Promoter + Promoter Group pre-Offer
percentage.  v7 therefore prefers explicit combined evidence, then safely sums
explicit A/B subtotals, and only then sums individual rows inside clearly
bounded Promoter and Promoter Group sections.  Existing v6 parsing remains the
fallback.  Promoter-contribution, lock-in and public-shareholder percentages are
never used.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_offer_docs_v6 as v6  # noqa: E402

base = v6.base
PARSER_VERSION = 7

_ORIGINAL_EXTRACT_PROMOTER_SHAREHOLDING = v6.extract_promoter_shareholding

_PRE_OFFER_TABLE_HEADING = re.compile(
    r"(?:pre[-\s]?offer\s+(?:and\s+post[-\s]?offer\s+)?shareholding|"
    r"pre[-\s]?offer\s+and\s+post[-\s]?offer\s+shareholding|"
    r"pre\s+and\s+post\s+offer\s+shareholding|"
    r"shareholding\s+pattern\s+of\s+(?:our\s+)?company)",
    re.I,
)

_PROMOTER_SECTION = re.compile(r"\bPromoters?\s+(?=1(?:\.|\s))", re.I)
_PROMOTER_GROUP_SECTION = re.compile(
    r"\bPromoter\s+Group(?:\s*\([^)]*\))?\s+(?=1(?:\.|\s))",
    re.I,
)
_SECTION_END = re.compile(
    r"\b(?:Additional\s+top\s+10|Other\s+public|Public\s+Shareholders|"
    r"Additional\s+shareholders|Non[-\s]?Promoter)\b",
    re.I,
)
_ROW_PCT = re.compile(
    r"\b\d[\d,]{2,}\s+"
    r"(100(?:\.0+)?|\d{1,2}(?:\.\d+)?)\s*%?\s+"
    r"(?=\[(?:●|•||\s)*\])",
    re.I,
)


def _valid_pct(value):
    pct = base.number(value)
    if pct is None:
        return None
    pct = float(pct)
    if not 0 <= pct <= 100:
        return None
    return pct


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", base.norm_space(text)).strip()


def _shareholding_windows(flat: str) -> list[str]:
    """Return wider, deduplicated windows around true pre-Offer table headings."""
    candidates: list[str] = []
    for match in _PRE_OFFER_TABLE_HEADING.finditer(flat):
        candidates.append(flat[max(0, match.start() - 500) : min(len(flat), match.start() + 9000)])
        if len(candidates) >= 18:
            break
    candidates.extend(v6._ranked_shareholding_windows(flat))

    out: list[str] = []
    seen: set[str] = set()
    for block in candidates:
        fingerprint = block[:320].casefold()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        out.append(block)
    return out


def _combined_pattern_pct(block: str):
    """Read a direct combined Promoter + Promoter Group pre-Offer percentage."""
    # Full shareholding-pattern tables commonly emit the category marker first:
    # `(A) Promoter and Promoter Group ... 61.53%`.
    row = re.search(
        r"(?:\(\s*A\s*\)|\bA\b)?\s*Promoters?\s+(?:and|&|/)\s+Promoter\s+Group"
        r".{0,650}?([0-9]+(?:\.[0-9]+)?)\s*%",
        block,
        re.I,
    )
    if row:
        pct = _valid_pct(row.group(1))
        if pct is not None:
            return pct

    # Some prospectuses state the combined percentage narratively rather than
    # in a compact row.  Requiring both the as-of-prospectus context and the
    # explicit Promoter Group phrase keeps this separate from promoter-only
    # ownership disclosures.
    narrative = re.search(
        r"(?:as\s+on|as\s+at)\s+the\s+date\s+of\s+(?:this|the)\s+"
        r"(?:red\s+herring\s+)?prospectus.{0,420}?"
        r"(?:our\s+)?Promoters?\s+along\s+with\s+(?:members\s+of\s+)?"
        r"(?:our\s+)?Promoter\s+Group.{0,220}?collectively\s+"
        r"(?:hold|holds|held).{0,120}?([0-9]+(?:\.[0-9]+)?)\s*%",
        block,
        re.I,
    )
    if not narrative:
        narrative = re.search(
            r"(?:our\s+)?Promoters?\s+along\s+with\s+(?:members\s+of\s+)?"
            r"(?:our\s+)?Promoter\s+Group.{0,220}?collectively\s+"
            r"(?:hold|holds|held).{0,120}?([0-9]+(?:\.[0-9]+)?)\s*%"
            r".{0,260}?(?:pre[-\s]?offer|pre[-\s]?issue|shareholding\s+pre\s+and\s+post)",
            block,
            re.I,
        )
    if narrative:
        pct = _valid_pct(narrative.group(1))
        if pct is not None:
            return pct
    return None


def _subtotal_pair_pct(block: str):
    """Sum explicit Promoter (A) and Promoter Group (B) pre-Offer subtotals."""
    if not _PROMOTER_GROUP_SECTION.search(block):
        return None
    match = re.search(
        r"(?:Sub[-\s]*total|Total)\s*\(\s*A\s*\)\s+"
        r"[\d,]{2,}\s+([0-9]+(?:\.[0-9]+)?)\s*%?"
        r".{0,2400}?"
        r"(?:Sub[-\s]*total|Total)\s*\(\s*B\s*\)\s+"
        r"[\d,]{2,}\s+([0-9]+(?:\.[0-9]+)?)\s*%?",
        block,
        re.I,
    )
    if not match:
        return None
    promoter_pct = _valid_pct(match.group(1))
    group_pct = _valid_pct(match.group(2))
    if promoter_pct is None or group_pct is None:
        return None
    combined = round(promoter_pct + group_pct, 4)
    return combined if 0 <= combined <= 100 else None


def _individual_section_pct(block: str):
    """Sum individual rows when the table has no category subtotal rows.

    This fallback is intentionally narrow: it requires numbered Promoter and
    Promoter Group sections, explicit pre-Offer context, placeholder post-Offer
    cells, and a public/additional-shareholder delimiter.  If either A/B subtotal
    appears but could not be parsed as a pair, no derived total is produced.
    """
    if not re.search(r"pre[-\s]?offer", block, re.I):
        return None
    if re.search(r"(?:Sub[-\s]*total|Total)\s*\(\s*[AB]\s*\)", block, re.I):
        return None

    group_match = _PROMOTER_GROUP_SECTION.search(block)
    if not group_match:
        return None
    promoter_matches = list(_PROMOTER_SECTION.finditer(block[: group_match.start()]))
    if not promoter_matches:
        return None
    promoter_match = promoter_matches[-1]

    tail = block[group_match.end() :]
    end_match = _SECTION_END.search(tail)
    if not end_match:
        return None
    group_end = group_match.end() + end_match.start()

    promoter_values = [float(value) for value in _ROW_PCT.findall(block[promoter_match.end() : group_match.start()])]
    group_values = [float(value) for value in _ROW_PCT.findall(block[group_match.end() : group_end])]
    if not promoter_values or not group_values:
        return None

    # A real table should expose at least two ownership rows overall.  Values
    # labelled `Negligible` are intentionally treated as zero and need not be
    # materialized in the sum.
    if len(promoter_values) + len(group_values) < 2:
        return None
    combined = round(sum(promoter_values) + sum(group_values), 4)
    return combined if 0 < combined <= 100 else None


def extract_promoter_shareholding(text: str):
    flat = _flat(text)

    # Prefer combined evidence before delegating to v6.  This prevents a
    # promoter-only narrative (for example 49.68%) from outranking a later
    # explicit Promoter + Promoter Group row (for example 61.53%).
    direct = _combined_pattern_pct(flat)
    if direct is not None:
        return {"promoters": [], "promoterPreIssuePct": direct}

    for block in _shareholding_windows(flat):
        direct = _combined_pattern_pct(block)
        if direct is not None:
            return {"promoters": [], "promoterPreIssuePct": direct}

        subtotal = _subtotal_pair_pct(block)
        if subtotal is not None:
            return {"promoters": [], "promoterPreIssuePct": subtotal}

        derived = _individual_section_pct(block)
        if derived is not None:
            return {"promoters": [], "promoterPreIssuePct": derived}

    return _ORIGINAL_EXTRACT_PROMOTER_SHAREHOLDING(text)


# Patch the shared base module used by parse_document_text() and all backfills.
base.extract_promoter_shareholding = extract_promoter_shareholding
base.PARSER_VERSION = PARSER_VERSION

parse_document_text = base.parse_document_text
extract_financials = v6.extract_financials
choose_document = v6.choose_document
apply_enrichment = v6.apply_enrichment
download_pdf = v6.download_pdf
extract_targeted_pdf_text = v6.extract_targeted_pdf_text


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
