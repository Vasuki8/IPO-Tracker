#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v5.

v5 builds on v4 and targets the two production gaps that remained after the
first successful deep-document backfill:

* financial tables whose PDF text is emitted vertically (labels on one line,
  values on following lines) or under newer financial-section headings;
* deep RHP pages, where table-of-contents references previously consumed the
  bounded scan before the actual financial/shareholding tables were reached.

The parser remains conservative: financial fallbacks require an explicit
financial section, at least two reporting periods and at least two recognized
metric series. Shareholding fallbacks require explicit pre-issue/pre-offer
percentage context. Existing exchange/SEBI values are still never overwritten.
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
v4 = isolated_module("run_offer_docs_v4")

base = v4.base
PARSER_VERSION = 5

_ORIGINAL_EXTRACT_FINANCIALS = base.extract_financials
_ORIGINAL_EXTRACT_PDF_TEXT = base.extract_pdf_text

_FINANCIAL_SECTION_MARKER = re.compile(
    r"(?:summary\s+of\s+(?:restated\s+)?(?:consolidated\s+|standalone\s+)?financial\s+information|"
    r"summary\s+of\s+financial\s+information|"
    r"restated\s+(?:consolidated\s+|standalone\s+)?financial\s+information|"
    r"statement\s+of\s+restated\s+financial\s+information|"
    r"financial\s+information\s+of\s+(?:our\s+)?(?:company|the\s+company)|"
    r"key\s+financial\s+information|"
    r"key\s+performance\s+indicators?)",
    re.I,
)

_FINANCIAL_METRICS = {
    "revenueCr": [
        r"Revenue\s+from\s+Operations",
        r"Total\s+(?:Revenue|Income)",
        r"Revenue\s+from\s+operation",
    ],
    "ebitdaCr": [
        r"\bEBITDA\b(?!\s+Margin)",
        r"Operating\s+EBITDA",
        r"Earnings\s+before\s+Interest,\s*Tax,\s*Depreciation\s+and\s+Amortisation",
    ],
    "patCr": [
        r"Profit\s+(?:after\s+Tax|for\s+the\s+(?:year|period))(?:\s*\(PAT\))?",
        r"Net\s+Profit\s+after\s+tax",
        r"Profit\s+after\s+taxation",
    ],
    "netWorthCr": [
        r"\bNet\s+Worth\b",
        r"\bNetworth\b",
    ],
    "ronwPct": [
        r"Return\s+on\s+Net\s+Worth",
        r"\bRoNW\b",
        r"Return\s+on\s+Networth",
    ],
    "roePct": [
        r"Return\s+on\s+Equity",
        r"\bROE\b",
    ],
    "eps": [
        r"(?:Basic\s+and\s+Diluted\s+)?Earnings\s+per\s+Share",
        r"\bBasic\s+EPS\b",
        r"Diluted\s+EPS",
    ],
}

_METRIC_UNION = re.compile(
    "|".join(
        rf"(?:{pattern})"
        for patterns in _FINANCIAL_METRICS.values()
        for pattern in patterns
    ),
    re.I,
)

_SHAREHOLDING_PAGE_MARKER = re.compile(
    r"(?:pre[-\s]?(?:issue|offer|ipo)\s+shareholding|"
    r"pre[-\s]?and[-\s]?post[-\s]?(?:issue|offer)\s+shareholding|"
    r"shareholding\s+pattern|"
    r"capital\s+structure|"
    r"promoters?\s+(?:and|&|/)\s+promoter\s+group)",
    re.I,
)

_PRE_CONTEXT = re.compile(
    r"(?:pre[-\s]?(?:issue|offer|ipo)|before\s+the\s+(?:issue|offer)|"
    r"prior\s+to\s+the\s+(?:issue|offer))",
    re.I,
)

_PROMOTER_GROUP_LABEL = (
    r"(?:Promoters?(?:\s*(?:and|&|/)\s*Promoter\s+Group)?|Promoter\s+Group)"
)


def _financial_years(block: str) -> list[str]:
    years: list[str] = []
    patterns = [
        r"\b(?:Fiscal|FY)\s*(20\d{2})\b",
        r"(?:March\s+31|31\s+March)[,\s]+(20\d{2})",
        r"(?:year|fiscal\s+year)\s+ended.{0,45}?\b(20\d{2})\b",
    ]
    for pattern in patterns:
        for year in re.findall(pattern, block, re.I | re.S):
            if year not in years:
                years.append(year)
    if len(years) < 2:
        # Bare years are only accepted close to a financial heading. This avoids
        # collecting filing dates from unrelated narrative pages.
        heading = _FINANCIAL_SECTION_MARKER.search(block)
        start = heading.start() if heading else 0
        for year in re.findall(r"\b(20[12]\d)\b", block[start : start + 2600]):
            if year not in years:
                years.append(year)
    return years[:4]


