"""Repair canonical static IPO data from Final Prospectuses only.

DRHP/RHP documents may remain linked for historical context, but they are not
eligible to populate canonical static fields. A failed Final Prospectus fetch
never removes prior data; successfully parsed Final Prospectus values supersede
older mixed-source canonical values and retain exact provenance.
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
import final_prospectus_policy as source_policy
import offer_parser as parser
import update_data as core

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"
CACHE = ROOT / ".cache/offer-documents"
IST = timezone(timedelta(hours=5, minutes=30))


def timestamp():
    return datetime.now(IST).isoformat(timespec="seconds")


def document_for(record):
    """Return the newest eligible Final Prospectus, never DRHP/RHP."""
    return source_policy.choose_final_prospectus(record)


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
    started = time.monotonic()
    with requests.get(url, headers=core.HEADERS, stream=True, timeout=(15, 30)) as response:
        response.raise_for_status()
        chunks, count = [], 0
        for chunk in response.iter_content(131072):
            if time.monotonic() - started > 120:
                raise requests.Timeout("Official PDF download exceeded its 120-second total budget")
            count += len(chunk)
            if count > 40 * 1024 * 1024:
                raise ValueError("Official PDF exceeds bounded 40 MiB extraction budget")
            chunks.append(chunk)
    data = b"".join(chunks)
    if not data.startswith(b"%PDF"):
        raise ValueError("Source returned non-PDF content")
    path.write_bytes(data)
    return data


def extract(record, doc):
    data = pdf_bytes(doc)
    text, pages, count = parser.extract_pdf_text(data)
    name = core.canonical_company(record.get("company", ""))
    observed = core.canonical_company(text[:25000])
    if not name or name not in observed:
        raise ValueError("Issuer identity not confirmed in the document's opening pages")
    parsed = parser.parse_document_text(text, record.get("priceBand"))
    return parsed, hashlib.sha256(data).hexdigest(), pages, count


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

    provenance = {
        "sourceUrl": doc["url"],
        "documentType": "PROSPECTUS",
        "documentDate": doc.get("filedDate"),
        "sha256": digest,
        "parserVersion": parser.PARSER_VERSION,
        "checkedAt": now,
        "evidence": parsed.get("fieldEvidence", {}),
        "sourcePolicy": "final-prospectus-only",
    }
    record["documentFieldProvenance"] = provenance
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
        "extractedAt": now,
        "conflicts": parsed.get("extractionConflicts", []),
        "sourcePolicy": "final-prospectus-only",
    }
    record["documentRepair"] = {
        "status": "updated" if changes else "no_change",
        "financialStatus": "validated" if parsed.get("financials") else "needs_review",
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


def run(payload, limit=8, force=False, workers=2, company=None, checkpoint=None, cached_only=False):
    candidates = []
    for record in payload.get("ipos", []):
        quarantine_intermediaries(record)
        if company and company.lower() not in record.get("company", "").lower():
            continue
        doc = document_for(record)
        if not doc:
            continue
        if cached_only and not (CACHE / (hashlib.sha256(doc["url"].encode()).hexdigest() + ".pdf")).exists():
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
        repair = record.get("documentRepair") or {}
        candidates.append(
            (
                repair.get("lastAttemptAt", ""),
                core.canonical_company(record.get("company", "")),
                record,
                doc,
            )
        )
    candidates.sort(key=lambda item: item[:2])
    selected = candidates[:limit] if limit else candidates
    outcomes, changes = [], 0
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 4))) as pool:
        futures = {pool.submit(extract, record, doc): (record, doc) for _, _, record, doc in selected}
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
    args = cli.parse_args()
    payload = json.loads(DATA_FILE.read_text())
    health = run(payload, max(0, args.limit), args.force, args.workers, args.company, atomic_save, args.cached_only)
    atomic_save(payload)
    print(json.dumps({key: value for key, value in health.items() if key != "outcomes"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
