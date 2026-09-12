#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v3.

v3 keeps the v2 wording fallbacks, fixes two quality-gate defects found in
production, and allows a conservative direct-PDF RHP/DRHP fallback when no
Abridged Prospectus is available. Only official SEBI PDF URLs are eligible.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_offer_docs_v2 as v2  # noqa: E402

base = v2.base
PARSER_VERSION = 3
base.PARSER_VERSION = PARSER_VERSION


def _clean_entity_header(value: str | None):
    if not value:
        return value
    cleaned = re.sub(
        r"^(?:TO\s+THE\s+(?:OFFER|ISSUE)\s+)+",
        "",
        str(value).strip(),
        flags=re.I,
    )
    return base.clean_name(cleaned)


def extract_intermediaries(text: str):
    leads, registrar = v2.extract_intermediaries(text)
    leads = base.dedupe(
        [cleaned for cleaned in (_clean_entity_header(x) for x in leads) if cleaned]
    )
    registrar = _clean_entity_header(registrar)
    return leads, registrar


def extract_issue_composition(text: str, price_band=None):
    """Trust explicit document amounts over price-derived estimates.

    A direct stated crore/million/lakh amount is authoritative. The older parser
    derived an amount from shares × cap price first, which could mask an explicit
    offer-document value when modern wording was used.
    """
    issue = dict(v2.extract_issue_composition(text, price_band) or {})
    block = base.section(
        text,
        [r"DETAILS\s+OF\s+THE\s+(?:ISSUE|OFFER)", r"ISSUE\s+DETAILS", r"OFFER\s+DETAILS"],
        [r"RISKS?\s+IN\s+RELATION", r"GENERAL\s+RISK", r"OBJECTS\s+OF\s+THE", r"LISTING"],
        9000,
    ) or text[:16000]

    explicit_fresh = v2._explicit_money_after(r"Fresh\s+Issue", block)
    explicit_ofs = v2._explicit_money_after(r"Offer\s+for\s+Sale", block)
    explicit_total = v2._explicit_money_after(
        r"(?:Total\s+Issue(?:\s+Size)?|Total\s+Offer(?:\s+Size)?|Issue\s+Size|Offer\s+Size)",
        block,
    )
    if explicit_fresh is not None:
        issue["freshIssueCr"] = explicit_fresh
    if explicit_ofs is not None:
        issue["ofsCr"] = explicit_ofs
    if explicit_total is not None:
        issue["totalIssueSizeCr"] = explicit_total
    elif issue.get("freshIssueCr") is not None and issue.get("ofsCr") is not None:
        issue["totalIssueSizeCr"] = round(
            float(issue["freshIssueCr"]) + float(issue["ofsCr"]), 4
        )
    return issue


def _official_sebi_pdf(doc: dict):
    url = str(doc.get("url") or "").strip()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not parsed.path.lower().endswith(".pdf"):
        return None
    if host != "sebi.gov.in" and not host.endswith(".sebi.gov.in"):
        return None
    return url


def choose_document(record):
    """Prefer Abridged Prospectus; safely fall back to a direct official PDF."""
    rank = {"PROSPECTUS": 4, "RHP": 3, "UDRHP": 2, "DRHP": 1, "DOCUMENT": 0}
    candidates = []
    for doc in record.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        url = _official_sebi_pdf(doc)
        if not url:
            continue
        title = str(doc.get("title") or "")
        typ = str(doc.get("type") or "DOCUMENT").upper()
        abridged = int("ABRIDGED" in title.upper() or "AP_" in url.upper())
        candidates.append(
            (abridged, rank.get(typ, 0), str(doc.get("filedDate") or ""), len(title), doc)
        )
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[:-1])[-1]


# parse_document_text() and base.main() resolve these functions through the base
# module globals, so patch them after importing v2.
base.extract_intermediaries = extract_intermediaries
base.extract_issue_composition = extract_issue_composition
base.choose_document = choose_document

parse_document_text = base.parse_document_text
apply_enrichment = base.apply_enrichment
extract_promoters = v2.extract_promoters
extract_financials = v2.extract_financials
extract_objects = v2.extract_objects
extract_promoter_shareholding = v2.extract_promoter_shareholding


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
