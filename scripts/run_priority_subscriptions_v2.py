#!/usr/bin/env python3
"""Phase 4.5B priority-subscription runner v2.

BSE's current public site exposes cumulative demand through an extensionless
route while the legacy/SME pages still link to CummDemandSchedule.aspx. Keep
both official forms so the collector works across the migration without using
third-party subscription data.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import priority_subscriptions as base  # noqa: E402

_original_alternates = base._alternate_bse_hosts


def official_demand_route_variants(url: str) -> list[str]:
    parsed = urlparse(url)
    out: list[str] = []

    # Current BSE route seen on the live site in 2026. Try this before the
    # legacy ASPX route because www.bseindia.com may render the latter as a
    # generic shell while beta serves an empty legacy table.
    if "cummdemandschedule" in parsed.path.lower():
        for host in ("www.bseindia.com", "beta.bseindia.com"):
            canonical = parsed._replace(
                netloc=host,
                path="/markets/publicissues/cummdemandschedule",
            )
            out.append(urlunparse(canonical))

    out.extend(_original_alternates(url))
    return list(dict.fromkeys(out))


base._alternate_bse_hosts = official_demand_route_variants

IssueLink = base.IssueLink
demand_candidates = base.demand_candidates
fetch_demand = base.fetch_demand
priority_open_targets = base.priority_open_targets


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
