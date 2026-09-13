#!/usr/bin/env python3
"""Fill recent priority IPO terms from full official SEBI offer documents.

This is a focused bridge for fields that exchange endpoints do not reliably
expose inside GitHub Actions. It consumes only full SEBI RHP/Prospectus PDFs
already attached to a priority record, reads the early offer-document pages,
and fills missing application lot / issue composition / issue size facts.

Safety rules:
- full official SEBI PDFs only; abridged and supplemental documents are rejected;
- lot size requires explicit Equity Share application-lot wording;
- lot-only records require a final Prospectus, because RHPs commonly retain [●];
- priority queue controls scope;
- all merges are fill-only;
- the source is labelled as a regulator offer document, never as an exchange;
- a failure on one PDF does not block the batch.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from pypdf import PdfReader

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_offer_docs_v11 as offer  # noqa: E402
import update_data as core  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = core.DATA_FILE
QUEUE_FILE = ROOT / "data" / "missing_queue.json"
PARSER_VERSION = 1
MAX_PAGES = 35
SUPPLEMENTAL_MARKERS = (
    "ADDENDUM",
    "CORRIGENDUM",
    "PUBLIC ANNOUNCEMENT",
    "ADVERTISEMENT",
)


def _official_sebi_pdf(url: str) -> bool:
    try:
        parsed = urlparse(str(url or ""))
        host = (parsed.hostname or "").lower()
        return host in {"sebi.gov.in", "www.sebi.gov.in"} and parsed.path.lower().endswith(".pdf")
    except Exception:
        return False


def choose_full_document(record: dict[str, Any]) -> dict[str, Any] | None:
    rank = {"PROSPECTUS": 4, "RHP": 3, "UDRHP": 2, "DRHP": 1}
    candidates: list[tuple[int, str, int, dict[str, Any]]] = []
    for doc in record.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        url = str(doc.get("url") or "")
        title = str(doc.get("title") or "")
        typ = str(doc.get("type") or "").upper()
        context = f"{typ} {title}".upper()
        if not _official_sebi_pdf(url):
            continue
        if any(marker in context for marker in SUPPLEMENTAL_MARKERS):
            continue
        if typ not in rank:
            continue
        if "ABRIDGED" in context or "/COMMONDOCS/" in url.upper() or "AP_" in url.upper():
            continue
        candidates.append((rank[typ], str(doc.get("filedDate") or ""), int("/attachdocs/" in url.lower()), doc))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1], item[2]))[3]


def should_attempt_document(gaps: set[str], doc: dict[str, Any] | None) -> bool:
    """Avoid downloading an RHP when the only unresolved fact is final lot size."""
    if not doc:
        return False
    if gaps == {"exchange.lotSize"}:
        return str(doc.get("type") or "").upper() == "PROSPECTUS"
    return True


def _valid_lot(value: str | int | float | None) -> int | None:
    parsed = core.integer(value)
    if parsed is None or not 1 <= parsed <= 20_000:
        return None
    return parsed


def extract_lot_size(text: str) -> int | None:
    """Parse only explicit IPO application-lot wording tied to Equity Shares."""
    flat = re.sub(r"\s+", " ", str(text or "")).strip()
    if not flat:
        return None

    strong_patterns = [
        r"\bminimum\s+Bid\s+Lot\s+(?:is|of|shall\s+be|compris(?:e|es|ing))?\s*[:\-]?\s*([\d,]{1,6})\s+Equity\s+Shares\b",
        r"\bBids?\s+(?:can|may|shall)\s+be\s+made\s+for\s+(?:a\s+)?minimum\s+(?:of\s+)?([\d,]{1,6})\s+Equity\s+Shares\b.{0,140}?\bmultiples?\s+of\b",
        r"\bminimum\s+(?:application|bid)\s+(?:size|lot)\b.{0,100}?([\d,]{1,6})\s+Equity\s+Shares\b",
    ]
    for pattern in strong_patterns:
        match = re.search(pattern, flat, re.I)
        if match:
            lot = _valid_lot(match.group(1))
            if lot is not None:
                return lot

    for match in re.finditer(r"\bBid\s+Lot\b.{0,90}?([\d,]{1,6})\s+Equity\s+Shares\b", flat, re.I):
        before = flat[max(0, match.start() - 120):match.start()].lower()
        if "anchor investor" in before or "employee" in before:
            continue
        lot = _valid_lot(match.group(1))
        if lot is not None:
            return lot
    return None


def extract_early_text(data: bytes, max_pages: int = MAX_PAGES) -> tuple[str, int, int]:
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            pass
    pages: list[str] = []
    page_count = len(reader.pages)
    for index, page in enumerate(reader.pages):
        if index >= max_pages:
            break
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    text = "\n".join(pages)
    if len(re.sub(r"\s+", " ", text)) < 500:
        raise ValueError("PDF contained too little extractable text")
    return text, min(page_count, max_pages), page_count


def priority_targets(queue_payload: dict[str, Any], priority_max: int) -> dict[str, set[str]]:
    targets: dict[str, set[str]] = {}
    wanted = {"exchange.lotSize", "exchange.issueSizeCr", "exchange.issueComposition"}
    for item in queue_payload.get("queue") or []:
        if not isinstance(item, dict):
            continue
        try:
            priority = int(item.get("priority"))
        except (TypeError, ValueError):
            continue
        if priority > priority_max or not item.get("id"):
            continue
        gaps = {str(x) for x in item.get("missingFields") or []} & wanted
        if gaps:
            targets[str(item["id"])] = gaps
    return targets


def merge_terms(record: dict[str, Any], text: str, doc: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    lot = extract_lot_size(text)
    if record.get("lotSize") in (None, "") and lot is not None:
        record["lotSize"] = lot
        changed.append("lotSize")
        cap = core.number((record.get("priceBand") or {}).get("max")) if isinstance(record.get("priceBand"), dict) else None
        if record.get("minInvestment") in (None, "") and cap:
            record["minInvestment"] = round(float(cap) * lot, 2)
            changed.append("minInvestment")

    issue = offer.base.extract_issue_composition(text, record.get("priceBand")) or {}
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
    sources = [s for s in sources if str((s or {}).get("name") or "") != "SEBI offer document terms"]
    sources.append(core.source_stamp("SEBI offer document terms", source_url, "regulator"))
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    observation = dict((record.get("observations") or {}).get("SEBIOfferDocument") or {})
    observation["documentUrl"] = doc.get("url")
    observation["filedDate"] = doc.get("filedDate")
    observation["parserVersion"] = PARSER_VERSION
    if lot is not None:
        observation["lotSize"] = lot
    if issue.get("totalIssueSizeCr") is not None:
        observation["issueSizeCr"] = issue["totalIssueSizeCr"]
    record.setdefault("observations", {})["SEBIOfferDocument"] = observation
    record["validation"] = core.build_validation(record)
    return changed


def enrich_payload(payload: dict[str, Any], session: requests.Session, *, priority_max: int = 2, limit: int = 25) -> dict[str, Any]:
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    targets = priority_targets(queue, priority_max)
    records = [r for r in payload.get("ipos") or [] if isinstance(r, dict) and str(r.get("id") or "") in targets]
    records.sort(key=lambda r: str(r.get("openDate") or ""), reverse=True)
    if limit > 0:
        records = records[:limit]

    attempted = extracted = updated = failed = skipped_lot_only_rhp = 0
    field_counts: dict[str, int] = {}
    errors: list[str] = []
    for record in records:
        record_id = str(record.get("id") or "")
        gaps = targets.get(record_id, set())
        doc = choose_full_document(record)
        if not should_attempt_document(gaps, doc):
            if doc and gaps == {"exchange.lotSize"}:
                skipped_lot_only_rhp += 1
            continue
        attempted += 1
        try:
            data = offer.base.download_pdf(session, str(doc.get("url") or ""))
            text, pages_read, page_count = extract_early_text(data)
            lot = extract_lot_size(text)
            issue = offer.base.extract_issue_composition(text, record.get("priceBand")) or {}
            if lot is not None or any(value is not None for value in issue.values()):
                extracted += 1
            changed = merge_terms(record, text, doc)
            if changed:
                updated += 1
                for field in changed:
                    field_counts[field] = field_counts.get(field, 0) + 1
                record["recentOfferTermsExtraction"] = {
                    "status": "extracted",
                    "parserVersion": PARSER_VERSION,
                    "documentUrl": doc.get("url"),
                    "pagesRead": pages_read,
                    "pageCount": page_count,
                    "changed": changed,
                    "asOf": core.now_ist().isoformat(timespec="seconds"),
                }
                print(f"SEBI offer terms {record.get('company')}: changed={','.join(changed)} pages={pages_read}/{page_count}")
        except Exception as exc:
            failed += 1
            errors.append(f"{record.get('company')}: {exc}")
            print(f"SEBI offer terms failed {record.get('company')}: {exc}")

    as_of = core.now_ist().isoformat(timespec="seconds")
    health = {
        "ok": failed == 0 or updated > 0,
        "priorityMax": priority_max,
        "targets": len(targets),
        "attempted": attempted,
        "extracted": extracted,
        "updated": updated,
        "failed": failed,
        "skippedLotOnlyRhp": skipped_lot_only_rhp,
        "fields": field_counts,
        "asOf": as_of,
        "errors": errors[:10],
    }
    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["SEBI-offer-terms"] = health
    return health


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority-max", type=int, default=2)
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers.update(core.HEADERS)
    health = enrich_payload(payload, session, priority_max=args.priority_max, limit=args.limit)
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "SEBI recent offer terms: "
        f"targets={health['targets']} attempted={health['attempted']} extracted={health['extracted']} "
        f"updated={health['updated']} failed={health['failed']} skipped_lot_only_rhp={health['skippedLotOnlyRhp']} "
        f"fields={health['fields']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
