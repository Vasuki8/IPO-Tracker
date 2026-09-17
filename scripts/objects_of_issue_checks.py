"""Conservative checks for objects-of-issue rows before canonical promotion.

Structural checks reject contents entries, share-lot metadata and malformed
values. The separate evidence contract binds every accepted allocation to its
observed table headers, monetary unit and physical source-row spans.
"""
from __future__ import annotations

import math
import re
from decimal import Decimal, InvalidOperation
from typing import Any


_CONTENTS_HEADING = re.compile(
    r"^(?:"
    r"(?:TABLE\s+OF\s+)?CONTENTS|"
    r"BASIS\s+FOR\s+(?:THE\s+)?(?:ISSUE|OFFER)\s+PRICE|"
    r"STATEMENT\s+OF\s+(?:POSSIBLE\s+)?(?:SPECIAL\s+)?TAX\s+BENEFITS|"
    r"SECTION\b\s*(?:[-–—:]\s*)?(?:[IVXLCDM]+|\d+)\b.*|"
    r"INDUSTRY\s+OVERVIEW|OUR\s+BUSINESS|"
    r"KEY\s+(?:INDUSTRY\s+)?REGULATIONS?(?:\s+AND\s+POLICIES)?(?:\s+IN\s+INDIA)?|"
    r"OUR\s+HISTORY|HISTORY\s+AND\s+(?:CERTAIN\s+)?CORPORATE\s+MATTERS|"
    r"OUR\s+MANAGEMENT|OUR\s+PROMOTERS?(?:\s+AND\s+PROMOTER\s+GROUP)?|"
    r"OUR\s+SUBSIDIARIES|(?:OUR\s+)?GROUP\s+COMPANIES|"
    r"DIVIDEND\s+POLICY|(?:RESTATED\s+)?FINANCIAL\s+INFORMATION|RISK\s+FACTORS"
    r")(?:\s+\d+)?[\s.:;\-–—]*$",
    re.I,
)
_DOT_LEADER = re.compile(r"(?:\.\s*){3,}|…")
_ROW_PREFIX = re.compile(r"^(?:\d+(?:\.\d+)*[.)]?|[A-Z][.)])\s+", re.I)
_TRAILING_NUMERIC_COLUMN = re.compile(r"\s[-+]?(?:\d[\d,]*\.\d+|\d{1,3}(?:,\d{2,3})+)$")
_PAGE_REFERENCE = re.compile(r"\bon\s+pages?\s*[.:;]?$", re.I)
_LOT_METADATA_LABEL = re.compile(
    r"^(?:Lot\s+Size|(?:The\s+)?(?:Minimum\s+)?(?:Market|Trading|Bid)\s+Lot(?:\s+Size)?)\b",
    re.I,
)
_LOT_METADATA_DETAIL = re.compile(
    r"^(?:"
    r"(?:and\s+)?(?:the\s+)?(?:minimum\s+)?(?:market|trading|bid)\s+lot\b|"
    r"(?:(?:for|of)\s+(?:the\s+)?)?(?:equity\s+)?shares?\b|"
    r"(?:(?:is|shall\s+be|will\s+be)\s+)?\d[\d,]*(?:\.\d+)?"
    r"(?:$|\s+(?:(?:equity\s+)?shares?\b|(?:and\s+)?in\s+multiples\b))"
    r")",
    re.I,
)


def _share_lot_metadata(purpose: str) -> bool:
    label = _LOT_METADATA_LABEL.match(purpose)
    if not label:
        return False
    detail = purpose[label.end():].strip(" :;=\u2013\u2014-")
    # A metadata label and quantity/definition cannot describe a use of proceeds.
    # Other continuations, such as production lot-size optimization, stay valid.
    return not detail or bool(_LOT_METADATA_DETAIL.match(detail))


