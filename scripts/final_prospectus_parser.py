"""Final Prospectus parser adapter.

Extends the strict offer parser with fields that are meaningful only once the
book-built offer is final, especially the fixed Offer/Issue Price, explicit bid
lot and final issue composition. Final issue price is deliberately kept distinct
from the historical bidding price band: a one-point fixed price is never
synthesized as a price band.
"""
from __future__ import annotations

import math
import re
from typing import Any

import legacy_offer_parser as legacy
import offer_parser as base

PARSER_VERSION = base.PARSER_VERSION + 3
extract_pdf_text = base.extract_pdf_text
valid_manager = base.valid_manager
valid_registrar = base.valid_registrar

_PRICE_PATTERNS = (
    re.compile(
        r"\b(?:OFFER|ISSUE)\s+PRICE\s*(?::|IS|OF)?\s*(?:₹|RS\.?|INR)\s*"
        r"([0-9][0-9,]*(?:\.\d+)?)\s*(?:PER\s+)?(?:EQUITY\s+)?SHARE\b",
        re.I,
    ),
    re.compile(
        r"\bPRICE\s+OF\s+(?:₹|RS\.?|INR)\s*([0-9][0-9,]*(?:\.\d+)?)\s*"
        r"PER\s+(?:EQUITY\s+)?SHARE\b",
        re.I,
    ),
)
_PRICE_BAND_PATTERNS = (
    re.compile(
        r"\bPRICE\s+BAND\b.{0,120}?(?:₹|RS\.?|INR)?\s*"
        r"([0-9][0-9,]*(?:\.\d+)?)\s*(?:TO|[-–—])\s*"
        r"(?:₹|RS\.?|INR)?\s*([0-9][0-9,]*(?:\.\d+)?)\s*"
        r"(?:PER\s+)?(?:EQUITY\s+)?SHARE\b",
        re.I,
    ),
    re.compile(
        r"\bFLOOR\s+PRICE\b.{0,100}?(?:₹|RS\.?|INR)\s*"
        r"([0-9][0-9,]*(?:\.\d+)?).{0,180}?\bCAP\s+PRICE\b.{0,100}?"
        r"(?:₹|RS\.?|INR)\s*([0-9][0-9,]*(?:\.\d+)?)",
        re.I,
    ),
)
_LOT_PATTERNS = (
    re.compile(
        r"\bMINIMUM\s+BID\s+LOT(?:\s+SIZE)?\s*"
        r"(?:(?:SHALL|WILL)\s+BE|SHALL\s+CONSIST\s+OF|IS|OF|MEANS|[:\-])?\s*"
        r"([0-9][0-9,]{0,7})\s+(?:FULLY\s+PAID[-\s]?UP\s+)?EQUITY\s+SHARES\b",
        re.I,
    ),
    re.compile(
        r"\bBID\s+LOT(?:\s+SIZE)?\s*"
        r"(?:(?:SHALL|WILL)\s+BE|SHALL\s+CONSIST\s+OF|IS|OF|MEANS|[:\-])\s*"
        r"([0-9][0-9,]{0,7})\s+(?:FULLY\s+PAID[-\s]?UP\s+)?EQUITY\s+SHARES\b",
        re.I,
    ),
    re.compile(
        r"\bBID\s+LOT\b.{0,80}?\b(?:MINIMUM\s+OF\s+)?"
        r"([0-9][0-9,]{0,7})\s+(?:FULLY\s+PAID[-\s]?UP\s+)?EQUITY\s+SHARES\b",
        re.I,
    ),
    re.compile(
        r"\bTHE\s+BID\s+LOT\s+(?:FOR\s+THE\s+(?:OFFER|ISSUE)\s+)?"
        r"(?:IS|SHALL\s+BE|WILL\s+BE)\s+([0-9][0-9,]{0,7})\s+"
        r"(?:FULLY\s+PAID[-\s]?UP\s+)?EQUITY\s+SHARES\b",
        re.I,
    ),
)

_SHARE_FIELDS = ("freshShares", "ofsShares")
_AMOUNT_FIELDS = ("freshIssueCr", "ofsCr", "totalIssueSizeCr")


