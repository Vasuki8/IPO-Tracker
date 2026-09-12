#!/usr/bin/env python3
"""Backfill recent IPO detail fields from BSE's Historical Public Issues archive.

BSE has served the historical archive in two modes over time: some hosts/renderings
return the IPO table directly, while the older ASP.NET Web Forms page first asks
for an issue type and requires a normal form submission. This script supports
both behaviours on both official BSE hosts, then reuses the conservative BSE
detail parser/merge logic from enrich_exchange_details.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402
import enrich_exchange_details as detail  # noqa: E402
import track_subscriptions as link_helpers  # noqa: E402

DATA_FILE = core.DATA_FILE
HISTORY_URLS = (
    detail.BSE_HISTORY_URL,
    "https://beta.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=2&Type=P",
)


def history_form_payload(html: str) -> dict[str, str]:
    """Build fields submitted when a browser selects Public Issue-Book Building."""
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if form is None:
        raise ValueError("historical page did not contain its ASP.NET form")

    payload: dict[str, str] = {}
    for field in form.find_all("input"):
        name = field.get("name")
        if not name:
            continue
        input_type = str(field.get("type") or "text").lower()
        if input_type == "hidden":
            payload[name] = str(field.get("value") or "")

    select = form.find(
        "select",
        id=lambda value: bool(value and "ddlIssueType" in value),
    ) or form.find(
        "select",
        attrs={"name": lambda value: bool(value and "ddlIssueType" in value)},
    )
    if select is None or not select.get("name"):
        raise ValueError("historical issue-type selector was not found")

    chosen = None
    for option in select.find_all("option"):
        label = " ".join(option.stripped_strings).lower()
        if "public issue" in label and "book building" in label:
            chosen = option
            break
    if chosen is None:
        raise ValueError("historical page has no Public Issue-Book Building option")
    payload[str(select.get("name"))] = str(chosen.get("value") or "")

    submit = form.find(
        "input",
        id=lambda value: bool(value and "btnSubmit" in value),
    )
    if submit is not None and submit.get("name"):
        payload[str(submit.get("name"))] = str(submit.get("value") or "Submit")
    return payload


def history_index(html: str, page_url: str) -> list[dict[str, str | None]]:
    soup = BeautifulSoup(html, "html.parser")
    index: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for tr in soup.find_all("tr"):
        label, url = link_helpers._extract_bse_display_link(tr, page_url)
        if not url or url in seen:
            continue
        low = url.lower()
        if "type=" in low and "type=ipo" not in low:
            continue
        company = detail._company_from_row(tr, label)
        key = core.canonical_company(company)
        if not key:
            continue
        seen.add(url)
        index.append(
            {
                "key": key,
                "url": url,
                "openDate": detail._start_date_from_display_url(url),
                "indexUrl": page_url,
            }
        )
    return index


def fetch_history_index(session: requests.Session) -> tuple[list[dict[str, str | None]], str, dict[str, Any]]:
    """Try direct-table and ASP.NET-form modes on both official BSE hosts."""
    attempts: dict[str, Any] = {}
    last_error: Exception | None = None

    for page_url in HISTORY_URLS:
        try:
            initial = session.get(page_url, timeout=35, headers={"Referer": f"{core.BSE_HOME}/"})
            initial.raise_for_status()

            direct = history_index(initial.text, page_url)
            if direct:
                attempts[page_url] = {"ok": True, "mode": "direct", "records": len(direct)}
                return direct, page_url, attempts

            try:
                payload = history_form_payload(initial.text)
            except Exception as form_exc:
                attempts[page_url] = {
                    "ok": False,
                    "mode": "get",
                    "records": 0,
                    "error": str(form_exc)[:250],
                    "bytes": len(initial.content),
                }
                last_error = form_exc
                continue

            response = session.post(
                page_url,
                data=payload,
                timeout=45,
                headers={
                    "Referer": page_url,
                    "Origin": page_url.split("/markets/", 1)[0],
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            response.raise_for_status()
            posted = history_index(response.text, page_url)
            if posted:
                attempts[page_url] = {"ok": True, "mode": "aspnet-post", "records": len(posted)}
                return posted, page_url, attempts
            error = ValueError("ASP.NET submission returned no IPO detail links")
            attempts[page_url] = {
                "ok": False,
                "mode": "aspnet-post",
                "records": 0,
                "error": str(error),
                "bytes": len(response.content),
            }
            last_error = error
        except Exception as exc:  # try the other official host
            attempts[page_url] = {"ok": False, "records": 0, "error": str(exc)[:250]}
            last_error = exc

    summary = "; ".join(
        f"{url}: {info.get('error', 'no data')}" for url, info in attempts.items()
    )
    raise ValueError(f"BSE historical archive unavailable on official hosts: {summary}") from last_error


def is_candidate(record: dict[str, Any], today: date, history_days: int) -> bool:
    open_date = core.iso_date(record.get("openDate"))
    if not open_date:
        return False
    try:
        opened = date.fromisoformat(open_date)
    except ValueError:
        return False
    if opened < today - timedelta(days=max(0, history_days)) or opened > today:
        return False
    return any(
        record.get(field) in (None, "", [], {})
        for field in ("lotSize", "issueSizeCr", "registrar", "leadManagers")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history-days", type=int, default=730)
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    today = core.now_ist().date()
    candidates = [row for row in records if is_candidate(row, today, args.history_days)]
    candidates.sort(key=lambda row: str(row.get("openDate") or ""), reverse=True)

    session = requests.Session()
    session.headers.update(core.HEADERS)
    session.headers.update(
        {
            "Referer": f"{core.BSE_HOME}/",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
    )

    try:
        index, archive_url, archive_health = fetch_history_index(session)
    except Exception as exc:  # official archive outage must not block other refreshes
        payload.setdefault("meta", {}).setdefault("sourceHealth", {})["BSE-history-detail"] = {
            "ok": False,
            "records": 0,
            "attempted": 0,
            "hosts": list(HISTORY_URLS),
            "error": str(exc)[:500],
        }
        DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"BSE historical detail unavailable: {exc}")
        return 0

    matched_records: list[tuple[dict[str, Any], str]] = []
    for record in candidates:
        url = detail.best_url(
            index,
            str(record.get("company") or ""),
            core.iso_date(record.get("openDate")),
        )
        if url:
            matched_records.append((record, url))
    if args.limit > 0:
        matched_records = matched_records[: args.limit]

    attempted = updated = failed = 0
    field_counts: dict[str, int] = {}
    errors: list[str] = []
    for record, url in matched_records:
        attempted += 1
        try:
            response = session.get(url, timeout=30, headers={"Referer": archive_url})
            response.raise_for_status()
            parsed = detail.parse_detail_html(response.text)
            changed = detail.merge_detail(record, parsed, url)
            if changed:
                updated += 1
                for field in changed:
                    field_counts[field] = field_counts.get(field, 0) + 1
            print(
                f"BSE history {record.get('company')} ({record.get('openDate')}): "
                f"{', '.join(changed) if changed else 'validated'}"
            )
        except Exception as exc:  # one old page must not stop the backfill
            failed += 1
            errors.append(f"{record.get('company')}: {exc}")

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["BSE-history-detail"] = {
        "ok": failed == 0 if attempted else True,
        "indexRecords": len(index),
        "archiveUrl": archive_url,
        "archiveHealth": archive_health,
        "candidates": len(candidates),
        "matched": len(matched_records),
        "attempted": attempted,
        "records": updated,
        "updated": updated,
        "failed": failed,
        "historyDays": args.history_days,
        "fieldsFilled": field_counts,
        "errors": errors[:10],
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"BSE historical detail: index={len(index)}, candidates={len(candidates)}, "
        f"matched={len(matched_records)}, attempted={attempted}, updated={updated}, "
        f"failed={failed}, fields={field_counts}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
