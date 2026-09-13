#!/usr/bin/env python3
"""Fill P4 issue size/composition from attached full official SEBI documents only.

This runner is deliberately narrower than ``enrich_recent_offer_terms.py``: it
never fills lot size. It exists so the issue-size/composition cleanup can run
independently while preserving the same conservative document selection, PDF
extraction, fill-only semantics, provenance and validation behavior.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_recent_offer_terms as base  # noqa: E402
import update_data as core  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = core.DATA_FILE
QUEUE_FILE = ROOT / "data" / "missing_queue.json"
PARSER_VERSION = 1
SOURCE_NAME = "SEBI offer document issue terms"
WANTED_GAPS = {"exchange.issueSizeCr", "exchange.issueComposition"}


def priority_targets(queue_payload: dict[str, Any], priority_max: int) -> dict[str, set[str]]:
    targets: dict[str, set[str]] = {}
    for item in queue_payload.get("queue") or []:
        if not isinstance(item, dict):
            continue
        try:
            priority = int(item.get("priority"))
        except (TypeError, ValueError):
            continue
        record_id = str(item.get("id") or "")
        if not record_id or priority > priority_max:
            continue
        gaps = {str(value) for value in item.get("missingFields") or []} & WANTED_GAPS
        if gaps:
            targets[record_id] = gaps
    return targets


def merge_issue_terms(record: dict[str, Any], text: str, doc: dict[str, Any]) -> list[str]:
    """Merge only issue-size/composition facts; lot-size data is intentionally ignored."""
    issue = base.offer.base.extract_issue_composition(text, record.get("priceBand")) or {}
    changed: list[str] = []

    if record.get("freshIssueCr") is None and issue.get("freshIssueCr") is not None:
        record["freshIssueCr"] = issue["freshIssueCr"]
        changed.append("freshIssueCr")
    if record.get("ofsCr") is None and issue.get("ofsCr") is not None:
        record["ofsCr"] = issue["ofsCr"]
        changed.append("ofsCr")
    if record.get("issueSizeCr") is None and issue.get("totalIssueSizeCr") is not None:
        record["issueSizeCr"] = issue["totalIssueSizeCr"]
        changed.append("issueSizeCr")
    if record.get("issueComposition") in (None, {}, []) and any(value is not None for value in issue.values()):
        record["issueComposition"] = issue
        changed.append("issueComposition")

    if not changed:
        return changed

    source_url = str(doc.get("sourcePage") or doc.get("url") or "")
    sources = list(record.get("sources") or [])
    sources = [source for source in sources if str((source or {}).get("name") or "") != SOURCE_NAME]
    sources.append(core.source_stamp(SOURCE_NAME, source_url, "regulator"))
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    observation = dict((record.get("observations") or {}).get("SEBIOfferIssueTerms") or {})
    observation.update(
        {
            "documentUrl": doc.get("url"),
            "filedDate": doc.get("filedDate"),
            "parserVersion": PARSER_VERSION,
        }
    )
    for key in (
        "freshIssueCr",
        "ofsCr",
        "totalIssueSizeCr",
        "freshShares",
        "ofsShares",
        "freshValueCr",
        "ofsValueCr",
    ):
        if issue.get(key) is not None:
            observation[key] = issue[key]
    record.setdefault("observations", {})["SEBIOfferIssueTerms"] = observation
    record["validation"] = core.build_validation(record)
    return changed


def enrich_payload(
    payload: dict[str, Any],
    session: requests.Session,
    *,
    priority_max: int = 4,
    limit: int = 60,
) -> dict[str, Any]:
    queue_payload = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    targets = priority_targets(queue_payload, priority_max)
    records = [
        record
        for record in payload.get("ipos") or []
        if isinstance(record, dict) and str(record.get("id") or "") in targets
    ]
    records.sort(key=lambda record: str(record.get("openDate") or ""), reverse=True)
    if limit > 0:
        records = records[:limit]

    attempted = extracted = updated = failed = no_document = 0
    field_counts: dict[str, int] = {}
    errors: list[str] = []

    for record in records:
        doc = base.choose_full_document(record)
        if not doc:
            no_document += 1
            continue
        attempted += 1
        try:
            data = base.offer.base.download_pdf(session, str(doc.get("url") or ""))
            text, pages_read, page_count = base.extract_early_text(data)
            issue = base.offer.base.extract_issue_composition(text, record.get("priceBand")) or {}
            if any(value is not None for value in issue.values()):
                extracted += 1
            changed = merge_issue_terms(record, text, doc)
            if changed:
                updated += 1
                for field in changed:
                    field_counts[field] = field_counts.get(field, 0) + 1
                record["p4IssueTermsExtraction"] = {
                    "status": "extracted",
                    "parserVersion": PARSER_VERSION,
                    "documentUrl": doc.get("url"),
                    "pagesRead": pages_read,
                    "pageCount": page_count,
                    "changed": changed,
                    "asOf": core.now_ist().isoformat(timespec="seconds"),
                }
                print(
                    f"SEBI P4 issue terms {record.get('company')}: "
                    f"changed={','.join(changed)} pages={pages_read}/{page_count}"
                )
        except Exception as exc:
            failed += 1
            errors.append(f"{record.get('company')}: {exc}")
            print(f"SEBI P4 issue terms failed {record.get('company')}: {exc}")

    health = {
        "ok": failed == 0 or updated > 0,
        "priorityMax": priority_max,
        "targets": len(targets),
        "attempted": attempted,
        "extracted": extracted,
        "updated": updated,
        "failed": failed,
        "noDocument": no_document,
        "fields": field_counts,
        "asOf": core.now_ist().isoformat(timespec="seconds"),
        "errors": errors[:10],
    }
    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["SEBI-offer-issue-terms"] = health
    return health


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority-max", type=int, default=4)
    parser.add_argument("--limit", type=int, default=60)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers.update(core.HEADERS)
    health = enrich_payload(payload, session, priority_max=args.priority_max, limit=args.limit)
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "SEBI P4 official issue terms: "
        f"targets={health['targets']} attempted={health['attempted']} extracted={health['extracted']} "
        f"updated={health['updated']} failed={health['failed']} no_document={health['noDocument']} "
        f"fields={health['fields']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
