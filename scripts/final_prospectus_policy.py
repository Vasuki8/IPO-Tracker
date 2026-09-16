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
import math
import re
from typing import Any
from urllib.parse import unquote, urlparse

from issue_composition_checks import COMPOSITION_FIELDS, composition_problems, quarantined_fields, record_composition_problems
from objects_of_issue_checks import objects_problems, objects_quarantined

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


def _known_non_final_route(url: Any) -> bool:
    """Reject official routes that are not full final offer documents."""
    try:
        parsed = urlparse(str(url or "").strip())
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return (
        host == "bseindia.com" and "/downloads/uploaddocs/notices/" in parsed.path.lower()
    ) or _sebi_abridged_pdf(url)


def is_final_prospectus(doc: dict[str, Any] | None) -> bool:
    """Return True only for an explicitly final Prospectus document.

    A title containing the word "prospectus" is not enough because both DRHP
    and RHP titles also contain it. Prefer the explicit document type, with a
    narrow title fallback that rejects draft/red-herring wording. Known BSE
    exchange-notice and SEBI Abridged Prospectus PDF routes are never canonical
    Final Prospectuses even if legacy metadata labeled them ``PROSPECTUS``.
    """
    if not isinstance(doc, dict) or _known_non_final_route(doc.get("url")):
        return False
    url = str(doc.get("url") or "")
    title = " ".join(str(doc.get("title") or "").split()).upper()
    if urlparse(url).path.lower().endswith(".pdf") and "ABRIDGED PROSPECTUS" in title:
        return False
    doc_type = _normal_type(doc.get("type"))
    if doc_type in FINAL_DOCUMENT_TYPES:
        return True
    return bool(
        title
        and "PROSPECTUS" in title
        and "RED HERRING" not in title
        and "DRAFT" not in title
        and "UDRHP" not in title
        and "RHP" not in title
        and "ABRIDGED PROSPECTUS" not in title
    )


def final_prospectus_from_source(source: dict[str, Any] | None) -> dict[str, Any] | None:
    """Promote a clearly final official PDF source into a document candidate."""
    if not isinstance(source, dict):
        return None
    url = str(source.get("url") or "").strip()
    if not url or _known_non_final_route(url):
        return None
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _FINAL_SOURCE_HOSTS:
        return None
    if not parsed.path.lower().endswith(".pdf"):
        return None

    label = " ".join(
        str(source.get(key) or "") for key in ("name", "title", "kind")
    ).upper()
    if "ABRIDGED PROSPECTUS" in label:
        return None
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


def _numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


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


def _financial_metric_plausible(key: str, value: Any) -> bool:
    if not _numeric(value):
        return False
    number = float(value)
    magnitude = abs(number)
    if key in {"roePct", "ronwPct"}:
        return magnitude <= 1000 and not 1900 <= magnitude <= 2100
    if key in {"eps", "dilutedEps"}:
        return magnitude <= 10_000 and not 1900 <= magnitude <= 2100
    return True


def _financial_evidence_supported(record: dict[str, Any], parsed: dict[str, Any]) -> bool:
    """Require every promoted financial cell to carry matching table evidence."""
    financials = parsed.get("financials")
    if not isinstance(financials, dict):
        return False
    periods = financials.get("periods")
    evidence = (parsed.get("fieldEvidence") or {}).get("financials")
    if not isinstance(periods, list) or len(periods) < 2 or not isinstance(evidence, dict) or not evidence:
        return False

    fiscal_years: list[int] = []
    metric_count = 0
    seen_periods: set[str] = set()
    for row in periods:
        if not isinstance(row, dict):
            return False
        period = str(row.get("period") or "")
        if not re.fullmatch(r"FY20\d{2}", period) or period in seen_periods:
            return False
        seen_periods.add(period)
        fiscal_years.append(int(period[2:]))
        for key, value in row.items():
            if key == "period" or value is None:
                continue
            metric_count += 1
            if not _financial_metric_plausible(str(key), value):
                return False
            cell = evidence.get(f"{period}.{key}")
            if not isinstance(cell, dict) or cell.get("normalizedValue") != value:
                return False

    if metric_count < 2:
        return False

    try:
        issue_year = int(str(record.get("openDate") or "")[:4])
    except (TypeError, ValueError):
        issue_year = 0
    if issue_year and fiscal_years:
        if max(fiscal_years) < issue_year - 2 or max(fiscal_years) > issue_year + 1:
            return False
        if min(fiscal_years) < issue_year - 6:
            return False

    return True


