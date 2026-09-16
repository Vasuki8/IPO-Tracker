#!/usr/bin/env python3
"""Run verified Final Prospectus fallbacks through one stable path.

Only explicitly final Prospectus documents are eligible to populate canonical
static IPO fields. Historical DRHP/RHP registry entries remain inert and may be
retained for document history, but they are never selected by this runner.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import final_prospectus_policy as source_policy  # noqa: E402
import legacy_offer_parser as parser  # noqa: E402
from issuer_offer_registry import VALIDATED_OFFER_DOCUMENTS  # noqa: E402
from parser_loader import isolated_module  # noqa: E402

base = isolated_module("enrich_issuer_offer_docs")
base.parser_v4 = parser
base.PARSER_VERSION = parser.PARSER_VERSION
base._extract_targeted_full_text = parser.extract_targeted_pdf_text

combined = dict(base.ISSUER_DOCUMENTS)
combined.update(VALIDATED_OFFER_DOCUMENTS)
base.ISSUER_DOCUMENTS = {
    record_id: spec
    for record_id, spec in combined.items()
    if source_policy.is_final_prospectus(spec)
}

_ORIGINAL_MERGE = base.merge_issuer_enrichment
_ORIGINAL_NEEDS_DEEP_SCAN = base._needs_deep_scan
FINAL_REVALIDATION_PREFIX = "provenance.finalProspectus."


def _revalidation_gaps(item: dict[str, Any]) -> set[str]:
    missing = {str(field) for field in (item.get("missingFields") or [])}
    return {
        field[len(FINAL_REVALIDATION_PREFIX):]
        for field in missing
        if field.startswith(FINAL_REVALIDATION_PREFIX)
    }


def _has_priority_or_revalidation_gap(item: dict[str, Any]) -> bool:
    return bool(base._has_priority_gap(item) or _revalidation_gaps(item))


def _needs_deep_scan_with_revalidation(
    item: dict[str, Any], parsed: dict[str, Any]
) -> tuple[bool, bool]:
    need_financials, need_shareholding = _ORIGINAL_NEEDS_DEEP_SCAN(item, parsed)
    pending = _revalidation_gaps(item)
    if "financials" in pending and not parsed.get("financials"):
        need_financials = True
    if "shareholding" in pending and not parsed.get("shareholding"):
        need_shareholding = True
    return need_financials, need_shareholding


base._needs_deep_scan = _needs_deep_scan_with_revalidation


def merge_validated_offer_enrichment(
    record,
    parsed,
    doc,
    *,
    pdf_hash,
    pages_read,
    page_count,
):
    if not source_policy.is_final_prospectus(doc):
        raise ValueError("Verified offer fallback is not a Final Prospectus")

    original_changed = list(
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

    checked_at = base.core.now_ist().isoformat(timespec="seconds")
    policy_changes = source_policy.apply_final_prospectus_static_fields(
        record,
        parsed,
        doc,
        sha256=pdf_hash,
        parser_version=parser.PARSER_VERSION,
        checked_at=checked_at,
    )
    if policy_changes:
        record.setdefault("dataCorrections", []).extend(policy_changes)

    extraction_source = str(doc.get("extractionSource") or "").strip()
    document_source = str(doc.get("documentSource") or "").strip()
    source_name = str(doc.get("sourceName") or "").strip()
    source_kind = str(doc.get("sourceKind") or "").strip()
    source_page = str(doc.get("sourcePage") or doc.get("url") or "")
    url = str(doc.get("url") or "")

    extraction = record.get("issuerDocumentExtraction")
    if isinstance(extraction, dict):
        extraction["parserVersion"] = parser.PARSER_VERSION
        extraction["documentType"] = "PROSPECTUS"
        extraction["extractedFields"] = parsed.get("extractedFields") or []
        extraction["sourcePolicy"] = "final-prospectus-only"
        if extraction_source:
            extraction["source"] = extraction_source

    if document_source:
        for item in record.get("documents") or []:
            if isinstance(item, dict) and str(item.get("url") or "") == url:
                item["source"] = document_source
                item["type"] = "PROSPECTUS"

    if source_name or source_kind:
        for source in record.get("sources") or []:
            if not isinstance(source, dict) or str(source.get("url") or "") != source_page:
                continue
            if source_name:
                source["name"] = source_name
            if source_kind:
                source["kind"] = source_kind

    observation = {
        "documentUrl": doc.get("url"),
        "documentType": "PROSPECTUS",
        "documentFiledDate": doc.get("filedDate"),
        "parserVersion": parser.PARSER_VERSION,
        "source": extraction_source or document_source or "Issuer website",
        "sourcePolicy": "final-prospectus-only",
    }
    for field in ("lotSize", "priceBand", "issueComposition"):
        if parsed.get(field) not in (None, "", [], {}):
            observation[field] = parsed[field]
    record.setdefault("observations", {})["FinalProspectus"] = observation

    changed_fields = list(dict.fromkeys(
        original_changed + [entry["field"] for entry in policy_changes]
    ))
    if isinstance(extraction, dict):
        extraction["changedFields"] = changed_fields
    return changed_fields


base.merge_issuer_enrichment = merge_validated_offer_enrichment


def _previous_failed_companies(payload: dict[str, Any]) -> set[str]:
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
        and source_policy.is_final_prospectus(
            {
                "type": previous.get("documentType"),
                "title": previous.get("documentTitle"),
            }
        )
    )


def _identity_safe_targets(
    payload: dict[str, Any],
    queue: dict[str, Any],
    priority_max: int,
    limit: int,
):
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
        if priority > priority_max or not spec or not _has_priority_or_revalidation_gap(item):
            continue
        if not source_policy.is_final_prospectus(spec):
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
        if _already_extracted(record, spec) and not _revalidation_gaps(item):
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
