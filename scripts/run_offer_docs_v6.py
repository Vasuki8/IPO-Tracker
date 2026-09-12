#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v6.

v6 keeps v5's deep-page and vertical-financial parsing and hardens promoter
pre-issue shareholding extraction for layouts observed in live prospectuses:

* ranked shareholding windows so real numeric tables outrank TOC/lock-in text;
* aggregate narrative wording such as "collectively holds ... aggregating to X%";
* Grand Total / Total Promoter Group rows where percentage columns omit `%`;
* direct "Promoter Holding Pre Issue" summary rows.

The fallback remains conservative: an explicit pre-issue/pre-offer context is
required and values must be valid percentages. It never derives ownership from
promoter-contribution or lock-in percentages.

Document selection continues to prefer direct official SEBI PDFs. When SEBI has
no eligible PDF, an official BSE-hosted Prospectus PDF captured from the BSE IPO
detail page is accepted as an exchange-official fallback. Extraction provenance
is copied from the selected document instead of being hardcoded to SEBI.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_offer_docs_v5 as v5  # noqa: E402

base = v5.base
PARSER_VERSION = 6

_ORIGINAL_EXTRACT_FINANCIALS = v5.extract_financials
_ORIGINAL_EXTRACT_PROMOTER_SHAREHOLDING = v5.extract_promoter_shareholding
_ORIGINAL_CHOOSE_DOCUMENT = v5.choose_document
_ORIGINAL_APPLY_ENRICHMENT = base.apply_enrichment

_PRE_CONTEXT = re.compile(
    r"(?:pre[-\s]?(?:issue|offer|ipo)|before\s+the\s+(?:issue|offer)|"
    r"prior\s+to\s+the\s+(?:issue|offer))",
    re.I,
)
_SHARE_MARKER = re.compile(
    r"(?:pre[-\s]?(?:issue|offer|ipo)\s+shareholding|"
    r"shareholding\s+(?:of\s+)?(?:our\s+)?promoters?|"
    r"promoters?\s+(?:and|&|/)\s+promoter\s+group|"
    r"shareholding\s+pattern|capital\s+structure|promoter\s+holding)",
    re.I,
)
_PROMOTER_LABEL = r"Promoters?(?:\s*(?:and|&|/)\s*Promoter\s+Group)?"


