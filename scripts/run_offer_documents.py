"""Repair and maintain document-derived data using the current parser.

Successful corrections retain old values and exact document provenance. A
failed fetch never removes prior data. Confidently identified contamination is
quarantined even when a replacement is not yet available.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import offer_parser as parser
import update_data as core

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data/ipos.json"
CACHE = ROOT / ".cache/offer-documents"
IST = timezone(timedelta(hours=5, minutes=30))


def timestamp():
    return datetime.now(IST).isoformat(timespec="seconds")


def document_for(record):
    previous = record.get("offerDocumentExtraction") or {}
    selected = parser.choose_document(record)
    if selected and (not previous.get('documentUrl') or str(selected.get('filedDate') or '') > str(previous.get('documentFiledDate') or '')):
        return selected
    if previous.get("documentUrl"):
        return {"url": previous["documentUrl"], "type": previous.get("documentType", "PROSPECTUS"), "title": previous.get("documentTitle", "Official offer document"), "source": previous.get("source", "SEBI"), "filedDate": previous.get("documentFiledDate")}
    return selected


def pdf_bytes(doc):
    url = doc["url"]
    if urlparse(url).scheme != "https":
        raise ValueError("Official document must use HTTPS")
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".pdf")
    if path.exists():
        return path.read_bytes()
    # The URL must have come from the record's source-linked document registry.
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
    changes, now = [], timestamp()
    for field in ("leadManagers", "registrar", "financials"):
        before, after = record.get(field), parsed.get(field)
        # A strict parser can retire a known-bad financial extraction, but does
        # not erase an established valid intermediary on an unsupported layout.
        if not after and field == "leadManagers":
            after = [name for name in (before or []) if parser.valid_manager(name)]
        if not after and field == "registrar":
            continue
        if not after and field == "financials":
            # Unsupported layout is not evidence that an existing disclosure
            # is false. Keep it explicitly pending source-table review.
            continue
        if before != after:
            changes.append({"field": field, "before": copy.deepcopy(before), "after": copy.deepcopy(after), "reason": "Revalidated financial table or intermediary role against source document", "sourceUrl": doc["url"], "sha256": digest, "parserVersion": parser.PARSER_VERSION, "correctedAt": now})
            record[field] = after
    # Existing official exchange terms remain authoritative and fill-only.
    for field in ("lotSize", "priceBand"):
        if record.get(field) in (None, {}, "") and parsed.get(field) not in (None, {}):
            record[field] = parsed[field]
    for field in ("promoters", "objectsOfIssue", "shareholding"):
        if record.get(field) in (None, [], {}) and parsed.get(field) not in (None, [], {}):
            record[field] = parsed[field]
    if changes:
        record.setdefault("dataCorrections", []).extend(changes)
    provenance = {"sourceUrl": doc["url"], "documentType": doc.get("type"), "documentDate": doc.get("filedDate"), "sha256": digest, "parserVersion": parser.PARSER_VERSION, "checkedAt": now, "evidence": parsed.get("fieldEvidence", {})}
    record["documentFieldProvenance"] = provenance
    record["offerDocumentExtraction"] = {"status": "extracted", "parserVersion": parser.PARSER_VERSION, "documentUrl": doc["url"], "documentType": doc.get("type"), "documentTitle": doc.get("title"), "documentFiledDate": doc.get("filedDate"), "source": doc.get("source", "SEBI"), "sha256": digest, "pagesRead": pages, "pageCount": page_count, "extractedFields": parsed.get("extractedFields", []), "extractedAt": now, "conflicts": parsed.get("extractionConflicts", [])}
    record["documentRepair"] = {"status": "updated" if changes else "no_change", "financialStatus": "validated" if parsed.get("financials") else "needs_review", "lastAttemptAt": now, "parserVersion": parser.PARSER_VERSION}
    return changes


def quarantine_intermediaries(record):
    for field in ('leadManagers', 'registrar'):
        old = record.get(field)
        if field == 'leadManagers':
            if not isinstance(old, list):
                continue
            clean = [name for name in old if parser.valid_manager(name)]
        else:
            if not old or parser.valid_registrar(old):
                continue
            clean = None
        if clean != old:
            record.setdefault("dataCorrections", []).append({"field": field, "before": old, "after": clean, "reason": "Quarantined exchange names, incomplete entities, and table headers from intermediary field", "parserVersion": parser.PARSER_VERSION, "correctedAt": timestamp()})
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
        if cached_only and not (CACHE / (hashlib.sha256(doc['url'].encode()).hexdigest() + '.pdf')).exists():
            continue
        previous = record.get("offerDocumentExtraction") or {}
        if not force and previous.get("parserVersion") == parser.PARSER_VERSION and previous.get("status") == "extracted" and previous.get("documentUrl") == doc["url"]:
            continue
        repair = record.get("documentRepair") or {}
        candidates.append((repair.get("lastAttemptAt", ""), core.canonical_company(record.get("company", "")), record, doc))
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
                outcome = {"id": record["id"], "status": "updated" if edits else "no_change", "changedFields": [entry["field"] for entry in edits]}
            except Exception as exc:
                record["documentRepair"] = {"status": "source_blocked" if isinstance(exc, requests.RequestException) else "parse_failed", "lastAttemptAt": timestamp(), "parserVersion": parser.PARSER_VERSION, "sourceUrl": doc["url"], "error": str(exc)[:300]}
                outcome = {"id": record["id"], **record["documentRepair"]}
            outcomes.append(outcome)
            print(json.dumps(outcome), flush=True)
            if checkpoint:
                checkpoint(payload)
    health = {"parserVersion": parser.PARSER_VERSION, "attempted": len(selected), "remaining": len(candidates) - len(selected), "changedFields": changes, "failed": sum(item["status"] in {"source_blocked", "parse_failed"} for item in outcomes), "checkedAt": timestamp(), "outcomes": sorted(outcomes, key=lambda item: item["id"])}
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
