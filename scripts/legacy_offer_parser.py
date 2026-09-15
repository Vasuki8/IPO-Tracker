"""Canonical legacy offer-document parser retained for issuer fallbacks.

This module flattens the final behavior of the former run_offer_docs_v2-v14
wrapper chain into one explicit implementation. Parser version 14 is retained
for provenance compatibility. New production repair work uses offer_parser
(v21); this module exists for issuer/document fallback paths and for the small
set of conservative recognizers that v21 still reuses.
"""
from __future__ import annotations

import io
import re
import time
from urllib.parse import urlparse

import requests
from pypdf import PdfReader

import enrich_offer_docs as base

PARSER_VERSION = 14
DATA_FILE = base.DATA_FILE
HEADERS = base.HEADERS
MAX_PDF_BYTES = base.MAX_PDF_BYTES
now_ist = base.now_ist
priority = base.priority


def _first_entity(block: str):
    entities = base._legal_entities(block)
    return entities[0] if entities else None


def extract_intermediaries(text: str):
    """Final legacy intermediary recognizer (v2 + v3 normalization)."""
    leads, registrar = base.extract_intermediaries(text)
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

    def clean(value):
        if not value:
            return value
        value = re.sub(r"^(?:TO\s+THE\s+(?:OFFER|ISSUE)\s+)+", "", str(value).strip(), flags=re.I)
        return base.clean_name(value)

    leads = base.dedupe([value for value in (clean(item) for item in leads) if value])
    return leads, clean(registrar)


