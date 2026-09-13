#!/usr/bin/env python3
"""Phase 2 dedicated SEBI priority filing discovery.

v1 discovers priority RHP/Prospectus landing pages from the newest dedicated
register pages.  SEBI's POST pagination is blocked from GitHub Actions, but the
GET-based all-list search endpoint remains accessible.  v2 uses that search
only for priority issuers still lacking a primary RHP/Prospectus landing page.

Only final-stage RHP or Prospectus search results are accepted here.  DRHP and
UDRHP results are deliberately ignored because recent exchange terms such as
lot size and final issue composition may not yet be fixed in draft documents.
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
import update_data as core  # noqa: E402

DATA_FILE = core.DATA_FILE
QUEUE_FILE = v1.QUEUE_FILE
SEARCH_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do"
PARSER_VERSION = 2


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
        out.append(
            {
                "type": typ,
                "title": title,
                "company": company,
                "companyKey": core.canonical_company(company),
                "url": href,
                "filedDate": filed or "",
                "source": "SEBI",
                "sourcePage": search_url,
            }
        )
        seen.add(href)
    return out


def has_primary_landing(record: dict[str, Any]) -> bool:
    for doc in record.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        url = str(doc.get("url") or "")
        typ = str(doc.get("type") or "").upper()
        if typ in {"RHP", "PROSPECTUS"} and "/filings/public-issues/" in url and not url.lower().endswith(".pdf"):
            return True
    return False


def _attach_matches(record: dict[str, Any], matches: list[dict[str, str]]) -> int:
    docs = [d for d in (record.get("documents") or []) if isinstance(d, dict)]
    existing = {str(d.get("url") or "") for d in docs}
    added = 0
    for candidate in matches:
        url = str(candidate.get("url") or "")
        if not url or url in existing:
            continue
        docs.append(
            {
                "type": candidate["type"],
                "title": candidate["title"],
                "url": url,
                "filedDate": candidate.get("filedDate") or None,
                "source": "SEBI",
                "sourcePage": candidate.get("sourcePage"),
            }
        )
        existing.add(url)
        added += 1
    if added:
        record["documents"] = core.dedupe_dicts(docs, ("url", "type"))
    return added


def enrich_payload(
    payload: dict[str, Any],
    session: requests.Session,
    *,
    priority_max: int = 2,
    search_limit: int = 30,
) -> dict[str, Any]:
    first_page = v1.enrich_payload(payload, session, priority_max=priority_max)
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    ids = v1.priority_ids(queue, priority_max)
    records = [r for r in payload.get("ipos") or [] if isinstance(r, dict) and str(r.get("id") or "") in ids]
    records = [r for r in records if not has_primary_landing(r)]
    records.sort(key=lambda r: str(r.get("openDate") or ""), reverse=True)
    if search_limit > 0:
        records = records[:search_limit]

    searched = matched_records = links_added = failed = 0
    errors: list[str] = []
    for record in records:
        searched += 1
        try:
            response = session.get(
                SEARCH_URL,
                params={"doListingAll": "yes", "search": str(record.get("company") or "")},
                timeout=30,
            )
            response.raise_for_status()
            candidates = parse_search_html(response.text)
            matches = v1.match_record(record, candidates)
            added = _attach_matches(record, matches)
            if added:
                matched_records += 1
                links_added += added
        except Exception as exc:
            failed += 1
            errors.append(f"{record.get('company')}: {exc}")

    as_of = core.now_ist().isoformat(timespec="seconds")
    health = {
        "ok": bool(first_page.get("ok")) or (searched > 0 and failed < searched),
        "parserVersion": PARSER_VERSION,
        "priorityMax": priority_max,
        "firstPageMatched": first_page.get("matchedRecords", 0),
        "firstPageLinks": first_page.get("linksAdded", 0),
        "searchedRecords": searched,
        "searchMatchedRecords": matched_records,
        "searchLinksAdded": links_added,
        "failed": failed,
        "asOf": as_of,
        "errors": errors[:10],
    }
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
    health = enrich_payload(
        payload,
        session,
        priority_max=args.priority_max,
        search_limit=args.search_limit,
    )
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "SEBI priority registers v2: "
        f"first_page={health['firstPageMatched']} searched={health['searchedRecords']} "
        f"search_matched={health['searchMatchedRecords']} search_links={health['searchLinksAdded']} "
        f"failed={health['failed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
