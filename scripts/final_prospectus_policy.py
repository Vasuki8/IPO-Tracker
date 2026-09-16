"""Canonical static-data policy for IPO offer disclosures.

The tracker may observe issue terms from exchanges and other public sources, but
canonical static IPO fields are authoritative only when extracted from a Final
Prospectus/Prospectus. DRHP/RHP documents remain useful for historical document
tracking, but they must never populate or override canonical static fields.

Dynamic/post-offer fields (subscription, allotment/listing outcome, listing
price and market performance) remain outside this policy and may continue to use
exchange/market sources.
"""
from __future__ import annotations

import copy
import re
from typing import Any
from urllib.parse import urlparse

FINAL_DOCUMENT_TYPES = {"PROSPECTUS", "FINALPROSPECTUS"}
STATIC_CANONICAL_FIELDS = (
    "priceBand",
    "lotSize",
    "issueSizeCr",
    "freshIssueCr",
    "ofsCr",
    "issueComposition",
    "leadManagers",
    "registrar",
    "promoters",
    "financials",
    "objectsOfIssue",
    "shareholding",
    "listing.issuePrice",
)

_FINAL_SOURCE_HOSTS = {
    "www.sebi.gov.in",
    "sebi.gov.in",
    "nsearchives.nseindia.com",
    "archives.nseindia.com",
    "www.bseindia.com",
    "bseindia.com",
}


def _normal_type(value: Any) -> str:
    return re.sub(r"[^A-Z]+", "", str(value or "").upper())


def is_final_prospectus(doc: dict[str, Any] | None) -> bool:
    """Return True only for an explicitly final Prospectus document.

    A title containing the word "prospectus" is not enough because both DRHP
    and RHP titles also contain it. Prefer the explicit document type, with a
    narrow title fallback that rejects draft/red-herring wording.
    """
    if not isinstance(doc, dict):
        return False
    doc_type = _normal_type(doc.get("type"))
    if doc_type in FINAL_DOCUMENT_TYPES:
        return True
    title = " ".join(str(doc.get("title") or "").split()).upper()
    return bool(
        title
        and "PROSPECTUS" in title
        and "RED HERRING" not in title
        and "DRAFT" not in title
        and "UDRHP" not in title
        and "RHP" not in title
    )


def final_prospectus_from_source(source: dict[str, Any] | None) -> dict[str, Any] | None:
    """Promote a clearly final official PDF source into a document candidate."""
    if not isinstance(source, dict):
        return None
    url = str(source.get("url") or "").strip()
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _FINAL_SOURCE_HOSTS:
        return None
    if not parsed.path.lower().endswith(".pdf"):
        return None

    label = " ".join(
        str(source.get(key) or "") for key in ("name", "title", "kind")
    ).upper()
    path = parsed.path.upper()
    final_hint = bool(
        "FINAL PROSPECTUS" in label
        or ("PROSPECTUS" in label and "RED HERRING" not in label and "DRAFT" not in label)
        or re.search(r"(?:^|/)FP_[^/]+\.PDF$", path)
        or "_PROSP" in path
        or "/PROSPECTUS" in path
    )
    if not final_hint or "RHP" in path or "DRHP" in path:
        return None

    return {
        "type": "PROSPECTUS",
        "title": source.get("name") or source.get("title") or "Final Prospectus",
        "url": url,
        "source": "NSE" if "nseindia.com" in (parsed.hostname or "") else "BSE" if "bseindia.com" in (parsed.hostname or "") else "SEBI",
        "filedDate": source.get("filedDate") or source.get("asOf"),
    }


