#!/usr/bin/env python3
"""Quality-gated entry point for the IPO updater.

This wrapper keeps the live collector conservative without duplicating its core
logic. It cleans preview-era data before merge and replaces the broad BSE HTML
parser with an IPO-only parser before running update_data.main().
"""
from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402

# Re-export helpers used by the regression tests.
canonical_company = core.canonical_company
parse_period = core.parse_period
parse_price_band_text = core.parse_price_band_text
field_equal = core.field_equal
nse_issue_metrics = core.nse_issue_metrics
merge_fill_only = core.merge_fill_only
build_validation = core.build_validation

LEGACY_SOURCE_MARKERS = (
    "seed snapshot",
    "reported by reuters",
)

PREVIEW_DERIVED_FIELDS = (
    "symbol",
    "exchange",
    "openDate",
    "closeDate",
    "allotmentDate",
    "listingDate",
    "priceBand",
    "lotSize",
    "issueSizeCr",
    "freshIssueCr",
    "ofsCr",
    "sharesOffered",
    "sharesBid",
    "subscription",
    "listing",
)


def _source_name(source):
    return str((source or {}).get("name") or "").strip()


def _is_legacy_source(source):
    name = _source_name(source).lower()
    return any(marker in name for marker in LEGACY_SOURCE_MARKERS)


def _source_root(source):
    name = _source_name(source)
    return name.split()[0].upper() if name else ""


def clean_existing_record(record):
    """Remove stale BSE snapshots and preview-only values before a live merge.

    BSE is intentionally re-fetched each run because this project currently
    uses BSE as a *current-issue validation layer*, not as a historical store.
    Preview seed values are also cleared so only fields re-observed from an
    official source survive.
    """
    if not isinstance(record, dict):
        return None

    rec = dict(record)
    company = str(rec.get("company") or "")
    if len(company) > 250 or company.lower().startswith(
        "security name exchange platform"
    ):
        return None

    sources = list(rec.get("sources") or [])
    if not sources and rec.get("source"):
        sources = [rec["source"]]

    # Remove the prior run's BSE validation. The strict IPO-only parser will
    # attach a fresh BSE observation later in this run.
    non_bse_sources = [s for s in sources if _source_root(s) != "BSE"]
    observations = dict(rec.get("observations") or {})
    observations.pop("BSE", None)
    rec["observations"] = observations

    # A BSE-only row came from the validation page. Drop it now; genuine IPO
    # rows will be re-added by the strict parser, while FPO/RI/debt/buyback rows
    # will disappear instead of accumulating in the database.
    if sources and not non_bse_sources:
        return None

    sources = non_bse_sources
    had_legacy = any(_is_legacy_source(s) for s in sources) or _is_legacy_source(
        rec.get("source")
    )

    if had_legacy:
        for field in PREVIEW_DERIVED_FIELDS:
            rec[field] = None
        sources = [s for s in sources if not _is_legacy_source(s)]

    rec["sources"] = sources
    if sources:
        rec["source"] = sources[0]
    else:
        rec.pop("source", None)
    return rec


def parse_bse_ipo_html(html, source_url=core.BSE_URL):
    """Parse only equity IPO rows from BSE's mixed public-issues table."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    for tr in soup.find_all("tr"):
        # recursive=False is important: BSE wraps its actual table inside outer
        # layout rows. Recursive selection previously collapsed the entire page
        # into one giant fake company record.
        nodes = tr.find_all(["th", "td"], recursive=False)
        cells = [" ".join(node.stripped_strings).strip() for node in nodes]
        if len(cells) < 8:
            continue

        company = cells[0].strip()
        platform = cells[1].strip()
        start_text = cells[2].strip()
        end_text = cells[3].strip()
        offer_price = cells[4].strip()
        issue_type = cells[6].strip().upper()
        issue_status = cells[7].strip()

        if not company or company.lower() in {"security name", "security", "issuer"}:
            continue
        if issue_type != "IPO":
            continue

        od = core.iso_date(start_text)
        cd = core.iso_date(end_text)
        if not od or not cd:
            continue

        board = "SME" if "SME" in platform.upper() else "Mainboard"
        band = core.parse_price_band_text(offer_price)
        src = core.source_stamp("BSE public issue", source_url, "exchange")

        rows.append(
            {
                "id": core.slugify(company),
                "matchKey": core.canonical_company(company),
                "company": company,
                "board": board,
                "exchange": "BSE SME" if board == "SME" else "BSE",
                "status": core.derive_status(od, cd, None, issue_status),
                "openDate": od,
                "closeDate": cd,
                "priceBand": band,
                "lotSize": None,
                "issueSizeCr": None,
                "issueType": "IPO",
                "sources": [src],
                "source": src,
                "observations": {
                    "BSE": {
                        "openDate": od,
                        "closeDate": cd,
                        "priceBand": band,
                        "lotSize": None,
                        "issueSizeCr": None,
                        "issueType": "IPO",
                    }
                },
            }
        )

    return core.dedupe_dicts(rows, ("matchKey", "openDate", "closeDate"))


# Apply the stricter BSE parser globally before core.main() constructs clients.
core.BSEClient.parse_html = staticmethod(parse_bse_ipo_html)
BSEClient = core.BSEClient

_original_load_existing = core.load_existing


def load_existing_cleaned():
    payload = _original_load_existing()
    cleaned = []
    for record in payload.get("ipos", []):
        item = clean_existing_record(record)
        if item is not None:
            cleaned.append(item)
    payload["ipos"] = cleaned
    return payload


core.load_existing = load_existing_cleaned


def main():
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())
