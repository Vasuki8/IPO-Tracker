#!/usr/bin/env python3
"""Discover direct SEBI PDF links hidden behind filing landing pages.

SEBI listing pages often link to a filing HTML page. That filing page, in turn,
contains an Abridged Prospectus PDF plus a viewer URL whose ``file`` parameter is
the full RHP/DRHP/Prospectus PDF. This script resolves those official links and
adds them to the existing record without replacing any data.

A very small canonical filing-page registry is also maintained for priority
records where a later addendum/announcement displaced the original RHP landing
page in upstream discovery. The registry stores only official SEBI filing-page
URLs; the PDF links are still resolved from SEBI at runtime.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = core.DATA_FILE
QUEUE_FILE = ROOT / "data" / "missing_queue.json"
SEBI_HOSTS = {"sebi.gov.in", "www.sebi.gov.in"}

# Official SEBI filing pages verified from the public-issues register. These are
# intentionally landing pages, not copied PDF URLs, so runtime resolution still
# discovers the current Abridged Prospectus + full RHP directly from SEBI.
CANONICAL_FILING_PAGES: dict[str, dict[str, str]] = {
    "rentomojo": {
        "type": "RHP",
        "title": "Rentomojo Limited - RHP",
        "url": "https://www.sebi.gov.in/filings/public-issues/sep-2026/rentomojo-limited-rhp_104269.html",
        "filedDate": "2026-09-04",
        "source": "SEBI",
    },
    "prasolchem": {
        "type": "RHP",
        "title": "Prasol Chemicals Limited - RHP",
        "url": "https://www.sebi.gov.in/filings/public-issues/sep-2026/prasol-chemicals-limited-rhp_104222.html",
        "filedDate": "2026-09-03",
        "source": "SEBI",
    },
}


def is_sebi_url(url: str) -> bool:
    try:
        return (urlparse(str(url)).hostname or "").lower() in SEBI_HOSTS
    except Exception:
        return False


def direct_pdf_from_url(url: str) -> str | None:
    """Return a direct SEBI PDF from either a PDF URL or SEBI's /web/?file= viewer."""
    raw = html_lib.unescape(str(url or "").strip())
    if not raw:
        return None
    parsed = urlparse(raw)
    if parsed.path.lower().endswith(".pdf") and is_sebi_url(raw):
        return raw
    if parsed.path.rstrip("/").lower().endswith("/web"):
        query = parse_qs(parsed.query)
        file_values = query.get("file") or query.get("File") or []
        if file_values:
            target = unquote(str(file_values[0]))
            if target.lower().endswith(".pdf") and is_sebi_url(target):
                return target
    return None


def infer_type(text: str, fallback: str | None = None) -> str:
    value = str(text or "").upper()
    # Supplemental notices must never masquerade as the underlying RHP merely
    # because their title contains the letters "RHP".
    if any(token in value for token in ("ADDENDUM", "CORRIGENDUM", "PUBLIC ANNOUNCEMENT")):
        return "ADDENDUM"
    if "UDRHP" in value or "UPDATED DRAFT" in value:
        return "UDRHP"
    if "DRHP" in value or "DRAFT RED HERRING" in value:
        return "DRHP"
    if re.search(r"\bRHP\b", value) or "RED HERRING PROSPECTUS" in value:
        return "RHP"
    if "PROSPECTUS" in value:
        return "PROSPECTUS"
    return str(fallback or "DOCUMENT").upper()


def extract_pdf_links(html: str, landing_url: str, *, fallback_type: str | None = None) -> list[dict[str, Any]]:
    """Extract direct official PDFs from one SEBI filing page."""
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    # Normal anchors cover the direct Abridged Prospectus and the /web/?file=
    # viewer used for the full offer document.
    for anchor in soup.select("a[href]"):
        href = urljoin(landing_url, str(anchor.get("href") or ""))
        direct = direct_pdf_from_url(href)
        if not direct or direct in seen:
            continue
        title = " ".join(anchor.stripped_strings).strip()
        typ = infer_type(f"{title} {href}", fallback=fallback_type)
        abridged = "ABRIDGED" in title.upper() or "AP_" in direct.upper()
        if abridged and fallback_type:
            # "Abridged Prospectus" alone would otherwise be classified as a
            # final prospectus even when it belongs to an RHP filing.
            typ = str(fallback_type).upper()
        out.append(
            {
                "type": typ,
                "title": title or f"SEBI {typ}",
                "url": direct,
                "source": "SEBI",
            }
        )
        seen.add(direct)

    # Some SEBI pages embed the viewer as raw HTML inside a title block. Catch
    # direct/encoded PDF URLs there as a conservative fallback.
    decoded = html_lib.unescape(html)
    patterns = [
        r"https?://(?:www\.)?sebi\.gov\.in/[^\"'<>\s]+?\.pdf",
        r"https?://(?:www\.)?sebi\.gov\.in/web/\?file=[^\"'<>\s]+",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, decoded, flags=re.I):
            direct = direct_pdf_from_url(match)
            if not direct or direct in seen:
                continue
            typ = infer_type(match, fallback=fallback_type)
            out.append(
                {
                    "type": typ,
                    "title": f"SEBI {typ}",
                    "url": direct,
                    "source": "SEBI",
                }
            )
            seen.add(direct)
    return out


