#!/usr/bin/env python3
"""Capture timestamped category-wise IPO subscription snapshots.

NSE ``/api/ipo-detail`` is the preferred source for QIB / NII / Retail / Total
multiples. NSE's Akamai layer can block cloud/datacenter runners even when the
public current-issue endpoints remain usable, so the collector transparently
falls back to BSE's official Cumulative Demand Schedule for the same live issue.
Changed observations are retained instead of overwriting previous values.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import update_data as core  # noqa: E402

DATA_FILE = core.DATA_FILE
NSE_HOME = core.NSE_HOME
NSE_API = core.NSE_API
NSE_DETAIL_PAGE = f"{NSE_HOME}/market-data/issue-information"
SNAPSHOT_KEYS = ("qib", "nii", "retail", "total")
MAX_HISTORY = 500


def _first(d: dict[str, Any], *keys, default=None):
    for key in keys:
        value = d.get(key)
        if value not in (None, "", "-", "--", "NA", "N/A"):
            return value
    return default


def _category_text(row: dict[str, Any]) -> str:
    parts = [
        _first(row, "category", "categoryName", "investorCategory", "bidCategory"),
        _first(row, "categoryCode", "code", "caCode"),
    ]
    return " ".join(str(x).strip() for x in parts if x not in (None, "")).lower()


def _classify_category(text: str):
    """Return (field, score) for a headline subscription category row.

    Both exchanges can expose NII amount sub-buckets. We intentionally keep the
    aggregate NII row rather than substituting one of those sub-buckets.
    """
    t = " ".join(text.lower().replace("-", " ").replace("_", " ").split())
    words = set(t.split())

    if "total" in words or t in {"overall", "grand total"}:
        return "total", 120
    if "qualified institutional" in t or "qib" in words or "qibs" in words:
        return "qib", 110
    if "retail" in t or "rii" in words or "riis" in words:
        return "retail", 110
    if "individual investor" in t and "non institutional" not in t:
        # NSE's newer SME terminology uses Individual Investor instead of Retail.
        return "retail", 90
    if (
        "non institutional" in t
        or "nii" in words
        or "niis" in words
        or "nib" in words
    ):
        split_markers = (
            "bid amount",
            "above",
            "below",
            "more than",
            "less than",
            "upto",
            "up to",
            "10 lakh",
            "10 lac",
            "2 lakh",
            "2 lac",
            "snii",
            "bnii",
            "small nii",
            "big nii",
        )
        if any(marker in t for marker in split_markers):
            return None, 0
        return "nii", 105
    return None, 0


def parse_bid_details(payload: Any) -> dict[str, float | None]:
    """Map NSE ``ipo-detail`` bid rows to qib/nii/retail/total multiples."""
    rows = payload.get("bidDetails") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        rows = []

    best: dict[str, tuple[int, float]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = core.number(
            _first(
                row,
                "noOfTime",
                "subscription",
                "timesSubscribed",
                "subscriptionTimes",
            )
        )
        if value is None or value < 0:
            continue
        field, score = _classify_category(_category_text(row))
        if not field:
            continue
        current = best.get(field)
        if current is None or score > current[0]:
            best[field] = (score, value)

    if "total" not in best and isinstance(payload, dict):
        root_total = core.number(
            _first(payload, "noOfTime", "subscription", "timesSubscribed", "totalSubscription")
        )
        if root_total is not None and root_total >= 0:
            best["total"] = (80, root_total)

    return {key: (best[key][1] if key in best else None) for key in SNAPSHOT_KEYS}


def parse_bse_demand_html(html: str) -> dict[str, float | None]:
    """Parse BSE's official Cumulative Demand Schedule table."""
    soup = BeautifulSoup(html, "html.parser")
    best: dict[str, tuple[int, float]] = {}
    for tr in soup.select("tr"):
        cells = [" ".join(c.stripped_strings).strip() for c in tr.select("th,td")]
        if len(cells) < 2:
            continue
        # Category is normally the second cell (after Sr.No.); Total begins in first.
        category = " ".join(cells[:2])
        field, score = _classify_category(category)
        if not field:
            continue
        value = None
        for cell in reversed(cells):
            value = core.number(cell)
            if value is not None:
                break
        if value is None or value < 0:
            continue
        current = best.get(field)
        if current is None or score > current[0]:
            best[field] = (score, value)
    return {key: (best[key][1] if key in best else None) for key in SNAPSHOT_KEYS}


def _same_values(a: dict[str, Any], b: dict[str, Any]) -> bool:
    for key in SNAPSHOT_KEYS:
        av = core.number(a.get(key))
        bv = core.number(b.get(key))
        if av is None and bv is None:
            continue
        if av is None or bv is None or abs(av - bv) > 1e-9:
            return False
    return True


