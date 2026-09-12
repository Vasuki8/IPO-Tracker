#!/usr/bin/env python3
"""Phase 4.5A BSE exchange-detail parser v2.

This wrapper keeps the established BSE index/matching/merge logic and broadens
only the label/value parsing used on official DisplayIPO pages. BSE has used
several labels for the same facts over time, especially market lot, minimum bid
quantity and issue size. v2 accepts those official variants and can parse a
monetary issue-size row directly when it carries an explicit unit.

The parser remains conservative:
- direct monetary issue size must include a recognizable rupee unit/context;
- direct monetary amount outranks a price-derived estimate from shares;
- all merges remain fill-only, with NSE values retaining precedence;
- BSE observations are still retained independently for conflict validation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_exchange_details as base  # noqa: E402

PARSER_VERSION = 2


def _pairs(html: str) -> dict[str, list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    out: dict[str, list[str]] = {}
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        if len(cells) < 2:
            continue
        label = " ".join(cells[0].stripped_strings).strip()
        if not label:
            continue
        values: list[str] = []
        for cell in cells[1:]:
            values.extend(base._cell_texts(cell))
        if values:
            out.setdefault(base.clean_label(label), []).extend(values)
    return out


def _values_for(pairs: dict[str, list[str]], *labels: str) -> list[str]:
    wanted = [base.clean_label(label) for label in labels]
    for label in wanted:
        if label in pairs:
            return pairs[label]
    for key, values in pairs.items():
        if any(label and label in key for label in wanted):
            return values
    return []


def _text_for(pairs: dict[str, list[str]], *labels: str) -> str | None:
    values = _values_for(pairs, *labels)
    return " ".join(values).strip() if values else None


def parse_money_crore(text: str | None, *, label: str | None = None) -> float | None:
    """Convert an explicit rupee monetary amount to crore.

    Bare numbers are accepted only when the field label itself explicitly says
    crore/lakh/million/billion. This prevents a share count from being mistaken
    for a rupee amount.
    """
    raw = " ".join(str(text or "").replace("₹", " Rs ").split())
    context = f"{label or ''} {raw}".lower()
    value = base.core.number(raw)
    if value is None or value <= 0:
        return None

    if re.search(r"\b(?:crore|crores|cr)\b", context):
        crore = value
    elif re.search(r"\b(?:lakh|lakhs|lac|lacs)\b", context):
        crore = value / 100.0
    elif re.search(r"\b(?:million|mn)\b", context):
        crore = value / 10.0
    elif re.search(r"\b(?:billion|bn)\b", context):
        crore = value * 100.0
    elif re.search(r"\b(?:rs|inr|rupees?)\b", context):
        # Explicit currency but no scale means raw rupees.
        crore = value / 10_000_000.0
    else:
        return None

    if not 0 < crore <= 100_000:
        return None
    return round(crore, 4)


def _direct_issue_size_crore(pairs: dict[str, list[str]]) -> float | None:
    labels = (
        "Issue Size – Amount",
        "Issue Size - Amount",
        "Issue Size Amount",
        "Issue Amount",
        "Issue Size (Rs. Cr.)",
        "Issue Size (Rs Cr)",
        "Issue Size (₹ Cr.)",
        "Issue Size in Crores",
        "Issue Size (Crore)",
        "Issue Size (Lakhs)",
        "Issue Size (Rs. Lakhs)",
    )
    for label in labels:
        values = _values_for(pairs, label)
        if not values:
            continue
        parsed = parse_money_crore(" ".join(values), label=label)
        if parsed is not None:
            return parsed
    return None


def parse_detail_html(html: str) -> dict[str, Any]:
    detail = dict(base.parse_detail_html(html))
    pairs = _pairs(html)

    market_lot = detail.get("marketLot") or base.core.integer(
        _text_for(
            pairs,
            "Market Lot",
            "Market Lot Size",
            "Bid Lot",
            "Bid Lot Size",
            "Lot Size",
            "Minimum Application Lot",
        )
    )
    min_bid = detail.get("minimumBidQuantity") or base.core.integer(
        _text_for(
            pairs,
            "Minimum Bid Quantity",
            "Minimum Bid Qty",
            "Minimum Order Quantity",
            "Minimum Order Qty",
            "Minimum Application Quantity",
            "Minimum Application Size",
        )
    )
    lot_size = min_bid or market_lot or detail.get("lotSize")

    shares = detail.get("sharesOffered") or base.core.integer(
        _text_for(
            pairs,
            "Issue Size – No. of Shares",
            "Issue Size - No. of Shares",
            "Issue Size (No. of Shares)",
            "Issue Size No of Shares",
            "No. of Shares Offered",
            "No of Shares Offered",
            "Number of Shares Offered",
            "No. of Equity Shares Offered",
            "Issue Size (Shares)",
        )
    )

    direct_issue_size = _direct_issue_size_crore(pairs)
    band = detail.get("priceBand") if isinstance(detail.get("priceBand"), dict) else None
    cap = base.core.number((band or {}).get("max"))
    derived_issue_size = round(shares * cap / 10_000_000, 2) if shares and cap else None
    issue_size = direct_issue_size if direct_issue_size is not None else detail.get("issueSizeCr") or derived_issue_size

    detail["marketLot"] = market_lot
    detail["minimumBidQuantity"] = min_bid
    detail["lotSize"] = lot_size
    detail["sharesOffered"] = shares
    detail["issueSizeCr"] = issue_size
    detail["minInvestment"] = round(lot_size * cap, 2) if lot_size and cap else detail.get("minInvestment")
    detail["exchangeDetailParserVersion"] = PARSER_VERSION
    return detail


# Patch the production entry point in this process. base.main resolves this
# global at runtime, so all existing indexing/matching/merge/health logic stays
# unchanged while using the v2 parser.
base.parse_detail_html = parse_detail_html

DATA_FILE = base.DATA_FILE
BSE_HISTORY_URL = base.BSE_HISTORY_URL
INDEX_URLS = base.INDEX_URLS
clean_label = base.clean_label
best_url = base.best_url
merge_detail = base.merge_detail
is_candidate = base.is_candidate
build_detail_index = base.build_detail_index


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
