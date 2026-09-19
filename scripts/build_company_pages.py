#!/usr/bin/env python3
"""Generate permanent IPO routes plus a compact public dashboard index.

The canonical collector dataset remains data/ipos.json. Browser-facing pages use:
- data/ipos-summary.json for the dashboard list/stats/filter view.
- a compact JSON profile embedded in each permanent ipo/<slug>/ route.

Embedding one profile in its existing route avoids a second per-company data file,
lets permanent pages render without downloading the multi-megabyte master dataset,
and lets the dashboard lazily fetch only one route when a user opens details.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from public_quality import project_record, summary_quality

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"
SUMMARY_FILE = ROOT / "data" / "ipos-summary.json"
OUT_DIR = ROOT / "ipo"
MANIFEST = OUT_DIR / "routes.json"

ROUTE_TEMPLATE_VERSION = 4
PUBLIC_SUMMARY_VERSION = 1
PROFILE_SCRIPT_ID = "ipo-profile-data"


def route_slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "ipo"


def _identity(record: dict[str, Any]) -> str:
    fields = (
        record.get("id"),
        record.get("company"),
        record.get("matchKey"),
        record.get("openDate"),
        record.get("listingDate"),
        record.get("board"),
        record.get("exchange"),
    )
    return "|".join(str(value or "") for value in fields)


def assign_routes(records: list[dict[str, Any]]) -> list[tuple[dict[str, Any], str]]:
    """Assign stable clean routes and add profilePath to every record."""
    bases = [route_slug(str(row.get("id") or row.get("company") or "")) for row in records]
    counts = Counter(bases)
    used: set[str] = set()
    assigned: list[tuple[dict[str, Any], str]] = []

    for record, base in zip(records, bases):
        route = base
        if counts[base] > 1:
            digest = hashlib.sha1(_identity(record).encode("utf-8")).hexdigest()[:8]
            route = f"{base}--{digest}"
        if route in used:
            suffix = 2
            candidate = f"{route}-{suffix}"
            while candidate in used:
                suffix += 1
                candidate = f"{route}-{suffix}"
            route = candidate
        used.add(route)
        record["profilePath"] = f"ipo/{route}/"
        assigned.append((record, route))

    return assigned


def _compact(value: Any) -> Any:
    """Recursively drop empty/null values while preserving 0 and False."""
    if isinstance(value, dict):
        out = {key: _compact(item) for key, item in value.items()}
        return {
            key: item
            for key, item in out.items()
            if item is not None and item != "" and item != [] and item != {}
        }
    if isinstance(value, list):
        out = [_compact(item) for item in value]
        return [item for item in out if item is not None and item != "" and item != [] and item != {}]
    return value


def _pick(mapping: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(mapping, dict):
        return {}
    return _compact({field: mapping.get(field) for field in fields})


def _pick_rows(rows: Any, fields: tuple[str, ...]) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    return [
        selected
        for row in rows
        if isinstance(row, dict)
        and (selected := _pick(row, fields))
    ]


def source_count(record: dict[str, Any]) -> int:
    sources = record.get("sources") or ([record["source"]] if isinstance(record.get("source"), dict) else [])
    families = {
        str(source.get("name") or "").split(" ")[0]
        for source in sources
        if isinstance(source, dict) and source.get("name")
    }
    return len(families)


def public_summary_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return compact directory/comparison fields and subscription provenance."""
    record = project_record(record)
    subscription = _pick(record.get("subscription"), ("total",))
    listing = _pick(record.get("listing"), ("gainPct",))
    lifecycle = _pick(record.get("lifecycle"), ("stage", "stageDate"))
    validation = _pick(record.get("validation"), ("status",))
    documents = _pick_rows(record.get("documents"), ("type",))
    price_band = _pick(record.get("priceBand"), ("min", "max"))

    return _compact(
        {
            "id": record.get("id"),
            "company": record.get("company"),
            "symbol": record.get("symbol"),
            "board": record.get("board"),
            "exchange": record.get("exchange"),
            "status": record.get("status"),
            "openDate": record.get("openDate"),
            "closeDate": record.get("closeDate"),
            "listingDate": record.get("listingDate"),
            "priceBand": price_band,
            "lotSize": record.get("lotSize"),
            "issueSizeCr": record.get("issueSizeCr"),
            "subscription": subscription,
            "publicQuality": summary_quality(record["publicQuality"]),
            **{key: record.get(key) for key in ("subscriptionObservedAt", "subscriptionCollectedAt", "subscriptionTimeBasis", "subscriptionAuthority", "subscriptionSourceUrl")},
            "subscriptionAsOf": record.get("subscriptionAsOf"),
            "subscriptionSource": record.get("subscriptionSource"),
            "listing": listing,
            "validation": validation,
            "lifecycle": lifecycle,
            "documents": documents,
            "sourceCount": source_count(record),
            "profilePath": record.get("profilePath"),
        }
    )


