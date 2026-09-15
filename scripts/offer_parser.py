"""Current offer-document parser with bounded table/role extraction.

Only explicitly headed financial rows with a matching reporting-period header
are accepted. Older recognition strategies remain private compatibility code
for other fields; they cannot supply financials or intermediary names.
"""
from __future__ import annotations

import io
import re
import shutil
import subprocess
from collections import OrderedDict

from pypdf import PdfReader
from parser_loader import isolated_module

PARSER_VERSION = 21
_legacy = isolated_module("run_offer_docs_v14")
base = _legacy.base
choose_document = _legacy.choose_document
download_pdf = _legacy.download_pdf
extract_lot_size = _legacy.extract_lot_size
extract_price_band = _legacy.extract_price_band

_METRICS = [
    ("ronwPct", r"(?:Return\s+on\s+Net\s*Worth|RoNW)"),
    ("roePct", r"(?:Return\s+on\s+Equity|ROE)"),
    ("netWorthCr", r"Net\s*Worth"),
    ("revenueCr", r"(?:Revenue\s+from\s+Operations?|Total\s+Revenue)"),
    ("totalIncomeCr", r"Total\s+Income"),
    ("ebitdaCr", r"(?:(?:Operating\s+)?EBITDA)(?!\s+Margin)"),
    ("patCr", r"(?:(?:Restated\s+)?(?:Net\s+)?Profit\s*(?:/\s*\(?loss\)?)?\s+(?:after\s+Tax(?:ation)?|for\s+the\s+(?:year|period)(?:\s*/\s*(?:year|period))?)|PAT)(?!\s+Margin)"),
    ("dilutedEps", r"(?:Diluted\s+(?:Earnings?\s+per\s+(?:Equity\s+)?Share|EPS))"),
    ("eps", r"(?:(?:Basic(?:\s+and\s+Diluted)?\s+)?Earnings?\s+per\s+(?:Equity\s+)?Share|Basic\s+EPS)"),
]
_ROWS = [(key, re.compile(r"^\s*(?:\d+[.)]?\s+)?" + label + r"\b", re.I)) for key, label in _METRICS]
_HEADING = re.compile(r"^\s*(?:\d+[.)]?\s*)?(?:(?:Summary\s+of\s+)?(?:the\s+)?(?:Restated\s+(?:(?:Consolidated|Standalone)\s+)?)?Financial\s+(?:Information|Statements)|Summary\s+of\s+(?:Key\s+)?Financial\s+(?:Information|Statements)|Key\s+Performance\s+Indicators(?:\s*\(KPIs?\))?|Key\s+Financial\s+Information)\s*[:.]?\s*$", re.I)
_YEAR = re.compile(r"\b(?:Fiscal|FY)\s*(20\d{2})\b|(?:March\s+31|31\s+March)[,\s]+(20\d{2})", re.I)
_TOKEN = re.compile(r"\(?[-+]?\d[\d,]*(?:\.\d+)?\)?%?|\[\s*[●•*]\s*\]|(?<!\w)[—–-](?!\w)")
_UNIT = re.compile(r"(?:₹|Rs\.?|INR)\s*(?:in\s+)?(crores?|millions?|lakhs?|lacs?|thousands?)", re.I)
_LEGAL = re.compile(r"\b(?:Private\s+Limited|Pvt\.?\s+Ltd\.?|Limited|Ltd\.?|LLP)\b", re.I)
_ROLE = re.compile(r"^\s*(?:\d+[.)]\s+)?(?:DETAILS\s+OF\s+(?:THE\s+)?)?(?:BOOK\s+RUNNING\s+LEAD\s+MANAGERS?(?:\s+TO\s+THE\s+(?:ISSUE|OFFER))?|LEAD\s+MANAGERS?(?:\s+TO\s+THE\s+(?:ISSUE|OFFER))?|BRLMS?)\s*[:\-]?\s*$", re.I)
_REGISTRAR = re.compile(r"^\s*(?:\d+[.)]\s+)?(?:DETAILS\s+OF\s+(?:THE\s+)?)?REGISTRAR\s+(?:TO\s+THE\s+(?:ISSUE|OFFER)|AND\s+SHARE\s+TRANSFER\s+AGENT)\s*[:\-]?\s*$", re.I)


