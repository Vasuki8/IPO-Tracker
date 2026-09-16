"""Shared consistency checks for issue amounts and their share-count basis.

These checks detect contradictions; they never infer a replacement disclosure.
Currency comparisons allow the rounding used in published crore amounts.
"""
from __future__ import annotations

import math
from typing import Any

COMPOSITION_FIELDS = ("issueComposition", "issueSizeCr", "freshIssueCr", "ofsCr")
AMOUNT_ALIASES = {
    "totalIssueSizeCr": "issueSizeCr",
    "freshIssueCr": "freshIssueCr",
    "ofsCr": "ofsCr",
}


def numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def amounts_match(left: float, right: float) -> bool:
    return abs(left - right) <= max(0.05, max(abs(left), abs(right)) * 0.005)


def composition_problems(value: Any) -> list[tuple[str, str]]:
    """Return incompatible amounts/counts, allowing genuinely absent components."""
    if value in (None, {}):
        return []
    if not isinstance(value, dict):
        return [("issueComposition", "Expected an issue-composition object")]
    problems = []
    for field in (*AMOUNT_ALIASES, "freshShares", "ofsShares", "valuationPriceUsed"):
        number = value.get(field)
        if number is None:
            continue
        if not numeric(number) or number < 0:
            problems.append(("issueComposition." + field, "Expected a finite non-negative number"))
        elif field.endswith("Shares") and number != int(number):
            problems.append(("issueComposition." + field, "Share count must be a whole number"))
        elif field == "valuationPriceUsed" and number == 0:
            problems.append(("issueComposition." + field, "Valuation price must be positive"))
    if problems:
        return problems

    fresh, ofs, total = (
        value.get("freshIssueCr"), value.get("ofsCr"), value.get("totalIssueSizeCr")
    )
    if all(numeric(number) for number in (fresh, ofs, total)):
        if not amounts_match(fresh + ofs, total):
            problems.append(("issueComposition.totalIssueSizeCr", "Fresh issue plus offer for sale does not match total issue size"))
    elif numeric(total):
        for field in ("freshIssueCr", "ofsCr"):
            amount = value.get(field)
            if numeric(amount) and amount > total and not amounts_match(amount, total):
                problems.append(("issueComposition." + field, "Issue component exceeds total issue size"))

    price = value.get("valuationPriceUsed")
    for shares_field, amount_field in (("freshShares", "freshIssueCr"), ("ofsShares", "ofsCr")):
        shares, amount = value.get(shares_field), value.get(amount_field)
        if not (numeric(shares) and numeric(amount)):
            continue
        if (shares == 0) != (amount == 0):
            problems.append(("issueComposition." + amount_field, "Zero shares and nonzero issue amount, or the reverse, are inconsistent"))
        elif numeric(price) and not amounts_match(shares * price / 10_000_000, amount):
            problems.append(("issueComposition." + amount_field, "Share count times valuation price does not match amount; source or discount evidence needs review"))
    return problems


def record_composition_problems(record: dict[str, Any]) -> list[tuple[str, str]]:
    """Also check displayed amount aliases against the retained composition."""
    composition = record.get("issueComposition")
    problems = composition_problems(composition)
    if isinstance(composition, dict):
        for component, field in AMOUNT_ALIASES.items():
            amount, displayed = composition.get(component), record.get(field)
            if numeric(amount) and numeric(displayed) and not amounts_match(amount, displayed):
                problems.append((field, "Displayed issue amount does not match issue composition"))
    fresh, ofs, total = (record.get(field) for field in ("freshIssueCr", "ofsCr", "issueSizeCr"))
    if all(numeric(number) for number in (fresh, ofs, total)) and not amounts_match(fresh + ofs, total):
        problems.append(("issueSizeCr", "Displayed fresh issue plus offer for sale does not match total issue size"))
    return problems


def quarantined_fields(record: dict[str, Any]) -> set[str]:
    review = record.get("issueCompositionReview") or {}
    if not isinstance(review, dict) or review.get("status") != "quarantined":
        return set()
    return set(review.get("fields") or []) & set(COMPOSITION_FIELDS)
