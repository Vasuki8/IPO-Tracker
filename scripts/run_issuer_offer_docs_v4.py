#!/usr/bin/env python3
"""Run validated P4 offer-document fallbacks with safe progressive targeting.

Version 4 layers source-backed regulatory/exchange fallbacks on top of v3,
keeps duplicate-id-safe issuer matching, and schedules verified documents in
bounded progressive batches. Documents already extracted by the current parser
are skipped, while issuers that failed in the previous batch are moved behind
never-attempted work so one slow/broken PDF cannot block the registry.

The verified issuer path uses parser v14, which retains v13's bounded deep-page
selection and fill-only gates while recognizing a narrow official-prospectus
cover-table intermediary layout. All download, PDF-magic and issuer-identity
validation remains owned by the established base runner.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from parser_loader import isolated_module
legacy_v3 = isolated_module("run_issuer_offer_docs_v3")
from parser_loader import isolated_module
parser_v14 = isolated_module("run_offer_docs_v14")

base = legacy_v3.base

# v3 establishes the broad official-document registry. Override only the parser
# module and version. Keep enrich_issuer_offer_docs' own targeted full-document
# financial/shareholding scanner: its calling contract and purpose are distinct
# from the generic offer-parser targeted-page helper.
base.parser_v4 = parser_v14
base.PARSER_VERSION = parser_v14.PARSER_VERSION

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
        "ardee": {
            "company": "Ardee Industries Limited",
            "url": "https://nsearchives.nseindia.com/corporate/FP_INE0XNF01022_10AUG2026.pdf",
            "host": "nsearchives.nseindia.com",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://nsearchives.nseindia.com/corporate/FP_INE0XNF01022_10AUG2026.pdf",
            "extractionSource": "NSE",
            "documentSource": "NSE",
            "sourceName": "NSE final Prospectus",
            "sourceKind": "exchange-filing",
        },
        "powerica": {
            "company": "Powerica Limited",
            "url": "https://nsearchives.nseindia.com/corporate/FP_INE921L01032_30MAR2026.pdf",
            "host": "nsearchives.nseindia.com",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://nsearchives.nseindia.com/corporate/FP_INE921L01032_30MAR2026.pdf",
            "extractionSource": "NSE",
            "documentSource": "NSE",
            "sourceName": "NSE final Prospectus",
            "sourceKind": "exchange-filing",
        },
    }
)


def _previous_failed_companies(payload: dict[str, Any]) -> set[str]:
    """Return canonical issuer names from the immediately previous runner errors."""
    health = (payload.get("meta") or {}).get("issuerOfferDocumentHealth") or {}
    failed: set[str] = set()
    for raw in health.get("errors") or []:
        company = str(raw or "").split(":", 1)[0].strip()
        canonical = base.core.canonical_company(company)
        if canonical:
            failed.add(canonical)
    return failed


def _already_extracted(record: dict[str, Any], spec: dict[str, Any]) -> bool:
    previous = record.get("issuerDocumentExtraction")
    if not isinstance(previous, dict):
        return False
    return bool(
        previous.get("status") == "extracted"
        and previous.get("parserVersion") == base.PARSER_VERSION
        and str(previous.get("documentUrl") or "") == str(spec.get("url") or "")
    )


def _identity_safe_targets(
    payload: dict[str, Any],
    queue: dict[str, Any],
    priority_max: int,
    limit: int,
):
    """Select exact issuers progressively, applying the limit after scheduling.

    Exchange history can legitimately contain multiple rows with the same symbol
    (for example an IPO plus a later withdrawal-option event). Collapsing those
    rows into a single id->record mapping can route a filing to the wrong row.
    This selector therefore requires exactly one issuer-identity match.

    Current-parser successes for the same document are skipped. Issuers reported
    as failures by the previous verified-document batch are sorted behind fresh
    candidates, preventing the bounded fast path from repeatedly spending its
    whole budget on the same slow or temporarily unavailable PDFs.
    """
    by_id: dict[str, list[dict[str, Any]]] = {}
    for record in payload.get("ipos") or []:
        if not isinstance(record, dict) or not record.get("id"):
            continue
        by_id.setdefault(str(record.get("id")), []).append(record)

    previous_failures = _previous_failed_companies(payload)
    candidates: list[tuple[tuple[int, int], dict[str, Any], dict[str, Any], dict[str, Any]]] = []

    for queue_index, item in enumerate(queue.get("queue") or []):
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

        record = matches[0]
        if _already_extracted(record, spec):
            continue

        candidates.append(
            (
                (1 if expected_company in previous_failures else 0, queue_index),
                record,
                item,
                spec,
            )
        )

    candidates.sort(key=lambda entry: entry[0])
    selected = [(record, item, spec) for _, record, item, spec in candidates]
    if limit > 0:
        selected = selected[:limit]
    return selected


base._targets = _identity_safe_targets


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