def _shareholding_score(block: str) -> int:
    pre = bool(_PRE_CONTEXT.search(block))
    promoter = bool(re.search(_PROMOTER_LABEL, block, re.I))
    pct_count = len(re.findall(r"\b(?:100(?:\.0+)?|\d{1,2}(?:\.\d+)?)\s*%", block))
    numeric_count = len(re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", block))
    aggregate = bool(re.search(r"(?:grand\s+total|sub\s*total|collectively|in\s+aggregate|promoter\s+holding)", block, re.I))
    return (12 if pre else 0) + (8 if promoter else 0) + min(pct_count, 8) * 2 + min(numeric_count // 8, 6) + (5 if aggregate else 0)


def _ranked_shareholding_windows(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", base.norm_space(text)).strip()
    candidates: list[tuple[int, int, str]] = []
    for match in _SHARE_MARKER.finditer(flat):
        block = flat[max(0, match.start() - 900) : min(len(flat), match.start() + 4200)]
        candidates.append((_shareholding_score(block), match.start(), block))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

    out: list[str] = []
    seen: set[str] = set()
    for score, _pos, block in candidates:
        if score < 20:
            continue
        fingerprint = block[:260].casefold()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        out.append(block)
        if len(out) >= 14:
            break
    return out


def _valid_pct(value):
    pct = base.number(value)
    if pct is None:
        return None
    pct = float(pct)
    if not 0 <= pct <= 100:
        return None
    return pct


def extract_promoter_shareholding(text: str):
    existing = _ORIGINAL_EXTRACT_PROMOTER_SHAREHOLDING(text)
    if existing:
        return existing

    for block in _ranked_shareholding_windows(text):
        if not _PRE_CONTEXT.search(block):
            continue

        narrative_patterns = [
            rf"{_PROMOTER_LABEL}.{{0,420}}?(?:collectively\s+)?(?:hold|holds|holding|held).{{0,320}}?"
            rf"(?:aggregat(?:e|es|ing)\s+(?:to\s+)?|represent(?:s|ing)?\s+|constitut(?:e|es|ing)\s+)?"
            rf"([0-9]+(?:\.[0-9]+)?)\s*%\s+of\s+(?:the\s+|our\s+)?"
            rf"(?:pre[-\s]?(?:issue|offer|ipo)|paid[-\s]?up\s+capital\s+before\s+the\s+(?:issue|offer))",
            rf"{_PROMOTER_LABEL}.{{0,180}}?in\s+aggregate.{{0,360}}?"
            rf"(?:represent(?:ing|s)?|constitut(?:ing|es)?|aggregat(?:ing|es)?\s+to)\s+"
            rf"([0-9]+(?:\.[0-9]+)?)\s*%\s+of\s+(?:the\s+)?pre[-\s]?(?:issue|offer|ipo)",
        ]
        for pattern in narrative_patterns:
            match = re.search(pattern, block, re.I)
            if match:
                pct = _valid_pct(match.group(1))
                if pct is not None:
                    return {"promoters": [], "promoterPreIssuePct": pct}

        direct = re.search(
            r"Promoter(?:s|\s+Group)?\s+(?:Share\s*)?Holding.{0,90}?"
            r"Pre[-\s]?(?:Issue|Offer|IPO).{0,80}?([0-9]+(?:\.[0-9]+)?)\s*%",
            block,
            re.I,
        )
        if direct:
            pct = _valid_pct(direct.group(1))
            if pct is not None:
                return {"promoters": [], "promoterPreIssuePct": pct}

        pre_pct_header = re.search(
            r"(?:Pre[-\s]?(?:Issue|IPO|Offer).{0,130}?(?:%|Percentage|Share\s+Holding)|"
            r"(?:%|Percentage|Share\s+Holding).{0,130}?Pre[-\s]?(?:Issue|IPO|Offer))",
            block,
            re.I,
        )
        if pre_pct_header:
            aggregate_rows = [
                r"Grand\s+Total(?:\s*\([^)]*\))?\s+([\d,]{4,})\s+([0-9]+(?:\.[0-9]+)?)\s*%?",
                r"Total\s+Promoter(?:s)?(?:\s*(?:and|&|/)\s*Promoter\s+Group)?\s+([\d,]{4,})\s+([0-9]+(?:\.[0-9]+)?)\s*%?",
                rf"{_PROMOTER_LABEL}\s+([\d,]{{4,}})\s+([0-9]+(?:\.[0-9]+)?)\s*%?",
            ]
            for pattern in aggregate_rows:
                match = re.search(pattern, block, re.I)
                if not match:
                    continue
                pct = _valid_pct(match.group(2))
                if pct is not None:
                    return {"promoters": [], "promoterPreIssuePct": pct}

        if re.search(r"Pre[-\s]?Issue\s+Shareholding\s+of\s+(?:our\s+)?Promoters?", block, re.I):
            subtotal = re.search(
                r"(?:Sub\s*Total|Total)\s*(?:\([^)]*\))?\s+([\d,]{4,})\s+([0-9]+(?:\.[0-9]+)?)\s*%?",
                block,
                re.I,
            )
            if subtotal:
                pct = _valid_pct(subtotal.group(2))
                if pct is not None:
                    return {"promoters": [], "promoterPreIssuePct": pct}

    return None


def extract_financials(text: str):
    """Merge v5 output with additional current-RHP PAT/revenue aliases."""
    existing = _ORIGINAL_EXTRACT_FINANCIALS(text)

    aliases = dict(v5._FINANCIAL_METRICS)
    aliases["patCr"] = [
        *aliases["patCr"],
        r"Profit\s*/?\s*\(?Loss\)?\s+After\s+Tax",
        r"\bPAT\b(?!\s+Margin)",
        r"Profit\s+after\s+taxation",
    ]
    aliases["revenueCr"] = [
        *aliases["revenueCr"],
        r"Revenue\s+from\s+operations?",
        r"\bRevenue\b",
    ]

    best = None
    best_score = -1
    for block in v5._financial_windows(text):
        years = v5._financial_years(block)
        if len(years) < 2:
            continue
        series = {
            key: v5._series_near_label(block, patterns, len(years))
            for key, patterns in aliases.items()
        }
        populated = {key: values for key, values in series.items() if len(values) >= len(years)}
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
        score = len(populated) * 10 + v5._financial_window_score(block)
        if score > best_score:
            best_score = score
            best = {"unit": "₹ crore", "periods": periods}
    return v5._merge_financials(existing, best)


def _official_bse_pdf(doc: dict):
    url = str(doc.get("url") or "").strip()
    if str(doc.get("source") or "").upper() != "BSE":
        return None
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    host = (parsed.hostname or "").lower()
    if host != "bseindia.com" and not host.endswith(".bseindia.com"):
        return None
    if not parsed.path.lower().endswith(".pdf"):
        return None
    return url


def choose_document(record):
    """Prefer SEBI; fall back only to an official BSE Prospectus PDF."""
    preferred = _ORIGINAL_CHOOSE_DOCUMENT(record)
    if preferred:
        return preferred

    rank = {"PROSPECTUS": 4, "RHP": 3, "UDRHP": 2, "DRHP": 1, "DOCUMENT": 0}
    candidates = []
    for doc in record.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        url = _official_bse_pdf(doc)
        if not url:
            continue
        title = str(doc.get("title") or "")
        typ = str(doc.get("type") or "DOCUMENT").upper()
        if "PROSPECTUS" not in title.upper() and typ not in {"PROSPECTUS", "RHP", "UDRHP", "DRHP"}:
            continue
        candidates.append((rank.get(typ, 0), str(doc.get("filedDate") or ""), len(title), doc))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[:-1])[-1]


def apply_enrichment(record, parsed, doc, pdf_hash, pages_read, page_count):
    """Use the base merge logic, then preserve the selected document's source."""
    _ORIGINAL_APPLY_ENRICHMENT(record, parsed, doc, pdf_hash, pages_read, page_count)
    extraction = record.get("offerDocumentExtraction")
    if isinstance(extraction, dict):
        extraction["source"] = str(doc.get("source") or "SEBI").upper()


base.extract_financials = extract_financials
base.extract_promoter_shareholding = extract_promoter_shareholding
base.choose_document = choose_document
base.apply_enrichment = apply_enrichment
base.PARSER_VERSION = PARSER_VERSION

parse_document_text = base.parse_document_text
download_pdf = v5.download_pdf
extract_targeted_pdf_text = v5.extract_targeted_pdf_text


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