def valid_entity(name):
    value = " ".join(str(name or "").split())
    if value.casefold() == 'bnp paribas':
        return True
    return bool(_LEGAL.search(value) and len(value.split()) >= 3 and not re.search(
        r"^(?:BSE|NSE|India|Issue|Offer)\s+Limited$|National\s+Stock\s+Exchange|(?:CONTACT|TELEPHONE|EMAIL|E-MAIL|BRLM|LOGO)|\bTEL\s*:|^(?:Manager|as)\b|Book\s+Built\s+Issue|^BNP\s+Paribas\s+|^(?!360\s+ONE\b)\d+\s", value, re.I) and value.count('(') == value.count(')'))


def valid_manager(name):
    return valid_entity(name) and bool(re.search(r'Capital|Securit|Financial|Finserv|Advis|Invest|Corporate|Merchant|Markets|Bank|Fiscal|Broking|Brokers|Wealth|WAM|Management|Consult|Shares|Morgan\s+Stanley|J\.?\s*P\.?\s*Morgan|Jefferies|BNP\s+Paribas', str(name), re.I))


def valid_registrar(name):
    return valid_entity(name) and bool(re.search(r'Technolog|Services|Fintech|Registry|Registrars|Intime|Sharegistry|Consultancy|Assignments|Computershare', str(name), re.I))


def _unit(text):
    hits = list(_UNIT.finditer(text))
    if not hits:
        return None
    name = hits[-1].group(1).lower()
    return ("million", 0.1) if name.startswith("million") else ("lakh", 0.01) if name.startswith(("lakh", "lac")) else ("thousand", 0.0001) if name.startswith("thousand") else ("crore", 1.0)


def _years(line):
    found = [a or b for a, b in _YEAR.findall(line)]
    if len(found) >= 2 and len(found) == len(set(found)):
        return found
    return []


def _numbers(tail, count):
    # Parenthesized footnote markers immediately following the row label are
    # removed before reading cells; parenthesized numeric cells remain negative.
    tail = re.sub(r"^\s*(?:\((?:PAT|EPS|ROE|RONW)\)|\(\s*in\s*[%₹]\s*\)|\(\s*%\s*\))\s*", "", tail, flags=re.I)
    tail = re.sub(r"^(?:\((?:[A-Za-z]|\d{1,2})\)|\[\d{1,2}\])+", "", tail)
    tail = _UNIT.sub("", tail)
    tail = re.sub(r"\b(?:in|times|per\s+share|Rs|INR)\b|[₹%]", " ", tail, flags=re.I)
    tokens = _TOKEN.findall(tail)
    if len(tokens) == count + 1 and re.match(r"^\s*\(\d{1,2}\)", tail):
        tail = re.sub(r"^\s*\(\d{1,2}\)", "", tail)
        tokens = _TOKEN.findall(tail)
    remainder = _TOKEN.sub("", tail)
    if re.search(r"[A-Za-z]", remainder) or len(tokens) != count:
        return None
    values = []
    for token in tokens:
        if "●" in token or "•" in token or token in {"-", "—", "–"}:
            values.append(None)
        else:
            negative = token.startswith("(")
            value = float(token.strip("()%").replace(",", ""))
            values.append(-value if negative else value)
    return values



_DATE_LABEL = re.compile(r"March\s+31|31\s+March|September\s+30|30\s+September|December\s+31|31\s+December|June\s+30|30\s+June", re.I)
_INTERIM = re.compile(r"months?|September|December|June", re.I)


def _period_columns(lines, index):
    line = lines[index]
    context = lines[max(0, index - 5):index]
    years = list(re.finditer(r"\b20\d{2}\b", line))
    explicit = list(_YEAR.finditer(line))
    if len(explicit) >= 2:
        annual = [n for n, year in enumerate(years) if any(hit.start() <= year.start() < hit.end() for hit in explicit)]
        annual_years = [years[n][0] for n in annual]
        if len(annual_years) != len(set(annual_years)):
            return None
        return {"years": [year[0] for year in years], "annual": annual, "positions": [(year.start() + year.end()) / 2 for year in years], "interim": bool(_INTERIM.search("\n".join(context))), "header": "\n".join(context + [line])}
    if not years:
        return None
    prefix = line[:years[0].start()].strip()
    if prefix and not re.fullmatch(r"(?:Particulars|no\.?|Sr\.?\s*no\.?|period\s+ended|months|Financial\s+Year)", prefix, re.I):
        return None
    if not re.fullmatch(r"\s*20\d{2}(?:\s+20\d{2}){1,4}\s*", line[years[0].start():]):
        return None
    for date_line in reversed(context):
        dates = list(_DATE_LABEL.finditer(date_line))
        if len(dates) == len(years):
            annual = [n for n, hit in enumerate(dates) if "march" in hit[0].lower()]
            # Every extra column must have an explicit non-March reporting date.
            if len(annual) >= 2 and (len(annual) < len(years) or not _INTERIM.search("\n".join(context))):
                selected = [years[n][0] for n in annual]
                if len(selected) == len(set(selected)):
                    return {"years": [year[0] for year in years], "annual": annual, "positions": [(year.start() + year.end()) / 2 for year in years], "interim": False, "header": "\n".join(context + [line])}
    if len(years) == len({year[0] for year in years}) and re.search(r"March\s+31|31\s+March|Fiscal", "\n".join(context), re.I):
        interim = bool(_INTERIM.search("\n".join(context)))
        return {"years": [year[0] for year in years], "annual": list(range(len(years))), "positions": [(year.start() + year.end()) / 2 for year in years], "interim": interim, "header": "\n".join(context + [line])}
    return None