def append_snapshot(record: dict[str, Any], snapshot: dict[str, Any], *, force=False) -> bool:
    """Append a changed snapshot; preserve a bounded, chronological history."""
    history = [x for x in (record.get("subscriptionHistory") or []) if isinstance(x, dict)]
    history.sort(key=lambda x: str(x.get("capturedAt") or ""))
    if history and not force and _same_values(history[-1], snapshot):
        record["subscriptionHistory"] = history[-MAX_HISTORY:]
        return False
    history.append(snapshot)
    record["subscriptionHistory"] = history[-MAX_HISTORY:]
    return True


def _is_open_record(record: dict[str, Any], today) -> bool:
    if not record.get("symbol"):
        return False
    try:
        opened = datetime.fromisoformat(record["openDate"]).date() if record.get("openDate") else None
        closed = datetime.fromisoformat(record["closeDate"]).date() if record.get("closeDate") else None
    except (TypeError, ValueError):
        opened = closed = None

    if opened and closed:
        return opened <= today <= closed
    return str(record.get("status") or "").lower() == "open"


def candidate_records(payload: dict[str, Any], *, company=None, limit=30):
    today = core.now_ist().date()
    rows = []
    needle = (company or "").strip().lower()
    for record in payload.get("ipos") or []:
        if not isinstance(record, dict) or not _is_open_record(record, today):
            continue
        if needle and needle not in str(record.get("company") or "").lower():
            continue
        rows.append(record)
    rows.sort(key=lambda x: (x.get("closeDate") or "", x.get("company") or ""))
    return rows[:limit] if limit > 0 else rows


class NSESubscriptionClient:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(core.HEADERS)
        self.primed = False
        self.prime_error: Exception | None = None

    def _prime(self):
        if self.primed:
            return
        if self.prime_error is not None:
            raise self.prime_error
        try:
            r = self.s.get(NSE_HOME, timeout=20)
            r.raise_for_status()
            self.primed = True
        except Exception as exc:  # remember a WAF block instead of retrying per IPO
            self.prime_error = exc
            raise

    def detail(self, symbol: str, board: str | None = None):
        self._prime()
        series_options = ["EQ", "SME"] if str(board or "").upper() == "SME" else ["EQ"]
        last_payload = None
        last_error = None
        for series in series_options:
            try:
                r = self.s.get(
                    f"{NSE_API}/ipo-detail",
                    params={"symbol": symbol, "series": series},
                    timeout=25,
                    headers={"Referer": NSE_DETAIL_PAGE},
                )
                r.raise_for_status()
                payload = r.json()
                last_payload = payload
                if isinstance(payload, dict) and isinstance(payload.get("bidDetails"), list):
                    return payload, series
            except Exception as exc:  # noqa: BLE001 - try the next supported series
                last_error = exc
        if last_payload is not None:
            return last_payload, series_options[-1]
        if last_error:
            raise last_error
        return {}, series_options[-1]


def _find_url(raw: str | None, page_name: str, page_url: str) -> str | None:
    if not raw or page_name.lower() not in raw.lower():
        return None
    decoded = html_lib.unescape(raw)
    match = re.search(
        rf"(?:https?://[^'\"\s)]+)?(?:/[^'\"\s)]*)?{re.escape(page_name)}\?[^'\"\s)<>]+",
        decoded,
        flags=re.I,
    )
    return urljoin(page_url, match.group(0)) if match else None


def _extract_bse_demand_url(tr, page_url: str) -> str | None:
    """Find a direct Cumulative Demand Schedule URL in BSE markup."""
    for tag in tr.select("a"):
        for raw in (tag.get("href"), tag.get("onclick")):
            found = _find_url(raw, "CummDemandSchedule.aspx", page_url)
            if found:
                return found
    return _find_url(str(tr), "CummDemandSchedule.aspx", page_url)


def _extract_bse_display_link(tr, page_url: str) -> tuple[str | None, str | None]:
    """Return (company label, DisplayIPO URL) from one BSE issue-table row."""
    for tag in tr.select("a"):
        for raw in (tag.get("href"), tag.get("onclick")):
            found = _find_url(raw, "DisplayIPO.aspx", page_url)
            if found:
                label = " ".join(tag.stripped_strings).strip() or None
                if not label:
                    cells = [" ".join(c.stripped_strings).strip() for c in tr.select("td")]
                    label = cells[0] if cells else None
                return label, found

    found = _find_url(str(tr), "DisplayIPO.aspx", page_url)
    if not found:
        return None, None
    cells = [" ".join(c.stripped_strings).strip() for c in tr.select("td")]
    return (cells[0] if cells else None), found


