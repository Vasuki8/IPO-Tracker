"""Repair canonical static IPO data from Final Prospectuses only.

DRHP/RHP documents may remain linked for historical context, but they are not
eligible to populate canonical static fields. A failed Final Prospectus fetch
never removes prior data; successfully parsed Final Prospectus values supersede
older mixed-source canonical values and retain exact provenance.

The parser also obeys the project phase gate. While P5 is locked, only records in
the actionable P0-P4 queue may be parsed or mutated; historical P5 documents are
left untouched until ``phase_status.json`` explicitly enables P5.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import final_prospectus_identity as identity
import final_prospectus_parser as parser
import final_prospectus_policy as source_policy
import update_data as core

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"
QUEUE_FILE = ROOT / "data" / "missing_queue.json"
PHASE_FILE = ROOT / "data" / "phase_status.json"
CACHE = ROOT / ".cache/offer-documents"
IST = timezone(timedelta(hours=5, minutes=30))
PDF_DOWNLOAD_ATTEMPTS = 3
PDF_DOWNLOAD_TOTAL_SECONDS = 180
PDF_MAX_BYTES = 40 * 1024 * 1024
_TRANSIENT_PDF_ERRORS = (
    requests.ConnectionError,
    requests.Timeout,
    requests.exceptions.ChunkedEncodingError,
    requests.exceptions.ContentDecodingError,
)


def timestamp():
    return datetime.now(IST).isoformat(timespec="seconds")


def document_for(record):
    """Return the safest eligible Final Prospectus, never DRHP/RHP."""
    return identity.choose_candidate(record, source_policy.final_prospectus_candidates(record))


def _download_pdf_once(url: str, deadline: float) -> bytes:
    """Download one bounded PDF attempt without caching partial bytes."""
    with requests.get(url, headers=core.HEADERS, stream=True, timeout=(15, 30)) as response:
        response.raise_for_status()
        chunks, count = [], 0
        for chunk in response.iter_content(131072):
            if time.monotonic() > deadline:
                raise requests.Timeout(
                    f"Official PDF download exceeded its {PDF_DOWNLOAD_TOTAL_SECONDS}-second total retry budget"
                )
            if not chunk:
                continue
            count += len(chunk)
            if count > PDF_MAX_BYTES:
                raise ValueError("Official PDF exceeds bounded 40 MiB extraction budget")
            chunks.append(chunk)
    data = b"".join(chunks)
    if not data.startswith(b"%PDF"):
        raise ValueError("Source returned non-PDF content")
    return data


def pdf_bytes(doc):
    if not source_policy.is_final_prospectus(doc):
        raise ValueError("Canonical static extraction requires a Final Prospectus")
    url = doc["url"]
    if urlparse(url).scheme != "https":
        raise ValueError("Official document must use HTTPS")
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".pdf")
    if path.exists():
        return path.read_bytes()

    deadline = time.monotonic() + PDF_DOWNLOAD_TOTAL_SECONDS
    for attempt in range(1, PDF_DOWNLOAD_ATTEMPTS + 1):
        try:
            data = _download_pdf_once(url, deadline)
            path.write_bytes(data)
            return data
        except _TRANSIENT_PDF_ERRORS:
            if attempt >= PDF_DOWNLOAD_ATTEMPTS or time.monotonic() >= deadline:
                raise
            remaining = max(0.0, deadline - time.monotonic())
            if remaining <= 0:
                raise
            time.sleep(min(0.5 * (2 ** (attempt - 1)), 2.0, remaining))

    raise RuntimeError("Official PDF retry loop ended without a result")


def extract(record, doc):
    data = pdf_bytes(doc)
    text, pages, count = parser.extract_pdf_text(data)
    name = core.canonical_company(record.get("company", ""))
    observed = core.canonical_company(text[:25000])
    text_identity_confirmed = bool(name and name in observed)
    if not text_identity_confirmed and not identity.official_identity_confirmed(record, doc):
        raise ValueError("Issuer identity not confirmed in the document's opening pages or official source metadata")
    parsed = parser.parse_document_text(text, record.get("priceBand"))
    return parsed, hashlib.sha256(data).hexdigest(), pages, count


def _canonical_fields_for_document(record, url):
    out = []
    for field, evidence in (record.get("staticFieldProvenance") or {}).items():
        if isinstance(evidence, dict) and evidence.get("sourceUrl") == url:
            out.append(field)
    return sorted(out)


def correct_record(record, parsed, doc, digest, pages, page_count):
    """Make recognized Final Prospectus static values canonical."""
    now = timestamp()
    changes = source_policy.apply_final_prospectus_static_fields(
        record,
        parsed,
        doc,
        sha256=digest,
        parser_version=parser.PARSER_VERSION,
        checked_at=now,
    )
    if changes:
        record.setdefault("dataCorrections", []).extend(changes)

    canonical_fields = _canonical_fields_for_document(record, doc["url"])
    record["offerDocumentExtraction"] = {
        "status": "extracted",
        "parserVersion": parser.PARSER_VERSION,
        "documentUrl": doc["url"],
        "documentType": "PROSPECTUS",
        "documentTitle": doc.get("title") or "Final Prospectus",
        "documentFiledDate": doc.get("filedDate"),
        "source": doc.get("source", "SEBI"),
        "sha256": digest,
        "pagesRead": pages,
        "pageCount": page_count,
        "extractedFields": parsed.get("extractedFields", []),
        "canonicalFields": canonical_fields,
        "extractedAt": now,
        "conflicts": parsed.get("extractionConflicts", []),
        "sourcePolicy": "final-prospectus-only",
    }
    financial_provenance = (record.get("staticFieldProvenance") or {}).get("financials") or {}
    financial_validated = bool(
        isinstance(financial_provenance, dict)
        and financial_provenance.get("sourceUrl") == doc["url"]
        and financial_provenance.get("value") == record.get("financials")
    )
    record["documentRepair"] = {
        "status": "updated" if changes else "no_change",
        "financialStatus": "validated" if financial_validated else "needs_review",
        "lastAttemptAt": now,
        "parserVersion": parser.PARSER_VERSION,
        "sourcePolicy": "final-prospectus-only",
    }
    return changes


def quarantine_intermediaries(record):
    """Remove obviously invalid legacy intermediary fragments before revalidation."""
    for field in ("leadManagers", "registrar"):
        old = record.get(field)
        if field == "leadManagers":
            if not isinstance(old, list):
                continue
            clean = [name for name in old if parser.valid_manager(name)]
        else:
            if not old or parser.valid_registrar(old):
                continue
            clean = None
        if clean != old:
            record.setdefault("dataCorrections", []).append(
                {
                    "field": field,
                    "before": old,
                    "after": clean,
                    "reason": "Quarantined invalid legacy intermediary data pending Final Prospectus revalidation",
                    "parserVersion": parser.PARSER_VERSION,
                    "correctedAt": timestamp(),
                }
            )
            record[field] = clean


def atomic_save(payload):
    temporary = DATA_FILE.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(DATA_FILE)


def _priority_key(record: dict) -> tuple[str, str]:
    return (
        str(record.get("id") or ""),
        core.canonical_company(str(record.get("company") or "")),
    )


def _load_queue_priorities() -> dict[tuple[str, str], int]:
    if not QUEUE_FILE.exists():
        return {}
    try:
        queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    priorities: dict[tuple[str, str], int] = {}
    for row in queue.get("queue") or []:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        try:
            priority = int(row.get("priority"))
        except (TypeError, ValueError):
            continue
        key = _priority_key(row)
        if not key[0] or not key[1]:
            continue
        priorities[key] = min(priority, priorities.get(key, priority))
    return priorities


def _effective_priority_max(requested: int | None) -> int:
    """Default to P0-P4 unless persisted phase status explicitly enables P5."""
    if requested is not None:
        return max(0, min(5, int(requested)))
    if PHASE_FILE.exists():
        try:
            phase = json.loads(PHASE_FILE.read_text(encoding="utf-8"))
            if (phase.get("p5") or {}).get("status") == "enabled":
                return 5
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    return 4


def _priority_allowed(
    record: dict,
    priorities: dict[tuple[str, str], int],
    priority_max: int,
) -> bool:
    # Once P5 is explicitly enabled, parser-version migrations may legitimately
    # revisit any final document, even if the record is no longer in the queue.
    if priority_max >= 5:
        return True
    priority = priorities.get(_priority_key(record))
    return priority is not None and priority <= priority_max


def run(
    payload,
    limit=8,
    force=False,
    workers=2,
    company=None,
    checkpoint=None,
    cached_only=False,
    priority_max=None,
):
    resolved_priority_max = _effective_priority_max(priority_max)
    priorities = _load_queue_priorities()
    candidates = []
    deferred_by_priority = 0

    for record in payload.get("ipos", []):
        if company and company.lower() not in record.get("company", "").lower():
            continue
        doc = document_for(record)
        if not doc:
            continue
        previous = record.get("offerDocumentExtraction") or {}
        if (
            not force
            and previous.get("parserVersion") == parser.PARSER_VERSION
            and previous.get("status") == "extracted"
            and previous.get("documentUrl") == doc["url"]
            and source_policy.is_final_prospectus(
                {"type": previous.get("documentType"), "title": previous.get("documentTitle")}
            )
        ):
            continue
        if not _priority_allowed(record, priorities, resolved_priority_max):
            deferred_by_priority += 1
            continue
        if cached_only and not (CACHE / (hashlib.sha256(doc["url"].encode()).hexdigest() + ".pdf")).exists():
            continue

        # Do not mutate intermediary fields on a record that the phase gate has
        # deferred. Quarantine is part of the selected record's revalidation.
        quarantine_intermediaries(record)
        repair = record.get("documentRepair") or {}
        candidates.append(
            (
                priorities.get(_priority_key(record), 99),
                repair.get("lastAttemptAt", ""),
                core.canonical_company(record.get("company", "")),
                record,
                doc,
            )
        )

    candidates.sort(key=lambda item: item[:3])
    selected = candidates[:limit] if limit else candidates
    outcomes, changes = [], 0
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 4))) as pool:
        futures = {
            pool.submit(extract, record, doc): (record, doc)
            for _, _, _, record, doc in selected
        }
        for future in as_completed(futures):
            record, doc = futures[future]
            try:
                parsed, digest, pages, count = future.result()
                edits = correct_record(record, parsed, doc, digest, pages, count)
                changes += len(edits)
                outcome = {
                    "id": record["id"],
                    "status": "updated" if edits else "no_change",
                    "changedFields": [entry["field"] for entry in edits],
                }
            except Exception as exc:
                record["documentRepair"] = {
                    "status": "source_blocked" if isinstance(exc, requests.RequestException) else "parse_failed",
                    "lastAttemptAt": timestamp(),
                    "parserVersion": parser.PARSER_VERSION,
                    "sourceUrl": doc["url"],
                    "error": str(exc)[:300],
                    "sourcePolicy": "final-prospectus-only",
                }
                outcome = {"id": record["id"], **record["documentRepair"]}
            outcomes.append(outcome)
            print(json.dumps(outcome), flush=True)
            if checkpoint:
                checkpoint(payload)
    health = {
        "parserVersion": parser.PARSER_VERSION,
        "sourcePolicy": "final-prospectus-only",
        "priorityMax": resolved_priority_max,
        "priorityQueueRecords": len(priorities),
        "deferredByPriority": deferred_by_priority,
        "attempted": len(selected),
        "remaining": len(candidates) - len(selected),
        "changedFields": changes,
        "failed": sum(item["status"] in {"source_blocked", "parse_failed"} for item in outcomes),
        "checkedAt": timestamp(),
        "outcomes": sorted(outcomes, key=lambda item: item["id"]),
    }
    payload.setdefault("meta", {})["documentRepairHealth"] = health
    return health


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--limit", type=int, default=8)
    cli.add_argument("--workers", type=int, default=2)
    cli.add_argument("--force", action="store_true")
    cli.add_argument("--company")
    cli.add_argument("--cached-only", action="store_true")
    cli.add_argument("--priority-max", type=int, choices=range(0, 6))
    args = cli.parse_args()
    payload = json.loads(DATA_FILE.read_text())
    health = run(
        payload,
        max(0, args.limit),
        args.force,
        args.workers,
        args.company,
        atomic_save,
        args.cached_only,
        args.priority_max,
    )
    atomic_save(payload)
    print(json.dumps({key: value for key, value in health.items() if key != "outcomes"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
