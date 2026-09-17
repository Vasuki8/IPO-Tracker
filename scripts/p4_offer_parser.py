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
from decimal import Decimal, InvalidOperation
from typing import Any

from objects_of_issue_checks import (
    is_issue_expense_purpose, objects_evidence_problems,
    objects_header_fragment as _object_header_fragment, objects_problems,
    objects_purpose_key as _object_purpose_key,
)

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


_OBJECTS_HEADING = re.compile(
    r"^(?:[a-z]\)\s*)?(?:OBJECTS?\s+OF\s+THE\s+(?:ISSUE|OFFER)|"
    r"UTILI[SZ]ATION\s+OF\s+(?:THE\s+)?(?:(?:NET|ISSUE)\s+)?(?:PROCEEDS|FUNDS))\s*:?[ \t]*$",
    re.I,
)
_OBJECT_TABLE_STOP = re.compile(
    r"^(?:(?:PROPOSED\s+)?(?:SCHEDULE\b|DEPLOYMENT\b)|MEANS\s+OF\s+FINANCE\b|"
    r"DETAILS\s+OF\b|DETAILED\s+(?:BREAK|OBJECT|UTILI)|"
    r"BASIS\s+FOR\s+(?:THE\s+)?(?:ISSUE|OFFER)\s+PRICE|"
    r"STATEMENT\s+OF\s+(?:POSSIBLE\s+)?(?:SPECIAL\s+)?TAX\s+BENEFITS|"
    r"SECTION\s+[IVX]+\b|RISK\s+FACTORS)", re.I,
)
_OBJECT_PURPOSE_HEADER = re.compile(r"\b(?:Particulars?|Purposes?|Objects?)\b", re.I)
_OBJECT_AMOUNT_HEADER = re.compile(r"\bAmount\b", re.I)
_OBJECT_PERCENT_HEADER = re.compile(r"%|\bPercentage\b|\bPer\s+cent\b", re.I)
_OBJECT_FISCAL_HEADER = re.compile(
    r"\b(?:deploy(?:ed|ment)?|fiscals?|financial\s+years?|FY\s*20\d{2}|20\d{2})\b", re.I,
)
_OBJECT_UNIT = re.compile(
    r"(?:\b(?:amounts?|figures?)\s+)?(?:\bin\s+(?:₹\s*|Rs\.?\s*|INR\s*)?|"
    r"(?:₹|Rs\.?|INR)\s*(?:in\s+)?)"
    r"(?P<unit>crores?|cr\.?|millions?|lakhs?|lacs?)\b", re.I,
)
_OBJECT_TOKEN = r"(?:\d{1,3}(?:,\d{2})*,\d{3}|\d+)(?:\.\d+)?|\[\s*[●•*]\s*\]|[—–-]|Nil"
_OBJECT_ROW_MARKER = re.compile(r"^\s*(?:\d+[.)]?\s+|[A-Z][.)]\s+|[A-Z]\s{2,})", re.I)
_OBJECT_FOOTNOTE = re.compile(r"^(?:\*|\^|[†‡]|\(\d+\)(?:\s|$)|Notes?\s*[:.])", re.I)
_OBJECT_BARE_FOOTNOTE = re.compile(r"(?:\*+|\^|[†‡]|\(\d+\))")
_OBJECT_NOTE_TEXT = re.compile(
    r"^(?:Subject\s+to\b|The\s+(?:amount|proceeds|funds|cost|expenses|net|gross)\b|"
    r"For\s+(?:further\s+)?details\b|See\b|As\s+(?:per|certified|stated|set\s+out)\b|Our\s+Company\b)",
    re.I,
)
_OBJECT_TOTAL = re.compile(r"^(?:Grand\s+)?Total(?:\s|\(|\*|$)", re.I)
_OBJECT_NON_ALLOCATION = re.compile(
    r"^(?:Gross\b.*\bProceeds|Net\s+(?:Issue\s+)?Proceeds|Less\b|\(Less\))", re.I,
)


