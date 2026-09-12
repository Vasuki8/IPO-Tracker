#!/usr/bin/env python3
"""Phase 4.5B priority-subscription runner v2.

BSE currently serves IPO cumulative demand through more than one official route.
The public site is being migrated from the legacy ``CummDemandSchedule.aspx``
page to an extensionless route, and the status query can behave differently for
live, forthcoming and historical SME issues. Keep a bounded set of official BSE
variants so the collector can recover without relying on third-party data.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import priority_subscriptions as base  # noqa: E402

_original_alternates = base._alternate_bse_hosts


def _demand_id(url: str) -> str | None:
    parsed = urlparse(url)
    query = {str(key).lower(): values for key, values in parse_qs(parsed.query).items()}
    values = query.get("id") or []
    if not values:
        return None
    value = "".join(ch for ch in str(values[0]) if ch.isdigit())
    return value or None


def official_demand_route_variants(url: str) -> list[str]:
    """Return conservative variants of one official BSE cumulative-demand URL.

    We never change the issue ID or leave BSE-controlled hosts. The variants only
    cover BSE's two public hosts, legacy/current route spellings and the status
    forms observed across mainboard/SME pages.
    """
    parsed = urlparse(url)
    if "cummdemandschedule" not in parsed.path.lower():
        return _original_alternates(url)

    issue_id = _demand_id(url)
    if not issue_id:
        return _original_alternates(url)

    out: list[str] = []

    # Keep the exact discovered URL first. DisplayIPO sometimes provides a route
    # that is more specific than the one we can construct from IPONo.
    out.append(url)

    for host in ("www.bseindia.com", "beta.bseindia.com"):
        # Legacy ASP.NET page. Try live first, then no-status and the two other
        # official status modes because SME rows can lag the public index state.
        for status in ("L", None, "F", "H"):
            params = {"ID": issue_id}
            if status:
                params["status"] = status
            legacy = parsed._replace(
                netloc=host,
                path="/markets/publicIssues/CummDemandSchedule.aspx",
                query=urlencode(params),
            )
            out.append(urlunparse(legacy))

        # Current BSE route. Keep both the live and status-free forms; the latter
        # is useful when the Angular shell ignores the legacy status parameter.
        for status in ("L", None):
            params = {"ID": issue_id}
            if status:
                params["status"] = status
            current = parsed._replace(
                netloc=host,
                path="/markets/publicissues/cummdemandschedule",
                query=urlencode(params),
            )
            out.append(urlunparse(current))

    # Preserve any normal same-path host variants supplied by the base collector.
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
