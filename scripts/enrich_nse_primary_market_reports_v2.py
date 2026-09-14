#!/usr/bin/env python3
"""Phase 4.5A NSE Primary Market monthly-report enricher v2.

v2 fixes archive-link discovery on NSE's static historical-report page. The v1
parser correctly handled workbook data, but tested the XLSX URL together with the
anchor label; appending label text after `.xlsx` prevented its end-anchored regex
from matching. v2 validates the URL itself and keeps the existing v1 parsing,
matching, fill-only merge and provenance behavior unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from parser_loader import isolated_module
base = isolated_module("enrich_nse_primary_market_reports")

PARSER_VERSION = 2


def extract_report_urls(html: str, max_reports: int = 0) -> list[str]:
    """Extract official NSE Primary Market XLSX links in page order."""
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for anchor in soup.select("a[href]"):
        href = urljoin(base.INDEX_URL, str(anchor.get("href") or "").strip())
        label = " ".join(anchor.stripped_strings).strip()
        parsed = urlparse(href)
        if not parsed.path.lower().endswith(".xlsx"):
            continue
        # Prefer the filename signal used by current archives, but accept a
        # clearly labelled Primary Market workbook for older naming variants.
        if not base.REPORT_NAME_RE.search(href) and "primary market" not in label.lower():
            continue
        if href not in urls:
            urls.append(href)
    return urls[:max_reports] if max_reports > 0 else urls


def discover_report_urls(session, max_reports: int) -> list[str]:
    try:
        session.get(base.core.NSE_HOME, timeout=20)
    except Exception:
        pass
    response = session.get(base.INDEX_URL, timeout=30)
    response.raise_for_status()
    return extract_report_urls(response.text, max_reports=max_reports)


# Patch only the discovery stage. Workbook parsing and record merging remain v1.
base.discover_report_urls = discover_report_urls

DATA_FILE = base.DATA_FILE
INDEX_URL = base.INDEX_URL
read_xlsx_rows = base.read_xlsx_rows
parse_report_rows = base.parse_report_rows
download_report = base.download_report
best_report_row = base.best_report_row
merge_report_row = base.merge_report_row
is_candidate = base.is_candidate
excel_date = base.excel_date


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
