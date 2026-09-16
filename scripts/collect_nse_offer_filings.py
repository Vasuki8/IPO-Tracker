"""Recover issue terms from NSE's issuer-linked final-listing XBRL filings.

The offer register establishes the issuer; the XML must independently match
the issue dates and security. A current trading lot is never an IPO lot source.
PDF discovery is bounded separately and only used for unresolved offer fields.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import update_data as core
from collect_final_issue_prices import accept_price, official_url

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/nse-offer-filings"
PAGE = "https://www.nseindia.com/companies-listing/corporate-filings-offer-documents"
FEEDS = [f"https://www.nseindia.com/api/corporates/offerdocs?index={board}" for board in ("sme", "equities")]
NS = "https://www.sebi.gov.in/xbrl/2022-03-31/in-capmkt"
ATTEMPT = "nseOfferFilings"


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean(value):
    text = str(value or "").strip()
    return "" if text in {"-", "NA", "N/A", "null"} else text


def source_date(value):
    value = clean(value)
    for fmt in ("%Y-%m-%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def archive_url(value, suffix):
    url = clean(value)
    return url if official_url(url) and urlparse(url).path.lower().endswith(suffix) else None


def matched_entries(record, rows):
    if record.get("issueEventType") or not source_date(record.get("openDate")):
        return []
    issuer = core.canonical_company(record.get("company", ""))
    if not issuer:
        return []
    matches = []
    for row in rows:
        if core.canonical_company(row.get("company", "")) != issuer:
            continue
        if any(clean(row.get(key)) and clean(record.get(key)) and clean(row[key]).upper() != clean(record[key]).upper() for key in ("symbol", "isin")):
            continue
        if any(clean(row.get(source)) and source_date(row[source]) != record.get(field) for source, field in (("issue_open_date", "openDate"), ("issue_close_date", "closeDate")) if record.get(field)):
            continue
        matches.append(row)
    return matches


def parse_listing(data):
    if len(data) > 1024 * 1024 or re.search(br"<!\s*(?:DOCTYPE|ENTITY)", data, re.I):
        raise ValueError("Unsupported XBRL document")
    root = ET.fromstring(data)
    if root.tag != "{http://www.xbrl.org/2003/instance}xbrl":
        raise ValueError("Expected a final-listing XBRL document")
    cells = defaultdict(set)
    units = {"MarketLot": "shares", "FinalIssuePrice": "INRPerShare"}
    for node in root:
        if not node.tag.startswith("{" + NS + "}"):
            continue
        key = node.tag.split("}", 1)[1]
        if key in units and node.get("unitRef") != units[key]:
            raise ValueError(f"Unexpected unit for {key}")
        if clean(node.text):
            cells[key].add(clean(node.text))
    if any(len(values) != 1 for values in cells.values()):
        raise ValueError("Conflicting values in final-listing XBRL")
    return {key: next(iter(values)) for key, values in cells.items()}


def verified_terms(record, entry, cells):
    if not matched_entries(record, [entry]):
        return False
    if source_date(cells.get("DateOfIssueOpen")) != record.get("openDate"):
        return False
    closed = source_date(cells.get("DateOfIssueClose"))
    if not closed or closed < record["openDate"] or record.get("closeDate") and closed != record["closeDate"]:
        return False
    # A symbol or ISIN must independently confirm the register's issuer match.
    confirmed = False
    for field, tag in (("symbol", "ScripID"), ("isin", "ISIN")):
        expected, observed = clean(record.get(field)).upper(), clean(cells.get(tag)).upper()
        if expected and observed:
            if expected != observed:
                return False
            confirmed = True
    listed = source_date(cells.get("DateOfListing"))
    return confirmed and bool(listed and closed <= listed <= date.today().isoformat())


def positive(value, integral=False):
    if not re.fullmatch(r"\d+(?:\.\d+)?", clean(value)):
        return None
    number = float(value)
    if not 0 < number < 1e9 or integral and (not number.is_integer() or number > 100000):
        return None
    return int(number) if integral else number


def merge_terms(record, entry, cells, url, digest):
    if not archive_url(url, ".xml") or not verified_terms(record, entry, cells):
        return []
    evidence = {"source": "NSE final-listing XBRL", "sourceUrl": url, "registerUrl": PAGE,
                "sha256": digest, "company": entry["company"], "symbol": cells.get("ScripID"),
                "isin": cells.get("ISIN"), "issueOpenDate": source_date(cells["DateOfIssueOpen"]),
                "issueCloseDate": source_date(cells["DateOfIssueClose"])}
    changed = []
    lot = positive(cells.get("MarketLot"), integral=True)
    # Keep a disclosed application minimum separate from the market/bid lot.
    # Existing values are never overwritten by this fill-only collector.
    if lot and not record.get("lotSize") and record.get("marketLot") in (None, lot):
        record["lotSize"] = lot
        record["marketLot"] = lot
        record["lotSizeEvidence"] = {**evidence, "field": "MarketLot", "value": lot, "checkedAt": stamp()}
        changed.append("lotSize")
    listed = source_date(cells.get("DateOfListing"))
    if not record.get("listingDate"):
        record["listingDate"] = listed
        record["listingDateEvidence"] = {**evidence, "field": "DateOfListing", "value": listed, "checkedAt": stamp()}
        changed.append("listingDate")
    price = positive(cells.get("FinalIssuePrice"))
    if price and accept_price(record, price, {**evidence, "field": "FinalIssuePrice"}):
        changed.append("listing.issuePrice")
    if changed:
        if not any(source.get("url") == url for source in record.get("sources", [])):
            record.setdefault("sources", []).append(core.source_stamp("NSE final-listing XBRL", url, "exchange"))
        record.setdefault("observations", {})["NSEFinalListing"] = {**evidence, "fields": cells}
        record["validation"] = core.build_validation(record)
    return changed


def discover_documents(record, entries):
    """Only final/RHP filings near this issue; drafts can belong to old attempts."""
    opened = date.fromisoformat(record["openDate"])
    closed = date.fromisoformat(record.get("closeDate") or record["openDate"])
    found = []
    for row in matched_entries(record, entries):
        for key, kind in (("fp", "PROSPECTUS"), ("rhp", "RHP")):
            url, filed = archive_url(row.get(key + "Attach"), ".pdf"), source_date(row.get(key + "Date"))
            if not url or not filed:
                continue
            when = date.fromisoformat(filed)
            if kind == "RHP" and not opened - timedelta(days=60) <= when <= opened:
                continue
            if kind == "PROSPECTUS" and not closed <= when <= closed + timedelta(days=30):
                continue
            found.append({"url": url, "source": "NSE", "type": kind, "title": record["company"] + " " + kind,
                          "filedDate": filed, "registerUrl": PAGE})
    added = 0
    for doc in sorted(found, key=lambda item: (item["filedDate"], item["type"]), reverse=True):
        if not any(old.get("url") == doc["url"] for old in record.get("documents", [])):
            record.setdefault("documents", []).append(doc)
            added += 1
    return added


def fetch(url, cache=False):
    if not official_url(url):
        raise ValueError("Expected an official NSE source")
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".xml")
    if cache and path.exists():
        data = path.read_bytes()
        parse_listing(data)
        return data
    started = time.monotonic()
    with requests.get(url, headers={**core.HEADERS, "Referer": PAGE}, stream=True, timeout=(10, 25)) as response:
        response.raise_for_status()
        chunks, total = [], 0
        for chunk in response.iter_content(131072):
            total += len(chunk)
            if total > (1024 * 1024 if cache else 8 * 1024 * 1024) or time.monotonic() - started > 45:
                raise ValueError("NSE response exceeds bounded download budget")
            chunks.append(chunk)
        data = b"".join(chunks)
    if cache:
        parse_listing(data)
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return data


def run(payload, limit=125, history_days=730, documents_limit=0, retry_days=7, checkpoint=None):
    rows, errors = [], []
    for url in FEEDS:
        try:
            entries = json.loads(fetch(url))
            if not isinstance(entries, list) or not all(isinstance(row, dict) for row in entries):
                raise ValueError("Unexpected NSE offer-register schema")
            rows.extend(entries)
        except (ValueError, requests.RequestException) as exc:
            errors.append({"sourceUrl": url, "error": str(exc)[:250]})
    index = defaultdict(list)
    for row in rows:
        index[core.canonical_company(row.get("company", ""))].append(row)
    today = date.today()
    cutoff = (today - timedelta(days=history_days)).isoformat()
    candidates = []
    for record in payload["ipos"]:
        if not cutoff <= str(record.get("openDate") or "") <= (today + timedelta(days=30)).isoformat() or record.get("issueEventType"):
            continue
        needs_docs = not record.get("lotSize") or not record.get("registrar") or not record.get("leadManagers")
        if not needs_docs and (record.get("listing") or {}).get("issuePriceEvidence") and record.get("listingDate"):
            continue
        entries = matched_entries(record, index[core.canonical_company(record.get("company", ""))])
        if not entries:
            continue
        fingerprint = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
        attempt = record.get(ATTEMPT) or {}
        if attempt.get("fingerprint") == fingerprint and str(attempt.get("lastAttemptAt", ""))[:10] > (today - timedelta(days=retry_days)).isoformat():
            continue
        candidates.append((bool(record.get("lotSize")), str(attempt.get("lastAttemptAt", "")), record["id"], record, entries, fingerprint))
    candidates.sort(key=lambda item: item[:3])
    selected = candidates[:limit]
    urls = sorted({url for *_, entries, _ in selected for row in entries if (url := archive_url(row.get("ipo_inlisting_xbrl_link"), ".xml"))})
    fetched = {}
    def load(url):
        raw = fetch(url, cache=True)
        return parse_listing(raw), hashlib.sha256(raw).hexdigest()
    outcomes, documents = [], 0
    health = {"registerRows": len(rows), "candidates": len(candidates), "attempted": 0, "updated": 0, "documentsDiscovered": 0, "failed": len(errors), "errors": errors, "outcomes": outcomes, "checkedAt": stamp()}
    payload.setdefault("meta", {})["nseOfferFilingsHealth"] = health
    def apply_record(item):
        nonlocal documents
        _, _, _, record, entries, fingerprint = item
        matches = []
        for entry in entries:
            url = archive_url(entry.get("ipo_inlisting_xbrl_link"), ".xml")
            if url in fetched and verified_terms(record, entry, fetched[url][0]):
                cells, digest = fetched[url]
                matches.append((entry, cells, url, digest))
        # Duplicate register rows are common; incompatible filings require review.
        signatures = {tuple(cells.get(key) for key in ("MarketLot", "FinalIssuePrice", "DateOfListing", "ISIN", "ScripID")) for _, cells, _, _ in matches}
        changed = merge_terms(record, *matches[0]) if len(signatures) == 1 else []
        added = 0
        if documents < documents_limit and (not record.get("lotSize") or not record.get("registrar") or not record.get("leadManagers")):
            added = discover_documents(record, entries)
            documents += bool(added)
        failed = any(archive_url(row.get("ipo_inlisting_xbrl_link"), ".xml") in {error["sourceUrl"] for error in errors} for row in entries)
        outcome = {"id": record["id"], "status": "updated" if changed or added else "conflict" if len(signatures) > 1 else "source_blocked" if failed else "no_match", "changedFields": changed, "documentsAdded": added}
        record[ATTEMPT] = {**outcome, "lastAttemptAt": stamp(), "fingerprint": fingerprint}
        outcomes.append(outcome)
        health.update(attempted=len(outcomes), updated=sum(item["status"] == "updated" for item in outcomes), documentsDiscovered=documents, failed=len(errors), checkedAt=stamp())
        if checkpoint:
            checkpoint(payload)
    pending = {n: {url for row in item[-2] if (url := archive_url(row.get("ipo_inlisting_xbrl_link"), ".xml"))} for n, item in enumerate(selected)}
    completed = set()
    def checkpoint_ready():
        for n, required in list(pending.items()):
            if required <= completed:
                apply_record(selected[n])
                del pending[n]
    checkpoint_ready()
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(load, url): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                fetched[url] = future.result()
            except (ValueError, ET.ParseError, requests.RequestException) as exc:
                errors.append({"sourceUrl": url, "error": str(exc)[:250]})
            completed.add(url)
            checkpoint_ready()
    return health


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--limit", type=int, default=125)
    cli.add_argument("--history-days", type=int, default=730)
    cli.add_argument("--documents-limit", type=int, default=0)
    cli.add_argument("--retry-days", type=int, default=7)
    args = cli.parse_args()
    path = ROOT / "data/ipos.json"
    payload = json.loads(path.read_text())
    def save(value):
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(path)
    health = run(payload, max(1, args.limit), max(0, args.history_days), max(0, args.documents_limit), max(0, args.retry_days), save)
    save(payload)
    print(json.dumps(health))


if __name__ == "__main__":
    main()
