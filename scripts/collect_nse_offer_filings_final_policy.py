#!/usr/bin/env python3
"""NSE offer-filings collector under the Final Prospectus source policy.

The underlying NSE register remains valuable for discovering Final Prospectus
PDFs and for post-offer listing dates. Static XBRL terms such as Market Lot and
Final Issue Price are retained only as observations; they never populate the
canonical IPO fields.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import collect_nse_offer_filings as base  # noqa: E402


def merge_dynamic_only(record, entry, cells, url, digest):
    if not base.archive_url(url, ".xml") or not base.verified_terms(record, entry, cells):
        return []

    evidence = {
        "source": "NSE final-listing XBRL",
        "sourceUrl": url,
        "registerUrl": base.PAGE,
        "sha256": digest,
        "company": entry["company"],
        "symbol": cells.get("ScripID"),
        "isin": cells.get("ISIN"),
        "issueOpenDate": base.source_date(cells["DateOfIssueOpen"]),
        "issueCloseDate": base.source_date(cells["DateOfIssueClose"]),
        "sourcePolicy": "dynamic-observation-only",
    }

    changed = []
    listed = base.source_date(cells.get("DateOfListing"))
    if listed and not record.get("listingDate"):
        record["listingDate"] = listed
        record["listingDateEvidence"] = {
            **evidence,
            "field": "DateOfListing",
            "value": listed,
            "checkedAt": base.stamp(),
        }
        changed.append("listingDate")

    # Preserve the official static terms only as an independent observation.
    # The Final Prospectus parser is the sole canonical source for these fields.
    record.setdefault("observations", {})["NSEFinalListing"] = {
        **evidence,
        "fields": cells,
        "canonicalStaticFieldsWritten": [],
    }
    if not any(source.get("url") == url for source in record.get("sources", [])):
        record.setdefault("sources", []).append(
            base.core.source_stamp("NSE final-listing XBRL", url, "exchange")
        )
    record["validation"] = base.core.build_validation(record)
    return changed


base.merge_terms = merge_dynamic_only


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