def _annual_values(tail, columns, offset):
    count = len(columns["years"])
    values = _numbers(tail, count)
    if values is not None and (not columns["interim"] or columns["annual"] != list(range(count))):
        return [values[n] for n in columns["annual"]], columns["annual"]
    # Some headers print only the fiscal years beside a separately headed
    # interim column. Prove horizontal alignment before dropping leading cells.
    if not columns["interim"] or columns["annual"] != list(range(count)):
        return None, []
    for extra in (0, 1, 2):
        values = _numbers(tail, count + extra)
        tokens = list(_TOKEN.finditer(tail))
        if len(tokens) == count + extra + 1 and re.match(r"^\s*\(\d{1,2}\)", tail):
            tokens = tokens[1:]
        if values is None or len(tokens) != count + extra:
            continue
        centers = [offset + (hit.start() + hit.end()) / 2 for hit in tokens]
        expected = columns["positions"]
        spacing = min((b - a for a, b in zip(expected, expected[1:])), default=0)
        tolerance = max(4, spacing * 0.42)
        if spacing >= 10 and (extra == 0 or centers[extra - 1] < expected[0] - spacing * 0.5) and all(abs(a - b) <= tolerance for a, b in zip(centers[extra:], expected)):
            return values[extra:], list(range(extra, count + extra))
    return None, []


def extract_financials_with_evidence(text):
    periods, evidence, conflicts = OrderedDict(), {}, set()
    previous_header_tail = []
    observations = {}
    pages = str(text or "").replace("\u00a0", " ").split("\f")
    for page_index, page in enumerate(pages, 1):
        page_number = re.search(r"\[PAGE (\d+)\]", page)
        page_no = int(page_number[1]) if page_number else page_index
        actual_lines = page.splitlines()
        prefix_length = len(previous_header_tail)
        lines = previous_header_tail + actual_lines
        headers, financial_section = [], bool(previous_header_tail)
        scope = "unspecified"
        previous_header_tail = actual_lines[-12:] if any(_HEADING.search(line) for line in actual_lines) else []
        for i, line in enumerate(lines):
            if _HEADING.search(line) and not re.search(r"\.{3,}", line):
                financial_section = True
                scope = "consolidated" if re.search(r"\bconsolidated\b", line, re.I) else "standalone" if re.search(r"\bstandalone\b", line, re.I) else "unspecified"
            if re.match(r"^\s*(?:\d+[.)]\s*)?(?:Risk\s+Factors|Objects\s+of\s+the|Comparison\s+with|Peer\s+Comparison|Related\s+Party|Our\s+Group\s+Companies|Industry\s+Overview)", line, re.I):
                financial_section = False
                headers = []
            columns = _period_columns(lines, i)
            if columns and (financial_section or re.search(r"Particulars|Performance\s+Indicators", line, re.I)):
                context = "\n".join(lines[max(0, i - 8):i + 1])
                explicit_scopes = {name for name in ("consolidated", "standalone") if re.search(r"\b" + name + r"\b", context, re.I)}
                table_scope = next(iter(explicit_scopes)) if len(explicit_scopes) == 1 else scope
                headers.append((i, columns, line, table_scope))
            metric = next(((key, pattern.match(line)) for key, pattern in _ROWS if pattern.match(line)), None)
            if i < prefix_length or not metric or not headers or i - headers[-1][0] > 28:
                continue
            key, match = metric
            header_i, columns, header, table_scope = headers[-1]
            years = [columns['years'][n] for n in columns['annual']]
            tail = line[match.end():]
            values, source_columns = _annual_values(tail, columns, match.end())
            if values is None and not _TOKEN.search(re.sub(r"\(\d+\)", "", tail)):
                # Vertical PDF cells are accepted only as an exact numeric block.
                for stop in range(i + 1, min(len(lines), i + len(years) + 3)):
                    tail += " " + lines[stop]
                    values, source_columns = _annual_values(tail, columns, match.end())
                    if values is not None:
                        break
                    if any(pattern.match(lines[stop]) for _, pattern in _ROWS):
                        break
            if values is None:
                continue
            unit = _unit("\n".join(lines[max(0, header_i - 8):i + 1]))
            if key.endswith("Cr") and unit is None:
                continue
            for year, value in zip(years, values):
                period = f"FY{year}"
                row = periods.setdefault(period, {"period": period})
                if value is None:
                    continue
                value = round(value * unit[1], 6) if key.endswith("Cr") else value
                path = period + "." + key
                cell = {"page": page_no, "header": columns["header"].strip()[-650:], "row": line.strip()[:400], "sourceColumns": source_columns, "normalizedValue": value, "scope": table_scope, "originalUnit": unit[0] if key.endswith("Cr") else ("percent" if key.endswith("Pct") else "rupees per share")}
                observations.setdefault(path, []).append((value, cell))
    for path, candidates in observations.items():
        # Explicit consolidated issuer figures take precedence over standalone
        # figures. An unlabelled disagreement still requires source review.
        if any(cell.get("scope") == "consolidated" for _, cell in candidates):
            candidates = [(value, cell) for value, cell in candidates if cell.get("scope") != "standalone"]
        value, cell = candidates[0]
        if any(abs(other - value) > max(0.00001, abs(value) * 0.0001) for other, _ in candidates):
            conflicts.add(path)
            continue
        period, key = path.split(".", 1)
        periods.setdefault(period, {"period": period})[key] = value
        evidence[path] = cell
    rows = [row for row in periods.values() if len(row) > 1]
    if len(rows) < 2 or len({key for row in rows for key in row if key != "period"}) < 2:
        return None, {}, sorted(conflicts)
    return {"unit": "₹ crore", "periods": rows}, evidence, sorted(conflicts)


