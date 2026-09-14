#!/usr/bin/env python3
"""Build data/ipos.json from NSE, SEBI and BSE public-market sources."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from record_integrity import issue_id

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"
IST = ZoneInfo("Asia/Kolkata")

NSE_HOME = "https://www.nseindia.com"
NSE_API = f"{NSE_HOME}/api"
NSE_SOURCE_URL = f"{NSE_HOME}/market-data/all-upcoming-issues-ipo"

SEBI_HOME = "https://www.sebi.gov.in"
SEBI_URL = (
    f"{SEBI_HOME}/sebiweb/home/HomeAction.do"
    "?doListingAll=yes&sid=3&smid=0&ssid=0"
)

BSE_HOME = "https://www.bseindia.com"
BSE_URL = f"{BSE_HOME}/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p"
BSE_URLS = [
    BSE_URL,
    "https://beta.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/152 Safari/537.36"
    ),
    "Accept": "application/json,text/html,application/xhtml+xml,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def now_ist():
    return datetime.now(IST)


def slugify(v: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", v.strip().lower()).strip("-") or "ipo"


def canonical_company(v: str) -> str:
    t = v.upper().replace("&", " AND ")
    t = re.sub(
        r"\b(LIMITED|LTD|PRIVATE|PVT|INCORPORATED|INC|CORPORATION|CORP)\b",
        " ",
        t,
    )
    t = re.sub(
        r"\b(ADDENDUM|CORRIGENDUM|UDRHP|DRHP|RHP|PROSPECTUS|DRAFT|ABRIDGED|"
        r"OFFER|DOCUMENT|FINAL|RED HERRING)\b",
        " ",
        t,
    )
    return re.sub(r"[^A-Z0-9]+", "", t)


def first(d: dict[str, Any], *keys, default=None):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", "-", "--", "NA", "N/A"):
            return v
    return default


def number(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        return float(v)
    m = re.search(
        r"-?\d+(?:\.\d+)?",
        str(v).replace(",", "").replace("₹", ""),
    )
    return float(m.group()) if m else None


def integer(v):
    n = number(v)
    return int(n) if n is not None else None


def iso_date(v):
    if v in (None, "", "-", "--"):
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()

    t = re.sub(r"\s+", " ", str(v).strip())
    for f in (
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
    ):
        try:
            return datetime.strptime(t, f).date().isoformat()
        except ValueError:
            pass
    return None


_DATE_TOKEN_RE = re.compile(
    r"(?:\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}"
    r"|\d{1,2}[-/]\d{1,2}[-/]\d{4}"
    r"|\d{4}-\d{1,2}-\d{1,2})"
)


def parse_period(text: str):
    parsed = []
    for token in _DATE_TOKEN_RE.findall(text or ""):
        d = iso_date(token)
        if d and d not in parsed:
            parsed.append(d)
        if len(parsed) == 2:
            break
    return (
        (parsed[0], parsed[1])
        if len(parsed) >= 2
        else (parsed[0], None)
        if parsed
        else (None, None)
    )


def parse_price_band_text(text: str):
    nums = [
        float(x.replace(",", ""))
        for x in re.findall(
            r"\d+(?:\.\d+)?",
            (text or "").replace(",", ""),
        )
    ]
    if not nums:
        return None
    return {"min": nums[0], "max": nums[-1]}


def price_band(r):
    lo = number(first(r, "minPrice", "priceMin", "lowerPrice", "floorPrice", "priceBandMin"))
    hi = number(first(r, "maxPrice", "priceMax", "upperPrice", "capPrice", "priceBandMax"))
    raw = first(r, "issuePrice", "priceBand", "priceRange")
    if (lo is None or hi is None) and raw is not None:
        p = parse_price_band_text(str(raw))
        if p:
            lo = lo if lo is not None else p["min"]
            hi = hi if hi is not None else p["max"]
    if lo is None and hi is None:
        return None
    return {
        "min": lo if lo is not None else hi,
        "max": hi if hi is not None else lo,
    }


def nse_issue_metrics(r, band):
    """Return (issue_size_crore, shares_offered) without mixing shares and rupees."""
    explicit_cr = number(
        first(
            r,
            "issueSizeCr",
            "issueSizeInCr",
            "issueSizeRsCr",
            "totalIssueSizeCr",
            "issueSizeCrore",
        )
    )
    raw_issue = number(first(r, "issueSize", "totalIssueSize"))
    shares = integer(
        first(
            r,
            "noOfSharesOffered",
            "sharesOffered",
            "numberOfSharesOffered",
            "totalSharesOffered",
        )
    )

    # Some NSE live/upcoming payloads use issueSize for share quantity.
    if shares is None and raw_issue is not None and raw_issue >= 100_000:
        shares = int(raw_issue)

    size_cr = explicit_cr
    upper_price = number((band or {}).get("max"))

    if size_cr is None and shares and upper_price:
        size_cr = round((shares * upper_price) / 10_000_000, 2)
    elif size_cr is None and raw_issue is not None and 0 < raw_issue < 100_000:
        # Historical responses may expose issueSize directly in ₹ crore.
        size_cr = raw_issue

    if size_cr is not None and (size_cr <= 0 or size_cr > 100_000):
        size_cr = None

    return size_cr, shares


def sanitize_issue_size(rec):
    """Remove implausible crore values previously parsed from share counts."""
    value = number(rec.get("issueSizeCr"))
    if value is None:
        return

    if value <= 0 or value > 100_000:
        shares = integer(rec.get("sharesOffered"))
        band = rec.get("priceBand") if isinstance(rec.get("priceBand"), dict) else {}
        upper_price = number((band or {}).get("max"))
        replacement = (
            round((shares * upper_price) / 10_000_000, 2)
            if shares and upper_price
            else None
        )
        rec["issueSizeCr"] = replacement
        nse_obs = (rec.get("observations") or {}).get("NSE")
        if isinstance(nse_obs, dict):
            nse_obs["issueSizeCr"] = replacement


def derive_status(od, cd, ld, hint=None, stage=None):
    today = now_ist().date()
    o = date.fromisoformat(od) if od else None
    c = date.fromisoformat(cd) if cd else None
    l = date.fromisoformat(ld) if ld else None
    if o and today < o:
        return "upcoming"
    if o and c and o <= today <= c:
        return "open"
    if l and today >= l:
        return "listed"
    if c and today > c:
        return "closed"
    h = (hint or "").lower()
    if "open" in h or "active" in h:
        return "open"
    if "list" in h:
        return "listed"
    return "upcoming"


def source_stamp(name, url, kind, as_of=None):
    return {
        "name": name,
        "kind": kind,
        "url": url,
        "asOf": as_of or now_ist().isoformat(timespec="seconds"),
    }


def map_subscription(r):
    out = {
        "qib": number(first(r, "qib", "qualifiedInstitutionalBuyers")),
        "nii": number(first(r, "nii", "hni", "nonInstitutionalInvestors")),
        "retail": number(first(r, "retail", "rii", "retailIndividualInvestors")),
        "total": number(first(r, "noOfTime", "subscription", "timesSubscribed", "totalSubscription")),
    }
    return out if any(v is not None for v in out.values()) else None


def normalize_nse_record(r, kind):
    company = str(
        first(
            r,
            "companyName",
            "company",
            "issuerName",
            "name",
            "symbol",
            default="Unknown IPO",
        )
    ).strip()
    symbol = first(r, "symbol", "nseSymbol", "securitySymbol")
    od = iso_date(first(r, "issueStartDate", "openDate", "issueOpenDate", "biddingStartDate"))
    cd = iso_date(first(r, "issueEndDate", "closeDate", "issueCloseDate", "biddingEndDate"))
    ld = iso_date(first(r, "listingDate", "dateOfListing"))
    board = "SME" if "SME" in str(r).upper() or "EMERGE" in str(r).upper() else "Mainboard"
    src = source_stamp(f"NSE {kind}", NSE_SOURCE_URL, "exchange")
    band = price_band(r)
    lot = integer(first(r, "lotSize", "marketLot", "minimumBidQuantity", "minBidQuantity"))
    size, shares_offered = nse_issue_metrics(r, band)

    return {
        "id": issue_id(slugify(str(symbol or company)), company, od),
        "matchKey": canonical_company(company),
        "symbol": str(symbol).strip() if symbol else None,
        "company": company,
        "board": board,
        "exchange": "NSE" if board == "Mainboard" else "NSE Emerge",
        "status": derive_status(
            od,
            cd,
            ld,
            str(first(r, "status", "issueStatus", default=kind)),
        ),
        "openDate": od,
        "closeDate": cd,
        "allotmentDate": iso_date(first(r, "allotmentDate", "basisOfAllotmentDate")),
        "listingDate": ld,
        "priceBand": band,
        "lotSize": lot,
        "issueSizeCr": size,
        "freshIssueCr": number(first(r, "freshIssue", "freshIssueCr")),
        "ofsCr": number(first(r, "offerForSale", "ofs", "ofsCr")),
        "sharesOffered": shares_offered,
        "sharesBid": integer(first(r, "noOfsharesBid", "sharesBid")),
        "subscription": map_subscription(r),
        "listing": None,
        "lifecycle": {"stage": "exchange", "stageDate": od},
        "documents": [],
        "sources": [src],
        "source": src,
        "observations": {
            "NSE": {
                "openDate": od,
                "closeDate": cd,
                "priceBand": band,
                "lotSize": lot,
                "issueSizeCr": size,
            }
        },
    }


def dedupe_dicts(items, keys):
    out = []
    seen = set()
    for item in items:
        key = tuple(item.get(x) for x in keys)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def merge_non_null(a, b):
    out = dict(a)
    for k, v in b.items():
        if v is not None and v != {} and v != []:
            out[k] = v
    return out


def merge_fill_only(base, incoming, protected=set()):
    out = dict(base)
    for k, v in incoming.items():
        if k in protected:
            continue
        if out.get(k) in (None, "", [], {}) and v not in (None, "", [], {}):
            out[k] = v
    return out


def best_match(records, key):
    if key in records:
        return key
    best = None
    score = 0
    for k in records:
        s = SequenceMatcher(None, key, k).ratio()
        if s > score:
            best, score = k, s
    return best if score >= 0.88 else None


def field_equal(field, a, b):
    if a is None or b is None:
        return None
    if field == "priceBand":
        if not isinstance(a, dict) or not isinstance(b, dict):
            return False
        return all(
            abs(float(a.get(k) or 0) - float(b.get(k) or 0)) <= 0.01
            for k in ("min", "max")
        )
    if field == "issueSizeCr":
        av, bv = number(a), number(b)
        if av is None or bv is None:
            return None
        return abs(av - bv) <= max(0.05, 0.005 * max(abs(av), abs(bv)))
    return a == b


def build_validation(rec):
    obs = rec.get("observations") or {}
    nse = obs.get("NSE") or {}
    bse = obs.get("BSE") or {}
    checks = []
    for f in ("openDate", "closeDate", "priceBand", "lotSize", "issueSizeCr"):
        match = field_equal(f, nse.get(f), bse.get(f))
        if match is not None:
            checks.append(
                {
                    "field": f,
                    "nse": nse.get(f),
                    "bse": bse.get(f),
                    "match": match,
                }
            )
    names = {
        s.get("name", "").split()[0]
        for s in rec.get("sources") or []
        if s.get("name")
    }
    status = (
        "conflict"
        if any(c["match"] is False for c in checks)
        else "verified"
        if len(names) >= 2 and (checks or "SEBI" in names)
        else "single-source"
    )
    return {
        "status": status,
        "checkedAt": now_ist().isoformat(timespec="seconds"),
        "checks": checks,
        "independentSources": sorted(names),
    }


class NSEClient:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(HEADERS)
        self.primed = False

    def get(self, path, params=None):
        if not self.primed:
            self.s.get(NSE_HOME, timeout=20)
            self.primed = True
        r = self.s.get(f"{NSE_API}{path}", params=params, timeout=25)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data
        for k in ("data", "records", "result"):
            if isinstance(data.get(k), list):
                return data[k]
        return []

    def current(self):
        return self.get("/ipo-current-issue")

    def upcoming(self):
        return self.get("/all-upcoming-issues", {"category": "ipo"})

    def past(self, start, end):
        return self.get(
            "/public-past-issues",
            {
                "from_date": start.strftime("%d-%m-%Y"),
                "to_date": end.strftime("%d-%m-%Y"),
            },
        )


class SEBIClient:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(HEADERS)

    def fetch_recent_filings(self, max_pages=4):
        out = []
        for page in range(1, max_pages + 1):
            r = self.s.get(SEBI_URL, params={"page": page}, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select("a[href]"):
                title = " ".join(a.stripped_strings).strip()
                up = title.upper()
                if not title or not any(
                    x in up for x in ("DRHP", "RHP", "PROSPECTUS", "RED HERRING")
                ):
                    continue
                typ = (
                    "UDRHP"
                    if "UDRHP" in up or "UPDATED DRAFT" in up
                    else "DRHP"
                    if "DRHP" in up or "DRAFT" in up
                    else "RHP"
                    if "RHP" in up or "RED HERRING" in up
                    else "PROSPECTUS"
                )
                out.append(
                    {
                        "company": re.sub(
                            r"\s*[-–:]?\s*(UDRHP|DRHP|RHP|RED HERRING PROSPECTUS|PROSPECTUS).*",
                            "",
                            title,
                            flags=re.I,
                        ).strip(),
                        "type": typ,
                        "title": title,
                        "url": urljoin(SEBI_HOME, a.get("href")),
                        "filedDate": iso_date(
                            a.find_parent().get_text(" ", strip=True)
                            if a.find_parent()
                            else ""
                        ),
                    }
                )
            time.sleep(0.15)
        return dedupe_dicts(out, ("url", "type"))


class BSEClient:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(HEADERS)
        self.s.headers.update({"Referer": f"{BSE_HOME}/"})

    @staticmethod
    def parse_html(html, source_url=BSE_URL):
        soup = BeautifulSoup(html, "html.parser")
        rows = []

        for tr in soup.select("tr"):
            cells = [" ".join(c.stripped_strings).strip() for c in tr.select("th,td")]
            if len(cells) < 3:
                continue

            date_cells = [(i, iso_date(cell)) for i, cell in enumerate(cells)]
            date_cells = [(i, d) for i, d in date_cells if d]
            if len(date_cells) < 2:
                od, cd = parse_period(" | ".join(cells))
                if not od or not cd:
                    continue
                date_indexes = []
            else:
                (i1, od), (i2, cd) = date_cells[:2]
                date_indexes = [i1, i2]

            first_date_index = date_indexes[0] if date_indexes else 1
            company_candidates = [c for c in cells[:first_date_index] if c]
            company = company_candidates[0] if company_candidates else cells[0]
            if not company or company.lower() in {
                "company",
                "issuer",
                "security name",
                "security",
            }:
                continue

            band = None
            if len(date_indexes) >= 2:
                end_idx = date_indexes[1]
                if end_idx + 1 < len(cells):
                    candidate = cells[end_idx + 1]
                    if candidate and not iso_date(candidate):
                        band = parse_price_band_text(candidate)

            if band is None:
                for cell in cells:
                    lowered = cell.lower()
                    if (
                        ("₹" in cell or "rs" in lowered or "price" in lowered)
                        and not iso_date(cell)
                    ):
                        p = parse_price_band_text(cell)
                        if p:
                            band = p
                            break

            src = source_stamp("BSE public issue", source_url, "exchange")
            rows.append(
                {
                    "id": slugify(company),
                    "matchKey": canonical_company(company),
                    "company": company,
                    "openDate": od,
                    "closeDate": cd,
                    "priceBand": band,
                    "lotSize": None,
                    "issueSizeCr": None,
                    "sources": [src],
                    "source": src,
                    "observations": {
                        "BSE": {
                            "openDate": od,
                            "closeDate": cd,
                            "priceBand": band,
                            "lotSize": None,
                            "issueSizeCr": None,
                        }
                    },
                }
            )

        return dedupe_dicts(rows, ("matchKey", "openDate", "closeDate"))

    def current_issues(self):
        last_error = None
        for url in BSE_URLS:
            try:
                r = self.s.get(url, timeout=30)
                r.raise_for_status()
                rows = self.parse_html(r.text, source_url=url)
                if rows:
                    return rows
            except Exception as exc:
                last_error = exc

        if last_error:
            raise last_error
        return []


def attach_sebi(records, filings):
    count = 0
    by = {}
    for f in filings:
        by.setdefault(canonical_company(f["company"]), []).append(f)

    rank = {"drhp": 1, "udrhp": 2, "rhp": 3, "prospectus": 4}
    for k, docs in by.items():
        m = best_match(records, k)
        if m is None:
            m = k
            company = docs[0]["company"]
            records[m] = {
                "id": slugify(company),
                "matchKey": k,
                "symbol": None,
                "company": company,
                "board": "Mainboard",
                "exchange": None,
                "status": "upcoming",
                "openDate": None,
                "closeDate": None,
                "listingDate": None,
                "priceBand": None,
                "lotSize": None,
                "issueSizeCr": None,
                "subscription": None,
                "listing": None,
                "documents": [],
                "sources": [],
                "observations": {},
            }

        rec = records[m]
        rec["documents"] = dedupe_dicts(
            (rec.get("documents") or []) + [{**d, "source": "SEBI"} for d in docs],
            ("url", "type"),
        )
        rec["sources"] = dedupe_dicts(
            (rec.get("sources") or [])
            + [
                source_stamp(
                    "SEBI public issues",
                    SEBI_URL,
                    "regulator",
                    d.get("filedDate"),
                )
                for d in docs
            ],
            ("name", "url"),
        )
        latest = max(docs, key=lambda d: rank.get(d["type"].lower(), 0))
        stage = latest["type"].lower()
        rec["lifecycle"] = {
            "stage": stage,
            "stageDate": latest.get("filedDate"),
            "candidate": not bool(rec.get("openDate")),
        }
        rec.setdefault("observations", {})["SEBI"] = {
            "stage": stage,
            "filedDate": latest.get("filedDate"),
            "documentCount": len(rec["documents"]),
        }
        count += 1
    return count


def attach_bse(records, rows):
    count = 0
    protected = {
        "company",
        "openDate",
        "closeDate",
        "listingDate",
        "priceBand",
        "lotSize",
        "issueSizeCr",
    }
    for b in rows:
        k = best_match(records, b["matchKey"])
        if k is None:
            records[b["matchKey"]] = b
            count += 1
            continue
        rec = records[k]
        rec["sources"] = dedupe_dicts(
            (rec.get("sources") or []) + (b.get("sources") or []),
            ("name", "url"),
        )
        rec.setdefault("observations", {}).update(b.get("observations") or {})
        records[k] = merge_fill_only(rec, b, protected)
        count += 1
    return count


def load_existing():
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"ipos": []}


def history_ranges(start, end, days=90):
    cur = start
    while cur <= end:
        stop = min(cur + timedelta(days=days - 1), end)
        yield cur, stop
        cur = stop + timedelta(days=1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--history-days", type=int, default=365)
    p.add_argument("--bootstrap-history", action="store_true")
    p.add_argument("--history-from", default="2000-01-01")
    p.add_argument("--skip-details", action="store_true")
    p.add_argument("--skip-sebi", action="store_true")
    p.add_argument("--skip-bse", action="store_true")
    p.add_argument("--sebi-pages", type=int, default=6)
    a = p.parse_args()

    existing = load_existing()
    records = {}
    errors = []
    health = {}
    fetched = False

    for x in existing.get("ipos", []):
        if isinstance(x, dict):
            k = x.get("matchKey") or canonical_company(str(x.get("company") or ""))
            x["matchKey"] = k
            records[k] = x

    n = NSEClient()
    gathered = []
    try:
        cur = n.current()
        up = n.upcoming()
        gathered += [normalize_nse_record(x, "current") for x in cur]
        gathered += [normalize_nse_record(x, "upcoming") for x in up]
        health["NSE-live"] = {"ok": True, "records": len(cur) + len(up)}
        fetched |= bool(cur or up)
    except Exception as e:
        errors.append(f"NSE live/upcoming: {e}")
        health["NSE-live"] = {"ok": False, "error": str(e)}

    end = now_ist().date()
    start = (
        date.fromisoformat(a.history_from)
        if a.bootstrap_history
        else end - timedelta(days=max(a.history_days, 1))
    )
    hcount = 0
    for s, e in history_ranges(start, end):
        try:
            rows = n.past(s, e)
            hcount += len(rows)
            gathered += [normalize_nse_record(x, "historical") for x in rows]
            fetched |= bool(rows)
            time.sleep(0.2)
        except Exception as ex:
            errors.append(f"NSE history {s}..{e}: {ex}")
            if not a.bootstrap_history:
                break
    health["NSE-history"] = {"ok": hcount > 0, "records": hcount}

    for item in gathered:
        key = item["matchKey"]
        m = best_match(records, key)
        old = records.pop(m) if m and m != key else records.get(key, {})
        merged = merge_non_null(old, item)
        merged["sources"] = dedupe_dicts(
            (old.get("sources") or []) + (item.get("sources") or []),
            ("name", "url"),
        )
        merged["documents"] = dedupe_dicts(
            (old.get("documents") or []) + (item.get("documents") or []),
            ("url", "type"),
        )
        records[key] = merged

    if not a.skip_sebi:
        try:
            filings = SEBIClient().fetch_recent_filings(a.sebi_pages)
            attached = attach_sebi(records, filings)
            health["SEBI"] = {
                "ok": bool(filings),
                "records": len(filings),
                "companiesAttached": attached,
            }
            if not filings:
                errors.append("SEBI filings: no records parsed")
            fetched |= bool(filings)
        except Exception as e:
            errors.append(f"SEBI filings: {e}")
            health["SEBI"] = {"ok": False, "error": str(e)}

    if not a.skip_bse:
        try:
            rows = BSEClient().current_issues()
            attached = attach_bse(records, rows)
            health["BSE"] = {
                "ok": bool(rows),
                "records": len(rows),
                "companiesAttached": attached,
            }
            if not rows:
                errors.append("BSE public issues: no rows parsed")
            fetched |= bool(rows)
        except Exception as e:
            errors.append(f"BSE public issues: {e}")
            health["BSE"] = {"ok": False, "error": str(e)}

    if not fetched and records:
        print("No source refreshed. Existing dataset preserved.", file=sys.stderr)
        return 2
    if not fetched:
        return 2

    for x in records.values():
        sanitize_issue_size(x)
        life = x.get("lifecycle") or {}
        x["status"] = derive_status(
            x.get("openDate"),
            x.get("closeDate"),
            x.get("listingDate"),
            x.get("status"),
            life.get("stage"),
        )
        x["documents"] = dedupe_dicts(x.get("documents") or [], ("url", "type"))
        x["sources"] = dedupe_dicts(
            x.get("sources") or ([x["source"]] if x.get("source") else []),
            ("name", "url"),
        )
        if x["sources"]:
            x["source"] = x["sources"][0]
        x["validation"] = build_validation(x)

    rows = sorted(
        records.values(),
        key=lambda x: (
            x.get("openDate")
            or x.get("listingDate")
            or (x.get("lifecycle") or {}).get("stageDate")
            or "0000-00-00",
            x.get("company") or "",
        ),
        reverse=True,
    )
    out = {
        "meta": {
            "schemaVersion": 2,
            "generatedAt": now_ist().isoformat(timespec="seconds"),
            "timezone": "Asia/Kolkata",
            "sources": ["NSE India", "SEBI", "BSE India"],
            "seed": False,
            "recordCount": len(rows),
            "historyStart": start.isoformat(),
            "sourceHealth": health,
            "errors": errors,
        },
        "ipos": rows,
    }
    DATA_FILE.write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} records to {DATA_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