def _demand_url_from_display_url(display_url: str) -> str | None:
    """BSE DisplayIPO URLs carry the IPONo used by CummDemandSchedule.

    Example official route:
    DisplayIPO.aspx?...&IPONo=612 -> CummDemandSchedule.aspx?ID=612&status=L
    """
    parsed = urlparse(html_lib.unescape(display_url))
    query = {str(k).lower(): v for k, v in parse_qs(parsed.query).items()}
    values = query.get("ipono") or []
    if not values:
        return None
    ipo_no = re.sub(r"[^0-9]", "", str(values[0]))
    if not ipo_no:
        return None
    base = urljoin(display_url, "CummDemandSchedule.aspx")
    return f"{base}?{urlencode({'ID': ipo_no, 'status': 'L'})}"


def _row_company_key(tr, label: str | None = None) -> str:
    candidates = []
    if label:
        candidates.append(label)
    for tag in tr.select("a"):
        text = " ".join(tag.stripped_strings).strip()
        low = text.lower()
        if text and not any(x in low for x in ("cumulative", "demand", "bid detail", "more")):
            candidates.append(text)
    cells = [" ".join(c.stripped_strings).strip() for c in tr.select("td")]
    if cells:
        candidates.append(cells[0])
    for text in candidates:
        key = core.canonical_company(text)
        if key:
            return key
    return ""


class BSESubscriptionClient:
    """Official fallback when NSE's WAF blocks a cloud runner."""

    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(core.HEADERS)
        self.s.headers.update({"Referer": f"{core.BSE_HOME}/"})
        self._index: list[tuple[str, str]] | None = None
        self._index_error: Exception | None = None

    def _load_index(self):
        if self._index is not None:
            return
        if self._index_error is not None:
            raise self._index_error
        last_error = None
        for page_url in core.BSE_URLS:
            try:
                r = self.s.get(page_url, timeout=30)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                index: list[tuple[str, str]] = []
                display_links = direct_links = 0
                for tr in soup.select("tr"):
                    label, display_url = _extract_bse_display_link(tr, page_url)
                    demand_url = None
                    if display_url:
                        display_links += 1
                        demand_url = _demand_url_from_display_url(display_url)
                    if not demand_url:
                        demand_url = _extract_bse_demand_url(tr, page_url)
                        if demand_url:
                            direct_links += 1
                    if not demand_url:
                        continue
                    key = _row_company_key(tr, label)
                    if key:
                        index.append((key, demand_url))
                if index:
                    self._index = index
                    print(
                        f"BSE subscription index: {len(index)} issues "
                        f"({display_links} DisplayIPO links, {direct_links} direct demand links)"
                    )
                    return
                last_error = ValueError(
                    f"No BSE IPO detail links found at {page_url} "
                    f"(DisplayIPO={display_links}, directDemand={direct_links})"
                )
            except Exception as exc:  # noqa: BLE001 - try beta BSE as fallback
                last_error = exc
        self._index_error = last_error or ValueError("BSE issue index unavailable")
        raise self._index_error

    def detail(self, company: str):
        self._load_index()
        needle = core.canonical_company(company)
        matches = [(key, url) for key, url in (self._index or []) if needle and (needle in key or key in needle)]
        if not matches:
            scored = []
            for key, url in self._index or []:
                ratio = SequenceMatcher(None, needle, key).ratio()
                scored.append((ratio, url, key))
            scored.sort(reverse=True)
            if scored and scored[0][0] >= 0.72:
                matches = [(scored[0][2], scored[0][1])]
        if not matches:
            raise ValueError(f"BSE cumulative-demand link not found for {company}")

        url = matches[0][1]
        r = self.s.get(url, timeout=30, headers={"Referer": core.BSE_URL})
        r.raise_for_status()
        parsed = parse_bse_demand_html(r.text)
        if not any(value is not None for value in parsed.values()):
            raise ValueError("BSE cumulative demand page returned no headline categories")
        return parsed, url


def _source_url(symbol: str, series: str):
    return f"{NSE_DETAIL_PAGE}?{urlencode({'symbol': symbol, 'series': series})}"


def _replace_subscription_source(record: dict[str, Any], source: dict[str, Any]):
    source_names = {"NSE subscription detail", "BSE cumulative demand"}
    sources = [
        s
        for s in (record.get("sources") or [])
        if str((s or {}).get("name") or "") not in source_names
    ]
    sources.append(source)
    record["sources"] = sources