def extract_financials(text):
    return extract_financials_with_evidence(text)[0]


def extract_intermediaries(text):
    # Keep PDF column positions until the contact column has been removed.
    # Only the first explicit role table is used; later mentions often describe
    # historical mandates or selling shareholders rather than this offer.
    output, evidence = {}, {}
    role_tail = []
    for page_index, page in enumerate(str(text or "").split("\f")[:5], 1):
        marker = re.search(r"\[PAGE (\d+)\]", page)
        page_no = int(marker[1]) if marker else page_index
        actual_lines = page.splitlines()
        lines = role_tail + actual_lines
        role_tail = []
        for index in range(max(0, len(actual_lines) - 12), len(actual_lines)):
            if _REGISTRAR.match(actual_lines[index]) or _ROLE.match(actual_lines[index]):
                role_tail = actual_lines[index:]
                break
        consumed = set()
        for i, line in enumerate(lines):
            if i in consumed:
                continue
            registrar_header = bool(re.match(r'^\s*NAME\s+OF\s+(?:THE\s+)?REGISTRAR\b', line, re.I))
            role = "leadManagers" if _ROLE.match(line) else "registrar" if _REGISTRAR.match(line) or registrar_header else None
            if role is None or role in output:
                continue
            block = [line] if registrar_header else []
            for offset, candidate in enumerate(lines[i + 1:i + 30], i + 1):
                if re.match(r'^\s*(?:OUR\s+PROMOTERS|GENERAL\s+INFORMATION|SUMMARY|ABOUT\s+(?:OUR|THE)|PROMOTERS?\b)', candidate, re.I):
                    break
                if re.fullmatch(r'\s*(?:Lead\s+)?Managers?\s*', candidate, re.I):
                    consumed.add(offset)
                    continue
                if role == 'leadManagers' and re.search(r'NAME\s+OF\s+(?:THE\s+)?REGISTRAR', candidate, re.I):
                    break
                if _ROLE.match(candidate) or _REGISTRAR.match(candidate) or re.match(r"^\s*(?:BID|ISSUE|OFFER)\s*[/ ]*(?:ISSUE\s+)?(?:PERIOD|PROGRAM|OPENS|CLOSES)|^\s*SYNDICATE", candidate, re.I):
                    break
                block.append(candidate)
            contact = next((re.search(r"CONTACT(?:\s+PERSON)?", row, re.I).start() for row in block if re.search(r"CONTACT(?:\s+PERSON)?", row, re.I)), None)
            candidates, pending, raw = [], "", []
            for candidate in block:
                if re.fullmatch(r"\s*(?:\[PAGE \d+\]|\d+)\s*", candidate):
                    continue
                cut = max(0, contact - 8) if contact is not None else len(candidate)
                # Never retain a truncated contact token at a column boundary.
                if 0 < cut < len(candidate) and not candidate[cut - 1].isspace() and not candidate[cut].isspace():
                    cut = candidate.rfind(" ", 0, cut)
                value = candidate[:cut] if contact is not None else re.split(r"\s{8,}", candidate.strip(), maxsplit=1)[0]
                value = re.sub(r"\s+", " ", value).strip()
                # A company cell can share a row with contact-column headings.
                # Reject headers only after isolating the company column.
                if re.search(r"\bNAME\b|\bLOGO\b|CONTACT\s+PERSON|TELEPHONE\s*(?:AND|&)|E-?MAIL\s+(?:AND|&)", value, re.I):
                    pending = ""
                    continue
                if ')' in value and '(' not in value:
                    pending = ''
                    continue
                value = re.split(r"\(formerly|\(previously", value, flags=re.I)[0].strip()
                if not value:
                    continue
                if re.search(r"formerly|known as|CONTACT|TELEPHONE|EMAIL|E-MAIL|https?://|@|^(?:PERSON|REGISTRAR|RUNNING LEAD|MANAGERS|LOGO)$", value, re.I):
                    pending = ""
                    continue
                value = re.sub(r"^\d+[.)]\s*", "", value)
                pending = " ".join((pending + " " + value).split())
                if role == 'leadManagers' and pending.casefold() == 'bnp paribas':
                    candidates.append('BNP Paribas')
                    pending, raw = '', []
                    continue
                raw.append(candidate.strip())
                suffix = _LEGAL.search(pending)
                if suffix:
                    name = pending[:suffix.end()].strip(" .,:;")
                    # Personal contact names, partial parentheses, and fragments
                    # are ambiguous and must not be promoted to company names.
                    if (valid_manager(name) if role == 'leadManagers' else valid_registrar(name)) and not re.search(r"/|\b(?:Mr|Ms|Mrs|PERSON|LOGO|RUNNING|MANAGERS)\b", name, re.I):
                        candidates.append(name)
                    pending, raw = "", []
                elif len(pending.split()) > 12:
                    pending, raw = "", []
            if candidates:
                unique = list({name.casefold(): name for name in reversed(candidates)}.values())[::-1]
                output[role] = unique
                evidence[role] = {"page": page_no, "heading": line.strip(), "entities": unique}
    return output.get("leadManagers", []), next(iter(output.get("registrar", [])), None), evidence


