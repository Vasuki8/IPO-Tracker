#!/usr/bin/env python3
"""Repair recent P4 offer-document residuals without weakening the main parser.

This runner is intentionally narrower than ``run_offer_documents.py``. It only
revisits recent records that are still incomplete or contain clearly invalid
legacy promoter/object extraction, reuses the already-linked official document,
confirms issuer identity, and merges fields recognized by the strict residual
parser. Unsupported layouts remain missing and are retried only after the
residual parser version changes (unless ``--force`` is supplied).
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

import offer_parser as parser  # noqa: E402
import p4_offer_parser as residual  # noqa: E402
import run_offer_documents as base  # noqa: E402
import update_data as core  # noqa: E402

DATA_FILE = base.DATA_FILE


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
    for field, validator in (
        ("promoters", residual.valid_promoters),
        ("objectsOfIssue", residual.valid_objects),
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


def extract(record: dict[str, Any], doc: dict[str, Any]):
    data = base.pdf_bytes(doc)
    text, pages, count = parser.extract_pdf_text(data)
    name = core.canonical_company(record.get("company", ""))
    observed = core.canonical_company(text[:25000])
    if not name or name not in observed:
        raise ValueError("Issuer identity not confirmed in the document's opening pages")
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


def _candidate(record: dict[str, Any], force: bool) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if not residual.needs_repair(record):
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


def run(payload: dict[str, Any], limit: int = 30, workers: int = 4, force: bool = False, checkpoint=None) -> dict[str, Any]:
    candidates = []
    for record in payload.get("ipos") or []:
        if not isinstance(record, dict):
            continue
        selected = _candidate(record, force)
        if selected:
            candidates.append(selected)
    candidates.sort(key=lambda pair: (str(pair[0].get("openDate") or ""), str(pair[0].get("company") or "")), reverse=True)
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
                outcome = {"id": record.get("id"), "status": "updated" if changed else "no_change", "changedFields": changed}
            except Exception as exc:
                record["p4OfferResidualRepair"] = {
                    "status": "source_blocked" if isinstance(exc, base.requests.RequestException) else "parse_failed",
                    "parserVersion": residual.PARSER_VERSION,
                    "mainParserVersion": parser.PARSER_VERSION,
                    "documentUrl": doc.get("url"),
                    "checkedAt": base.timestamp(),
                    "error": str(exc)[:300],
                }
                outcome = {"id": record.get("id"), **record["p4OfferResidualRepair"]}
            outcomes.append(outcome)
            print(json.dumps(outcome), flush=True)
            if checkpoint:
                checkpoint(payload)

    health = {
        "parserVersion": residual.PARSER_VERSION,
        "mainParserVersion": parser.PARSER_VERSION,
        "targets": len(candidates),
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
