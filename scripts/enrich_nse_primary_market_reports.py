#!/usr/bin/env python3
"""Phase 4.5A backfill from official NSE Primary Market monthly XLSX reports.

NSE publishes monthly Primary Market reports containing issuer-level IPO facts,
including symbol, Total Issue Size (shares), Fresh Issue Size, Offer for Sale,
issue/open/close/listing dates, issue price and Issue Size (₹ crore). This source
fills the large recent-history gaps left by the live/past JSON endpoints.

Safety rules:
- only equity rows whose Issue_Type contains IPO are accepted;
- records are matched by exact symbol or canonical issuer, with issue-date checks;
- existing normalized values are never overwritten;
- Fresh/OFS rupee amounts are derived only from official share counts and the
  official issue price in the same monthly report;
- every merge retains the exact monthly XLSX URL as exchange provenance.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402

DATA_FILE = core.DATA_FILE
INDEX_URL = "https://www.nseindia.com/static/regulations/segment-wise-historical-reports-capital-primary-market"
REPORT_NAME_RE = re.compile(r"primary[_\s-]*market.*\.xlsx(?:\?|$)", re.I)

MAIN_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
DOC_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
EXCEL_EPOCH = date(1899, 12, 30)


def header_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def excel_date(value: Any) -> str | None:
    direct = core.iso_date(value)
    if direct:
        return direct
    try:
        serial = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if not 20_000 <= serial <= 80_000:
        return None
    return (EXCEL_EPOCH + timedelta(days=int(serial))).isoformat()


def _column_index(ref: str) -> int:
    match = re.match(r"[A-Z]+", ref or "A")
    letters = match.group(0) if match else "A"
    value = 0
    for char in letters:
        value = value * 26 + (ord(char) - 64)
    return value - 1


def read_xlsx_rows(data: bytes) -> list[list[str]]:
    """Read the first worksheet using only stdlib OOXML primitives."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", MAIN_NS):
                shared.append("".join(node.text or "" for node in item.iterfind(".//m:t", MAIN_NS)))

        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        relationships = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        targets = {
            relation.attrib["Id"]: relation.attrib["Target"]
            for relation in relationships.findall("r:Relationship", REL_NS)
        }
        first_sheet = workbook.find(".//m:sheet", MAIN_NS)
        if first_sheet is None:
            return []
        target = targets.get(first_sheet.attrib.get(DOC_REL, ""))
        if not target:
            return []
        target = target.lstrip("/")
        sheet_path = target if target.startswith("xl/") else f"xl/{target}"
        sheet = ET.fromstring(zf.read(sheet_path))

        out: list[list[str]] = []
        for row in sheet.findall(".//m:sheetData/m:row", MAIN_NS):
            values: dict[int, str] = {}
            for cell in row.findall("m:c", MAIN_NS):
                index = _column_index(cell.attrib.get("r", "A1"))
                kind = cell.attrib.get("t")
                if kind == "inlineStr":
                    text = "".join(node.text or "" for node in cell.iterfind(".//m:t", MAIN_NS))
                else:
                    node = cell.find("m:v", MAIN_NS)
                    raw = node.text if node is not None else ""
                    if kind == "s" and raw:
                        try:
                            text = shared[int(raw)]
                        except (ValueError, IndexError):
                            text = raw
                    else:
                        text = raw
                text = " ".join(str(text or "").split())
                if text:
                    values[index] = text
            if not values:
                continue
            out.append([values.get(i, "") for i in range(max(values) + 1)])
        return out


def _value(row: list[str], columns: dict[str, int], *aliases: str) -> str | None:
    for alias in aliases:
        index = columns.get(header_key(alias))
        if index is not None and index < len(row):
            value = str(row[index] or "").strip()
            if value and value.upper() not in {"NA", "N/A", "-", "--"}:
                return value
    return None


