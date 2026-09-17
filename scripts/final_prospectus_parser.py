"""Final Prospectus parser adapter.

Extends the strict offer parser with fields that are meaningful only once the
book-built offer is final, especially the fixed Offer/Issue Price, explicit bid
lot, deep pre-issue promoter shareholding and final issue composition. Final
issue price is deliberately kept distinct from the historical bidding price
band: a one-point fixed price is never synthesized as a price band.
"""
from __future__ import annotations

import math
import re
from typing import Any

import legacy_offer_parser as legacy
import offer_parser as base
from p4_offer_parser import extract_objects
from issue_composition_checks import amounts_match, composition_problems
from objects_of_issue_checks import objects_evidence_problems

PARSER_VERSION = base.PARSER_VERSION + 10
extract_pdf_text = base.extract_pdf_text
valid_manager = base.valid_manager
valid_registrar = base.valid_registrar

_PRICE_PATTERNS = (
    re.compile(
        r"\b(?:OFFER|ISSUE)\s+PRICE\s*(?::|IS|OF)?\s*(?:₹|RS\.?|INR)\s*"
        r"([0-9][0-9,]*(?:\.\d+)?)\s*(?:PER\s+)?(?:EQUITY\s+)?SHARE\b",
        re.I,
    ),
    re.compile(
        r"\bPRICE\s+OF\s+(?:₹|RS\.?|INR)\s*([0-9][0-9,]*(?:\.\d+)?)\s*"
        r"PER\s+(?:EQUITY\s+)?SHARE\b",
        re.I,
    ),
)
_PRICE_BAND_PATTERNS = (
    # A definitions table may disclose the two values before their parenthetic
    # Floor/Cap labels, rather than writing a numeric "low to high" range.
    re.compile(
        r"\bPRICE\s+BAND\s+(?:OF\s+)?(?:A\s+)?MINIMUM\s+PRICE\s+OF\s*"
        r"(?:₹|RS\.?|INR)\s*([0-9][0-9,]*(?:\.\d+)?)\s*"
        r"PER\s+(?:EQUITY\s+)?SHARES?\s*\(\s*(?:I\.E\.,?\s*)?(?:THE\s+)?FLOOR\s+PRICE\s*\)\s*"
        r"AND\s+(?:THE\s+)?MAXIMUM\s+PRICE\s+OF\s*"
        r"(?:₹|RS\.?|INR)\s*([0-9][0-9,]*(?:\.\d+)?)\s*"
        r"PER\s+(?:EQUITY\s+)?SHARES?\s*\(\s*(?:I\.E\.,?\s*)?(?:THE\s+)?CAP\s+PRICE\s*\)",
        re.I,
    ),
    re.compile(
        r"\bPRICE\s+BAND\b.{0,120}?(?:₹|RS\.?|INR)?\s*"
        r"([0-9][0-9,]*(?:\.\d+)?)\s*(?:TO|[-–—])\s*"
        r"(?:₹|RS\.?|INR)?\s*([0-9][0-9,]*(?:\.\d+)?)\s*"
        r"(?:PER\s+)?(?:EQUITY\s+)?SHARE\b",
        re.I,
    ),
    re.compile(
        r"\bFLOOR\s+PRICE\b.{0,100}?(?:₹|RS\.?|INR)\s*"
        r"([0-9][0-9,]*(?:\.\d+)?).{0,180}?\bCAP\s+PRICE\b.{0,100}?"
        r"(?:₹|RS\.?|INR)\s*([0-9][0-9,]*(?:\.\d+)?)",
        re.I,
    ),
)
_LOT_PATTERNS = (
    re.compile(
        r"\bMINIMUM\s+BID\s+LOT(?:\s+SIZE)?\s*"
        r"(?:(?:SHALL|WILL)\s+BE|SHALL\s+CONSIST\s+OF|IS|OF|MEANS|[:\-])?\s*"
        r"([0-9][0-9,]{0,7})\s+(?:FULLY\s+PAID[-\s]?UP\s+)?EQUITY\s+SHARES\b",
        re.I,
    ),
    re.compile(
        r"\bBID\s+LOT(?:\s+SIZE)?\s*"
        r"(?:(?:SHALL|WILL)\s+BE|SHALL\s+CONSIST\s+OF|IS|OF|MEANS|[:\-])\s*"
        r"([0-9][0-9,]{0,7})\s+(?:FULLY\s+PAID[-\s]?UP\s+)?EQUITY\s+SHARES\b",
        re.I,
    ),
    re.compile(
        r"\bBID\s+LOT\b.{0,80}?\b(?:MINIMUM\s+OF\s+)?"
        r"([0-9][0-9,]{0,7})\s+(?:FULLY\s+PAID[-\s]?UP\s+)?EQUITY\s+SHARES\b",
        re.I,
    ),
    re.compile(
        r"\bTHE\s+BID\s+LOT\s+(?:FOR\s+THE\s+(?:OFFER|ISSUE)\s+)?"
        r"(?:IS|SHALL\s+BE|WILL\s+BE)\s+([0-9][0-9,]{0,7})\s+"
        r"(?:FULLY\s+PAID[-\s]?UP\s+)?EQUITY\s+SHARES\b",
        re.I,
    ),
)
_SHAREHOLDING_MARKER = re.compile(
    r"(?:pre[-\s]?(?:issue|offer|ipo).{0,100}(?:shareholding|share\s+holding)|"
    r"(?:shareholding|share\s+holding).{0,100}pre[-\s]?(?:issue|offer|ipo)|"
    r"shareholding\s+pattern|promoters?\s+(?:and|&|/)\s+promoter\s+group|"
    r"total\s*(?:[-–—]\s*)?c\s*\(\s*a\s*\+\s*b\s*\)|"
    r"total\s*\(\s*a\s*\+\s*b\s*\))",
    re.I,
)

_SHARE_FIELDS = ("freshShares", "ofsShares")
_AMOUNT_FIELDS = ("freshIssueCr", "ofsCr", "totalIssueSizeCr")

