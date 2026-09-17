"""Conservative checks for objects-of-issue rows before canonical promotion.

These checks reject recognizable contents entries and malformed values. They do
not establish source evidence or require legitimate purposes to match a keyword
list; monetary units and source rows remain the extractor's responsibility.
"""
from __future__ import annotations

import math
import re
from typing import Any


_CONTENTS_HEADING = re.compile(
    r"^(?:"
    r"(?:TABLE\s+OF\s+)?CONTENTS|"
    r"BASIS\s+FOR\s+(?:THE\s+)?(?:ISSUE|OFFER)\s+PRICE|"
    r"STATEMENT\s+OF\s+(?:POSSIBLE\s+)?(?:SPECIAL\s+)?TAX\s+BENEFITS|"
    r"SECTION\b\s*(?:[-–—:]\s*)?(?:[IVXLCDM]+|\d+)\b.*|"
    r"INDUSTRY\s+OVERVIEW|OUR\s+BUSINESS|"
    r"KEY\s+(?:INDUSTRY\s+)?REGULATIONS?(?:\s+AND\s+POLICIES)?(?:\s+IN\s+INDIA)?|"
    r"OUR\s+HISTORY|HISTORY\s+AND\s+(?:CERTAIN\s+)?CORPORATE\s+MATTERS|"
    r"OUR\s+MANAGEMENT|OUR\s+PROMOTERS?(?:\s+AND\s+PROMOTER\s+GROUP)?|"
    r"OUR\s+SUBSIDIARIES|(?:OUR\s+)?GROUP\s+COMPANIES|"
    r"DIVIDEND\s+POLICY|(?:RESTATED\s+)?FINANCIAL\s+INFORMATION|RISK\s+FACTORS"
    r")(?:\s+\d+)?[\s.:;\-–—]*$",
    re.I,
)
_DOT_LEADER = re.compile(r"(?:\.\s*){3,}|…")
_ROW_PREFIX = re.compile(r"^(?:\d+(?:\.\d+)*[.)]?|[A-Z][.)])\s+", re.I)
_TRAILING_NUMERIC_COLUMN = re.compile(r"\s[-+]?(?:\d[\d,]*\.\d+|\d{1,3}(?:,\d{2,3})+)$")
_PAGE_REFERENCE = re.compile(r"\bon\s+pages?\s*[.:;]?$", re.I)


def objects_problems(value: Any) -> list[str]:
    """Return problems in disclosed rows; absent objects are not an error."""
    if value is None or value == []:
        return []
    if not isinstance(value, list):
        return ["Expected an objects-of-issue list"]

    problems: list[str] = []
    for index, row in enumerate(value, 1):
        label = f"Objects-of-issue row {index}"
        if not isinstance(row, dict):
            problems.append(label + " must be an object")
            continue

        purpose = row.get("purpose")
        if not isinstance(purpose, str) or not purpose.strip():
            problems.append(label + " needs a nonempty purpose")
        else:
            normalized = " ".join(purpose.split())
            heading = _ROW_PREFIX.sub("", normalized)
            if _CONTENTS_HEADING.fullmatch(heading) or _DOT_LEADER.search(normalized):
                problems.append(label + " resembles a table-of-contents entry, not a use of proceeds")
            elif _TRAILING_NUMERIC_COLUMN.search(normalized):
                problems.append(label + " purpose ends in a numeric table column; amount alignment needs review")
            elif _PAGE_REFERENCE.search(normalized):
                problems.append(label + " ends in a page reference; its page number is not a monetary amount")

        amount = row.get("amountCr")
        if amount is not None:
            valid_amount = isinstance(amount, (int, float)) and not isinstance(amount, bool)
            if valid_amount:
                try:
                    valid_amount = math.isfinite(amount) and amount >= 0
                except OverflowError:
                    valid_amount = False
            if not valid_amount:
                problems.append(label + " amount must be finite and non-negative, or null if undisclosed")
    return problems


def objects_quarantined(record: dict[str, Any]) -> bool:
    review = record.get("objectsOfIssueReview")
    return isinstance(review, dict) and review.get("status") == "quarantined"
