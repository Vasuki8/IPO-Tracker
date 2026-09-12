#!/usr/bin/env python3
"""Validated issuer-hosted offer-document fallback for critical IPO gaps.

SEBI and BSE remain the preferred document sources. This fallback is deliberately
small and explicit: it is used only for issuer-owned investor-relations PDFs that
have been manually verified from the issuer's own website, and only when a
priority record still has missing structured offer data.

Every PDF is revalidated at runtime before any value is written:
* the URL host must exactly match the whitelisted issuer host;
* the response must be a real PDF (handled by parser v4's downloader);
* extractable text must contain the expected company identity;
* existing exchange/SEBI values are never overwritten.

For full RHPs, the normal parser reads the first 30 pages. If a priority record is
still missing financials or promoter shareholding, this module performs a bounded
page scan and only appends pages around relevant section headings. That avoids
parsing hundreds of irrelevant pages while still reaching sections that are often
located deep inside SME offer documents.
"""
from __future__ import annotations

import argparse
import hashlib
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

import run_offer_docs_v4 as parser_v4  # noqa: E402
import update_data as core  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = core.DATA_FILE
QUEUE_FILE = ROOT / "data" / "missing_queue.json"
PARSER_VERSION = parser_v4.PARSER_VERSION

# These URLs were reached from the issuers' own investor-relations pages. The
# registry is intentionally explicit rather than accepting arbitrary websites.
ISSUER_DOCUMENTS: dict[str, dict[str, str]] = {
    "maharaja-speedex-india-limited": {
        "company": "Maharaja & Speedex India Limited",
        "url": "https://speedexind.com/wp-content/uploads/2026/09/SPeedex-RHP.pdf",
        "host": "speedexind.com",
        "type": "RHP",
        "title": "Red Herring Prospectus",
        "sourcePage": "https://speedexind.com/changes-in-name/",
    },
    "raksan-transformers-limited": {
        "company": "Raksan Transformers Limited",
        "url": "https://raksantransformers.com/assets/pdf/drhp.pdf",
        "host": "raksantransformers.com",
        "type": "RHP",
        "title": "Red Herring Prospectus",
        "sourcePage": "https://raksantransformers.com/corporategovernance/prospectus",
    },
    "century-business-media-limited": {
        "company": "Century Business Media Limited",
        "url": "https://centurymedia.in/wp-content/uploads/2026/09/Red-Herring-Prospectus.pdf",
        "host": "centurymedia.in",
        "type": "RHP",
        "title": "Red Herring Prospectus",
        "sourcePage": "https://centurymedia.in/investorrelation/",
    },
}

OFFER_GAPS = (
    "exchange.issueComposition",
    "offer.registrar",
    "offer.leadManagers",
    "offer.promoters",
    "offer.financials",
    "offer.objectsOfIssue",
    "offer.promoterShareholding",
)

_FINANCIAL_MARKERS = re.compile(
    r"(?:summary\s+of\s+restated|restated\s+(?:consolidated\s+)?financial|"
    r"key\s+performance\s+indicators?|financial\s+information)",
    re.I,
)
_SHAREHOLDING_MARKERS = re.compile(
    r"(?:pre[-\s]?and[-\s]?post[-\s]?issue\s+shareholding|"
    r"shareholding\s+pattern|capital\s+structure|"
    r"promoters?\s+and\s+promoter\s+group)",
    re.I,
)


def _normal_host(value: str) -> str:
    return re.sub(r"^www\.", "", str(value or "").strip().lower())


def _host_matches(url: str, expected_host: str) -> bool:
    host = _normal_host(urlparse(str(url or "")).hostname or "")
    expected = _normal_host(expected_host)
    return bool(host and expected and host == expected)


def _name_tokens(company: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[A-Z0-9]+", str(company or "").upper())
        if len(token) >= 3 and token not in {"LIMITED", "PRIVATE", "INDIA", "LTD"}
    ]


def _identity_matches(company: str, text: str) -> bool:
    needle = core.canonical_company(company)
    haystack = core.canonical_company(str(text or "")[:30000])
    if not needle or not haystack:
        return False
    if needle in haystack:
        return True
    # Legal suffixes and punctuation vary across filings. Require every
    # meaningful issuer-name token rather than fuzzy matching an unrelated PDF.
    tokens = _name_tokens(company)
    upper = str(text or "")[:30000].upper()
    return len(tokens) >= 2 and all(token in upper for token in tokens)


def _has_priority_gap(item: dict[str, Any]) -> bool:
    missing = {str(field) for field in (item.get("missingFields") or [])}
    return any(field in missing for field in OFFER_GAPS)


