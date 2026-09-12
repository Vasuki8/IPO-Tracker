#!/usr/bin/env python3
"""Phase 4.5B: priority-driven backfill for open and upcoming IPOs.

This module deliberately stays on official sources.  It extends the existing
collectors in three places that matter most to the repair queue:

* include BSE SME's official current-issue index when looking for DisplayIPO /
  cumulative-demand links;
* discover official BSE SME filing PDFs for current priority issuers;
* allow a normal RHP/DRHP/Prospectus PDF as a fallback when an abridged offer
  document is unavailable or did not contain a still-missing critical field.

Existing populated values remain primary.  The underlying merge helpers only
fill missing exchange fields and all document/subscription writes retain source
provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_exchange_details as exchange  # noqa: E402
import enrich_offer_docs as offer  # noqa: E402
import track_subscriptions as subscriptions  # noqa: E402
import update_data as core  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = core.DATA_FILE
QUEUE_FILE = ROOT / "data" / "missing_queue.json"

# SEBI's official securities-market data curation page points to these BSE SME
# resources for equity issues / SME IPO filings.
BSE_SME_CURRENT_URL = "https://www.bsesme.com/PublicIssues/PublicIssues.aspx?id=2"
BSE_SME_DOCS_URL = "https://www.bsesme.com/PublicIssues/SMEIPODRHP.aspx"

OFFICIAL_DOC_HOSTS = {
    "sebi.gov.in",
    "www.sebi.gov.in",
    "bseindia.com",
    "www.bseindia.com",
    "beta.bseindia.com",
    "bsesme.com",
    "www.bsesme.com",
}

OFFER_GAP_PREFIXES = (
    "offer.",
    "exchange.issueComposition",
)


def _is_official_document_url(url: str) -> bool:
    try:
        host = (urlparse(str(url)).hostname or "").lower()
    except Exception:
        return False
    return host in OFFICIAL_DOC_HOSTS


def _document_type(text: str) -> str:
    value = str(text or "").upper()
    if "UDRHP" in value:
        return "UDRHP"
    if "DRHP" in value:
        return "DRHP"
    if re.search(r"\bRHP\b", value) or "RED HERRING" in value:
        return "RHP"
    if "PROSPECTUS" in value:
        return "PROSPECTUS"
    return "DOCUMENT"


def choose_fallback_document(record: dict[str, Any], *, exclude_url: str | None = None):
    """Prefer abridged official PDFs, then fall back to later-stage full PDFs."""
    rank = {"PROSPECTUS": 4, "RHP": 3, "UDRHP": 2, "DRHP": 1, "DOCUMENT": 0}
    candidates = []
    for doc in record.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        url = str(doc.get("url") or "").strip()
        if not url or url == exclude_url or not _is_official_document_url(url):
            continue
        title = str(doc.get("title") or "")
        joined = f"{title} {url}"
        typ = str(doc.get("type") or _document_type(joined)).upper()
        # Offer-document pages can use download handlers, so accept explicit
        # offer-document types even when the URL itself does not end in .pdf.
        looks_like_doc = ".pdf" in url.lower() or typ in rank or any(
            token in joined.upper() for token in ("DRHP", "RHP", "PROSPECTUS")
        )
        if not looks_like_doc:
            continue
        abridged = int("ABRIDGED" in joined.upper() or "AP_" in joined.upper())
        candidates.append(
            (
                abridged,
                rank.get(typ, 0),
                str(doc.get("filedDate") or ""),
                len(title),
                doc,
            )
        )
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[:-1])[-1]


def load_priority_targets(
    payload: dict[str, Any],
    queue_payload: dict[str, Any],
    *,
    priority_max: int,
    limit: int,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    records = {
        str(record.get("id")): record
        for record in payload.get("ipos") or []
        if isinstance(record, dict) and record.get("id")
    }
    selected: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for item in queue_payload.get("queue") or []:
        if not isinstance(item, dict):
            continue
        try:
            priority = int(item.get("priority"))
        except (TypeError, ValueError):
            continue
        if priority > priority_max:
            continue
        record = records.get(str(item.get("id")))
        if not record:
            continue
        selected.append((record, item))
        if limit > 0 and len(selected) >= limit:
            break
    return selected


def _subscription_index_rows(html: str, page_url: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[tuple[str, str]] = []
    for tr in soup.select("tr"):
        label, display_url = subscriptions._extract_bse_display_link(tr, page_url)
        demand_url = (
            subscriptions._demand_url_from_display_url(display_url)
            if display_url
            else None
        )
        if not demand_url:
            demand_url = subscriptions._extract_bse_demand_url(tr, page_url)
        if not demand_url:
            continue
        key = subscriptions._row_company_key(tr, label)
        if key:
            rows.append((key, demand_url))
    return rows


def build_bse_subscription_index(
    session: requests.Session,
    page_urls: list[str] | tuple[str, ...] | None = None,
):
    """Merge Mainboard and SME official subscription indexes instead of stopping at the first page."""
    urls = list(page_urls or [*core.BSE_URLS, BSE_SME_CURRENT_URL])
    merged: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    health: dict[str, Any] = {}
    for page_url in urls:
        try:
            response = session.get(page_url, timeout=30)
            response.raise_for_status()
            rows = _subscription_index_rows(response.text, page_url)
            for row in rows:
                if row not in seen:
                    seen.add(row)
                    merged.append(row)
            health[page_url] = {"ok": True, "records": len(rows)}
        except Exception as exc:  # one official index should not suppress the others
            health[page_url] = {"ok": False, "records": 0, "error": str(exc)[:250]}
    if not merged:
        failures = [f"{url}: {info.get('error', 'no issue links')}" for url, info in health.items()]
        raise ValueError("No official BSE/BSE SME subscription links found; " + "; ".join(failures[:3]))
    return merged, health


def best_subscription_url(index: list[tuple[str, str]], company: str) -> str | None:
    needle = core.canonical_company(company)
    if not needle:
        return None
    exact = [(key, url) for key, url in index if key == needle]
    if exact:
        return exact[0][1]
    contained = [(key, url) for key, url in index if needle in key or key in needle]
    if contained:
        return contained[0][1]
    scored = sorted(
        ((SequenceMatcher(None, needle, key).ratio(), url) for key, url in index),
        reverse=True,
    )
    return scored[0][1] if scored and scored[0][0] >= 0.72 else None


def discover_bse_sme_documents(
    session: requests.Session,
    targets: list[tuple[dict[str, Any], dict[str, Any]]],
) -> tuple[int, dict[str, Any]]:
    """Attach official BSE SME filing links to matching priority records."""
    try:
        response = session.get(BSE_SME_DOCS_URL, timeout=35)
        response.raise_for_status()
    except Exception as exc:
        return 0, {"ok": False, "records": 0, "error": str(exc)[:250]}

    soup = BeautifulSoup(response.text, "html.parser")
    target_keys = {
        core.canonical_company(str(record.get("company") or "")): record
        for record, _ in targets
    }
    added = 0
    for tr in soup.select("tr"):
        row_text = " ".join(tr.stripped_strings)
        row_key = core.canonical_company(row_text)
        if not row_key:
            continue
        matches = [
            record
            for key, record in target_keys.items()
            if key and (key in row_key or row_key in key)
        ]
        if not matches:
            continue
        for anchor in tr.select("a[href]"):
            raw_url = str(anchor.get("href") or "").strip()
            if not raw_url:
                continue
            url = urljoin(BSE_SME_DOCS_URL, raw_url)
            context = f"{' '.join(anchor.stripped_strings)} {row_text} {url}"
            typ = _document_type(context)
            if typ == "DOCUMENT" and ".pdf" not in url.lower():
                continue
            if not _is_official_document_url(url):
                continue
            title = " ".join(anchor.stripped_strings).strip() or f"BSE SME {typ}"
            for record in matches:
                docs = [d for d in (record.get("documents") or []) if isinstance(d, dict)]
                if any(str(d.get("url") or "") == url for d in docs):
                    continue
                docs.append(
                    {
                        "type": typ,
                        "title": title,
                        "url": url,
                        "filedDate": None,
                        "source": "BSE SME",
                    }
                )
                record["documents"] = docs
                sources = [s for s in (record.get("sources") or []) if isinstance(s, dict)]
                sources.append(core.source_stamp("BSE SME filing index", BSE_SME_DOCS_URL, "exchange"))
                record["sources"] = core.dedupe_dicts(sources, ("name", "url"))
                added += 1
    return added, {"ok": True, "records": added}


def run_exchange_backfill(
    payload: dict[str, Any],
    targets: list[tuple[dict[str, Any], dict[str, Any]]],
    session: requests.Session,
):
    urls = tuple(dict.fromkeys((*exchange.INDEX_URLS, BSE_SME_CURRENT_URL)))
    exchange.INDEX_URLS = urls
    attempted = updated = failed = matched = 0
    errors: list[str] = []
    try:
        index, page_health = exchange.build_detail_index(session)
    except Exception as exc:
        return {"ok": False, "attempted": 0, "updated": 0, "failed": 0, "error": str(exc)[:300]}

    for record, item in targets:
        missing = set(item.get("missingFields") or [])
        if not missing.intersection(
            {"exchange.lotSize", "exchange.issueSizeCr", "offer.registrar", "offer.leadManagers"}
        ):
            continue
        url = exchange.best_url(index, str(record.get("company") or ""), core.iso_date(record.get("openDate")))
        if not url:
            continue
        matched += 1
        attempted += 1
        try:
            response = session.get(url, timeout=30, headers={"Referer": BSE_SME_CURRENT_URL})
            response.raise_for_status()
            detail = exchange.parse_detail_html(response.text)
            changed = exchange.merge_detail(record, detail, url)
            updated += int(bool(changed))
            print(f"Critical BSE detail {record.get('company')}: {', '.join(changed) if changed else 'validated'}")
        except Exception as exc:
            failed += 1
            errors.append(f"{record.get('company')}: {exc}")

    return {
        "ok": failed == 0,
        "attempted": attempted,
        "matched": matched,
        "updated": updated,
        "failed": failed,
        "pageHealth": page_health,
        "errors": errors[:10],
    }


def run_subscription_backfill(
    payload: dict[str, Any],
    targets: list[tuple[dict[str, Any], dict[str, Any]]],
    session: requests.Session,
):
    live_targets = [
        (record, item)
        for record, item in targets
        if int(item.get("priority", 99)) == 0
        and any(str(field).startswith("subscription.") for field in (item.get("missingFields") or []))
    ]
    nse = subscriptions.NSESubscriptionClient()
    try:
        bse_index, page_health = build_bse_subscription_index(session)
        print(
            "Critical BSE subscription index: "
            f"{len(bse_index)} issue links across {sum(1 for x in page_health.values() if x.get('ok'))} healthy pages"
        )
    except Exception as exc:
        bse_index, page_health = [], {"error": str(exc)}

    attempted = updated = snapshots_added = failed = 0
    nse_records = bse_records = 0
    errors: list[str] = []
    warnings: list[str] = []
    for record, _ in live_targets:
        attempted += 1
        company = str(record.get("company") or "")
        try:
            try:
                detail, series = nse.detail(str(record.get("symbol") or "").strip(), record.get("board"))
                added = subscriptions.update_record(record, detail, series=series)
                source_used = "NSE"
                nse_records += 1
            except Exception as nse_exc:
                url = best_subscription_url(bse_index, company)
                if not url:
                    raise ValueError(f"NSE unavailable ({nse_exc}); BSE/BSE SME cumulative-demand link not found")
                referer = BSE_SME_CURRENT_URL if "bsesme.com" in url.lower() else core.BSE_URL
                response = session.get(url, timeout=30, headers={"Referer": referer})
                response.raise_for_status()
                parsed = subscriptions.parse_bse_demand_html(response.text)
                if not any(value is not None for value in parsed.values()):
                    raise ValueError("BSE cumulative demand page returned no headline categories")
                added = subscriptions.apply_subscription(
                    record,
                    parsed,
                    source_name="BSE cumulative demand",
                    source_url=url,
                    snapshot_source="BSE cumulative demand",
                )
                source_used = "BSE"
                bse_records += 1
                warnings.append(f"{company}: NSE unavailable; used official BSE/BSE SME cumulative demand")
            updated += 1
            snapshots_added += int(added)
            values = record.get("subscription") or {}
            print(
                f"Critical subscription {company} [{source_used}]: "
                f"QIB={values.get('qib')} NII={values.get('nii')} "
                f"Retail={values.get('retail')} Total={values.get('total')}"
            )
        except Exception as exc:
            failed += 1
            msg = f"{company}: {exc}"
            errors.append(msg)
            print(f"Critical subscription failed: {msg}", file=sys.stderr)

    health = {
        "ok": failed == 0 if attempted else True,
        "attempted": attempted,
        "updated": updated,
        "snapshotsAdded": snapshots_added,
        "failed": failed,
        "nseRecords": nse_records,
        "bseFallbackRecords": bse_records,
        "asOf": core.now_ist().isoformat(timespec="seconds"),
        "warnings": warnings[:10],
        "errors": errors[:10],
        "pageHealth": page_health,
    }
    meta = payload.setdefault("meta", {})
    meta["subscriptionHealth"] = health
    meta.setdefault("sourceHealth", {})["IPO-subscription"] = {
        "ok": health["ok"],
        "records": updated,
        "attempted": attempted,
        "snapshotsAdded": snapshots_added,
        "failed": failed,
        "nseRecords": nse_records,
        "bseFallbackRecords": bse_records,
        "asOf": health["asOf"],
        "errors": errors[:5],
    }
    return health


def run_document_backfill(
    payload: dict[str, Any],
    targets: list[tuple[dict[str, Any], dict[str, Any]]],
    session: requests.Session,
    *,
    force: bool = False,
):
    discovered, discovery_health = discover_bse_sme_documents(session, targets)
    if discovered:
        print(f"Discovered {discovered} official BSE SME document links for priority IPOs")

    attempted = extracted = failed = 0
    errors: list[str] = []
    # Keep the fallback bounded; full offer documents can be materially larger
    # than abridged prospectuses, but 35 MB still prevents runaway downloads.
    previous_cap = offer.MAX_PDF_BYTES
    offer.MAX_PDF_BYTES = max(previous_cap, 35 * 1024 * 1024)
    try:
        for record, item in targets:
            missing = [str(field) for field in (item.get("missingFields") or [])]
            if not any(field.startswith(OFFER_GAP_PREFIXES) for field in missing):
                continue
            previous = record.get("offerDocumentExtraction") or {}
            exclude = None
            if previous.get("status") == "extracted" and not force:
                exclude = str(previous.get("documentUrl") or "") or None
            doc = choose_fallback_document(record, exclude_url=exclude)
            if not doc:
                continue
            attempted += 1
            try:
                data = offer.download_pdf(session, str(doc.get("url")))
                text, pages_read, page_count = offer.extract_pdf_text(data)
                parsed = offer.parse_document_text(text, record.get("priceBand"))
                if not parsed.get("extractedFields"):
                    raise ValueError("no structured fields recognized")
                offer.apply_enrichment(
                    record,
                    parsed,
                    doc,
                    hashlib.sha256(data).hexdigest(),
                    pages_read,
                    page_count,
                )
                extracted += 1
                print(
                    f"Critical offer doc {record.get('company')}: "
                    f"{', '.join(parsed.get('extractedFields') or [])}"
                )
            except Exception as exc:
                failed += 1
                errors.append(f"{record.get('company')}: {exc}")
                print(f"Critical offer-document fallback failed: {record.get('company')}: {exc}", file=sys.stderr)
    finally:
        offer.MAX_PDF_BYTES = previous_cap

    health = {
        "ok": failed == 0 if attempted else True,
        "attempted": attempted,
        "extracted": extracted,
        "failed": failed,
        "documentsDiscovered": discovered,
        "discoveryHealth": discovery_health,
        "errors": errors[:10],
        "asOf": core.now_ist().isoformat(timespec="seconds"),
    }
    payload.setdefault("meta", {})["criticalOfferDocumentHealth"] = health
    return health


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority-max", type=int, default=1)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--exchange-only", action="store_true")
    parser.add_argument("--subscriptions-only", action="store_true")
    parser.add_argument("--documents-only", action="store_true")
    parser.add_argument("--force-docs", action="store_true")
    args = parser.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    queue_payload = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else {"queue": []}
    targets = load_priority_targets(
        payload,
        queue_payload,
        priority_max=args.priority_max,
        limit=args.limit,
    )
    print(
        f"Critical backfill targets: {len(targets)} "
        f"(priority <= P{args.priority_max}, limit={args.limit or 'all'})"
    )

    modes = [args.exchange_only, args.subscriptions_only, args.documents_only]
    run_all = not any(modes)
    session = requests.Session()
    session.headers.update(core.HEADERS)

    result: dict[str, Any] = {
        "ok": True,
        "targetCount": len(targets),
        "priorityMax": args.priority_max,
        "asOf": core.now_ist().isoformat(timespec="seconds"),
    }

    if run_all or args.exchange_only:
        result["exchange"] = run_exchange_backfill(payload, targets, session)
    if run_all or args.subscriptions_only:
        result["subscriptions"] = run_subscription_backfill(payload, targets, session)
    if run_all or args.documents_only:
        result["documents"] = run_document_backfill(
            payload,
            targets,
            session,
            force=args.force_docs,
        )

    result["ok"] = all(
        section.get("ok", True)
        for section in result.values()
        if isinstance(section, dict)
    )
    meta = payload.setdefault("meta", {})
    meta["schemaVersion"] = max(int(meta.get("schemaVersion") or 1), 4)
    meta["criticalBackfillHealth"] = result
    meta.setdefault("sourceHealth", {})["Critical-backfill"] = {
        "ok": result["ok"],
        "records": len(targets),
        "asOf": result["asOf"],
    }

    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
