#!/usr/bin/env python3
"""NSE offer-filings collector under the Final Prospectus source policy.

NSE remains useful for two things here:
1. dynamic/post-offer listing observations from the final-listing XBRL; and
2. discovery of the issuer's official Final Prospectus PDF.

Static XBRL terms such as Market Lot and Final Issue Price are observations only.
Final Prospectus discovery is deliberately independent of whether legacy static
fields are already populated: a record with lot size/registrar/lead managers but
without a Final Prospectus must still be discovered and revalidated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import collect_nse_offer_filings as base  # noqa: E402
import final_prospectus_policy as final_policy  # noqa: E402

DISCOVERY_ATTEMPT = "nseFinalProspectusDiscovery"
DISCOVERY_WINDOW_DAYS = 60


def merge_dynamic_only(record, entry, cells, url, digest):
    if not base.archive_url(url, ".xml") or not base.verified_terms(record, entry, cells):
        return []

    evidence = {
        "source": "NSE final-listing XBRL",
        "sourceUrl": url,
        "registerUrl": base.PAGE,
        "sha256": digest,
        "company": entry["company"],
        "symbol": cells.get("ScripID"),
        "isin": cells.get("ISIN"),
        "issueOpenDate": base.source_date(cells["DateOfIssueOpen"]),
        "issueCloseDate": base.source_date(cells["DateOfIssueClose"]),
        "sourcePolicy": "dynamic-observation-only",
    }

    changed = []
    listed = base.source_date(cells.get("DateOfListing"))
    if listed and not record.get("listingDate"):
        record["listingDate"] = listed
        record["listingDateEvidence"] = {
            **evidence,
            "field": "DateOfListing",
            "value": listed,
            "checkedAt": base.stamp(),
        }
        changed.append("listingDate")

    record.setdefault("observations", {})["NSEFinalListing"] = {
        **evidence,
        "fields": cells,
        "canonicalStaticFieldsWritten": [],
    }
    if not any(source.get("url") == url for source in record.get("sources", [])):
        record.setdefault("sources", []).append(
            base.core.source_stamp("NSE final-listing XBRL", url, "exchange")
        )
    record["validation"] = base.core.build_validation(record)
    return changed


def _pending_revalidation(record: dict[str, Any]) -> list[str]:
    state = record.get("staticSourcePolicy") or {}
    if not isinstance(state, dict) or state.get("policy") != "final-prospectus-only":
        return []
    allowed = set(final_policy.STATIC_CANONICAL_FIELDS)
    return sorted(
        {
            str(field)
            for field in (state.get("pendingRevalidationFields") or [])
            if str(field) in allowed
        }
    )


def needs_final_prospectus(record: dict[str, Any]) -> bool:
    """A populated legacy record still needs discovery until a final PDF exists."""
    if record.get("issueEventType") or not base.source_date(record.get("openDate")):
        return False
    return final_policy.choose_final_prospectus(record) is None


def eligible_final_documents(
    record: dict[str, Any], entries: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return only identity-matched NSE ``fpAttach`` PDFs for this exact issue."""
    if not needs_final_prospectus(record):
        return []
    closed_text = base.source_date(record.get("closeDate") or record.get("openDate"))
    if not closed_text:
        return []
    closed = date.fromisoformat(closed_text)
    latest = closed + timedelta(days=DISCOVERY_WINDOW_DAYS)
    found: dict[str, dict[str, Any]] = {}

    for row in base.matched_entries(record, entries):
        url = base.archive_url(row.get("fpAttach"), ".pdf")
        filed = base.source_date(row.get("fpDate"))
        if not url or not filed:
            continue
        when = date.fromisoformat(filed)
        if not closed <= when <= latest:
            continue
        found[url] = {
            "url": url,
            "source": "NSE",
            "type": "PROSPECTUS",
            "title": f"{record.get('company') or 'Issuer'} Final Prospectus",
            "filedDate": filed,
            "registerUrl": base.PAGE,
        }

    return sorted(
        found.values(),
        key=lambda item: (str(item.get("filedDate") or ""), str(item.get("url") or "")),
        reverse=True,
    )


def _attach_final_document(record: dict[str, Any], doc: dict[str, Any]) -> bool:
    """Attach or repair the NSE-classified final document; never attach an RHP."""
    documents = record.setdefault("documents", [])
    for old in documents:
        if not isinstance(old, dict) or str(old.get("url") or "") != doc["url"]:
            continue
        changed = False
        for key in ("source", "type", "title", "filedDate", "registerUrl"):
            if doc.get(key) not in (None, "") and old.get(key) != doc.get(key):
                old[key] = doc[key]
                changed = True
        return changed
    documents.append(dict(doc))
    return True