def parse_report_rows(rows: list[list[str]], source_url: str) -> list[dict[str, Any]]:
    if not rows:
        return []
    header_index = None
    columns: dict[str, int] = {}
    for idx, row in enumerate(rows[:10]):
        candidate = {header_key(value): col for col, value in enumerate(row) if value}
        required = {"companyname", "symbol", "issuetype", "totalissuesize"}
        if required.issubset(candidate):
            header_index = idx
            columns = candidate
            break
    if header_index is None:
        return []

    output: list[dict[str, Any]] = []
    for row in rows[header_index + 1 :]:
        company = _value(row, columns, "Company_Name", "Company Name")
        symbol = _value(row, columns, "Symbol")
        issue_type = _value(row, columns, "Issue_Type", "Issue Type") or ""
        instrument = _value(row, columns, "Instrument_Type", "Instrument Type") or ""
        if not company or not symbol or "IPO" not in issue_type.upper():
            continue
        if instrument and "EQUITY" not in instrument.upper():
            continue

        total_shares = core.integer(_value(row, columns, "Total_Issue_Size", "Total Issue Size"))
        fresh_shares = core.integer(_value(row, columns, "Fresh_Issue_Size", "Fresh Issue Size"))
        ofs_shares = core.integer(_value(row, columns, "Offer_For_Sale", "Offer For Sale"))
        issue_price = core.number(_value(row, columns, "Issue_Price", "Issue Price"))
        issue_size_cr = core.number(
            _value(row, columns, "Issue_Size (In Crores)", "Issue Size (In Crores)", "Issue Size in Crores")
        )
        open_date = excel_date(_value(row, columns, "Issue_Open_Date", "Issue Open Date"))
        close_date = excel_date(_value(row, columns, "Issue_Close_Date", "Issue Close Date"))
        listing_date = excel_date(_value(row, columns, "Listing_Date", "Listing Date"))

        fresh_cr = (
            round(fresh_shares * issue_price / 10_000_000, 4)
            if fresh_shares is not None and issue_price is not None
            else None
        )
        ofs_cr = (
            round(ofs_shares * issue_price / 10_000_000, 4)
            if ofs_shares is not None and issue_price is not None
            else None
        )
        composition = {
            "freshShares": fresh_shares,
            "ofsShares": ofs_shares,
            "freshIssueCr": fresh_cr,
            "ofsCr": ofs_cr,
            "totalIssueSizeCr": issue_size_cr,
            "valuationPriceUsed": issue_price,
        }

        output.append(
            {
                "company": company,
                "matchKey": core.canonical_company(company),
                "symbol": symbol.strip().upper(),
                "exchange": _value(row, columns, "Exchange"),
                "issueType": issue_type,
                "openDate": open_date,
                "closeDate": close_date,
                "listingDate": listing_date,
                "sharesOffered": total_shares,
                "freshIssueCr": fresh_cr,
                "ofsCr": ofs_cr,
                "issueSizeCr": issue_size_cr,
                "issuePrice": issue_price,
                "issueComposition": composition,
                "sourceUrl": source_url,
            }
        )
    return output