def _financial_window_score(block: str) -> int:
    marker_hits = len(_FINANCIAL_SECTION_MARKER.findall(block))
    metric_hits = sum(
        1
        for patterns in _FINANCIAL_METRICS.values()
        if any(re.search(pattern, block, re.I) for pattern in patterns)
    )
    years = len(_financial_years(block))
    numerics = len(base._numeric_tokens(block))
    return marker_hits * 5 + metric_hits * 4 + min(years, 4) * 3 + min(numerics // 12, 5)


def _financial_windows(text: str) -> list[str]:
    windows: list[tuple[int, int, str]] = []
    for match in _FINANCIAL_SECTION_MARKER.finditer(text):
        start = max(0, match.start() - 300)
        end = min(len(text), match.start() + 14000)
        block = text[start:end]
        windows.append((_financial_window_score(block), match.start(), block))
    windows.sort(key=lambda item: (item[0], item[1]), reverse=True)

    selected: list[str] = []
    fingerprints: set[str] = set()
    for score, _pos, block in windows:
        if score <= 0:
            continue
        fingerprint = re.sub(r"\s+", " ", block[:220]).casefold()
        if fingerprint in fingerprints:
            continue
        fingerprints.add(fingerprint)
        selected.append(block)
        if len(selected) >= 8:
            break
    return selected


def _series_near_label(block: str, patterns: list[str], period_count: int) -> list[float]:
    if period_count <= 0:
        return []
    combined = re.compile("|".join(rf"(?:{pattern})" for pattern in patterns), re.I)
    for match in combined.finditer(block):
        # pypdf often emits a row label first and the table cells on subsequent
        # lines. Read a bounded tail and stop before the next known metric label.
        tail = block[match.end() : match.end() + 950]
        next_metric = _METRIC_UNION.search(tail)
        if next_metric and next_metric.start() > 12:
            tail = tail[: next_metric.start()]
        values = base._numeric_tokens(tail)
        if len(values) >= period_count:
            return values[:period_count]
    return []


def _merge_financials(existing, incoming):
    if not incoming:
        return existing
    if not existing:
        return incoming
    old_periods = {
        str(row.get("period")): dict(row)
        for row in (existing.get("periods") or [])
        if isinstance(row, dict) and row.get("period")
    }
    for row in incoming.get("periods") or []:
        if not isinstance(row, dict) or not row.get("period"):
            continue
        period = str(row["period"])
        target = old_periods.setdefault(period, {"period": period})
        for key, value in row.items():
            if key != "period" and target.get(key) is None and value is not None:
                target[key] = value
    periods = list(old_periods.values())
    return {"unit": "₹ crore", "periods": periods} if periods else existing


def extract_financials(text: str):
    """Parse both horizontal and vertically extracted financial tables."""
    existing = _ORIGINAL_EXTRACT_FINANCIALS(text)
    best = None
    best_score = -1

    for block in _financial_windows(text):
        years = _financial_years(block)
        if len(years) < 2:
            continue

        series = {
            key: _series_near_label(block, patterns, len(years))
            for key, patterns in _FINANCIAL_METRICS.items()
        }
        populated = {key: values for key, values in series.items() if len(values) >= len(years)}
        # Two independent metric rows are required for a new fallback parse.
        # That is deliberately stricter than the completeness audit's "any row"
        # definition and prevents narrative prose from being mistaken for a table.
        if len(populated) < 2:
            continue

        unit = base.detect_money_unit(block)
        periods = []
        for idx, year in enumerate(years):
            row = {"period": f"FY{year}"}
            for key, values in populated.items():
                value = values[idx]
                row[key] = base.to_crore(value, unit) if key.endswith("Cr") else value
            periods.append(row)

        candidate = {"unit": "₹ crore", "periods": periods}
        score = len(populated) * 10 + _financial_window_score(block)
        if score > best_score:
            best_score = score
            best = candidate

    return _merge_financials(existing, best)


def extract_promoter_shareholding(text: str):
    """Extend v4 with percentage-column tables that omit literal percent signs."""
    existing = v4.extract_promoter_shareholding(text)
    if existing:
        return existing

    flat = re.sub(r"\s+", " ", base.norm_space(text)).strip()
    windows = []
    for match in _SHAREHOLDING_PAGE_MARKER.finditer(flat):
        windows.append(flat[max(0, match.start() - 700) : match.start() + 3200])
        if len(windows) >= 18:
            break

    for block in windows:
        if not _PRE_CONTEXT.search(block):
            continue

        pct_header = re.search(
            r"(?:pre[-\s]?(?:issue|offer|ipo).{0,100}?(?:%|percentage)|"
            r"(?:%|percentage).{0,100}?pre[-\s]?(?:issue|offer|ipo))",
            block,
            re.I,
        )
        if pct_header:
            row = re.search(
                rf"{_PROMOTER_GROUP_LABEL}\s*[:\-]?\s+"
                rf"([\d,]{{4,}})\s+([0-9]+(?:\.[0-9]+)?)"
                rf"(?:\s*%|\s+(?:[\d,]{{4,}}\s+)?[0-9]+(?:\.[0-9]+)?\s*%?)",
                block,
                re.I,
            )
            if row:
                pct = v4._valid_pct(row.group(2))
                if pct is not None:
                    return {"promoters": [], "promoterPreIssuePct": pct}

        narrative = re.search(
            rf"{_PROMOTER_GROUP_LABEL}.{{0,360}}?"
            rf"(?:hold|holds|holding|held|represent(?:s|ed|ing)?|"
            rf"constitut(?:e|es|ed|ing)|aggregate\s+shareholding).{{0,240}}?"
            rf"([0-9]+(?:\.[0-9]+)?)\s*%\s+(?:of\s+)?(?:our\s+|the\s+)?"
            rf"(?:pre[-\s]?(?:issue|offer|ipo)|before\s+the\s+(?:issue|offer)|"
            rf"prior\s+to\s+the\s+(?:issue|offer))",
            block,
            re.I,
        )
        if narrative:
            pct = v4._valid_pct(narrative.group(1))
            if pct is not None:
                return {"promoters": [], "promoterPreIssuePct": pct}
    return None


def _financial_page_score(text: str) -> int:
    if not text:
        return 0
    marker = bool(_FINANCIAL_SECTION_MARKER.search(text))
    metric_hits = sum(
        1
        for patterns in _FINANCIAL_METRICS.values()
        if any(re.search(pattern, text, re.I) for pattern in patterns)
    )
    year_hits = len(set(re.findall(r"\b20[12]\d\b", text)))
    numeric_hits = len(base._numeric_tokens(text))
    if not marker and metric_hits < 2:
        return 0
    return (8 if marker else 0) + metric_hits * 5 + min(year_hits, 4) * 3 + min(numeric_hits // 10, 5)


def _shareholding_page_score(text: str) -> int:
    if not text:
        return 0
    marker = bool(_SHAREHOLDING_PAGE_MARKER.search(text))
    promoter = bool(re.search(_PROMOTER_GROUP_LABEL, text, re.I))
    pre_context = bool(_PRE_CONTEXT.search(text))
    pct_hits = len(re.findall(r"\b[0-9]+(?:\.[0-9]+)?\s*%", text))
    if not marker and not (promoter and pre_context):
        return 0
    return (8 if marker else 0) + (6 if promoter else 0) + (5 if pre_context else 0) + min(pct_hits, 6) * 2


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
    """Append high-signal deep pages without stopping on TOC references.

    All later pages are scored up to a bounded limit. Only the strongest marker
    pages and their immediate context are appended to the first-30-page text.
    This keeps parser input compact while allowing real tables deep in an RHP to
    outrank early table-of-contents references.
    """
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
    scores: list[tuple[int, int]] = []
    cache: dict[int, str] = {}

    for idx in range(first_pages, stop_at):
        try:
            page_text = reader.pages[idx].extract_text() or ""
        except Exception:
            page_text = ""
        cache[idx] = page_text
        score = 0
        if need_financials:
            score = max(score, _financial_page_score(page_text))
        if need_shareholding:
            score = max(score, _shareholding_page_score(page_text))
        if score > 0:
            scores.append((score, idx))

    if not scores:
        return base_text, stop_at, page_count

    scores.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected_centers = [idx for _score, idx in scores[:max_hits]]
    selected_pages: set[int] = set()
    for center in selected_centers:
        for idx in range(max(first_pages, center - 1), min(stop_at, center + context_pages + 1)):
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


# Patch the base module globals resolved by parse_document_text() and main().
base.extract_financials = extract_financials
base.extract_promoter_shareholding = extract_promoter_shareholding
base.extract_pdf_text = extract_pdf_text
base.extract_targeted_pdf_text = extract_targeted_pdf_text
base.PARSER_VERSION = PARSER_VERSION

parse_document_text = base.parse_document_text
apply_enrichment = base.apply_enrichment
choose_document = v4.choose_document
download_pdf = v4.download_pdf


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