def final_prospectus_candidates(record: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    for doc in record.get("documents") or []:
        if not isinstance(doc, dict) or not is_final_prospectus(doc):
            continue
        url = str(doc.get("url") or "").strip()
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.path.lower().endswith(".pdf") or not url:
            continue
        if url not in seen:
            candidates.append(copy.deepcopy(doc))
            seen.add(url)

    for source in record.get("sources") or []:
        promoted = final_prospectus_from_source(source)
        if not promoted:
            continue
        url = str(promoted.get("url") or "")
        if url not in seen:
            candidates.append(promoted)
            seen.add(url)

    previous = record.get("offerDocumentExtraction") or {}
    previous_doc = {
        "type": previous.get("documentType"),
        "title": previous.get("documentTitle"),
        "url": previous.get("documentUrl"),
        "source": previous.get("source"),
        "filedDate": previous.get("documentFiledDate"),
    }
    if is_final_prospectus(previous_doc):
        url = str(previous_doc.get("url") or "").strip()
        if url and url not in seen:
            candidates.append(previous_doc)

    return candidates


def choose_final_prospectus(record: dict[str, Any]) -> dict[str, Any] | None:
    candidates = final_prospectus_candidates(record)
    if not candidates:
        return None
    candidates.sort(
        key=lambda doc: (
            str(doc.get("filedDate") or ""),
            "abridged" not in str(doc.get("title") or "").lower(),
            str(doc.get("url") or ""),
        ),
        reverse=True,
    )
    return candidates[0]


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def field_value(record: dict[str, Any], field: str) -> Any:
    if field == "listing.issuePrice":
        listing = record.get("listing")
        return listing.get("issuePrice") if isinstance(listing, dict) else None
    return record.get(field)


def _set_field_value(record: dict[str, Any], field: str, value: Any) -> None:
    if field == "listing.issuePrice":
        listing = dict(record.get("listing") or {})
        listing["issuePrice"] = copy.deepcopy(value)
        record["listing"] = listing
    else:
        record[field] = copy.deepcopy(value)


def _static_values(parsed: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for field in (
        "priceBand",
        "lotSize",
        "leadManagers",
        "registrar",
        "promoters",
        "financials",
        "objectsOfIssue",
        "shareholding",
    ):
        value = parsed.get(field)
        if _present(value):
            values[field] = copy.deepcopy(value)

    issue_price = parsed.get("issuePrice")
    if _present(issue_price):
        values["listing.issuePrice"] = issue_price

    composition = parsed.get("issueComposition")
    if _present(composition) and isinstance(composition, dict):
        values["issueComposition"] = copy.deepcopy(composition)
        total = composition.get("totalIssueSizeCr")
        fresh = composition.get("freshIssueCr")
        ofs = composition.get("ofsCr")
        if _present(total):
            values["issueSizeCr"] = total
        if _present(fresh):
            values["freshIssueCr"] = fresh
        if _present(ofs) or ofs == 0:
            values["ofsCr"] = ofs
    return values


def apply_final_prospectus_static_fields(
    record: dict[str, Any],
    parsed: dict[str, Any],
    doc: dict[str, Any],
    *,
    sha256: str | None = None,
    parser_version: Any = None,
    checked_at: str | None = None,
) -> list[dict[str, Any]]:
    """Make extracted Final Prospectus values canonical, including overwrites.

    Only fields actually recognized in the Final Prospectus are changed. Older
    values are retained when the final parser has no supported evidence for that
    field, but they are listed as pending revalidation in ``staticSourcePolicy``.
    """
    if not is_final_prospectus(doc):
        raise ValueError("Canonical static fields require a Final Prospectus")

    changes: list[dict[str, Any]] = []
    source_url = str(doc.get("url") or "")
    extracted = _static_values(parsed)
    for field, after in extracted.items():
        before = field_value(record, field)
        if before == after:
            continue
        _set_field_value(record, field, after)
        changes.append(
            {
                "field": field,
                "before": copy.deepcopy(before),
                "after": copy.deepcopy(after),
                "reason": "Final Prospectus is the canonical source for static IPO data",
                "sourceUrl": source_url,
                "sha256": sha256,
                "parserVersion": parser_version,
                "correctedAt": checked_at,
            }
        )

    provenance = record.setdefault("staticFieldProvenance", {})
    for field in extracted:
        provenance[field] = {
            "sourceUrl": source_url,
            "documentType": "PROSPECTUS",
            "documentDate": doc.get("filedDate"),
            "sha256": sha256,
            "parserVersion": parser_version,
            "checkedAt": checked_at,
        }

    if "listing.issuePrice" in extracted:
        listing = dict(record.get("listing") or {})
        listing["issuePriceEvidence"] = {
            "source": "Final Prospectus",
            "sourceUrl": source_url,
            "documentType": "PROSPECTUS",
            "documentDate": doc.get("filedDate"),
            "sha256": sha256,
            "parserVersion": parser_version,
            "checkedAt": checked_at,
            "value": extracted["listing.issuePrice"],
        }
        record["listing"] = listing

    pending = [
        field
        for field in STATIC_CANONICAL_FIELDS
        if _present(field_value(record, field)) and field not in provenance
    ]
    record["staticSourcePolicy"] = {
        "policy": "final-prospectus-only",
        "documentUrl": source_url,
        "documentType": "PROSPECTUS",
        "checkedAt": checked_at,
        "verifiedFields": sorted(provenance),
        "pendingRevalidationFields": sorted(pending),
    }
    return changes