def extract_promoters(text: str):
    promoters = base.extract_promoters(text)
    if promoters:
        return promoters
    block = base.section(
        text,
        [r"\bOUR\s+PROMOTERS?\b", r"\bPROMOTERS?\s+OF\s+THE\s+COMPANY\b", r"\bPROMOTER\s+DETAILS\b"],
        [r"DETAILS\s+OF\s+THE\s+(?:ISSUE|OFFER)", r"OBJECTS\s+OF\s+THE\s+(?:ISSUE|OFFER)", r"ISSUE\s+DETAILS"],
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
    match = re.search(r"Our\s+Promoters?\s+(?:are|is)\s*[:\-]?\s*(.+?)(?:\.|\n)", text, re.I | re.S)
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
        if match:
            word = match.group(2).lower()
            unit = "million" if "million" in word else "lakh" if "lakh" in word or "lac" in word else "crore"
            return base.to_crore(base.number(match.group(1)), unit)
    return None


def _share_count_near(label_pattern: str, text: str):
    return base._share_count(
        [
            rf"{label_pattern}.{{0,320}}?(?:up\s*to\s+|upto\s+)?([\d,]{{4,}})\s+(?:fully\s+paid[-\s]?up\s+)?Equity\s+Shares",
            rf"{label_pattern}.{{0,320}}?comprising\s+(?:up\s*to\s+|upto\s+)?([\d,]{{4,}})\s+(?:fully\s+paid[-\s]?up\s+)?Equity\s+Shares",
        ],
        text,
    )


def _money_cr_near(label_pattern: str, text: str):
    match = re.search(
        rf"{label_pattern}.{{0,420}}?(?:aggregat(?:e|es|ing)\s+(?:up\s*to\s+|upto\s+)?|for\s+an\s+amount\s+(?:up\s+to\s+)?|amounting\s+to\s+)?(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s*(crores?|cr\.?|million|lakhs?|lacs?)\b",
        text,
        re.I,
    )
    if not match:
        return None
    value = base.number(match.group(1))
    if value is None:
        return None
    unit = match.group(2).lower()
    if unit.startswith("million"):
        return round(float(value) / 10.0, 4)
    if unit.startswith("lakh") or unit.startswith("lac"):
        return round(float(value) / 100.0, 4)
    return round(float(value), 4)


def extract_issue_composition(text: str, price_band=None):
    """Final legacy issue-composition recognizer (effective v4 behavior)."""
    issue = dict(base.extract_issue_composition(text, price_band) or {})
    block = base.section(
        text,
        [r"DETAILS\s+OF\s+THE\s+(?:ISSUE|OFFER)", r"ISSUE\s+DETAILS", r"OFFER\s+DETAILS"],
        [r"RISKS?\s+IN\s+RELATION", r"GENERAL\s+RISK", r"OBJECTS\s+OF\s+THE", r"LISTING"],
        9000,
    ) or text[:16000]

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
        issue["freshIssueCr"] = round(issue["freshShares"] * cap / 10_000_000, 2) if issue.get("freshShares") and cap else _explicit_money_after(r"Fresh\s+Issue", block)
    if issue.get("ofsCr") is None:
        if issue.get("ofsShares") and cap:
            issue["ofsCr"] = round(issue["ofsShares"] * cap / 10_000_000, 2)
        elif issue.get("ofsShares") == 0:
            issue["ofsCr"] = 0.0
        else:
            issue["ofsCr"] = _explicit_money_after(r"Offer\s+for\s+Sale", block)

    for key, label in (
        ("freshIssueCr", r"Fresh\s+Issue"),
        ("ofsCr", r"Offer\s+for\s+Sale"),
        ("totalIssueSizeCr", r"(?:Total\s+Issue(?:\s+Size)?|Total\s+Offer(?:\s+Size)?|Issue\s+Size|Offer\s+Size)"),
    ):
        explicit = _explicit_money_after(label, block)
        if explicit is not None:
            issue[key] = explicit

    flat = base.norm_space(text)
    if issue.get("freshShares") is None:
        issue["freshShares"] = _share_count_near(r"\bFresh\s+Issue\b", flat)
    if issue.get("ofsShares") is None:
        issue["ofsShares"] = _share_count_near(r"\bOffer\s+for\s+Sale\b", flat)
    explicit_fresh = _money_cr_near(r"\bFresh\s+Issue\b", flat)
    explicit_ofs = _money_cr_near(r"\bOffer\s+for\s+Sale\b", flat)
    if explicit_fresh is not None:
        issue["freshIssueCr"] = explicit_fresh
    if explicit_ofs is not None:
        issue["ofsCr"] = explicit_ofs

    fresh_only = re.search(
        r"(?:fresh\s+issue\s+only|fresh\s+issue\s+without\s+an?\s+offer\s+for\s+sale|compris(?:e|es|ing)\s+(?:solely|only)\s+(?:of\s+)?(?:a\s+)?fresh\s+issue|offer\s+for\s+sale.{0,100}?(?:not\s+applicable|nil|none))",
        flat,
        re.I,
    )
    if fresh_only and issue.get("ofsShares") is None:
        issue["ofsShares"] = 0
        issue["ofsCr"] = 0.0

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
        fresh, ofs = issue.get("freshIssueCr"), issue.get("ofsCr")
        if fresh is not None and ofs is not None:
            issue["totalIssueSizeCr"] = round(float(fresh) + float(ofs), 4)
        elif fresh is not None and issue.get("ofsShares") == 0:
            issue["totalIssueSizeCr"] = round(float(fresh), 4)
    return issue


def _extract_financials_v2(text: str):
    existing = base.extract_financials(text)
    block = base.section(
        text,
        [r"Summary\s+of\s+(?:Restated\s+)?(?:Consolidated\s+|Standalone\s+)?Financial\s+Information", r"Restated\s+(?:Consolidated\s+|Standalone\s+)?Financial\s+Information", r"Financial\s+Information\s+of\s+the\s+Company"],
        [r"Summary\s+of\s+Key\s+Performance", r"Key\s+Performance\s+Indicators", r"\bRisk\s+Factors\b", r"OBJECTS\s+OF\s+THE"],
        10000,
    )
    kpi = base.section(text, [r"Summary\s+of\s+Key\s+Performance\s+Indicators", r"Key\s+Performance\s+Indicators(?:\s*\(KPIs?\))?"], [r"\bRisk\s+Factors\b", r"Details\s+of\s+the\s+weighted", r"OBJECTS\s+OF\s+THE"], 8000)
    if not block and existing:
        return existing
    combined = (block or "") + "\n" + (kpi or "")
    if not combined.strip():
        return existing
    years = re.findall(r"\b(?:Fiscal|FY)\s*(20\d{2})\b", combined, re.I)
    if not years:
        years = re.findall(r"(?:March\s+31|31\s+March)[,\s]+(20\d{2})", combined, re.I)
    if not years:
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
    old = {row.get("period"): row for row in ((existing or {}).get("periods") or [])}
    for idx, year in enumerate(years):
        period = f"FY{year}"
        row = dict(old.get(period) or {"period": period})
        for key, values in series.items():
            if key not in row and idx < len(values):
                row[key] = base.to_crore(values[idx], unit) if key.endswith("Cr") else values[idx]
        if len(row) > 1:
            periods.append(row)
    return {"unit": "₹ crore", "periods": periods} if periods else existing


_FINANCIAL_SECTION_MARKER = re.compile(
    r"(?:summary\s+of\s+(?:restated\s+)?(?:consolidated\s+|standalone\s+)?financial\s+information|summary\s+of\s+financial\s+information|restated\s+(?:consolidated\s+|standalone\s+)?financial\s+information|statement\s+of\s+restated\s+financial\s+information|financial\s+information\s+of\s+(?:our\s+)?(?:company|the\s+company)|key\s+financial\s+information|key\s+performance\s+indicators?)",
    re.I,
)
_FINANCIAL_METRICS = {
    "revenueCr": [r"Revenue\s+from\s+Operations", r"Total\s+(?:Revenue|Income)", r"Revenue\s+from\s+operation"],
    "ebitdaCr": [r"\bEBITDA\b(?!\s+Margin)", r"Operating\s+EBITDA", r"Earnings\s+before\s+Interest,\s*Tax,\s*Depreciation\s+and\s+Amortisation"],
    "patCr": [r"Profit\s+(?:after\s+Tax|for\s+the\s+(?:year|period))(?:\s*\(PAT\))?", r"Net\s+Profit\s+after\s+tax", r"Profit\s+after\s+taxation"],
    "netWorthCr": [r"\bNet\s+Worth\b", r"\bNetworth\b"],
    "ronwPct": [r"Return\s+on\s+Net\s+Worth", r"\bRoNW\b", r"Return\s+on\s+Networth"],
    "roePct": [r"Return\s+on\s+Equity", r"\bROE\b"],
    "eps": [r"(?:Basic\s+and\s+Diluted\s+)?Earnings\s+per\s+Share", r"\bBasic\s+EPS\b", r"Diluted\s+EPS"],
}
_METRIC_UNION = re.compile("|".join(rf"(?:{p})" for pats in _FINANCIAL_METRICS.values() for p in pats), re.I)
_SHAREHOLDING_PAGE_MARKER = re.compile(r"(?:pre[-\s]?(?:issue|offer|ipo)\s+shareholding|pre[-\s]?and[-\s]?post[-\s]?(?:issue|offer)\s+shareholding|shareholding\s+pattern|capital\s+structure|promoters?\s+(?:and|&|/)\s+promoter\s+group)", re.I)
_PRE_CONTEXT = re.compile(r"(?:pre[-\s]?(?:issue|offer|ipo)|before\s+the\s+(?:issue|offer)|prior\s+to\s+the\s+(?:issue|offer))", re.I)
_PROMOTER_GROUP_LABEL = r"(?:Promoters?(?:\s*(?:and|&|/)\s*Promoter\s+Group)?|Promoter\s+Group)"


def _financial_years(block: str):
    years = []
    for pattern in (r"\b(?:Fiscal|FY)\s*(20\d{2})\b", r"(?:March\s+31|31\s+March)[,\s]+(20\d{2})", r"(?:year|fiscal\s+year)\s+ended.{0,45}?\b(20\d{2})\b"):
        for year in re.findall(pattern, block, re.I | re.S):
            if year not in years:
                years.append(year)
    if len(years) < 2:
        heading = _FINANCIAL_SECTION_MARKER.search(block)
        start = heading.start() if heading else 0
        for year in re.findall(r"\b(20[12]\d)\b", block[start:start + 2600]):
            if year not in years:
                years.append(year)
    return years[:4]


def _financial_window_score(block: str):
    metric_hits = sum(1 for pats in _FINANCIAL_METRICS.values() if any(re.search(p, block, re.I) for p in pats))
    return len(_FINANCIAL_SECTION_MARKER.findall(block)) * 5 + metric_hits * 4 + min(len(_financial_years(block)), 4) * 3 + min(len(base._numeric_tokens(block)) // 12, 5)


def _financial_windows(text: str):
    windows = []
    for match in _FINANCIAL_SECTION_MARKER.finditer(text):
        block = text[max(0, match.start() - 300):min(len(text), match.start() + 14000)]
        windows.append((_financial_window_score(block), match.start(), block))
    windows.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected, seen = [], set()
    for score, _pos, block in windows:
        fingerprint = re.sub(r"\s+", " ", block[:220]).casefold()
        if score <= 0 or fingerprint in seen:
            continue
        seen.add(fingerprint)
        selected.append(block)
        if len(selected) >= 8:
            break
    return selected


def _series_near_label(block: str, patterns, period_count: int):
    combined = re.compile("|".join(rf"(?:{pattern})" for pattern in patterns), re.I)
    for match in combined.finditer(block):
        tail = block[match.end():match.end() + 950]
        next_metric = _METRIC_UNION.search(tail)
        if next_metric and next_metric.start() > 12:
            tail = tail[:next_metric.start()]
        values = base._numeric_tokens(tail)
        if len(values) >= period_count:
            return values[:period_count]
    return []


def _merge_financials(existing, incoming):
    if not incoming:
        return existing
    if not existing:
        return incoming
    periods = {str(row.get("period")): dict(row) for row in (existing.get("periods") or []) if isinstance(row, dict) and row.get("period")}
    for row in incoming.get("periods") or []:
        if not isinstance(row, dict) or not row.get("period"):
            continue
        target = periods.setdefault(str(row["period"]), {"period": str(row["period"])})
        for key, value in row.items():
            if key != "period" and target.get(key) is None and value is not None:
                target[key] = value
    return {"unit": "₹ crore", "periods": list(periods.values())} if periods else existing


def _extract_financials_v5(text: str):
    existing = _extract_financials_v2(text)
    best, best_score = None, -1
    for block in _financial_windows(text):
        years = _financial_years(block)
        if len(years) < 2:
            continue
        series = {key: _series_near_label(block, patterns, len(years)) for key, patterns in _FINANCIAL_METRICS.items()}
        populated = {key: values for key, values in series.items() if len(values) >= len(years)}
        if len(populated) < 2:
            continue
        unit = base.detect_money_unit(block)
        periods = []
        for idx, year in enumerate(years):
            row = {"period": f"FY{year}"}
            for key, values in populated.items():
                value = values[idx]
                row[key] = base.to_crore(value, unit) if key.endswith("Cr") else value
            periods.append(row)
        score = len(populated) * 10 + _financial_window_score(block)
        if score > best_score:
            best_score, best = score, {"unit": "₹ crore", "periods": periods}
    return _merge_financials(existing, best)


def extract_financials(text: str):
    """Final legacy financial recognizer (effective v6 behavior)."""
    existing = _extract_financials_v5(text)
    aliases = dict(_FINANCIAL_METRICS)
    aliases["patCr"] = [*aliases["patCr"], r"Profit\s*/?\s*\(?Loss\)?\s+After\s+Tax", r"\bPAT\b(?!\s+Margin)", r"Profit\s+after\s+taxation"]
    aliases["revenueCr"] = [*aliases["revenueCr"], r"Revenue\s+from\s+operations?", r"\bRevenue\b"]
    best, best_score = None, -1
    for block in _financial_windows(text):
        years = _financial_years(block)
        if len(years) < 2:
            continue
        series = {key: _series_near_label(block, patterns, len(years)) for key, patterns in aliases.items()}
        populated = {key: values for key, values in series.items() if len(values) >= len(years)}
        if len(populated) < 2:
            continue
        unit = base.detect_money_unit(block)
        periods = []
        for idx, year in enumerate(years):
            row = {"period": f"FY{year}"}
            for key, values in populated.items():
                value = values[idx]
                row[key] = base.to_crore(value, unit) if key.endswith("Cr") else value
            periods.append(row)
        score = len(populated) * 10 + _financial_window_score(block)
        if score > best_score:
            best_score, best = score, {"unit": "₹ crore", "periods": periods}
    return _merge_financials(existing, best)


def extract_objects(text: str):
    existing = base.extract_objects(text)
    if existing:
        return existing
    block = base.section(
        text,
        [r"\bObjects\s+of\s+the\s+(?:Issue|Offer)\b", r"\bObjects\s+of\s+the\s+Fresh\s+Issue\b", r"\bUtilisation\s+of\s+(?:Net\s+)?Proceeds\b"],
        [r"Pre\s+and\s+Post[-\s]?Issue", r"Summary\s+of\s+Restated", r"Financial\s+Information", r"\bRisk\s+Factors\b"],
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


def _valid_pct(value):
    pct = base.number(value)
    if pct is None:
        return None
    pct = float(pct)
    return pct if 0 <= pct <= 100 else None


def _shareholding_v2(text: str):
    existing = base.extract_promoter_shareholding(text)
    if existing:
        return existing
    block = base.section(
        text,
        [r"Pre[-\s]?Issue\s+Shareholding\s+of\s+(?:our\s+)?Promoters?", r"Shareholding\s+of\s+(?:the\s+)?Promoters?.{0,40}?Pre[-\s]?Issue", r"Pre\s+and\s+Post[-\s]?Issue\s+shareholding"],
        [r"Summary\s+of\s+Restated", r"Financial\s+Information", r"Key\s+Performance"],
        7000,
    )
    if not block:
        return None
    aggregate = re.search(r"Promoters?\s+(?:and\s+Promoter\s+Group)?.{0,260}?([0-9]+(?:\.[0-9]+)?)\s*%", block, re.I | re.S)
    if aggregate:
        pct = _valid_pct(aggregate.group(1))
        if pct is not None:
            return {"promoters": [], "promoterPreIssuePct": pct}
    return None


def _shareholding_v4(text: str):
    existing = _shareholding_v2(text)
    if existing:
        return existing
    flat = re.sub(r"\s+", " ", base.norm_space(text)).strip()
    markers = [r"Promoters?\s+(?:and|&)\s+Promoter\s+Group", r"Promoters?\s+Shareholding", r"Shareholding\s+Pattern", r"Pre[-\s]?(?:Issue|Offer|IPO)"]
    windows = []
    for marker in markers:
        for match in re.finditer(marker, flat, re.I):
            windows.append(flat[max(0, match.start() - 500):min(len(flat), match.end() + 2200)])
            if len(windows) >= 12:
                break
        if len(windows) >= 12:
            break
    pre_context = r"(?:pre[-\s]?(?:issue|offer|ipo)|before\s+the\s+(?:issue|offer)|prior\s+to\s+the\s+(?:issue|offer))"
    promoter_label = r"(?:Promoters?(?:\s+(?:and|&)\s+Promoter\s+Group)?|Promoter\s+Group)"
    for block in windows:
        if not re.search(pre_context, block, re.I):
            continue
        row = re.search(rf"{promoter_label}\s*[:\-]?\s+(?:[\d,]+\s+)?([0-9]+(?:\.[0-9]+)?)\s*%(?:\s+(?:[\d,]+\s+)?([0-9]+(?:\.[0-9]+)?)\s*%)?", block, re.I)
        if row:
            pct = _valid_pct(row.group(1))
            if pct is not None:
                return {"promoters": [], "promoterPreIssuePct": pct}
        sentence = re.search(rf"{promoter_label}.{{0,320}}?(?:hold|holds|holding|constitut(?:e|es|ing)).{{0,220}}?([0-9]+(?:\.[0-9]+)?)\s*%\s+(?:of\s+)?(?:our\s+|the\s+)?{pre_context}", block, re.I)
        if sentence:
            pct = _valid_pct(sentence.group(1))
            if pct is not None:
                return {"promoters": [], "promoterPreIssuePct": pct}
    return None


def _shareholding_v5(text: str):
    existing = _shareholding_v4(text)
    if existing:
        return existing
    flat = re.sub(r"\s+", " ", base.norm_space(text)).strip()
    windows = [flat[max(0, m.start() - 700):m.start() + 3200] for m in _SHAREHOLDING_PAGE_MARKER.finditer(flat)][:18]
    for block in windows:
        if not _PRE_CONTEXT.search(block):
            continue
        header = re.search(r"(?:pre[-\s]?(?:issue|offer|ipo).{0,100}?(?:%|percentage)|(?:%|percentage).{0,100}?pre[-\s]?(?:issue|offer|ipo))", block, re.I)
        if header:
            row = re.search(rf"{_PROMOTER_GROUP_LABEL}\s*[:\-]?\s+([\d,]{{4,}})\s+([0-9]+(?:\.[0-9]+)?)(?:\s*%|\s+(?:[\d,]{{4,}}\s+)?[0-9]+(?:\.[0-9]+)?\s*%?)", block, re.I)
            if row:
                pct = _valid_pct(row.group(2))
                if pct is not None:
                    return {"promoters": [], "promoterPreIssuePct": pct}
        narrative = re.search(rf"{_PROMOTER_GROUP_LABEL}.{{0,360}}?(?:hold|holds|holding|held|represent(?:s|ed|ing)?|constitut(?:e|es|ed|ing)|aggregate\s+shareholding).{{0,240}}?([0-9]+(?:\.[0-9]+)?)\s*%\s+(?:of\s+)?(?:our\s+|the\s+)?(?:pre[-\s]?(?:issue|offer|ipo)|before\s+the\s+(?:issue|offer)|prior\s+to\s+the\s+(?:issue|offer))", block, re.I)
        if narrative:
            pct = _valid_pct(narrative.group(1))
            if pct is not None:
                return {"promoters": [], "promoterPreIssuePct": pct}
    return None


def _shareholding_score(block: str):
    pct_count = len(re.findall(r"\b(?:100(?:\.0+)?|\d{1,2}(?:\.\d+)?)\s*%", block))
    numeric_count = len(re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", block))
    return (12 if _PRE_CONTEXT.search(block) else 0) + (8 if re.search(_PROMOTER_GROUP_LABEL, block, re.I) else 0) + min(pct_count, 8) * 2 + min(numeric_count // 8, 6) + (5 if re.search(r"(?:grand\s+total|sub\s*total|collectively|in\s+aggregate|promoter\s+holding)", block, re.I) else 0)


def _ranked_shareholding_windows(text: str):
    flat = re.sub(r"\s+", " ", base.norm_space(text)).strip()
    marker = re.compile(r"(?:pre[-\s]?(?:issue|offer|ipo)\s+shareholding|shareholding\s+(?:of\s+)?(?:our\s+)?promoters?|promoters?\s+(?:and|&|/)\s+promoter\s+group|shareholding\s+pattern|capital\s+structure|promoter\s+holding)", re.I)
    candidates = []
    for match in marker.finditer(flat):
        block = flat[max(0, match.start() - 900):min(len(flat), match.start() + 4200)]
        candidates.append((_shareholding_score(block), match.start(), block))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    out, seen = [], set()
    for score, _pos, block in candidates:
        fp = block[:260].casefold()
        if score < 20 or fp in seen:
            continue
        seen.add(fp)
        out.append(block)
        if len(out) >= 14:
            break
    return out


def _shareholding_v6(text: str):
    existing = _shareholding_v5(text)
    if existing:
        return existing
    promoter_label = r"Promoters?(?:\s*(?:and|&|/)\s*Promoter\s+Group)?"
    for block in _ranked_shareholding_windows(text):
        if not _PRE_CONTEXT.search(block):
            continue
        patterns = [
            rf"{promoter_label}.{{0,420}}?(?:collectively\s+)?(?:hold|holds|holding|held).{{0,320}}?(?:aggregat(?:e|es|ing)\s+(?:to\s+)?|represent(?:s|ing)?\s+|constitut(?:e|es|ing)\s+)?([0-9]+(?:\.[0-9]+)?)\s*%\s+of\s+(?:the\s+|our\s+)?(?:pre[-\s]?(?:issue|offer|ipo)|paid[-\s]?up\s+capital\s+before\s+the\s+(?:issue|offer))",
            rf"{promoter_label}.{{0,180}}?in\s+aggregate.{{0,360}}?(?:represent(?:ing|s)?|constitut(?:ing|es)?|aggregat(?:ing|es)?\s+to)\s+([0-9]+(?:\.[0-9]+)?)\s*%\s+of\s+(?:the\s+)?pre[-\s]?(?:issue|offer|ipo)",
        ]
        for pattern in patterns:
            match = re.search(pattern, block, re.I)
            if match:
                pct = _valid_pct(match.group(1))
                if pct is not None:
                    return {"promoters": [], "promoterPreIssuePct": pct}
        direct = re.search(r"Promoter(?:s|\s+Group)?\s+(?:Share\s*)?Holding.{0,90}?Pre[-\s]?(?:Issue|Offer|IPO).{0,80}?([0-9]+(?:\.[0-9]+)?)\s*%", block, re.I)
        if direct:
            pct = _valid_pct(direct.group(1))
            if pct is not None:
                return {"promoters": [], "promoterPreIssuePct": pct}
        header = re.search(r"(?:Pre[-\s]?(?:Issue|IPO|Offer).{0,130}?(?:%|Percentage|Share\s+Holding)|(?:%|Percentage|Share\s+Holding).{0,130}?Pre[-\s]?(?:Issue|IPO|Offer))", block, re.I)
        if header:
            for pattern in (
                r"Grand\s+Total(?:\s*\([^)]*\))?\s+([\d,]{4,})\s+([0-9]+(?:\.[0-9]+)?)\s*%?",
                r"Total\s+Promoter(?:s)?(?:\s*(?:and|&|/)\s*Promoter\s+Group)?\s+([\d,]{4,})\s+([0-9]+(?:\.[0-9]+)?)\s*%?",
                rf"{promoter_label}\s+([\d,]{{4,}})\s+([0-9]+(?:\.[0-9]+)?)\s*%?",
            ):
                match = re.search(pattern, block, re.I)
                if match:
                    pct = _valid_pct(match.group(2))
                    if pct is not None:
                        return {"promoters": [], "promoterPreIssuePct": pct}
        if re.search(r"Pre[-\s]?Issue\s+Shareholding\s+of\s+(?:our\s+)?Promoters?", block, re.I):
            subtotal = re.search(r"(?:Sub\s*Total|Total)\s*(?:\([^)]*\))?\s+([\d,]{4,})\s+([0-9]+(?:\.[0-9]+)?)\s*%?", block, re.I)
            if subtotal:
                pct = _valid_pct(subtotal.group(2))
                if pct is not None:
                    return {"promoters": [], "promoterPreIssuePct": pct}
    return None


_PRE_OFFER_TABLE_HEADING = re.compile(r"(?:pre[-\s]?offer\s+(?:and\s+post[-\s]?offer\s+)?shareholding|pre[-\s]?offer\s+and\s+post[-\s]?offer\s+shareholding|pre\s+and\s+post\s+offer\s+shareholding|shareholding\s+pattern\s+of\s+(?:our\s+)?company)", re.I)
_PROMOTER_SECTION = re.compile(r"\bPromoters?\s+(?=1(?:\.|\s))", re.I)
_PROMOTER_GROUP_SECTION = re.compile(r"\bPromoter\s+Group(?:\s*\([^)]*\))?\s+(?=1(?:\.|\s))", re.I)
_SECTION_END = re.compile(r"\b(?:Additional\s+top\s+10|Other\s+public|Public\s+Shareholders|Additional\s+shareholders|Non[-\s]?Promoter)\b", re.I)
_ROW_PCT = re.compile(r"\b\d[\d,]{2,}\s+(100(?:\.0+)?|\d{1,2}(?:\.\d+)?)\s*%?\s+(?=\[(?:●|•||\s)*\])", re.I)


def _shareholding_windows_v7(flat: str):
    candidates = [flat[max(0, m.start() - 500):min(len(flat), m.start() + 9000)] for m in _PRE_OFFER_TABLE_HEADING.finditer(flat)][:18]
    candidates.extend(_ranked_shareholding_windows(flat))
    out, seen = [], set()
    for block in candidates:
        fp = block[:320].casefold()
        if fp not in seen:
            seen.add(fp)
            out.append(block)
    return out


def _combined_pattern_pct(block: str):
    row = re.search(r"(?:\(\s*A\s*\)|\bA\b)\s*Promoters?\s+(?:and|&|/)\s+Promoter\s+Group.{0,650}?([0-9]+(?:\.[0-9]+)?)\s*%", block, re.I)
    if row:
        pct = _valid_pct(row.group(1))
        if pct is not None:
            return pct
    narrative = re.search(r"(?:as\s+on|as\s+at)\s+the\s+date\s+of\s+(?:this|the)\s+(?:red\s+herring\s+)?prospectus.{0,420}?(?:our\s+)?Promoters?\s+along\s+with\s+(?:members\s+of\s+)?(?:our\s+)?Promoter\s+Group.{0,220}?collectively\s+(?:hold|holds|held).{0,120}?([0-9]+(?:\.[0-9]+)?)\s*%", block, re.I)
    if not narrative:
        narrative = re.search(r"(?:our\s+)?Promoters?\s+along\s+with\s+(?:members\s+of\s+)?(?:our\s+)?Promoter\s+Group.{0,220}?collectively\s+(?:hold|holds|held).{0,120}?([0-9]+(?:\.[0-9]+)?)\s*%.{0,260}?(?:pre[-\s]?offer|pre[-\s]?issue|shareholding\s+pre\s+and\s+post)", block, re.I)
    return _valid_pct(narrative.group(1)) if narrative else None


def _subtotal_pair_pct(block: str):
    if not _PROMOTER_GROUP_SECTION.search(block):
        return None
    match = re.search(r"(?:Sub[-\s]*total|Total)\s*\(\s*A\s*\)\s+[\d,]{2,}\s+([0-9]+(?:\.[0-9]+)?)\s*%?.{0,2400}?(?:Sub[-\s]*total|Total)\s*\(\s*B\s*\)\s+[\d,]{2,}\s+([0-9]+(?:\.[0-9]+)?)\s*%?", block, re.I)
    if not match:
        return None
    a, b = _valid_pct(match.group(1)), _valid_pct(match.group(2))
    if a is None or b is None:
        return None
    total = round(a + b, 4)
    return total if 0 <= total <= 100 else None


def _individual_section_pct(block: str):
    if not re.search(r"pre[-\s]?offer", block, re.I) or re.search(r"(?:Sub[-\s]*total|Total)\s*\(\s*[AB]\s*\)", block, re.I):
        return None
    group = _PROMOTER_GROUP_SECTION.search(block)
    if not group:
        return None
    promoters = list(_PROMOTER_SECTION.finditer(block[:group.start()]))
    if not promoters:
        return None
    promoter = promoters[-1]
    tail = block[group.end():]
    end = _SECTION_END.search(tail)
    if not end:
        return None
    promoter_values = [float(v) for v in _ROW_PCT.findall(block[promoter.end():group.start()])]
    group_values = [float(v) for v in _ROW_PCT.findall(block[group.end():group.end() + end.start()])]
    if not promoter_values or not group_values or len(promoter_values) + len(group_values) < 2:
        return None
    total = round(sum(promoter_values) + sum(group_values), 4)
    return total if 0 < total <= 100 else None


def _shareholding_v7(text: str):
    flat = re.sub(r"\s+", " ", base.norm_space(text)).strip()
    direct = _combined_pattern_pct(flat)
    if direct is not None:
        return {"promoters": [], "promoterPreIssuePct": direct}
    for block in _shareholding_windows_v7(flat):
        for value in (_combined_pattern_pct(block), _subtotal_pair_pct(block), _individual_section_pct(block)):
            if value is not None:
                return {"promoters": [], "promoterPreIssuePct": value}
    return _shareholding_v6(text)


def _explicit_ab_total(text: str):
    flat = re.sub(r"\s+", " ", base.norm_space(text)).strip()
    for match in re.finditer(r"Total\s*\(\s*A\s*\+\s*B\s*\)\s+[\d,]{2,}\s+(100(?:\.0+)?|\d{1,2}(?:\.\d+)?)\s*%?", flat, re.I):
        block = flat[max(0, match.start() - 4200):min(len(flat), match.end() + 500)]
        if re.search(r"pre[-\s]?(?:offer|issue|ipo)", block, re.I) and re.search(r"\bPromoters?\b", block, re.I) and re.search(r"\bPromoter\s+Group\b", block, re.I) and not re.search(r"minimum\s+promoters?['’]?\s+contribution", block[-1200:], re.I):
            pct = _valid_pct(match.group(1))
            if pct is not None:
                return pct
    return None


def _explicit_combined_ownership(text: str):
    flat = re.sub(r"\s+", " ", base.norm_space(text)).strip()
    for match in re.finditer(r"Total\s*(?:[-–—]\s*)?C\s*\(\s*A\s*\+\s*B\s*\)\s+[\d,]{2,}\s+(100(?:\.0+)?|\d{1,2}(?:\.\d+)?)\s*%?", flat, re.I):
        block = flat[max(0, match.start() - 4200):min(len(flat), match.end() + 700)]
        if re.search(r"pre[-\s]?(?:issue|offer|ipo)", block, re.I) and re.search(r"promoter\s+group", block, re.I) and not re.search(r"minimum\s+promoters?['’]?\s+contribution", block[-1400:], re.I):
            pct = _valid_pct(match.group(1))
            if pct is not None:
                return pct
    for match in re.finditer(r"Total\s*\(\s*A\s*\)\s+Promoter\s+and\s+Promoter\s+Group\s+\d{1,4}\s+[\d,]{4,}\s+(?:-\s+){0,3}[\d,]{4,}\s+(100(?:\.0+)?|\d{1,2}\.\d+)\b", flat, re.I):
        before = flat[max(0, match.start() - 3200):match.start()]
        after = flat[match.end():min(len(flat), match.end() + 900)]
        if re.search(r"shareholding", before, re.I) and re.search(r"(?:voting\s+rights|A\s*\+\s*B\s*\+\s*C|dematerialized)", before, re.I) and re.search(r"\(\s*B\s*\)\s+Public\b", after, re.I):
            pct = _valid_pct(match.group(1))
            if pct is not None:
                return pct
    return None


def extract_promoter_shareholding(text: str):
    combined = _explicit_combined_ownership(text)
    if combined is not None:
        return {"promoters": [], "promoterPreIssuePct": combined}
    combined = _explicit_ab_total(text)
    if combined is not None:
        return {"promoters": [], "promoterPreIssuePct": combined}
    return _shareholding_v7(text)


def _flat(text: str):
    return re.sub(r"\s+", " ", base.norm_space(text or "")).strip()


def _valid_lot(value):
    lot = base.integer(value)
    return lot if lot is not None and 0 < lot <= 100_000 else None


def extract_lot_size(text: str):
    flat = _flat(text)
    patterns = (
        r"\bminimum\s+bid\s+lot(?:\s+size)?\s*(?:is|of|:|-)?\s*([\d,]{1,8})\s+(?:fully\s+paid[-\s]?up\s+)?equity\s+shares\b",
        r"\bbid\s+lot(?:\s+size)?\s*(?:is|of|:|-)?\s*([\d,]{1,8})\s+(?:fully\s+paid[-\s]?up\s+)?equity\s+shares\b",
        r"\bminimum\s+bid\s+quantity\s*(?:is|of|:|-)?\s*([\d,]{1,8})\s+(?:fully\s+paid[-\s]?up\s+)?equity\s+shares\b",
        r"\bbids?\s+(?:can|may)\s+be\s+made\s+for\s+(?:a\s+)?minimum\s+of\s+([\d,]{1,8})\s+(?:fully\s+paid[-\s]?up\s+)?equity\s+shares\b",
        r"\bminimum\s+of\s+([\d,]{1,8})\s+(?:fully\s+paid[-\s]?up\s+)?equity\s+shares.{0,100}?\bminimum\s+bid\s+lot\b",
        r"\bmarket\s+lot\s*(?:is|of|:|-)?\s*([\d,]{1,8})\s+(?:fully\s+paid[-\s]?up\s+)?equity\s+shares\b",
    )
    for pattern in patterns:
        match = re.search(pattern, flat, re.I)
        if match:
            lot = _valid_lot(match.group(1))
            if lot is not None:
                return lot
    return None


def _valid_band(lo, hi=None):
    low, high = base.number(lo), base.number(hi if hi is not None else lo)
    if low is None or high is None:
        return None
    low, high = float(low), float(high)
    return {"min": low, "max": high} if 0 < low <= high <= 100_000 else None


def extract_price_band(text: str):
    flat = _flat(text)
    for pattern in (
        r"\bprice\s+band\b.{0,100}?(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)\s*(?:to|[-–—])\s*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)\s+per\s+equity\s+share\b",
        r"\bfloor\s+price\b.{0,90}?(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?).{0,140}?\bcap\s+price\b.{0,90}?(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s+per\s+equity\s+share\b",
    ):
        match = re.search(pattern, flat, re.I)
        if match:
            band = _valid_band(match.group(1), match.group(2))
            if band:
                return band
    fixed = re.search(r"\b(?:issue|offer)\s+price\b\s*(?:is|of|:|at)?\s*(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s+per\s+equity\s+share\b", flat, re.I)
    return _valid_band(fixed.group(1)) if fixed else None


_SUPPLEMENTAL_TYPES = {"ADDENDUM", "CORRIGENDUM", "ANNOUNCEMENT", "ADVERTISEMENT"}
_SUPPLEMENTAL_MARKERS = ("ADDENDUM", "CORRIGENDUM", "PUBLIC ANNOUNCEMENT", "PRE-ISSUE ADVERTISEMENT", "PRE ISSUE ADVERTISEMENT", "PRICE BAND ADVERTISEMENT")


def is_supplemental_document(doc: dict):
    typ = str(doc.get("type") or "").strip().upper()
    title = str(doc.get("title") or "").strip().upper()
    return typ in _SUPPLEMENTAL_TYPES or any(marker in title for marker in _SUPPLEMENTAL_MARKERS)


def _official_sebi_pdf(doc: dict):
    url = str(doc.get("url") or "").strip()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return url if parsed.path.lower().endswith(".pdf") and (host == "sebi.gov.in" or host.endswith(".sebi.gov.in")) else None


def _official_bse_pdf(doc: dict):
    url = str(doc.get("url") or "").strip()
    if str(doc.get("source") or "").upper() != "BSE":
        return None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return url if parsed.path.lower().endswith(".pdf") and (host == "bseindia.com" or host.endswith(".bseindia.com")) else None


def choose_document(record):
    docs = [doc for doc in (record.get("documents") or []) if isinstance(doc, dict) and not is_supplemental_document(doc)]
    if not docs:
        return None
    rank = {"PROSPECTUS": 4, "RHP": 3, "UDRHP": 2, "DRHP": 1, "DOCUMENT": 0}
    sebi = []
    for doc in docs:
        url = _official_sebi_pdf(doc)
        if not url:
            continue
        title, typ = str(doc.get("title") or ""), str(doc.get("type") or "DOCUMENT").upper()
        abridged = int("ABRIDGED" in title.upper() or "AP_" in url.upper())
        sebi.append((abridged, rank.get(typ, 0), str(doc.get("filedDate") or ""), len(title), doc))
    if sebi:
        return max(sebi, key=lambda item: item[:-1])[-1]
    bse = []
    for doc in docs:
        url = _official_bse_pdf(doc)
        if not url:
            continue
        title, typ = str(doc.get("title") or ""), str(doc.get("type") or "DOCUMENT").upper()
        if "PROSPECTUS" not in title.upper() and typ not in {"PROSPECTUS", "RHP", "UDRHP", "DRHP"}:
            continue
        bse.append((rank.get(typ, 0), str(doc.get("filedDate") or ""), len(title), doc))
    return max(bse, key=lambda item: item[:-1])[-1] if bse else None


def download_pdf(session, url, *, attempts: int = 3, retry_delay: float = 1.0):
    last_error = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            return base.download_pdf(session, url)
        except (requests.RequestException, OSError) as exc:
            last_error = exc
            if attempt >= attempts:
                raise
            time.sleep(retry_delay * attempt)
    raise last_error or RuntimeError("PDF download failed without an error")


def _financial_page_score(text: str):
    if not text:
        return 0
    marker = bool(_FINANCIAL_SECTION_MARKER.search(text))
    metric_hits = sum(1 for pats in _FINANCIAL_METRICS.values() if any(re.search(p, text, re.I) for p in pats))
    year_hits = len(set(re.findall(r"\b20[12]\d\b", text)))
    numeric_hits = len(base._numeric_tokens(text))
    return 0 if not marker and metric_hits < 2 else (8 if marker else 0) + metric_hits * 5 + min(year_hits, 4) * 3 + min(numeric_hits // 10, 5)


def _shareholding_page_score(text: str):
    if not text:
        return 0
    marker = bool(_SHAREHOLDING_PAGE_MARKER.search(text))
    promoter = bool(re.search(_PROMOTER_GROUP_LABEL, text, re.I))
    pre = bool(_PRE_CONTEXT.search(text))
    pct = len(re.findall(r"\b[0-9]+(?:\.[0-9]+)?\s*%", text))
    score = 0 if not marker and not (promoter and pre) else (8 if marker else 0) + (6 if promoter else 0) + (5 if pre else 0) + min(pct, 6) * 2
    flat = re.sub(r"\s+", " ", text).strip()
    if re.search(r"(?:\(\s*A\s*\)|\bA\b)\s*Promoters?\s+(?:and|&|/)\s+Promoter\s+Group", flat, re.I):
        score += 40
    if re.search(r"(?:Sub[-\s]*total|Total)\s*\(\s*A\s*\).{0,2600}?(?:Sub[-\s]*total|Total)\s*\(\s*B\s*\)", flat, re.I):
        score += 35
    if re.search(r"Promoters?.{0,800}?Promoter\s+Group", flat, re.I) and re.search(r"pre[-\s]?(?:offer|issue|ipo)", flat, re.I):
        score += 18
    if re.search(r"Promoters?.{0,260}?Promoter\s+Group.{0,260}?collectively\s+(?:hold|holds|held)", flat, re.I):
        score += 25
    return score


def _offer_term_page_score(text: str):
    if not text:
        return 0
    flat = re.sub(r"\s+", " ", text).strip()
    score = 0
    for pattern, points in (
        (r"\bminimum\s+bid\s+lot\b", 80), (r"\bminimum\s+bid\s+quantity\b", 70), (r"\bbid\s+lot\b", 55), (r"\bmarket\s+lot\b", 50),
        (r"\bbids?\s+(?:can|may)\s+be\s+made\s+for\s+(?:a\s+)?minimum\s+of\b", 45), (r"\bprice\s+band\b", 35), (r"\bfloor\s+price\b", 25),
        (r"\bcap\s+price\b", 25), (r"\b(?:issue|offer)\s+price\b", 15), (r"\b(?:issue\s+procedure|terms?\s+of\s+the\s+offer|how\s+to\s+apply|bid(?:ding)?\s+process)\b", 12),
    ):
        if re.search(pattern, flat, re.I):
            score += points
    return score


def extract_targeted_pdf_text(data: bytes, base_text: str, *, need_financials: bool = True, need_shareholding: bool = True, need_offer_terms: bool = True, max_scan_pages: int = 520, max_hits: int = 16, term_hits: int = 12, context_pages: int = 2):
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            pass
    page_count = len(reader.pages)
    first_pages = min(30, page_count)
    if page_count <= first_pages or not (need_financials or need_shareholding or need_offer_terms):
        return base_text, first_pages, page_count
    stop_at = min(page_count, max_scan_pages)
    financial_scores, shareholding_scores, term_scores, cache = [], [], [], {}
    for idx in range(first_pages, stop_at):
        try:
            page_text = reader.pages[idx].extract_text() or ""
        except Exception:
            page_text = ""
        cache[idx] = page_text
        if need_financials and (score := _financial_page_score(page_text)) > 0:
            financial_scores.append((score, idx))
        if need_shareholding and (score := _shareholding_page_score(page_text)) > 0:
            shareholding_scores.append((score, idx))
        if need_offer_terms and (score := _offer_term_page_score(page_text)) > 0:
            term_scores.append((score, idx))
    selected = set()
    for scores, limit in ((financial_scores, max_hits), (shareholding_scores, max_hits), (term_scores, term_hits)):
        scores.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected.update(idx for _score, idx in scores[:limit])
    if not selected:
        return base_text, stop_at, page_count
    pages = set()
    before, after = (1 if context_pages > 0 else 0), max(0, context_pages)
    for center in selected:
        pages.update(range(max(first_pages, center - before), min(stop_at, center + after + 1)))
    collected = [base_text]
    for idx in sorted(pages):
        text = cache.get(idx) or ""
        if text.strip():
            collected.append(text)
    return "\n".join(collected), stop_at, page_count


def extract_pdf_text(data: bytes):
    first_text, pages_read, page_count = base.extract_pdf_text(data)
    if page_count <= pages_read:
        return first_text, pages_read, page_count
    return extract_targeted_pdf_text(data, first_text)


_COVER_INTERMEDIARY_HEADERS = (
    re.compile(r"NAME\s+AND\s+LOGO\s+OF\s+(?:THE\s+)?BRLM\s+CONTACT\s+PERSON\s+EMAIL\s+AND\s+TELEPHONE", re.I),
    re.compile(r"NAME\s+AND\s+LOGO\s+OF\s+THE\s+REGISTRAR\s+CONTACT\s+PERSON\s+EMAIL\s+AND\s+TELEPHONE", re.I),
)


def normalize_cover_intermediary_headers(text: str):
    normalized = text or ""
    for pattern in _COVER_INTERMEDIARY_HEADERS:
        normalized = pattern.sub(" ", normalized)
    return normalized


def parse_document_text(text: str, price_band=None):
    text = (text or "").replace("\r", "\n")
    leads, registrar = extract_intermediaries(text)
    if not leads or not registrar:
        fallback_leads, fallback_registrar = extract_intermediaries(normalize_cover_intermediary_headers(text))
        leads = leads or fallback_leads
        registrar = registrar or fallback_registrar
    promoters = extract_promoters(text)
    issue = extract_issue_composition(text, price_band)
    financials = extract_financials(text)
    objects = extract_objects(text)
    shareholding = extract_promoter_shareholding(text)
    lot_size = extract_lot_size(text)
    parsed_band = extract_price_band(text)
    result = {
        "leadManagers": leads,
        "registrar": registrar,
        "promoters": promoters,
        "issueComposition": issue,
        "financials": financials,
        "objectsOfIssue": objects,
        "shareholding": shareholding,
        "lotSize": lot_size,
        "priceBand": parsed_band,
    }
    fields = []
    if leads: fields.append("leadManagers")
    if registrar: fields.append("registrar")
    if promoters: fields.append("promoters")
    if any(v not in (None, 0) for v in issue.values()): fields.append("issueComposition")
    if financials: fields.append("financials")
    if objects: fields.append("objectsOfIssue")
    if shareholding: fields.append("shareholding")
    if lot_size is not None: fields.append("lotSize")
    if parsed_band is not None: fields.append("priceBand")
    result["extractedFields"] = fields
    return result


def apply_enrichment(record, parsed, doc, pdf_hash, pages_read, page_count):
    """Final legacy fill/observation behavior with parser-v14 provenance."""
    base.apply_enrichment(record, parsed, doc, pdf_hash, pages_read, page_count)
    extraction = record.get("offerDocumentExtraction")
    if isinstance(extraction, dict):
        extraction["source"] = str(doc.get("source") or "SEBI").upper()
    changed = []
    lot_size, price_band = parsed.get("lotSize"), parsed.get("priceBand")
    if record.get("lotSize") is None and lot_size is not None:
        record["lotSize"] = lot_size
        changed.append("lotSize")
    if record.get("priceBand") in (None, {}, []) and price_band:
        record["priceBand"] = price_band
        changed.append("priceBand")
    if lot_size is not None or price_band:
        observation = {"documentUrl": doc.get("url"), "documentType": doc.get("type"), "documentFiledDate": doc.get("filedDate"), "parserVersion": PARSER_VERSION}
        if lot_size is not None: observation["lotSize"] = lot_size
        if price_band: observation["priceBand"] = price_band
        record.setdefault("observations", {})["SEBI-offer"] = observation
    extraction = record.get("offerDocumentExtraction")
    if isinstance(extraction, dict):
        extraction["parserVersion"] = PARSER_VERSION
        extraction["extractedFields"] = parsed.get("extractedFields") or []
        if changed:
            extraction["changedFields"] = list(dict.fromkeys(list(extraction.get("changedFields") or []) + changed))
    observation = (record.get("observations") or {}).get("SEBI-offer")
    if isinstance(observation, dict):
        observation["parserVersion"] = PARSER_VERSION


def main():
    """Compatibility CLI: run the original base workflow with canonical hooks."""
    originals = {
        name: getattr(base, name)
        for name in ("extract_intermediaries", "extract_promoters", "extract_issue_composition", "extract_financials", "extract_objects", "extract_promoter_shareholding", "parse_document_text", "choose_document", "download_pdf", "extract_pdf_text", "apply_enrichment")
    }
    previous_version = base.PARSER_VERSION
    try:
        base.extract_intermediaries = extract_intermediaries
        base.extract_promoters = extract_promoters
        base.extract_issue_composition = extract_issue_composition
        base.extract_financials = extract_financials
        base.extract_objects = extract_objects
        base.extract_promoter_shareholding = extract_promoter_shareholding
        base.parse_document_text = parse_document_text
        base.choose_document = choose_document
        base.download_pdf = download_pdf
        base.extract_pdf_text = extract_pdf_text
        base.apply_enrichment = apply_enrichment
        base.PARSER_VERSION = PARSER_VERSION
        return base.main()
    finally:
        for name, value in originals.items():
            setattr(base, name, value)
        base.PARSER_VERSION = previous_version


if __name__ == "__main__":
    raise SystemExit(main())
