"""Current strict layout adapters for the P4 residual parser.

These adapters sit on top of ``p4_offer_parser`` and narrow two source layouts
that need column/sentence-aware handling: paired cover-page intermediary columns
and explicit promoter declarations. Keeping the adapters small makes their
source-layout assumptions easy to regression-test.
"""
from __future__ import annotations

import re
from typing import Any

import p4_offer_parser as common

PARSER_VERSION = common.PARSER_VERSION
RECENT_DAYS = common.RECENT_DAYS
valid_promoter_name = common.valid_promoter_name
valid_promoters = common.valid_promoters
valid_objects = common.valid_objects
_valid_shareholding = common._valid_shareholding
_has_financials = common._has_financials
is_recent = common.is_recent
needs_repair = common.needs_repair
extract_objects = common.extract_objects
extract_promoter_shareholding = common.extract_promoter_shareholding
extract_numeric_date_financials = common.extract_numeric_date_financials
merge_parsed = common.merge_parsed

_ROLE_LABEL = re.compile(
    r"^(?:NAME(?:\s+AND\s+LOGO)?|LOGO|CONTACT\s+PERSON|TELEPHONE|TEL\.?|PHONE|"
    r"E-?MAIL|EMAIL|WEBSITE|ADDRESS|SEBI\s+REG(?:ISTRATION)?\.?\s+NO\.?)$",
    re.I,
)
_ROLE_LABEL_PREFIX = re.compile(
    r"^(?:(?:NAME(?:\s+AND\s+LOGO)?|LOGO|CONTACT\s+PERSON|TELEPHONE|TEL\.?|PHONE|"
    r"E-?MAIL|EMAIL|WEBSITE|ADDRESS)\s+)+",
    re.I,
)


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


def _is_role_label(value: str) -> bool:
    return bool(_ROLE_LABEL.fullmatch(_space(value)))


def _entities(block: str, validator) -> list[str]:
    pattern = re.compile(
        r"([A-Z0-9][A-Za-z0-9&'().,/+\-]*(?:\s+[A-Z0-9][A-Za-z0-9&'().,/+\-]*){0,10}\s+"
        r"(?:Private\s+Limited|Pvt\.?\s+Ltd\.?|Limited|Ltd\.?|LLP))",
        re.I,
    )
    values = []
    for match in pattern.finditer(_space(block)):
        name = _space(match.group(1)).strip(" ,.;:-")
        name = _ROLE_LABEL_PREFIX.sub("", name).strip(" ,.;:-")
        if validator(name):
            values.append(name)
    return _dedupe(values)


def extract_paired_intermediaries(text: str):
    """Parse role names when lead-manager and registrar headings share a row."""
    for page_index, page in enumerate(str(text or "").split("\f")[:6], 1):
        lines = page.splitlines()
        for index, line in enumerate(lines):
            left = common._ROLE_LEFT.search(line)
            right = common._ROLE_RIGHT.search(line)
            if not left or not right or right.start() <= left.end() + 4:
                continue

            left_cells: list[str] = []
            right_cells: list[str] = []
            boundary = right.start()
            for raw in lines[index + 1:index + 30]:
                if re.search(r"^\s*(?:BID|ISSUE|OFFER)\s*[/ ]*(?:ISSUE\s+)?(?:PERIOD|OPENS|CLOSES)|^\s*ANCHOR\s+BID", raw, re.I):
                    break
                # Prospectus covers normally separate the two logical columns
                # with a wide whitespace run. Prefer that proof over the heading
                # position because company names can be wider than the heading.
                cells = [cell.strip() for cell in re.split(r"\s{4,}", raw.strip()) if cell.strip()]
                if len(cells) >= 2:
                    left_cell, right_cell = cells[0], cells[-1]
                    if not _is_role_label(left_cell):
                        left_cells.append(left_cell)
                    if not _is_role_label(right_cell):
                        right_cells.append(right_cell)
                    continue
                if not cells or _is_role_label(cells[0]):
                    continue
                # Wrapped single-column fragments are accepted only when their
                # indentation clearly places them on one side of the boundary.
                first_nonspace = len(raw) - len(raw.lstrip())
                if first_nonspace >= max(1, boundary - 4):
                    right_cells.append(cells[0])
                else:
                    left_cells.append(cells[0])

            managers = _entities("\n".join(left_cells), common._MANAGER.search)
            registrars = _entities("\n".join(right_cells), common._REGISTRAR.search)
            if managers or registrars:
                evidence = {}
                heading = _space(line)
                if managers:
                    evidence["leadManagers"] = {"page": page_index, "heading": heading, "entities": managers}
                if registrars:
                    evidence["registrar"] = {"page": page_index, "heading": heading, "entities": registrars[:1]}
                return managers, (registrars[0] if registrars else None), evidence
    return [], None, {}


