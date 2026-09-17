"""Synthetic source tables for tests of the objects evidence contract only."""
from __future__ import annotations

import copy
from typing import Any


def objects_evidence(rows: list[dict[str, Any]], *, page: int = 100) -> dict[str, Any]:
    """Build explicit test source cells; production legacy data must be re-read."""
    source_rows = []
    for row in rows:
        purpose = row["purpose"]
        token = "[●]" if row.get("amountCr") is None else str(row["amountCr"])
        line = f"{purpose}    {token}"
        amount_start = len(purpose) + 4
        source_rows.append({
            "page": page,
            "purpose": purpose,
            "amountToken": token,
            "normalizedValue": row.get("amountCr"),
            "lines": [{"page": page, "text": line}],
            "purposeSpans": [{"line": 0, "start": 0, "end": len(purpose)}],
            "amountSpan": {"line": 0, "start": amount_start, "end": len(line)},
        })
    return {
        "schemaVersion": 1,
        "page": page,
        "heading": "OBJECTS OF THE ISSUE",
        "headingRaw": "OBJECTS OF THE ISSUE",
        "unit": "crore",
        "unitText": "(₹ in crore)",
        "unitPage": page,
        "tableHeaders": [{"page": page, "text": "Particulars    Amount (₹ in crore)"}],
        "rows": copy.deepcopy(rows),
        "sourceRows": source_rows,
    }


def objects_parsed(rows: list[dict[str, Any]], *, page: int = 100) -> dict[str, Any]:
    return {
        "objectsOfIssue": copy.deepcopy(rows),
        "fieldEvidence": {"objectsOfIssue": objects_evidence(rows, page=page)},
        "extractedFields": ["objectsOfIssue"],
    }