_PROMOTER_HEADING = re.compile(
    r"^\s*(?P<heading>OUR\s+PROMOTERS?|"
    r"(?:(?:NAMES?\s+OF\s+)?(?:THE\s+)?)PROMOTERS?\s+OF\s+(?:OUR\s+|THE\s+)?COMPANY)"
    r"\b(?!\s*(?:AND|&)\s+PROMOTER\s+GROUP)(?P<names>.*)$",
    re.I,
)
_PROMOTER_END = re.compile(
    r"^(?:DETAILS\s+OF|(?:ISSUE|OFFER)\s+DETAILS|INITIAL\s+PUBLIC|"
    r"RISKS?\s+IN\s+RELATION|RISK\s+FACTORS|GENERAL\s+RISK|LISTING|"
    r"BOOK\s+RUNNING|REGISTRAR\s+TO|BID\s*/|OBJECTS?\s+OF|"
    r"FOR\s+DETAILS|THE\s+DETAILS|OUR\s+COMPANY|TABLE\s+OF\s+CONTENTS|SECTION\s+[IVX])\b",
    re.I,
)
_PROMOTER_JUNK = re.compile(
    r"\b(?:being|namely|promoters?|selling|shareholders?|equity|shares?|offer|issue|"
    r"details|our|are|is|including|page|contact|telephone|email|website|risk|listing|respectively)\b",
    re.I,
)
_PROMOTER_LEGAL_END = re.compile(
    r"(?:\b(?:PRIVATE\s+LIMITED|PVT\.?\s+LTD\.?|PTE\.?\s+LTD\.?|LIMITED|LTD\.?|LLP|LLC|PLC|"
    r"INC\.?|CORP\.?|ASA|AS|S\.?A\.?)|\(\s*HUF\s*\))$", re.I,
)
_PROMOTER_HUF_END = re.compile(r"\(\s*HUF\s*\)$", re.I)

# Keep labels adjacent to their own share count. The legacy recognizer searched
# hundreds of characters past each label and could attach a seller's quantity,
# an adjacent table column, or a use-of-proceeds amount to the whole offer.
_COMPOSITION_NUMBER = r"[0-9][0-9,]*"
_COMPOSITION_FOOTNOTE = r"\s*[*^#†‡]*\s*"
_COMPOSITION_QUANTITY = (
    rf"(?:UP\s+TO\s+|UPTO\s+)?(?P<shares>{_COMPOSITION_NUMBER})"
    + _COMPOSITION_FOOTNOTE
    + r"(?:FULLY\s+PAID[-\s]?UP\s+)?EQUITY\s+SHARES\b"
)
_COMPOSITION_PART = re.compile(
    r"\b(?P<label>FRESH\s+ISSUE|OFFER\s+FOR\s+SALE)\s*"
    r"(?::|[-–—])?\s*(?:OF\s+)?" + _COMPOSITION_QUANTITY,
    re.I,
)
_COMPOSITION_EMPTY_PART = re.compile(
    r"\b(?P<label>FRESH\s+ISSUE|OFFER\s+FOR\s+SALE)\s*"
    r"(?::|[-–—])?\s*(?:IS\s+)?(?:NOT\s+APPLICABLE|NIL|NONE)\b",
    re.I,
)
_COMPOSITION_INITIAL = re.compile(
    r"\bINITIAL\s+PUBLIC\s+(?:OFFER(?:ING)?|ISSUE)\s+(?:OF\s+)?"
    + _COMPOSITION_QUANTITY,
    re.I,
)
_COMPOSITION_MONEY = re.compile(
    r"\bAGGREGAT(?:ING|ES|E)\s*(?:(?:UP\s*TO|TO)\s*)?"
    r"(?:₹|RS\.?|INR)\s*(?P<amount>[0-9][0-9,]*(?:\.\d+)?)"
    + _COMPOSITION_FOOTNOTE
    + r"(?P<unit>CRORES?|CR\.?|MILLIONS?|LAKHS?|LACS?)\b",
    re.I,
)
_COMPOSITION_SELLER_PREFIX = re.compile(
    r"\s*\^?\s*(?:(?:BEARING\s+|OF\s+)?FACE\s+VALUE\s+(?:OF\s+)?"
    r"(?:₹|RS\.?|INR)\s*[0-9][0-9,]*(?:\.\d+)?\s+EACH\s*,?\s*)?"
    + r"(?:" + _COMPOSITION_MONEY.pattern + r")?"
    + _COMPOSITION_FOOTNOTE + r"$",
    re.I,
)
_COMPOSITION_WHOLE_OFS = re.compile(
    _COMPOSITION_FOOTNOTE
    + r"(?:THROUGH\s+AN\s+OFFER\s+FOR\s+SALE\s*\(\s*(?:THE\s+)?"
    r"[\"“']OFFER[\"”']\s+OR\s+[\"“']OFFER\s+FOR\s+SALE[\"”']\s*\)"
    r"|\(\s*(?:THE\s+)?[\"“']OFFER[\"”']\s*\)\s*,?\s*"
    r"THROUGH\s+AN\s+(?P<seller_label>OFFER\s+FOR\s+SALE)\b)",
    re.I,
)
_COMPOSITION_BOUNDARY = re.compile(
    r"\b(?:FRESH\s+ISSUE|OFFER\s+FOR\s+SALE|PRE[-\s]?IPO|"
    r"NET\s+PROCEEDS|OBJECTS\s+OF|GENERAL\s+CORPORATE|"
    r"TOTAL\s+(?:ISSUE|OFFER)(?:\s+SIZE)?)\b|"
    + _COMPOSITION_QUANTITY,
    re.I,
)
_COMPOSITION_SECTION = re.compile(
    r"^\s*(?:DETAILS\s+OF\s+THE\s+(?:ISSUE|OFFER)(?:\s+TO\s+PUBLIC)?|"
    r"(?:ISSUE|OFFER)\s+DETAILS|THE\s+(?:OFFER|ISSUE))\s*$",
    re.I | re.M,
)
_COMPOSITION_END = re.compile(
    r"\b(?:RISKS?\s+IN\s+RELATION|GENERAL\s+RISK|"
    r"THE\s+FACE\s+VALUE|THE\s+(?:OFFER|ISSUE)\s+(?:WAS|WILL|SHALL)|"
    r"OUR\s+COMPANY\s+HAS|FOR\s+DETAILS|OBJECTS\s+OF\s+THE)\b",
    re.I,
)