def public_profile_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return the compact, display-only record embedded in a permanent route."""
    record = project_record(record)
    sources = record.get("sources") or ([record["source"]] if isinstance(record.get("source"), dict) else [])
    profile = {
        "publicQuality": record["publicQuality"],
        **{key: record.get(key) for key in ("marketLot", "minimumBidQuantity", "subscriptionObservedAt", "subscriptionCollectedAt", "subscriptionTimeBasis", "subscriptionAuthority", "subscriptionSourceUrl")},
        "id": record.get("id"),
        "company": record.get("company"),
        "symbol": record.get("symbol"),
        "board": record.get("board"),
        "exchange": record.get("exchange"),
        "status": record.get("status"),
        "issueType": record.get("issueType"),
        "openDate": record.get("openDate"),
        "closeDate": record.get("closeDate"),
        "allotmentDate": record.get("allotmentDate"),
        "listingDate": record.get("listingDate"),
        "lotSize": record.get("lotSize"),
        "issueSizeCr": record.get("issueSizeCr"),
        "freshIssueCr": record.get("freshIssueCr"),
        "ofsCr": record.get("ofsCr"),
        "subscriptionAsOf": record.get("subscriptionAsOf"),
        "subscriptionSource": record.get("subscriptionSource"),
        "profilePath": record.get("profilePath"),
        "priceBand": _pick(record.get("priceBand"), ("min", "max")),
        "subscription": _pick(record.get("subscription"), ("qib", "nii", "retail", "total")),
        "subscriptionHistory": _pick_rows(
            record.get("subscriptionHistory"),
            ("capturedAt", "observedAt", "collectedAt", "timeBasis", "qib", "nii", "retail", "total", "source", "sourceUrl"),
        ),
        "listing": _pick(record.get("listing"), ("issuePrice", "listPrice", "gainPct")),
        "lifecycle": _pick(record.get("lifecycle"), ("stage", "stageDate")),
        "documents": _pick_rows(record.get("documents"), ("type", "title", "url", "filedDate")),
        "sources": _pick_rows(sources, ("name", "asOf", "url")),
        "validation": {
            **_pick(record.get("validation"), ("status",)),
            "checks": _pick_rows(
                (record.get("validation") or {}).get("checks") if isinstance(record.get("validation"), dict) else [],
                ("field", "match", "nse", "bse"),
            ),
        },
        "offerDocumentExtraction": _pick(
            record.get("offerDocumentExtraction"),
            ("status", "documentUrl", "documentType", "pagesRead", "pageCount", "extractedAt"),
        ),
        "issueComposition": _pick(
            record.get("issueComposition"),
            ("freshShares", "ofsShares", "freshValueCr", "ofsValueCr", "valuationPriceUsed", "qualifiers"),
        ),
        "leadManagers": record.get("leadManagers"),
        "registrar": record.get("registrar"),
        "promoters": record.get("promoters"),
        "objectsOfIssue": _pick_rows(record.get("objectsOfIssue"), ("purpose", "amountCr")),
        "financials": {
            "periods": _pick_rows(
                (record.get("financials") or {}).get("periods") if isinstance(record.get("financials"), dict) else [],
                ("period", "revenueCr", "ebitdaCr", "patCr", "netWorthCr", "ronwPct", "roePct", "eps"),
            )
        },
        "shareholding": _pick(record.get("shareholding"), ("promoterPreIssuePct",)),
    }
    return _compact(profile)


def public_summary_payload(payload: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    public_meta = _compact(
        {
            "generatedAt": meta.get("generatedAt"),
            "schemaVersion": meta.get("schemaVersion"),
            "seed": meta.get("seed"),
            "sourceHealth": meta.get("sourceHealth"),
            "errors": meta.get("errors"),
            "recordCount": len(records),
            "publicSummaryVersion": PUBLIC_SUMMARY_VERSION,
        }
    )
    return {"meta": public_meta, "ipos": [public_summary_record(record) for record in records]}


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _script_json(value: Any) -> str:
    # Prevent embedded data from ever closing the application/json script tag.
    return _json_text(value).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def route_digest(record: dict[str, Any], route: str) -> str:
    """Fingerprint only bytes that can affect one generated route."""
    value = {
        "templateVersion": ROUTE_TEMPLATE_VERSION,
        "route": route,
        "profile": public_profile_record(record),
    }
    return hashlib.sha256(_json_text(value).encode("utf-8")).hexdigest()[:16]


def page_html(record: dict[str, Any], route: str) -> str:
    company = str(record.get("company") or "Indian IPO")
    symbol = str(record.get("symbol") or record.get("exchange") or "IPO")
    title = html.escape(f"{company} IPO | India IPO Tracker", quote=True)
    description = html.escape(
        f"{company} IPO details, issue dates, price band, subscription, SEBI documents, financials and official source validation.",
        quote=True,
    )
    company_html = html.escape(company, quote=True)
    symbol_html = html.escape(symbol, quote=True)
    record_id = html.escape(str(record.get("id") or ""), quote=True)
    profile_path = html.escape(str(record.get("profilePath") or f"ipo/{route}/"), quote=True)
    route_html = html.escape(route, quote=True)
    embedded_profile = _script_json({"ipo": public_profile_record(record)})

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#07111f" />
  <meta name="description" content="{description}" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta name="twitter:card" content="summary" />
  <title>{title}</title>
  <base href="../../" />
  <link rel="canonical" href="ipo/{route_html}/" />
  <link rel="stylesheet" href="styles.css" />
  <link rel="stylesheet" href="phase4.css" />
  <link rel="stylesheet" href="company.css" />
  <link rel="stylesheet" href="company-page.css" />
  <link rel="stylesheet" href="public-quality.css" />
</head>
<body class="company-route-body" data-ipo-id="{record_id}" data-profile-path="{profile_path}">
  <div class="company-route-shell">
    <header class="topbar company-route-topbar">
      <a class="brand" href="./" aria-label="Back to India IPO Tracker" style="text-decoration:none;color:inherit">
        <div class="brand-mark">IP</div>
        <div>
          <div class="brand-title">India IPO Tracker</div>
          <div class="brand-subtitle">{company_html} · {symbol_html}</div>
        </div>
      </a>
      <div class="company-route-actions">
        <a class="company-route-back" href="./">← All IPOs</a>
        <button class="company-route-share" id="copyCompanyLink" type="button">Copy link</button>
      </div>
    </header>

    <div class="company-route-freshness" id="routeFreshness">Loading official-source data…</div>
    <main class="company-route-main" id="companyPage" aria-live="polite">
      <div class="company-route-error"><div class="eyebrow">LOADING IPO PROFILE</div><h1>{company_html}</h1><p>Loading the latest official-source record…</p></div>
    </main>

    <footer class="company-route-footer">
      <span>Source-linked IPO research · not investment advice.</span>
      <a href="methodology.html">Sources &amp; methodology</a> · <a href="./">Back to all IPOs</a>
    </footer>
  </div>

  <script id="{PROFILE_SCRIPT_ID}" type="application/json">{embedded_profile}</script>
  <script src="public-quality.js" defer></script>
  <script src="company-page.js" defer></script>
  <script src="company.js" defer></script>
</body>
</html>
"""


