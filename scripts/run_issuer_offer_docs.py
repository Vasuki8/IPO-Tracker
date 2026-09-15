#!/usr/bin/env python3
"""Run verified issuer/regulator offer-document fallbacks through one stable path.

The runner preserves the established exact-host, PDF-magic, issuer-identity and
fill-only gates while using the final legacy parser contract (v14). Verified
fallback registrations live separately in issuer_offer_registry.py so adding a
source no longer requires another executable parser wrapper.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import legacy_offer_parser as parser  # noqa: E402
from issuer_offer_registry import VALIDATED_OFFER_DOCUMENTS  # noqa: E402
from parser_loader import isolated_module  # noqa: E402

base = isolated_module("enrich_issuer_offer_docs")

# Preserve the final effective v4 behavior without traversing v2/v3/v4 or the
# numbered offer-parser aliases. The generic targeted parser remains compatible
# with the issuer runner's financial/shareholding call contract and also retains
# the finalized lot/price deep-page recognition introduced before v14.
base.parser_v4 = parser
base.PARSER_VERSION = parser.PARSER_VERSION
base._extract_targeted_full_text = parser.extract_targeted_pdf_text
base.ISSUER_DOCUMENTS.update(VALIDATED_OFFER_DOCUMENTS)

_ORIGINAL_MERGE = base.merge_issuer_enrichment


def merge_validated_offer_enrichment(
    record,
    parsed,
    doc,
    *,
    pdf_hash,
    pages_read,
    page_count,
):
    """Fill missing fields and preserve source-specific provenance observations."""
    changed = list(
        _ORIGINAL_MERGE(
            record,
            parsed,
            doc,
            pdf_hash=pdf_hash,
            pages_read=pages_read,
            page_count=page_count,
        )
        or []
    )

    extraction_source = str(doc.get("extractionSource") or "").strip()
    document_source = str(doc.get("documentSource") or "").strip()
    source_name = str(doc.get("sourceName") or "").strip()
    source_kind = str(doc.get("sourceKind") or "").strip()
    source_page = str(doc.get("sourcePage") or doc.get("url") or "")
    url = str(doc.get("url") or "")

    extraction = record.get("issuerDocumentExtraction")
    if isinstance(extraction, dict):
        extraction["parserVersion"] = parser.PARSER_VERSION
        extraction["extractedFields"] = parsed.get("extractedFields") or []
        if extraction_source:
            extraction["source"] = extraction_source

    if document_source:
        for item in record.get("documents") or []:
            if isinstance(item, dict) and str(item.get("url") or "") == url:
                item["source"] = document_source

    if source_name or source_kind:
        for source in record.get("sources") or []:
            if not isinstance(source, dict) or str(source.get("url") or "") != source_page:
                continue
            if source_name:
                source["name"] = source_name
            if source_kind:
                source["kind"] = source_kind

    lot_size = parsed.get("lotSize")
    price_band = parsed.get("priceBand")
    term_changes: list[str] = []
    if record.get("lotSize") is None and lot_size is not None:
        record["lotSize"] = lot_size
        term_changes.append("lotSize")
    if record.get("priceBand") in (None, {}, []) and price_band:
        record["priceBand"] = price_band
        term_changes.append("priceBand")

    if lot_size is not None or price_band:
        observation_source = str(
            doc.get("extractionSource")
            or doc.get("documentSource")
            or "Issuer website"
        )
        observation = {
            "documentUrl": doc.get("url"),
            "documentType": doc.get("type"),
            "documentFiledDate": doc.get("filedDate"),
            "parserVersion": parser.PARSER_VERSION,
            "source": observation_source,
        }
        if lot_size is not None:
            observation["lotSize"] = lot_size
        if price_band:
            observation["priceBand"] = price_band
        record.setdefault("observations", {})["Offer-document"] = observation

    if isinstance(extraction, dict) and term_changes:
        existing = list(extraction.get("changedFields") or [])
        extraction["changedFields"] = list(dict.fromkeys(existing + term_changes))

    return list(dict.fromkeys(changed + term_changes))


base.merge_issuer_enrichment = merge_validated_offer_enrichment


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
    """Select exactly one verified issuer per id and schedule fresh work first."""
    by_id: dict[str, list[dict[str, Any]]] = {}
    for record in payload.get("ipos") or []:
        if not isinstance(record, dict) or not record.get("id"):
            continue
        by_id.setdefault(str(record.get("id")), []).append(record)

    previous_failures = _previous_failed_companies(payload)
    candidates: list[
        tuple[tuple[int, int], dict[str, Any], dict[str, Any], dict[str, Any]]
    ] = []

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
            if base.core.canonical_company(str(record.get("company") or ""))
            == expected_company
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
    return selected[:limit] if limit > 0 else selected


base._targets = _identity_safe_targets


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
