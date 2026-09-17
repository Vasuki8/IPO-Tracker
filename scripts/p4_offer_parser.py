"""Strict residual parsers for recent IPO offer-document gaps.

The main offer parser deliberately fails closed when a layout is not proven.
This module handles a small set of recurring, source-verified layouts that are
common in NSE SME prospectuses: paired intermediary columns, explicit promoter
headings, real Objects-of-Issue tables (not table-of-contents rows), aggregate
pre-issue promoter shareholding, and numeric-date restated P&L tables.

All recognizers require strong headings/context and are safe to run fill-only.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from objects_of_issue_checks import objects_problems

PARSER_VERSION = 1
RECENT_DAYS = 730

_LEGAL = re.compile(r"\b(?:Private\s+Limited|Pvt\.?\s+Ltd\.?|Limited|Ltd\.?|LLP)\b", re.I)
_MANAGER = re.compile(
    r"Capital|Securit|Financial|Finserv|Advis|Invest|Corporate|Merchant|Markets|Bank|"
    r"Fiscal|Broking|Brokers|Wealth|WAM|Management|Consult|Shares|Morgan\s+Stanley|"
    r"J\.?\s*P\.?\s*Morgan|Jefferies|BNP\s+Paribas",
    re.I,
)
_REGISTRAR = re.compile(
    r"Technolog|Services|Fintech|Registry|Registrars|Intime|Sharegistry|Consultancy|"
    r"Assignments|Computershare|Maashitla\s+Securities|Bigshare|Cameo",
    re.I,
)
_ROLE_LEFT = re.compile(
    r"(?:BOOK\s+RUNNING\s+)?LEAD\s+MANAGERS?(?:\s+TO\s+THE\s+(?:ISSUE|OFFER))?",
    re.I,
)
_ROLE_RIGHT = re.compile(r"REGISTRAR\s+TO\s+THE\s+(?:ISSUE|OFFER)", re.I)
_OBJECT_KEYWORDS = re.compile(
    r"working\s+capital|general\s+corporate|capital\s+expenditure|purchase|procure|"
    r"repay|prepay|borrow|investment|acquisition|expansion|issue\s+(?:related\s+)?expenses?|"
    r"software|hardware|equipment|plant|machinery|warehouse|subsidiar|loan|debt|funding|"
    r"office|studio|land|construction",
    re.I,
)
_BAD_OBJECT = re.compile(
    r"^(?:BASIS\s+FOR\s+(?:THE\s+)?(?:ISSUE|OFFER)\s+PRICE|STATEMENT\s+OF\s+(?:POSSIBLE\s+)?(?:SPECIAL\s+)?TAX\s+BENEFITS|"
    r"SECTION\b|INDUSTRY\s+OVERVIEW|OUR\s+BUSINESS|KEY\s+(?:INDUSTRY\s+)?REGULATIONS?|OUR\s+HISTORY|"
    r"HISTORY\s+AND|OUR\s+MANAGEMENT|OUR\s+PROMOTER|OUR\s+SUBSIDIAR|OUR\s+GROUP|DIVIDEND\s+POLICY|"
    r"FINANCIAL\s+INFORMATION|RISK\s+FACTORS)",
    re.I,
)
_PERSON_PREFIX = re.compile(r"^(?:(?:being|namely)\s+|(?:Mr|Ms|Mrs|Dr)\.?\s+)+", re.I)
_GENERIC_NAME = re.compile(
    r"\b(?:promoters?|company|details|issue|offer|page|contact|telephone|email|website|risk|listing)\b",
    re.I,
)
_NUMERIC_DATE = re.compile(r"\b(0?[1-9]|[12]\d|3[01])[-/.](0?[1-9]|1[0-2])[-/.](20\d{2})\b")
_MONEY_TOKEN = re.compile(r"\(?[-+]?\d[\d,]*(?:\.\d+)?\)?|\[\s*[●•*]\s*\]|(?<!\w)[—–-](?!\w)")


def _space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u00a0", " ")).strip()


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            out.append(value)
    return out


def _legal_entities(block: str) -> list[str]:
    flat = _space(block)
    pattern = re.compile(
        r"([A-Z0-9][A-Za-z0-9&'().,/+\-]*(?:\s+[A-Z0-9][A-Za-z0-9&'().,/+\-]*){0,10}\s+"
        r"(?:Private\s+Limited|Pvt\.?\s+Ltd\.?|Limited|Ltd\.?|LLP))"
    )
    out = []
    for match in pattern.finditer(flat):
        name = _space(match.group(1)).strip(" ,.;:-")
        if not re.search(r"CONTACT|TELEPHONE|EMAIL|E-MAIL|NAME\s+AND\s+LOGO", name, re.I):
            out.append(name)
    return _dedupe(out)


def valid_promoter_name(value: Any) -> bool:
    name = _space(value).strip(" ,.;:-")
    if not name or len(name) > 140:
        return False
    if _LEGAL.search(name):
        return len(name.split()) >= 3 and not re.search(r"CONTACT|TELEPHONE|EMAIL|REGISTRAR|LEAD\s+MANAGER", name, re.I)
    clean = _PERSON_PREFIX.sub("", name)
    words = clean.split()
    if not 2 <= len(words) <= 9 or _GENERIC_NAME.search(clean):
        return False
    if any(not re.fullmatch(r"[A-Za-z][A-Za-z.'\-]*", word) for word in words):
        return False
    return True


def valid_promoters(value: Any) -> bool:
    return isinstance(value, list) and 1 <= len(value) <= 20 and all(valid_promoter_name(item) for item in value)


def valid_objects(value: Any) -> bool:
    if not isinstance(value, list) or not value or len(value) > 20 or objects_problems(value):
        return False
    good = 0
    for row in value:
        if not isinstance(row, dict):
            return False
        purpose = _space(row.get("purpose"))
        if not purpose or _BAD_OBJECT.search(purpose):
            return False
        amount = row.get("amountCr")
        if amount is not None and (not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount < 0):
            return False
        if _OBJECT_KEYWORDS.search(purpose):
            good += 1
    return good >= 1


def _valid_shareholding(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    pct = value.get("promoterPreIssuePct")
    return isinstance(pct, (int, float)) and not isinstance(pct, bool) and 0 <= float(pct) <= 100


def _has_financials(value: Any) -> bool:
    periods = value.get("periods") if isinstance(value, dict) else None
    return isinstance(periods, list) and len(periods) >= 2 and any(
        isinstance(row, dict) and any(row.get(key) is not None for key in ("revenueCr", "patCr", "ebitdaCr", "netWorthCr", "eps"))
        for row in periods
    )


def is_recent(record: dict[str, Any], today: date | None = None) -> bool:
    try:
        opened = date.fromisoformat(str(record.get("openDate") or "")[:10])
    except ValueError:
        return False
    return opened >= (today or date.today()) - timedelta(days=RECENT_DAYS)


def needs_repair(record: dict[str, Any], today: date | None = None) -> bool:
    if not is_recent(record, today):
        return False
    shareholding = record.get("shareholding")
    return any(
        (
            not record.get("registrar"),
            not record.get("leadManagers"),
            not valid_promoters(record.get("promoters")),
            not valid_objects(record.get("objectsOfIssue")),
            not _has_financials(record.get("financials")),
            not _valid_shareholding(shareholding),
            not record.get("documentFieldProvenance"),
        )
    )


def extract_paired_intermediaries(text: str):
    pages = str(text or "").split("\f")[:6]
    for page_index, page in enumerate(pages, 1):
        lines = page.splitlines()
        for index, line in enumerate(lines):
            left = _ROLE_LEFT.search(line)
            right = _ROLE_RIGHT.search(line)
            if not left or not right or right.start() <= left.end() + 8:
                continue
            boundary = right.start()
            left_rows: list[str] = []
            right_rows: list[str] = []
            for row in lines[index + 1:index + 30]:
                if re.search(r"^\s*(?:BID|ISSUE|OFFER)\s*[/ ]*(?:ISSUE\s+)?(?:PERIOD|OPENS|CLOSES)|^\s*ANCHOR\s+BID", row, re.I):
                    break
                left_rows.append(row[:boundary])
                right_rows.append(row[boundary:])
            managers = [name for name in _legal_entities("\n".join(left_rows)) if _MANAGER.search(name)]
            registrars = [name for name in _legal_entities("\n".join(right_rows)) if _REGISTRAR.search(name)]
            if managers or registrars:
                evidence = {}
                if managers:
                    evidence["leadManagers"] = {"page": page_index, "heading": _space(line), "entities": managers}
                if registrars:
                    evidence["registrar"] = {"page": page_index, "heading": _space(line), "entities": registrars[:1]}
                return managers, (registrars[0] if registrars else None), evidence
    return [], None, {}


def _promoter_payload(flat: str) -> tuple[str, str] | None:
    patterns = [
        ("NAMES OF PROMOTERS OF THE COMPANY", r"NAMES?\s+OF\s+(?:THE\s+)?PROMOTERS?\s+OF\s+(?:OUR\s+|THE\s+)?COMPANY\s*[:\-]?\s*(.{1,900}?)(?=DETAILS\s+OF\s+(?:THE\s+)?(?:ISSUE|OFFER)|RISKS?\s+IN\s+RELATION|GENERAL\s+RISK|LISTING|$)"),
        ("OUR PROMOTERS", r"OUR\s+PROMOTERS?\s*:\s*(.{1,900}?)(?=DETAILS\s+OF\s+(?:THE\s+)?(?:ISSUE|OFFER)|RISKS?\s+IN\s+RELATION|GENERAL\s+RISK|LISTING|$)"),
        ("PROMOTERS OF OUR COMPANY", r"Promoters?\s+of\s+Our\s+Company\s+(?:are|is)\s+(.{1,700}?)(?=For\s+details|DETAILS\s+OF\s+(?:THE\s+)?(?:ISSUE|OFFER)|$)"),
    ]
    for heading, pattern in patterns:
        match = re.search(pattern, flat, re.I)
        if match:
            return heading, match.group(1)
    return None


def extract_promoters(text: str):
    front = " ".join(str(text or "").split("\f")[:25])[:160000]
    flat = _space(front)
    found = _promoter_payload(flat)
    if not found:
        return [], {}
    heading, payload = found
    payload = re.split(r"\bFor\s+details\b|\bThe\s+details\s+of\s+our\s+Promoters\b", payload, maxsplit=1, flags=re.I)[0]
    payload = re.sub(r"Promoters?\s+of\s+Our\s+Company\s+(?:are|is)\s+", "", payload, flags=re.I)
    payload = re.sub(r"\((?:i|ii|iii|iv|v|vi|vii|viii|ix|x)\)", ";", payload, flags=re.I)
    payload = re.sub(r"\b(?:and)\b", ";", payload, flags=re.I)
    pieces = re.split(r"\s*[,;]\s*", payload)
    names = []
    for raw in pieces:
        name = _space(raw).strip(" .,:;-()")
        name = re.sub(r"^(?:and\s+)?(?:being|namely)\s+", "", name, flags=re.I)
        name = re.sub(r"^(?:Mr|Ms|Mrs|Dr)\.?\s+", "", name, flags=re.I)
        if valid_promoter_name(name):
            names.append(name)
    names = _dedupe(names)
    return (names, {"promoters": {"heading": heading, "entities": names}}) if names else ([], {})


def _money_unit(block: str):
    match = re.search(r"(?:₹|Rs\.?|INR)?\s*(?:in\s+)?(crores?|cr\.?|millions?|lakhs?|lacs?)\b", block, re.I)
    if not match:
        return ("crore", 1.0)
    unit = match.group(1).lower()
    if unit.startswith("million"):
        return ("million", 0.1)
    if unit.startswith("lakh") or unit.startswith("lac"):
        return ("lakh", 0.01)
    return ("crore", 1.0)


def _amount(value: str, factor: float):
    token = value.strip()
    if "●" in token or "•" in token or token in {"-", "—", "–"}:
        return None
    return round(float(token.replace(",", "")) * factor, 6)


def extract_objects(text: str):
    source = str(text or "")
    heading = re.compile(r"(?im)^\s*(?:[a-z]\)\s*)?OBJECTS?\s+OF\s+THE\s+(?:ISSUE|OFFER)\s*$")
    best: list[dict[str, Any]] = []
    best_evidence = {}
    for match in list(heading.finditer(source))[:12]:
        block = source[match.start():match.start() + 14000]
        stop = re.search(r"(?im)^\s*(?:BASIS\s+FOR\s+(?:THE\s+)?(?:ISSUE|OFFER)\s+PRICE|STATEMENT\s+OF\s+(?:POSSIBLE\s+)?(?:SPECIAL\s+)?TAX\s+BENEFITS|SECTION\s+[IVX]+\b|RISK\s+FACTORS)\s*$", block[200:])
        if stop:
            block = block[:200 + stop.start()]
        context_score = sum(bool(re.search(pattern, block, re.I)) for pattern in (
            r"Net\s+Proceeds", r"Utili[sz]ation", r"Working\s+Capital", r"General\s+Corporate", r"fund\s+requirements?", r"proposes?\s+to\s+utili[sz]e",
        ))
        if context_score < 2:
            continue
        unit_name, factor = _money_unit(block)
        rows: list[dict[str, Any]] = []
        for raw in block.splitlines():
            line = _space(raw)
            if len(line) < 8 or re.search(r"^(?:Sr\.?\s*No\.?|Particulars?|Amount|Gross\s+Proceeds|Net\s+Proceeds|Less:|Total\b|For\s+further\s+details|Note\b)", line, re.I):
                continue
            row = re.match(
                r"^(?:\d+[.)]?|[A-Z][.)]?)?\s*(.+?)\s+(?:Up\s+to\s+)?(?:₹|Rs\.?|INR)?\s*(\[\s*[●•*]\s*\]|[\d,]+(?:\.\d+)?)(?:\s+(?:100(?:\.0+)?|\d{1,2}(?:\.\d+)?)\s*%)?\s*$",
                line,
                re.I,
            )
            if not row:
                continue
            purpose = _space(row.group(1)).strip(" .,:;-*")
            if not _OBJECT_KEYWORDS.search(purpose) or _BAD_OBJECT.search(purpose):
                continue
            rows.append({"purpose": purpose, "amountCr": _amount(row.group(2), factor)})
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in rows:
            key = row["purpose"].casefold()
            if key not in seen:
                seen.add(key)
                unique.append(row)
        if len(unique) > len(best):
            best = unique[:15]
            page_marker = list(re.finditer(r"\[PAGE (\d+)\]", source[:match.start()]))
            page = int(page_marker[-1].group(1)) if page_marker else None
            best_evidence = {"objectsOfIssue": {"page": page, "heading": "OBJECTS OF THE ISSUE", "unit": unit_name, "rows": best}}
    return best, best_evidence


def extract_promoter_shareholding(text: str):
    flat = _space(" ".join(str(text or "").split("\f")[:35])[:220000])
    direct_patterns = [
        r"(?:our\s+)?Promoters?\s+and\s+(?:members\s+of\s+)?(?:our\s+)?Promoter\s+Group.{0,180}?(?:hold|holds|held|holding).{0,80}?([0-9]+(?:\.\d+)?)\s*%\s+(?:of\s+)?(?:the\s+)?pre[-\s]?issue",
        r"(?:our\s+)?Promoters?\s+and\s+(?:our\s+)?Promoter\s+Group\s+(?:holds?|held)\s+([0-9]+(?:\.\d+)?)\s*%\s+pre[-\s]?issue",
        r"aggregate\s+pre[-\s]?issue\s+shareholding\s+of\s+(?:our\s+)?Promoters?\s+and\s+Promoter\s+Group.{0,500}?(?:Total|aggregate).{0,160}?([0-9]+(?:\.\d+)?)\s*%",
    ]
    for pattern in direct_patterns:
        match = re.search(pattern, flat, re.I)
        if match:
            pct = float(match.group(1))
            if 0 <= pct <= 100:
                return {"promoters": [], "promoterPreIssuePct": pct}, {"shareholding": {"basis": "explicit pre-issue promoter ownership", "promoterPreIssuePct": pct}}
    marker = re.search(r"aggregate\s+pre[-\s]?issue\s+shareholding\s+of\s+(?:our\s+)?Promoters?\s+and\s+Promoter\s+Group", flat, re.I)
    if marker:
        block = flat[marker.start():marker.start() + 4200]
        values = []
        for match in re.finditer(r"[\d,]{4,}\s+([0-9]+(?:\.\d+)?)\b", block):
            pct = float(match.group(1))
            if 0 < pct <= 100:
                values.append(pct)
        if 1 <= len(values) <= 20:
            total = round(sum(values), 4)
            if 0 < total <= 100:
                return {"promoters": [], "promoterPreIssuePct": total}, {"shareholding": {"basis": "aggregate pre-issue promoter table", "promoterPreIssuePct": total}}
    return None, {}


def _financial_unit(block: str):
    match = re.search(r"(?:Rs\.?|₹|INR)\s*(?:in\s+)?(Lakhs?|Lacs?|Crores?|Million)\b", block, re.I)
    if not match:
        return None
    unit = match.group(1).lower()
    if unit.startswith("lakh") or unit.startswith("lac"):
        return ("lakh", 0.01)
    if unit.startswith("million"):
        return ("million", 0.1)
    return ("crore", 1.0)


def _row_numbers(tail: str, count: int):
    tail = re.sub(r"^\s*\([^)]*\)\s*", "", tail)
    tokens = _MONEY_TOKEN.findall(tail)
    if len(tokens) != count:
        return None
    values = []
    for token in tokens:
        token = token.strip()
        if "●" in token or "•" in token or token in {"-", "—", "–"}:
            values.append(None)
        else:
            negative = token.startswith("(")
            value = float(token.strip("()").replace(",", ""))
            values.append(-value if negative else value)
    return values


def extract_numeric_date_financials(text: str):
    source = str(text or "")
    heading = re.search(r"(?im)^\s*RESTATED\s+(?:SUMMARY\s+)?STATEMENT\s+OF\s+PROFIT\s+(?:AND|&)\s+LOSS\s*$", source)
    if not heading:
        return None, {}
    block = source[heading.start():heading.start() + 18000]
    unit = _financial_unit(block[:2500])
    if unit is None:
        return None, {}
    lines = block.splitlines()
    header_i = None
    dates = []
    for i, line in enumerate(lines[:80]):
        found = list(_NUMERIC_DATE.finditer(line))
        if len(found) >= 3:
            header_i, dates = i, found
            break
    if header_i is None:
        return None, {}
    years = [match.group(3) for match in dates]
    annual = [i for i, match in enumerate(dates) if int(match.group(1)) == 31 and int(match.group(2)) == 3]
    if len(annual) < 2 or len({years[i] for i in annual}) != len(annual):
        return None, {}
    metrics = [
        ("revenueCr", re.compile(r"^\s*(?:\d+[.)]?\s+)?Revenue\s+From\s+Operations\b", re.I)),
        ("patCr", re.compile(r"^\s*(?:\d+[.)]?\s+)?(?:Profit\s*/?\s*\(?Loss\)?\s+for\s+the\s+Year|Profit\s+after\s+Tax)\b", re.I)),
        ("eps", re.compile(r"^\s*(?:\d+[.)]?\s+)?Basic\s*(?:&|and)\s*Diluted\s+Earning(?:s)?\s+Per\s+Share\b", re.I)),
    ]
    periods = {f"FY{years[i]}": {"period": f"FY{years[i]}"} for i in annual}
    evidence = {}
    for line in lines[header_i + 1:header_i + 120]:
        for key, pattern in metrics:
            match = pattern.match(line)
            if not match:
                continue
            tail = line[match.end():]
            values = _row_numbers(tail, len(dates))
            if values is None:
                continue
            for column in annual:
                value = values[column]
                if value is None:
                    continue
                normalized = round(value * unit[1], 6) if key.endswith("Cr") else value
                period = f"FY{years[column]}"
                periods[period][key] = normalized
                evidence[f"{period}.{key}"] = {"header": _space(lines[header_i]), "row": _space(line), "normalizedValue": normalized, "originalUnit": unit[0] if key.endswith("Cr") else "rupees per share", "scope": "unspecified"}
    rows = [row for row in periods.values() if len(row) > 1]
    metrics_found = {key for row in rows for key in row if key != "period"}
    if len(rows) < 2 or len(metrics_found) < 2:
        return None, {}
    return {"unit": "₹ crore", "periods": rows}, {"financials": evidence}


def parse_document_text(text: str) -> dict[str, Any]:
    leads, registrar, role_evidence = extract_paired_intermediaries(text)
    promoters, promoter_evidence = extract_promoters(text)
    objects, object_evidence = extract_objects(text)
    shareholding, shareholding_evidence = extract_promoter_shareholding(text)
    financials, financial_evidence = extract_numeric_date_financials(text)
    evidence = {}
    for item in (role_evidence, promoter_evidence, object_evidence, shareholding_evidence, financial_evidence):
        evidence.update(item)
    return {
        "leadManagers": leads,
        "registrar": registrar,
        "promoters": promoters,
        "objectsOfIssue": objects,
        "shareholding": shareholding,
        "financials": financials,
        "fieldEvidence": evidence,
        "residualParserVersion": PARSER_VERSION,
    }


def merge_parsed(primary: dict[str, Any], supplement: dict[str, Any]) -> dict[str, Any]:
    out = dict(primary or {})
    if not out.get("leadManagers") and supplement.get("leadManagers"):
        out["leadManagers"] = supplement["leadManagers"]
    if not out.get("registrar") and supplement.get("registrar"):
        out["registrar"] = supplement["registrar"]
    if not valid_promoters(out.get("promoters")) and valid_promoters(supplement.get("promoters")):
        out["promoters"] = supplement["promoters"]
    if not valid_objects(out.get("objectsOfIssue")) and valid_objects(supplement.get("objectsOfIssue")):
        out["objectsOfIssue"] = supplement["objectsOfIssue"]
    if not _valid_shareholding(out.get("shareholding")) and _valid_shareholding(supplement.get("shareholding")):
        out["shareholding"] = supplement["shareholding"]
    if not _has_financials(out.get("financials")) and _has_financials(supplement.get("financials")):
        out["financials"] = supplement["financials"]
    evidence = dict(out.get("fieldEvidence") or {})
    for key, value in (supplement.get("fieldEvidence") or {}).items():
        if key == "financials":
            current = dict(evidence.get("financials") or {})
            current.update(value or {})
            evidence["financials"] = current
        elif key not in evidence:
            evidence[key] = value
    out["fieldEvidence"] = evidence
    out["residualParserVersion"] = supplement.get("residualParserVersion")
    extracted = list(out.get("extractedFields") or [])
    for field in ("leadManagers", "registrar", "promoters", "objectsOfIssue", "shareholding", "financials"):
        if out.get(field) not in (None, [], {}) and field not in extracted:
            extracted.append(field)
    out["extractedFields"] = extracted
    return out
