#!/usr/bin/env python3
"""Priority live-subscription runner with a transparent tertiary fallback.

Source order is deliberately strict:
1. NSE ipo-detail (official)
2. BSE cumulative demand / SME public-issue pages (official)
3. Groww's public IPO subscription table (secondary)

The third source exists only because NSE blocks GitHub-hosted runners and BSE's
2026 public-site migration currently returns an empty legacy cumulative-demand
table for several live SME IPOs. Secondary observations are explicitly labelled
and never presented as exchange-originated data.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
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
SECONDARY_SOURCE_NAME = "Groww IPO subscription (secondary)"


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


def parse_groww_subscription_html(html: str) -> list[dict[str, Any]]:
    """Parse the public Groww IPO subscription table without positional guessing.

    A row is accepted only when a table exposes explicit Company, QIB, NII,
    Retail and Total headers. This intentionally fails closed if Groww changes
    the page structure instead of silently mapping the wrong columns.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for table in soup.find_all("table"):
        header_row = None
        header_cells: list[str] = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"], recursive=False)
            texts = [" ".join(cell.stripped_strings).strip() for cell in cells]
            normalized = [_norm_header(text) for text in texts]
            if any(h in {"company", "companyname"} for h in normalized) and "qib" in normalized and "nii" in normalized and "retail" in normalized and "total" in normalized:
                header_row = tr
                header_cells = normalized
                break
        if header_row is None:
            continue

        def idx(*aliases: str) -> int | None:
            wanted = {_norm_header(alias) for alias in aliases}
            for index, value in enumerate(header_cells):
                if value in wanted:
                    return index
            return None

        company_i = idx("Company", "Company Name")
        qib_i = idx("QIB")
        nii_i = idx("NII", "NII/HNI")
        retail_i = idx("Retail", "RII")
        total_i = idx("Total")
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
            company = texts[int(company_i)].strip()
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


class GrowwSubscriptionClient:
    """Last-resort, explicitly secondary live-subscription source."""

    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(core.HEADERS)
        self.s.headers.update({"Referer": "https://groww.in/ipo"})
        self._rows: list[dict[str, Any]] | None = None
        self._error: Exception | None = None

    def _load(self):
        if self._rows is not None:
            return
        if self._error is not None:
            raise self._error
        try:
            response = self.s.get(GROWW_SUBSCRIPTION_URL, timeout=30)
            response.raise_for_status()
            rows = parse_groww_subscription_html(response.text)
            if not rows:
                raise ValueError("Groww subscription page contained no parseable table rows")
            self._rows = rows
            print(f"Secondary Groww subscription table: {len(rows)} parseable issues")
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
            return row["subscription"], GROWW_SUBSCRIPTION_URL

        contained = [
            row for row in self._rows or []
            if needle in row["key"] or row["key"] in needle
        ]
        if contained:
            row = max(contained, key=lambda item: len(item["key"]))
            return row["subscription"], GROWW_SUBSCRIPTION_URL

        scored = sorted(
            (
                (SequenceMatcher(None, needle, row["key"]).ratio(), row)
                for row in self._rows or []
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        if not scored or scored[0][0] < 0.72:
            raise ValueError(f"Groww subscription row not found for {company}")
        return scored[0][1]["subscription"], GROWW_SUBSCRIPTION_URL


def _mark_secondary_provenance(record: dict[str, Any]) -> None:
    """Correct the generic apply_subscription stamp to explicit secondary data."""
    for source in record.get("sources") or []:
        if str((source or {}).get("name") or "") == SECONDARY_SOURCE_NAME:
            source["kind"] = "secondary-market-data"


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

    secondary = GrowwSubscriptionClient()
    attempted = updated = snapshots_added = failed = 0
    nse_records = bse_records = secondary_records = 0
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
                    parsed, source_url = secondary.detail(company)
                    added = sub.apply_subscription(
                        record,
                        parsed,
                        source_name=SECONDARY_SOURCE_NAME,
                        source_url=source_url,
                        snapshot_source=SECONDARY_SOURCE_NAME,
                        force_snapshot=args.force_snapshot,
                    )
                    _mark_secondary_provenance(record)
                    source_used = "Groww secondary"
                    secondary_records += 1
                    warnings.append(
                        f"{company}: official live feeds unavailable "
                        f"(NSE: {str(nse_exc)[:140]}; BSE: {str(bse_exc)[:220]}); "
                        "used explicitly labelled Groww secondary subscription table"
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
        "asOf": as_of,
        "errors": errors[:5],
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Priority subscriptions v3: "
        f"attempted={attempted} updated={updated} snapshots_added={snapshots_added} "
        f"failed={failed} nse={nse_records} bse={bse_records} secondary={secondary_records}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
