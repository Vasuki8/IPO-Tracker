#!/usr/bin/env python3
"""Core market updater with Final-Prospectus-only canonical static fields.

NSE/BSE remain authoritative discovery/lifecycle sources. Their static offer
terms are retained as observations for cross-checking, but are stripped from
canonical fields before merge. Final Prospectus extraction owns those fields.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import final_prospectus_policy as policy  # noqa: E402
import run_update_v2 as base  # noqa: E402

core = base.core
_TOP_LEVEL_STATIC = {
    field for field in policy.STATIC_CANONICAL_FIELDS if "." not in field
}
_ORIGINAL_NORMALIZE_NSE = core.normalize_nse_record
_ORIGINAL_MERGE_FILL_ONLY = core.merge_fill_only
_ORIGINAL_BSE_CURRENT = core.BSEClient.current_issues


def _observation_bucket(record: dict[str, Any]) -> dict[str, Any]:
    observations = record.setdefault("observations", {})
    exchange = str(record.get("exchange") or "").upper()
    key = "BSE" if "BSE" in exchange else "NSE"
    return observations.setdefault(key, {})


def strip_static_canonical(record: dict[str, Any]) -> dict[str, Any]:
    """Move source-supplied static values to observations, not canonical fields."""
    observation = _observation_bucket(record)
    observed_static = observation.setdefault("staticOfferTerms", {})
    for field in _TOP_LEVEL_STATIC:
        value = record.get(field)
        if value in (None, "", [], {}):
            continue
        observed_static[field] = copy.deepcopy(value)
        record[field] = None
    record.setdefault("staticSourcePolicy", {}).update(
        {
            "policy": "final-prospectus-only",
            "marketStaticTerms": "observation-only",
        }
    )
    return record


def normalize_nse_record(row, kind):
    return strip_static_canonical(_ORIGINAL_NORMALIZE_NSE(row, kind))


def merge_fill_only(existing, incoming, protected=set()):
    # Exchange/BSE merge helpers may still carry static keys. Protect them even
    # if the canonical record is currently blank and awaiting a Final Prospectus.
    return _ORIGINAL_MERGE_FILL_ONLY(
        existing,
        incoming,
        set(protected) | _TOP_LEVEL_STATIC,
    )


def current_issues_observation_only(self):
    rows = _ORIGINAL_BSE_CURRENT(self)
    return [strip_static_canonical(row) for row in rows]


core.normalize_nse_record = normalize_nse_record
core.merge_fill_only = merge_fill_only
core.BSEClient.current_issues = current_issues_observation_only


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
