#!/usr/bin/env python3
"""Phase 3: enrich IPO records from SEBI abridged offer documents.

The extractor intentionally prioritizes short Abridged Prospectus PDFs because
those documents repeat the most decision-useful RHP/Prospectus disclosures in a
consistent, machine-readable form. Missing values remain null; no OCR or
third-party data is used.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"
IST = ZoneInfo("Asia/Kolkata")
PARSER_VERSION = 1
MAX_PDF_BYTES = 20 * 1024 * 1024

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/152 Safari/537.36"
    ),
    "Accept": "application/pdf,text/html,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def now_ist():
    return datetime.now(IST)


def number(v):
    if v is None:
        return None
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?", str(v).replace("₹", ""))
    return float(m.group().replace(",", "")) if m else None


def integer(v):
    n = number(v)
    return int(n) if n is not None else None


def norm_space(text: str) -> str:
    return re.sub(r"[ \t]+", " ", (text or "").replace("\u00a0", " ")).strip()


def clean_name(name: str) -> str:
    value = re.sub(r"\s+", " ", (name or "").replace("\u00a0", " ")).strip(" ,.;:-")
    return re.sub(r"^\d+\.\s*", "", value).strip()


def dedupe(items):
    out = []
    seen = set()
    for item in items:
        key = item.casefold() if isinstance(item, str) else json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def detect_money_unit(text: str) -> str:
    t = text.lower()
    if re.search(r"(?:₹|rs\.?|inr)\s*(?:in\s*)?million", t):
        return "million"
    if re.search(r"(?:₹|rs\.?|inr)\s*(?:in\s*)?(?:lakhs?|lacs?)", t):
        return "lakh"
    if re.search(r"(?:₹|rs\.?|inr)\s*(?:in\s*)?(?:crores?|cr\.?)", t):
        return "crore"
    return "crore"


def to_crore(value, unit):
    if value is None:
        return None
    if unit == "million":
        return round(float(value) / 10.0, 4)
    if unit == "lakh":
        return round(float(value) / 100.0, 4)
    return round(float(value), 4)


def section(text: str, starts, ends, max_chars=None) -> str:
    flags = re.I | re.S
    start_match = None
    for pattern in starts:
        m = re.search(pattern, text, flags)
        if m and (start_match is None or m.start() < start_match.start()):
            start_match = m
    if not start_match:
        return ""
    start = start_match.end()
    end = len(text)
    for pattern in ends:
        m = re.search(pattern, text[start:], flags)
        if m:
            end = min(end, start + m.start())
    block = text[start:end]
    return block[:max_chars] if max_chars else block


def _legal_entities(block: str) -> list[str]:
    if not block:
        return []
    flat = norm_space(block)
    flat = re.sub(
        r"Name\s+and\s+Logo\s+of\s+the\s+Book\s+Running\s+Lead\s+Manager(?:s)?",
        " ",
        flat,
        flags=re.I,
    )
    flat = re.sub(r"Name\s+of\s+the\s+Registrar", " ", flat, flags=re.I)
    flat = re.sub(r"Contact\s+Person\s+E-?mail\s+and\s+Telephone", " ", flat, flags=re.I)
    pattern = re.compile(
        r"([A-Z][A-Za-z0-9&'().,/+-]*(?:\s+[A-Z][A-Za-z0-9&'().,/+-]*){0,8}\s+"
        r"(?:Private\s+Limited|Limited|Ltd\.?|LLP))"
    )
    banned = ("BOOK RUNNING", "LEAD MANAGER", "REGISTRAR", "NAME AND LOGO", "NAME OF THE")
    found = []
    for m in pattern.finditer(flat):
        name = clean_name(m.group(1))
        if any(x in name.upper() for x in banned):
            continue
        found.append(name)
    return dedupe(found)


def extract_intermediaries(text: str):
    lead_block = section(
        text,
        [r"BOOK\s+RUNNING\s+LEAD\s+MANAGER(?:S)?"],
        [r"REGISTRAR\s+TO\s+THE\s+ISSUE", r"BID\s*/?\s*ISSUE\s+PERIOD"],
        2500,
    )
    registrar_block = section(
        text,
        [r"REGISTRAR\s+TO\s+THE\s+ISSUE"],
        [r"BID\s*/?\s*ISSUE\s+PERIOD", r"ANCHOR\s+INVESTOR", r"IN\s+THE\s+NATURE"],
        1500,
    )
    leads = _legal_entities(lead_block)
    registrars = _legal_entities(registrar_block)
    return leads, (registrars[0] if registrars else None)


def extract_promoters(text: str) -> list[str]:
    block = section(
        text,
        [r"THE\s+PROMOTERS\s+OF\s+OUR\s+COMPANY"],
        [r"DETAILS\s+OF\s+THE\s+ISSUE"],
        1200,
    )
    if block:
        first_line = next(
            (norm_space(line) for line in block.splitlines() if norm_space(line)),
            "",
        )
        if first_line:
            pieces = re.split(r"\s*,\s*|\s+\bAND\b\s+", first_line, flags=re.I)
            names = [clean_name(x) for x in pieces if 2 <= len(clean_name(x)) <= 100]
            if 1 <= len(names) <= 12:
                return dedupe(names)

    m = re.search(
        r"(?:\b3\.\s*)?Promoters\s+(.*?)\s+(?:are|is)\s+the\s+Promoters?\s+of\s+our\s+Company",
        text,
        re.I | re.S,
    )
    if m:
        flat = norm_space(m.group(1))
        pieces = re.split(r"\s*,\s*|\s+\band\b\s+", flat, flags=re.I)
        names = [clean_name(x) for x in pieces if 2 <= len(clean_name(x)) <= 100]
        return dedupe(names[:12])
    return []


def _share_count(patterns, text):
    for pattern in patterns:
        m = re.search(pattern, text, re.I | re.S)
        if m:
            return integer(m.group(1))
    return None


def extract_issue_composition(text: str, price_band=None):
    block = section(
        text,
        [r"DETAILS\s+OF\s+THE\s+ISSUE"],
        [r"RISKS?\s+IN\s+RELATION", r"GENERAL\s+RISK", r"LISTING"],
        5000,
    ) or text[:8000]

    fresh_shares = _share_count(
        [
            r"Fresh\s+issue\s+of\s+up\s+to\s+([\d,]+)\s+Equity\s+Shares",
            r"Fresh\s+Issue.*?up\s+to\s+([\d,]+)\s+Equity\s+Shares",
        ],
        block,
    )
    ofs_shares = _share_count(
        [
            r"Offer\s+for\s+Sale\s+of\s+up\s+to\s+([\d,]+)\s+Equity\s+Shares",
            r"Offer\s+for\s+Sale.*?up\s+to\s+([\d,]+)\s+Equity\s+Shares",
        ],
        block,
    )
    if re.search(r"DETAILS\s+OF\s+THE\s+OFFER\s+FOR\s+SALE\s+NOT\s+APPLICABLE", block, re.I | re.S):
        ofs_shares = 0

    cap = number((price_band or {}).get("max")) if isinstance(price_band, dict) else None
    fresh_cr = round(fresh_shares * cap / 10_000_000, 2) if fresh_shares and cap else None
    ofs_cr = round(ofs_shares * cap / 10_000_000, 2) if ofs_shares and cap else (0.0 if ofs_shares == 0 else None)
    total_cr = (
        round((fresh_cr or 0) + (ofs_cr or 0), 2)
        if fresh_cr is not None and ofs_cr is not None
        else fresh_cr if fresh_cr is not None and ofs_shares == 0
        else None
    )

    return {
        "freshShares": fresh_shares,
        "ofsShares": ofs_shares,
        "freshIssueCr": fresh_cr,
        "ofsCr": ofs_cr,
        "totalIssueSizeCr": total_cr,
        "valuationPriceUsed": cap,
    }


def _numeric_tokens(text: str):
    cleaned = re.sub(r"\(\d+\)", "", text)
    tokens = re.findall(r"\(?-?\d[\d,]*(?:\.\d+)?\)?%?", cleaned)
    out = []
    for token in tokens:
        neg = token.startswith("(") and token.rstrip("%").endswith(")")
        raw = token.replace(",", "").replace("%", "").strip("()")
        try:
            value = float(raw)
        except ValueError:
            continue
        out.append(-value if neg else value)
    return out


def _series_line(lines, patterns, periods):
    for line in lines:
        clean = norm_space(line)
        for pattern in patterns:
            m = re.search(pattern, clean, re.I)
            if m:
                vals = _numeric_tokens(clean[m.end():])
                if len(vals) >= len(periods):
                    return vals[: len(periods)]
    return []


def extract_financials(text: str):
    financial_block = section(
        text,
        [r"Summary\s+of\s+Restated.*?Financial\s+Information"],
        [r"Summary\s+of\s+Key\s+Performance\s+Indicators", r"\bRisk\s+Factors\b"],
        7000,
    )
    kpi_block = section(
        text,
        [r"Summary\s+of\s+Key\s+Performance\s+Indicators", r"Key\s+Performance\s+Indicators\s*\(KPIs\)"],
        [r"\bRisk\s+Factors\b", r"Details\s+of\s+the\s+weighted"],
        7000,
    )
    block = financial_block or kpi_block
    if not block:
        return None

    years = re.findall(r"\b(?:Fiscal|FY)\s*(20\d{2})\b", block, re.I)
    if not years and kpi_block:
        years = re.findall(r"\b(?:Fiscal|FY)\s*(20\d{2})\b", kpi_block, re.I)
    years = dedupe(years)[:4]
    if not years:
        return None

    lines = (financial_block + "\n" + kpi_block).splitlines()
    unit = detect_money_unit(financial_block or kpi_block)
    revenue = _series_line(lines, [r"Revenue\s+from\s+Operations"], years)
    ebitda = _series_line(lines, [r"\bEBITDA\b(?!\s+Margin)"], years)
    pat = _series_line(
        lines,
        [r"Profit\s+after\s+Tax(?:\s*\(PAT\))?", r"Net\s+Profit\s+after\s+tax"],
        years,
    )
    net_worth = _series_line(lines, [r"^Net\s+Worth\b"], years)
    ronw = _series_line(lines, [r"Return\s+on\s+Net\s+Worth"], years)
    roe = _series_line(lines, [r"Return\s+on\s+Equity"], years)
    eps = _series_line(
        lines,
        [r"(?:Basic\s+and\s+Diluted\s+)?Earnings\s+per\s+Share", r"\bBasic\s+EPS\b"],
        years,
    )

    periods = []
    for idx, year in enumerate(years):
        row = {"period": f"FY{year}"}
        if idx < len(revenue):
            row["revenueCr"] = to_crore(revenue[idx], unit)
        if idx < len(ebitda):
            row["ebitdaCr"] = to_crore(ebitda[idx], unit)
        if idx < len(pat):
            row["patCr"] = to_crore(pat[idx], unit)
        if idx < len(net_worth):
            row["netWorthCr"] = to_crore(net_worth[idx], unit)
        if idx < len(ronw):
            row["ronwPct"] = ronw[idx]
        if idx < len(roe):
            row["roePct"] = roe[idx]
        if idx < len(eps):
            row["eps"] = eps[idx]
        if len(row) > 1:
            periods.append(row)

    return {"unit": "₹ crore", "periods": periods} if periods else None


def extract_objects(text: str):
    block = section(
        text,
        [r"\bObjects\s+of\s+the\s+Issue\b"],
        [r"Pre\s+and\s+Post[-\s]?Issue", r"Summary\s+of\s+Restated", r"\bRisk\s+Factors\b"],
        6000,
    )
    if not block:
        return []

    unit = detect_money_unit(block)
    out = []
    for raw in block.splitlines():
        line = norm_space(raw)
        if not line or len(line) < 6:
            continue
        if re.search(r"^(?:The Net Proceeds|Particulars|Amount|\(?₹|For further details|Grand Total|Note)", line, re.I):
            continue
        m = re.match(r"(.+?)\s+((?:[\d,]+(?:\.\d+)?)|\[.?●.?\])(?:\s*)$", line)
        if not m:
            continue
        purpose = clean_name(m.group(1))
        if len(purpose) < 5:
            continue
        token = m.group(2)
        amount = None if "●" in token else to_crore(number(token), unit)
        out.append({"purpose": purpose, "amountCr": amount})
    return out[:12]


def extract_promoter_shareholding(text: str):
    block = section(
        text,
        [r"Pre\s+and\s+Post[-\s]?Issue\s+shareholding"],
        [r"Summary\s+of\s+Restated", r"Summary\s+of\s+Key\s+Performance"],
        7000,
    )
    if not block:
        return None

    rows = []
    started = False
    for raw in block.splitlines():
        line = norm_space(raw)
        if re.search(r"Promoters?\s+and\s+Promoter\s+Group", line, re.I):
            started = True
            continue
        if started and re.fullmatch(r"Promoter\s+Group(?:\s*\(\d+\))?", line, re.I):
            break
        if not started:
            continue
        m = re.match(
            r"^\d+\.\s+(.+?)\s+([\d,.]+|Nil)\s+(\d+(?:\.\d+)?|Negligible)\b",
            line,
            re.I,
        )
        if not m:
            continue
        name = clean_name(m.group(1))
        shares = 0 if m.group(2).lower() == "nil" else integer(m.group(2))
        pct = 0.0 if m.group(3).lower() == "negligible" else number(m.group(3))
        rows.append({"name": name, "preIssueShares": shares, "preIssuePct": pct})

    if not rows:
        return None
    total_pct = round(sum(r.get("preIssuePct") or 0 for r in rows), 4)
    return {"promoters": rows, "promoterPreIssuePct": total_pct}


def parse_document_text(text: str, price_band=None):
    text = text.replace("\r", "\n")
    leads, registrar = extract_intermediaries(text)
    promoters = extract_promoters(text)
    issue = extract_issue_composition(text, price_band)
    financials = extract_financials(text)
    objects = extract_objects(text)
    shareholding = extract_promoter_shareholding(text)

    result = {
        "leadManagers": leads,
        "registrar": registrar,
        "promoters": promoters,
        "issueComposition": issue,
        "financials": financials,
        "objectsOfIssue": objects,
        "shareholding": shareholding,
    }
    extracted_fields = []
    if leads:
        extracted_fields.append("leadManagers")
    if registrar:
        extracted_fields.append("registrar")
    if promoters:
        extracted_fields.append("promoters")
    if any(v not in (None, 0) for v in issue.values()):
        extracted_fields.append("issueComposition")
    if financials:
        extracted_fields.append("financials")
    if objects:
        extracted_fields.append("objectsOfIssue")
    if shareholding:
        extracted_fields.append("shareholding")
    result["extractedFields"] = extracted_fields
    return result


def choose_document(record):
    docs = record.get("documents") or []
    candidates = []
    rank = {"PROSPECTUS": 4, "RHP": 3, "UDRHP": 2, "DRHP": 1}
    for d in docs:
        url = str(d.get("url") or "")
        title = str(d.get("title") or "")
        if not url.lower().endswith(".pdf"):
            continue
        if "ABRIDGED" not in title.upper() and "AP_" not in url.upper():
            continue
        typ = str(d.get("type") or "").upper()
        candidates.append((rank.get(typ, 0), d.get("filedDate") or "", len(title), d))
    if not candidates:
        return None
    return max(candidates, key=lambda x: (x[0], x[1], x[2]))[3]


def download_pdf(session, url):
    with session.get(url, headers=HEADERS, stream=True, timeout=45) as r:
        r.raise_for_status()
        ctype = (r.headers.get("content-type") or "").lower()
        length = integer(r.headers.get("content-length"))
        if length and length > MAX_PDF_BYTES:
            raise ValueError(f"PDF too large ({length} bytes)")
        chunks = []
        total = 0
        for chunk in r.iter_content(128 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > MAX_PDF_BYTES:
                raise ValueError("PDF exceeded size limit")
            chunks.append(chunk)
        data = b"".join(chunks)
        if not data.startswith(b"%PDF") and "pdf" not in ctype:
            raise ValueError(f"URL did not return a PDF ({ctype or 'unknown content type'})")
        return data


def extract_pdf_text(data: bytes):
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            pass
    pages = []
    for i, page in enumerate(reader.pages):
        if i >= 30:
            break
        pages.append(page.extract_text() or "")
    text = "\n".join(pages)
    if len(norm_space(text)) < 500:
        raise ValueError("PDF contained too little extractable text")
    return text, min(len(reader.pages), 30), len(reader.pages)


def apply_enrichment(record, parsed, doc, pdf_hash, pages_read, page_count):
    issue = parsed.get("issueComposition") or {}

    if record.get("freshIssueCr") is None and issue.get("freshIssueCr") is not None:
        record["freshIssueCr"] = issue["freshIssueCr"]
    if record.get("ofsCr") is None and issue.get("ofsCr") is not None:
        record["ofsCr"] = issue["ofsCr"]
    if record.get("issueSizeCr") is None and issue.get("totalIssueSizeCr") is not None:
        record["issueSizeCr"] = issue["totalIssueSizeCr"]

    for field in ("leadManagers", "registrar", "promoters", "financials", "objectsOfIssue", "shareholding"):
        value = parsed.get(field)
        if value not in (None, [], {}):
            record[field] = value

    if any(v is not None for v in issue.values()):
        record["issueComposition"] = issue

    record["offerDocumentExtraction"] = {
        "status": "extracted",
        "parserVersion": PARSER_VERSION,
        "documentUrl": doc.get("url"),
        "documentType": doc.get("type"),
        "documentTitle": doc.get("title"),
        "documentFiledDate": doc.get("filedDate"),
        "sha256": pdf_hash,
        "pagesRead": pages_read,
        "pageCount": page_count,
        "extractedFields": parsed.get("extractedFields") or [],
        "extractedAt": now_ist().isoformat(timespec="seconds"),
        "source": "SEBI",
    }


def priority(record):
    status_rank = {"open": 0, "upcoming": 1, "closed": 2, "listed": 3}
    status = str(record.get("status") or "")
    date_key = (
        record.get("openDate")
        or (record.get("lifecycle") or {}).get("stageDate")
        or record.get("listingDate")
        or ""
    )
    date_num = int(str(date_key).replace("-", "")) if date_key else 0
    return (status_rank.get(status, 4), -date_num)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=6)
    p.add_argument("--force", action="store_true")
    p.add_argument("--company", default=None)
    a = p.parse_args()

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = payload.get("ipos") or []
    session = requests.Session()
    session.headers.update(HEADERS)

    candidates = []
    for rec in records:
        if a.company and a.company.lower() not in str(rec.get("company") or "").lower():
            continue
        doc = choose_document(rec)
        if not doc:
            continue
        prev = rec.get("offerDocumentExtraction") or {}
        if (
            not a.force
            and prev.get("status") == "extracted"
            and prev.get("parserVersion") == PARSER_VERSION
            and prev.get("documentUrl") == doc.get("url")
        ):
            continue
        candidates.append((priority(rec), rec, doc))

    candidates.sort(key=lambda x: x[0])
    total_eligible = len(candidates)
    if a.limit > 0:
        candidates = candidates[: a.limit]

    attempted = extracted = failed = 0
    errors = []
    for _, rec, doc in candidates:
        attempted += 1
        try:
            data = download_pdf(session, doc["url"])
            text, pages_read, page_count = extract_pdf_text(data)
            parsed = parse_document_text(text, rec.get("priceBand"))
            if not parsed.get("extractedFields"):
                raise ValueError("no structured fields recognized")
            digest = hashlib.sha256(data).hexdigest()
            apply_enrichment(rec, parsed, doc, digest, pages_read, page_count)
            extracted += 1
            print(
                f"Extracted {rec.get('company')}: "
                f"{', '.join(parsed.get('extractedFields') or [])}"
            )
        except Exception as exc:
            failed += 1
            msg = f"{rec.get('company')}: {exc}"
            errors.append(msg)
            rec["offerDocumentExtraction"] = {
                "status": "error",
                "parserVersion": PARSER_VERSION,
                "documentUrl": doc.get("url"),
                "lastAttemptAt": now_ist().isoformat(timespec="seconds"),
                "error": str(exc)[:300],
                "source": "SEBI",
            }
            print(f"Offer document extraction failed: {msg}")

    meta = payload.setdefault("meta", {})
    meta["schemaVersion"] = max(int(meta.get("schemaVersion") or 1), 3)
    meta["offerDocumentHealth"] = {
        "ok": failed == 0 if attempted else True,
        "attempted": attempted,
        "extracted": extracted,
        "failed": failed,
        "eligibleRemaining": max(0, total_eligible - extracted),
        "parserVersion": PARSER_VERSION,
        "asOf": now_ist().isoformat(timespec="seconds"),
        "errors": errors[:10],
    }
    meta.setdefault("sourceHealth", {})["Offer-docs"] = {
        "ok": failed == 0 if attempted else True,
        "records": extracted,
        "attempted": attempted,
        "failed": failed,
    }

    DATA_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Offer docs: attempted={attempted}, extracted={extracted}, failed={failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