def objects_problems(value: Any) -> list[str]:
    """Return problems in disclosed rows; absent objects are not an error."""
    if value is None or value == []:
        return []
    if not isinstance(value, list):
        return ["Expected an objects-of-issue list"]

    problems: list[str] = []
    for index, row in enumerate(value, 1):
        label = f"Objects-of-issue row {index}"
        if not isinstance(row, dict):
            problems.append(label + " must be an object")
            continue

        purpose = row.get("purpose")
        if not isinstance(purpose, str) or not purpose.strip():
            problems.append(label + " needs a nonempty purpose")
        else:
            normalized = " ".join(purpose.split())
            heading = _ROW_PREFIX.sub("", normalized)
            if _CONTENTS_HEADING.fullmatch(heading) or _DOT_LEADER.search(normalized):
                problems.append(label + " resembles a table-of-contents entry, not a use of proceeds")
            elif _share_lot_metadata(heading):
                problems.append(label + " describes a share lot or bid quantity, not a use of proceeds")
            elif _TRAILING_NUMERIC_COLUMN.search(normalized):
                problems.append(label + " purpose ends in a numeric table column; amount alignment needs review")
            elif _PAGE_REFERENCE.search(normalized):
                problems.append(label + " ends in a page reference; its page number is not a monetary amount")

        amount = row.get("amountCr")
        if amount is not None:
            valid_amount = isinstance(amount, (int, float)) and not isinstance(amount, bool)
            if valid_amount:
                try:
                    valid_amount = math.isfinite(amount) and amount >= 0
                except OverflowError:
                    valid_amount = False
            if not valid_amount:
                problems.append(label + " amount must be finite and non-negative, or null if undisclosed")
    return problems


def objects_quarantined(record: dict[str, Any]) -> bool:
    review = record.get("objectsOfIssueReview")
    return isinstance(review, dict) and review.get("status") == "quarantined"


