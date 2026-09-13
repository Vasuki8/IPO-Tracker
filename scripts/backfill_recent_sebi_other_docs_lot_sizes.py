#!/usr/bin/env python3
"""Backfill P4 recent IPO lot sizes from SEBI Public Issues -> Other Documents.

SEBI publishes post-offer material (for example price-band advertisements,
prospectus-related notices and allotment advertisements) separately from the
main DRHP/RHP stream. Those documents can contain the final bid lot even when
the earlier RHP still has placeholders.

Safety rules:
- only actionable P4 recent-history records with missing exchange.lotSize;
- SEBI-hosted company detail pages and PDFs only;
- company identity is matched before any PDF is downloaded;
- reuse the strict explicit-Equity-Shares lot parser from
  enrich_recent_offer_terms.py;
- fill-only: never overwrite an existing lot size;
- placeholders / ambiguous text do not produce a value;
- failures are isolated per page/document;
- only genuine data changes write data/ipos.json.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

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
SEBI_OTHER_DOCS_URL = (
    "https://www.sebi.gov.in/sebiweb/home/HomeAction.do"
    "?doListing=yes&sid=3&smid=78&ssid=15"
)
PARSER_VERSION = 1
MAX_PDF_PAGES = 20
PREFERRED_LABELS = (
    "PRICE BAND",
    "BID LOT",
    "OFFER DOCUMENT",
    "PROSPECTUS",
    "BASIS OF ALLOTMENT",
    "ALLOTMENT ADVERTISEMENT",
    "PUBLIC ANNOUNCEMENT",
    "ISSUE ADVERTISEMENT",
)


@dataclass
class CandidatePage:
    record_id: str
    company: str
    url: str
    filed_date: str | None
    anchor_text: str


def _is_sebi_url(url: str) -> bool:
    try:
        host = (urlparse(str(url or "")).hostname or "").lower()
        return host in {"sebi.gov.in", "www.sebi.gov.in"}
    except Exception:
        return False


def _canonical(value: Any) -> str:
    return core.canonical_company(str(value or ""))


def _identity_score(company: str, text: str) -> float:
    """Conservative company identity score using canonical containment/equality."""
    expected = _canonical(company)
    observed = _canonical(text)
    if not expected or not observed:
        return 0.0
    if expected == observed:
        return 1.0
    if expected in observed or observed in expected:
        shorter = min(len(expected), len(observed))
        longer = max(len(expected), len(observed))
        return shorter / longer if longer else 0.0
    # Reuse repository fuzzy matcher semantics without importing private state.
    from difflib import SequenceMatcher

    return SequenceMatcher(None, expected, observed).ratio()


def p4_lot_targets(queue_payload: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for row in queue_payload.get("queue") or []:
        if not isinstance(row, dict):
            continue
        if row.get("priorityLabel") != "P4 recent history (2y)":
            continue
        if "exchange.lotSize" not in (row.get("missingFields") or []):
            continue
        record_id = str(row.get("id") or "").strip()
        if record_id:
            out.add(record_id)
    return out


def discover_company_pages(
    session: requests.Session,
    records: list[dict[str, Any]],
    *,
    max_pages: int = 40,
    pause: float = 0.12,
) -> tuple[list[CandidatePage], list[str]]:
    """Discover SEBI Other Documents detail pages matching target companies."""
    by_id = {str(r.get("id") or ""): r for r in records}
    found: dict[str, CandidatePage] = {}
    errors: list[str] = []

    for page in range(1, max_pages + 1):
        try:
            response = session.get(SEBI_OTHER_DOCS_URL, params={"page": page}, timeout=30)
            response.raise_for_status()
        except Exception as exc:
            errors.append(f"listing page {page}: {exc}")
            # One transient page should not hide later pages, but repeated failures
            # are unlikely to improve within the same run.
            if len(errors) >= 3:
                break
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        page_matches = 0
        anchors = soup.select("a[href]")
        if not anchors:
            break

        for anchor in anchors:
            href = urljoin("https://www.sebi.gov.in", anchor.get("href") or "")
            if not _is_sebi_url(href):
                continue
            path = urlparse(href).path.lower()
            if "/filings/public-issues/" not in path or not path.endswith(".html"):
                continue

            anchor_text = " ".join(anchor.stripped_strings).strip()
            parent_text = " ".join(anchor.find_parent().stripped_strings).strip() if anchor.find_parent() else anchor_text
            identity_text = anchor_text or parent_text
            if not identity_text:
                continue

            best_id = None
            best_score = 0.0
            for record_id, record in by_id.items():
                if record_id in found:
                    continue
                score = _identity_score(str(record.get("company") or ""), identity_text)
                if score > best_score:
                    best_id, best_score = record_id, score

            if best_id is None or best_score < 0.90:
                continue

            record = by_id[best_id]
            filed_date = core.iso_date(parent_text)
            found[best_id] = CandidatePage(
                record_id=best_id,
                company=str(record.get("company") or ""),
                url=href,
                filed_date=filed_date,
                anchor_text=identity_text,
            )
            page_matches += 1

        # SEBI has roughly 25 rows per page. If a page has no detail links at all,
        # stop rather than walking arbitrary pagination forever.
        detail_links = [
            a for a in anchors
            if "/filings/public-issues/" in urlparse(urljoin("https://www.sebi.gov.in", a.get("href") or "")).path.lower()
        ]
        if not detail_links:
            break
        if len(found) >= len(records):
            break
        if pause > 0:
            time.sleep(pause)

    return list(found.values()), errors


def discover_pdfs(session: requests.Session, page: CandidatePage) -> list[dict[str, Any]]:
    response = session.get(page.url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    for anchor in soup.select("a[href]"):
        url = urljoin(page.url, anchor.get("href") or "")
        if not _is_sebi_url(url) or not urlparse(url).path.lower().endswith(".pdf"):
            continue
        if url in seen:
            continue
        seen.add(url)
        label = " ".join(anchor.stripped_strings).strip()
        if not label and anchor.find_parent():
            label = " ".join(anchor.find_parent().stripped_strings).strip()
        upper = label.upper()
        priority = next((i for i, marker in enumerate(PREFERRED_LABELS) if marker in upper), len(PREFERRED_LABELS))
        out.append(
            {
                "url": url,
                "title": label or "SEBI Other Document",
                "sourcePage": page.url,
                "filedDate": page.filed_date,
                "priority": priority,
            }
        )

    out.sort(key=lambda row: (row["priority"], row["title"], row["url"]))
    return out


def extract_pdf_text(data: bytes, max_pages: int = MAX_PDF_PAGES) -> tuple[str, int, int]:
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            pass
    total = len(reader.pages)
    chunks: list[str] = []
    for index, page in enumerate(reader.pages):
        if index >= max_pages:
            break
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            chunks.append("")
    text = "\n".join(chunks)
    if len(re.sub(r"\s+", " ", text)) < 120:
        raise ValueError("PDF contained too little extractable text")
    return text, min(total, max_pages), total


def apply_lot(record: dict[str, Any], lot: int, doc: dict[str, Any], *, pages_read: int, page_count: int) -> list[str]:
    if record.get("lotSize") not in (None, ""):
        return []
    if not 1 <= int(lot) <= 20_000:
        return []

    record["lotSize"] = int(lot)
    changed = ["lotSize"]
    band = record.get("priceBand") if isinstance(record.get("priceBand"), dict) else {}
    cap = core.number((band or {}).get("max"))
    if record.get("minInvestment") in (None, "") and cap:
        record["minInvestment"] = round(float(cap) * int(lot), 2)
        changed.append("minInvestment")

    source_page = str(doc.get("sourcePage") or doc.get("url") or SEBI_OTHER_DOCS_URL)
    source = core.source_stamp("SEBI public issue other document", source_page, "regulator", doc.get("filedDate"))
    sources = [s for s in (record.get("sources") or []) if isinstance(s, dict)]
    sources = [s for s in sources if str(s.get("name") or "") != source["name"]]
    sources.append(source)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    docs = [d for d in (record.get("documents") or []) if isinstance(d, dict)]
    docs.append(
        {
            "type": "OTHER",
            "title": doc.get("title") or "SEBI Other Document",
            "url": doc.get("url"),
            "sourcePage": source_page,
            "filedDate": doc.get("filedDate"),
            "source": "SEBI",
        }
    )
    record["documents"] = core.dedupe_dicts(docs, ("url", "type"))

    observation = dict((record.get("observations") or {}).get("SEBIOtherDocument") or {})
    observation.update(
        {
            "lotSize": int(lot),
            "documentUrl": doc.get("url"),
            "sourcePage": source_page,
            "filedDate": doc.get("filedDate"),
            "pagesRead": pages_read,
            "pageCount": page_count,
            "parserVersion": PARSER_VERSION,
        }
    )
    record.setdefault("observations", {})["SEBIOtherDocument"] = observation
    record["validation"] = core.build_validation(record)
    return changed


def backfill(
    payload: dict[str, Any],
    session: requests.Session,
    *,
    max_listing_pages: int = 40,
    limit: int = 125,
    max_pdfs_per_record: int = 5,
    pause: float = 0.12,
) -> dict[str, Any]:
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    target_ids = p4_lot_targets(queue)
    records = [
        row for row in (payload.get("ipos") or [])
        if isinstance(row, dict)
        and str(row.get("id") or "") in target_ids
        and row.get("lotSize") in (None, "")
    ]
    records.sort(key=lambda row: str(row.get("openDate") or ""), reverse=True)
    if limit > 0:
        records = records[:limit]

    pages, listing_errors = discover_company_pages(
        session,
        records,
        max_pages=max_listing_pages,
        pause=pause,
    )
    by_id = {str(row.get("id") or ""): row for row in records}

    attempted_docs = matched_pages = updated = failed = 0
    updated_ids: list[str] = []
    errors = list(listing_errors)

    for page in pages:
        record = by_id.get(page.record_id)
        if not record or record.get("lotSize") not in (None, ""):
            continue
        matched_pages += 1
        try:
            pdfs = discover_pdfs(session, page)
        except Exception as exc:
            failed += 1
            errors.append(f"{page.company} detail page: {exc}")
            continue

        for doc in pdfs[:max_pdfs_per_record]:
            attempted_docs += 1
            try:
                response = session.get(str(doc["url"]), timeout=45)
                response.raise_for_status()
                text, pages_read, page_count = extract_pdf_text(response.content)
                # Confirm the downloaded document still names the intended issuer.
                issuer_text = re.sub(r"\s+", " ", text[:15_000])
                if _identity_score(page.company, issuer_text) < 0.40:
                    continue
                lot = terms.extract_lot_size(text)
                if lot is None:
                    continue
                changed = apply_lot(record, lot, doc, pages_read=pages_read, page_count=page_count)
                if changed:
                    updated += 1
                    updated_ids.append(page.record_id)
                    print(f"SEBI other-doc lot {page.company}: lotSize={lot} doc={doc.get('title')}")
                    break
            except Exception as exc:
                failed += 1
                errors.append(f"{page.company} {doc.get('title')}: {exc}")
            if pause > 0:
                time.sleep(pause)

    return {
        "targets": len(target_ids),
        "selected": len(records),
        "matchedPages": matched_pages,
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
    parser.add_argument("--max-pdfs-per-record", type=int, default=5)
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
        max_pdfs_per_record=max(1, args.max_pdfs_per_record),
        pause=max(0.0, args.pause),
    )

    if health["updated"]:
        payload.setdefault("meta", {}).setdefault("sourceHealth", {})["SEBI-other-doc-lot-backfill"] = health
        DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(health, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
