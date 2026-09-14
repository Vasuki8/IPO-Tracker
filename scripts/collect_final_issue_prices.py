"""Persist explicit final offer prices from official NSE monthly IPO reports.

An exact canonical issuer and matching issue date are mandatory. The price band
is used only as a consistency check, never as the final-price source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import update_data as core
from parser_loader import isolated_module
from validate_data import numeric

reports = isolated_module("enrich_nse_primary_market_reports_v3")
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/monthly-reports"


def official_url(url):
    parsed = urlparse(str(url))
    return parsed.scheme == "https" and parsed.hostname in {"www.nseindia.com", "nsearchives.nseindia.com", "archives.nseindia.com"}


def matched_report(record, rows):
    if record.get("issueEventType") or not record.get("openDate"):
        return None
    key = core.canonical_company(record.get("company", ""))
    candidates = []
    for row in rows:
        if row.get("matchKey") != key or not official_url(row.get("sourceUrl")):
            continue
        if row.get("symbol") and record.get("symbol") and row["symbol"] != record["symbol"]:
            continue
        # Reports sometimes contain a typo in an issue date. Such rows cannot
        # establish a final-price baseline without an independent date review.
        if row.get("openDate") != record["openDate"]:
            continue
        if record.get("closeDate") and row.get("closeDate") and row["closeDate"] != record["closeDate"]:
            continue
        if numeric(row.get("issuePrice")) and row["issuePrice"] > 0:
            candidates.append(row)
    if len({row["issuePrice"] for row in candidates}) != 1:
        return None
    return candidates[0] if candidates else None


def accept_price(record, value, evidence):
    if not numeric(value) or value <= 0 or not official_url(evidence.get("sourceUrl")):
        return False
    if evidence.get("issueOpenDate") != record.get("openDate"):
        return False
    if core.canonical_company(evidence.get("company", "")) != core.canonical_company(record.get("company", "")):
        return False
    band = record.get("priceBand") or {}
    if (numeric(band.get("min")) and value < band["min"]) or (numeric(band.get("max")) and value > band["max"]):
        return False
    listing = record.get("listing") or {}
    if listing.get("issuePrice") is not None and listing["issuePrice"] != value:
        return False
    if listing.get("issuePrice") == value and listing.get("issuePriceEvidence"):
        return False
    record["listing"] = {**listing, "issuePrice": value, "issuePriceEvidence": {**evidence, "value": value, "checkedAt": datetime.now(timezone.utc).isoformat()}}
    return True


def merge_price(record, row):
    if matched_report(record, [row]) is None:
        return False
    evidence = {"source": "NSE primary-market monthly report", "sourceUrl": row["sourceUrl"], "sha256": row.get("sha256"), "company": row["company"], "symbol": row.get("symbol"), "issueOpenDate": row["openDate"], "issueCloseDate": row.get("closeDate"), "field": "Issue_Price"}
    accepted = accept_price(record, row["issuePrice"], evidence)
    if accepted:
        sources = record.setdefault("sources", [])
        if not any(source.get("url") == row["sourceUrl"] for source in sources):
            sources.append(core.source_stamp("NSE primary-market monthly report", row["sourceUrl"], "exchange"))
        record.setdefault("observations", {})["NSEFinalIssuePrice"] = {**evidence, "value": row["issuePrice"]}
    return accepted


def existing_verified_prices(payload):
    updated = 0
    for record in payload.get("ipos", []):
        observation = (record.get("observations") or {}).get("VerifiedP4FinalIssueTerms") or {}
        urls = observation.get("sourceUrls") or []
        circulars = [url for url in urls if official_url(url) and "/content/circulars/" in url]
        if not circulars or "final issue price" not in str(observation.get("sourceBasis", "")).lower():
            continue
        evidence = {"source": "Previously verified NSE listing circular", "sourceUrl": circulars[0], "company": record.get("company"), "symbol": record.get("symbol"), "issueOpenDate": observation.get("openDate"), "sourceBasis": observation.get("sourceBasis")}
        updated += int(accept_price(record, observation.get("issuePrice"), evidence))
    return updated


def load_report(url):
    if not official_url(url):
        raise ValueError("Monthly report is not on an official NSE host")
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".xlsx")
    if path.exists():
        data = path.read_bytes()
    else:
        session = requests.Session()
        session.headers.update(core.HEADERS)
        data = reports.download_report(session, url)
        if len(data) > 8 * 1024 * 1024:
            raise ValueError("Monthly workbook exceeds 8 MiB")
        path.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    return [{**row, "sha256": digest} for row in reports.parse_report_rows(reports.read_xlsx_rows(data), url)]


def run(payload, history_days=730, max_reports=36):
    today = date.today()
    cutoff = (today - timedelta(days=history_days)).isoformat()
    candidates = [record for record in payload["ipos"] if cutoff <= str(record.get("openDate") or "") <= today.isoformat() and not record.get("issueEventType") and not (record.get("listing") or {}).get("issuePriceEvidence")]
    updated = existing_verified_prices(payload)
    session = requests.Session()
    session.headers.update(core.HEADERS)
    errors, rows = [], []
    try:
        urls = reports.discover_report_urls(session, max_reports)
    except Exception as exc:
        urls = []
        errors.append({"source": reports.INDEX_URL, "error": str(exc)[:250]})
    # Existing source-linked workbooks remain usable if index discovery fails.
    if not urls:
        urls = list(dict.fromkeys(source["url"] for record in candidates for source in record.get("sources", []) if "primary-market monthly" in source.get("name", "").lower() and official_url(source.get("url"))))[:max_reports]
    def fetch(url):
        try:
            return load_report(url), None
        except Exception as exc:
            return [], {"source": url, "error": str(exc)[:250]}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for found, error in pool.map(fetch, urls):
            rows.extend(found)
            if error:
                errors.append(error)
    for record in candidates:
        row = matched_report(record, rows)
        if row:
            updated += int(merge_price(record, row))
    health = {"updated": updated, "candidates": len(candidates), "reportRows": len(rows), "reports": len(urls), "failed": len(errors), "errors": errors, "checkedAt": datetime.now(timezone.utc).isoformat()}
    payload.setdefault("meta", {})["finalIssuePriceHealth"] = health
    return health


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--history-days", type=int, default=730)
    cli.add_argument("--max-reports", type=int, default=36)
    args = cli.parse_args()
    path = ROOT / "data/ipos.json"
    payload = json.loads(path.read_text())
    print(json.dumps(run(payload, max(0, args.history_days), max(1, args.max_reports))))
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


if __name__ == "__main__":
    main()