_TABLE_HEADING = re.compile(
    r"(?:(?:[A-Z]|\d+)[.)]\s*)?(?:OBJECTS?\s+OF\s+(?:THE\s+)?(?:ISSUE|OFFER)|"
    r"UTILI[ZS]ATION\s+OF\s+(?:THE\s+)?(?:(?:NET|GROSS)\s+)?(?:(?:ISSUE|OFFER)\s+)?(?:PROCEEDS|FUNDS))\s*[:.]?",
    re.I,
)
_OBSERVED_UNIT = re.compile(
    r"(?:(?:₹|Rs\.?|INR|Rupees)\s*(?:in\s+)?|\bin\s+(?:(?:₹|Rs\.?|INR)\s*)?)"
    r"(crores?|cr\.?|millions?|lakhs?|lacs?)\b",
    re.I,
)
_SOURCE_NUMBER = re.compile(r"(?:\d+|\d{1,3}(?:,\d{2,3})+)(?:\.\d+)?")
_UNDISCLOSED_AMOUNT = re.compile(r"\[\s*[●•*]\s*\]|[●•*—–-]")


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def _positive_page(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def objects_header_fragment(raw: str) -> bool:
    """Recognize bounded allocation-column labels, including wrapped headers."""
    words = re.findall(r"[A-Za-z]+|20\d{2}", raw)
    permitted = {
        "sr", "s", "no", "n", "particular", "particulars", "purpose", "purposes", "object", "objects",
        "amount", "amounts", "cost", "estimated", "total", "proposed", "allocation", "of", "gross",
        "issue", "size", "proceeds", "percentage", "per", "cent", "to", "be", "funded", "from", "net",
        "in", "lakh", "lakhs", "lac", "lacs", "crore", "crores", "million", "millions", "rs", "inr",
        "deployment", "deployed", "fiscal", "fiscals", "financial", "year", "years", "fy",
    }
    return bool(words) and all(word.casefold() in permitted or re.fullmatch(r"20\d{2}", word) for word in words)


def objects_purpose_key(purpose: str) -> str:
    """Compare table scopes without changing the observed canonical wording."""
    value = re.sub(r"(?:\s*(?:\(\d+\)|\*+|[†‡#]))+$", "", purpose)
    value = _normalized_text(value).rstrip(" .;:").casefold()
    if re.fullmatch(r"working capital(?: expenditure)? requirements?", value):
        return "working capital requirement"
    if re.fullmatch(r"general corporate purposes?", value):
        return "general corporate purposes"
    return value


def is_issue_expense_purpose(purpose: str) -> bool:
    return bool(re.fullmatch(r"issue(?: related)? expenses?", objects_purpose_key(purpose)))


def _source_unit(text: str) -> str | None:
    units = set()
    for match in _OBSERVED_UNIT.finditer(text):
        token = match.group(1).lower()
        units.add("million" if token.startswith("million") else
                  "lakh" if token.startswith(("lakh", "lac")) else "crore")
    return next(iter(units)) if len(units) == 1 else None


def _source_amount(token: str, unit: str) -> tuple[bool, float | None]:
    if _UNDISCLOSED_AMOUNT.fullmatch(token):
        return True, None
    if token.casefold() == "nil":
        return True, 0.0
    if len(token) > 40 or not _SOURCE_NUMBER.fullmatch(token):
        return False, None
    try:
        factor = {"crore": Decimal("1"), "million": Decimal("0.1"), "lakh": Decimal("0.01")}[unit]
        amount = float((Decimal(token.replace(",", "")) * factor).quantize(Decimal("0.000001")))
    except (ValueError, OverflowError, KeyError, InvalidOperation):
        return False, None
    return (True, amount) if math.isfinite(amount) else (False, None)


def _objects_unit_span_problems(evidence: dict[str, Any]) -> list[str]:
    """Check a monetary-unit label split across physical table-header lines."""
    if "unitSourceLines" not in evidence and "unitSpans" not in evidence:
        return []
    sources, spans = evidence.get("unitSourceLines"), evidence.get("unitSpans")
    headers = evidence.get("tableHeaders")
    if (not isinstance(sources, list) or not sources
            or not isinstance(spans, list) or not spans
            or not isinstance(headers, list)
            or any(not isinstance(row, dict) or not _positive_page(row.get("page"))
                   or not isinstance(row.get("text"), str) or not row["text"].strip()
                   or "\n" in row["text"] or "\r" in row["text"] for row in sources)
            or any(not isinstance(row, dict) or not _positive_page(row.get("page"))
                   or not isinstance(row.get("text"), str) for row in headers)):
        return ["Wrapped objects unit needs physical source lines and spans from the table headers"]
    source_keys = [(row["page"], row["text"]) for row in sources]
    header_keys = [(row["page"], row["text"]) for row in headers]
    if (len(set(source_keys)) != len(source_keys)
            or any(key not in header_keys for key in source_keys)
            or [row["page"] for row in sources] != sorted(row["page"] for row in sources)
            or evidence.get("unitPage") != sources[0]["page"]):
        return ["Wrapped objects unit source lines must match distinct ordered table headers and the unit page"]
    header_positions = [header_keys.index(key) for key in source_keys]
    if header_positions != sorted(header_positions):
        return ["Wrapped objects unit source lines must follow physical table-header order"]

    parts = []
    previous_line, previous_end = -1, -1
    for span in spans:
        if not isinstance(span, dict):
            return ["Wrapped objects unit spans need valid physical source bounds"]
        line, start, end = span.get("line"), span.get("start"), span.get("end")
        if (not all(isinstance(part, int) and not isinstance(part, bool) for part in (line, start, end))
                or not 0 <= line < len(sources)
                or not 0 <= start < end <= len(sources[line]["text"])):
            return ["Wrapped objects unit spans need valid physical source bounds"]
        if line < previous_line or (line == previous_line and start < previous_end):
            return ["Wrapped objects unit spans must follow source order without duplication or overlap"]
        parts.append(sources[line]["text"][start:end])
        previous_line, previous_end = line, end
    if _normalized_text(" ".join(parts)) != evidence.get("unitText"):
        return ["Wrapped objects unit text must equal its physical source spans"]
    return []


def objects_evidence_problems(value: Any, evidence: Any) -> list[str]:
    """Check that each allocation equals a captured source-table row.

    Spans use zero-based physical-line indexes and half-open character offsets.
    They preserve the source text, including wrapped purposes, instead of
    manufacturing an evidence envelope from already normalized output. Source
    URL/hash and final-document identity are checked by the canonical policy.
    """
    problems = objects_problems(value)
    if value is None or value == [] or problems:
        return problems
    if (not isinstance(evidence, dict) or not isinstance(evidence.get("schemaVersion"), int)
            or evidence.get("schemaVersion") != 1 or isinstance(evidence.get("schemaVersion"), bool)):
        return ["Objects of issue need source-table evidence version 1"]
    if not _positive_page(evidence.get("page")):
        problems.append("Objects table needs a positive PDF heading page")
    heading, raw_heading = evidence.get("heading"), evidence.get("headingRaw")
    if (not isinstance(heading, str) or not isinstance(raw_heading, str)
            or "\n" in raw_heading or "\r" in raw_heading
            or _normalized_text(raw_heading) != heading
            or not _TABLE_HEADING.fullmatch(heading)):
        problems.append("Objects table needs an observed standalone objects or utilisation heading")

    unit, unit_text = evidence.get("unit"), evidence.get("unitText")
    if (unit not in ("crore", "million", "lakh") or not isinstance(unit_text, str)
            or _source_unit(unit_text) != unit or not _positive_page(evidence.get("unitPage"))):
        problems.append("Objects table needs an explicit matching monetary unit and PDF page")
    problems.extend(_objects_unit_span_problems(evidence))

    headers = evidence.get("tableHeaders")
    if (not isinstance(headers, list) or not headers
            or any(not isinstance(row, dict) or not _positive_page(row.get("page"))
                   or not isinstance(row.get("text"), str) or not row["text"].strip()
                   or "\n" in row["text"] or "\r" in row["text"] for row in headers)):
        problems.append("Objects table needs captured physical column headers")
        header_text = ""
    else:
        header_text = " ".join(row["text"] for row in headers)
    if (not re.search(r"\b(?:particulars?|purposes?|objects?)\b", header_text, re.I)
            or not re.search(r"\b(?:amount|cost)\b", header_text, re.I)
            or len(re.findall(r"\b(?:amount|cost)\b", header_text, re.I)) != 1
            or re.search(r"\b(?:FY\s*\d{2,4}|20\d{2}|fiscals?|financial\s+years?|deployment|schedule|already\s+spent)\b", header_text, re.I)):
        problems.append("Objects table needs purpose and allocation-amount columns, without a deployment schedule")
    purpose_headers = [re.search(r"\b(?:particulars?|purposes?|objects?)\b", row["text"], re.I)
                       for row in (headers if isinstance(headers, list) else [])
                       if isinstance(row, dict) and isinstance(row.get("text"), str)]
    amount_headers = [re.search(r"\b(?:amount|cost)\b", row["text"], re.I)
                      for row in (headers if isinstance(headers, list) else [])
                      if isinstance(row, dict) and isinstance(row.get("text"), str)]
    purposes, amounts = [match for match in purpose_headers if match], [match for match in amount_headers if match]
    if (not isinstance(headers, list)
            or any(not isinstance(row, dict) or not isinstance(row.get("text"), str)
                   or not objects_header_fragment(row["text"]) for row in headers)
            or len(purposes) != 1 or len(amounts) != 1
            or len(re.findall(r"\b(?:particulars?|purposes?|objects?)\b", header_text, re.I)) != 1
            or amounts[0].start() <= purposes[0].end()):
        problems.append("Objects evidence must retain identifiable purpose and amount column positions")
    percent_column = bool(re.search(r"%|\bpercentage\b|\bper\s+cent\b", header_text, re.I))

    source_rows = evidence.get("sourceRows")
    if evidence.get("rows") != value:
        problems.append("Objects evidence rows do not equal the accepted allocation list")
    if not isinstance(source_rows, list) or len(source_rows) != len(value):
        return problems + ["Every object needs exactly one matching physical source row"]

    seen_purposes: set[str] = set()
    prior_page = 0
    for index, (row, source_row) in enumerate(zip(value, source_rows), 1):
        label = f"Objects source row {index}"
        if not isinstance(source_row, dict):
            problems.append(label + " must be an object")
            continue
        purpose = source_row.get("purpose")
        if purpose != row.get("purpose"):
            problems.append(label + " purpose does not match the accepted object")
        if isinstance(purpose, str):
            key = _normalized_text(purpose).casefold()
            if key in seen_purposes:
                problems.append(label + " repeats an allocation purpose")
            seen_purposes.add(key)
        lines = source_row.get("lines")
        if (not isinstance(lines, list) or not lines
                or any(not isinstance(line, dict) or not _positive_page(line.get("page"))
                       or not isinstance(line.get("text"), str) or not line["text"].strip()
                       or "\n" in line["text"] or "\r" in line["text"] for line in lines)):
            problems.append(label + " needs physical text lines and PDF pages")
            continue
        pages = [line["page"] for line in lines]
        if (not _positive_page(source_row.get("page")) or source_row["page"] != pages[0]
                or pages != sorted(pages) or pages[0] < prior_page):
            problems.append(label + " has inconsistent PDF row pages")
        prior_page = pages[-1]
        table_pages = [header.get("page") for header in (headers if isinstance(headers, list) else []) if isinstance(header, dict)]
        if table_pages and all(_positive_page(page) for page in table_pages) and pages[-1] > max(table_pages) + 1:
            problems.append(label + " lies beyond the bounded allocation table")
        if index == 1:
            heading_page, unit_page = evidence.get("page"), evidence.get("unitPage")
            header_pages = [header.get("page") for header in (headers if isinstance(headers, list) else []) if isinstance(header, dict)]
            if (_positive_page(heading_page) and _positive_page(unit_page)
                    and all(_positive_page(page) for page in header_pages)
                    and (not heading_page <= unit_page <= pages[0]
                         or pages[0] - unit_page > 1
                         or header_pages != sorted(header_pages)
                         or any(not heading_page <= page <= pages[0] or pages[0] - page > 1 for page in header_pages))):
                problems.append("Objects heading, unit and column headers must precede the same source table")
        used: dict[int, list[tuple[int, int]]] = {}

        def read_span(span: Any) -> str | None:
            if not isinstance(span, dict):
                return None
            line_index, start, end = span.get("line"), span.get("start"), span.get("end")
            if not all(isinstance(part, int) and not isinstance(part, bool) for part in (line_index, start, end)):
                return None
            if not (0 <= line_index < len(lines) and 0 <= start < end <= len(lines[line_index]["text"])):
                return None
            spans = used.setdefault(line_index, [])
            if any(start < old_end and end > old_start for old_start, old_end in spans):
                return None
            spans.append((start, end))
            return lines[line_index]["text"][start:end]

        purpose_spans = source_row.get("purposeSpans")
        parts = [read_span(span) for span in purpose_spans] if isinstance(purpose_spans, list) else []
        if (not parts or any(part is None for part in parts)
                or _normalized_text(" ".join(part or "" for part in parts)) != purpose):
            problems.append(label + " purpose must equal its physical source spans")
        elif [(span["line"], span["start"]) for span in purpose_spans] != sorted(
                (span["line"], span["start"]) for span in purpose_spans):
            problems.append(label + " purpose spans must follow physical source order")
        amount_text = read_span(source_row.get("amountSpan"))
        token = source_row.get("amountToken")
        if not isinstance(token, str) or amount_text != token or token != token.strip():
            problems.append(label + " amount token must equal its physical source span")
        if "amountAnnotationSpans" in source_row:
            annotations = source_row["amountAnnotationSpans"]
            amount_span = source_row.get("amountSpan")
            if not isinstance(annotations, list) or not 1 <= len(annotations) <= 3:
                problems.append(label + " amount annotations need bounded physical source spans")
            else:
                for annotation in annotations:
                    fragment = read_span(annotation)
                    if (fragment is None or not re.fullmatch(r"(?:\s*(?:\(+\d+\)|[*†‡#^]))+", fragment)
                            or amount_text is None
                            or not isinstance(amount_span, dict)
                            or annotation.get("line") != amount_span.get("line")
                            or annotation.get("start", -1) < amount_span.get("end", 0)):
                        problems.append(label + " amount annotation must be a trailing observed footnote")
        valid_amount, expected = _source_amount(token, unit) if isinstance(token, str) and isinstance(unit, str) else (False, None)
        normalized = source_row.get("normalizedValue")
        if (not valid_amount or "normalizedValue" not in source_row
                or isinstance(normalized, bool) or normalized != expected or row.get("amountCr") != expected):
            problems.append(label + " amount must match the source token and monetary-unit conversion")

        percentages = 0
        for line_index, line in enumerate(lines):
            raw = line["text"]
            numbering = re.match(r"^\s*(?:(?:\(?\d+\)?[.)]?|[A-Z][.)])\s+|[A-Z]\s{2,})", raw, re.I)
            first_cell = min((start for start, _end in used.get(line_index, [])), default=0)
            if numbering and numbering.end() <= first_cell:
                raw = " " * numbering.end() + raw[numbering.end():]
            for start, end in sorted(used.get(line_index, []), reverse=True):
                raw = raw[:start] + " " * (end - start) + raw[end:]
            remainder = _normalized_text(raw)
            remainder = re.sub(r"\bUp\s+to\b|₹|\bRs\.?(?=\s|$)|\b(?:INR|Rupees)\b", "", remainder, flags=re.I).strip()
            if not remainder:
                continue
            if percent_column and re.fullmatch(r"\d+(?:\.\d+)?\s*%?", remainder):
                percent = float(remainder.rstrip("% "))
                amount_span = source_row.get("amountSpan")
                amount_end = amount_span.get("end") if isinstance(amount_span, dict) else None
                numeric_start = re.search(r"\d", raw)
                if (percent <= 100 and isinstance(amount_span, dict) and amount_span.get("line") == line_index
                        and isinstance(amount_end, int) and numeric_start and numeric_start.start() >= amount_end):
                    percentages += 1
                    continue
            problems.append(label + " has text or numeric columns outside its captured allocation cells")
        if percentages > 1:
            problems.append(label + " has more than one percentage column")
    if problems:
        return problems
    return _objects_scope_problems(value, evidence)


def _objects_proceeds_reconciliation_problems(
        value: list[dict[str, Any]], evidence: dict[str, Any]) -> list[str]:
    """Bind allocation totals to separately disclosed issuer net proceeds.

    A reconciliation is a source table, not another allocation list. Its
    explicit Fresh Issue or Issue scope prevents an unrelated expense table
    from being treated as funds available to the issuer.
    """
    if "proceedsReconciliation" not in evidence:
        return []
    tables = evidence["proceedsReconciliation"]
    if not isinstance(tables, list) or not 1 <= len(tables) <= 3:
        return ["Objects proceeds reconciliation must contain one to three standalone source tables"]

    problems = []
    allocations = [row for row in value if not is_issue_expense_purpose(row["purpose"])]
    if not allocations or any(row.get("amountCr") is None for row in value):
        problems.append("Objects proceeds reconciliation requires fully disclosed non-expense allocations")
        allocation_total = None
    else:
        allocation_total = sum((Decimal(str(row["amountCr"])) for row in allocations), Decimal("0"))

    expected_labels = (
        r"(?:gross\s+proceeds(?:\s+(?:of|from)\s+(?:the\s+)?(?:fresh\s+)?(?:issue|offer))?|gross\s+(?:issue|offer)\s+proceeds)",
        r"(?:\(less\)|less)\s*:?\s*(?:(?:public\s+)?(?:issue|offer)(?:[\s-]+related)?\s+)?expenses?"
        r"(?:\s+(?:in\s+relation\s+to|of|for)\s+(?:the\s+)?(?:fresh\s+)?(?:issue|offer))?",
        r"net\s+(?:(?:issue|offer)\s+)?proceeds(?:\s+(?:of|from)\s+(?:the\s+)?(?:fresh\s+)?(?:issue|offer))?",
    )
    prior_amounts = None
    for index, table in enumerate(tables, 1):
        label = f"Objects proceeds reconciliation {index}"
        if (not isinstance(table, dict)
                or any(key in table for key in ("proceedsReconciliation", "corroboratingSourceTables", "tableTotal"))
                or not isinstance(table.get("rows"), list) or len(table["rows"]) != 3):
            problems.append(label + " needs exactly three rows in a standalone source table")
            continue
        source_rows = table["rows"]
        if objects_evidence_problems(source_rows, table):
            problems.append(label + " lacks matching standalone source evidence")
            continue
        # Some PDFs repeat an opening parenthesis around a numeric footnote.
        # Normalize only that bounded suffix for role comparison; raw purposes
        # and their physical spans remain unchanged.
        labels = [re.sub(r"(?:\s*(?:\(+\d+\)|\*+|[†‡#]))+$", "", row["purpose"]).strip().casefold()
                  for row in source_rows]
        if any(not re.fullmatch(pattern, normalized, re.I)
               for pattern, normalized in zip(expected_labels, labels)):
            problems.append(label + " needs explicit gross Fresh Issue, issuer expenses and Net Proceeds rows in order")
            continue
        ambiguous_scope = labels[0] == "gross proceeds" or bool(re.search(r"\boffer\b", labels[0]))
        if ambiguous_scope:
            context = table.get("issuerProceedsContext")
            first_page = table["sourceRows"][0]["page"]
            if (not isinstance(context, list) or not 1 <= len(context) <= 3
                    or any(not isinstance(row, dict) or not _positive_page(row.get("page"))
                           or not table["page"] <= row["page"] <= first_page
                           or not isinstance(row.get("text"), str) or "\n" in row["text"]
                           or not re.fullmatch(
                               r"(?:The\s+)?Fresh\s+Issue|The\s+details\s+of\s+the\s+(?:net\s+)?proceeds\s+of\s+the\s+Fresh\s+Issue\b.{0,120}(?:below|follows)[:.]?",
                               _normalized_text(row["text"]), re.I) for row in context)):
                problems.append(label + " needs observed Fresh Issue context for bare or Offer proceeds labels")
        if any(row.get("amountCr") is None for row in source_rows):
            problems.append(label + " requires disclosed amounts for gross proceeds, expenses and net proceeds")
            continue
        amounts = tuple(Decimal(str(row["amountCr"])) for row in source_rows)
        gross, expenses, net = amounts
        tolerance = Decimal("0.000003")
        if abs(gross - expenses - net) > tolerance:
            problems.append(label + " does not reconcile gross Fresh Issue less issuer expenses to Net Proceeds")
        if prior_amounts is not None and any(abs(before - after) > tolerance
                                             for before, after in zip(prior_amounts, amounts)):
            problems.append("Objects proceeds reconciliation tables disagree on gross proceeds, expenses or net proceeds")
        prior_amounts = amounts
        allocation_tolerance = Decimal("0.000001") * max(1, len(allocations))
        if allocation_total is not None and abs(allocation_total - net) > allocation_tolerance:
            problems.append("Objects allocations excluding explicit issue expenses do not reconcile to disclosed Net Proceeds")
    return problems


def _objects_scope_problems(value: list[dict[str, Any]], evidence: dict[str, Any]) -> list[str]:
    """Verify disclosed totals and narrowly reconciled net/gross summaries."""
    problems = _objects_proceeds_reconciliation_problems(value, evidence)
    total = evidence.get("tableTotal")
    scope = evidence.get("tableScope", "unspecified")
    if scope not in ("net", "gross", "unspecified"):
        problems.append("Objects table has an unsupported proceeds scope")
    if total is not None:
        if not isinstance(total, dict):
            return ["Objects table total needs its physical source row"]
        total_value = [{"purpose": total.get("purpose"), "amountCr": total.get("normalizedValue")}]
        standalone = {key: val for key, val in evidence.items()
                      if key not in {"tableTotal", "tableScope", "corroboratingSourceTables", "proceedsReconciliation"}}
        standalone.update(rows=total_value, sourceRows=[total])
        if objects_evidence_problems(total_value, standalone):
            problems.append("Objects table total must match its physical source cells")
        elif (total.get("normalizedValue") is not None and all(row.get("amountCr") is not None for row in value)
                and abs(math.fsum(row["amountCr"] for row in value) - total["normalizedValue"]) > max(1, len(value)) * 0.000001):
            problems.append("Objects allocations do not reconcile to the disclosed table total")
    total_label = objects_purpose_key(str((total or {}).get("purpose") or ""))
    if total is not None and not re.fullmatch(
            r"(?:grand\s+)?total(?:\s+(?:(?:ipo|issue|offer)\s+)?proceeds)?|(?:net|gross)\s+(?:issue\s+)?proceeds",
            total_label, re.I):
        problems.append("Objects total must be explicitly labelled Total, Net Proceeds or Gross Proceeds")
    if (isinstance(total, dict) and _positive_page(total.get("page"))
            and total["page"] < evidence["sourceRows"][-1]["lines"][-1]["page"]):
        problems.append("Objects table total must follow its allocation rows")
    if scope == "net" and not re.fullmatch(r"Net\s+(?:Issue\s+)?Proceeds", total_label, re.I):
        problems.append("Net allocation scope requires an explicit Net Proceeds total")
    if scope == "gross":
        header_text = " ".join(row["text"] for row in evidence["tableHeaders"])
        if re.fullmatch(r"Net\s+(?:Issue\s+)?Proceeds", total_label, re.I):
            problems.append("An explicitly net total cannot close a gross allocation table")
        if (not re.search(r"(?:%|percentage|per\s+cent)\s+of\s+(?:the\s+)?Gross", header_text, re.I)
                and not re.fullmatch(r"Gross\s+(?:Issue\s+)?Proceeds", total_label, re.I)):
            problems.append("Gross allocation scope requires an explicit gross-proceeds label")

    corroboration = evidence.get("corroboratingSourceTables")
    if corroboration is None:
        return problems
    if not isinstance(corroboration, list) or not 1 <= len(corroboration) <= 3:
        return problems + ["Objects corroboration must contain bounded standalone source tables"]
    if (scope != "gross" or not isinstance(total, dict) or total.get("normalizedValue") is None
            or any(row.get("amountCr") is None for row in value)):
        return problems + ["Net/gross reconciliation requires a complete gross allocation table and total"]
    gross_objects = [(objects_purpose_key(row["purpose"]), row["amountCr"])
                     for row in value if not is_issue_expense_purpose(row["purpose"])]
    expenses = [row for row in value if is_issue_expense_purpose(row["purpose"])]
    if not expenses or not gross_objects:
        problems.append("Net/gross reconciliation may add only explicit issue expenses")
    for table in corroboration:
        if (not isinstance(table, dict) or "corroboratingSourceTables" in table
                or not isinstance(table.get("rows"), list) or not table["rows"]
                or objects_evidence_problems(table["rows"], table)):
            problems.append("Corroborating objects table lacks matching standalone source evidence")
            continue
        net_total = table.get("tableTotal")
        if (table.get("tableScope") != "net" or not isinstance(net_total, dict)
                or net_total.get("normalizedValue") is None
                or any(row.get("amountCr") is None for row in table["rows"])):
            problems.append("Corroborating table must disclose its net allocation scope and total")
            continue
        net_objects = [(objects_purpose_key(row["purpose"]), row["amountCr"]) for row in table["rows"]]
        if net_objects != gross_objects:
            problems.append("Net and gross summaries disagree on their non-expense allocations")
    return problems