def _number(token: str) -> float | None:
    try:
        value = float(token.replace(",", ""))
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _page_number(page: str, fallback: int) -> int:
    marker = re.search(r"\[PAGE\s+(\d+)\]", str(page or ""), re.I)
    if not marker:
        return fallback
    try:
        value = int(marker.group(1))
    except ValueError:
        return fallback
    return value if value > 0 else fallback


def _promoter_names(payload: str, *, single=False) -> list[str]:
    payload = re.split(r"\b(?:For\s+details|The\s+details\s+of\s+our\s+Promoters)\b", payload, maxsplit=1, flags=re.I)[0]
    payload = re.sub(
        r"^(?:(?:(?:The\s+)?Promoters?\s+of\s+(?:our|the)\s+Company|Our\s+Promoters?)\s+)?"
        r"(?:are|is)\s*[:\-]?\s*", "", payload, flags=re.I,
    )
    payload = re.sub(r"^(?:being|namely)\s+", "", payload, flags=re.I)
    payload = re.sub(r"\(\s*(?:[ivx]+|\d{1,2})\s*\)", ";", payload, flags=re.I)
    payload = payload.strip(" ;")
    # A singular promoter heading can name one corporation containing AND.
    if single and _PROMOTER_LEGAL_END.search(payload) and not re.search(r"[,;]", payload):
        joined = re.split(r"\s+AND\s+", payload, flags=re.I)
        if any(_PROMOTER_LEGAL_END.search(part.strip()) for part in joined[:-1]):
            return []
        pieces = [payload]
    else:
        for segment in re.split(r"[,;]", payload):
            joined = re.split(r"\s+AND\s+", segment.strip(), flags=re.I)
            if len(joined) > 2 and any(_PROMOTER_LEGAL_END.search(part.strip()) for part in joined):
                return []
        pieces = re.split(r"\s*[,;]\s*|\s+AND\s+", payload, flags=re.I)
    names = []
    for piece in pieces:
        name = " ".join(piece.split()).strip(" ,;:")
        name = re.sub(r"^(?:Mr|Mrs|Ms|Dr)\.?\s+", "", name, flags=re.I)
        if not re.search(r"\b(?:Ltd|Pte|Inc|Corp|Co|S\.?A)\.$", name, re.I):
            name = name.rstrip(".")
        words = name.split()
        if not 4 <= len(name) <= 140 or not 2 <= len(words) <= 12 or _PROMOTER_JUNK.search(name):
            return []
        if huf := _PROMOTER_HUF_END.search(name):
            # Preserve the source name, including M/S, but require a named
            # HUF rather than allowing the prefix and suffix alone to qualify.
            person = re.sub(r"^M/S\s+", "", name[:huf.start()].strip(), flags=re.I)
            person_words = person.split()
            valid = len(person_words) >= 2 and all(re.fullmatch(r"[A-Za-z][A-Za-z.'\-]*", word) for word in person_words)
        elif _PROMOTER_LEGAL_END.search(name):
            valid = bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9\s.'&()/+\-]*", name))
        else:
            valid = all(re.fullmatch(r"[A-Za-z][A-Za-z.'\-]*", word) for word in words)
        if not valid or name.count("(") != name.count(")"):
            return []
        if name.casefold() not in {existing.casefold() for existing in names}:
            names.append(name)
    return names if 1 <= len(names) <= (1 if single else 20) else []


def _ambiguous_promoter_rows(parts: list[str]) -> bool:
    nonempty = [part.strip() for part in parts if part.strip()]
    for previous, current in zip(nonempty, nonempty[1:]):
        if re.search(r"[,;]$|\bAND$", previous, re.I) or re.match(r"[,;]|AND\b", current, re.I):
            continue
        left = re.split(r"[,;]|\bAND\b", previous, flags=re.I)[-1].strip()
        right = re.split(r"[,;]|\bAND\b", current, flags=re.I)[0].strip()
        # A stand-alone legal suffix can complete the previous entity; two
        # independently plausible name rows cannot safely become one person.
        if _promoter_names(left) and _promoter_names(right) and not _PROMOTER_LEGAL_END.fullmatch(right):
            return True
    return False


def extract_final_promoters(text: str) -> tuple[list[str], dict[str, Any]]:
    """Use complete headed name lists; seller definitions are not promoter lists."""
    observations = []
    for page_index, page in enumerate(str(text or "")[:100000].split("\f")[:12], 1):
        lines = page.splitlines()
        for index, line in enumerate(lines):
            match = _PROMOTER_HEADING.match(line)
            if not match:
                continue
            first = match.group("names").strip(" :\t-")
            # Contents entries and promoter-group headings do not name people.
            if re.fullmatch(r"[.\s]*\d+", first) or re.search(r"\.{3,}", first):
                continue
            rows, parts = [line.strip()], [first]
            terminated = False
            for following in lines[index + 1:index + 9]:
                value = following.strip()
                if not value:
                    continue
                if _PROMOTER_END.match(value) or (_PROMOTER_HEADING.match(value) and any(parts)):
                    terminated = True
                    break
                rows.append(value)
                parts.append(value)
                if sum(map(len, parts)) > 1400:
                    terminated = False
                    break
            if not terminated or _ambiguous_promoter_rows(parts):
                continue
            names = _promoter_names(
                " ".join(parts).strip(),
                single=bool(re.search(r"\bPROMOTER\b", match.group("heading"), re.I)),
            )
            if names:
                observations.append((names, {
                    "page": _page_number(page, page_index),
                    "heading": " ".join(match.group("heading").split()),
                    "rows": rows,
                    "entities": names,
                    "method": "bounded-promoter-heading-v1",
                }))
    identities = {frozenset(name.casefold().rstrip(".") for name in names) for names, _ in observations}
    if len(identities) != 1:
        return [], {}
    names, evidence = observations[0]
    return names, {"promoters": evidence}


