"""Actionable source-review tasks, separate from missing-field completeness.

Evidence paths are JSON pointers relative to the canonical record identified by
the queue row's id. Compact rows store [field, definition index] pairs; the
definitions retain exact reasons and instructions without repeating long text.
Source selectors use the explicit, allow-listed gap projection on compact rows.
"""
from __future__ import annotations

import copy
import re
from typing import Any

from source_review_holds import HOLD_REVIEW_TYPES

FINANCIAL_FIELD = re.compile(
    r"financials\.FY\d{4}\.(?:revenueCr|totalIncomeCr|ebitdaCr|patCr|netWorthCr|eps|dilutedEps|ronwPct|roePct)\Z"
)
FINAL_GAPS = {
    "registrar": "offer.registrar",
    "leadManagers": "offer.leadManagers",
    "objectsOfIssue": "offer.objectsOfIssue",
    "issueComposition": "provenance.finalProspectus.issueComposition",
    "issueSizeCr": "provenance.finalProspectus.issueSizeCr",
    "freshIssueCr": "provenance.finalProspectus.freshIssueCr",
    "ofsCr": "provenance.finalProspectus.ofsCr",
    "listing.issuePrice": "provenance.finalProspectus.listing.issuePrice",
}
AUTOMATIC_REVIEW_GAPS = frozenset({"offer.financials", *FINAL_GAPS.values()})


def _pointer_exists(record: dict[str, Any], path: str) -> bool:
    value: Any = record
    for key in path.lstrip("/").split("/"):
        key = key.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or key not in value:
            return False
        value = value[key]
    return True


def review_task(record: dict[str, Any], issue: dict[str, Any]) -> dict[str, Any]:
    """Retain the review verbatim and select a source path, never a replacement value."""
    field = issue.get("field")
    financial = isinstance(field, str) and bool(FINANCIAL_FIELD.fullmatch(field))
    gap = "offer.financials" if financial else FINAL_GAPS.get(field) if isinstance(field, str) else None
    review_type = issue.get("reviewType")
    if review_type == 'active_offer_terms_conflict':
        gap = None
        route = 'manual-source-review'
        action = ('Reconcile this issuer/offer against the exact reviewed active disclosure and conflicting official '
                  'exchange rows or explicit superseding notice. Preserve the receipt and contradictory evidence; '
                  'collection recency alone cannot resolve the review. Completed static terms still require Final Prospectus evidence.')
        paths = ['/activeOfferTerms', '/observations', '/sources', '/dataCorrections', '/dataReview']
    elif review_type == 'subscription_snapshot_conflict':
        gap = None
        route = 'manual-source-review'
        action = ('Reconcile the exact issuer/offer, complete subscription snapshot and bid denominators against '
                  'issue-specific exchange detail or explicitly labelled secondary evidence. A newer collection '
                  'clock or a headline total alone cannot resolve this review. Preserve the original snapshot/history.')
        paths = ['/subscription', '/subscriptionSource', '/subscriptionSourceUrl', '/subscriptionObservedAt',
                 '/subscriptionCollectedAt', '/subscriptionAsOf', '/subscriptionTimeBasis',
                 '/subscriptionHistory', '/observations', '/sources', '/dataCorrections']
    elif isinstance(review_type, str) and review_type in HOLD_REVIEW_TYPES:
        gap = None
        route = "manual-source-review"
        action = (
            "Reconcile the documented conflict against authoritative source evidence or an explicit superseding disclosure; "
            "another extraction of the same PDF does not resolve this review. Retain the public hold until that review is resolved."
            if review_type == "document_conflict" else
            "Review the retained field and source-role or layout evidence, then publish an accepted source-backed correction. "
            "Retain the public hold until the source and value binding no longer matches."
        )
        pointer = str(field).replace("~", "~0").replace("/", "~1")
        paths = ["/staticFieldProvenance/" + pointer, "/documentFieldProvenance", "/dataCorrections", "/dataReview"]
    elif review_type is not None:
        gap = None
        route = "manual-triage"
        action = "Identify the unsupported review type and authoritative source with an operator before scheduling source work."
        paths = ["/dataReview", "/documentFieldProvenance", "/sources"]
    elif gap:
        route = "final-prospectus-review"
        action = (
            "Review the identified Final Prospectus table and field evidence; retain the hold until an accepted correction. "
            "Automatic parsing remains subject to source identity, parser-version and retry limits."
        )
        if financial:
            paths = ["/offerDocumentExtraction", "/documentFieldProvenance/evidence/financials", "/staticFieldProvenance/financials", "/financials"]
        elif field == "listing.issuePrice":
            paths = ["/listing/issuePriceEvidence", "/staticFieldProvenance/listing.issuePrice", "/offerDocumentExtraction"]
        else:
            paths = ["/documentRepair", "/documentFieldProvenance", "/staticFieldProvenance", "/staticSourcePolicy", "/dataReview", "/dataCorrections"]
    elif isinstance(field, str) and field in {"listing", "listingDate", "openDate", "closeDate", "allotmentDate"}:
        route = "official-exchange-review"
        action = "Manually reconcile the issue-specific official exchange notice or price report with retained evidence; do not estimate dates or prices."
        paths = ["/listing/priceConflicts", "/listing", "/listingDateEvidence", "/dataReview", "/sources"]
    else:
        route = "manual-triage"
        action = "Identify the field and authoritative source with an operator; unsupported or malformed review fields are not sent to an automatic collector."
        paths = ["/dataReview", "/offerDocumentExtraction", "/documentFieldProvenance", "/sources"]
    paths += ["/documents", "/activeOfferTerms"]
    task = {
        "field": field,
        "reason": issue.get("reason"),
        "route": route,
        "repairGap": gap,
        "evidencePaths": [path for path in paths if _pointer_exists(record, path)],
        "nextAction": action,
    }
    if review_type is not None:
        task["reviewType"] = review_type
    if issue.get("displayHold") is not None:
        task["displayHold"] = copy.deepcopy(issue["displayHold"])
    return task


