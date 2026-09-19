#!/usr/bin/env python3
"""Quality-gated entry point for the IPO updater.

This wrapper keeps the live collector conservative without duplicating its core
logic. It cleans preview-era data, normalizes legacy/current NSE field aliases,
preserves richer enrichment fields across core refreshes, and replaces the broad
BSE HTML parser with an IPO-only parser before running update_data.main().
"""
from __future__ import annotations

import copy
import json
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
    """Remove stale BSE validation snapshots and preview-only values before merge."""
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

    # Reviewed universe identity is durable evidence, not a disposable current
    # page comparison. Bind preservation to its admitted source URL.
    admission = rec.get("universeAdmission") or {}
    identity_url = (admission.get("identitySource") or {}).get("url")
    # Remove prior BSE validation/detail observations because those official pages
    # are re-fetched after every core run. Keep BSE cumulative-demand provenance,
    # which belongs to the independent live-subscription collector.
    non_bse_sources = [
        s
        for s in sources
        if not (
            _source_root(s) == "BSE"
            and "cumulative demand" not in _source_name(s).lower()
            and not (identity_url and s.get("url") == identity_url)
        )
    ]
    observations = dict(rec.get("observations") or {})
    if not (identity_url and (observations.get("BSE") or {}).get("sourceUrl") == identity_url):
        observations.pop("BSE", None)
    rec["observations"] = observations

    # A validation-only BSE row is dropped and refetched. A subscription record is
    # not validation-only, so cumulative-demand provenance is intentionally kept.
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


# NSE has changed field names across the live/upcoming/past endpoints. The core
# normalizer accepts the canonical live names; copy known official aliases into
# those canonical keys first so historical data is not silently discarded.
_original_normalize_nse_record = core.normalize_nse_record


def normalize_nse_record(record, kind):
    row = dict(record or {})
    aliases = {
        "symbol": ("smSymbol",),
        "issueStartDate": ("ipoStartDate", "startDate"),
        "issueEndDate": ("ipoEndDate", "endDate"),
        "lotSize": ("bidLot", "marketLot"),
        "listingDate": ("dateOfListing",),
    }
    for canonical, alternatives in aliases.items():
        if row.get(canonical) not in (None, "", "-", "--"):
            continue
        for alias in alternatives:
            value = row.get(alias)
            if value not in (None, "", "-", "--"):
                row[canonical] = value
                break

    # Some NSE past-issue responses label the security code under series or
    # securityType. We do not use it as the symbol, but retaining it in the row
    # lets the core board classifier correctly identify SME/Emerge records.
    return _original_normalize_nse_record(row, kind)


core.normalize_nse_record = normalize_nse_record


# Generic issue-feed multiples remain in source-bound observations. The detail
# collector owns the complete accepted subscription family, including its history.
# Protect absence as well as existing fields; an incoming-only clock cannot create
# a new attribution. Keep this compatibility entrypoint for existing callers.
_original_merge_non_null = core.merge_non_null


def merge_non_null_preserving_nested(base, incoming):
    out = _original_merge_non_null(base, incoming)
    for key in set(base) | set(incoming):
        if key.startswith("subscription"):
            if key in base:
                out[key] = copy.deepcopy(base[key])
            else:
                out.pop(key, None)
    return out


core.merge_non_null = merge_non_null_preserving_nested
merge_non_null = merge_non_null_preserving_nested


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


def _preserve_enrichment_meta(previous_meta):
    """Never downgrade schema or erase health from independent enrichment jobs."""
    try:
        payload = json.loads(core.DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return

    meta = payload.setdefault("meta", {})
    old_schema = int((previous_meta or {}).get("schemaVersion") or 1)
    new_schema = int(meta.get("schemaVersion") or 1)
    meta["schemaVersion"] = max(old_schema, new_schema)

    old_health = dict((previous_meta or {}).get("sourceHealth") or {})
    old_health.update(meta.get("sourceHealth") or {})
    meta["sourceHealth"] = old_health

    for key in ("offerDocumentHealth", "subscriptionHealth"):
        if key not in meta and (previous_meta or {}).get(key) is not None:
            meta[key] = previous_meta[key]

    old_history_start = (previous_meta or {}).get("historyStart")
    new_history_start = meta.get("historyStart")
    if old_history_start and new_history_start:
        meta["historyStart"] = min(str(old_history_start), str(new_history_start))
    elif old_history_start and not new_history_start:
        meta["historyStart"] = old_history_start

    core.DATA_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main():
    previous = _original_load_existing()
    result = core.main()
    if result == 0:
        _preserve_enrichment_meta(previous.get("meta") or {})
    return result


if __name__ == "__main__":
    raise SystemExit(main())