def apply_subscription(
    record: dict[str, Any],
    parsed: dict[str, float | None],
    *,
    source_name: str,
    source_url: str,
    snapshot_source: str,
    force_snapshot=False,
    observed_at=None,
):
    if not any(value is not None for value in parsed.values()):
        raise ValueError("Subscription source returned no headline category rows")

    captured_at = core.now_ist().isoformat(timespec="seconds")
    current = dict(record.get("subscription") or {})
    for key, value in parsed.items():
        if value is not None:
            current[key] = value
    record["subscription"] = current
    record["subscriptionAsOf"] = captured_at
    record["subscriptionCollectedAt"] = captured_at
    record["subscriptionObservedAt"] = observed_at
    record["subscriptionTimeBasis"] = "source-observation" if observed_at else "collection-only"
    record["subscriptionSource"] = source_name

    snapshot = {"capturedAt": captured_at, "observedAt": observed_at, "source": snapshot_source, "sourceUrl": source_url}
    snapshot.update({key: core.number(current.get(key)) for key in SNAPSHOT_KEYS})
    added = append_snapshot(record, snapshot, force=force_snapshot)

    source = core.source_stamp(source_name, source_url, "exchange", captured_at)
    _replace_subscription_source(record, source)
    return added


def update_record(record: dict[str, Any], detail: Any, *, series="EQ", force_snapshot=False):
    """Backward-compatible NSE application helper used by tests and callers."""
    parsed = parse_bid_details(detail)
    symbol = str(record.get("symbol") or "").strip()
    return apply_subscription(
        record,
        parsed,
        source_name="NSE subscription detail",
        source_url=_source_url(symbol, series),
        snapshot_source="NSE ipo-detail",
        force_snapshot=force_snapshot,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--company", default=None)
    parser.add_argument("--force-snapshot", action="store_true")
    args = parser.parse_args()

    try:
        payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"Cannot load {DATA_FILE}: {exc}", file=sys.stderr)
        return 2

    records = candidate_records(payload, company=args.company, limit=args.limit)
    nse = NSESubscriptionClient()
    bse = BSESubscriptionClient()
    attempted = updated = snapshots_added = failed = 0
    source_counts = {"NSE": 0, "BSE": 0}
    errors = []
    warnings = []

    for record in records:
        attempted += 1
        company = str(record.get("company") or "")
        try:
            try:
                detail, series = nse.detail(
                    str(record.get("symbol") or "").strip(), record.get("board")
                )
                added = update_record(
                    record,
                    detail,
                    series=series,
                    force_snapshot=args.force_snapshot,
                )
                source_counts["NSE"] += 1
                source_used = "NSE"
            except Exception as nse_exc:  # official BSE fallback for WAF/API failures
                parsed, bse_url = bse.detail(company)
                added = apply_subscription(
                    record,
                    parsed,
                    source_name="BSE cumulative demand",
                    source_url=bse_url,
                    snapshot_source="BSE cumulative demand",
                    force_snapshot=args.force_snapshot,
                )
                source_counts["BSE"] += 1
                source_used = "BSE"
                warnings.append(
                    f"{company}: NSE unavailable ({nse_exc}); used BSE cumulative demand"
                )

            updated += 1
            snapshots_added += int(added)
            print(
                f"Subscription {company} [{source_used}]: "
                f"QIB={record.get('subscription', {}).get('qib')} "
                f"NII={record.get('subscription', {}).get('nii')} "
                f"Retail={record.get('subscription', {}).get('retail')} "
                f"Total={record.get('subscription', {}).get('total')}"
            )
        except Exception as exc:  # noqa: BLE001 - one issue must not block the refresh
            failed += 1
            msg = f"{company}: {exc}"
            errors.append(msg)
            print(f"Subscription refresh failed: {msg}", file=sys.stderr)

    meta = payload.setdefault("meta", {})
    meta["schemaVersion"] = max(int(meta.get("schemaVersion") or 1), 4)
    health = {
        "ok": failed == 0 if attempted else True,
        "attempted": attempted,
        "updated": updated,
        "snapshotsAdded": snapshots_added,
        "failed": failed,
        "nseRecords": source_counts["NSE"],
        "bseFallbackRecords": source_counts["BSE"],
        "asOf": core.now_ist().isoformat(timespec="seconds"),
        "warnings": warnings[:10],
        "errors": errors[:10],
    }
    meta["subscriptionHealth"] = health
    source_health = meta.setdefault("sourceHealth", {})
    source_health.pop("NSE-subscription", None)
    source_health["IPO-subscription"] = {
        "ok": health["ok"],
        "records": updated,
        "attempted": attempted,
        "snapshotsAdded": snapshots_added,
        "failed": failed,
        "nseRecords": source_counts["NSE"],
        "bseFallbackRecords": source_counts["BSE"],
    }

    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Subscription tracking: attempted={attempted}, updated={updated}, "
        f"snapshots_added={snapshots_added}, failed={failed}, "
        f"nse={source_counts['NSE']}, bse_fallback={source_counts['BSE']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
