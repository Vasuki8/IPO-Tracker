#!/usr/bin/env python3
"""Capture live subscription data for every currently open IPO.

NSE remains preferred. When its WAF blocks GitHub Actions, BSE is used. For SME
issues we do not assume that DisplayIPO's IPONo is always the cumulative-demand
ID: the collector first opens the official DisplayIPO page and follows any real
CummDemandSchedule link exposed there, then tries the constructed route and the
same official route on BSE's primary/beta hosts.

Open issues are refreshed on every subscription run even when they already have
a snapshot. Subscription multiples change throughout the bidding window, so a
missing-data queue is not a valid freshness scheduler for live demand data.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import track_subscriptions as sub  # noqa: E402
import update_data as core  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = core.DATA_FILE
QUEUE_FILE = ROOT / "data" / "missing_queue.json"
BSE_SME_CURRENT_URL = "https://www.bsesme.com/PublicIssues/PublicIssues.aspx?id=2"


@dataclass(frozen=True)
class IssueLink:
    key: str
    display_url: str | None
    direct_demand_url: str | None
    index_url: str


def _issue_links_from_html(html: str, page_url: str) -> list[IssueLink]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[IssueLink] = []
    seen: set[tuple[str, str | None, str | None]] = set()
    for tr in soup.select("tr"):
        label, display_url = sub._extract_bse_display_link(tr, page_url)
        direct = sub._extract_bse_demand_url(tr, page_url)
        if not display_url and not direct:
            continue
        key = sub._row_company_key(tr, label)
        if not key:
            continue
        token = (key, display_url, direct)
        if token in seen:
            continue
        seen.add(token)
        out.append(IssueLink(key, display_url, direct, page_url))
    return out


def build_issue_index(session: requests.Session, page_urls=None):
    urls = list(page_urls or [*core.BSE_URLS, BSE_SME_CURRENT_URL])
    all_links: list[IssueLink] = []
    health: dict[str, Any] = {}
    for page_url in urls:
        try:
            response = session.get(page_url, timeout=30)
            response.raise_for_status()
            rows = _issue_links_from_html(response.text, page_url)
            all_links.extend(rows)
            health[page_url] = {"ok": True, "records": len(rows)}
        except Exception as exc:
            health[page_url] = {"ok": False, "records": 0, "error": str(exc)[:250]}
    if not all_links:
        raise ValueError("No BSE public-issue links found")
    return all_links, health


def best_issue_links(index: list[IssueLink], company: str) -> list[IssueLink]:
    needle = core.canonical_company(company)
    if not needle:
        return []
    exact = [row for row in index if row.key == needle]
    if exact:
        return exact
    contained = [row for row in index if needle in row.key or row.key in needle]
    if contained:
        return contained
    scored = sorted(
        ((SequenceMatcher(None, needle, row.key).ratio(), row) for row in index),
        key=lambda x: x[0],
        reverse=True,
    )
    if not scored or scored[0][0] < 0.72:
        return []
    best_score = scored[0][0]
    return [row for score, row in scored if score >= best_score - 0.02]


def _alternate_bse_hosts(url: str) -> list[str]:
    parsed = urlparse(html_lib.unescape(url))
    host = (parsed.hostname or "").lower()
    if host not in {"www.bseindia.com", "beta.bseindia.com", "bseindia.com"}:
        return [url]
    out = [url]
    for netloc in ("www.bseindia.com", "beta.bseindia.com"):
        if netloc == parsed.netloc:
            continue
        out.append(urlunparse(parsed._replace(netloc=netloc)))
    return list(dict.fromkeys(out))


def demand_link_from_display_html(html: str, display_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    direct = sub._extract_bse_demand_url(soup, display_url)
    if direct:
        return direct
    decoded = html_lib.unescape(html)
    match = re.search(
        r"(?:https?://[^'\"\s)]+)?(?:/[^'\"\s)]*)?CummDemandSchedule(?:\.aspx)?\?[^'\"\s)<>]+",
        decoded,
        flags=re.I,
    )
    return urljoin(display_url, match.group(0)) if match else None


def demand_candidates(session: requests.Session, rows: list[IssueLink]) -> tuple[list[str], list[str]]:
    candidates: list[str] = []
    diagnostics: list[str] = []
    for row in rows:
        if row.direct_demand_url:
            candidates.extend(_alternate_bse_hosts(row.direct_demand_url))
        if row.display_url:
            try:
                response = session.get(row.display_url, timeout=25, headers={"Referer": row.index_url})
                response.raise_for_status()
                discovered = demand_link_from_display_html(response.text, row.display_url)
                if discovered:
                    candidates.extend(_alternate_bse_hosts(discovered))
                else:
                    diagnostics.append(f"display page had no demand link: {row.display_url}")
            except Exception as exc:
                diagnostics.append(f"display fetch failed {row.display_url}: {exc}")
            constructed = sub._demand_url_from_display_url(row.display_url)
            if constructed:
                candidates.extend(_alternate_bse_hosts(constructed))
    return list(dict.fromkeys(candidates)), diagnostics


def diagnose_demand_html(html: str) -> str:
    """Return bounded markup diagnostics without dumping ViewState or full HTML."""
    soup = BeautifulSoup(html, "html.parser")
    table_bits = []
    for table in soup.select("table")[:8]:
        ident = table.get("id") or "-"
        classes = ".".join(table.get("class") or []) or "-"
        rows = []
        for tr in table.select("tr")[:10]:
            cells = [
                re.sub(r"\s+", " ", cell.get_text(" ", strip=True))[:100]
                for cell in tr.find_all(["th", "td"], recursive=False)
            ]
            if cells:
                rows.append(" | ".join(cells))
        if rows:
            table_bits.append(f"table#{ident}.{classes}: " + " || ".join(rows[:6]))

    hidden_names = []
    for field in soup.select('input[type="hidden"][name]'):
        name = str(field.get("name") or "")
        if name and name not in {"__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR"}:
            hidden_names.append(name)

    scripts = []
    for script in soup.select("script"):
        src = script.get("src")
        if src:
            scripts.append(str(src))
    keywords = []
    decoded = html_lib.unescape(html)
    for key in ("QIB", "Retail", "NII", "Category", "Demand", "CummDemand", "ajax", "/api/", "IPONo", "RC100"):
        match = re.search(re.escape(key), decoded, flags=re.I)
        if not match:
            continue
        start = max(0, match.start() - 90)
        end = min(len(decoded), match.end() + 180)
        snippet = re.sub(r"\s+", " ", decoded[start:end])[:280]
        keywords.append(f"{key}=>{snippet}")

    bits = []
    if table_bits:
        bits.append("TABLES: " + " /// ".join(table_bits[:5]))
    if hidden_names:
        bits.append("HIDDEN: " + ",".join(dict.fromkeys(hidden_names))[:600])
    if scripts:
        bits.append("SCRIPTS: " + ",".join(dict.fromkeys(scripts))[:900])
    if keywords:
        bits.append("KEYWORDS: " + " /// ".join(keywords[:8]))
    return " || ".join(bits)[:5000] or "no useful table/script diagnostics"


def fetch_demand(session: requests.Session, rows: list[IssueLink]):
    urls, diagnostics = demand_candidates(session, rows)
    attempts: list[str] = []
    for url in urls:
        try:
            response = session.get(
                url,
                timeout=25,
                headers={"Referer": rows[0].index_url if rows else core.BSE_URL},
            )
            response.raise_for_status()
            parsed = sub.parse_bse_demand_html(response.text)
            if any(value is not None for value in parsed.values()):
                return parsed, url, diagnostics + attempts
            soup = BeautifulSoup(response.text, "html.parser")
            title = " ".join(soup.title.stripped_strings).strip() if soup.title else "no title"
            attempts.append(
                f"no categories {url} · {title} · {diagnose_demand_html(response.text)}"
            )
        except Exception as exc:
            attempts.append(f"fetch failed {url}: {exc}")
    raise ValueError("; ".join((diagnostics + attempts)[-6:]) or "no BSE demand candidates")


def priority_open_targets(payload: dict[str, Any], queue_payload: dict[str, Any], limit: int):
    """Refresh every currently open issue, not only records with missing fields.

    The missing-data queue is useful for structural gaps, but live subscription
    multiples can change many times after their first successful snapshot. Using
    queue membership as the target gate made already-populated issues silently
    stale. Keep the parameter for compatibility with existing runner versions,
    while delegating eligibility to the date-aware subscription scheduler.
    """
    del queue_payload
    return sub.candidate_records(payload, limit=limit)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--force-snapshot", action="store_true")
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    queue_payload = (
        json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    )
    targets = priority_open_targets(payload, queue_payload, args.limit)

    nse = sub.NSESubscriptionClient()
    bse_session = requests.Session()
    bse_session.headers.update(core.HEADERS)
    try:
        index, page_health = build_issue_index(bse_session)
        print(
            f"Priority BSE issue index: {len(index)} links across "
            f"{sum(1 for value in page_health.values() if value.get('ok'))} healthy pages"
        )
    except Exception as exc:
        index, page_health = [], {"error": str(exc)}

    attempted = updated = snapshots_added = failed = 0
    nse_records = bse_records = 0
    errors: list[str] = []
    warnings: list[str] = []

    for record in targets:
        attempted += 1
        company = str(record.get("company") or "")
        try:
            try:
                detail, series = nse.detail(
                    str(record.get("symbol") or "").strip(), record.get("board")
                )
                added = sub.update_record(
                    record,
                    detail,
                    series=series,
                    force_snapshot=args.force_snapshot,
                )
                source_used = "NSE"
                nse_records += 1
            except Exception as nse_exc:
                matches = best_issue_links(index, company)
                if not matches:
                    raise ValueError(f"NSE unavailable ({nse_exc}); no matching BSE issue link")
                parsed, source_url, diagnostics = fetch_demand(bse_session, matches)
                added = sub.apply_subscription(
                    record,
                    parsed,
                    source_name="BSE cumulative demand",
                    source_url=source_url,
                    snapshot_source="BSE cumulative demand",
                    force_snapshot=args.force_snapshot,
                )
                source_used = "BSE"
                bse_records += 1
                if diagnostics:
                    warnings.append(f"{company}: " + " | ".join(diagnostics[-2:]))
            updated += 1
            snapshots_added += int(bool(added))
            current = record.get("subscription") or {}
            print(
                f"Priority subscription {company} [{source_used}]: "
                f"QIB={current.get('qib')} NII={current.get('nii')} "
                f"Retail={current.get('retail')} Total={current.get('total')}"
            )
        except Exception as exc:
            failed += 1
            message = f"{company}: {exc}"
            errors.append(message)
            print(f"Priority subscription failed: {message}", file=sys.stderr)

    as_of = core.now_ist().isoformat(timespec="seconds")
    health = {
        "ok": failed == 0 if attempted else True,
        "attempted": attempted,
        "updated": updated,
        "snapshotsAdded": snapshots_added,
        "failed": failed,
        "nseRecords": nse_records,
        "bseFallbackRecords": bse_records,
        "asOf": as_of,
        "pageHealth": page_health,
        "warnings": warnings[:10],
        "errors": errors[:10],
    }
    meta = payload.setdefault("meta", {})
    meta["subscriptionHealth"] = health
    meta.setdefault("sourceHealth", {})["IPO-subscription"] = {
        "ok": health["ok"],
        "records": updated,
        "attempted": attempted,
        "snapshotsAdded": snapshots_added,
        "failed": failed,
        "nseRecords": nse_records,
        "bseFallbackRecords": bse_records,
        "asOf": as_of,
        "errors": errors[:5],
    }
    DATA_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        "Priority subscriptions: "
        f"attempted={attempted} updated={updated} snapshots_added={snapshots_added} "
        f"failed={failed} nse={nse_records} bse={bse_records}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