def review_gaps(row: dict[str, Any]) -> set[str]:
    """Read the rich or compact projection; manual tasks never select a collector."""
    gaps = {
        gap for gap in (row.get("sourceReviewGaps") or [])
        if isinstance(gap, str) and gap in AUTOMATIC_REVIEW_GAPS
    }
    for task in row.get("sourceReviewItems") or []:
        if isinstance(task, dict) and task.get("route") == "final-prospectus-review":
            gap = task.get("repairGap")
            if isinstance(gap, str) and gap in AUTOMATIC_REVIEW_GAPS:
                gaps.add(gap)
    return gaps


def actionable_gaps(row: dict[str, Any]) -> set[str]:
    return {gap for gap in (row.get("missingFields") or []) if isinstance(gap, str)} | review_gaps(row)


def compact_review_items(row: dict[str, Any], definitions: list[dict[str, Any]]) -> list[list[Any]]:
    items = []
    for task in row.get("sourceReviewItems") or []:
        definition = {key: copy.deepcopy(value) for key, value in task.items() if key != "field"}
        if definition not in definitions:
            definitions.append(definition)
        items.append([task.get("field"), definitions.index(definition)])
    return items


def expand_review_items(row: dict[str, Any], definitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Decode losslessly; malformed definition references fail instead of disappearing."""
    expanded = []
    for item in row.get("sourceReviewItems") or []:
        if isinstance(item, dict):
            expanded.append(copy.deepcopy(item))
            continue
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("Invalid compact source-review item")
        field, index = item
        if type(index) is not int or not 0 <= index < len(definitions):
            raise ValueError("Invalid source-review definition index")
        definition = definitions[index]
        if not isinstance(definition, dict) or not definition.get("reason") or not definition.get("route"):
            raise ValueError("Invalid source-review definition")
        expanded.append({"field": field, **copy.deepcopy(definition)})
    return expanded
