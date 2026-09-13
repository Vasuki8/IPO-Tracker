#!/usr/bin/env python3
"""Fill actionable P4 lot-size gaps from SEBI Public Issues -> Other Documents.

The normal SEBI DRHP/RHP stream often ends before the final bid lot is fixed.
SEBI also publishes post-filing documents such as price-band advertisements and
allotment notices. This pass discovers those regulator-hosted documents and
reuses our strict explicit-Equity-Shares lot parser.
"""
from __future__ import annotations

import argparse
import html as html_lib
import io
import json
import re
import sys
import time
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_recent_offer_terms as terms  # noqa: E402
import update_data as core  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = core.DATA_FILE
QUEUE_FILE = ROOT / "data" / "missing_queue.json"
SEBI_HOME = "https://www.sebi.gov.in"
SEBI_OTHER_DOCS_URL = (
    f"{SEBI_HOME}/sebiweb/home/HomeAction.do"
    "?doListing=yes&sid=3&smid=78&ssid=15"
)
MAX_PDF_PAGES = 20
PARSER_VERSION = 2
PREFERRED_LABELS = (
    "PRICE BAND",
    "BID LOT",
    "OFFER DOCUMENT",
    "PROSPECTUS",
    "BASIS OF ALLOTMENT",
    "ALLOTMENT ADVERTISEMENT",
    "ISSUE ADVERTISEMENT",
    "PUBLIC ANNOUNCEMENT",
)


@dataclass
class CandidatePage:
    record_id: str
    company: str
    url: str
    filed_date: str | None


def _is_sebi(url: str) -> bool:
    host = (urlparse(str(url or "")).hostname or "").lower()
    return host in {"sebi.gov.in", "www.sebi.gov.in"}


def _canonical(value: Any) -> str:
    return core.canonical_company(str(value or ""))


def identity_score(company: str, text: str) -> float:
    expected, observed = _canonical(company), _canonical(text)
    if not expected or not observed:
        return 0.0
    if expected == observed or expected in observed:
        return 1.0
    if observed in expected:
        return len(observed) / len(expected)
    return SequenceMatcher(None, expected, observed).ratio()


def p4_targets(queue: dict[str, Any]) -> set[str]:
    return {
        str(row.get("id"))
        for row in (queue.get("queue") or [])
        if isinstance(row, dict)
        and row.get("id")
        and row.get("priorityLabel") == "P4 recent history (2y)"
        and "exchange.lotSize" in (row.get("missingFields") or [])
    }


def discover_pages(session: requests.Session, records: list[dict[str, Any]], max_pages: int, pause: float) -> tuple[list[CandidatePage], list[str]]:
    pending = {str(r.get("id")): r for r in records}
    found: dict[str, CandidatePage] = {}
    errors: list[str] = []
    consecutive_failures = 0

    for page_no in range(1, max_pages + 1):
        try:
            response = session.get(SEBI_OTHER_DOCS_URL, params={"page": page_no}, timeout=30)
            response.raise_for_status()
            consecutive_failures = 0
        except Exception as exc:
            errors.append(f"listing page {page_no}: {exc}")
            consecutive_failures += 1
            if consecutive_failures >= 3:
                break
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        detail_anchors = []
        for anchor in soup.select("a[href]"):
            href = urljoin(SEBI_HOME, anchor.get("href") or "")
            path = urlparse(href).path.lower()
            if _is_sebi(href) and "/filings/public-issues/" in path and path.endswith(".html"):
                detail_anchors.append((anchor, href))
        if not detail_anchors:
            break

        for anchor, href in detail_anchors:
            label = " ".join(anchor.stripped_strings).strip()
            parent = " ".join(anchor.find_parent().stripped_strings).strip() if anchor.find_parent() else label
            identity_text = label or parent
            best_id, best_score = None, 0.0
            for record_id, record in pending.items():
                if record_id in found:
                    continue
                score = identity_score(str(record.get("company") or ""), identity_text)
                if score > best_score:
                    best_id, best_score = record_id, score
            if best_id is None or best_score < 0.90:
                continue
            found[best_id] = CandidatePage(
                record_id=best_id,
                company=str(pending[best_id].get("company") or ""),
                url=href,
                filed_date=core.iso_date(parent),
            )

        if len(found) == len(pending):
            break
        if pause:
            time.sleep(pause)

    return list(found.values()), errors


