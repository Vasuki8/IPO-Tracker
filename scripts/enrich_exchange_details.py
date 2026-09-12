#!/usr/bin/env python3
"""Fill missing IPO terms from official BSE current and historical detail pages.

BSE's public-issue list pages link to DisplayIPO.aspx, which exposes fields such
as market lot, minimum bid quantity, issue shares, registrar and lead managers.
The current page covers live/forthcoming issues; the historical page (`id=2`)
provides older IPO links. This enricher combines both official indexes and uses
company + issue-start-date matching so repeated issuers cannot collide.

Populated NSE values remain primary: BSE fills gaps and records an independent
observation for conflict validation rather than silently overwriting NSE data.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402
import track_subscriptions as subscription_helpers  # noqa: E402

DATA_FILE = core.DATA_FILE
BSE_HISTORY_URL = f"{core.BSE_HOME}/markets/PublicIssues/IPOIssues_new.aspx?id=2&Type=P"
INDEX_URLS = tuple(dict.fromkeys((*core.BSE_URLS, BSE_HISTORY_URL)))


def clean_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _cell_texts(cell) -> list[str]:
    return [" ".join(str(x).split()) for x in cell.stripped_strings if str(x).strip()]


def parse_detail_html(html: str) -> dict[str, Any]:
    """Parse the stable label/value table exposed by BSE DisplayIPO.aspx."""
    soup = BeautifulSoup(html, "html.parser")
    pairs: dict[str, list[str]] = {}

    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        if len(cells) < 2:
            continue
        label = " ".join(cells[0].stripped_strings).strip()
        if not label:
            continue
        values: list[str] = []
        for cell in cells[1:]:
            values.extend(_cell_texts(cell))
        if values:
            pairs.setdefault(clean_label(label), []).extend(values)

    def values_for(*labels: str) -> list[str]:
        wanted = [clean_label(label) for label in labels]
        for wanted_label in wanted:
            if wanted_label in pairs:
                return pairs[wanted_label]
        for key, values in pairs.items():
            if any(wanted_label and wanted_label in key for wanted_label in wanted):
                return values
        return []

    def text_for(*labels: str) -> str | None:
        values = values_for(*labels)
        return " ".join(values).strip() if values else None

    symbol = text_for("Symbol")
    period = text_for("Issue Period")
    od, cd = core.parse_period(period or "")
    price_text = text_for("Price Band", "Issue Price", "Offer Price")
    band = core.parse_price_band_text(price_text or "") if price_text else None

    market_lot = core.integer(text_for("Market Lot"))
    min_bid = core.integer(text_for("Minimum Bid Quantity"))
    lot_size = min_bid or market_lot

    shares = core.integer(
        text_for(
            "Issue Size – No. of Shares",
            "Issue Size - No. of Shares",
            "Issue Size (No. of Shares)",
            "Issue Size No of Shares",
        )
    )
    cap = core.number((band or {}).get("max"))
    issue_size_cr = round(shares * cap / 10_000_000, 2) if shares and cap else None

    lead_values = values_for(
        "Book Running Lead Manager",
        "Book Running Lead Managers",
        "Lead Managers",
        "Lead Manager",
    )
    lead_values.extend(values_for("Co-Book Running Lead Manager", "Co Book Running Lead Manager"))
    lead_managers: list[str] = []
    for raw in lead_values:
        # BSE commonly renders numbered managers in a single cell.
        for part in re.split(r"(?:^|\s)\d+\)\s*|\s*;\s*|\s*\|\s*", raw):
            name = " ".join(part.split()).strip(" ,-;")
            if name and name not in lead_managers:
                lead_managers.append(name)

    registrar_values = values_for("Registrar", "Name of the Registrar")
    registrar = registrar_values[0].strip() if registrar_values else None

    face_value = core.number(text_for("Face Value"))
    min_investment = round(lot_size * cap, 2) if lot_size and cap else None

    security_type = text_for("Security Type")
    is_equity = not security_type or "equity" in security_type.lower()

    return {
        "isEquity": is_equity,
        "symbol": symbol,
        "openDate": od,
        "closeDate": cd,
        "priceBand": band,
        "marketLot": market_lot,
        "minimumBidQuantity": min_bid,
        "lotSize": lot_size,
        "sharesOffered": shares,
        "issueSizeCr": issue_size_cr,
        "faceValue": face_value,
        "minInvestment": min_investment,
        "leadManagers": lead_managers,
        "registrar": registrar,
    }


def _company_from_row(tr, label: str | None) -> str:
    if label and len(label) > 3:
        return label
    cells = tr.find_all("td", recursive=False)
    if cells:
        return " ".join(cells[0].stripped_strings).strip()
    return ""


def _start_date_from_display_url(url: str) -> str | None:
    """Extract BSE's historical `startdt=DD/MM/YYYY` query parameter."""
    try:
        query = {str(k).lower(): v for k, v in parse_qs(urlparse(unquote(url)).query).items()}
        values = query.get("startdt") or []
        if not values:
            return None
        raw = str(values[0]).strip()
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt).date().isoformat()
            except ValueError:
                continue
    except Exception:
        return None
    return None