def seed_canonical_filing_page(record: dict[str, Any], docs: list[dict[str, Any]]) -> bool:
    """Add a missing official filing landing page for a known priority record."""
    canonical = CANONICAL_FILING_PAGES.get(str(record.get("id") or ""))
    if not canonical:
        return False
    url = canonical["url"]
    if any(str(existing.get("url") or "") == url for existing in docs):
        return False
    docs.append(dict(canonical))
    return True


def priority_ids(queue_payload: dict[str, Any], priority_max: int) -> set[str]:
    ids: set[str] = set()
    for item in queue_payload.get("queue") or []:
        if not isinstance(item, dict):
            continue
        try:
            priority = int(item.get("priority"))
        except (TypeError, ValueError):
            continue
        if priority <= priority_max and item.get("id"):
            ids.add(str(item["id"]))
    return ids


def enrich_payload(payload: dict[str, Any], session: requests.Session, *, priority_max: int = 2, limit: int = 40):
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    ids = priority_ids(queue, priority_max)
    attempted = resolved_pages = added = failed = seeded_pages = 0
    errors: list[str] = []

    records = [r for r in payload.get("ipos") or [] if isinstance(r, dict) and str(r.get("id")) in ids]
    if limit > 0:
        records = records[:limit]

    for record in records:
        docs = [d for d in (record.get("documents") or []) if isinstance(d, dict)]
        if seed_canonical_filing_page(record, docs):
            seeded_pages += 1

        landing_docs = []
        for doc in docs:
            url = str(doc.get("url") or "")
            if not is_sebi_url(url) or direct_pdf_from_url(url):
                continue
            # Only resolve filing pages/offer-document-looking SEBI links.
            title = str(doc.get("title") or "")
            context = f"{title} {url}".upper()
            if not any(token in context for token in ("RHP", "DRHP", "PROSPECTUS", "/FILINGS/PUBLIC-ISSUES/")):
                continue
            landing_docs.append(doc)

        for doc in landing_docs:
            attempted += 1
            url = str(doc.get("url") or "")
            try:
                response = session.get(url, timeout=30)
                response.raise_for_status()
                links = extract_pdf_links(response.text, url, fallback_type=str(doc.get("type") or "DOCUMENT"))
                if links:
                    resolved_pages += 1
                for link in links:
                    link["filedDate"] = doc.get("filedDate")
                    link["sourcePage"] = url
                    if any(str(existing.get("url") or "") == link["url"] for existing in docs):
                        continue
                    docs.append(link)
                    added += 1
            except Exception as exc:
                failed += 1
                errors.append(f"{record.get('company')}: {exc}")
        record["documents"] = core.dedupe_dicts(docs, ("url", "type"))

    health = {
        "ok": failed == 0,
        "attempted": attempted,
        "resolvedPages": resolved_pages,
        "seededPages": seeded_pages,
        "linksAdded": added,
        "failed": failed,
        "asOf": core.now_ist().isoformat(timespec="seconds"),
        "errors": errors[:10],
    }
    meta = payload.setdefault("meta", {})
    meta["sebiDocumentLinkHealth"] = health
    meta.setdefault("sourceHealth", {})["SEBI-document-links"] = {
        "ok": health["ok"],
        "records": added,
        "attempted": attempted,
        "asOf": health["asOf"],
        "errors": errors[:5],
    }
    return health


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority-max", type=int, default=2)
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers.update(core.HEADERS)
    health = enrich_payload(payload, session, priority_max=args.priority_max, limit=args.limit)
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "SEBI document links: "
        f"attempted={health['attempted']} resolved={health['resolvedPages']} "
        f"seeded={health['seededPages']} added={health['linksAdded']} failed={health['failed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