def _object_lines(text: str) -> list[dict[str, Any]]:
    """Keep physical layout and actual PDF pages, including across page breaks."""
    lines = []
    for page_index, page_text in enumerate(text.split("\f"), 1):
        page_number = page_index
        for line in page_text.splitlines():
            marker = re.fullmatch(r"\s*\[PAGE (\d+)\]\s*", line)
            if marker:
                page_number = int(marker.group(1))
                continue
            lines.append({"page": page_number, "text": line})
    return lines


def _object_unit(lines: list[dict[str, Any]], start: int, header: int):
    for source_line in reversed(lines[max(start, header - 8):header + 1]):
        units = list(_OBJECT_UNIT.finditer(source_line["text"]))
        if not units:
            continue
        names = {
            "million" if match["unit"].lower().startswith("million") else
            "lakh" if match["unit"].lower().startswith(("lakh", "lac")) else "crore"
            for match in units
        }
        if len(names) != 1:
            return None
        name = names.pop()
        return name, {"million": Decimal("0.1"), "lakh": Decimal("0.01"), "crore": Decimal("1")}[name], source_line
    return None


def _object_header(lines: list[dict[str, Any]], index: int):
    raw = lines[index]["text"]
    purpose = _OBJECT_PURPOSE_HEADER.search(raw)
    if not purpose:
        return None
    # A narrative mentioning a purpose and amount is not a table header.
    prefix = _space(raw[:purpose.start()])
    if prefix and not re.fullmatch(r"(?:Sr|S)\.?\s*(?:No|N)\.?", prefix, re.I):
        return None
    if not _object_header_fragment(raw):
        return None
    first, last = index, index
    while first > max(0, index - 2):
        prior = lines[first - 1]["text"]
        if _OBJECT_UNIT.search(prior) or not _object_header_fragment(prior):
            break
        first -= 1
    while last + 1 < min(len(lines), index + 4):
        if not _object_header_fragment(lines[last + 1]["text"]):
            break
        last += 1
    headers = lines[first:last + 1]
    joined = " ".join(row["text"] for row in headers)
    if not _OBJECT_AMOUNT_HEADER.search(joined):
        return None
    if (len(_OBJECT_AMOUNT_HEADER.findall(joined)) != 1
            or len(_OBJECT_PURPOSE_HEADER.findall(joined)) != 1
            or _OBJECT_FISCAL_HEADER.search(joined)):
        return {"unsupported": True}
    amount_line = next(row for row in headers if _OBJECT_AMOUNT_HEADER.search(row["text"]))
    amount = _OBJECT_AMOUNT_HEADER.search(amount_line["text"])
    if amount.start() <= purpose.end():
        return {"unsupported": True}
    # Compact text is accepted only for a single header and one amount per row.
    compact = (len(headers) == 1
               and not re.search(r" {2,}", raw[purpose.end():amount.start()]))
    return {
        "headers": headers, "next": last + 1, "amountColumn": amount.start(),
        "compact": compact, "percentage": bool(_OBJECT_PERCENT_HEADER.search(joined)),
    }


def _object_amount(token: str, factor: Decimal):
    if token.casefold() == "nil":
        return 0.0
    if token.startswith("[") or token in {"—", "–", "-"}:
        return None
    return float((Decimal(token.replace(",", "")) * factor).quantize(Decimal("0.000001")))


def _object_row_tail(raw: str, percentage: bool):
    percent = r"\s+(?P<percentage>\d+(?:\.\d+)?)\s*%?" if percentage else ""
    match = re.search(r"(?<!\S)(?:(?:₹|Rs\.?|INR)\s*)?(?P<amount>" + _OBJECT_TOKEN + r")" + percent + r"\s*$", raw, re.I)
    if not match or (percentage and not 0 <= float(match["percentage"]) <= 100):
        return None
    return match


def _object_purpose_span(raw: str, end: int):
    prefix = raw[:end]
    qualifier = re.search(r"(?:Up\s+to\s+)?(?:₹|Rs\.?|INR)\s*$|Up\s+to\s*$", prefix, re.I)
    if qualifier:
        end = qualifier.start()
    end = len(raw[:end].rstrip())
    marker = _OBJECT_ROW_MARKER.match(raw[:end])
    start = marker.end() if marker else len(raw[:end]) - len(raw[:end].lstrip())
    return (start, end) if start < end else None