def build_detail_index(session: requests.Session) -> tuple[list[dict[str, str | None]], dict[str, Any]]:
    """Combine current + historical BSE IPO detail indexes."""
    index: list[dict[str, str | None]] = []
    seen_urls: set[str] = set()
    page_health: dict[str, Any] = {}

    for page_url in INDEX_URLS:
        try:
            response = session.get(page_url, timeout=35)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            count_before = len(index)
            for tr in soup.find_all("tr"):
                label, display_url = subscription_helpers._extract_bse_display_link(tr, page_url)
                if not display_url or display_url in seen_urls:
                    continue
                # Historical BSE pages can contain other public-issue types. Only
                # follow links explicitly marked as IPO when the parameter exists.
                low_url = display_url.lower()
                if "type=" in low_url and "type=ipo" not in low_url:
                    continue
                company = _company_from_row(tr, label)
                key = core.canonical_company(company)
                if not key:
                    continue
                seen_urls.add(display_url)
                index.append(
                    {
                        "key": key,
                        "url": display_url,
                        "openDate": _start_date_from_display_url(display_url),
                        "indexUrl": page_url,
                    }
                )
            page_health[page_url] = {"ok": True, "records": len(index) - count_before}
        except Exception as exc:  # each official page is independently optional
            page_health[page_url] = {"ok": False, "records": 0, "error": str(exc)[:250]}

    if not index:
        failures = [f"{url}: {info.get('error')}" for url, info in page_health.items() if not info.get("ok")]
        raise ValueError("No BSE DisplayIPO links found; " + "; ".join(failures[:3]))
    return index, page_health


def _date_distance(left: str | None, right: str | None) -> int:
    if not left or not right:
        return 99_999
    try:
        return abs((date.fromisoformat(left) - date.fromisoformat(right)).days)
    except ValueError:
        return 99_999


def best_url(index: list[dict[str, str | None]], company: str, open_date: str | None = None) -> str | None:
    """Match issuer first, then choose the closest official issue start date."""
    needle = core.canonical_company(company)
    if not needle:
        return None

    exact = [item for item in index if item.get("key") == needle]
    contained = [
        item
        for item in index
        if item not in exact
        and item.get("key")
        and (needle in str(item["key"]) or str(item["key"]) in needle)
    ]
    candidates = exact or contained

    if not candidates:
        scored: list[tuple[float, dict[str, str | None]]] = []
        for item in index:
            ratio = SequenceMatcher(None, needle, str(item.get("key") or "")).ratio()
            if ratio >= 0.82:
                scored.append((ratio, item))
        if not scored:
            return None
        best_ratio = max(score for score, _ in scored)
        candidates = [item for score, item in scored if score >= best_ratio - 0.02]

    # Historical issuers may have multiple issues. If BSE supplied startdt, a
    # date within seven days is a strong identity check. Otherwise prefer a
    # current-page link with no date metadata only when there is one candidate.
    dated = [item for item in candidates if item.get("openDate")]
    if open_date and dated:
        dated.sort(key=lambda item: _date_distance(open_date, item.get("openDate")))
        if _date_distance(open_date, dated[0].get("openDate")) <= 7:
            return str(dated[0]["url"])
        # Do not cross-match a repeated issuer to a distant historical offer.
        if len(candidates) > 1:
            return None
    return str(candidates[0]["url"]) if candidates else None


def is_candidate(record: dict[str, Any], today: date, history_days: int) -> bool:
    open_date = core.iso_date(record.get("openDate"))
    if not open_date:
        return False
    try:
        opened = date.fromisoformat(open_date)
    except ValueError:
        return False
    if not (today - timedelta(days=max(0, history_days)) <= opened <= today + timedelta(days=90)):
        return False
    return any(
        record.get(field) in (None, "", [], {})
        for field in ("lotSize", "issueSizeCr", "registrar", "leadManagers")
    )


