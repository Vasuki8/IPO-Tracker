#!/usr/bin/env python3
"""Phase 4.5A NSE Primary Market monthly-report enricher v3.

v3 keeps v2's fixed archive discovery and adds support for the historical NSE
workbook layouts observed across the P4 two-year window:

- older and newer files may omit the Symbol column entirely;
- 2026 IPO rows may leave Instrument_Type blank;
- issue-size headers vary between "In Crores" and "In cr.";
- an otherwise exact symbol + issuer match may contain a bad workbook issue date.

Safety rules remain conservative. Exact symbol matches also require the exact
canonical issuer. Symbol-less workbooks are matched only by exact canonical
issuer plus a tight issue-date check. Existing normalized fields remain fill-only.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_nse_primary_market_reports_v2 as v2  # noqa: E402

base = v2.base
core = base.core
PARSER_VERSION = 3


def parse_report_rows(rows: list[list[str]], source_url: str) -> list[dict[str, Any]]:
    if not rows:
        return []

    header_index = None
    columns: dict[str, int] = {}
    for idx, row in enumerate(rows[:12]):
        candidate = {base.header_key(value): col for col, value in enumerate(row) if value}
        # Symbol is deliberately optional: many official 2024 and 2026 NSE
        # monthly workbooks do not publish it at all.
        required = {"companyname", "issuetype", "totalissuesize"}
        if required.issubset(candidate):
            header_index = idx
            columns = candidate
            break
    if header_index is None:
        return []

    output: list[dict[str, Any]] = []
    for row in rows[header_index + 1 :]:
        company = base._value(row, columns, "Company_Name", "Company Name")
        symbol = base._value(row, columns, "Symbol")
        issue_type = base._value(row, columns, "Issue_Type", "Issue Type") or ""
        instrument = base._value(row, columns, "Instrument_Type", "Instrument Type") or ""

        if not company or "IPO" not in issue_type.upper():
            continue
        # Blank Instrument_Type is common in newer IPO monthly reports. A
        # populated non-equity instrument remains an explicit rejection signal.
        if instrument and "EQUITY" not in instrument.upper():
            continue

        total_shares = core.integer(
            base._value(row, columns, "Total_Issue_Size", "Total Issue Size")
        )
        fresh_shares = core.integer(
            base._value(row, columns, "Fresh_Issue_Size", "Fresh Issue Size")
        )
        ofs_shares = core.integer(
            base._value(row, columns, "Offer_For_Sale", "Offer For Sale")
        )
        issue_price = core.number(base._value(row, columns, "Issue_Price", "Issue Price"))
        issue_size_cr = core.number(
            base._value(
                row,
                columns,
                "Issue_Size (In Crores)",
                "Issue Size (In Crores)",
                "Issue Size in Crores",
                "Issue Size (In cr.)",
                "Issue_Size (In cr.)",
                "Issue Size (Rs. Cr.)",
                "Issue Size (Rs Cr)",
            )
        )
        open_date = base.excel_date(
            base._value(row, columns, "Issue_Open_Date", "Issue Open Date")
        )
        close_date = base.excel_date(
            base._value(row, columns, "Issue_Close_Date", "Issue Close Date")
        )
        listing_date = base.excel_date(
            base._value(row, columns, "Listing_Date", "Listing Date")
        )

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
                "symbol": symbol.strip().upper() if symbol else None,
                "exchange": base._value(row, columns, "Exchange"),
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


def _date_distance(left: str | None, right: str | None) -> int:
    if not left or not right:
        return 99_999
    try:
        return abs((date.fromisoformat(left) - date.fromisoformat(right)).days)
    except ValueError:
        return 99_999


def best_report_row(rows: list[dict[str, Any]], record: dict[str, Any]) -> dict[str, Any] | None:
    """Return one safely identified monthly-report IPO row.

    A symbol is accepted only together with the same canonical issuer. This lets
    us tolerate a known bad issue date in one official workbook without allowing
    a recycled or malformed symbol to cross-match another issuer.

    When the workbook has no symbol, exact canonical issuer + near issue date is
    mandatory. This is the common 2024/2026 historical layout.
    """
    record_symbol = str(record.get("symbol") or "").strip().upper()
    record_key = core.canonical_company(str(record.get("company") or ""))
    record_open = core.iso_date(record.get("openDate"))

    if record_symbol and record_key:
        strong = [
            row
            for row in rows
            if str(row.get("symbol") or "").strip().upper() == record_symbol
            and row.get("matchKey") == record_key
        ]
        if len(strong) == 1:
            return strong[0]
        if len(strong) > 1 and record_open:
            dated = [row for row in strong if row.get("openDate")]
            if dated:
                dated.sort(key=lambda row: _date_distance(record_open, row.get("openDate")))
                if _date_distance(record_open, dated[0].get("openDate")) <= 45:
                    return dated[0]
            return None

    if not record_key:
        return None

    company_candidates = [row for row in rows if row.get("matchKey") == record_key]
    if not company_candidates:
        return None

    # A different populated report symbol is evidence against a company-only
    # fallback. Blank-symbol rows are the historical layout we explicitly support.
    compatible = [
        row
        for row in company_candidates
        if not row.get("symbol")
        or not record_symbol
        or str(row.get("symbol") or "").strip().upper() == record_symbol
    ]
    if not compatible:
        return None

    if record_open:
        dated = [row for row in compatible if row.get("openDate")]
        if dated:
            dated.sort(key=lambda row: _date_distance(record_open, row.get("openDate")))
            if _date_distance(record_open, dated[0].get("openDate")) <= 14:
                return dated[0]
            return None

    return compatible[0] if len(compatible) == 1 else None


# v2 owns the corrected archive discovery. Patch the shared v1 execution path
# with v3 parsing/matching before delegating to its mature fill-only main().
base.discover_report_urls = v2.discover_report_urls
base.parse_report_rows = parse_report_rows
base.best_report_row = best_report_row

DATA_FILE = base.DATA_FILE
INDEX_URL = base.INDEX_URL
extract_report_urls = v2.extract_report_urls
discover_report_urls = v2.discover_report_urls
read_xlsx_rows = base.read_xlsx_rows
download_report = base.download_report
merge_report_row = base.merge_report_row
is_candidate = base.is_candidate
excel_date = base.excel_date


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
