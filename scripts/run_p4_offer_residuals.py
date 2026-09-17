#!/usr/bin/env python3
"""Repair recent P4 offer-document residuals without weakening the main parser.

This runner is intentionally narrower than ``run_offer_documents.py``. It only
revisits recent records that are still incomplete or contain clearly invalid
legacy promoter/object extraction, reuses the already-linked official document,
confirms issuer identity, and merges fields recognized by the strict residual
parser. Current P0-P4 queue records with offer/final-prospectus provenance gaps
are always processed before general cleanup candidates.

Unsupported layouts remain missing and are retried only after the residual
parser version changes (unless ``--force`` is supplied).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import final_prospectus_parser as parser  # noqa: E402
import p4_offer_layouts as residual  # noqa: E402
import run_offer_documents as base  # noqa: E402
import update_data as core  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = base.DATA_FILE
QUEUE_FILE = ROOT / "data" / "missing_queue.json"


def _audit_change(record: dict[str, Any], field: str, before: Any, after: Any, doc: dict[str, Any], digest: str) -> None:
    record.setdefault("dataCorrections", []).append(
        {
            "field": field,
            "before": copy.deepcopy(before),
            "after": copy.deepcopy(after),
            "reason": "Revalidated a recent P4 offer-document residual against a strict source layout",
            "sourceUrl": doc["url"],
            "sha256": digest,
            "parserVersion": parser.PARSER_VERSION,
            "residualParserVersion": residual.PARSER_VERSION,
            "correctedAt": base.timestamp(),
        }
    )


def _replace_invalid_residuals(record: dict[str, Any], parsed: dict[str, Any], doc: dict[str, Any], digest: str) -> list[str]:
    changed: list[str] = []
    # Objects and their source-table evidence are accepted together by
    # ``correct_record``. A value-only fallback must never revive rejected rows.
    for field, validator in (
        ("promoters", residual.valid_promoters),
    ):
        before = record.get(field)
        after = parsed.get(field)
        if validator(before) or not validator(after) or before == after:
            continue
        _audit_change(record, field, before, after, doc, digest)
        record[field] = copy.deepcopy(after)
        changed.append(field)

    before_shareholding = record.get("shareholding")
    after_shareholding = parsed.get("shareholding")
    before_pct = (before_shareholding or {}).get("promoterPreIssuePct") if isinstance(before_shareholding, dict) else None
    after_pct = (after_shareholding or {}).get("promoterPreIssuePct") if isinstance(after_shareholding, dict) else None
    if before_pct is None and after_pct is not None and residual._valid_shareholding(after_shareholding):
        record["shareholding"] = copy.deepcopy(after_shareholding)
        changed.append("shareholding")

    return changed


def _retain_verified_document(record: dict[str, Any], doc: dict[str, Any], digest: str) -> bool:
    """Persist an identity-verified source document in canonical provenance."""
    url = str(doc.get("url") or "").strip()
    if not url:
        return False

    entry = {
        "type": doc.get("type") or "Prospectus",
        "title": doc.get("title") or doc.get("type") or "Offer document",
        "url": url,
        "sourcePage": doc.get("sourcePage"),
        "source": doc.get("source") or doc.get("documentSource") or doc.get("extractionSource"),
        "filedDate": doc.get("filedDate"),
        "sha256": digest,
        "verifiedAt": base.timestamp(),
    }
    entry = {key: value for key, value in entry.items() if value not in (None, "")}

    documents = [copy.deepcopy(item) for item in (record.get("documents") or []) if isinstance(item, dict)]
    for index, existing in enumerate(documents):
        if str(existing.get("url") or "").strip() != url:
            continue
        merged = dict(existing)
        for key, value in entry.items():
            if merged.get(key) in (None, ""):
                merged[key] = value
        # A fresh verification time alone is not a meaningful document change.
        if merged.keys() == existing.keys() and all(
            key == "verifiedAt" or merged.get(key) == existing.get(key) for key in merged
        ):
            return False
        if merged != existing:
            documents[index] = merged
            record["documents"] = documents
            return True
        return False

    documents.append(entry)
    record["documents"] = documents
    return True


def extract(record: dict[str, Any], doc: dict[str, Any]):
    data = base.pdf_bytes(doc)
    text, pages, count = parser.extract_pdf_text(data)
    contradictory = base.identity.contradictory_cover_issuer(record, text)
    if contradictory:
        raise ValueError(f"Final Prospectus cover issuer {contradictory!r} contradicts expected issuer {record.get('company')!r}")
    name = core.canonical_company(record.get("company", ""))
    observed = core.canonical_company(text[:25000])
    text_identity_confirmed = bool(name and name in observed)
    if not text_identity_confirmed and not base.identity.official_identity_confirmed(record, doc):
        raise ValueError("Issuer identity not confirmed in the document's opening pages or official source metadata")
    primary = parser.parse_document_text(text, record.get("priceBand"))
    supplement = residual.parse_document_text(text)
    parsed = residual.merge_parsed(primary, supplement)
    return parsed, hashlib.sha256(data).hexdigest(), pages, count


def apply_result(
    record: dict[str, Any], parsed: dict[str, Any], doc: dict[str, Any], digest: str, pages: int, page_count: int
) -> list[str]:
    changed = [entry["field"] for entry in base.correct_record(record, parsed, doc, digest, pages, page_count)]
    for field in _replace_invalid_residuals(record, parsed, doc, digest):
        if field not in changed:
            changed.append(field)
    if _retain_verified_document(record, doc, digest) and "documents" not in changed:
        changed.append("documents")

    # ``correct_record`` persists the combined field evidence. Mark this
    # supplemental pass independently so unchanged unsupported layouts are not
    # downloaded on every maintenance run.
    record["p4OfferResidualRepair"] = {
        "status": "updated" if changed else "no_change",
        "parserVersion": residual.PARSER_VERSION,
        "mainParserVersion": parser.PARSER_VERSION,
        "documentUrl": doc["url"],
        "checkedAt": base.timestamp(),
        "changedFields": changed,
    }
    return changed


def _candidate(
    record: dict[str, Any], force: bool, queue_target: bool = False
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    # The authoritative missing-data queue is allowed to schedule a retry even
    # when the generic residual predicates are already satisfied. This matters
    # for records whose only remaining gaps are Final Prospectus provenance
    # fields such as lot size, fixed issue price, or issue composition.
    if not queue_target and not residual.needs_repair(record):
        return None
    doc = base.document_for(record)
    if not doc:
        return None
    previous = record.get("p4OfferResidualRepair") or {}
    if (
        not force
        and previous.get("parserVersion") == residual.PARSER_VERSION
        and previous.get("mainParserVersion") == parser.PARSER_VERSION
        and previous.get("documentUrl") == doc.get("url")
    ):
        return None
    return record, doc


def p4_offer_queue_order(queue_payload: dict[str, Any]) -> dict[str, int]:
    """Map actionable pre-P5 offer/final-prospectus gaps to authoritative queue order."""
    ordered: dict[str, int] = {}
    for index, row in enumerate(queue_payload.get("queue") or []):
        if not isinstance(row, dict):
            continue
        try:
            priority = int(row.get("priority"))
        except (TypeError, ValueError):
            continue
        if not 0 <= priority <= 4:
            continue
        missing = [str(field) for field in (row.get("missingFields") or [])]
        if not any(
            field.startswith("offer.")
            or field.startswith("provenance.finalProspectus.")
            or field == "provenance.documents"
            for field in missing
        ):
            continue
        record_id = str(row.get("id") or "").strip()
        if record_id and record_id not in ordered:
            ordered[record_id] = index
    return ordered


def _load_queue_payload() -> dict[str, Any]:
    try:
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {"queue": []}


def run(
    payload: dict[str, Any],
    limit: int = 30,
    workers: int = 4,
    force: bool = False,
    checkpoint=None,
    queue_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    queue_order = p4_offer_queue_order(queue_payload if queue_payload is not None else _load_queue_payload())
    candidates = []
    for record in payload.get("ipos") or []:
        if not isinstance(record, dict):
            continue
        record_id = str(record.get("id") or "")
        selected = _candidate(record, force, queue_target=record_id in queue_order)
        if selected:
            candidates.append(selected)

    # Stable two-pass ordering: newest general cleanup first, then place actual
    # pre-P5 offer/provenance gaps ahead of it in the queue's existing order.
    candidates.sort(
        key=lambda pair: (str(pair[0].get("openDate") or ""), str(pair[0].get("company") or "")),
        reverse=True,
    )
    candidates.sort(
        key=lambda pair: (
            0,
            queue_order[str(pair[0].get("id") or "")],
        )
        if str(pair[0].get("id") or "") in queue_order
        else (1, 0)
    )
    selected = candidates[:limit] if limit else candidates

    outcomes: list[dict[str, Any]] = []
    changed_fields = 0
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 4))) as pool:
        futures = {pool.submit(extract, record, doc): (record, doc) for record, doc in selected}
        for future in as_completed(futures):
            record, doc = futures[future]
            try:
                parsed, digest, pages, count = future.result()
                changed = apply_result(record, parsed, doc, digest, pages, count)
                changed_fields += len(changed)
                outcome = {
                    "id": record.get("id"),
                    "status": "updated" if changed else "no_change",
                    "changedFields": changed,
                    "p4QueueTarget": str(record.get("id") or "") in queue_order,
                }
            except Exception as exc:
                record["p4OfferResidualRepair"] = {
                    "status": "source_blocked" if isinstance(exc, base.requests.RequestException) else "parse_failed",
                    "parserVersion": residual.PARSER_VERSION,
                    "mainParserVersion": parser.PARSER_VERSION,
                    "documentUrl": doc.get("url"),
                    "checkedAt": base.timestamp(),
                    "error": str(exc)[:300],
                }
                outcome = {
                    "id": record.get("id"),
                    **record["p4OfferResidualRepair"],
                    "p4QueueTarget": str(record.get("id") or "") in queue_order,
                }
            outcomes.append(outcome)
            print(json.dumps(outcome), flush=True)
            if checkpoint:
                checkpoint(payload)

    selected_ids = {str(record.get("id") or "") for record, _doc in selected}
    health = {
        "parserVersion": residual.PARSER_VERSION,
        "mainParserVersion": parser.PARSER_VERSION,
        "targets": len(candidates),
        "p4QueueTargets": len(queue_order),
        "p4QueueTargetsAttempted": len(selected_ids & set(queue_order)),
        "attempted": len(selected),
        "remaining": max(0, len(candidates) - len(selected)),
        "changedFields": changed_fields,
        "failed": sum(item.get("status") in {"source_blocked", "parse_failed"} for item in outcomes),
        "checkedAt": base.timestamp(),
        "outcomes": sorted(outcomes, key=lambda item: str(item.get("id") or "")),
    }
    payload.setdefault("meta", {})["p4OfferResidualHealth"] = health
    return health


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--limit", type=int, default=30)
    cli.add_argument("--workers", type=int, default=4)
    cli.add_argument("--force", action="store_true")
    args = cli.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    health = run(payload, max(0, args.limit), args.workers, args.force, base.atomic_save)
    base.atomic_save(payload)
    print(json.dumps({key: value for key, value in health.items() if key != "outcomes"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