def _bare_object_footnote_closes(lines: list[dict[str, Any]], index: int, header: dict[str, Any]) -> bool:
    """An isolated superscript can precede another row, so it cannot end a table."""
    for next_index in range(index + 1, min(len(lines), index + 9)):
        source_line = lines[next_index]
        flat = _space(source_line["text"])
        if source_line["page"] > lines[index]["page"] + 1:
            return False
        if not flat or re.fullmatch(r"Page\s+\d+\s+of\s+\d+|\d+", flat, re.I):
            continue
        if _OBJECT_BARE_FOOTNOTE.fullmatch(flat):
            continue
        if _OBJECT_TABLE_STOP.match(flat):
            return True
        if _object_header(lines, next_index) or _object_row_tail(source_line["text"], header["percentage"]):
            return False
        return bool(_OBJECT_NOTE_TEXT.match(flat) or _OBJECT_FOOTNOTE.match(flat))
    return False


def _object_table(lines: list[dict[str, Any]], index: int, heading_index: int, header: dict[str, Any], unit):
    """Read one allocation table; None skips a non-allocation reconciliation."""
    unit_name, factor, unit_line = unit
    source_rows = []
    pending = None
    invalid = False
    closed = False
    total_row = None
    table_scope = "unspecified"

    def finish():
        nonlocal pending, invalid
        if pending is None:
            return
        if "amountToken" not in pending:
            invalid = True
        else:
            pending["purpose"] = _space(" ".join(
                pending["lines"][span["line"]]["text"][span["start"]:span["end"]]
                for span in pending["purposeSpans"]
            ))
            source_rows.append(pending)
        pending = None

    table_end = min(len(lines), header["next"] + 70)
    for source_index in range(header["next"], table_end):
        source_line = lines[source_index]
        raw = source_line["text"]
        flat = _space(raw)
        if source_line["page"] > lines[index]["page"] + 1:
            invalid = True
            break
        if not flat:
            continue
        if re.fullmatch(r"Page\s+\d+\s+of\s+\d+|\d+", flat, re.I):
            continue
        row_flat = _space(_OBJECT_ROW_MARKER.sub("", raw, count=1))
        net_total = bool(re.match(r"Net\s+(?:Issue\s+)?Proceeds\b", row_flat, re.I))
        gross_total = bool(re.match(r"Gross\b.*\bProceeds\b", row_flat, re.I))
        if _OBJECT_TOTAL.match(row_flat) or ((net_total or gross_total) and (pending or source_rows)):
            tail = _object_row_tail(raw, header["percentage"])
            span = _object_purpose_span(raw, tail.start("amount")) if tail else None
            if not tail or not span:
                invalid = True
                break
            try:
                normalized = _object_amount(tail["amount"], factor)
            except (InvalidOperation, ValueError, OverflowError):
                invalid = True
                break
            total_row = {
                "page": source_line["page"], "purpose": _space(raw[span[0]:span[1]]),
                "amountToken": tail["amount"], "normalizedValue": normalized,
                "lines": [dict(source_line)], "purposeSpans": [{"line": 0, "start": span[0], "end": span[1]}],
                "amountSpan": {"line": 0, "start": tail.start("amount"), "end": tail.end("amount")},
            }
            gross_header = re.search(r"(?:%|Percentage|Per\s+cent)\s+of\s+Gross\b",
                                     " ".join(row["text"] for row in header["headers"]), re.I)
            table_scope = "net" if net_total else "gross" if gross_total or gross_header else "unspecified"
            closed = True
            break
        if _OBJECT_FOOTNOTE.match(flat):
            note_amount = _object_row_tail(raw, header["percentage"])
            if note_amount and (header["compact"] or note_amount.start("amount") >= header["amountColumn"] - 4):
                # Parenthesized numbering or a floating superscript may belong
                # to another allocation row, rather than a prose footnote.
                invalid = True
                break
            closed = (not _OBJECT_BARE_FOOTNOTE.fullmatch(flat)
                      or _bare_object_footnote_closes(lines, source_index, header))
            invalid = not closed
            break
        if _OBJECT_TABLE_STOP.match(flat) or _OBJECTS_HEADING.fullmatch(flat):
            closed = True
            break
        if _object_header(lines, source_index):
            # A repeated/new header does not prove that the preceding rows were
            # complete. Pagination remains unsupported until its rows are bound.
            invalid = True
            break
        if _OBJECT_NON_ALLOCATION.match(row_flat):
            return False if pending or source_rows else None
        tail = _object_row_tail(raw, header["percentage"])
        marker = _OBJECT_ROW_MARKER.match(raw)
        span = _object_purpose_span(raw, tail.start("amount") if tail else len(raw))
        purpose_piece = raw[span[0]:span[1]] if span else ""
        if tail:
            # An extra amount column must not become the end of a purpose.
            if re.search(r"(?:^|\s)\d[\d,]*(?:\.\d+)?\s*$", purpose_piece):
                invalid = True
                break
            if not header["compact"] and tail.start("amount") < header["amountColumn"] - 4:
                invalid = True
                break
            if marker or pending is None or "amountToken" in pending:
                finish()
                if not span:
                    invalid = True
                    break
                pending = {"page": source_line["page"], "lines": [], "purposeSpans": []}
            line_index = len(pending["lines"])
            pending["lines"].append(dict(source_line))
            if span:
                pending["purposeSpans"].append({"line": line_index, "start": span[0], "end": span[1]})
            token = tail["amount"]
            if len(token) > 40:
                invalid = True
                break
            try:
                normalized = _object_amount(token, factor)
            except (InvalidOperation, ValueError, OverflowError):
                invalid = True
                break
            pending.update({
                "amountToken": token, "normalizedValue": normalized,
                "amountSpan": {"line": line_index, "start": tail.start("amount"), "end": tail.end("amount")},
            })
        elif marker:
            finish()
            if not span or header["compact"]:
                invalid = True
                break
            pending = {
                "page": source_line["page"], "lines": [dict(source_line)],
                "purposeSpans": [{"line": 0, "start": span[0], "end": span[1]}],
            }
        elif pending and span and not header["compact"]:
            first = pending["purposeSpans"][0]
            if abs(span[0] - first["start"]) > 2 or raw[header["amountColumn"]:].strip():
                invalid = True
                break
            # Only the purpose column can wrap. Unexplained numeric cells stop acceptance.
            if re.search(r"(?:^|\s)\d[\d,]*(?:\.\d+)?\s*$", purpose_piece):
                invalid = True
                break
            line_index = len(pending["lines"])
            pending["lines"].append(dict(source_line))
            pending["purposeSpans"].append({"line": line_index, "start": span[0], "end": span[1]})
        else:
            invalid = True
            break
    if not closed and table_end < len(lines):
        invalid = True
    finish()
    if invalid:
        return False
    rows = []
    kept_sources = []
    seen = {}
    for row in source_rows:
        key = _object_purpose_key(row["purpose"])
        if key in seen:
            if seen[key] != row["normalizedValue"]:
                return False
            continue
        seen[key] = row["normalizedValue"]
        rows.append({"purpose": row["purpose"], "amountCr": row["normalizedValue"]})
        kept_sources.append(row)
    if not rows:
        return None
    if not valid_objects(rows):
        return False
    if (total_row and total_row["normalizedValue"] is not None
            and all(row["amountCr"] is not None for row in rows)
            and abs(sum(row["amountCr"] for row in rows) - total_row["normalizedValue"]) > max(1e-6, len(rows) * 1e-6)):
        return False
    heading_line = lines[heading_index]
    evidence = {
        "schemaVersion": 1, "page": heading_line["page"],
        "heading": _space(heading_line["text"]), "headingRaw": heading_line["text"],
        "unit": unit_name, "unitText": unit_line["text"], "unitPage": unit_line["page"],
        "tableHeaders": [dict(row) for row in header["headers"]],
        "rows": [dict(row) for row in rows], "sourceRows": kept_sources,
        "tableScope": table_scope,
    }
    if total_row:
        evidence["tableTotal"] = total_row
    return rows, evidence