def _number(token: str) -> float | None:
    try:
        value = float(token.replace(",", ""))
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _page_number(page: str, fallback: int) -> int:
    marker = re.search(r"\[PAGE\s+(\d+)\]", str(page or ""), re.I)
    if not marker:
        return fallback
    try:
        value = int(marker.group(1))
    except ValueError:
        return fallback
    return value if value > 0 else fallback


def extract_final_lot_size(text: str) -> tuple[int | None, dict[str, Any]]:
    """Extract one unambiguous explicit Bid Lot from the full parsed document.

    Final Prospectuses can place the Bid Lot definition far beyond the first 20
    pages used by the compatibility front-matter parser. Search the already
    bounded Poppler text page-by-page, but accept only wording that explicitly
    says Bid Lot/Minimum Bid Lot. Generic minimum application/bid quantity is
    intentionally excluded because SME minimum applications may span two lots.
    """
    observations: list[tuple[int, int, str]] = []
    for page_index, page in enumerate(str(text or "").split("\f"), 1):
        compact = " ".join(page.replace("\u00a0", " ").split())
        for pattern in _LOT_PATTERNS:
            for match in pattern.finditer(compact):
                value = _number(match.group(1))
                if value is None or value != int(value):
                    continue
                lot = int(value)
                if 0 < lot <= 100_000:
                    observations.append((lot, _page_number(page, page_index), match.group(0)))

    unique = sorted({lot for lot, _, _ in observations})
    if len(unique) != 1:
        return None, {}
    lot = unique[0]
    evidence_hit = next(hit for hit in observations if hit[0] == lot)
    return lot, {
        "lotSize": {
            "page": evidence_hit[1],
            "heading": evidence_hit[2],
            "value": lot,
            "basis": "explicit Bid Lot/Minimum Bid Lot in Final Prospectus",
        }
    }


def extract_final_issue_price(text: str) -> tuple[float | None, dict[str, Any]]:
    """Extract one unambiguous fixed price from Final Prospectus front matter."""
    front_pages = str(text or "").split("\f")[:12]
    values: list[tuple[float, int, str]] = []
    for page_index, page in enumerate(front_pages, 1):
        compact = " ".join(page.replace("\u00a0", " ").split())
        for pattern in _PRICE_PATTERNS:
            for match in pattern.finditer(compact):
                value = _number(match.group(1))
                if value is not None and 0 < value <= 100_000:
                    values.append((value, _page_number(page, page_index), match.group(0)))
    unique = sorted({value for value, _, _ in values})
    if len(unique) != 1:
        return None, {}
    value = unique[0]
    evidence_hit = next(hit for hit in values if hit[0] == value)
    return value, {
        "issuePrice": {
            "page": evidence_hit[1],
            "heading": evidence_hit[2],
            "value": value,
            "basis": "explicit fixed Offer/Issue Price in Final Prospectus",
        }
    }


