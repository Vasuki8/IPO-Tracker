#!/usr/bin/env python3
"""Discover priority IPO filing pages from SEBI's dedicated public-issue registers.

The generic SEBI feed contains many unrelated filings, so recent IPO records can
fall out of its shallow daily window.  SEBI also exposes dedicated first-page
registers for Red Herring Documents and Final Offer Documents.  Those pages are
GET-accessible from GitHub Actions and contain the newest 25 filings in each
category.

This enricher is deliberately conservative:
- only missing-queue records at the requested priority are considered;
- supplemental notices (addenda/corrigenda/announcements) are ignored;
- company matching is exact after legal-name normalization, with a tightly
  bounded fuzzy fallback and a filing/open-date proximity check;
- only official SEBI filing landing pages are added, fill-only;
- direct PDFs are still resolved later by enrich_sebi_document_links.py.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = core.DATA_FILE
QUEUE_FILE = ROOT / "data" / "missing_queue.json"

REGISTER_URLS = {
    "RHP": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=11&ssid=15",
    "PROSPECTUS": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=12&ssid=15",
}
SUPPLEMENTAL_MARKERS = (
    "ADDENDUM",
    "CORRIGENDUM",
    "PUBLIC ANNOUNCEMENT",
    "ADVERTISEMENT",
)


def parse_sebi_date(value: str | None) -> str | None:
    raw = " ".join(str(value or "").split())
    for fmt in ("%b %d, %Y", "%d %b %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def title_company(title: str) -> str:
    value = " ".join(str(title or "").split())
    value = re.sub(
        r"\s*[-–:]?\s*(?:UDRHP|UPDATED\s+DRAFT|DRHP|DRAFT\s+RED\s+HERRING|"
        r"RHP|RED\s+HERRING\s+PROSPECTUS|PROSPECTUS|ABRIDGED\s+PROSPECTUS)\b.*$",
        "",
        value,
        flags=re.I,
    )
    return value.strip(" -–:")


def parse_register_html(html: str, register_url: str, doc_type: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in soup.select("table tbody tr"):
        anchor = row.select_one('a[href*="/filings/public-issues/"]')
        if not anchor:
            continue
        title = " ".join(anchor.stripped_strings).strip()
        title_attr = BeautifulSoup(str(anchor.get("title") or ""), "html.parser").get_text(" ", strip=True)
        context = f"{title} {title_attr}".upper()
        if any(marker in context for marker in SUPPLEMENTAL_MARKERS):
            continue
        href = urljoin(register_url, str(anchor.get("href") or "").strip())
        if not href.startswith("https://www.sebi.gov.in/filings/public-issues/") or href in seen:
            continue
        cells = row.find_all("td")
        filed = parse_sebi_date(" ".join(cells[0].stripped_strings) if cells else "")
        company = title_company(title or title_attr)
        if not company:
            continue
        out.append(
            {
                "type": doc_type,
                "title": title or title_attr or f"SEBI {doc_type}",
                "company": company,
                "companyKey": core.canonical_company(company),
                "url": href,
                "filedDate": filed or "",
                "source": "SEBI",
                "sourcePage": register_url,
            }
        )
        seen.add(href)
    return out


def _date_distance(open_date: str | None, filed_date: str | None) -> int:
    try:
        return abs((date.fromisoformat(str(open_date)) - date.fromisoformat(str(filed_date))).days)
    except (TypeError, ValueError):
        return 9999


def match_record(record: dict[str, Any], candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    needle = core.canonical_company(str(record.get("company") or ""))
    if not needle:
        return []
    open_date = core.iso_date(record.get("openDate"))

    exact = [c for c in candidates if c.get("companyKey") == needle]
    if exact:
        return [c for c in exact if not open_date or _date_distance(open_date, c.get("filedDate")) <= 60]

    scored: list[tuple[float, dict[str, str]]] = []
    for candidate in candidates:
        key = str(candidate.get("companyKey") or "")
        if not key:
            continue
        score = SequenceMatcher(None, needle, key).ratio()
        if score < 0.93:
            continue
        if open_date and _date_distance(open_date, candidate.get("filedDate")) > 60:
            continue
        scored.append((score, candidate))
    if not scored:
        return []
    best = max(score for score, _ in scored)
    return [candidate for score, candidate in scored if score >= best - 0.01]


def priority_ids(queue_payload: dict[str, Any], priority_max: int) -> set[str]:
    out: set[str] = set()
    for item in queue_payload.get("queue") or []:
        if not isinstance(item, dict):
            continue
        try:
            priority = int(item.get("priority"))
        except (TypeError, ValueError):
            continue
        if priority <= priority_max and item.get("id"):
            out.add(str(item["id"]))
    return out


def discover_registers(session: requests.Session) -> tuple[list[dict[str, str]], dict[str, Any]]:
    all_candidates: list[dict[str, str]] = []
    health: dict[str, Any] = {}
    for doc_type, url in REGISTER_URLS.items():
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            rows = parse_register_html(response.text, url, doc_type)
            all_candidates.extend(rows)
            health[doc_type] = {"ok": True, "records": len(rows), "url": url}
        except Exception as exc:
            health[doc_type] = {"ok": False, "records": 0, "url": url, "error": str(exc)[:250]}
    return all_candidates, health


def enrich_payload(payload: dict[str, Any], session: requests.Session, *, priority_max: int = 2) -> dict[str, Any]:
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    ids = priority_ids(queue, priority_max)
    candidates, register_health = discover_registers(session)

    matched_records = links_added = 0
    matched_by_type: dict[str, int] = {}
    for record in payload.get("ipos") or []:
        if not isinstance(record, dict) or str(record.get("id") or "") not in ids:
            continue
        matches = match_record(record, candidates)
        if not matches:
            continue
        docs = [d for d in (record.get("documents") or []) if isinstance(d, dict)]
        existing = {str(d.get("url") or "") for d in docs}
        added_here = 0
        for candidate in matches:
            url = str(candidate.get("url") or "")
            if not url or url in existing:
                continue
            doc = {
                "type": candidate["type"],
                "title": candidate["title"],
                "url": url,
                "filedDate": candidate.get("filedDate") or None,
                "source": "SEBI",
                "sourcePage": candidate.get("sourcePage"),
            }
            docs.append(doc)
            existing.add(url)
            added_here += 1
            links_added += 1
            typ = candidate["type"]
            matched_by_type[typ] = matched_by_type.get(typ, 0) + 1
        if added_here:
            matched_records += 1
            record["documents"] = core.dedupe_dicts(docs, ("url", "type"))

    ok_registers = sum(1 for info in register_health.values() if info.get("ok"))
    as_of = core.now_ist().isoformat(timespec="seconds")
    health = {
        "ok": ok_registers > 0,
        "priorityMax": priority_max,
        "registers": register_health,
        "candidates": len(candidates),
        "matchedRecords": matched_records,
        "linksAdded": links_added,
        "matchedByType": matched_by_type,
        "asOf": as_of,
    }
    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["SEBI-priority-registers"] = {
        "ok": health["ok"],
        "records": matched_records,
        "linksAdded": links_added,
        "asOf": as_of,
        "registers": register_health,
    }
    return health


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority-max", type=int, default=2)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers.update(core.HEADERS)
    health = enrich_payload(payload, session, priority_max=args.priority_max)
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "SEBI priority registers: "
        f"candidates={health['candidates']} matched={health['matchedRecords']} "
        f"links={health['linksAdded']} types={health['matchedByType']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
