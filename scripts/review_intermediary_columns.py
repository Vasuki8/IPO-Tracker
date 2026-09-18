"""Bounded source-review helper; deliberately not wired into any collector.

Supports a lead-manager / registrar cover table with one current legal entity
per role. Fixed-layout character spans must keep each entity in its own column.
Unsupported, incomplete or conflicting layouts fail closed. This is a source
review aid, not permission to publish a parse or alter a retained review hold.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from urllib.parse import urlparse

PARSER_VERSION = "reviewed-intermediary-columns-v1"
_LEAD = re.compile(r"(?:BOOK\s+RUNNING\s+)?LEAD\s+MANAGERS?(?:\s+TO\s+THE\s+(?:ISSUE|OFFER))?", re.I)
_REGISTRAR = re.compile(r"REGISTRAR\s+TO\s+THE\s+(?:ISSUE|OFFER)", re.I)
_LEGAL = re.compile(r"\b(?:PRIVATE\s+LIMITED|PVT\.?\s+LTD\.?|LIMITED|LTD\.?|LLP)\b", re.I)
_META = re.compile(r"^(?:SEBI\b|REGISTERED\b|ADDRESS\b|TEL(?:EPHONE)?\b|FAX\b|CONTACT\b|E-?MAIL\b|EMAIL\b|WEBSITE\b|INVESTOR\b|CIN\b|\d+[ ,/-])|https?://|www\.|@", re.I)
_FORMER = re.compile(r"\b(?:FORMERLY|PREVIOUSLY|KNOWN\s+AS)\b", re.I)
_END = re.compile(r"^(?:(?:BID\s*/\s*)?(?:ISSUE|OFFER)\s+(?:PROGRAMME?|PERIOD|OPENS|OPENED|CLOSES|CLOSED)|ANCHOR\s+(?:BID|PORTION))\b", re.I)


class ReviewLayoutError(ValueError):
    """The retained physical text does not prove the supported role layout."""


def _space(value):
    return " ".join(value.split())


def _name(value):
    return (len(value.split()) >= 3 and len(value) <= 160
            and len(list(_LEGAL.finditer(value))) == 1
            and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 &'().,/+\-]*", value))
            and bool(re.search(r"(?:LIMITED|LTD\.?|LLP)$", value, re.I))
            and not _FORMER.search(value) and not _META.search(value)
            and not re.search(r"\b(?:MANAGERS?|REGISTRAR|LOGO|NAME|PERSON)\b", value, re.I))


def _parse_block(raw_lines, page):
    heading = raw_lines[0]
    lead, registrar = _LEAD.search(heading), _REGISTRAR.search(heading)
    if not lead or not registrar or registrar.start() - lead.end() < 12:
        raise ReviewLayoutError("Two distinct role headings and a wide separator are required")
    if heading[:lead.start()].strip() or heading[registrar.end():].strip():
        raise ReviewLayoutError("Additional heading text is ambiguous")
    gap = heading[lead.end():registrar.start()]
    # Some PDF logo glyphs are emitted as a single isolated character between
    # widely separated cells. They are retained verbatim, never used as a role.
    if gap.strip() and not re.fullmatch(r"\s{8,}[A-Z]\s{8,}", gap):
        raise ReviewLayoutError("Unrecognised content between role headings")
    boundary = (lead.end() + registrar.start()) // 2
    states = {field: {"parts": [], "spans": [], "name": None, "closed": False}
              for field in ("leadManagers", "registrar")}
    for line_index, raw in enumerate(raw_lines[1:], 1):
        if _END.match(raw.strip()):
            break
        if all(state["closed"] for state in states.values()):
            break
        # A physical word across the proposed divider invalidates the table;
        # changing the divider to make an expected company fit is not allowed.
        if raw[max(0, boundary - 2):boundary + 2].strip():
            raise ReviewLayoutError("Source text crosses the role-column divider")
        for field, start, end in (("leadManagers", 0, boundary), ("registrar", boundary, len(raw))):
            state = states[field]
            if state["closed"]:
                continue
            cell = raw[start:end]
            token = cell.strip()
            if not token or re.fullmatch(r"(?:NAME\s+AND\s+LOGO|LOGO)", token, re.I):
                continue
            if _META.search(token) or _FORMER.search(token):
                if not state["name"]:
                    raise ReviewLayoutError("No complete current entity before role metadata")
                state["closed"] = True
                continue
            if state["name"]:
                raise ReviewLayoutError("Additional entity or unexplained text in a role cell")
            actual_start = start + len(cell) - len(cell.lstrip())
            actual_end = start + len(cell.rstrip())
            state["parts"].append(token)
            state["spans"].append({"line": line_index, "start": actual_start,
                                   "end": actual_end, "text": raw[actual_start:actual_end]})
            candidate = _space(" ".join(state["parts"]))
            if _LEGAL.search(candidate):
                if not _name(candidate):
                    raise ReviewLayoutError("Role cell is not one complete current legal entity")
                state["name"] = candidate
            elif len(state["parts"]) >= 3 or len(candidate) > 160:
                raise ReviewLayoutError("Unsupported wrapped role entity")
    if any(not state["name"] for state in states.values()):
        raise ReviewLayoutError("Both role columns must contain a complete entity")
    if states["leadManagers"]["name"].casefold() == states["registrar"]["name"].casefold():
        raise ReviewLayoutError("Identical entity in both roles needs separate review")
    evidence = {}
    for field, match, start, end in (("leadManagers", lead, 0, boundary),
                                    ("registrar", registrar, boundary, None)):
        evidence[field] = {
            "page": page, "heading": _space(match.group()),
            "entities": [states[field]["name"]], "rawLines": list(raw_lines),
            "headingLine": heading,
            "headingSpan": {"start": match.start(), "end": match.end(), "text": match.group()},
            "columnStart": start, "columnEnd": end,
            "nameSpans": states[field]["spans"], "method": PARSER_VERSION,
        }
    return {"leadManagers": [states["leadManagers"]["name"]],
            "registrar": states["registrar"]["name"], "fieldEvidence": evidence}


def extract_intermediary_columns(text, *, page):
    """Read one physical page; require every supported table to agree.

    ``page`` is the one-based physical PDF page. Retained span line indices and
    character offsets are zero-based, with ends excluded, within ``rawLines``.
    A caller must independently bind the page text to exact source PDF bytes.
    """
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ReviewLayoutError("A positive physical page number is required")
    if not isinstance(text, str) or "\f" in text or "\t" in text:
        raise ReviewLayoutError("One physical fixed-layout page without tabs is required")
    lines = text.splitlines()
    candidates = []
    for i, line in enumerate(lines):
        if not (_LEAD.search(line) and _REGISTRAR.search(line)):
            continue
        block = [line]
        for raw in lines[i + 1:i + 41]:
            if _END.match(raw.strip()):
                break
            block.append(raw)
        candidates.append(_parse_block(block, page))
    if not candidates:
        raise ReviewLayoutError("No paired role table on this physical page")
    values = {(tuple(item["leadManagers"]), item["registrar"]) for item in candidates}
    if len(values) != 1:
        raise ReviewLayoutError("Paired role tables disagree")
    return candidates[0]


def validate_evidence(field, value, detail):
    """Replay retained source spans, rejecting any mismatch with the field.

    This proves internal layout consistency. The publication reviewer still
    verifies document identity/hash/date and that these raw lines occur there.
    """
    if field not in {"leadManagers", "registrar"} or not isinstance(detail, dict):
        raise ReviewLayoutError("Unsupported intermediary evidence field")
    raw = detail.get("rawLines")
    if not isinstance(raw, list) or not raw or any(not isinstance(line, str) or "\n" in line or "\r" in line for line in raw):
        raise ReviewLayoutError("Exact original physical lines are required")
    parsed = extract_intermediary_columns("\n".join(raw), page=detail.get("page"))
    if parsed[field] != value or parsed["fieldEvidence"][field] != detail:
        raise ReviewLayoutError("Retained role value or physical spans do not replay")
    return True


def has_reviewed_role_evidence(record, field):
    """Recognize only a complete, replayable current reviewed-field proof.

    A legal name need not contain the old parser's financial-brand vocabulary.
    Matching document authority, offer identity, value and role spans remain
    mandatory. This does not treat an extraction/version label as acceptance.
    """
    from final_prospectus_policy import is_final_prospectus
    from final_prospectus_identity import known_non_final_document_url
    proof = (record.get('staticFieldProvenance') or {}).get(field)
    if (not isinstance(proof, dict) or proof.get('parserVersion') != PARSER_VERSION
            or proof.get('field') != field or proof.get('value') != record.get(field)
            or not record.get('openDate') or proof.get('issueOpenDate') != record['openDate']
            or not isinstance(proof.get('sourceUrl'), str) or not proof['sourceUrl'].startswith('https://')
            or not re.fullmatch(r'[a-f0-9]{64}', str(proof.get('sha256') or ''))
            or not proof.get('checkedAt') or not proof.get('documentDate')
            or not is_final_prospectus({'type': proof.get('documentType'), 'url': proof.get('sourceUrl')})
            or known_non_final_document_url(record, proof['sourceUrl'])):
        return False
    try:
        identity = proof.get('identity')
        if (not isinstance(identity, dict) or set(identity) != {'id', 'company', 'symbol', 'openDate'}
                or any(not isinstance(v, str) or not v or record.get(k) != v for k, v in identity.items())):
            return False
        url = urlparse(proof['sourceUrl'])
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            return False
        date.fromisoformat(proof['documentDate'])
        if datetime.fromisoformat(proof['checkedAt']).utcoffset() is None:
            return False
        return validate_evidence(field, record.get(field), proof.get('evidence'))
    except (ValueError, TypeError, KeyError):
        return False