def extract_explicit_price_band(text: str) -> tuple[dict[str, float] | None, dict[str, Any]]:
    """Extract only an explicitly stated bidding range; never infer it from issue price."""
    pages = str(text or "").split("\f")[:40]
    values: list[tuple[float, float, int, str]] = []
    for page_index, page in enumerate(pages, 1):
        compact = " ".join(page.replace("\u00a0", " ").split())
        for pattern in _PRICE_BAND_PATTERNS:
            for match in pattern.finditer(compact):
                low, high = _number(match.group(1)), _number(match.group(2))
                if low is None or high is None:
                    continue
                if 0 < low <= high <= 100_000:
                    values.append((low, high, _page_number(page, page_index), match.group(0)))
    unique = sorted({(low, high) for low, high, _, _ in values})
    if len(unique) != 1:
        return None, {}
    low, high = unique[0]
    evidence_hit = next(hit for hit in values if hit[0] == low and hit[1] == high)
    band = {"min": low, "max": high}
    return band, {
        "priceBand": {
            "page": evidence_hit[2],
            "heading": evidence_hit[3],
            "value": band,
            "basis": "explicit Price Band/Floor Price/Cap Price in Final Prospectus",
        }
    }


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def validate_issue_composition(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None

    normalized: dict[str, Any] = {}
    for field in _SHARE_FIELDS:
        raw = value.get(field)
        if raw is None:
            continue
        if not _finite_number(raw) or float(raw) < 0 or float(raw) != int(float(raw)):
            return None
        shares = int(float(raw))
        if shares > 100_000_000_000:
            return None
        normalized[field] = shares

    for field in _AMOUNT_FIELDS:
        raw = value.get(field)
        if raw is None:
            continue
        if not _finite_number(raw) or float(raw) < 0 or float(raw) > 10_000_000:
            return None
        normalized[field] = round(float(raw), 6)

    valuation = value.get("valuationPriceUsed")
    if valuation is not None:
        if not _finite_number(valuation) or not 0 < float(valuation) <= 100_000:
            return None
        normalized["valuationPriceUsed"] = float(valuation)

    meaningful = any(
        normalized.get(field) not in (None, 0)
        for field in (*_SHARE_FIELDS, *_AMOUNT_FIELDS)
    )
    if not meaningful:
        return None

    fresh = normalized.get("freshIssueCr")
    ofs = normalized.get("ofsCr")
    total = normalized.get("totalIssueSizeCr")
    if fresh is not None and ofs is not None:
        expected = round(fresh + ofs, 6)
        if total is None:
            normalized["totalIssueSizeCr"] = expected
        else:
            tolerance = max(0.05, abs(total) * 0.005)
            if abs(total - expected) > tolerance:
                return None

    fresh_shares = normalized.get("freshShares")
    ofs_shares = normalized.get("ofsShares")
    if fresh_shares == 0 and ofs_shares == 0:
        return None

    return normalized


def extract_final_issue_composition(
    text: str, price_band: dict[str, Any] | None = None
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    candidate = legacy.extract_issue_composition(text, price_band)
    composition = validate_issue_composition(candidate)
    if not composition:
        return None, {}
    return composition, {
        "issueComposition": {
            "basis": "validated Final Prospectus issue composition",
            "freshShares": composition.get("freshShares"),
            "ofsShares": composition.get("ofsShares"),
            "freshIssueCr": composition.get("freshIssueCr"),
            "ofsCr": composition.get("ofsCr"),
            "totalIssueSizeCr": composition.get("totalIssueSizeCr"),
        }
    }


def parse_document_text(text: str, price_band=None) -> dict[str, Any]:
    parsed = base.parse_document_text(text, price_band)

    lot_size, lot_evidence = extract_final_lot_size(text)
    if lot_size is not None:
        # The explicit Final Prospectus Bid Lot is stronger than compatibility
        # fallbacks such as a generic minimum bid quantity.
        parsed["lotSize"] = lot_size

    issue_price, price_evidence = extract_final_issue_price(text)
    if issue_price is not None:
        parsed["issuePrice"] = issue_price

    explicit_band, band_evidence = extract_explicit_price_band(text)
    if explicit_band is not None:
        parsed["priceBand"] = explicit_band
    else:
        # The compatibility parser treats a fixed Issue/Offer Price as a
        # degenerate band. That is useful historically but semantically wrong
        # for the canonical `priceBand` field, so discard it unless an actual
        # band/floor-cap statement is present in the Final Prospectus.
        parsed.pop("priceBand", None)

    composition_band = explicit_band
    if issue_price is not None:
        composition_band = {"min": issue_price, "max": issue_price}
    composition, composition_evidence = extract_final_issue_composition(
        text, composition_band
    )
    if composition is not None:
        parsed["issueComposition"] = composition

    field_evidence = dict(parsed.get("fieldEvidence") or {})
    field_evidence.update(lot_evidence)
    field_evidence.update(price_evidence)
    field_evidence.update(band_evidence)
    field_evidence.update(composition_evidence)
    parsed["fieldEvidence"] = field_evidence

    extracted = [
        field
        for field in (parsed.get("extractedFields") or [])
        if field != "priceBand"
    ]
    if lot_size is not None and "lotSize" not in extracted:
        extracted.append("lotSize")
    if explicit_band is not None and "priceBand" not in extracted:
        extracted.append("priceBand")
    if issue_price is not None and "issuePrice" not in extracted:
        extracted.append("issuePrice")
    if composition is not None and "issueComposition" not in extracted:
        extracted.append("issueComposition")
    parsed["extractedFields"] = extracted
    parsed["finalProspectusParserVersion"] = PARSER_VERSION
    return parsed
