#!/usr/bin/env python3
"""Fill P4 issue size/composition from official BSE issue pages and PDFs only.

The runner is intentionally narrow: it does not fill lot size, price band,
listing date or offer-intermediary fields. It uses BSE DisplayIPO identity/date
matching for total issue size and document discovery, then parses only direct
BSE-hosted Prospectus/GID PDFs for fresh/OFS composition.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_exchange_details_v2 as bse  # noqa: E402
import enrich_recent_offer_terms as offer_terms  # noqa: E402
import update_data as core  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = core.DATA_FILE
QUEUE_FILE = ROOT / "data" / "missing_queue.json"
WANTED_GAPS = {"exchange.issueSizeCr", "exchange.issueComposition"}
PARSER_VERSION = 1


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


def _norm_symbol(value: Any) -> str:
    return "".join(ch for ch in str(value or "").upper() if ch.isalnum())


def identity_ok(record: dict[str, Any], detail: dict[str, Any]) -> bool:
    """Reject a BSE detail page when both sides expose different symbols."""
    incoming = _norm_symbol(detail.get("symbol"))
    existing = _norm_symbol(record.get("symbol"))
    if incoming and existing and incoming != existing:
        return False
    return bool(detail.get("isEquity", True))


def _official_bse_pdf(url: str) -> bool:
    try:
        parsed = urlparse(str(url or ""))
        host = (parsed.hostname or "").lower()
        return (host == "bseindia.com" or host.endswith(".bseindia.com")) and parsed.path.lower().endswith(".pdf")
    except Exception:
        return False


def _add_documents(record: dict[str, Any], documents: list[dict[str, Any]]) -> int:
    existing = [doc for doc in (record.get("documents") or []) if isinstance(doc, dict)]
    urls = {str(doc.get("url") or "") for doc in existing}
    added = 0
    for doc in documents:
        url = str((doc or {}).get("url") or "")
        if not _official_bse_pdf(url) or url in urls:
            continue
        existing.append(doc)
        urls.add(url)
        added += 1
    if added:
        record["documents"] = core.dedupe_dicts(existing, ("url", "type"))
    return added


def merge_bse_detail(record: dict[str, Any], detail: dict[str, Any], url: str) -> list[str]:
    if not identity_ok(record, detail):
        return []
    changed: list[str] = []
    if record.get("issueSizeCr") is None and detail.get("issueSizeCr") is not None:
        record["issueSizeCr"] = detail["issueSizeCr"]
        changed.append("issueSizeCr")

    added_docs = _add_documents(record, [doc for doc in (detail.get("documents") or []) if isinstance(doc, dict)])
    if added_docs:
        changed.append("documents")

    if not changed:
        return changed

    sources = list(record.get("sources") or [])
    sources = [source for source in sources if str((source or {}).get("name") or "") != "BSE issue-term detail"]
    sources.append(core.source_stamp("BSE issue-term detail", url, "exchange"))
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    obs = dict((record.get("observations") or {}).get("BSEIssueTerms") or {})
    obs.update({"url": url, "parserVersion": PARSER_VERSION})
    if detail.get("issueSizeCr") is not None:
        obs["issueSizeCr"] = detail["issueSizeCr"]
    if detail.get("sharesOffered") is not None:
        obs["sharesOffered"] = detail["sharesOffered"]
    record.setdefault("observations", {})["BSEIssueTerms"] = obs
    record["validation"] = core.build_validation(record)
    return changed


def choose_bse_offer_pdf(record: dict[str, Any]) -> dict[str, Any] | None:
    candidates = []
    for doc in record.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        url = str(doc.get("url") or "")
        if not _official_bse_pdf(url):
            continue
        context = f"{doc.get('type') or ''} {doc.get('title') or ''}".upper()
        if any(marker in context for marker in ("ADDENDUM", "CORRIGENDUM", "ADVERTISEMENT", "ANNOUNCEMENT")):
            continue
        if not any(marker in context for marker in ("PROSPECTUS", "RHP", "GID", "OFFER DOCUMENT")):
            continue
        rank = 3 if "PROSPECTUS" in context or "GID" in context else 2 if "RHP" in context else 1
        candidates.append((rank, str(doc.get("filedDate") or ""), doc))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def download_bse_pdf(session: requests.Session, url: str) -> bytes:
    response = session.get(url, timeout=45, headers={"Referer": bse.BSE_HISTORY_URL})
    response.raise_for_status()
    data = response.content
    content_type = str(response.headers.get("content-type") or "").lower()
    if not data.startswith(b"%PDF") and "pdf" not in content_type:
        raise ValueError("BSE document response was not a PDF")
    return data


def merge_bse_pdf_terms(record: dict[str, Any], text: str, doc: dict[str, Any]) -> list[str]:
    issue = offer_terms.offer.base.extract_issue_composition(text, record.get("priceBand")) or {}
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

    pdf_url = str(doc.get("url") or "")
    sources = list(record.get("sources") or [])
    sources = [source for source in sources if str((source or {}).get("name") or "") != "BSE Prospectus issue terms"]
    sources.append(core.source_stamp("BSE Prospectus issue terms", pdf_url, "exchange"))
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    obs = dict((record.get("observations") or {}).get("BSEProspectusIssueTerms") or {})
    obs.update({"documentUrl": pdf_url, "parserVersion": PARSER_VERSION})
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
            obs[key] = issue[key]
    record.setdefault("observations", {})["BSEProspectusIssueTerms"] = obs
    record["validation"] = core.build_validation(record)
    return changed


def enrich_payload(payload: dict[str, Any], session: requests.Session, *, priority_max: int = 4, limit: int = 50) -> dict[str, Any]:
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    targets = priority_targets(queue, priority_max)
    records = [record for record in payload.get("ipos") or [] if isinstance(record, dict) and str(record.get("id") or "") in targets]
    records.sort(key=lambda record: str(record.get("openDate") or ""), reverse=True)
    if limit > 0:
        records = records[:limit]

    detail_attempted = detail_updated = pdf_attempted = pdf_updated = failed = 0
    field_counts: dict[str, int] = {}
    errors: list[str] = []

    try:
        index, index_health = bse.build_detail_index(session)
    except Exception as exc:
        health = {
            "ok": False,
            "targets": len(targets),
            "error": str(exc),
            "asOf": core.now_ist().isoformat(timespec="seconds"),
        }
        payload.setdefault("meta", {}).setdefault("sourceHealth", {})["BSE-P4-issue-terms"] = health
        return health

    for record in records:
        record_id = str(record.get("id") or "")
        gaps = targets.get(record_id, set())
        detail_url = bse.best_url(index, str(record.get("company") or ""), core.iso_date(record.get("openDate")))
        if detail_url:
            detail_attempted += 1
            try:
                response = session.get(detail_url, timeout=35, headers={"Referer": bse.BSE_HISTORY_URL})
                response.raise_for_status()
                detail = bse.parse_detail_html(response.text)
                changed = merge_bse_detail(record, detail, detail_url)
                if changed:
                    detail_updated += 1
                    for field in changed:
                        field_counts[field] = field_counts.get(field, 0) + 1
                    print(f"BSE P4 detail {record.get('company')}: changed={','.join(changed)}")
            except Exception as exc:
                failed += 1
                errors.append(f"detail {record.get('company')}: {exc}")

        if "exchange.issueComposition" not in gaps:
            continue
        doc = choose_bse_offer_pdf(record)
        if not doc:
            continue
        pdf_attempted += 1
        try:
            data = download_bse_pdf(session, str(doc.get("url") or ""))
            text, pages_read, page_count = offer_terms.extract_early_text(data, max_pages=50)
            changed = merge_bse_pdf_terms(record, text, doc)
            if changed:
                pdf_updated += 1
                for field in changed:
                    field_counts[field] = field_counts.get(field, 0) + 1
                record["p4BseIssueTermsExtraction"] = {
                    "status": "extracted",
                    "parserVersion": PARSER_VERSION,
                    "documentUrl": doc.get("url"),
                    "pagesRead": pages_read,
                    "pageCount": page_count,
                    "changed": changed,
                    "asOf": core.now_ist().isoformat(timespec="seconds"),
                }
                print(f"BSE P4 prospectus {record.get('company')}: changed={','.join(changed)} pages={pages_read}/{page_count}")
        except Exception as exc:
            failed += 1
            errors.append(f"pdf {record.get('company')}: {exc}")

    health = {
        "ok": failed == 0 or detail_updated > 0 or pdf_updated > 0,
        "targets": len(targets),
        "detailAttempted": detail_attempted,
        "detailUpdated": detail_updated,
        "pdfAttempted": pdf_attempted,
        "pdfUpdated": pdf_updated,
        "failed": failed,
        "fields": field_counts,
        "indexHealth": index_health,
        "asOf": core.now_ist().isoformat(timespec="seconds"),
        "errors": errors[:12],
    }
    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["BSE-P4-issue-terms"] = health
    return health


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority-max", type=int, default=4)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers.update(core.HEADERS)
    session.headers.update({"Referer": f"{core.BSE_HOME}/"})
    health = enrich_payload(payload, session, priority_max=args.priority_max, limit=args.limit)
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "BSE P4 official issue terms: "
        f"targets={health.get('targets', 0)} detail_attempted={health.get('detailAttempted', 0)} "
        f"detail_updated={health.get('detailUpdated', 0)} pdf_attempted={health.get('pdfAttempted', 0)} "
        f"pdf_updated={health.get('pdfUpdated', 0)} failed={health.get('failed', 0)} "
        f"fields={health.get('fields', {})}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
