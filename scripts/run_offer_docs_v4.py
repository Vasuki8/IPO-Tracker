#!/usr/bin/env python3
"""Phase 4.5B offer-document parser v4.

v4 keeps the quality gates from v3 and adds production hardening fixes:

* normalize modern Fresh Issue / OFS wording (including ``upto``) before
  deciding that issue composition is unavailable;
* capture explicit Fresh Issue / OFS monetary amounts when share counts are not
  present in the same summary block;
* retry transient/truncated PDF transfers instead of turning one incomplete
  HTTP read into a permanent extraction error.

Only the same direct official SEBI PDFs accepted by v3 are eligible.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_offer_docs_v3 as v3  # noqa: E402

base = v3.base
PARSER_VERSION = 4
base.PARSER_VERSION = PARSER_VERSION

_ORIGINAL_DOWNLOAD_PDF = base.download_pdf


def _share_count_near(label_pattern: str, text: str):
    """Conservatively capture a share count close to a named issue component."""
    patterns = [
        rf"{label_pattern}.{{0,320}}?(?:up\s*to\s+|upto\s+)?([\d,]{{4,}})\s+(?:fully\s+paid[-\s]?up\s+)?Equity\s+Shares",
        rf"{label_pattern}.{{0,320}}?comprising\s+(?:up\s*to\s+|upto\s+)?([\d,]{{4,}})\s+(?:fully\s+paid[-\s]?up\s+)?Equity\s+Shares",
    ]
    return base._share_count(patterns, text)


def _money_cr_near(label_pattern: str, text: str):
    """Capture an explicit rupee amount near Fresh Issue / OFS wording."""
    money = re.search(
        rf"{label_pattern}.{{0,420}}?(?:aggregat(?:e|es|ing)\s+(?:up\s*to\s+|upto\s+)?|"
        rf"for\s+an\s+amount\s+(?:up\s*to\s+)?|amounting\s+to\s+)?"
        rf"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s*"
        rf"(crores?|cr\.?|million|lakhs?|lacs?)\b",
        text,
        re.I,
    )
    if not money:
        return None
    value = base.number(money.group(1))
    if value is None:
        return None
    unit = money.group(2).lower()
    if unit.startswith("million"):
        return round(float(value) / 10.0, 4)
    if unit.startswith("lakh") or unit.startswith("lac"):
        return round(float(value) / 100.0, 4)
    return round(float(value), 4)


def extract_issue_composition(text: str, price_band=None):
    """Extend v3 with whitespace-normalized current prospectus wording."""
    issue = dict(v3.extract_issue_composition(text, price_band) or {})
    flat = base.norm_space(text)

    if issue.get("freshShares") is None:
        issue["freshShares"] = _share_count_near(r"\bFresh\s+Issue\b", flat)
    if issue.get("ofsShares") is None:
        issue["ofsShares"] = _share_count_near(r"\bOffer\s+for\s+Sale\b", flat)

    # Prefer explicit document amounts over values inferred from share count × cap
    # price. This also handles summaries that disclose only aggregate rupee values.
    explicit_fresh_cr = _money_cr_near(r"\bFresh\s+Issue\b", flat)
    explicit_ofs_cr = _money_cr_near(r"\bOffer\s+for\s+Sale\b", flat)
    if explicit_fresh_cr is not None:
        issue["freshIssueCr"] = explicit_fresh_cr
    if explicit_ofs_cr is not None:
        issue["ofsCr"] = explicit_ofs_cr

    # Explicit fresh-only wording is strong enough to record zero OFS. Merely
    # failing to find an OFS phrase is intentionally NOT treated as zero.
    fresh_only = re.search(
        r"(?:fresh\s+issue\s+only|fresh\s+issue\s+without\s+an?\s+offer\s+for\s+sale|"
        r"compris(?:e|es|ing)\s+(?:solely|only)\s+(?:of\s+)?(?:a\s+)?fresh\s+issue|"
        r"offer\s+for\s+sale.{0,100}?(?:not\s+applicable|nil|none))",
        flat,
        re.I,
    )
    if fresh_only and issue.get("ofsShares") is None:
        issue["ofsShares"] = 0
        issue["ofsCr"] = 0.0

    cap = base.number((price_band or {}).get("max")) if isinstance(price_band, dict) else issue.get("valuationPriceUsed")
    if cap:
        issue["valuationPriceUsed"] = cap

    if issue.get("freshIssueCr") is None and issue.get("freshShares") and cap:
        issue["freshIssueCr"] = round(float(issue["freshShares"]) * float(cap) / 10_000_000, 2)
    if issue.get("ofsCr") is None:
        if issue.get("ofsShares") and cap:
            issue["ofsCr"] = round(float(issue["ofsShares"]) * float(cap) / 10_000_000, 2)
        elif issue.get("ofsShares") == 0:
            issue["ofsCr"] = 0.0

    if issue.get("totalIssueSizeCr") is None:
        fresh = issue.get("freshIssueCr")
        ofs = issue.get("ofsCr")
        if fresh is not None and ofs is not None:
            issue["totalIssueSizeCr"] = round(float(fresh) + float(ofs), 4)
        elif fresh is not None and issue.get("ofsShares") == 0:
            issue["totalIssueSizeCr"] = round(float(fresh), 4)

    return issue


def download_pdf(session, url, *, attempts: int = 3, retry_delay: float = 1.0):
    """Retry transport-level PDF truncation while preserving all v3 quality gates."""
    last_error = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            return _ORIGINAL_DOWNLOAD_PDF(session, url)
        except (requests.RequestException, OSError) as exc:
            last_error = exc
            if attempt >= attempts:
                raise
            # A short bounded delay is enough for SEBI/BSE edge-node hiccups and
            # avoids turning the daily enrichment job into a long retry loop.
            time.sleep(retry_delay * attempt)
    if last_error:
        raise last_error
    raise RuntimeError("PDF download failed without an error")


# base.main()/parse_document_text resolve these functions from the base module.
base.extract_issue_composition = extract_issue_composition
base.download_pdf = download_pdf
base.PARSER_VERSION = PARSER_VERSION

parse_document_text = base.parse_document_text
apply_enrichment = base.apply_enrichment
choose_document = v3.choose_document


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