def discover_report_urls(session: requests.Session, max_reports: int) -> list[str]:
    # Prime NSE cookies before reading the static historical-report page.
    try:
        session.get(core.NSE_HOME, timeout=20)
    except Exception:
        pass
    response = session.get(INDEX_URL, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    urls: list[str] = []
    for anchor in soup.select("a[href]"):
        href = urljoin(INDEX_URL, str(anchor.get("href") or ""))
        context = f"{href} {' '.join(anchor.stripped_strings)}"
        if not REPORT_NAME_RE.search(context):
            continue
        if href not in urls:
            urls.append(href)
    return urls[:max_reports] if max_reports > 0 else urls


def download_report(session: requests.Session, url: str) -> bytes:
    headers = {
        **core.HEADERS,
        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,*/*",
        "Referer": core.NSE_HOME + "/",
    }
    response = session.get(url, headers=headers, timeout=45)
    response.raise_for_status()
    data = response.content
    if len(data) < 1_000 or not data.startswith(b"PK"):
        raise ValueError("NSE monthly report did not return a valid XLSX archive")
    return data


def _date_distance(left: str | None, right: str | None) -> int:
    if not left or not right:
        return 99_999
    try:
        return abs((date.fromisoformat(left) - date.fromisoformat(right)).days)
    except ValueError:
        return 99_999


def best_report_row(rows: list[dict[str, Any]], record: dict[str, Any]) -> dict[str, Any] | None:
    symbol = str(record.get("symbol") or "").strip().upper()
    match_key = core.canonical_company(str(record.get("company") or ""))
    open_date = core.iso_date(record.get("openDate"))

    candidates = [row for row in rows if symbol and row.get("symbol") == symbol]
    if not candidates and match_key:
        candidates = [row for row in rows if row.get("matchKey") == match_key]
    if not candidates:
        return None

    if open_date:
        dated = [row for row in candidates if row.get("openDate")]
        if dated:
            dated.sort(key=lambda row: _date_distance(open_date, row.get("openDate")))
            if _date_distance(open_date, dated[0].get("openDate")) <= 14:
                return dated[0]
            return None
    return candidates[0] if len(candidates) == 1 else None


def merge_report_row(record: dict[str, Any], row: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    for field in ("symbol", "openDate", "closeDate", "listingDate", "sharesOffered", "issueSizeCr", "freshIssueCr", "ofsCr"):
        value = row.get(field)
        if record.get(field) in (None, "", [], {}) and value not in (None, "", [], {}):
            record[field] = value
            changed.append(field)

    incoming_composition = row.get("issueComposition") or {}
    if not record.get("issueComposition") and any(value is not None for value in incoming_composition.values()):
        record["issueComposition"] = incoming_composition
        changed.append("issueComposition")

    source_url = str(row.get("sourceUrl") or INDEX_URL)
    source = core.source_stamp("NSE primary-market monthly report", source_url, "exchange")
    sources = list(record.get("sources") or [])
    if not any(str(item.get("url") or "") == source_url for item in sources if isinstance(item, dict)):
        sources.append(source)
        record["sources"] = core.dedupe_dicts(sources, ("name", "url"))

    nse_obs = dict((record.get("observations") or {}).get("NSE") or {})
    for field in ("openDate", "closeDate", "issueSizeCr"):
        if nse_obs.get(field) is None and row.get(field) is not None:
            nse_obs[field] = row[field]
    record.setdefault("observations", {})["NSE"] = nse_obs
    record["validation"] = core.build_validation(record)
    return changed


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
        for field in ("issueSizeCr", "issueComposition", "listingDate")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history-days", type=int, default=730)
    parser.add_argument("--max-reports", type=int, default=30)
    parser.add_argument("--limit", type=int, default=0, help="Optional record limit; 0 means all candidates.")
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]
    today = core.now_ist().date()
    candidates = [row for row in records if is_candidate(row, today, args.history_days)]
    candidates.sort(key=lambda row: str(row.get("openDate") or ""), reverse=True)
    if args.limit > 0:
        candidates = candidates[: args.limit]

    session = requests.Session()
    session.headers.update(core.HEADERS)
    report_urls: list[str] = []
    report_rows: list[dict[str, Any]] = []
    failures: list[str] = []

    try:
        report_urls = discover_report_urls(session, args.max_reports)
    except Exception as exc:
        failures.append(f"index: {exc}")

    for url in report_urls:
        try:
            data = download_report(session, url)
            report_rows.extend(parse_report_rows(read_xlsx_rows(data), url))
        except Exception as exc:
            failures.append(f"{urlparse(url).path.rsplit('/', 1)[-1]}: {exc}")

    updated = matched = 0
    field_counts: dict[str, int] = {}
    for record in candidates:
        row = best_report_row(report_rows, record)
        if not row:
            continue
        matched += 1
        changed = merge_report_row(record, row)
        if changed:
            updated += 1
            for field in changed:
                field_counts[field] = field_counts.get(field, 0) + 1

    health = {
        "ok": bool(report_rows) and len(failures) < max(1, len(report_urls)),
        "indexUrl": INDEX_URL,
        "reportsDiscovered": len(report_urls),
        "reportRows": len(report_rows),
        "candidates": len(candidates),
        "matched": matched,
        "updated": updated,
        "historyDays": args.history_days,
        "fieldsFilled": field_counts,
        "errors": failures[:10],
        "asOf": core.now_ist().isoformat(timespec="seconds"),
    }
    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["NSE-primary-market-reports"] = health
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "NSE primary-market reports: "
        f"reports={len(report_urls)}, rows={len(report_rows)}, candidates={len(candidates)}, "
        f"matched={matched}, updated={updated}, fields={field_counts}, failures={len(failures)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
