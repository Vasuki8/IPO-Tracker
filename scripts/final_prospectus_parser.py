"""Final Prospectus parser adapter.

Extends the strict offer parser with fields that are meaningful only once the
book-built offer is final, especially the fixed Offer/Issue Price. The adapter
keeps the existing bounded extraction and validation behavior.
"""
from __future__ import annotations

import re
from typing import Any

import offer_parser as base

PARSER_VERSION = base.PARSER_VERSION + 1
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


def extract_final_issue_price(text: str) -> tuple[float | None, dict[str, Any]]:
    """Extract one unambiguous fixed price from Final Prospectus front matter."""
    front_pages = str(text or "").split("\f")[:12]
    values: list[tuple[float, int, str]] = []
    for page_index, page in enumerate(front_pages, 1):
        compact = " ".join(page.replace("\u00a0", " ").split())
        for pattern in _PRICE_PATTERNS:
            for match in pattern.finditer(compact):
                try:
                    value = float(match.group(1).replace(",", ""))
                except ValueError:
                    continue
                if 0 < value <= 100_000:
                    values.append((value, page_index, match.group(0)))
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


def parse_document_text(text: str, price_band=None) -> dict[str, Any]:
    parsed = base.parse_document_text(text, price_band)
    issue_price, evidence = extract_final_issue_price(text)
    if issue_price is not None:
        parsed["issuePrice"] = issue_price
        field_evidence = dict(parsed.get("fieldEvidence") or {})
        field_evidence.update(evidence)
        parsed["fieldEvidence"] = field_evidence
        extracted = list(parsed.get("extractedFields") or [])
        if "issuePrice" not in extracted:
            extracted.append("issuePrice")
        parsed["extractedFields"] = extracted
    parsed["finalProspectusParserVersion"] = PARSER_VERSION
    return parsed
