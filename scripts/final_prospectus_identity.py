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
NON_FINAL_DOCUMENT_TYPES = {
    "RHP",
    "DRHP",
    "UDRHP",
    "REDHERRINGPROSPECTUS",
    "DRAFTREDHERRINGPROSPECTUS",
    "UPDATEDDRAFTREDHERRINGPROSPECTUS",
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


def _normal_document_type(value: Any) -> str:
    return re.sub(r"[^A-Z]+", "", str(value or "").upper())


def _sebi_abridged_pdf(url: Any) -> bool:
    """Recognize SEBI's direct Abridged Prospectus PDF routes."""
    try:
        parsed = urlparse(str(url or "").strip())
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host != "sebi.gov.in":
        return False
    path = unquote(parsed.path).lower()
    if not path.endswith(".pdf") or "/sebi_data/commondocs/" not in path:
        return False
    name = path.rsplit("/", 1)[-1]
    return "abridged prospectus" in name or bool(re.search(r"(?:^|[\s_-])ap_p\.pdf$", name, re.I))


def _known_non_final_source_route(url: Any) -> bool:
    """Reject official source routes that are not full final offer documents."""
    try:
        parsed = urlparse(str(url or "").strip())
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.lower()
    return (
        host == "bseindia.com" and "/downloads/uploaddocs/notices/" in path
    ) or _sebi_abridged_pdf(url)


def known_non_final_document_url(record: dict[str, Any], url: Any) -> bool:
    """Return True when exact official metadata proves a URL is not final.

    Older extraction records sometimes mislabeled attached RHP/Abridged PDFs as
    ``PROSPECTUS``. BSE exchange-notice PDFs were also historically captured
    from nested issue-detail rows. Exact URL/route guards reject only those
    contradicted sources without guessing about otherwise valid final PDFs.
    """
    target = str(url or "").strip()
    if not target:
        return False
    if _known_non_final_source_route(target):
        return True
    is_pdf = urlparse(target).path.lower().endswith(".pdf")
    for doc in record.get("documents") or []:
        if not isinstance(doc, dict) or str(doc.get("url") or "").strip() != target:
            continue
        if _normal_document_type(doc.get("type")) in NON_FINAL_DOCUMENT_TYPES:
            return True
        if is_pdf and "ABRIDGED PROSPECTUS" in str(doc.get("title") or "").upper():
            return True
    return False


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
    """Reject clearly stale, contradicted, or misattached candidates."""
    if known_non_final_document_url(record, doc.get("url")):
        return False
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
    """Choose the safest candidate, rotating away from a previously failed URL.

    A failed source is skipped only when another independently eligible Final
    Prospectus exists. If it is the only candidate, it remains selectable so
    transient source failures can be retried on a later collection run.
    """
    eligible = [doc for doc in candidates if isinstance(doc, dict) and candidate_acceptable(record, doc)]
    if not eligible:
        return None

    repair = record.get("documentRepair") or {}
    if isinstance(repair, dict) and repair.get("status") in {"source_blocked", "parse_failed"}:
        failed_url = str(repair.get("sourceUrl") or "").strip()
        if failed_url:
            alternatives = [doc for doc in eligible if str(doc.get("url") or "").strip() != failed_url]
            if alternatives:
                eligible = alternatives

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
