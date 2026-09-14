#!/usr/bin/env python3
"""Quality-gated offer-document parser v2.

This wrapper keeps the battle-tested Phase 3 parser intact and adds conservative
fallbacks for newer SEBI Abridged Prospectus wording. Existing exchange values
still win; the underlying apply_enrichment() only fills missing issue totals.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from parser_loader import isolated_module
base = isolated_module("enrich_offer_docs")

PARSER_VERSION = 2
base.PARSER_VERSION = PARSER_VERSION

_v1_intermediaries = base.extract_intermediaries
_v1_promoters = base.extract_promoters
_v1_issue = base.extract_issue_composition
_v1_financials = base.extract_financials
_v1_objects = base.extract_objects
_v1_shareholding = base.extract_promoter_shareholding


def _first_entity(block: str):
    entities = base._legal_entities(block)
    return entities[0] if entities else None


def extract_intermediaries(text: str):
    leads, registrar = _v1_intermediaries(text)
    if not leads:
        block = base.section(
            text,
            [
                r"BOOK\s+RUNNING\s+LEAD\s+MANAGER(?:S)?\s+(?:TO\s+THE\s+)?(?:ISSUE|OFFER)",
                r"BOOK\s+RUNNING\s+LEAD\s+MANAGER(?:S)?",
                r"BRLM(?:S)?\s+(?:TO\s+THE\s+)?(?:ISSUE|OFFER)",
            ],
            [
                r"REGISTRAR\s+TO\s+THE\s+(?:ISSUE|OFFER)",
                r"ISSUE\s+OPENS?",
                r"BID\s*/?\s*ISSUE\s+PERIOD",
            ],
            3500,
        )
        leads = base._legal_entities(block)
    if not registrar:
        block = base.section(
            text,
            [
                r"REGISTRAR\s+TO\s+THE\s+(?:ISSUE|OFFER)",
                r"REGISTRAR\s+AND\s+SHARE\s+TRANSFER\s+AGENT",
            ],
            [
                r"BID\s*/?\s*ISSUE\s+PERIOD",
                r"ISSUE\s+OPENS?",
                r"BOOK\s+RUNNING",
                r"SYNDICATE",
            ],
            2200,
        )
        registrar = _first_entity(block)
    leads = [re.sub(r"^TO THE (?:ISSUE|OFFER)\s+", "", x, flags=re.I) for x in leads]
    return leads, registrar


def extract_promoters(text: str):
    promoters = _v1_promoters(text)
    if promoters:
        return promoters

    block = base.section(
        text,
        [
            r"\bOUR\s+PROMOTERS?\b",
            r"\bPROMOTERS?\s+OF\s+THE\s+COMPANY\b",
            r"\bPROMOTER\s+DETAILS\b",
        ],
        [
            r"DETAILS\s+OF\s+THE\s+(?:ISSUE|OFFER)",
            r"OBJECTS\s+OF\s+THE\s+(?:ISSUE|OFFER)",
            r"ISSUE\s+DETAILS",
        ],
        1800,
    )
    if block:
        lines = [base.norm_space(line) for line in block.splitlines() if base.norm_space(line)]
        for line in lines[:6]:
            candidate = re.sub(r"^(?:Our\s+Promoters?\s+(?:are|is)\s*[:\-]?\s*)", "", line, flags=re.I)
            if len(candidate) > 400:
                continue
            parts = re.split(r"\s*,\s*|\s+\band\b\s+|\s*;\s*", candidate, flags=re.I)
            names = [base.clean_name(part) for part in parts]
            names = [name for name in names if 2 <= len(name) <= 120 and not re.search(r"promoter|company|details", name, re.I)]
            if 1 <= len(names) <= 12:
                return base.dedupe(names)

    match = re.search(
        r"Our\s+Promoters?\s+(?:are|is)\s*[:\-]?\s*(.+?)(?:\.|\n)",
        text,
        re.I | re.S,
    )
    if match:
        parts = re.split(r"\s*,\s*|\s+\band\b\s+", base.norm_space(match.group(1)), flags=re.I)
        return base.dedupe([base.clean_name(x) for x in parts if 2 <= len(base.clean_name(x)) <= 120])[:12]
    return []


def _explicit_money_after(label_pattern: str, text: str):
    patterns = [
        rf"{label_pattern}.{{0,260}}?aggregat(?:ing|es|e)\s+(?:up\s+to\s+|to\s+|approximately\s+)?(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s*(crore|crores|cr\.?|million|lakh|lakhs|lac|lacs)",
        rf"{label_pattern}.{{0,180}}?(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s*(crore|crores|cr\.?|million|lakh|lakhs|lac|lacs)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I | re.S)
        if not match:
            continue
        unit_word = match.group(2).lower()
        unit = "million" if "million" in unit_word else "lakh" if "lakh" in unit_word or "lac" in unit_word else "crore"
        return base.to_crore(base.number(match.group(1)), unit)
    return None


def extract_issue_composition(text: str, price_band=None):
    issue = dict(_v1_issue(text, price_band) or {})
    block = base.section(
        text,
        [r"DETAILS\s+OF\s+THE\s+(?:ISSUE|OFFER)", r"ISSUE\s+DETAILS", r"OFFER\s+DETAILS"],
        [r"RISKS?\s+IN\s+RELATION", r"GENERAL\s+RISK", r"OBJECTS\s+OF\s+THE", r"LISTING"],
        8000,
    ) or text[:14000]

    if issue.get("freshShares") is None:
        issue["freshShares"] = base._share_count(
            [
                r"Fresh\s+Issue\s*(?:of|:|–|-)?.{0,100}?([\d,]+)\s+Equity\s+Shares",
                r"Fresh\s+Issue.{0,180}?comprising\s+([\d,]+)\s+Equity\s+Shares",
                r"Issue\s+of\s+up\s+to\s+([\d,]+)\s+new\s+Equity\s+Shares",
            ],
            block,
        )
    if issue.get("ofsShares") is None:
        issue["ofsShares"] = base._share_count(
            [
                r"Offer\s+for\s+Sale\s*(?:of|:|–|-)?.{0,100}?([\d,]+)\s+Equity\s+Shares",
                r"Offer\s+for\s+Sale.{0,180}?comprising\s+([\d,]+)\s+Equity\s+Shares",
            ],
            block,
        )

    if re.search(r"(?:OFFER\s+FOR\s+SALE|OFS).{0,120}?(?:NOT\s+APPLICABLE|NIL|NONE)", block, re.I | re.S):
        issue["ofsShares"] = 0
        issue["ofsCr"] = 0.0

    cap = base.number((price_band or {}).get("max")) if isinstance(price_band, dict) else issue.get("valuationPriceUsed")
    if cap:
        issue["valuationPriceUsed"] = cap
    if issue.get("freshIssueCr") is None:
        if issue.get("freshShares") and cap:
            issue["freshIssueCr"] = round(issue["freshShares"] * cap / 10_000_000, 2)
        else:
            issue["freshIssueCr"] = _explicit_money_after(r"Fresh\s+Issue", block)
    if issue.get("ofsCr") is None:
        if issue.get("ofsShares") and cap:
            issue["ofsCr"] = round(issue["ofsShares"] * cap / 10_000_000, 2)
        elif issue.get("ofsShares") == 0:
            issue["ofsCr"] = 0.0
        else:
            issue["ofsCr"] = _explicit_money_after(r"Offer\s+for\s+Sale", block)

    # Explicit disclosed amounts take precedence over cap-price estimates.
    for key, label in (("freshIssueCr", r"Fresh\s+Issue"), ("ofsCr", r"Offer\s+for\s+Sale"), ("totalIssueSizeCr", r"(?:Total\s+Issue(?:\s+Size)?|Total\s+Offer(?:\s+Size)?|Issue\s+Size)")):
        explicit = _explicit_money_after(label, block)
        if explicit is not None:
            issue[key] = explicit

    if issue.get("totalIssueSizeCr") is None:
        fresh = issue.get("freshIssueCr")
        ofs = issue.get("ofsCr")
        if fresh is not None and ofs is not None:
            issue["totalIssueSizeCr"] = round(float(fresh) + float(ofs), 4)
        else:
            total = _explicit_money_after(r"(?:Total\s+Issue|Total\s+Offer|Issue\s+Size|Offer\s+Size)", block)
            if total is not None:
                issue["totalIssueSizeCr"] = total
    return issue


def _fallback_financial_block(text: str):
    return base.section(
        text,
        [
            r"Summary\s+of\s+(?:Restated\s+)?(?:Consolidated\s+|Standalone\s+)?Financial\s+Information",
            r"Restated\s+(?:Consolidated\s+|Standalone\s+)?Financial\s+Information",
            r"Financial\s+Information\s+of\s+the\s+Company",
        ],
        [
            r"Summary\s+of\s+Key\s+Performance",
            r"Key\s+Performance\s+Indicators",
            r"\bRisk\s+Factors\b",
            r"OBJECTS\s+OF\s+THE",
        ],
        10000,
    )


def extract_financials(text: str):
    existing = _v1_financials(text)
    block = _fallback_financial_block(text)
    kpi = base.section(
        text,
        [r"Summary\s+of\s+Key\s+Performance\s+Indicators", r"Key\s+Performance\s+Indicators(?:\s*\(KPIs?\))?"],
        [r"\bRisk\s+Factors\b", r"Details\s+of\s+the\s+weighted", r"OBJECTS\s+OF\s+THE"],
        8000,
    )
    if not block and existing:
        return existing
    combined = (block or "") + "\n" + (kpi or "")
    if not combined.strip():
        return existing

    years = re.findall(r"\b(?:Fiscal|FY)\s*(20\d{2})\b", combined, re.I)
    if not years:
        years = re.findall(r"(?:March\s+31|31\s+March)[,\s]+(20\d{2})", combined, re.I)
    if not years:
        # Table headers often contain bare years. Limit to the first four unique
        # recent years within the financial section only.
        years = re.findall(r"\b(20[12]\d)\b", combined)
    years = base.dedupe(years)[:4]
    if not years:
        return existing

    lines = combined.splitlines()
    unit = base.detect_money_unit(block or kpi)
    series = {
        "revenueCr": base._series_line(lines, [r"Revenue\s+from\s+Operations", r"Total\s+(?:Revenue|Income)"], years),
        "ebitdaCr": base._series_line(lines, [r"\bEBITDA\b(?!\s+Margin)", r"Operating\s+EBITDA"], years),
        "patCr": base._series_line(lines, [r"Profit\s+(?:after\s+Tax|for\s+the\s+(?:year|period))(?:\s*\(PAT\))?", r"Net\s+Profit\s+after\s+tax"], years),
        "netWorthCr": base._series_line(lines, [r"^Net\s+Worth\b", r"Networth\b"], years),
        "ronwPct": base._series_line(lines, [r"Return\s+on\s+Net\s+Worth", r"RoNW\b"], years),
        "roePct": base._series_line(lines, [r"Return\s+on\s+Equity", r"\bROE\b"], years),
        "eps": base._series_line(lines, [r"(?:Basic\s+and\s+Diluted\s+)?Earnings\s+per\s+Share", r"\bBasic\s+EPS\b", r"Diluted\s+EPS"], years),
    }

    periods = []
    old_by_period = {row.get("period"): row for row in ((existing or {}).get("periods") or [])}
    for idx, year in enumerate(years):
        period = f"FY{year}"
        row = dict(old_by_period.get(period) or {"period": period})
        for key, values in series.items():
            if key in row or idx >= len(values):
                continue
            value = values[idx]
            row[key] = base.to_crore(value, unit) if key.endswith("Cr") else value
        if len(row) > 1:
            periods.append(row)
    if periods:
        return {"unit": "₹ crore", "periods": periods}
    return existing


def extract_objects(text: str):
    existing = _v1_objects(text)
    if existing:
        return existing
    block = base.section(
        text,
        [
            r"\bObjects\s+of\s+the\s+(?:Issue|Offer)\b",
            r"\bObjects\s+of\s+the\s+Fresh\s+Issue\b",
            r"\bUtilisation\s+of\s+(?:Net\s+)?Proceeds\b",
        ],
        [
            r"Pre\s+and\s+Post[-\s]?Issue",
            r"Summary\s+of\s+Restated",
            r"Financial\s+Information",
            r"\bRisk\s+Factors\b",
        ],
        8000,
    )
    if not block:
        return []
    unit = base.detect_money_unit(block)
    out = []
    for raw in block.splitlines():
        line = base.norm_space(raw)
        if not line or len(line) < 6 or re.search(r"^(?:Particulars|Amount|Total|Grand\s+Total|Note|For\s+further)", line, re.I):
            continue
        match = re.match(r"(?:\d+[.)]\s*)?(.+?)\s+((?:[\d,]+(?:\.\d+)?)|\[.?●.?\]|NA|N/?A)\s*$", line, re.I)
        if not match:
            continue
        purpose = base.clean_name(match.group(1))
        token = match.group(2)
        amount = None if "●" in token or re.fullmatch(r"N/?A", token, re.I) else base.to_crore(base.number(token), unit)
        if len(purpose) >= 5:
            out.append({"purpose": purpose, "amountCr": amount})
    return out[:12]


def extract_promoter_shareholding(text: str):
    existing = _v1_shareholding(text)
    if existing:
        return existing
    block = base.section(
        text,
        [
            r"Pre[-\s]?Issue\s+Shareholding\s+of\s+(?:our\s+)?Promoters?",
            r"Shareholding\s+of\s+(?:the\s+)?Promoters?.{0,40}?Pre[-\s]?Issue",
            r"Pre\s+and\s+Post[-\s]?Issue\s+shareholding",
        ],
        [r"Summary\s+of\s+Restated", r"Financial\s+Information", r"Key\s+Performance"],
        7000,
    )
    if not block:
        return None
    aggregate = re.search(
        r"Promoters?\s+(?:and\s+Promoter\s+Group)?.{0,260}?([0-9]+(?:\.[0-9]+)?)\s*%",
        block,
        re.I | re.S,
    )
    if aggregate:
        pct = base.number(aggregate.group(1))
        if pct is not None and 0 <= pct <= 100:
            return {"promoters": [], "promoterPreIssuePct": pct}
    return None


# Patch the base module globals used by parse_document_text() and main().
base.extract_intermediaries = extract_intermediaries
base.extract_promoters = extract_promoters
base.extract_issue_composition = extract_issue_composition
base.extract_financials = extract_financials
base.extract_objects = extract_objects
base.extract_promoter_shareholding = extract_promoter_shareholding

# Re-export helpers so tests/importers can use this module like the base parser.
parse_document_text = base.parse_document_text
choose_document = base.choose_document
apply_enrichment = base.apply_enrichment


def main():
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