def _needs_deep_scan(item: dict[str, Any], parsed: dict[str, Any]) -> tuple[bool, bool]:
    missing = {str(field) for field in (item.get("missingFields") or [])}
    need_financials = "offer.financials" in missing and not parsed.get("financials")
    need_shareholding = "offer.promoterShareholding" in missing and not parsed.get("shareholding")
    return need_financials, need_shareholding


def _extract_targeted_full_text(
    data: bytes,
    base_text: str,
    *,
    need_financials: bool,
    need_shareholding: bool,
    max_scan_pages: int = 420,
    max_hits: int = 14,
) -> tuple[str, int, int]:
    """Append only relevant deep-document pages to the normal first-30-page text.

    We inspect later pages one by one, keep pages that contain a requested section
    marker plus the following two pages, and stop after a bounded number of hits.
    The returned page count is the actual PDF page count; pages_read is the number
    of pages inspected, which is useful provenance for the extraction record.
    """
    if not need_financials and not need_shareholding:
        return base_text, 30, 30

    reader = PdfReader(io.BytesIO(data))
    page_count = len(reader.pages)
    if page_count <= 30:
        return base_text, page_count, page_count

    collected: list[str] = [base_text]
    capture_next = 0
    hits = 0
    inspected = min(30, page_count)
    stop_at = min(page_count, max_scan_pages)

    for idx in range(30, stop_at):
        inspected = idx + 1
        try:
            page_text = reader.pages[idx].extract_text() or ""
        except Exception:
            page_text = ""

        marker_hit = bool(
            (need_financials and _FINANCIAL_MARKERS.search(page_text))
            or (need_shareholding and _SHAREHOLDING_MARKERS.search(page_text))
        )
        if marker_hit:
            hits += 1
            capture_next = max(capture_next, 2)
            collected.append(page_text)
        elif capture_next > 0:
            collected.append(page_text)
            capture_next -= 1

        if hits >= max_hits and capture_next == 0:
            break

    return "\n".join(collected), inspected, page_count


def _merge_dict_missing(existing: dict[str, Any] | None, incoming: dict[str, Any] | None):
    out = dict(existing or {})
    for key, value in (incoming or {}).items():
        if out.get(key) is None and value is not None:
            out[key] = value
    return out


def merge_issuer_enrichment(
    record: dict[str, Any],
    parsed: dict[str, Any],
    doc: dict[str, Any],
    *,
    pdf_hash: str,
    pages_read: int,
    page_count: int,
) -> list[str]:
    """Fill only missing values and keep primary SEBI/exchange data intact."""
    changed: list[str] = []
    issue = parsed.get("issueComposition") or {}

    for field, issue_key in (
        ("freshIssueCr", "freshIssueCr"),
        ("ofsCr", "ofsCr"),
        ("issueSizeCr", "totalIssueSizeCr"),
    ):
        value = issue.get(issue_key)
        if record.get(field) is None and value is not None:
            record[field] = value
            changed.append(field)

    if issue:
        old_issue = record.get("issueComposition") or {}
        merged = _merge_dict_missing(old_issue, issue)
        if merged != old_issue:
            record["issueComposition"] = merged
            changed.append("issueComposition")

    for field in ("registrar", "leadManagers", "promoters", "financials", "objectsOfIssue", "shareholding"):
        value = parsed.get(field)
        current = record.get(field)
        if current in (None, [], {}) and value not in (None, [], {}):
            record[field] = value
            changed.append(field)

    record["issuerDocumentExtraction"] = {
        "status": "extracted",
        "parserVersion": PARSER_VERSION,
        "documentUrl": doc.get("url"),
        "documentType": doc.get("type"),
        "documentTitle": doc.get("title"),
        "sourcePage": doc.get("sourcePage"),
        "sha256": pdf_hash,
        "pagesRead": pages_read,
        "pageCount": page_count,
        "extractedFields": parsed.get("extractedFields") or [],
        "changedFields": changed,
        "extractedAt": core.now_ist().isoformat(timespec="seconds"),
        "source": "Issuer website",
    }

    documents = [d for d in (record.get("documents") or []) if isinstance(d, dict)]
    if not any(str(d.get("url") or "") == str(doc.get("url") or "") for d in documents):
        documents.append(
            {
                "type": doc.get("type") or "RHP",
                "title": doc.get("title") or "Issuer-hosted offer document",
                "url": doc.get("url"),
                "filedDate": None,
                "source": "Issuer website",
            }
        )
        record["documents"] = documents

    sources = [s for s in (record.get("sources") or []) if isinstance(s, dict)]
    sources.append(
        core.source_stamp(
            "Issuer-hosted offer document",
            str(doc.get("sourcePage") or doc.get("url") or ""),
            "issuer-filing",
        )
    )
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))
    return changed