def _entry_fingerprint(entries: list[dict[str, Any]]) -> str:
    relevant = []
    for row in entries:
        relevant.append(
            {
                key: row.get(key)
                for key in (
                    "company",
                    "symbol",
                    "isin",
                    "issue_open_date",
                    "issue_close_date",
                    "fpAttach",
                    "fpDate",
                )
            }
        )
    return hashlib.sha256(
        json.dumps(relevant, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def _load_register_rows() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for url in base.FEEDS:
        try:
            data = json.loads(base.fetch(url))
            if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
                raise ValueError("Unexpected NSE offer-register schema")
            rows.extend(data)
        except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
            errors.append({"sourceUrl": url, "error": str(exc)[:250]})
    return rows, errors


def discover_final_prospectuses(
    payload: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    limit: int,
    history_days: int,
    documents_limit: int,
    retry_days: int,
    today: date | None = None,
    checkpoint=None,
) -> dict[str, Any]:
    """Discover final PDFs even when legacy static values are already non-null."""
    today = today or date.today()
    cutoff = (today - timedelta(days=max(0, history_days))).isoformat()
    future = (today + timedelta(days=30)).isoformat()

    candidates: list[tuple[str, int, dict[str, Any], list[dict[str, Any]], str]] = []
    skipped_recent = 0
    matched_records = 0

    for record in payload.get("ipos") or []:
        if not isinstance(record, dict) or not needs_final_prospectus(record):
            continue
        opened = base.source_date(record.get("openDate"))
        if not opened or not cutoff <= opened <= future:
            continue

        matches = base.matched_entries(record, rows)
        if not matches:
            continue
        matched_records += 1
        fingerprint = _entry_fingerprint(matches)
        attempt = record.get(DISCOVERY_ATTEMPT) or {}
        last_attempt = str(attempt.get("lastAttemptAt") or "")[:10]
        retry_cutoff = (today - timedelta(days=max(0, retry_days))).isoformat()
        if attempt.get("fingerprint") == fingerprint and last_attempt > retry_cutoff:
            skipped_recent += 1
            continue

        candidates.append(
            (
                opened,
                len(_pending_revalidation(record)),
                record,
                matches,
                fingerprint,
            )
        )

    candidates.sort(key=lambda item: (item[0], item[1], str(item[2].get("id") or "")), reverse=True)
    selected = candidates[: max(0, limit)] if limit > 0 else candidates

    attempted = 0
    documents_added = 0
    records_with_final = 0
    no_final_in_register = 0
    outcomes: list[dict[str, Any]] = []

    for opened, _pending_count, record, matches, fingerprint in selected:
        if documents_limit > 0 and documents_added >= documents_limit:
            break
        docs = eligible_final_documents(record, matches)
        changed = False
        if docs:
            changed = _attach_final_document(record, docs[0])
            records_with_final += 1
            if changed:
                documents_added += 1
            status = "updated" if changed else "already_attached"
        else:
            no_final_in_register += 1
            status = "no_final_prospectus"

        attempted += 1
        outcome = {
            "id": record.get("id"),
            "company": record.get("company"),
            "openDate": opened,
            "status": status,
            "documentUrl": docs[0]["url"] if docs else None,
        }
        record[DISCOVERY_ATTEMPT] = {
            **outcome,
            "lastAttemptAt": base.stamp(),
            "fingerprint": fingerprint,
        }
        outcomes.append(outcome)
        if checkpoint and changed:
            checkpoint(payload)

    health = {
        "registerRows": len(rows),
        "matchedRecords": matched_records,
        "candidates": len(candidates),
        "selected": len(selected),
        "attempted": attempted,
        "recordsWithFinalProspectus": records_with_final,
        "documentsDiscovered": documents_added,
        "noFinalProspectusInRegister": no_final_in_register,
        "skippedRecentFingerprint": skipped_recent,
        "deferredByDocumentLimit": max(0, len(selected) - attempted),
        "historyDays": max(0, history_days),
        "checkedAt": base.stamp(),
        "outcomes": outcomes,
    }
    return health


def run(
    payload: dict[str, Any],
    *,
    limit: int = 125,
    history_days: int = 730,
    documents_limit: int = 20,
    retry_days: int = 7,
    checkpoint=None,
) -> dict[str, Any]:
    original_merge = base.merge_terms
    try:
        base.merge_terms = merge_dynamic_only
        dynamic_health = base.run(
            payload,
            limit=max(1, limit),
            history_days=max(0, history_days),
            documents_limit=0,
            retry_days=max(0, retry_days),
            checkpoint=checkpoint,
        )
    finally:
        base.merge_terms = original_merge

    rows, register_errors = _load_register_rows()
    discovery = discover_final_prospectuses(
        payload,
        rows,
        limit=max(1, limit),
        history_days=max(0, history_days),
        documents_limit=max(0, documents_limit),
        retry_days=max(0, retry_days),
        checkpoint=checkpoint,
    )
    discovery["failed"] = len(register_errors)
    discovery["errors"] = register_errors

    health = payload.setdefault("meta", {}).setdefault("nseOfferFilingsHealth", {})
    health.update(dynamic_health)
    health["finalProspectusDiscovery"] = discovery
    health["checkedAt"] = base.stamp()
    return health


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--limit", type=int, default=125)
    cli.add_argument("--history-days", type=int, default=730)
    cli.add_argument("--documents-limit", type=int, default=20)
    cli.add_argument("--retry-days", type=int, default=7)
    args = cli.parse_args()

    path = base.ROOT / "data/ipos.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    def save(value: dict[str, Any]) -> None:
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    health = run(
        payload,
        limit=max(1, args.limit),
        history_days=max(0, args.history_days),
        documents_limit=max(0, args.documents_limit),
        retry_days=max(0, args.retry_days),
        checkpoint=save,
    )
    save(payload)
    print(json.dumps(health))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
