#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v12.

v12 keeps v11's conservative offer-document extraction and adds two finalized
issue terms that are important to the P4 recent-history backlog:

* minimum bid / market lot size; and
* explicit finalized price band (or fixed issue price).

The new rules are deliberately narrow. They require IPO-specific wording close
to ``Equity Shares`` and never infer a lot from generic quantities or a price
from face value, discounts, financial tables, or valuation text. Existing NSE or
BSE values always win; document terms are fill-only and the exact source PDF is
retained in a separate SEBI-offer observation for provenance.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_offer_docs_v11 as v11  # noqa: E402

base = v11.base
PARSER_VERSION = 12

_ORIGINAL_PARSE_DOCUMENT_TEXT = v11.parse_document_text
_ORIGINAL_APPLY_ENRICHMENT = v11.apply_enrichment


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", base.norm_space(text or "")).strip()


def _valid_lot(value):
    lot = base.integer(value)
    if lot is None or lot <= 0 or lot > 100_000:
        return None
    return lot


def extract_lot_size(text: str):
    """Extract only an explicitly stated minimum IPO bid lot."""
    flat = _flat(text)
    patterns = (
        # "Minimum Bid Lot: 125 Equity Shares"
        r"\bminimum\s+bid\s+lot(?:\s+size)?\s*(?:is|of|:|-)?\s*"
        r"([\d,]{1,8})\s+(?:fully\s+paid[-\s]?up\s+)?equity\s+shares\b",
        # "Bid Lot: 125 Equity Shares"
        r"\bbid\s+lot(?:\s+size)?\s*(?:is|of|:|-)?\s*"
        r"([\d,]{1,8})\s+(?:fully\s+paid[-\s]?up\s+)?equity\s+shares\b",
        # "Minimum Bid Quantity: 1,200 Equity Shares"
        r"\bminimum\s+bid\s+quantity\s*(?:is|of|:|-)?\s*"
        r"([\d,]{1,8})\s+(?:fully\s+paid[-\s]?up\s+)?equity\s+shares\b",
        # "Bids can be made for a minimum of 1,200 Equity Shares ..."
        r"\bbids?\s+(?:can|may)\s+be\s+made\s+for\s+(?:a\s+)?minimum\s+of\s+"
        r"([\d,]{1,8})\s+(?:fully\s+paid[-\s]?up\s+)?equity\s+shares\b",
        # "minimum of 1,200 Equity Shares (the Minimum Bid Lot)"
        r"\bminimum\s+of\s+([\d,]{1,8})\s+"
        r"(?:fully\s+paid[-\s]?up\s+)?equity\s+shares.{0,100}?\bminimum\s+bid\s+lot\b",
        # Some final prospectuses use Market Lot rather than Bid Lot.
        r"\bmarket\s+lot\s*(?:is|of|:|-)?\s*([\d,]{1,8})\s+"
        r"(?:fully\s+paid[-\s]?up\s+)?equity\s+shares\b",
    )
    for pattern in patterns:
        match = re.search(pattern, flat, re.I)
        if match:
            lot = _valid_lot(match.group(1))
            if lot is not None:
                return lot
    return None


def _valid_band(lo, hi=None):
    low = base.number(lo)
    high = base.number(hi if hi is not None else lo)
    if low is None or high is None:
        return None
    low = float(low)
    high = float(high)
    if low <= 0 or high <= 0 or low > high or high > 100_000:
        return None
    return {"min": low, "max": high}


def extract_price_band(text: str):
    """Extract a finalized price band/fixed issue price from explicit IPO wording."""
    flat = _flat(text)

    range_patterns = (
        r"\bprice\s+band\b.{0,100}?(?:₹|Rs\.?|INR)?\s*"
        r"([\d,]+(?:\.\d+)?)\s*(?:to|[-–—])\s*(?:₹|Rs\.?|INR)?\s*"
        r"([\d,]+(?:\.\d+)?)\s+per\s+equity\s+share\b",
        r"\bfloor\s+price\b.{0,90}?(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)"
        r".{0,140}?\bcap\s+price\b.{0,90}?(?:₹|Rs\.?|INR)\s*"
        r"([\d,]+(?:\.\d+)?)\s+per\s+equity\s+share\b",
    )
    for pattern in range_patterns:
        match = re.search(pattern, flat, re.I)
        if match:
            band = _valid_band(match.group(1), match.group(2))
            if band:
                return band

    # Fixed-price IPOs: require an explicit currency and "per Equity Share" so
    # face value, employee discounts and accounting values cannot match.
    fixed = re.search(
        r"\b(?:issue|offer)\s+price\b\s*(?:is|of|:|at)?\s*"
        r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s+per\s+equity\s+share\b",
        flat,
        re.I,
    )
    if fixed:
        return _valid_band(fixed.group(1))
    return None


def parse_document_text(text: str, price_band=None):
    parsed = dict(_ORIGINAL_PARSE_DOCUMENT_TEXT(text, price_band) or {})
    lot_size = extract_lot_size(text)
    parsed_band = extract_price_band(text)
    parsed["lotSize"] = lot_size
    parsed["priceBand"] = parsed_band

    fields = list(parsed.get("extractedFields") or [])
    if lot_size is not None and "lotSize" not in fields:
        fields.append("lotSize")
    if parsed_band is not None and "priceBand" not in fields:
        fields.append("priceBand")
    parsed["extractedFields"] = fields
    return parsed


def apply_enrichment(record, parsed, doc, pdf_hash, pages_read, page_count):
    """Keep exchange values authoritative and fill missing offer terms only."""
    _ORIGINAL_APPLY_ENRICHMENT(record, parsed, doc, pdf_hash, pages_read, page_count)

    changed = []
    lot_size = parsed.get("lotSize")
    price_band = parsed.get("priceBand")
    if record.get("lotSize") is None and lot_size is not None:
        record["lotSize"] = lot_size
        changed.append("lotSize")
    if record.get("priceBand") in (None, {}, []) and price_band:
        record["priceBand"] = price_band
        changed.append("priceBand")

    # Preserve the document observation even when an exchange value already
    # exists. That makes disagreement auditable without silently overwriting the
    # exchange-normalized field.
    if lot_size is not None or price_band:
        observation = {
            "documentUrl": doc.get("url"),
            "documentType": doc.get("type"),
            "documentFiledDate": doc.get("filedDate"),
            "parserVersion": PARSER_VERSION,
        }
        if lot_size is not None:
            observation["lotSize"] = lot_size
        if price_band:
            observation["priceBand"] = price_band
        record.setdefault("observations", {})["SEBI-offer"] = observation

    extraction = record.get("offerDocumentExtraction")
    if isinstance(extraction, dict):
        extraction["parserVersion"] = PARSER_VERSION
        extraction["extractedFields"] = parsed.get("extractedFields") or []
        if changed:
            prior = list(extraction.get("changedFields") or [])
            extraction["changedFields"] = list(dict.fromkeys(prior + changed))


# base.main() resolves these functions through enrich_offer_docs module globals.
base.parse_document_text = parse_document_text
base.apply_enrichment = apply_enrichment
base.PARSER_VERSION = PARSER_VERSION

extract_promoter_shareholding = v11.extract_promoter_shareholding
extract_financials = v11.extract_financials
extract_targeted_pdf_text = v11.extract_targeted_pdf_text
extract_pdf_text = v11.extract_pdf_text
choose_document = v11.choose_document
download_pdf = v11.download_pdf


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
