#!/usr/bin/env python3
"""Run parser-v13 offer-document extraction with progressive bounded retries.

The extraction, quality gates and fill-only merge semantics remain parser v13.
This wrapper changes only candidate scheduling: never-attempted documents are
processed before current-parser errors, and failed documents are retried oldest
first. A bounded daily run therefore advances through the eligible backlog
instead of repeatedly spending its entire budget on the same front-slice errors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_offer_docs_v13 as parser_v13  # noqa: E402

base = parser_v13.base
PARSER_VERSION = parser_v13.PARSER_VERSION
DATA_FILE = base.DATA_FILE
SCHEDULER_VERSION = 1


def candidate_sort_key(record: dict[str, Any], doc: dict[str, Any]) -> tuple[Any, ...]:
    """Unattempted first; current-parser failures retry oldest first."""
    previous = record.get("offerDocumentExtraction")
    previous = previous if isinstance(previous, dict) else {}
    same_error = bool(
        previous.get("status") == "error"
        and previous.get("parserVersion") == PARSER_VERSION
        and str(previous.get("documentUrl") or "") == str(doc.get("url") or "")
    )
    retry_at = str(previous.get("lastAttemptAt") or "") if same_error else ""
    return (
        1 if same_error else 0,
        retry_at,
        *base.priority(record),
    )


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--limit", type=int, default=6)
    cli.add_argument("--force", action="store_true")
    cli.add_argument("--company", default=None)
    args = cli.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = payload.get("ipos") or []
    session = requests.Session()
    session.headers.update(base.HEADERS)

    candidates: list[tuple[tuple[Any, ...], dict[str, Any], dict[str, Any]]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        if args.company and args.company.lower() not in str(record.get("company") or "").lower():
            continue
        doc = parser_v13.choose_document(record)
        if not doc:
            continue
        previous = record.get("offerDocumentExtraction") or {}
        if (
            not args.force
            and isinstance(previous, dict)
            and previous.get("status") == "extracted"
            and previous.get("parserVersion") == PARSER_VERSION
            and previous.get("documentUrl") == doc.get("url")
        ):
            continue
        candidates.append((candidate_sort_key(record, doc), record, doc))

    candidates.sort(key=lambda item: item[0])
    total_eligible = len(candidates)
    if args.limit > 0:
        candidates = candidates[: args.limit]

    attempted = extracted = failed = 0
    errors: list[str] = []
    for _, record, doc in candidates:
        attempted += 1
        try:
            data = parser_v13.download_pdf(session, doc["url"])
            text, pages_read, page_count = parser_v13.extract_pdf_text(data)
            parsed = parser_v13.parse_document_text(text, record.get("priceBand"))
            if not parsed.get("extractedFields"):
                raise ValueError("no structured fields recognized")
            digest = hashlib.sha256(data).hexdigest()
            parser_v13.apply_enrichment(
                record,
                parsed,
                doc,
                digest,
                pages_read,
                page_count,
            )
            extracted += 1
            print(
                f"Extracted {record.get('company')}: "
                f"{', '.join(parsed.get('extractedFields') or [])}"
            )
        except Exception as exc:
            failed += 1
            message = f"{record.get('company')}: {exc}"
            errors.append(message)
            record["offerDocumentExtraction"] = {
                "status": "error",
                "parserVersion": PARSER_VERSION,
                "schedulerVersion": SCHEDULER_VERSION,
                "documentUrl": doc.get("url"),
                "lastAttemptAt": base.now_ist().isoformat(timespec="seconds"),
                "error": str(exc)[:300],
                "source": "SEBI",
            }
            print(f"Offer document extraction failed: {message}")

    meta = payload.setdefault("meta", {})
    meta["schemaVersion"] = max(int(meta.get("schemaVersion") or 1), 3)
    meta["offerDocumentHealth"] = {
        "ok": failed == 0 if attempted else True,
        "attempted": attempted,
        "extracted": extracted,
        "failed": failed,
        "eligibleRemaining": max(0, total_eligible - extracted),
        "parserVersion": PARSER_VERSION,
        "schedulerVersion": SCHEDULER_VERSION,
        "asOf": base.now_ist().isoformat(timespec="seconds"),
        "errors": errors[:10],
    }
    meta.setdefault("sourceHealth", {})["Offer-docs"] = {
        "ok": failed == 0 if attempted else True,
        "records": extracted,
        "attempted": attempted,
        "failed": failed,
        "parserVersion": PARSER_VERSION,
        "schedulerVersion": SCHEDULER_VERSION,
    }

    DATA_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        "Offer docs progressive: "
        f"attempted={attempted}, extracted={extracted}, failed={failed}, "
        f"eligible={total_eligible}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