def _static_values(record: dict[str, Any], parsed: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for field in (
        "priceBand",
        "lotSize",
        "leadManagers",
        "registrar",
        "promoters",
        "objectsOfIssue",
        "shareholding",
    ):
        value = parsed.get(field)
        if field == "objectsOfIssue" and objects_problems(value):
            continue
        if _present(value):
            values[field] = copy.deepcopy(value)

    financials = parsed.get("financials")
    if _present(financials) and _financial_evidence_supported(record, parsed):
        values["financials"] = copy.deepcopy(financials)

    issue_price = parsed.get("issuePrice")
    if _present(issue_price):
        values["listing.issuePrice"] = issue_price

    composition = parsed.get("issueComposition")
    if _present(composition) and isinstance(composition, dict) and not composition_problems(composition):
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
        projected = {field: copy.deepcopy(record.get(field)) for field in COMPOSITION_FIELDS}
        projected.update({field: values[field] for field in COMPOSITION_FIELDS if field in values})
        if record_composition_problems(projected):
            # A partial source extraction must not combine a newly evidenced
            # component with incompatible retained totals from an older source.
            for field in COMPOSITION_FIELDS:
                values.pop(field, None)
    return values


def _field_detail_evidence(parsed: dict[str, Any], field: str) -> Any:
    evidence = parsed.get("fieldEvidence") or {}
    if not isinstance(evidence, dict):
        return None
    if field in {"issueSizeCr", "freshIssueCr", "ofsCr", "issueComposition"}:
        return evidence.get("issueComposition")
    if field == "listing.issuePrice":
        return evidence.get("issuePrice")
    return evidence.get(field)


def _canonical_evidence(
    record: dict[str, Any],
    field: str,
    value: Any,
    doc: dict[str, Any],
    *,
    source_url: str,
    sha256: str | None,
    parser_version: Any,
    checked_at: str | None,
    detail_evidence: Any = None,
) -> dict[str, Any]:
    out = {
        "source": "Final Prospectus",
        "sourceUrl": source_url,
        "documentType": "PROSPECTUS",
        "documentDate": doc.get("filedDate"),
        "sha256": sha256,
        "parserVersion": parser_version,
        "checkedAt": checked_at,
        "issueOpenDate": record.get("openDate"),
        "field": field,
        "value": copy.deepcopy(value),
    }
    if detail_evidence not in (None, {}, []):
        out["evidence"] = copy.deepcopy(detail_evidence)
    return out


def apply_final_prospectus_static_fields(
    record: dict[str, Any],
    parsed: dict[str, Any],
    doc: dict[str, Any],
    *,
    sha256: str | None = None,
    parser_version: Any = None,
    checked_at: str | None = None,
) -> list[dict[str, Any]]:
    """Make extracted Final Prospectus values canonical, including overwrites."""
    if not is_final_prospectus(doc):
        raise ValueError("Canonical static fields require a Final Prospectus")

    changes: list[dict[str, Any]] = []
    source_url = str(doc.get("url") or "")
    extracted = _static_values(record, parsed)
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
    for field, value in extracted.items():
        provenance[field] = _canonical_evidence(
            record,
            field,
            value,
            doc,
            source_url=source_url,
            sha256=sha256,
            parser_version=parser_version,
            checked_at=checked_at,
            detail_evidence=_field_detail_evidence(parsed, field),
        )

    # A partial source repair resolves only the fields actually supported by
    # this extraction. Unread components stay explicitly queued even if null.
    held = quarantined_fields(record)
    if held:
        remaining = held - set(extracted)
        review = record["issueCompositionReview"]
        review["fields"] = sorted(remaining)
        if not remaining:
            review["status"] = "resolved"
            review["resolvedAt"] = checked_at
            review["resolvedSourceUrl"] = source_url

    if objects_quarantined(record) and "objectsOfIssue" in extracted:
        record["objectsOfIssueReview"].update({
            "status": "resolved", "resolvedAt": checked_at,
            "resolvedSourceUrl": source_url,
        })

    accepted_evidence: dict[str, Any] = {}
    for field in extracted:
        detail = _field_detail_evidence(parsed, field)
        key = (
            "issueComposition"
            if field in {"issueSizeCr", "freshIssueCr", "ofsCr", "issueComposition"}
            else "issuePrice"
            if field == "listing.issuePrice"
            else field
        )
        if detail not in (None, {}, []) and key not in accepted_evidence:
            accepted_evidence[key] = copy.deepcopy(detail)
    record["documentFieldProvenance"] = {
        "sourceUrl": source_url,
        "documentType": "PROSPECTUS",
        "documentDate": doc.get("filedDate"),
        "sha256": sha256,
        "parserVersion": parser_version,
        "checkedAt": checked_at,
        "evidence": accepted_evidence,
        "sourcePolicy": "final-prospectus-only",
    }

    if "lotSize" in extracted:
        record["lotSizeEvidence"] = _canonical_evidence(
            record,
            "lotSize",
            extracted["lotSize"],
            doc,
            source_url=source_url,
            sha256=sha256,
            parser_version=parser_version,
            checked_at=checked_at,
            detail_evidence=_field_detail_evidence(parsed, "lotSize"),
        )

    if "listing.issuePrice" in extracted:
        listing = dict(record.get("listing") or {})
        listing["issuePriceEvidence"] = _canonical_evidence(
            record,
            "listing.issuePrice",
            extracted["listing.issuePrice"],
            doc,
            source_url=source_url,
            sha256=sha256,
            parser_version=parser_version,
            checked_at=checked_at,
            detail_evidence=_field_detail_evidence(parsed, "listing.issuePrice"),
        )
        record["listing"] = listing

    pending = [
        field
        for field in STATIC_CANONICAL_FIELDS
        if _present(field_value(record, field)) and field not in provenance
    ]
    pending = sorted(set(pending) | quarantined_fields(record) | ({"objectsOfIssue"} if objects_quarantined(record) else set()))
    record["staticSourcePolicy"] = {
        "policy": "final-prospectus-only",
        "documentUrl": source_url,
        "documentType": "PROSPECTUS",
        "checkedAt": checked_at,
        "verifiedFields": sorted(provenance),
        "pendingRevalidationFields": sorted(pending),
    }
    return changes