def extract_final_lot_size(text: str) -> tuple[int | None, dict[str, Any]]:
    """Extract one unambiguous explicit Bid Lot from the full parsed document."""
    observations: list[tuple[int, int, str]] = []
    for page_index, page in enumerate(str(text or "").split("\f"), 1):
        compact = " ".join(page.replace("\u00a0", " ").split())
        for pattern in _LOT_PATTERNS:
            for match in pattern.finditer(compact):
                value = _number(match.group(1))
                if value is None or value != int(value):
                    continue
                lot = int(value)
                if 0 < lot <= 100_000:
                    observations.append((lot, _page_number(page, page_index), match.group(0)))

    unique = sorted({lot for lot, _, _ in observations})
    if len(unique) != 1:
        return None, {}
    lot = unique[0]
    evidence_hit = next(hit for hit in observations if hit[0] == lot)
    return lot, {
        "lotSize": {
            "page": evidence_hit[1],
            "heading": evidence_hit[2],
            "value": lot,
            "basis": "explicit Bid Lot/Minimum Bid Lot in Final Prospectus",
        }
    }


def extract_final_promoter_shareholding(text: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Recover explicit pre-issue promoter ownership from deep document pages.

    The compatibility parser looks only at front matter. Here we search for a
    bounded set of strong shareholding markers across the already extracted PDF,
    then run the proven legacy recognizer only on a three-page local window.
    Multiple different ownership percentages fail closed.
    """
    pages = str(text or "").split("\f")
    candidate_indexes: list[tuple[int, str]] = []
    seen_indexes: set[int] = set()
    for index, page in enumerate(pages):
        compact = " ".join(page.replace("\u00a0", " ").split())
        marker = _SHAREHOLDING_MARKER.search(compact)
        if marker and index not in seen_indexes:
            seen_indexes.add(index)
            candidate_indexes.append((index, marker.group(0)))
        if len(candidate_indexes) >= 24:
            break

    observations: list[tuple[float, int, str]] = []
    for index, heading in candidate_indexes:
        start = max(0, index - 1)
        end = min(len(pages), index + 2)
        window = "\f".join(pages[start:end])
        parsed = legacy.extract_promoter_shareholding(window)
        if not isinstance(parsed, dict):
            continue
        pct = parsed.get("promoterPreIssuePct")
        if not isinstance(pct, (int, float)) or isinstance(pct, bool):
            continue
        value = round(float(pct), 6)
        if 0 <= value <= 100:
            observations.append((value, _page_number(pages[index], index + 1), heading))

    unique = sorted({pct for pct, _, _ in observations})
    if len(unique) != 1:
        return None, {}
    pct = unique[0]
    evidence_hit = next(hit for hit in observations if hit[0] == pct)
    shareholding = {"promoters": [], "promoterPreIssuePct": pct}
    return shareholding, {
        "shareholding": {
            "page": evidence_hit[1],
            "heading": evidence_hit[2],
            "promoterPreIssuePct": pct,
            "basis": "explicit pre-issue promoter ownership in Final Prospectus",
        }
    }


def extract_final_issue_price(text: str) -> tuple[float | None, dict[str, Any]]:
    """Extract one unambiguous fixed price from Final Prospectus front matter."""
    front_pages = str(text or "").split("\f")[:12]
    values: list[tuple[float, int, str]] = []
    for page_index, page in enumerate(front_pages, 1):
        compact = " ".join(page.replace("\u00a0", " ").split())
        for pattern_index, pattern in enumerate(_PRICE_PATTERNS):
            for match in pattern.finditer(compact):
                if pattern_index == 1:
                    # A price-band definition also says "price of ... per
                    # Equity Share". Its floor/cap are bidding limits, not two
                    # competing final prices (e.g. Manipal's 322/339 band).
                    before = compact[max(0, match.start() - 40):match.start()]
                    after = compact[match.end():match.end() + 60]
                    if re.search(r"\b(?:MINIMUM|MAXIMUM|FLOOR|CAP)\s*$", before, re.I) or re.match(
                        r"\s*\(\s*(?:THE\s+)?(?:FLOOR|CAP)\s+PRICE\s*\)", after, re.I
                    ):
                        continue
                    # An unlabeled transaction price is usable only inside the
                    # initial public offer's leading cash-pricing clause. Past
                    # placements/acquisitions elsewhere are not issue prices.
                    offers = [hit for hit in _COMPOSITION_INITIAL.finditer(compact) if hit.end() <= match.start()]
                    if not offers or not re.search(r"\bAT\s+(?:A\s+)?$", before, re.I):
                        continue
                    lead = compact[offers[-1].end():match.start()]
                    if len(lead) > 900 or _COMPOSITION_BOUNDARY.search(lead) or _COMPOSITION_END.search(lead):
                        continue
                    if _COMPOSITION_MONEY.search(lead) or re.search(
                        r"\b(?:PRE[-\s]?IPO|PLACEMENT|ACQUISITION|ACQUIRED|HISTORICAL)\b|;|\.(?=\s+[A-Z])",
                        lead, re.I,
                    ):
                        continue
                value = _number(match.group(1))
                if value is not None and 0 < value <= 100_000:
                    statement = compact[offers[-1].start():match.end()] if pattern_index == 1 else match.group(0)
                    values.append((value, _page_number(page, page_index), statement))
    unique = sorted({value for value, _, _ in values})
    if len(unique) != 1:
        return None, {}
    value = unique[0]
    evidence_hit = next(hit for hit in values if hit[0] == value)
    return value, {
        "issuePrice": {
            "page": evidence_hit[1],
            "heading": evidence_hit[2],
            "value": value,
            "basis": "explicit fixed Offer/Issue Price in Final Prospectus",
            "method": "final-offer-price-v2",
        }
    }


def extract_explicit_price_band(text: str) -> tuple[dict[str, float] | None, dict[str, Any]]:
    """Extract only an explicitly stated bidding range; never infer it from issue price."""
    pages = str(text or "").split("\f")[:40]
    values: list[tuple[float, float, int, str]] = []
    for page_index, page in enumerate(pages, 1):
        compact = " ".join(page.replace("\u00a0", " ").split())
        for pattern in _PRICE_BAND_PATTERNS:
            for match in pattern.finditer(compact):
                low, high = _number(match.group(1)), _number(match.group(2))
                if low is None or high is None:
                    continue
                if 0 < low <= high <= 100_000:
                    values.append((low, high, _page_number(page, page_index), match.group(0)))
    unique = sorted({(low, high) for low, high, _, _ in values})
    if len(unique) != 1:
        return None, {}
    low, high = unique[0]
    evidence_hit = next(hit for hit in values if hit[0] == low and hit[1] == high)
    band = {"min": low, "max": high}
    return band, {
        "priceBand": {
            "page": evidence_hit[2],
            "heading": evidence_hit[3],
            "value": band,
            "basis": "explicit Price Band/Floor Price/Cap Price in Final Prospectus",
        }
    }


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def validate_issue_composition(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None

    normalized: dict[str, Any] = {}
    for field in _SHARE_FIELDS:
        raw = value.get(field)
        if raw is None:
            continue
        if not _finite_number(raw) or float(raw) < 0 or float(raw) != int(float(raw)):
            return None
        shares = int(float(raw))
        if shares > 100_000_000_000:
            return None
        normalized[field] = shares

    for field in _AMOUNT_FIELDS:
        raw = value.get(field)
        if raw is None:
            continue
        if not _finite_number(raw) or float(raw) < 0 or float(raw) > 10_000_000:
            return None
        normalized[field] = round(float(raw), 6)

    valuation = value.get("valuationPriceUsed")
    if valuation is not None:
        if not _finite_number(valuation) or not 0 < float(valuation) <= 100_000:
            return None
        normalized["valuationPriceUsed"] = float(valuation)

    meaningful = any(
        normalized.get(field) not in (None, 0)
        for field in (*_SHARE_FIELDS, *_AMOUNT_FIELDS)
    )
    if not meaningful:
        return None

    fresh = normalized.get("freshIssueCr")
    ofs = normalized.get("ofsCr")
    total = normalized.get("totalIssueSizeCr")
    if fresh is not None and ofs is not None:
        expected = round(fresh + ofs, 6)
        if total is None:
            normalized["totalIssueSizeCr"] = expected
        else:
            tolerance = max(0.05, abs(total) * 0.005)
            if abs(total - expected) > tolerance:
                return None

    fresh_shares = normalized.get("freshShares")
    ofs_shares = normalized.get("ofsShares")
    if fresh_shares == 0 and ofs_shares == 0:
        return None

    if composition_problems(normalized):
        return None

    return normalized


def _composition_blocks(text: str) -> list[tuple[int, str]]:
    """Prefer the offer narrative; never flatten adjacent cover-table columns."""
    narratives: list[tuple[int, str]] = []
    sections: list[tuple[int, str]] = []
    for index, page in enumerate(str(text or "").split("\f")[:12], 1):
        page_number = _page_number(page, index)
        compact = " ".join(page.replace("\u00a0", " ").split())
        for match in _COMPOSITION_INITIAL.finditer(compact):
            block = compact[match.start():match.start() + 6000]
            end = _COMPOSITION_END.search(block, match.end() - match.start())
            narratives.append((page_number, block[:end.start()] if end else block))
        for match in _COMPOSITION_SECTION.finditer(page):
            raw_block = page[match.end():match.end() + 9000]
            header_lines = raw_block.splitlines()[:6]
            header = " ".join(" ".join(header_lines).split())
            if re.search(r"\b(?:FRESH\s+ISSUE|OFFER\s+FOR\s+SALE)\s+SIZE\b", header, re.I):
                continue
            if any(
                len(re.findall(r"\b(?:FRESH\s+ISSUE|OFFER\s+FOR\s+SALE)\b", line, re.I)) > 1
                and not _COMPOSITION_PART.search(line)
                for line in header_lines
            ):
                continue
            block = " ".join(raw_block.split())
            end = _COMPOSITION_END.search(block)
            sections.append((page_number, block[:end.start()] if end else block))
    return narratives or sections


def _composition_amount(
    block: str, start: int
) -> tuple[float | None, int]:
    """Find the first aggregate amount inside this share-count clause only."""
    tail = block[start:start + 1000]
    boundary = _COMPOSITION_BOUNDARY.search(tail)
    if boundary:
        tail = tail[:boundary.start()]
    # A sentence break must not connect an unvalued component to another fact.
    sentence = re.search(r"(?<![0-9])\.(?=\s|$)|;", tail)
    if sentence:
        tail = tail[:sentence.start()]
    money = _COMPOSITION_MONEY.search(tail)
    if not money:
        return None, start
    amount = _number(money.group("amount"))
    if amount is None:
        return None, start
    unit = money.group("unit").lower()
    factor = 0.1 if unit.startswith("million") else 0.01 if unit.startswith(("lakh", "lac")) else 1.0
    return round(amount * factor, 6), start + money.end()


def _whole_ofs_sellers_match(block: str, start: int, total_shares: int, total_amount: float) -> bool:
    """Check seller disclosures without using them to value the whole offer."""
    tail = block[start:]
    leading = re.match(r"\s+OF\s+", tail, re.I)
    if not leading:
        return False
    boundary = re.search(
        r"\b(?:THE\s+(?:OFFER|ISSUE)\s+(?:INCLUDED|INCLUDES|CONSTITUTED|CONSTITUTES|LESS|AND)|"
        r"RESERVATION|RESERVED|SUBSCRIPTION|ALLOCATION|ALLOTMENT|NET\s+(?:OFFER|ISSUE))\b", tail, re.I,
    )
    if boundary:
        tail = tail[:boundary.start()]
    quantities = list(re.finditer(_COMPOSITION_QUANTITY, tail, re.I))
    if not quantities or quantities[0].start() != leading.end():
        return False
    total = 0
    amounts = []
    for index, quantity in enumerate(quantities):
        if index:
            separator = tail[quantities[index - 1].end():quantity.start()]
            if not re.search(r"(?:,\s*(?:AND\s+)?|\bAND\s+)$", separator, re.I):
                return False
        end = quantities[index + 1].start() if index + 1 < len(quantities) else len(tail)
        # Each quantity must be explicitly owned by a seller, not merely
        # appear in an adjacent component or reservation clause.
        row = tail[quantity.end():end]
        seller = re.search(r"\bBY\s+[A-Z]", row, re.I)
        prefix = _COMPOSITION_SELLER_PREFIX.fullmatch(row[:seller.start()]) if seller else None
        if not prefix:
            return False
        shares = int(quantity.group("shares").replace(",", ""))
        total += shares
        if prefix.group("amount") is not None:
            # This prefix is already bounded to its seller; a currency marker
            # such as "Rs. " must not be mistaken for a sentence boundary.
            amount = _number(prefix.group("amount"))
            if amount is None:
                return False
            unit = prefix.group("unit").lower()
            factor = 0.1 if unit.startswith("million") else 0.01 if unit.startswith(("lakh", "lac")) else 1.0
            amount = round(amount * factor, 6)
            if composition_problems({"ofsShares": shares, "ofsCr": amount}):
                return False
            if amount > total_amount and not amounts_match(amount, total_amount):
                return False
            amounts.append(amount)
    known_amount = sum(amounts)
    if known_amount > total_amount and not amounts_match(known_amount, total_amount):
        return False
    if len(amounts) == len(quantities) and not amounts_match(known_amount, total_amount):
        return False
    return total == total_shares


def _mixed_ofs_sellers(tail: str) -> tuple[int, float] | None:
    """Sum a complete, directly owned and fully quoted mixed-offer seller list."""
    quantities = list(re.finditer(_COMPOSITION_QUANTITY, tail, re.I))
    if not quantities or quantities[0].start() != 0:
        return None
    shares = 0
    amounts = []
    seller_alias = (
        r"\(\s*(?:THE\s+)?[\"“'](?:PROMOTER\s+|INVESTOR\s+|OTHER\s+)?"
        r"SELLING\s+SHAREHOLDERS?[\"”']\s*\)"
    )
    final_definition = (
        r"(?:\s+AND\s+SUCH\s+EQUITY\s+SHARES\s+OFFERED\s+BY\s+THE\s+"
        r"(?:PROMOTER\s+|INVESTOR\s+|OTHER\s+)?SELLING\s+SHAREHOLDERS)?\s*"
        r"\(\s*(?:THE\s+)?[\"“']OFFER\s+FOR\s+SALE[\"”']"
        r"(?:\s*,?\s*AND\s+TOGETHER\s+WITH\s+THE\s+FRESH\s+ISSUE\s*,\s*"
        r"THE\s+[\"“']OFFER[\"”'])?\s*\)"
    )
    for index, quantity in enumerate(quantities):
        end = quantities[index + 1].start() if index + 1 < len(quantities) else len(tail)
        row = tail[quantity.end():end]
        seller = re.search(r"\bBY\s+(?=[A-Z])", row, re.I)
        prefix = _COMPOSITION_SELLER_PREFIX.fullmatch(row[:seller.start()]) if seller else None
        if not prefix or prefix.group("amount") is None:
            return None
        owner = row[seller.end():].strip()
        if index + 1 < len(quantities):
            separator = re.search(r"(?:,\s*(?:AND\s+)?|\s+AND)\s*$", owner, re.I)
            if not separator:
                return None
            owner = owner[:separator.start()].strip()
        else:
            owner = re.sub(r"\s*" + final_definition + r"\s*\.?\s*$", "", owner, flags=re.I)
            owner = owner.rstrip(".").strip()
        owner = re.sub(r"\s*" + seller_alias + r"\s*$", "", owner, flags=re.I)
        # A seller must be named, not an adjacent reservation or a generic
        # shareholder group. Sentence breaks cannot join two disclosures.
        name = re.sub(r"\b(?:MR|MRS|MS|DR|PTE|LTD|INC|CORP|CO)\.(?=\s)", "", owner, flags=re.I)
        if re.search(r"\.(?=\s)|;|\b(?:EMPLOYEES|COMPANY)\b", name, re.I) or not _promoter_names(owner, single=True):
            return None
        amount = _number(prefix.group("amount"))
        if amount is None:
            return None
        unit = prefix.group("unit").lower()
        factor = 0.1 if unit.startswith("million") else 0.01 if unit.startswith(("lakh", "lac")) else 1.0
        amount = round(amount * factor, 6)
        count = int(quantity.group("shares").replace(",", ""))
        if composition_problems({"ofsShares": count, "ofsCr": amount}):
            return None
        shares += count
        amounts.append(amount)
    return shares, round(sum(amounts), 6)


def extract_final_issue_composition(
    text: str, price_band: dict[str, Any] | None = None
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Extract final offer clauses with independent, auditable field evidence.

    ``price_band`` remains a compatibility argument, but cannot value the final
    offer. A price stated as the final Issue/Offer Price in this document can.
    Repeated conflicting clauses fail closed, including conflicting totals.
    """
    candidate: dict[str, Any] = {}
    evidence: dict[str, Any] = {}
    ambiguous = False

    def observe(field: str, value: float | int, page: int, row: str, basis: str = "explicit final offer clause") -> None:
        nonlocal ambiguous
        if field in candidate and candidate[field] != value:
            ambiguous = True
            return
        candidate[field] = value
        evidence.setdefault(field, {"page": page, "row": row, "normalizedValue": value, "basis": basis})

    for page_number, block in _composition_blocks(text):
        seller_label_start = None
        total = _COMPOSITION_INITIAL.search(block)
        if total:
            total_amount, end = _composition_amount(block, total.end())
            row = block[total.start():max(total.end(), end)]
            observe("totalShares", int(total.group("shares").replace(",", "")), page_number, row)
            if total_amount is not None:
                observe("totalIssueSizeCr", total_amount, page_number, row)
                # Some fresh-only covers define the entire Initial Public Issue
                # as the Fresh Issue after its total, rather than before it.
                definition = re.match(
                    _COMPOSITION_FOOTNOTE
                    + r"\(\s*(?:THE\s+)?[\"“'](?:ISSUE[\"”']\s+OR\s+[\"“'])?"
                    r"FRESH\s+ISSUE[\"”']\s*\)",
                    block[end:], re.I,
                )
                if definition:
                    row = block[total.start():end + definition.end()]
                    observe("freshShares", candidate["totalShares"], page_number, row)
                    observe("freshIssueCr", total_amount, page_number, row)
                # This definition attaches the whole Initial Public Offer to
                # OFS. Its following quantities can belong to individual
                # sellers, so keep the initial total rather than skipping the
                # parenthesis in the ordinary component recognizer.
                whole_ofs = _COMPOSITION_WHOLE_OFS.match(block[end:])
                if whole_ofs:
                    mixed_fresh = any(
                        not _COMPOSITION_EMPTY_PART.match(block, mention.start())
                        for mention in re.finditer(r"\bFRESH\s+ISSUE\b", block, re.I)
                    )
                    if mixed_fresh or not _whole_ofs_sellers_match(
                        block, end + whole_ofs.end(), candidate["totalShares"], total_amount
                    ):
                        # The shorthand cannot resolve a separate fresh-issue
                        # clause or an incomplete/conflicting seller list.
                        ambiguous = True
                    else:
                        row = block[total.start():end + whole_ofs.end()]
                        basis = "entire initial offer explicitly defined as offer for sale"
                        observe("ofsShares", candidate["totalShares"], page_number, row, basis)
                        observe("ofsCr", total_amount, page_number, row, basis)
                        if whole_ofs.group("seller_label"):
                            seller_label_start = end + whole_ofs.start("seller_label")
        else:
            for label in re.finditer(r"\bTOTAL\s+(?:ISSUE|OFFER)(?:\s+SIZE)?\b", block, re.I):
                amount, end = _composition_amount(block, label.end())
                if amount is not None:
                    observe("totalIssueSizeCr", amount, page_number, block[label.start():end])

        parts = list(_COMPOSITION_PART.finditer(block))
        for part_index, match in enumerate(parts):
            shares = int(match.group("shares").replace(",", ""))
            if match.start() == seller_label_start and shares != candidate.get("totalShares"):
                # This exact label introduces the corroborated seller list.
                # A sole seller equal to the entire offer, and all separate
                # component clauses, still participate in amount conflicts.
                continue
            prefix = "fresh" if match.group("label").upper().startswith("FRESH") else "ofs"
            if prefix == "ofs" and total:
                fresh = next((part for part in reversed(parts[:part_index]) if part.group("label").upper().startswith("FRESH")), None)
                if fresh:
                    # Keep this path local to the initial offer and its fresh
                    # component. Subsequent explicit components still pass
                    # through observe, including repeated OFS contradictions.
                    tail_end = parts[part_index + 1].start() if part_index + 1 < len(parts) else len(block)
                    tail = block[match.start("shares"):tail_end]
                    boundary = re.search(
                        r"\b(?:INITIAL\s+PUBLIC|PRE[-\s]?IPO|NET\s+PROCEEDS|OBJECTS\s+OF|"
                        r"THE\s+(?:OFFER|ISSUE)\s+(?:INCLUDED|INCLUDES|CONSTITUTED|CONSTITUTES|LESS|AND)|"
                        r"RESERVATION|RESERVED|SUBSCRIPTION|ALLOCATION|ALLOTMENT|NET\s+(?:OFFER|ISSUE))\b",
                        tail, re.I,
                    )
                    if boundary:
                        tail = tail[:boundary.start()]
                    quantities = list(re.finditer(_COMPOSITION_QUANTITY, tail, re.I))
                    expected_shares = int(total.group("shares").replace(",", "")) - int(fresh.group("shares").replace(",", ""))
                    first_end = quantities[1].start() if len(quantities) > 1 else len(tail)
                    first_tail = tail[quantities[0].end():first_end]
                    owner = re.search(r"\bBY\b", first_tail, re.I)
                    directly_owned = owner and _COMPOSITION_SELLER_PREFIX.fullmatch(first_tail[:owner.start()])
                    breakdown = re.search(
                        r"\b(?:COMPRISING|INCLUDING)\b|\(\s*(?:THE\s+)?[\"“'](?:OFFERED\s+SHARES|OFFER\s+FOR\s+SALE)",
                        first_tail[:owner.start()] if owner else first_tail, re.I,
                    )
                    if shares != expected_shares or directly_owned or (len(quantities) > 1 and not breakdown):
                        summed = _mixed_ofs_sellers(tail)
                        fresh_amount, _ = _composition_amount(block, fresh.end())
                        if (
                            summed is None or summed[0] != expected_shares
                            or fresh_amount is None or total_amount is None
                            or not amounts_match(fresh_amount + summed[1], total_amount)
                        ):
                            ambiguous = True
                            continue
                        row = block[match.start():match.start("shares")] + tail
                        basis = "sum of complete named OFS seller clauses, reconciled with explicit fresh issue and initial offer"
                        observe("ofsShares", summed[0], page_number, row, basis)
                        observe("ofsCr", summed[1], page_number, row, basis)
                        continue
            amount, end = _composition_amount(block, match.end())
            row = block[match.start():max(match.end(), end)]
            observe(prefix + "Shares", shares, page_number, row)
            if amount is not None:
                observe("freshIssueCr" if prefix == "fresh" else "ofsCr", amount, page_number, row)

        for match in _COMPOSITION_EMPTY_PART.finditer(block):
            prefix = "fresh" if match.group("label").upper().startswith("FRESH") else "ofs"
            observe(prefix + "Shares", 0, page_number, match.group(0))
            observe("freshIssueCr" if prefix == "fresh" else "ofsCr", 0.0, page_number, match.group(0))

    if ambiguous or not any(field in candidate for field in _SHARE_FIELDS):
        return None, {}

    total_shares = candidate.pop("totalShares", None)
    if total_shares is not None:
        fresh, ofs = candidate.get("freshShares"), candidate.get("ofsShares")
        if any(shares is not None and shares > total_shares for shares in (fresh, ofs)):
            return None, {}
        if fresh is not None and ofs is not None:
            if fresh + ofs != total_shares:
                return None, {}
        elif fresh == total_shares or ofs == total_shares:
            # An explicit component that equals the entire stated offer proves
            # there are no shares in the other component; absence alone cannot.
            missing = "ofs" if fresh == total_shares else "fresh"
            source = evidence["totalShares"]
            basis = "stated component equals the entire stated offer share count"
            observe(missing + "Shares", 0, source["page"], source["row"], basis)
            observe("ofsCr" if missing == "ofs" else "freshIssueCr", 0.0, source["page"], source["row"], basis)

    final_price, price_evidence = extract_final_issue_price(text)
    # An offer discount can make shares * headline price an overstatement.
    # Explicit disclosed amounts remain usable; unsupported discount arithmetic
    # must never supply missing amounts or claim uniform-price valuation.
    discount = bool(re.search(r"\bDISCOUNT(?:ED)?\b", "\f".join(str(text or "").split("\f")[:12]), re.I))
    if final_price is not None and not discount:
        candidate["valuationPriceUsed"] = final_price
        evidence["valuationPriceUsed"] = price_evidence["issuePrice"]
        for shares_field, amount_field in (("freshShares", "freshIssueCr"), ("ofsShares", "ofsCr")):
            if shares_field in candidate and amount_field not in candidate:
                source = evidence[shares_field]
                amount = round(candidate[shares_field] * final_price / 10_000_000, 6)
                observe(amount_field, amount, source["page"], source["row"], "explicit share count multiplied by explicit final issue price")

    if "totalIssueSizeCr" not in candidate and all(field in candidate for field in ("freshIssueCr", "ofsCr")):
        source = evidence["freshIssueCr"]
        observe("totalIssueSizeCr", round(candidate["freshIssueCr"] + candidate["ofsCr"], 6), source["page"], source["row"], "sum of independently evidenced fresh issue and offer for sale")

    if ambiguous:
        return None, {}
    composition = validate_issue_composition(candidate)
    if not composition:
        return None, {}
    first = next(value for key, value in evidence.items() if key != "valuationPriceUsed")
    return composition, {
        "issueComposition": {
            "basis": "validated Final Prospectus issue composition",
            "method": "bounded-final-offer-clauses-v1",
            "page": first["page"],
            "heading": "Final offer composition",
            "fields": evidence,
            "totalShares": total_shares,
            "freshShares": composition.get("freshShares"),
            "ofsShares": composition.get("ofsShares"),
            "freshIssueCr": composition.get("freshIssueCr"),
            "ofsCr": composition.get("ofsCr"),
            "totalIssueSizeCr": composition.get("totalIssueSizeCr"),
        }
    }


def parse_document_text(text: str, price_band=None) -> dict[str, Any]:
    parsed = base.parse_document_text(text, price_band)
    promoters, promoter_evidence = extract_final_promoters(text)
    parsed["finalPromoterAssessment"] = "accepted" if promoters else "unresolved"
    if promoters:
        parsed["promoters"] = promoters
    else:
        parsed.pop("promoters", None)
    objects, object_evidence = extract_objects(text)
    if objects and not objects_evidence_problems(objects, object_evidence.get("objectsOfIssue")):
        parsed["objectsOfIssue"] = objects
    else:
        objects, object_evidence = [], {}
        parsed.pop("objectsOfIssue", None)

    lot_size, lot_evidence = extract_final_lot_size(text)
    if lot_size is not None:
        parsed["lotSize"] = lot_size

    shareholding, shareholding_evidence = extract_final_promoter_shareholding(text)
    if shareholding is not None:
        parsed["shareholding"] = shareholding

    issue_price, price_evidence = extract_final_issue_price(text)
    if issue_price is not None:
        parsed["issuePrice"] = issue_price

    explicit_band, band_evidence = extract_explicit_price_band(text)
    if explicit_band is not None:
        parsed["priceBand"] = explicit_band
    else:
        parsed.pop("priceBand", None)

    composition, composition_evidence = extract_final_issue_composition(text)
    if composition is not None:
        parsed["issueComposition"] = composition
    else:
        parsed.pop("issueComposition", None)

    field_evidence = dict(parsed.get("fieldEvidence") or {})
    field_evidence.pop("promoters", None)
    field_evidence.pop("issueComposition", None)
    field_evidence.pop("objectsOfIssue", None)
    field_evidence.update(object_evidence)
    field_evidence.update(lot_evidence)
    field_evidence.update(promoter_evidence)
    field_evidence.update(shareholding_evidence)
    field_evidence.update(price_evidence)
    field_evidence.update(band_evidence)
    field_evidence.update(composition_evidence)
    parsed["fieldEvidence"] = field_evidence

    extracted = [
        field
        for field in (parsed.get("extractedFields") or [])
        if field not in {"priceBand", "issueComposition", "promoters", "objectsOfIssue"}
    ]
    if objects:
        extracted.append("objectsOfIssue")
    if promoters:
        extracted.append("promoters")
    if lot_size is not None and "lotSize" not in extracted:
        extracted.append("lotSize")
    if shareholding is not None and "shareholding" not in extracted:
        extracted.append("shareholding")
    if explicit_band is not None and "priceBand" not in extracted:
        extracted.append("priceBand")
    if issue_price is not None and "issuePrice" not in extracted:
        extracted.append("issuePrice")
    if composition is not None and "issueComposition" not in extracted:
        extracted.append("issueComposition")
    parsed["extractedFields"] = extracted
    parsed["finalProspectusParserVersion"] = PARSER_VERSION
    return parsed
