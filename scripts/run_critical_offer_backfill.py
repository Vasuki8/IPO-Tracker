#!/usr/bin/env python3
"""Safe Phase 4.5B offer-document fallback runner.

The generic critical_backfill module also handles exchange/subscription work.
For PDF extraction we use stricter selection: only a direct official PDF (or a
SEBI viewer URL whose file parameter is a PDF) is eligible. This prevents an
HTML filing landing page from ever being handed to pypdf. Parser v8 is used for
the actual extraction, including separate deep financial/shareholding page
budgets and bounded retries for truncated PDF transfers.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import critical_backfill as base  # noqa: E402
import run_offer_docs_v8 as parser_v8  # noqa: E402

# Use the v8-patched base parser for full-document fallbacks too.
base.offer = parser_v8.base


def _direct_pdf_url(url: str) -> str | None:
    raw = str(url or "").strip()
    if not raw:
        return None
    parsed = urlparse(raw)
    if parsed.path.lower().endswith(".pdf"):
        return raw
    query = parse_qs(parsed.query)
    for key in ("file", "File"):
        for value in query.get(key, []):
            target = unquote(str(value))
            if urlparse(target).path.lower().endswith(".pdf"):
                return target
    return None


def safe_choose_fallback_document(record, *, exclude_url=None):
    rank = {"PROSPECTUS": 4, "RHP": 3, "UDRHP": 2, "DRHP": 1, "DOCUMENT": 0}
    candidates = []
    for doc in record.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        original_url = str(doc.get("url") or "").strip()
        direct = _direct_pdf_url(original_url)
        if not direct or original_url == exclude_url or direct == exclude_url:
            continue
        if not base._is_official_document_url(direct):
            continue
        title = str(doc.get("title") or "")
        typ = str(doc.get("type") or base._document_type(f"{title} {direct}")).upper()
        if typ not in rank:
            continue
        clean_doc = dict(doc)
        clean_doc["url"] = direct
        abridged = int("ABRIDGED" in title.upper() or "AP_" in direct.upper())
        candidates.append((abridged, rank.get(typ, 0), str(doc.get("filedDate") or ""), len(title), clean_doc))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[:-1])[-1]


base.choose_fallback_document = safe_choose_fallback_document


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