def _object_net_gross_agree(net, gross) -> bool:
    net_rows, net_evidence = net
    gross_rows, gross_evidence = gross
    if net_evidence.get("tableScope") != "net" or gross_evidence.get("tableScope") != "gross":
        return False
    for rows, evidence in (net, gross):
        total = evidence.get("tableTotal", {}).get("normalizedValue")
        if (total is None or any(row["amountCr"] is None for row in rows)
                or abs(sum(row["amountCr"] for row in rows) - total) > max(1e-6, len(rows) * 1e-6)):
            return False
    non_expenses = [row for row in gross_rows if not is_issue_expense_purpose(row["purpose"])]
    if len(non_expenses) == len(gross_rows) or len(non_expenses) != len(net_rows):
        return False
    return all(_object_purpose_key(net_row["purpose"]) == _object_purpose_key(gross_row["purpose"])
               and net_row["amountCr"] == gross_row["amountCr"]
               for net_row, gross_row in zip(net_rows, non_expenses))


def extract_objects(text: str):
    """Accept only explicit, bounded purpose/allocation tables with raw evidence."""
    lines = _object_lines(str(text or ""))
    active_heading = None
    candidates = []
    for index, source_line in enumerate(lines):
        flat = _space(source_line["text"])
        if _OBJECTS_HEADING.fullmatch(flat):
            active_heading = index
            continue
        if active_heading is None:
            continue
        if (_OBJECT_TABLE_STOP.match(flat) or index - active_heading > 150
                or source_line["page"] > lines[active_heading]["page"] + 2):
            active_heading = None
            continue
        header = _object_header(lines, index)
        if not header:
            continue
        if header.get("unsupported"):
            return [], {}
        unit = _object_unit(lines, active_heading, index)
        if not unit:
            continue
        found = _object_table(lines, index, active_heading, header, unit)
        if found is False:
            return [], {}
        if found:
            candidates.append(found)
    if not candidates:
        return [], {}
    selected = candidates[0]
    corroborations = []
    for candidate in candidates[1:]:
        expected = [(_object_purpose_key(row["purpose"]), row["amountCr"]) for row in selected[0]]
        observed = [(_object_purpose_key(row["purpose"]), row["amountCr"]) for row in candidate[0]]
        if observed == expected:
            continue
        if _object_net_gross_agree(selected, candidate):
            corroborations.append(selected[1])
            selected = candidate
        elif _object_net_gross_agree(candidate, selected):
            corroborations.append(candidate[1])
        else:
            return [], {}
    rows, evidence = selected
    if corroborations:
        evidence["corroboratingSourceTables"] = corroborations
    return rows, {"objectsOfIssue": evidence}


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
    evidence = dict(out.get("fieldEvidence") or {})
    supplement_evidence = supplement.get("fieldEvidence") or {}
    # Values and their physical table proof must always come from the same parser.
    primary_objects_supported = (valid_objects(out.get("objectsOfIssue"))
                                 and not objects_evidence_problems(out["objectsOfIssue"], evidence.get("objectsOfIssue")))
    supplement_objects_supported = (valid_objects(supplement.get("objectsOfIssue"))
                                    and not objects_evidence_problems(supplement["objectsOfIssue"], supplement_evidence.get("objectsOfIssue")))
    if not primary_objects_supported and supplement_objects_supported:
        out["objectsOfIssue"] = supplement["objectsOfIssue"]
        evidence["objectsOfIssue"] = supplement_evidence["objectsOfIssue"]
    final_promoters_assessed = out.get("finalPromoterAssessment") in {"accepted", "unresolved"}
    if not out.get("leadManagers") and supplement.get("leadManagers"):
        out["leadManagers"] = supplement["leadManagers"]
    if not out.get("registrar") and supplement.get("registrar"):
        out["registrar"] = supplement["registrar"]
    if not final_promoters_assessed and not valid_promoters(out.get("promoters")) and valid_promoters(supplement.get("promoters")):
        out["promoters"] = supplement["promoters"]
    if not _valid_shareholding(out.get("shareholding")) and _valid_shareholding(supplement.get("shareholding")):
        out["shareholding"] = supplement["shareholding"]
    if not _has_financials(out.get("financials")) and _has_financials(supplement.get("financials")):
        out["financials"] = supplement["financials"]
    for key, value in supplement_evidence.items():
        if key == "objectsOfIssue":
            continue
        if key == "promoters" and final_promoters_assessed:
            continue
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