def parse_document_text(text, price_band=None):
    # Call only the compatibility recognizers still needed. Invoking an old
    # whole-document parser also recomputed the retired financial extraction
    # and could spend minutes in unbounded regular-expression scans.
    front = "\f".join(text.split("\f")[:20])[:100000]
    parsed = {"promoters": base.extract_promoters(front), "objectsOfIssue": base.extract_objects(front), "shareholding": _legacy.extract_promoter_shareholding(front), "lotSize": extract_lot_size(front), "priceBand": extract_price_band(front)}
    financials, financial_evidence, conflicts = extract_financials_with_evidence(text)
    leads, registrar, intermediary_evidence = extract_intermediaries(text)
    parsed.update(financials=financials, leadManagers=leads, registrar=registrar)
    parsed["fieldEvidence"] = {"financials": financial_evidence, **intermediary_evidence}
    parsed["extractionConflicts"] = conflicts
    parsed["extractedFields"] = [key for key in ("leadManagers", "registrar", "promoters", "issueComposition", "financials", "objectsOfIssue", "shareholding", "lotSize", "priceBand") if parsed.get(key) not in (None, [], {})]
    return parsed


def extract_pdf_text(data):
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        reader.decrypt("")
    count = len(reader.pages)
    # Poppler preserves table columns and avoids repeatedly walking hundreds
    # of PDF content streams in Python.
    if shutil.which("pdftotext"):
        result = subprocess.run(["pdftotext", "-layout", "-fixed", "3", "-enc", "UTF-8", "-f", "1", "-l", str(min(count, 520)), "-", "-"], input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=True)
        pages = result.stdout.decode("utf-8").split("\f")[:min(count, 520)]
        return "\f".join(f"[PAGE {i + 1}]\n{text}" for i, text in enumerate(pages)), len(pages), count
    raise RuntimeError("poppler-utils is required to preserve validated PDF table columns")
