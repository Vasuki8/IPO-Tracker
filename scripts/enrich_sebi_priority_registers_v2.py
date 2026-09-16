#!/usr/bin/env python3
"""SEBI Final Prospectus discovery for priority IPO records.

The dedicated SEBI register first page is useful for the newest filings, while
SEBI's GET-based all-list search can recover older issuer filing pages. Under the
Final-Prospectus-only source policy an existing RHP is *not* completion: the
search remains active until an actual issuer-qualified Prospectus landing page
(or direct final Prospectus PDF) is known.

DRHP/RHP remain document history only. This module attaches only final
``PROSPECTUS`` matches from the all-list search; direct PDFs are resolved later
by ``enrich_sebi_document_links.py`` and parsed by the canonical Final
Prospectus parser.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_sebi_priority_registers as v1  # noqa: E402
import final_prospectus_identity as identity  # noqa: E402
import final_prospectus_policy as final_policy  # noqa: E402
import update_data as core  # noqa: E402

DATA_FILE = core.DATA_FILE
QUEUE_FILE = v1.QUEUE_FILE
SEARCH_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do"
PARSER_VERSION = 4
ATTEMPT_KEY = "sebiFinalProspectusSearch"


def infer_primary_type(title: str) -> str | None:
    value = " ".join(str(title or "").split()).upper()
    if any(marker in value for marker in v1.SUPPLEMENTAL_MARKERS):
        return None
    if "UDRHP" in value or "UPDATED DRAFT" in value or "DRHP" in value or "DRAFT RED HERRING" in value:
        return None
    if re.search(r"\bRHP\b", value) or "RED HERRING PROSPECTUS" in value:
        return "RHP"
    if "PROSPECTUS" in value:
        return "PROSPECTUS"
    return None


def parse_search_html(html: str, search_url: str = SEARCH_URL) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in soup.select("table tbody tr"):
        anchor = row.select_one('a[href*="/filings/public-issues/"]')
        if not anchor:
            continue
        title = " ".join(anchor.stripped_strings).strip()
        typ = infer_primary_type(title)
        if not typ:
            continue
        href = urljoin(search_url, str(anchor.get("href") or "").strip())
        if not href.startswith("https://www.sebi.gov.in/filings/public-issues/") or href in seen:
            continue
        cells = row.find_all("td")
        filed = v1.parse_sebi_date(" ".join(cells[0].stripped_strings) if cells else "")
        company = v1.title_company(title)
        if not company:
            continue
        out.append({"type": typ, "title": title, "company": company, "companyKey": core.canonical_company(company), "url": href, "filedDate": filed or "", "source": "SEBI", "sourcePage": search_url})
        seen.add(href)
    return out


def has_primary_landing(record: dict[str, Any]) -> bool:
    """Compatibility helper: any RHP/Prospectus SEBI landing page."""
    for doc in record.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        url = str(doc.get("url") or "")
        typ = str(doc.get("type") or "").upper()
        if typ in {"RHP", "PROSPECTUS"} and "/filings/public-issues/" in url and not url.lower().endswith(".pdf"):
            return True
    return False


def has_final_prospectus_landing(record: dict[str, Any]) -> bool:
    selected = identity.choose_candidate(record, final_policy.final_prospectus_candidates(record))
    if selected is not None and identity.discovery_complete(record, selected):
        return True
    for doc in record.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        url = str(doc.get("url") or "")
        if (
            final_policy.is_final_prospectus(doc)
            and "/filings/public-issues/" in url
            and not url.lower().endswith(".pdf")
            and identity.discovery_complete(record, doc)
        ):
            return True
    return False


def final_prospectus_matches(record: dict[str, Any], candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    return [candidate for candidate in v1.match_record(record, candidates) if str(candidate.get("type") or "").upper() == "PROSPECTUS"]


def _attach_matches(record: dict[str, Any], matches: list[dict[str, str]]) -> int:
    docs = [d for d in (record.get("documents") or []) if isinstance(d, dict)]
    existing = {str(d.get("url") or "") for d in docs}
    added = 0
    for candidate in matches:
        if str(candidate.get("type") or "").upper() != "PROSPECTUS":
            continue
        url = str(candidate.get("url") or "")
        if not url or url in existing:
            continue
        docs.append({"type": "PROSPECTUS", "title": candidate["title"], "company": candidate.get("company"), "url": url, "filedDate": candidate.get("filedDate") or None, "source": "SEBI", "sourcePage": candidate.get("sourcePage")})
        existing.add(url)
        added += 1
    if added:
        record["documents"] = core.dedupe_dicts(docs, ("url", "type"))
    return added


def _date_number(value: Any) -> int:
    digits = re.sub(r"\D", "", str(value or ""))
    try:
        return int(digits[:8]) if digits else 0
    except ValueError:
        return 0


def search_candidate_sort_key(record: dict[str, Any]) -> tuple[int, str, int]:
    attempt = record.get(ATTEMPT_KEY)
    last_attempt = str(attempt.get("lastAttemptAt") or "") if isinstance(attempt, dict) else ""
    return (1 if last_attempt else 0, last_attempt, -_date_number(record.get("openDate")))


def _stamp_attempt(record: dict[str, Any], *, status: str, links_added: int = 0, error: str | None = None) -> None:
    entry: dict[str, Any] = {"status": status, "linksAdded": links_added, "lastAttemptAt": core.now_ist().isoformat(timespec="seconds"), "sourceUrl": SEARCH_URL, "parserVersion": PARSER_VERSION}
    if error:
        entry["error"] = str(error)[:300]
    record[ATTEMPT_KEY] = entry


def enrich_payload(payload: dict[str, Any], session: requests.Session, *, priority_max: int = 2, search_limit: int = 30) -> dict[str, Any]:
    first_page = v1.enrich_payload(payload, session, priority_max=priority_max)
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    ids = v1.priority_ids(queue, priority_max)
    records = [r for r in payload.get("ipos") or [] if isinstance(r, dict) and str(r.get("id") or "") in ids]
    records = [r for r in records if not has_final_prospectus_landing(r)]
    records.sort(key=search_candidate_sort_key)
    if search_limit > 0:
        records = records[:search_limit]

    searched = matched_records = links_added = failed = 0
    errors: list[str] = []
    for record in records:
        searched += 1
        try:
            response = session.get(SEARCH_URL, params={"doListingAll": "yes", "search": str(record.get("company") or "")}, timeout=30)
            response.raise_for_status()
            matches = final_prospectus_matches(record, parse_search_html(response.text))
            added = _attach_matches(record, matches)
            _stamp_attempt(record, status="matched-final-prospectus" if added else "no-final-prospectus", links_added=added)
            if added:
                matched_records += 1
                links_added += added
        except Exception as exc:
            failed += 1
            errors.append(f"{record.get('company')}: {exc}")
            _stamp_attempt(record, status="error", error=str(exc))

    as_of = core.now_ist().isoformat(timespec="seconds")
    health = {"ok": bool(first_page.get("ok")) or (searched > 0 and failed < searched), "parserVersion": PARSER_VERSION, "priorityMax": priority_max, "firstPageMatched": first_page.get("matchedRecords", 0), "firstPageLinks": first_page.get("linksAdded", 0), "awaitingFinalProspectus": len(records), "searchedRecords": searched, "finalProspectusMatchedRecords": matched_records, "finalProspectusLinksAdded": links_added, "failed": failed, "asOf": as_of, "errors": errors[:10]}
    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["SEBI-priority-registers"] = health
    return health


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority-max", type=int, default=2)
    parser.add_argument("--search-limit", type=int, default=30)
    args = parser.parse_args()
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers.update(core.HEADERS)
    health = enrich_payload(payload, session, priority_max=args.priority_max, search_limit=args.search_limit)
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("SEBI Final Prospectus discovery: " f"first_page={health['firstPageMatched']} searched={health['searchedRecords']} " f"final_matched={health['finalProspectusMatchedRecords']} " f"final_links={health['finalProspectusLinksAdded']} failed={health['failed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