def merge_detail(record: dict[str, Any], detail: dict[str, Any], url: str) -> list[str]:
    if not detail.get("isEquity", True):
        return []
    changed: list[str] = []

    simple_fields = (
        "symbol",
        "openDate",
        "closeDate",
        "priceBand",
        "lotSize",
        "sharesOffered",
        "issueSizeCr",
        "faceValue",
        "minInvestment",
        "registrar",
    )
    for field in simple_fields:
        value = detail.get(field)
        if record.get(field) in (None, "", [], {}) and value not in (None, "", [], {}):
            record[field] = value
            changed.append(field)

    if not record.get("leadManagers") and detail.get("leadManagers"):
        record["leadManagers"] = detail["leadManagers"]
        changed.append("leadManagers")

    if detail.get("minimumBidQuantity") is not None:
        record["minimumBidQuantity"] = detail["minimumBidQuantity"]
    if detail.get("marketLot") is not None:
        record["marketLot"] = detail["marketLot"]

    stamp = core.source_stamp("BSE issue detail", url, "exchange")
    sources = list(record.get("sources") or [])
    sources = [s for s in sources if str((s or {}).get("name") or "") != "BSE issue detail"]
    sources.append(stamp)
    record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    bse_obs = dict((record.get("observations") or {}).get("BSE") or {})
    for field in ("openDate", "closeDate", "priceBand", "lotSize", "issueSizeCr"):
        if detail.get(field) is not None:
            bse_obs[field] = detail[field]
    record.setdefault("observations", {})["BSE"] = bse_obs
    record["validation"] = core.build_validation(record)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument(
        "--history-days",
        type=int,
        default=730,
        help="Backfill exchange detail for IPOs opened within this many days (default: 730).",
    )
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [record for record in payload.get("ipos") or [] if isinstance(record, dict)]
    today = core.now_ist().date()
    candidates = [record for record in records if is_candidate(record, today, args.history_days)]
    candidates.sort(key=lambda r: str(r.get("openDate") or ""), reverse=True)
    if args.limit > 0:
        candidates = candidates[: args.limit]

    session = requests.Session()
    session.headers.update(core.HEADERS)
    session.headers.update({"Referer": f"{core.BSE_HOME}/"})

    attempted = updated = failed = matched = 0
    field_counts: dict[str, int] = {}
    errors: list[str] = []

    try:
        index, page_health = build_detail_index(session)
    except Exception as exc:  # source outage must not block the core dataset
        health = {
            "ok": False,
            "attempted": 0,
            "updated": 0,
            "failed": 0,
            "error": str(exc),
        }
        payload.setdefault("meta", {}).setdefault("sourceHealth", {})["BSE-detail"] = health
        DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"BSE detail enrichment unavailable: {exc}")
        return 0

    print(f"BSE detail index: {len(index)} IPO links across {len(INDEX_URLS)} official index URLs")

    for record in candidates:
        url = best_url(index, str(record.get("company") or ""), core.iso_date(record.get("openDate")))
        if not url:
            continue
        matched += 1
        attempted += 1
        try:
            response = session.get(url, timeout=30, headers={"Referer": BSE_HISTORY_URL})
            response.raise_for_status()
            detail = parse_detail_html(response.text)
            changed = merge_detail(record, detail, url)
            if changed:
                updated += 1
                for field in changed:
                    field_counts[field] = field_counts.get(field, 0) + 1
            print(f"BSE detail {record.get('company')}: {', '.join(changed) if changed else 'validated'}")
        except Exception as exc:  # one malformed page cannot block other IPOs
            failed += 1
            errors.append(f"{record.get('company')}: {exc}")

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["BSE-detail"] = {
        "ok": failed == 0 if attempted else True,
        "records": updated,
        "indexRecords": len(index),
        "candidates": len(candidates),
        "matched": matched,
        "attempted": attempted,
        "updated": updated,
        "failed": failed,
        "historyDays": args.history_days,
        "fieldsFilled": field_counts,
        "indexHealth": page_health,
        "errors": errors[:10],
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"BSE detail enrichment: candidates={len(candidates)}, matched={matched}, "
        f"attempted={attempted}, updated={updated}, failed={failed}, fields={field_counts}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
