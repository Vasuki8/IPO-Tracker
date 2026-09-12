#!/usr/bin/env python3
"""Priority live-subscription runner with transparent secondary fallbacks.

Source order is deliberately strict:
1. NSE ipo-detail (official)
2. BSE cumulative demand / SME public-issue pages (official)
3. Groww's public IPO subscription table (secondary)
4. IPO Dhamaka's public subscription table (secondary)

Secondary sources exist only because NSE blocks GitHub-hosted runners and BSE's
2026 public-site migration currently returns an empty legacy cumulative-demand
table for several live SME IPOs. Secondary observations are explicitly labelled
and never presented as exchange-originated data.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_priority_subscriptions_v2 as official  # noqa: E402

base = official.base
sub = base.sub
core = base.core

DATA_FILE = core.DATA_FILE
QUEUE_FILE = base.QUEUE_FILE
GROWW_SUBSCRIPTION_URL = "https://groww.in/ipo/subscription"
IPODHAMAKA_SUBSCRIPTION_URL = "https://ipodhamaka.in/subscription/"
GROWW_SOURCE_NAME = "Groww IPO subscription (secondary)"
IPODHAMAKA_SOURCE_NAME = "IPO Dhamaka subscription (secondary)"
# Backwards-compatible alias used by older tests/data helpers.
SECONDARY_SOURCE_NAME = GROWW_SOURCE_NAME


def _norm_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _multiple(value: str | None) -> float | None:
    text = str(value or "").strip()
    if text in {"", "-", "--", "—", "NA", "N/A"}:
        return None
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*[x×]?", text.replace(",", ""), flags=re.I)
    if not match:
        return None
    number = float(match.group(1))
    return number if number >= 0 else None


def _clean_secondary_company_name(value: str) -> str:
    """Remove exchange/board badges that some tables append to company names."""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(
        r"(?:NSE\s*/\s*BSE|BSE\s*/\s*SME|NSE\s*/\s*SME|BSE\s+SME|NSE\s+SME)\s*$",
        "",
        text,
        flags=re.I,
    ).strip()
    return text


def _parse_named_subscription_table(
    html: str,
    *,
    company_aliases: tuple[str, ...],
    qib_aliases: tuple[str, ...],
    nii_aliases: tuple[str, ...],
    retail_aliases: tuple[str, ...],
    total_aliases: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Parse a table only when all category columns are explicitly named.

    This deliberately fails closed if a provider changes its markup. We never
    infer category positions from column order.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    alias_groups = {
        "company": {_norm_header(x) for x in company_aliases},
        "qib": {_norm_header(x) for x in qib_aliases},
        "nii": {_norm_header(x) for x in nii_aliases},
        "retail": {_norm_header(x) for x in retail_aliases},
        "total": {_norm_header(x) for x in total_aliases},
    }

    for table in soup.find_all("table"):
        header_row = None
        header_cells: list[str] = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"], recursive=False)
            texts = [" ".join(cell.stripped_strings).strip() for cell in cells]
            normalized = [_norm_header(text) for text in texts]
            if all(any(cell in aliases for cell in normalized) for aliases in alias_groups.values()):
                header_row = tr
                header_cells = normalized
                break
        if header_row is None:
            continue

        def idx(group: str) -> int | None:
            wanted = alias_groups[group]
            for index, value in enumerate(header_cells):
                if value in wanted:
                    return index
            return None

        company_i = idx("company")
        qib_i = idx("qib")
        nii_i = idx("nii")
        retail_i = idx("retail")
        total_i = idx("total")
        required = (company_i, qib_i, nii_i, retail_i, total_i)
        if any(value is None for value in required):
            continue

        for tr in header_row.find_all_next("tr"):
            if tr.find_parent("table") is not table:
                break
            cells = tr.find_all(["th", "td"], recursive=False)
            texts = [" ".join(cell.stripped_strings).strip() for cell in cells]
            max_index = max(int(value) for value in required if value is not None)
            if len(texts) <= max_index:
                continue
            company = _clean_secondary_company_name(texts[int(company_i)])
            key = core.canonical_company(company)
            if not key or key in seen:
                continue
            parsed = {
                "qib": _multiple(texts[int(qib_i)]),
                "nii": _multiple(texts[int(nii_i)]),
                "retail": _multiple(texts[int(retail_i)]),
                "total": _multiple(texts[int(total_i)]),
            }
            if not any(value is not None for value in parsed.values()):
                continue
            seen.add(key)
            rows.append({"company": company, "key": key, "subscription": parsed})

    return rows


def parse_groww_subscription_html(html: str) -> list[dict[str, Any]]:
    """Parse Groww by explicit Company/QIB/NII/Retail/Total headers."""
    return _parse_named_subscription_table(
        html,
        company_aliases=("Company", "Company Name"),
        qib_aliases=("QIB",),
        nii_aliases=("NII", "NII/HNI"),
        retail_aliases=("Retail", "RII"),
        total_aliases=("Total",),
    )


def parse_ipodhamaka_subscription_html(html: str) -> list[dict[str, Any]]:
    """Parse IPO Dhamaka's aggregate live table by named columns.

    The page includes sHNI and bHNI columns as well; they are intentionally
    ignored because the explicit NII column is the aggregate we need.
    """
    return _parse_named_subscription_table(
        html,
        company_aliases=("IPO", "Company", "Company Name"),
        qib_aliases=("QIB", "QIB (X)"),
        nii_aliases=("NII", "NII (X)", "NII/HNI"),
        retail_aliases=("Retail", "Retail (X)", "RII"),
        total_aliases=("Total", "Total (X)"),
    )


class _TableSubscriptionClient:
    source_url = ""
    source_name = ""

    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(core.HEADERS)
        self._rows: list[dict[str, Any]] | None = None
        self._error: Exception | None = None

    def parse(self, html: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _load(self):
        if self._rows is not None:
            return
        if self._error is not None:
            raise self._error
        try:
            response = self.s.get(self.source_url, timeout=30)
            response.raise_for_status()
            rows = self.parse(response.text)
            if not rows:
                raise ValueError(f"{self.source_name} page contained no parseable table rows")
            self._rows = rows
            print(f"{self.source_name}: {len(rows)} parseable issues")
        except Exception as exc:
            self._error = exc
            raise

    def detail(self, company: str):
        self._load()
        needle = core.canonical_company(company)
        if not needle:
            raise ValueError(f"Cannot match empty company name: {company!r}")

        exact = [row for row in self._rows or [] if row["key"] == needle]
        if exact:
            row = exact[0]
            return row["subscription"], self.source_url

        contained = [
            row for row in self._rows or []
            if needle in row["key"] or row["key"] in needle
        ]
        if contained:
            row = max(contained, key=lambda item: len(item["key"]))
            return row["subscription"], self.source_url

        scored = sorted(
            (
                (SequenceMatcher(None, needle, row["key"]).ratio(), row)
                for row in self._rows or []
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        if not scored or scored[0][0] < 0.72:
            raise ValueError(f"{self.source_name} row not found for {company}")
        return scored[0][1]["subscription"], self.source_url


class GrowwSubscriptionClient(_TableSubscriptionClient):
    """Last-resort, explicitly secondary live-subscription source."""

    source_url = GROWW_SUBSCRIPTION_URL
    source_name = GROWW_SOURCE_NAME

    def __init__(self):
        super().__init__()
        self.s.headers.update({"Referer": "https://groww.in/ipo"})

    def parse(self, html: str) -> list[dict[str, Any]]:
        return parse_groww_subscription_html(html)


class IPODhamakaSubscriptionClient(_TableSubscriptionClient):
    """Static named-column fallback used only after official feeds and Groww."""

    source_url = IPODHAMAKA_SUBSCRIPTION_URL
    source_name = IPODHAMAKA_SOURCE_NAME

    def __init__(self):
        super().__init__()
        self.s.headers.update({"Referer": "https://ipodhamaka.in/"})

    def parse(self, html: str) -> list[dict[str, Any]]:
        return parse_ipodhamaka_subscription_html(html)


def _mark_secondary_provenance(record: dict[str, Any], source_name: str = SECONDARY_SOURCE_NAME) -> None:
    """Correct the generic apply_subscription stamp to explicit secondary data."""
    for source in record.get("sources") or []:
        if str((source or {}).get("name") or "") == source_name:
            source["kind"] = "secondary-market-data"


def _secondary_detail(clients: list[_TableSubscriptionClient], company: str):
    errors = []
    for client in clients:
        try:
            parsed, url = client.detail(company)
            return parsed, url, client.source_name
        except Exception as exc:
            errors.append(f"{client.source_name}: {exc}")
    raise ValueError("; ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--force-snapshot", action="store_true")
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    queue_payload = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    targets = base.priority_open_targets(payload, queue_payload, args.limit)

    nse = sub.NSESubscriptionClient()
    bse_session = requests.Session()
    bse_session.headers.update(core.HEADERS)
    try:
        index, page_health = base.build_issue_index(bse_session)
        print(
            f"Priority BSE issue index: {len(index)} links across "
            f"{sum(1 for value in page_health.values() if value.get('ok'))} healthy pages"
        )
    except Exception as exc:
        index, page_health = [], {"error": str(exc)}

    secondary_clients: list[_TableSubscriptionClient] = [
        GrowwSubscriptionClient(),
        IPODhamakaSubscriptionClient(),
    ]
    attempted = updated = snapshots_added = failed = 0
    nse_records = bse_records = secondary_records = 0
    secondary_source_counts: Counter[str] = Counter()
    errors: list[str] = []
    warnings: list[str] = []

    for record in targets:
        attempted += 1
        company = str(record.get("company") or "")
        try:
            try:
                detail, series = nse.detail(str(record.get("symbol") or "").strip(), record.get("board"))
                added = sub.update_record(record, detail, series=series, force_snapshot=args.force_snapshot)
                source_used = "NSE"
                nse_records += 1
            except Exception as nse_exc:
                try:
                    matches = base.best_issue_links(index, company)
                    if not matches:
                        raise ValueError("no matching BSE public-issue link")
                    parsed, source_url, diagnostics = base.fetch_demand(bse_session, matches)
                    added = sub.apply_subscription(
                        record,
                        parsed,
                        source_name="BSE cumulative demand",
                        source_url=source_url,
                        snapshot_source="BSE cumulative demand",
                        force_snapshot=args.force_snapshot,
                    )
                    source_used = "BSE"
                    bse_records += 1
                    if diagnostics:
                        warnings.append(f"{company}: " + " | ".join(diagnostics[-2:]))
                except Exception as bse_exc:
                    parsed, source_url, secondary_source_name = _secondary_detail(secondary_clients, company)
                    added = sub.apply_subscription(
                        record,
                        parsed,
                        source_name=secondary_source_name,
                        source_url=source_url,
                        snapshot_source=secondary_source_name,
                        force_snapshot=args.force_snapshot,
                    )
                    _mark_secondary_provenance(record, secondary_source_name)
                    source_used = secondary_source_name.replace(" subscription (secondary)", " secondary")
                    secondary_records += 1
                    secondary_source_counts[secondary_source_name] += 1
                    warnings.append(
                        f"{company}: official live feeds unavailable "
                        f"(NSE: {str(nse_exc)[:140]}; BSE: {str(bse_exc)[:220]}); "
                        f"used explicitly labelled {secondary_source_name}"
                    )

            updated += 1
            snapshots_added += int(bool(added))
            current = record.get("subscription") or {}
            print(
                f"Priority subscription {company} [{source_used}]: "
                f"QIB={current.get('qib')} NII={current.get('nii')} "
                f"Retail={current.get('retail')} Total={current.get('total')}"
            )
        except Exception as exc:
            failed += 1
            message = f"{company}: {exc}"
            errors.append(message)
            print(f"Priority subscription failed: {message}", file=sys.stderr)

    as_of = core.now_ist().isoformat(timespec="seconds")
    health = {
        "ok": failed == 0 if attempted else True,
        "degraded": secondary_records > 0,
        "attempted": attempted,
        "updated": updated,
        "snapshotsAdded": snapshots_added,
        "failed": failed,
        "nseRecords": nse_records,
        "bseFallbackRecords": bse_records,
        "secondaryFallbackRecords": secondary_records,
        "secondarySources": dict(secondary_source_counts),
        "asOf": as_of,
        "pageHealth": page_health,
        "warnings": warnings[:10],
        "errors": errors[:10],
    }
    meta = payload.setdefault("meta", {})
    meta["schemaVersion"] = max(int(meta.get("schemaVersion") or 1), 4)
    meta["subscriptionHealth"] = health
    meta.setdefault("sourceHealth", {})["IPO-subscription"] = {
        "ok": health["ok"],
        "degraded": health["degraded"],
        "records": updated,
        "attempted": attempted,
        "snapshotsAdded": snapshots_added,
        "failed": failed,
        "nseRecords": nse_records,
        "bseFallbackRecords": bse_records,
        "secondaryFallbackRecords": secondary_records,
        "secondarySources": dict(secondary_source_counts),
        "asOf": as_of,
        "errors": errors[:5],
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Priority subscriptions v3: "
        f"attempted={attempted} updated={updated} snapshots_added={snapshots_added} "
        f"failed={failed} nse={nse_records} bse={bse_records} secondary={secondary_records} "
        f"secondary_sources={dict(secondary_source_counts)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
