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
    if gap:
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
    paths += ["/documents"]
    return {
        "field": field,
        "reason": issue.get("reason"),
        "route": route,
        "repairGap": gap,
        "evidencePaths": [path for path in paths if _pointer_exists(record, path)],
        "nextAction": action,
    }


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