def _candidate_urls_from_text(raw: str, base_url: str) -> set[str]:
    """Extract PDF/attachment URLs hidden in href, onclick, JS or escaped HTML."""
    decoded = html_lib.unescape(str(raw or ""))
    decoded = decoded.replace("\\/", "/")
    candidates: set[str] = set()

    patterns = (
        r"https?://[^\s\"'<>]+?\.pdf(?:\?[^\s\"'<>]*)?",
        r"(?:/|\.\./|\./)?(?:sebi_data|webfiles|commonDocs|attachdocs)/[^\s\"'<>]+?\.pdf(?:\?[^\s\"'<>]*)?",
        r"[^\s\"'<>]+?\.pdf(?:\?[^\s\"'<>]*)?",
    )
    for pattern in patterns:
        for match in re.findall(pattern, decoded, flags=re.I):
            cleaned = unquote(str(match)).rstrip(")],;}")
            url = urljoin(base_url, cleaned)
            if _is_sebi(url) and urlparse(url).path.lower().endswith(".pdf"):
                candidates.add(url)
    return candidates


def extract_document_candidates(page_html: str, base_url: str) -> list[dict[str, Any]]:
    """Find SEBI PDFs even when the detail page uses onclick/JS wrappers."""
    soup = BeautifulSoup(page_html, "html.parser")
    labels: dict[str, str] = {}

    for tag in soup.find_all(True):
        tag_text = " ".join(tag.stripped_strings).strip()
        blobs = []
        for value in tag.attrs.values():
            if isinstance(value, list):
                blobs.extend(str(v) for v in value)
            else:
                blobs.append(str(value))
        for blob in blobs:
            for url in _candidate_urls_from_text(blob, base_url):
                labels.setdefault(url, tag_text)

    for url in _candidate_urls_from_text(page_html, base_url):
        labels.setdefault(url, "")

    docs = []
    for url, label in labels.items():
        upper = label.upper()
        rank = next((i for i, marker in enumerate(PREFERRED_LABELS) if marker in upper), len(PREFERRED_LABELS))
        docs.append({"url": url, "title": label or "SEBI Other Document", "rank": rank})
    docs.sort(key=lambda d: (d["rank"], d["title"], d["url"]))
    return docs


def discover_pdfs(session: requests.Session, page: CandidatePage) -> list[dict[str, Any]]:
    response = session.get(page.url, timeout=30)
    response.raise_for_status()
    docs = extract_document_candidates(response.text, page.url)
    for doc in docs:
        doc["sourcePage"] = page.url
        doc["filedDate"] = page.filed_date
    return docs


def pdf_text(data: bytes, max_pages: int = MAX_PDF_PAGES) -> tuple[str, int, int]:
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            pass
    total = len(reader.pages)
    chunks = []
    for idx, page in enumerate(reader.pages):
        if idx >= max_pages:
            break
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            chunks.append("")
    text = "\n".join(chunks)
    if len(re.sub(r"\s+", " ", text)) < 120:
        raise ValueError("PDF contained too little extractable text")
    return text, min(total, max_pages), total


