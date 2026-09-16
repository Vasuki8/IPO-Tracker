"""Issuer-aware Final Prospectus candidate ranking and validation.

This module deliberately does not parse PDFs. It only decides whether document
metadata is plausible enough to select a Final Prospectus for parsing or to
consider issuer discovery complete. PDF text identity remains the primary
content-level guard in ``run_offer_documents.py``.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Iterable
from urllib.parse import unquote, urlparse

OFFICIAL_HOSTS = {
    "sebi.gov.in",
    "nsearchives.nseindia.com",
    "archives.nseindia.com",
    "bseindia.com",
}

LEGAL_WORDS = {
    "CO",
    "COMPANY",
    "CORP",
    "CORPORATION",
    "INC",
    "LIMITED",
    "LLP",
    "LTD",
    "PLC",
    "PRIVATE",
    "PUBLIC",
    "PVT",
}
DOCUMENT_WORDS = {
    "ABRIDGED",
    "ADDENDUM",
    "CORRIGENDUM",
    "DOCUMENT",
    "DRAFT",
    "DRHP",
    "FINAL",
    "OFFER",
    "PROSPECTUS",
    "RED",
    "HERRING",
    "RHP",
    "UDRHP",
}


def issuer_key(value: Any) -> str:
    """Return a stable alphanumeric issuer key without legal/document words."""
    text = unquote(str(value or "")).upper().replace("&", " AND ")
    words = re.findall(r"[A-Z0-9]+", text)
    kept = [word for word in words if word not in LEGAL_WORDS and word not in DOCUMENT_WORDS]
    return "".join(kept)


def _official_host(value: Any) -> bool:
    try:
        host = (urlparse(str(value or "")).hostname or "").lower()
    except ValueError:
        return False
    if host.startswith("www."):
        host = host[4:]
    return host in OFFICIAL_HOSTS


def _contains_issuer(record: dict[str, Any], value: Any) -> bool:
    expected = issuer_key(record.get("company"))
    observed = issuer_key(value)
    return bool(expected and len(expected) >= 5 and expected in observed)


def official_identity_score(record: dict[str, Any], doc: dict[str, Any]) -> int:
    """Score issuer identity hints that originate on an official market source.

    A title/company hint is trusted only when the document itself or its source
    page is on SEBI/NSE/BSE. Issuer text embedded in an official source-page URL
    or direct archive filename is also strong evidence.
    """
    url = str(doc.get("url") or "")
    source_page = str(doc.get("sourcePage") or "")
    official = _official_host(url) or _official_host(source_page)
    if not official:
        return 0

    score = 0
    if _contains_issuer(record, doc.get("company")):
        score = max(score, 5)
    if _contains_issuer(record, doc.get("title")):
        score = max(score, 5)
    if _official_host(source_page) and _contains_issuer(record, source_page):
        score = max(score, 4)
    if _official_host(url) and _contains_issuer(record, url):
        score = max(score, 3)
    return score


def _parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _lifecycle_dates(record: dict[str, Any]) -> list[date]:
    values: list[Any] = [record.get("openDate"), record.get("closeDate"), record.get("listingDate")]
    listing = record.get("listing")
    if isinstance(listing, dict):
        values.extend([listing.get("date"), listing.get("listingDate")])
    return [parsed for value in values if (parsed := _parse_date(value)) is not None]


def date_status(record: dict[str, Any], doc: dict[str, Any]) -> str:
    """Return ``plausible``, ``implausible`` or ``unknown`` for filedDate.

    The window is intentionally broad. A Final Prospectus normally clusters
    around issue close/listing; the generous bounds only reject obvious stale or
    misattached documents. Strong issuer identity can still rescue a document
    whose source supplied an observational date instead of its filing date.
    """
    filed = _parse_date(doc.get("filedDate"))
    lifecycle = _lifecycle_dates(record)
    if filed is None or not lifecycle:
        return "unknown"
    lower = min(lifecycle) - timedelta(days=120)
    upper = max(lifecycle) + timedelta(days=120)
    return "plausible" if lower <= filed <= upper else "implausible"


def candidate_acceptable(record: dict[str, Any], doc: dict[str, Any]) -> bool:
    """Reject clearly stale/misattached generic candidates before PDF parsing."""
    status = date_status(record, doc)
    return status != "implausible" or official_identity_score(record, doc) > 0


def discovery_complete(record: dict[str, Any], doc: dict[str, Any]) -> bool:
    """Only issuer-qualified official metadata may stop Final Prospectus search."""
    return official_identity_score(record, doc) > 0 and candidate_acceptable(record, doc)


def official_identity_confirmed(record: dict[str, Any], doc: dict[str, Any]) -> bool:
    """Narrow fallback when opening-page PDF text extraction loses issuer text."""
    return official_identity_score(record, doc) >= 3 and candidate_acceptable(record, doc)


def _filed_sort_value(doc: dict[str, Any]) -> str:
    parsed = _parse_date(doc.get("filedDate"))
    return parsed.isoformat() if parsed else ""


def choose_candidate(record: dict[str, Any], candidates: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    """Choose the safest candidate, preferring issuer evidence over recency."""
    eligible = [doc for doc in candidates if isinstance(doc, dict) and candidate_acceptable(record, doc)]
    if not eligible:
        return None
    eligible.sort(
        key=lambda doc: (
            official_identity_score(record, doc),
            2 if date_status(record, doc) == "plausible" else 1 if date_status(record, doc) == "unknown" else 0,
            _filed_sort_value(doc),
            "abridged" not in str(doc.get("title") or "").lower(),
            str(doc.get("url") or ""),
        ),
        reverse=True,
    )
    return eligible[0]