def _promoter_payload(flat: str) -> tuple[str, str] | None:
    patterns = [
        (
            "NAMES OF PROMOTERS OF THE COMPANY",
            r"NAMES?\s+OF\s+(?:THE\s+)?PROMOTERS?\s+OF\s+(?:OUR\s+|THE\s+)?COMPANY\s*[:\-]?\s*(.{1,900}?)(?=DETAILS\s+OF\s+(?:(?:THE\s+)?(?:ISSUE|OFFER)|OFFER\s+TO\s+PUBLIC)|RISKS?\s+IN\s+RELATION|GENERAL\s+RISK|LISTING|$)",
        ),
        (
            "OUR PROMOTERS",
            r"OUR\s+PROMOTERS?\s*:?\s*(.{1,900}?)(?=DETAILS\s+OF\s+(?:(?:THE\s+)?(?:ISSUE|OFFER)|OFFER\s+TO\s+PUBLIC)|RISKS?\s+IN\s+RELATION|GENERAL\s+RISK|LISTING|$)",
        ),
        (
            "PROMOTERS OF OUR COMPANY",
            r"Promoters?\s+of\s+Our\s+Company\s+(?:are|is)\s+(.{1,700}?)(?=For\s+details|DETAILS\s+OF\s+(?:(?:THE\s+)?(?:ISSUE|OFFER)|OFFER\s+TO\s+PUBLIC)|$)",
        ),
    ]
    for heading, pattern in patterns:
        match = re.search(pattern, flat, re.I)
        if match:
            return heading, match.group(1)
    return None


def _clean_person_or_entity(raw: str) -> str:
    name = _space(raw).strip(" .,:;-()")
    name = re.sub(
        r"^(?:(?:The\s+)?Promoters?\s+of\s+(?:our\s+|the\s+)?Company\s+(?:are|is)\s*[:\-]?\s*)",
        "",
        name,
        flags=re.I,
    )
    name = re.sub(r"^(?:The\s+)?(?:being|namely)\s+", "", name, flags=re.I)
    name = re.sub(r"^(?:Mr|Ms|Mrs|Dr)\.?\s+", "", name, flags=re.I)
    return _space(name).strip(" .,:;-()")


def extract_promoters(text: str):
    front = " ".join(str(text or "").split("\f")[:25])[:160000]
    flat = _space(front)
    found = _promoter_payload(flat)
    if not found:
        return [], {}
    heading, payload = found
    payload = re.split(r"\bFor\s+details\b|\bThe\s+details\s+of\s+our\s+Promoters\b", payload, maxsplit=1, flags=re.I)[0]
    payload = re.sub(r"\((?:i|ii|iii|iv|v|vi|vii|viii|ix|x)\)", ";", payload, flags=re.I)
    payload = re.sub(r"\b(?:and)\b", ";", payload, flags=re.I)

    names = []
    for raw in re.split(r"\s*[,;]\s*", payload):
        name = _clean_person_or_entity(raw)
        if valid_promoter_name(name):
            names.append(name)
    names = _dedupe(names)
    return (names, {"promoters": {"heading": heading, "entities": names}}) if names else ([], {})


def parse_document_text(text: str) -> dict[str, Any]:
    result = common.parse_document_text(text)
    leads, registrar, role_evidence = extract_paired_intermediaries(text)
    promoters, promoter_evidence = extract_promoters(text)

    if leads:
        result["leadManagers"] = leads
    if registrar:
        result["registrar"] = registrar
    if valid_promoters(promoters):
        result["promoters"] = promoters

    evidence = dict(result.get("fieldEvidence") or {})
    for supplement in (role_evidence, promoter_evidence):
        evidence.update(supplement)
    result["fieldEvidence"] = evidence
    result["residualParserVersion"] = PARSER_VERSION

    extracted = list(result.get("extractedFields") or [])
    for field in ("leadManagers", "registrar", "promoters", "objectsOfIssue", "shareholding", "financials"):
        if result.get(field) not in (None, [], {}) and field not in extracted:
            extracted.append(field)
    result["extractedFields"] = extracted
    return result