def load_manifest() -> dict[str, Any]:
    try:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def write_text_if_changed(path: Path, content: str) -> bool:
    """Write text only when bytes would actually change."""
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos", []) if isinstance(row, dict) and row.get("id")]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    previous_manifest = load_manifest()
    previous = set(previous_manifest.get("routes") or [])
    previous_digests = previous_manifest.get("routeDigests") or {}
    if not isinstance(previous_digests, dict):
        previous_digests = {}

    old_profile_paths = {id(record): record.get("profilePath") for record in records}
    assigned = assign_routes(records)
    current = {route for _, route in assigned}
    profile_paths_changed = any(
        old_profile_paths[id(record)] != record.get("profilePath")
        for record, _route in assigned
    )

    if profile_paths_changed:
        DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary_content = _json_text(public_summary_payload(payload, records)) + "\n"
    summary_changed = write_text_if_changed(SUMMARY_FILE, summary_content)

    written = unchanged = 0
    route_digests: dict[str, str] = {}
    for record, route in assigned:
        digest = route_digest(record, route)
        route_digests[route] = digest
        target_dir = OUT_DIR / route
        target = target_dir / "index.html"
        if previous_digests.get(route) == digest and target.exists():
            unchanged += 1
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        if write_text_if_changed(target, page_html(record, route)):
            written += 1
        else:
            unchanged += 1

    removed = 0
    for stale in sorted(previous - current):
        target_dir = OUT_DIR / stale
        if target_dir.is_dir() and (target_dir / "index.html").exists():
            shutil.rmtree(target_dir)
            removed += 1

    manifest = {
        "generatedFrom": "data/ipos.json",
        "publicIndex": "data/ipos-summary.json",
        "recordCount": len(records),
        "routeCount": len(current),
        "templateVersion": ROUTE_TEMPLATE_VERSION,
        "routes": sorted(current),
        "routeDigests": route_digests,
    }
    manifest_content = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    write_text_if_changed(MANIFEST, manifest_content)

    print(
        f"Company routes: records={len(records)}, routes={len(current)}, "
        f"written={written}, unchanged={unchanged}, removed={removed}, "
        f"dataRewrite={'yes' if profile_paths_changed else 'no'}, "
        f"summaryWrite={'yes' if summary_changed else 'no'}, "
        f"summaryBytes={len(summary_content.encode('utf-8'))}"
    )
    if len(current) != len(records):
        raise RuntimeError("Permanent-route count does not match IPO record count")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