def _targets(payload: dict[str, Any], queue: dict[str, Any], priority_max: int, limit: int):
    by_id = {
        str(record.get("id")): record
        for record in (payload.get("ipos") or [])
        if isinstance(record, dict) and record.get("id")
    }
    selected = []
    for item in queue.get("queue") or []:
        if not isinstance(item, dict):
            continue
        try:
            priority = int(item.get("priority"))
        except (TypeError, ValueError):
            continue
        record_id = str(item.get("id") or "")
        if priority > priority_max or record_id not in ISSUER_DOCUMENTS or not _has_priority_gap(item):
            continue
        record = by_id.get(record_id)
        if record:
            selected.append((record, item, ISSUER_DOCUMENTS[record_id]))
        if limit > 0 and len(selected) >= limit:
            break
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority-max", type=int, default=2)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    targets = _targets(payload, queue, args.priority_max, args.limit)

    session = requests.Session()
    session.headers.update(core.HEADERS)
    attempted = extracted = updated = failed = deep_scanned = 0
    errors: list[str] = []

    previous_cap = parser_v4.base.MAX_PDF_BYTES
    parser_v4.base.MAX_PDF_BYTES = max(previous_cap, 35 * 1024 * 1024)
    try:
        for record, item, spec in targets:
            attempted += 1
            company = str(record.get("company") or spec.get("company") or "")
            try:
                if not _host_matches(spec["url"], spec["host"]):
                    raise ValueError("issuer PDF host failed whitelist validation")
                data = parser_v4.download_pdf(session, spec["url"])
                text, pages_read, page_count = parser_v4.base.extract_pdf_text(data)
                if not _identity_matches(company, text):
                    raise ValueError("PDF identity did not match the expected issuer")
                parsed = parser_v4.parse_document_text(text, record.get("priceBand"))

                need_financials, need_shareholding = _needs_deep_scan(item, parsed)
                if (need_financials or need_shareholding) and page_count > pages_read:
                    deep_text, deep_pages_read, page_count = _extract_targeted_full_text(
                        data,
                        text,
                        need_financials=need_financials,
                        need_shareholding=need_shareholding,
                    )
                    reparsed = parser_v4.parse_document_text(deep_text, record.get("priceBand"))
                    # Prefer the deep parse only when it adds a requested field;
                    # otherwise retain the stable first-30-page result.
                    if (
                        (need_financials and reparsed.get("financials"))
                        or (need_shareholding and reparsed.get("shareholding"))
                    ):
                        parsed = reparsed
                    pages_read = max(pages_read, deep_pages_read)
                    deep_scanned += 1

                if not parsed.get("extractedFields"):
                    raise ValueError("no structured offer fields recognized")
                changed = merge_issuer_enrichment(
                    record,
                    parsed,
                    spec,
                    pdf_hash=hashlib.sha256(data).hexdigest(),
                    pages_read=pages_read,
                    page_count=page_count,
                )
                extracted += 1
                updated += int(bool(changed))
                print(
                    f"Issuer offer doc {company}: "
                    f"extracted={','.join(parsed.get('extractedFields') or [])} "
                    f"changed={','.join(changed) if changed else 'none'} "
                    f"pages={pages_read}/{page_count}"
                )
            except Exception as exc:
                failed += 1
                message = f"{company}: {exc}"
                errors.append(message)
                print(f"Issuer offer-document fallback failed: {message}", file=sys.stderr)
    finally:
        parser_v4.base.MAX_PDF_BYTES = previous_cap

    as_of = core.now_ist().isoformat(timespec="seconds")
    health = {
        "ok": failed == 0 if attempted else True,
        "attempted": attempted,
        "extracted": extracted,
        "updated": updated,
        "deepScanned": deep_scanned,
        "failed": failed,
        "asOf": as_of,
        "errors": errors[:10],
    }
    meta = payload.setdefault("meta", {})
    meta["issuerOfferDocumentHealth"] = health
    meta.setdefault("sourceHealth", {})["Issuer-offer-docs"] = {
        "ok": health["ok"],
        "records": extracted,
        "attempted": attempted,
        "updated": updated,
        "deepScanned": deep_scanned,
        "failed": failed,
        "asOf": as_of,
        "errors": errors[:5],
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Issuer offer docs: "
        f"attempted={attempted} extracted={extracted} updated={updated} "
        f"deep_scanned={deep_scanned} failed={failed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
