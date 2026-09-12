#!/usr/bin/env python3
"""Core updater v2 with aggregate BSE + BSE SME current-issue coverage.

The original quality-gated updater remains authoritative for NSE/SEBI merging and
validation. This wrapper only widens the BSE current-issue collector so a BSE-SME
only IPO cannot disappear merely because the main BSE public-issues page is the
first healthy endpoint.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_update as gated  # noqa: E402

core = gated.core
BSE_SME_CURRENT_URL = "https://www.bsesme.com/PublicIssues/PublicIssues.aspx?id=2"


def _header_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _find_header_index(headers: list[str], *aliases: str) -> int | None:
    wanted = {_header_key(alias) for alias in aliases}
    for index, value in enumerate(headers):
        if value in wanted:
            return index
    return None


def parse_bse_sme_html(html: str, source_url: str = BSE_SME_CURRENT_URL) -> list[dict[str, Any]]:
    """Parse BSE SME's current public-issue table by header names.

    Unlike the main BSE parser, this does not assume fixed column positions. It
    requires explicit company/open/close headers and therefore fails closed if
    the page layout changes.
    """
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict[str, Any]] = []

    company_aliases = ("Security Name", "Company Name", "Issue Name", "Issuer", "Name of the Issue")
    open_aliases = ("Start Date", "Open Date", "Issue Open Date", "Issue Opening Date", "Opening Date")
    close_aliases = ("End Date", "Close Date", "Issue Close Date", "Issue Closing Date", "Closing Date")
    price_aliases = ("Offer Price", "Issue Price", "Price Band", "Price")
    lot_aliases = ("Lot Size", "Market Lot", "Minimum Bid Quantity", "Min Bid Qty")
    type_aliases = ("Type of Issue", "Issue Type", "Type")
    status_aliases = ("Issue Status", "Status")
    listing_aliases = ("Listing Date", "Date of Listing")

    for table in soup.find_all("table"):
        header_row = None
        headers: list[str] = []
        indexes: dict[str, int | None] = {}

        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"], recursive=False)
            texts = [" ".join(cell.stripped_strings).strip() for cell in cells]
            normalized = [_header_key(text) for text in texts]
            company_i = _find_header_index(normalized, *company_aliases)
            open_i = _find_header_index(normalized, *open_aliases)
            close_i = _find_header_index(normalized, *close_aliases)
            if company_i is not None and open_i is not None and close_i is not None:
                header_row = tr
                headers = normalized
                indexes = {
                    "company": company_i,
                    "open": open_i,
                    "close": close_i,
                    "price": _find_header_index(normalized, *price_aliases),
                    "lot": _find_header_index(normalized, *lot_aliases),
                    "type": _find_header_index(normalized, *type_aliases),
                    "status": _find_header_index(normalized, *status_aliases),
                    "listing": _find_header_index(normalized, *listing_aliases),
                }
                break

        if header_row is None:
            continue

        for tr in header_row.find_all_next("tr"):
            if tr.find_parent("table") is not table:
                break
            cells = tr.find_all(["th", "td"], recursive=False)
            texts = [" ".join(cell.stripped_strings).strip() for cell in cells]
            required = [indexes["company"], indexes["open"], indexes["close"]]
            if any(value is None for value in required):
                continue
            max_required = max(int(value) for value in required if value is not None)
            if len(texts) <= max_required:
                continue

            def value(name: str) -> str | None:
                idx = indexes.get(name)
                if idx is None or idx >= len(texts):
                    return None
                text = texts[idx].strip()
                return text or None

            company = value("company") or ""
            issue_type = (value("type") or "IPO").strip().upper()
            if issue_type and "IPO" not in issue_type:
                continue
            open_date = core.iso_date(value("open"))
            close_date = core.iso_date(value("close"))
            if not company or not open_date or not close_date:
                continue

            listing_date = core.iso_date(value("listing"))
            price = core.parse_price_band_text(value("price") or "")
            lot = core.integer(value("lot"))
            status_text = value("status")
            source = core.source_stamp("BSE SME public issue", source_url, "exchange")
            observation = {
                "openDate": open_date,
                "closeDate": close_date,
                "listingDate": listing_date,
                "priceBand": price,
                "lotSize": lot,
                "issueSizeCr": None,
                "issueType": "IPO",
            }
            out.append(
                {
                    "id": core.slugify(company),
                    "matchKey": core.canonical_company(company),
                    "company": company,
                    "board": "SME",
                    "exchange": "BSE SME",
                    "status": core.derive_status(open_date, close_date, listing_date, status_text),
                    "openDate": open_date,
                    "closeDate": close_date,
                    "listingDate": listing_date,
                    "priceBand": price,
                    "lotSize": lot,
                    "issueSizeCr": None,
                    "issueType": "IPO",
                    "sources": [source],
                    "source": source,
                    "observations": {"BSE": observation},
                }
            )

    return core.dedupe_dicts(out, ("matchKey", "openDate", "closeDate"))


def aggregate_bse_current_issues(session, page_urls=None) -> list[dict[str, Any]]:
    urls = list(page_urls or [*core.BSE_URLS, BSE_SME_CURRENT_URL])
    rows: list[dict[str, Any]] = []
    failures: list[str] = []

    for url in urls:
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            if "bsesme.com" in url.lower():
                parsed = parse_bse_sme_html(response.text, url)
            else:
                parsed = gated.parse_bse_ipo_html(response.text, url)
            rows.extend(parsed)
            print(f"BSE current source {url}: {len(parsed)} IPO rows")
        except Exception as exc:  # one BSE endpoint must not suppress the others
            failures.append(f"{url}: {exc}")
            print(f"BSE current source failed {url}: {exc}", file=sys.stderr)

    if rows:
        return core.dedupe_dicts(rows, ("matchKey", "openDate", "closeDate"))
    if failures:
        raise RuntimeError("; ".join(failures[-3:]))
    return []


def current_issues_aggregate(self):
    return aggregate_bse_current_issues(self.s)


core.BSEClient.current_issues = current_issues_aggregate
BSEClient = core.BSEClient

# Re-export the normalizer/test helpers so this wrapper can be used as the new
# quality-gated entry point without changing downstream imports.
canonical_company = gated.canonical_company
parse_period = gated.parse_period
parse_price_band_text = gated.parse_price_band_text
field_equal = gated.field_equal
nse_issue_metrics = gated.nse_issue_metrics
normalize_nse_record = gated.normalize_nse_record
merge_non_null = gated.merge_non_null
merge_fill_only = gated.merge_fill_only
build_validation = gated.build_validation
clean_existing_record = gated.clean_existing_record


def main() -> int:
    return gated.main()


if __name__ == "__main__":
    raise SystemExit(main())