def apply_lot(record: dict[str, Any], lot: int, doc: dict[str, Any], pages_read: int, page_count: int) -> list[str]:
    if record.get("lotSize") not in (None, "") or not 1 <= int(lot) <= 20_000:
        return []
    record["lotSize"] = int(lot)
    changed = ["lotSize"]
    band = record.get("priceBand") if isinstance(record.get("priceBand"), dict) else {}
    cap = core.number((band or {}).get("max"))
    if record.get("minInvestment") in (None, "") and cap:
        record["minInvestment"] = round(float(cap) * int(lot), 2)
        changed.append("minInvestment")

    source_page = str(doc.get("sourcePage") or SEBI_OTHER_DOCS_URL)
    source = core.source_stamp("SEBI public issue other document", source_page, "regulator", doc.get("filedDate"))
    sources = [s for s in (record.get("sources") or []) if isinstance(s, dict) and s.get("name") != source["name"]]
    sources.append(source)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    docs = [d for d in (record.get("documents") or []) if isinstance(d, dict)]
    docs.append({
        "type": "OTHER",
        "title": doc.get("title") or "SEBI Other Document",
        "url": doc.get("url"),
        "sourcePage": source_page,
        "filedDate": doc.get("filedDate"),
        "source": "SEBI",
    })
    record["documents"] = core.dedupe_dicts(docs, ("url", "type"))
    record.setdefault("observations", {})["SEBIOtherDocument"] = {
        "lotSize": int(lot),
        "documentUrl": doc.get("url"),
        "sourcePage": source_page,
        "filedDate": doc.get("filedDate"),
        "pagesRead": pages_read,
        "pageCount": page_count,
        "parserVersion": PARSER_VERSION,
    }
    record["validation"] = core.build_validation(record)
    return changed


def backfill(payload: dict[str, Any], session: requests.Session, max_listing_pages: int = 40, limit: int = 125, max_pdfs: int = 5, pause: float = 0.12) -> dict[str, Any]:
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    target_ids = p4_targets(queue)
    records = [
        r for r in (payload.get("ipos") or [])
        if isinstance(r, dict)
        and str(r.get("id") or "") in target_ids
        and r.get("lotSize") in (None, "")
    ]
    records.sort(key=lambda r: str(r.get("openDate") or ""), reverse=True)
    if limit > 0:
        records = records[:limit]

    pages, errors = discover_pages(session, records, max_listing_pages, pause)
    by_id = {str(r.get("id") or ""): r for r in records}
    attempted_docs = discovered_docs = updated = failed = 0
    updated_ids: list[str] = []

    for page in pages:
        record = by_id.get(page.record_id)
        if not record or record.get("lotSize") not in (None, ""):
            continue
        try:
            docs = discover_pdfs(session, page)
            discovered_docs += len(docs)
        except Exception as exc:
            failed += 1
            errors.append(f"{page.company} detail: {exc}")
            continue

        for doc in docs[:max_pdfs]:
            attempted_docs += 1
            try:
                response = session.get(str(doc["url"]), timeout=45)
                response.raise_for_status()
                content_type = str(response.headers.get("content-type") or "").lower()
                if "pdf" not in content_type and not response.content.startswith(b"%PDF"):
                    continue
                text, pages_read, page_count = pdf_text(response.content)
                if identity_score(page.company, text[:20_000]) < 0.90:
                    continue
                lot = terms.extract_lot_size(text)
                if lot is None:
                    continue
                if apply_lot(record, lot, doc, pages_read, page_count):
                    updated += 1
                    updated_ids.append(page.record_id)
                    print(f"SEBI other-doc lot {page.company}: {lot} ({doc.get('title')})")
                    break
            except Exception as exc:
                failed += 1
                errors.append(f"{page.company} {doc.get('title')}: {exc}")
            if pause:
                time.sleep(pause)

    return {
        "targets": len(target_ids),
        "selected": len(records),
        "matchedPages": len(pages),
        "discoveredDocuments": discovered_docs,
        "attemptedDocuments": attempted_docs,
        "updated": updated,
        "failed": failed,
        "updatedIds": updated_ids,
        "errors": errors[:20],
        "asOf": core.now_ist().isoformat(timespec="seconds"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-listing-pages", type=int, default=40)
    parser.add_argument("--limit", type=int, default=125)
    parser.add_argument("--max-pdfs", type=int, default=5)
    parser.add_argument("--pause", type=float, default=0.12)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers.update(core.HEADERS)
    health = backfill(
        payload,
        session,
        max_listing_pages=max(1, args.max_listing_pages),
        limit=max(0, args.limit),
        max_pdfs=max(1, args.max_pdfs),
        pause=max(0.0, args.pause),
    )
    if health["updated"]:
        payload.setdefault("meta", {}).setdefault("sourceHealth", {})["SEBI-other-doc-lot-backfill"] = health
        DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(health, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
