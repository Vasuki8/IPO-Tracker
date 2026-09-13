#!/usr/bin/env python3
"""Run validated P4 offer-document fallbacks with duplicate-id-safe targeting.

Version 4 layers three source-backed fallbacks on top of v3 and replaces the
base target selector so duplicate exchange symbols cannot silently redirect an
offer document to an auxiliary event row. All download, PDF-magic, issuer-
identity, parser-v13 and fill-only merge gates remain owned by the established
base runner.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_issuer_offer_docs_v3 as legacy_v3  # noqa: E402

base = legacy_v3.base

base.ISSUER_DOCUMENTS.update(
    {
        "indomim": {
            "company": "INDO-MIM Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1784523106091.pdf",
            "host": "www.sebi.gov.in",
            "type": "RHP",
            "title": "Red Herring Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/jul-2026/indo-mim-limited-rhp_102938.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI Red Herring Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "omni": {
            "company": "Omnitech Engineering Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1771933506852.pdf",
            "host": "www.sebi.gov.in",
            "type": "RHP",
            "title": "Red Herring Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/feb-2026/omnitech-engineering-limited-rhp_99941.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI Red Herring Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "rsl": {
            "company": "Rajputana Stainless Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/apr-2026/1775629467259.pdf",
            "host": "www.sebi.gov.in",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/apr-2026/rajputana-stainless-limited-prospectus_100791.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI final Prospectus",
            "sourceKind": "regulatory-filing",
        },
    }
)


def _identity_safe_targets(
    payload: dict[str, Any],
    queue: dict[str, Any],
    priority_max: int,
    limit: int,
):
    """Select a registered target by both record id and canonical issuer name.

    Exchange history can legitimately contain multiple rows with the same symbol
    (for example an IPO plus a later withdrawal-option event). Collapsing those
    rows into a single id->record mapping can route a filing to the wrong row.
    This selector keeps every candidate and requires exactly one issuer-identity
    match before allowing the established parser/downloader to run.
    """
    by_id: dict[str, list[dict[str, Any]]] = {}
    for record in payload.get("ipos") or []:
        if not isinstance(record, dict) or not record.get("id"):
            continue
        by_id.setdefault(str(record.get("id")), []).append(record)

    selected = []
    for item in queue.get("queue") or []:
        if not isinstance(item, dict):
            continue
        try:
            priority = int(item.get("priority"))
        except (TypeError, ValueError):
            continue

        record_id = str(item.get("id") or "")
        spec = base.ISSUER_DOCUMENTS.get(record_id)
        if priority > priority_max or not spec or not base._has_priority_gap(item):
            continue

        expected_company = base.core.canonical_company(str(spec.get("company") or ""))
        queue_company = base.core.canonical_company(str(item.get("company") or ""))
        if queue_company and queue_company != expected_company:
            continue

        matches = [
            record
            for record in by_id.get(record_id, [])
            if base.core.canonical_company(str(record.get("company") or "")) == expected_company
        ]
        if len(matches) != 1:
            continue

        selected.append((matches[0], item, spec))
        if limit > 0 and len(selected) >= limit:
            break
    return selected


base._targets = _identity_safe_targets


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
