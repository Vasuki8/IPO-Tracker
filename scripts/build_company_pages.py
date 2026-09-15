#!/usr/bin/env python3
"""Generate clean static GitHub Pages routes for every IPO record.

Each route is tiny and loads the live record from data/ipos.json, so issue terms,
subscription history and financials stay current without rebuilding page HTML on
every data change. New company IDs get routes automatically during the core
refresh workflow.
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

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"
OUT_DIR = ROOT / "ipo"
MANIFEST = OUT_DIR / "routes.json"
ROUTE_TEMPLATE_VERSION = 2


def route_slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "ipo"


def _identity(record: dict) -> str:
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


def assign_routes(records: list[dict]) -> list[tuple[dict, str]]:
    """Assign stable clean routes and add profilePath to every record."""
    bases = [route_slug(str(row.get("id") or row.get("company") or "")) for row in records]
    counts = Counter(bases)
    used: set[str] = set()
    assigned: list[tuple[dict, str]] = []

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


def page_html(record: dict, route: str) -> str:
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

    return f'''<!doctype html>
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
      <span>Official-source IPO research tracker · not investment advice.</span>
      <a href="./">Back to all IPOs</a>
    </footer>
  </div>

  <script src="company-page.js" defer></script>
  <script src="company.js" defer></script>
</body>
</html>
'''


def load_manifest() -> dict:
    try:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def write_text_if_changed(path: Path, content: str) -> bool:
    """Write text only when bytes would actually change."""
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def route_content_digest(assigned: list[tuple[dict, str]]) -> str:
    """Digest only fields embedded in static route HTML.

    Live IPO facts are intentionally excluded because company-page.js reads them
    from data/ipos.json at runtime; changing those facts must not rebuild 1,000+
    route shells.
    """
    digest = hashlib.sha256()
    for record, route in sorted(assigned, key=lambda item: item[1]):
        fields = (
            route,
            record.get("id"),
            record.get("company"),
            record.get("symbol"),
            record.get("exchange"),
            record.get("profilePath"),
        )
        digest.update("\0".join(str(value or "") for value in fields).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos", []) if isinstance(row, dict) and row.get("id")]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    previous_manifest = load_manifest()
    previous = set(previous_manifest.get("routes") or [])
    old_profile_paths = {id(record): record.get("profilePath") for record in records}
    assigned = assign_routes(records)
    current = {route for _, route in assigned}
    profile_paths_changed = any(
        old_profile_paths[id(record)] != record.get("profilePath")
        for record, _route in assigned
    )

    # Avoid serializing/writing the 4.7 MB dataset on every refresh when route
    # assignments are unchanged.
    if profile_paths_changed:
        DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    digest = route_content_digest(assigned)
    manifest_matches = (
        previous == current
        and previous_manifest.get("templateVersion") == ROUTE_TEMPLATE_VERSION
        and previous_manifest.get("contentDigest") == digest
    )

    written = unchanged = 0
    if manifest_matches:
        # A committed manifest and route tree move together, so there is no need
        # to open and compare every generated index.html on every data refresh.
        unchanged = len(current)
    else:
        for record, route in assigned:
            target_dir = OUT_DIR / route
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / "index.html"
            content = page_html(record, route)
            if write_text_if_changed(target, content):
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
        "recordCount": len(records),
        "routeCount": len(current),
        "templateVersion": ROUTE_TEMPLATE_VERSION,
        "contentDigest": digest,
        "routes": sorted(current),
    }
    manifest_content = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    write_text_if_changed(MANIFEST, manifest_content)

    print(
        f"Company routes: records={len(records)}, routes={len(current)}, "
        f"written={written}, unchanged={unchanged}, removed={removed}, "
        f"dataRewrite={'yes' if profile_paths_changed else 'no'}"
    )
    if len(current) != len(records):
        raise RuntimeError("Permanent-route count does not match IPO record count")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
