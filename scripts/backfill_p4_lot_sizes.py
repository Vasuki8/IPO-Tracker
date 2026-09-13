#!/usr/bin/env python3
"""Progressively recover recent P4 IPO lot sizes from official BSE details.

The full-history BSE sweep and the recent P4 lot-size sweep must not share a
cooldown marker. Historical archival work may already have considered a record
for other exchange-core gaps; that must not suppress a dedicated recent lot-size
attempt. This wrapper reuses the conservative BSE archive, matching and v2 detail
parser while giving P4 its own attempt key and targeting lotSize only in
core-only mode.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_exchange_details_v2 as detail_v2  # noqa: E402
import backfill_bse_history as base  # noqa: E402

P4_ATTEMPT_KEY = "p4LotSizeBackfill"
_ORIGINAL_MISSING_DETAIL_FIELDS = base.missing_detail_fields


def missing_detail_fields(record: dict[str, Any], *, core_only: bool) -> list[str]:
    """Make the dedicated P4 core-only sweep consume only lot-size gaps."""
    if core_only:
        return ["lotSize"] if record.get("lotSize") in (None, "", [], {}) else []
    return _ORIGINAL_MISSING_DETAIL_FIELDS(record, core_only=core_only)


# Reuse the proven BSE archive/matching/network logic with parser v2, but isolate
# P4 retry state from the Phase 4.5D full-history archival sweep.
base.detail.parse_detail_html = detail_v2.parse_detail_html
base.ATTEMPT_KEY = P4_ATTEMPT_KEY
base.missing_detail_fields = missing_detail_fields

DATA_FILE = base.DATA_FILE
is_candidate = base.is_candidate
attempted_recently = base.attempted_recently
mark_attempt = base.mark_attempt


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
