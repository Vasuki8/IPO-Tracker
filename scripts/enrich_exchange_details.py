#!/usr/bin/env python3
"""Fill missing live/upcoming IPO terms from official BSE issue-detail pages.

The BSE public-issues list is useful for validation but does not expose fields
such as market lot, minimum bid quantity, registrar, lead managers, face value,
or symbol. Each equity IPO row links to DisplayIPO.aspx, which does expose those
fields. This enricher follows only the currently listed IPO detail links and
fills missing values without overwriting populated NSE values.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
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
import track_subscriptions as subscription_helpers  # noqa: E402

DATA_FILE = core.DATA_FILE


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
    co_leads = values_for("Co-Book Running Lead Manager", "Co Book Running Lead Manager")
    lead_values.extend(co_leads)
    lead_managers: list[str] = []
    for raw in lead_values:
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


def build_detail_index(session: requests.Session) -> tuple[list[tuple[str, str]], str]:
    last_error: Exception | None = None
    for page_url in core.BSE_URLS:
        try:
            response = session.get(page_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            index: list[tuple[str, str]] = []
            for tr in soup.find_all("tr"):
                label, display_url = subscription_helpers._extract_bse_display_link(tr, page_url)
                if not display_url:
                    continue
                company = _company_from_row(tr, label)
                key = core.canonical_company(company)
                if key:
                    index.append((key, display_url))
            if index:
                return index, page_url
            last_error = ValueError(f"No BSE DisplayIPO links found at {page_url}")
        except Exception as exc:  # noqa: BLE001 - beta BSE remains an official fallback
            last_error = exc
    if last_error:
        raise last_error
    raise ValueError("BSE issue detail index unavailable")


def best_url(index: list[tuple[str, str]], company: str) -> str | None:
    needle = core.canonical_company(company)
    if not needle:
        return None
    for key, url in index:
        if key == needle:
            return url
    for key, url in index:
        if needle in key or key in needle:
            return url
    scored = [(SequenceMatcher(None, needle, key).ratio(), url) for key, url in index]
    scored.sort(reverse=True)
    return scored[0][1] if scored and scored[0][0] >= 0.82 else None


def is_candidate(record: dict[str, Any], today: date) -> bool:
    open_date = core.iso_date(record.get("openDate"))
    if not open_date:
        return False
    try:
        opened = date.fromisoformat(open_date)
    except ValueError:
        return False
    if not (today - timedelta(days=45) <= opened <= today + timedelta(days=90)):
        return False
    return any(
        record.get(field) in (None, "", [], {})
        for field in ("symbol", "lotSize", "issueSizeCr", "registrar", "leadManagers")
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
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [record for record in payload.get("ipos") or [] if isinstance(record, dict)]
    today = core.now_ist().date()
    candidates = [record for record in records if is_candidate(record, today)]
    candidates.sort(key=lambda r: str(r.get("openDate") or ""), reverse=True)
    if args.limit > 0:
        candidates = candidates[: args.limit]

    session = requests.Session()
    session.headers.update(core.HEADERS)
    session.headers.update({"Referer": f"{core.BSE_HOME}/"})

    attempted = updated = failed = 0
    field_counts: dict[str, int] = {}
    errors: list[str] = []

    try:
        index, source_page = build_detail_index(session)
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

    for record in candidates:
        url = best_url(index, str(record.get("company") or ""))
        if not url:
            continue
        attempted += 1
        try:
            response = session.get(url, timeout=30, headers={"Referer": source_page})
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
        "attempted": attempted,
        "updated": updated,
        "failed": failed,
        "fieldsFilled": field_counts,
        "errors": errors[:10],
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"BSE detail enrichment: candidates={len(candidates)}, attempted={attempted}, "
        f"updated={updated}, failed={failed}, fields={field_counts}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
