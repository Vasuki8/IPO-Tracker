#!/usr/bin/env python3
"""Run verified Final Prospectus fallbacks through one stable path.

Only explicitly final Prospectus documents are eligible to populate canonical
static IPO fields. Historical DRHP/RHP registry entries remain inert and may be
retained for document history, but they are never selected by this runner.

All canonical static writes, including financials and their table evidence, go
through ``final_prospectus_policy``. The historical issuer helper is used for
bounded downloading/target selection only and cannot independently mutate
canonical static fields.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import final_prospectus_parser as parser  # noqa: E402
import final_prospectus_policy as source_policy  # noqa: E402
from issuer_offer_registry import VALIDATED_OFFER_DOCUMENTS  # noqa: E402
from parser_loader import isolated_module  # noqa: E402

base = isolated_module("enrich_issuer_offer_docs")
# ``enrich_issuer_offer_docs.main`` expects its parser module to expose the
# downloader plus ``base.extract_pdf_text``. The current Final Prospectus parser
# delegates both to the current strict offer parser; no legacy whole-document
# parser is used for canonical extraction.
parser.download_pdf = parser.base.download_pdf
base.parser_v4 = parser
base.PARSER_VERSION = parser.PARSER_VERSION

combined = dict(base.ISSUER_DOCUMENTS)
combined.update(VALIDATED_OFFER_DOCUMENTS)
base.ISSUER_DOCUMENTS = {
    record_id: spec
    for record_id, spec in combined.items()
    if source_policy.is_final_prospectus(spec)
}

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


def _canonical_fields_for_document(record: dict[str, Any], url: str) -> list[str]:
    fields = []
    for field, evidence in (record.get("staticFieldProvenance") or {}).items():
        if isinstance(evidence, dict) and str(evidence.get("sourceUrl") or "") == url:
            fields.append(str(field))
    return sorted(fields)


def _record_document_metadata(record: dict[str, Any], doc: dict[str, Any]) -> None:
    url = str(doc.get("url") or "")
    document_source = str(doc.get("documentSource") or "").strip()
    documents = [d for d in (record.get("documents") or []) if isinstance(d, dict)]
    existing = next((item for item in documents if str(item.get("url") or "") == url), None)
    if existing is None:
        existing = {
            "type": "PROSPECTUS",
            "title": doc.get("title") or "Final Prospectus",
            "url": url,
            "filedDate": doc.get("filedDate"),
            "source": document_source or doc.get("source") or "Issuer website",
        }
        documents.append(existing)
    else:
        existing["type"] = "PROSPECTUS"
        if doc.get("title"):
            existing["title"] = doc.get("title")
        if doc.get("filedDate"):
            existing["filedDate"] = doc.get("filedDate")
        if document_source:
            existing["source"] = document_source
    record["documents"] = base.core.dedupe_dicts(documents, ("url", "type"))

    source_name = str(doc.get("sourceName") or "").strip()
    source_kind = str(doc.get("sourceKind") or "").strip()
    source_page = str(doc.get("sourcePage") or url)
    sources = [s for s in (record.get("sources") or []) if isinstance(s, dict)]
    matching = next((s for s in sources if str(s.get("url") or "") == source_page), None)
    if matching is None:
        matching = base.core.source_stamp(
            source_name or "Final Prospectus",
            source_page,
            source_kind or "issuer-filing",
        )
        sources.append(matching)
    else:
        if source_name:
            matching["name"] = source_name
        if source_kind:
            matching["kind"] = source_kind
    record["sources"] = base.core.dedupe_dicts(sources, ("name", "url"))


def merge_validated_offer_enrichment(
    record,
    parsed,
    doc,
    *,
    pdf_hash,
    pages_read,
    page_count,
):
    """Promote only policy-validated Final Prospectus static fields atomically."""
    if not source_policy.is_final_prospectus(doc):
        raise ValueError("Verified offer fallback is not a Final Prospectus")

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

    _record_document_metadata(record, doc)

    extraction_source = str(doc.get("extractionSource") or "").strip()
    document_source = str(doc.get("documentSource") or "").strip()
    url = str(doc.get("url") or "")
    changed_fields = [entry["field"] for entry in policy_changes]
    canonical_fields = _canonical_fields_for_document(record, url)
    record["issuerDocumentExtraction"] = {
        "status": "extracted",
        "parserVersion": parser.PARSER_VERSION,
        "documentUrl": url,
        "documentType": "PROSPECTUS",
        "documentTitle": doc.get("title") or "Final Prospectus",
        "sourcePage": doc.get("sourcePage"),
        "sha256": pdf_hash,
        "pagesRead": pages_read,
        "pageCount": page_count,
        "extractedFields": parsed.get("extractedFields") or [],
        "canonicalFields": canonical_fields,
        "changedFields": changed_fields,
        "extractedAt": checked_at,
        "source": extraction_source or document_source or "Issuer website",
        "sourcePolicy": "final-prospectus-only",
    }

    observation = {
        "documentUrl": url,
        "documentType": "PROSPECTUS",
        "documentFiledDate": doc.get("filedDate"),
        "parserVersion": parser.PARSER_VERSION,
        "source": extraction_source or document_source or "Issuer website",
        "sourcePolicy": "final-prospectus-only",
        "canonicalStaticFieldsWritten": canonical_fields,
    }
    for field in ("lotSize", "priceBand", "issueComposition"):
        if parsed.get(field) not in (None, "", [], {}):
            observation[field] = parsed[field]
    record.setdefault("observations", {})["FinalProspectus"] = observation
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
