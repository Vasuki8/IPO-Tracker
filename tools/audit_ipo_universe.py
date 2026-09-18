#!/usr/bin/env python3
"""Read-only official IPO name inventory: resumable capture and offline reconciliation.

This tool never imports a collector/writer or changes canonical data. Register
membership establishes a disclosure/name observation, not final IPO authority.
"""
from __future__ import annotations

import argparse
import collections
import copy
import datetime as dt
import difflib
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import time
import unicodedata
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

VERSION = "official-universe-v1"
ROOT = Path(__file__).resolve().parents[1]
SEBI = "https://www.sebi.gov.in"
SEBI_REGISTERS = {"draft": (10, "Draft Offer Documents filed with SEBI"),
                  "rhp": (11, "Red Herring Documents filed with ROC"),
                  "final_prospectus": (12, "Final Offer Documents filed with ROC"),
                  "other": (78, "Other Documents")}
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json,text/html,*/*"}
MATCHED = {"exact_match", "normalized_match", "known_alias"}


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def normalize_name(value: str) -> str:
    """Only legal Ltd/Limited suffix, case, whitespace, punctuation and &/and.

    Keep PRIVATE/PVT, Corporation, geographical and business words. Compact
    punctuation is useful for initials but every collision remains a review.
    """
    value = unicodedata.normalize("NFKC", value).casefold().replace("&", " and ")
    value = re.sub(r"[\W_]+", " ", value, flags=re.UNICODE).strip()
    value = re.sub(r"\s+(?:limited|ltd)$", "", value)
    return "".join(value.split())


def issuer_from_title(title: str) -> tuple[str, list[str]]:
    """Remove anchored filing annotations, never arbitrary company-name words."""
    value = " ".join(title.split()).strip()
    flags = []
    value = re.sub(r"^(?:addendum(?:\s+[ivx\d]+)?|corrigendum)\s+(?:to\s+)?(?:the\s+)?(?:drhp\s+of\s+)?", "", value, flags=re.I)
    # A legal suffix gives a bounded company span even when repeated abridged
    # links or an old-name parenthesis follow it. Retain the original title too.
    legal = re.search(r"\b(?:limited|ltd\.?)(?=$|\s|[-–—(:,])", value, re.I)
    if legal:
        suffix = value[legal.end():].strip()
        if not suffix or re.match(r"^[-–—:,(]|^(?:DRHP|UDRHP|RHP|prospectus|addendum|corrigendum|formerly)\b", suffix, re.I):
            if re.search(r"formerly|previously|erstwhile", suffix, re.I):
                flags.append("published_rename_requires_alias_review")
            return value[:legal.end()].strip(), flags
    value = re.split(r"\s+[-–—:]\s*(?:draft\b|DRHP\b|UDRHP\b|RHP\b|red herring|prospectus\b|addendum\b|corrigendum\b|abridged\b)", value, maxsplit=1, flags=re.I)[0]
    if not re.search(r"\b(?:limited|ltd\.?)$", value, re.I):
        flags.append("issuer_boundary_requires_review")
    return value.strip(" -–—:"), flags


def date_value(value):
    if value is None:
        return None
    for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%b %d, %Y", "%d %b %Y"):
        try:
            return dt.datetime.strptime(str(value).strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return None


def filing_stage(title, register):
    up = title.upper()
    if re.search(r"WITHDRAWAL OPTION", up):
        return "withdrawal_option_notice"
    if re.search(r"WITHDRAW|CANCEL", up):
        return "withdrawn_or_cancelled_notice"
    if re.search(r"\bUDRHP\b|\bDRHP\b|DRAFT", up):
        return "draft"
    if re.search(r"\bRHP\b|RED HERRING", up):
        return "rhp"
    if "PROSPECTUS" in up and "ABRIDGED" not in up:
        return "final_prospectus"
    return register


def record_base(receipt, index, name, url, **fields):
    return {"recordId": receipt["key"] + ":" + str(index), "cohort": receipt["key"],
            "source": receipt["source"], "issuerName": name,
            "normalizedName": normalize_name(name), "url": url,
            "sourceUrl": receipt["responseUrl"], "retrievedAt": receipt["retrievedAt"],
            "responseSha256": receipt["sha256"], "reportingDate": None,
            "filingDate": None, "issueOpenDate": None, "issueCloseDate": None,
            "listingDate": None, "board": None, "officialIdentifier": None,
            "lifecycleStage": "unknown", "identityFlags": [], "scope": "equity_public_issue_candidate",
            **fields}


def parse_sebi(content: bytes, receipt):
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text(" ", strip=True)
    found = re.search(r"(\d+)\s+to\s+(\d+)\s+of\s+([\d,]+)\s+records", text)
    if not found:
        raise ValueError("SEBI missing explicit pagination denominator")
    start, end, total = (int(x.replace(",", "")) for x in found.groups())
    expected = receipt["page"] * 25 + 1
    if start != expected or end != min(start + 24, total):
        raise ValueError(f"SEBI wrong page/range: {start}-{end}/{total}; requested {expected}")
    rows = []
    for tr in soup.select("table tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) != 2 or not date_value(cells[0].get_text(" ", strip=True)):
            continue
        links = [{"title": a.get_text(" ", strip=True), "url": urljoin(SEBI, a.get("href", ""))}
                 for a in cells[1].select("a[href]") if a.get_text(" ", strip=True)]
        links = [x for x in links if urlparse(x["url"]).hostname == "www.sebi.gov.in"]
        if not links:
            raise ValueError("SEBI dated row has no official link")
        title = links[0]["title"]
        name, flags = issuer_from_title(title)
        scope = "other_public_issue" if re.search(r"\bFPO\b|FOLLOW.ON|RIGHTS ISSUE|\bREIT\b|\bINVIT\b|DEBENTURE", title, re.I) else "equity_public_issue_candidate"
        rows.append(record_base(receipt, start + len(rows), name, links[0]["url"],
            publishedTitle=title, linkedDocuments=links, identityFlags=flags,
            filingDate=date_value(cells[0].get_text(" ", strip=True)),
            lifecycleStage=filing_stage(title, receipt["register"]), register=receipt["register"],
            documentRole="supplemental" if re.search(r"ADDENDUM|CORRIGENDUM|ANNOUNCEMENT|ADVERTISEMENT", title, re.I) else "primary",
            officialIdentifier=(re.search(r"_(\d+)\.html", links[0]["url"]).group(1) if re.search(r"_(\d+)\.html", links[0]["url"]) else None), scope=scope))
    if len(rows) != end - start + 1:
        raise ValueError(f"SEBI row count {len(rows)} differs from displayed range {start}-{end}")
    return rows, {"start": start, "end": end, "reportedTotal": total, "pages": math.ceil(total / 25)}


def parse_nse(content, receipt):
    data = json.loads(content)
    if isinstance(data, dict):
        data = next((data[k] for k in ("data", "records", "result") if isinstance(data.get(k), list)), None)
    if not isinstance(data, list):
        raise ValueError("NSE response lacks a recognized record array")
    rows = []
    for raw in data:
        name = raw.get("companyName") or raw.get("company") or raw.get("issuerName") or raw.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("NSE unnamed source row")
        series = str(raw.get("series") or raw.get("securityType") or "").upper()
        board = "SME" if series == "SME" else "Mainboard" if series == "EQ" else None
        opened = date_value(raw.get("issueStartDate") or raw.get("ipoStartDate") or raw.get("openDate"))
        closed = date_value(raw.get("issueEndDate") or raw.get("ipoEndDate") or raw.get("closeDate"))
        listed = date_value(raw.get("listingDate") or raw.get("dateOfListing"))
        status = str(raw.get("status") or raw.get("issueStatus") or "")
        kind = receipt["register"]
        stage = "completed_issue_listing_unverified" if kind == "historical" else "current"
        if re.search(r"withdraw|cancel", status, re.I):
            stage = "withdrawn_or_cancelled"
        elif listed:
            stage = "listed"
        elif status.casefold() == "closed":
            stage = "closed"
        elif opened and opened > receipt["asOf"]:
            stage = "upcoming"
        elif opened and closed and opened <= receipt["asOf"] <= closed:
            stage = "open"
        category = raw.get("securityType") or raw.get("issueType")
        scope = "other_public_issue" if series in {"IV", "REIT", "INVIT", "NCD", "DEBT", "GB", "N0", "RR"} or re.search(r"\bFPO\b|\bREIT|\bINVIT|DEBT|NCD|RIGHTS|ETF|SGB", str(category or series), re.I) else "equity_public_issue_candidate"
        if series and series not in {"EQ", "SME", "BE"} and scope != "other_public_issue":
            scope = "unclassified_public_issue"
        flags = []
        if kind == "historical" and receipt.get("fromDate"):
            if not any(receipt["fromDate"] <= value <= receipt["toDate"] for value in (opened, closed, listed) if value):
                flags.append("historical_row_outside_requested_dates_or_undated")
        if re.search(r"special withdrawal|re.?bid|extension", name, re.I):
            flags.append("auxiliary_offer_event_requires_review")
        rows.append(record_base(receipt, len(rows) + 1, name, receipt["responseUrl"],
            issueOpenDate=opened, issueCloseDate=closed, listingDate=listed, board=board,
            officialIdentifier=raw.get("symbol"), identifierType="NSE symbol", sourceStatus=status or None,
            category=category, lifecycleStage=stage, scope=scope, identityFlags=flags, rawIdentity={k: raw[k] for k in raw if k.lower() in {
                "companyname", "company", "issuername", "name", "symbol", "series", "securitytype", "issuetype", "status", "issuestatus", "issuestartdate", "issueenddate", "ipostartdate", "ipoenddate", "listingdate", "dateoflisting", "isbse"}}))
    return rows, {"returnedRows": len(rows), "reportedTotal": None,
                  "completeness": "returned cohort only; endpoint supplies no total/history-start guarantee"}


def parse_bse(content, receipt):
    soup = BeautifulSoup(content, "html.parser")
    rows = []
    for tr in soup.select("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 4:
            continue
        # Select leaf data rows, not layout tables containing the entire archive.
        if any(c.find("tr") for c in cells):
            continue
        values = [c.get_text(" ", strip=True) for c in cells]
        dates = [(i, date_value(v)) for i, v in enumerate(values) if date_value(v)]
        if len(dates) < 2:
            continue
        name = values[0]
        link = cells[0].find("a")
        href = str(link.get("href") or "") if link else ""
        if href.lower().startswith("javascript"):
            match = re.search(r"['\"]([^'\"]*(?:IPODisplay|IPO_Display)[^'\"]*)['\"]", href, re.I)
            href = match.group(1) if match else ""
        url = urljoin(receipt["responseUrl"], href) if href else receipt["responseUrl"]
        if urlparse(url).hostname not in {"www.bseindia.com", "beta.bseindia.com"}:
            raise ValueError("BSE nonofficial detail link")
        platform = values[1].casefold()
        board = "SME" if platform == "sme" else "Mainboard" if platform in {"mainboard", "main board"} else None
        query = {k.casefold(): v[0] for k, v in parse_qs(urlparse(url).query).items()}
        opened, closed = dates[0][1], dates[1][1]
        stage = "completed_issue_listing_unverified" if receipt["register"] == "historical" else "current"
        if receipt["register"] != "historical" and opened > receipt["asOf"]:
            stage = "upcoming"
        elif receipt["register"] != "historical" and opened <= receipt["asOf"] <= closed:
            stage = "open"
        issue_type = query.get("type", "").upper()
        scope = "other_public_issue" if issue_type and issue_type not in {"IPO", "FPO"} else "equity_public_issue_candidate"
        rows.append(record_base(receipt, len(rows) + 1, name, url, issueOpenDate=opened,
            issueCloseDate=closed, board=board, category=receipt["issueTypeLabel"],
            officialIdentifier=query.get("scripcd") or query.get("scrip_cd") or query.get("id"),
            identifierType="BSE detail query identifier", lifecycleStage=stage,
            publishedIdentityCells=values[:dates[1][0] + 1], sourceIssueType=issue_type or None,
            sourceStatus=query.get("status"), scope=scope))
    if not rows:
        raise ValueError("BSE no issue rows: form/shell/empty response is not a verified empty universe")
    if re.search(r"Page\$\d+|Page\$Next|Page\$Last", str(soup)):
        raise ValueError("BSE pagination detected; archive incomplete")
    return rows, {"returnedRows": len(rows), "reportedTotal": None,
                  "completeness": "all rows of returned form result; no exchange-wide total supplied"}


PARSERS = {"SEBI": parse_sebi, "NSE": parse_nse, "BSE": parse_bse}


def bse_identity(content):
    """Replay only the physical issuer header and three identity rows."""
    soup = BeautifulSoup(content, "html.parser")
    headers = {x.get_text(" ", strip=True) for x in soup.select("td.TTHeader")}
    values = collections.defaultdict(set)
    for tr in soup.select("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) == 2 and not any(c.find("tr") for c in cells):
            label, value = (c.get_text(" ", strip=True) for c in cells)
            if label in {"Security Type", "Symbol", "Issue Period"}:
                values[label].add(value)
    if len(headers) != 1 or any(len(values[k]) != 1 for k in ("Security Type", "Symbol", "Issue Period")):
        raise ValueError("Ambiguous/incomplete BSE identity rows")
    period = next(iter(values["Issue Period"])).split(" to ")
    if len(period) != 2 or not all(date_value(x) for x in period):
        raise ValueError("Unsupported BSE issue period")
    return {"issuerName": next(iter(headers)), "securityType": next(iter(values["Security Type"])),
            "symbol": next(iter(values["Symbol"])), "openDate": date_value(period[0]), "closeDate": date_value(period[1])}


def read_bound_response(root, receipt):
    content = gzip.decompress((root / receipt["rawFile"]).read_bytes())
    if digest(content) != receipt["sha256"] or receipt.get("httpStatus") != 200:
        raise ValueError("Unverified source response")
    return content


def validate_alias_evidence(root, aliases, tracker):
    by_id = {r["id"]: r for r in tracker}
    receipts = []
    for filename in ("alias-source-receipts.json", "admission-source-receipts.json"):
        path = root / filename
        if path.exists():
            receipts.extend(json.loads(path.read_text(encoding="utf-8")))
    for alias in aliases:
        receipt = next((r for r in receipts if r.get("url") == alias["sourceUrl"] and r.get("sha256") == alias.get("sha256")), None)
        if not receipt:
            raise ValueError("Alias has no retained response binding")
        identity = bse_identity(read_bound_response(root, receipt))
        target = by_id[alias["trackerId"]]
        if identity != alias["sourceIdentity"] or identity["issuerName"] != alias["name"] or identity["securityType"] != "Equity" or any(identity[k] != target.get(k) for k in ("symbol", "openDate", "closeDate")):
            raise ValueError("Alias source/tracker identity mismatch")


def prepare_admissions(root, tracker_path, plan, aliases):
    """Produce a reviewable proposal; no fetching, numerical backfill or writer."""
    raw = tracker_path.read_bytes()
    if digest(raw) != plan["baselineSha256"]:
        raise ValueError("Admission baseline changed")
    manifest, observations, _ = load_observations(root)
    payload = json.loads(raw)
    validate_alias_evidence(root, aliases, payload["ipos"])
    results, _ = reconcile(observations, payload["ipos"], aliases)
    by_record = {r["recordId"]: r for r in results}
    details = {r["recordId"]: r for r in json.loads((root / "admission-source-receipts.json").read_text(encoding="utf-8"))}
    existing_ids = {r["id"] for r in payload["ipos"]}
    existing_symbols = {str(r.get("symbol") or "").upper() for r in payload["ipos"]}
    new_records = []
    seen_sources = set()
    for selection in plan["records"]:
        row = by_record[selection["recordId"]]
        if row["recordId"] in seen_sources or selection["id"] in existing_ids or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", selection["id"]):
            raise ValueError("Duplicate/invalid admission identity")
        if row["classification"] != "genuinely_missing" or row["identityFlags"] or row["scope"] != "equity_public_issue_candidate":
            raise ValueError("Admission requires an unambiguous missing candidate")
        if row["board"] not in {"Mainboard", "SME"} or not row["issueOpenDate"] or not row["issueCloseDate"]:
            raise ValueError("Admission lacks official board/issue identity")
        if row["source"] == "BSE":
            receipt = details[row["recordId"]]
            proof = bse_identity(read_bound_response(root, receipt))
            if receipt["url"] != row["url"] or proof["issuerName"] != row["issuerName"] or proof["securityType"] != "Equity" or proof["openDate"] != row["issueOpenDate"] or proof["closeDate"] != row["issueCloseDate"]:
                raise ValueError("BSE detail and register identity disagree")
            if row.get("sourceStatus") != "H" or row["issueCloseDate"] > manifest["asOf"]:
                raise ValueError("This admission batch requires an officially historical closed issue")
            symbol, status = proof["symbol"], "closed"
            evidence_receipt = {k: receipt[k] for k in ("url", "retrievedAt", "sha256", "rawFile")}
        elif row["source"] == "NSE":
            if row["lifecycleStage"] != "listed" or not row["listingDate"] or row["listingDate"] > manifest["asOf"]:
                raise ValueError("NSE admission requires an explicit historical listing date")
            symbol, status = row["officialIdentifier"], "listed"
            evidence_receipt = {"url": row["url"], "retrievedAt": row["retrievedAt"], "sha256": row["responseSha256"]}
        else:
            raise ValueError("Draft/filing-only admissions require a separate reviewed batch")
        if not symbol or symbol.upper() in existing_symbols:
            raise ValueError("Symbol already exists; review possible alias before adding")
        source = {"name": row["source"] + " official issue identity", "url": row["url"], "kind": "exchange", "asOf": row["retrievedAt"]}
        record = {"id": selection["id"], "company": row["issuerName"], "symbol": symbol,
            "board": row["board"], "exchange": row["source"] + (" SME" if row["board"] == "SME" and row["source"] == "BSE" else " Emerge" if row["board"] == "SME" else ""),
            "status": status, "openDate": row["issueOpenDate"], "closeDate": row["issueCloseDate"], "listingDate": row["listingDate"],
            "lifecycle": {"stage": "exchange", "stageDate": row["issueOpenDate"]}, "documents": [], "sources": [source], "source": source,
            "observations": {row["source"]: {"company": row["issuerName"], "symbol": symbol,
                "openDate": row["issueOpenDate"], "closeDate": row["issueCloseDate"], "listingDate": row["listingDate"],
                "observedAt": None, "collectedAt": row["retrievedAt"], "timeBasis": "collection_only", "sourceUrl": row["url"]}},
            "universeAdmission": {"reviewVersion": "official-universe-admission-v1", "reviewedAt": plan["reviewedAt"],
                "recordId": row["recordId"], "registerResponseSha256": row["responseSha256"], "identitySource": evidence_receipt,
                "scope": "Issuer, board and exchange lifecycle only; no static terms, financials or subscription accepted"}}
        for field in ("priceBand", "lotSize", "marketLot", "minimumBidQuantity", "minimumApplicationAmount", "issueSizeCr", "freshIssueCr", "ofsCr", "issueComposition", "financials", "subscription", "listing", "allotmentDate", "leadManagers", "registrar", "promoters", "objectsOfIssue", "shareholding"):
            record[field] = None
        if record["listingDate"]:
            record["listingDateEvidence"] = {"value": record["listingDate"], "sourceUrl": row["url"],
                "issueOpenDate": record["openDate"], "company": record["company"], "symbol": symbol,
                "sha256": row["responseSha256"], "collectedAt": row["retrievedAt"], "observedAt": None}
        existing_ids.add(record["id"])
        existing_symbols.add(symbol.upper())
        seen_sources.add(row["recordId"])
        new_records.append(record)
    proposed = copy.deepcopy(payload)
    proposed["ipos"].extend(new_records)
    proposed.setdefault("meta", {})["recordCount"] = len(proposed["ipos"])
    proposed["meta"]["generatedAt"] = plan["reviewedAt"]
    return proposed


class Capture:
    def __init__(self, root, as_of, max_new=500, retry_failed=False):
        self.root, self.as_of, self.max_new, self.retry_failed = root, as_of, max_new, retry_failed
        self.path = root / "capture.json"
        self.manifest = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {
            "schemaVersion": 1, "toolVersion": VERSION, "asOf": as_of, "cohorts": {}, "accessAttempts": []}
        if self.manifest["asOf"] != as_of:
            raise ValueError("Use a new snapshot directory for a different as-of date")
        self.count = 0
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def save(self):
        dump(self.path, self.manifest)

    def fetch(self, key, source, url, *, data=None, **meta):
        old = self.manifest["cohorts"].get(key)
        if old and (old["status"] == "verified_response" or not self.retry_failed):
            return old
        if self.count >= self.max_new:
            return None
        self.count += 1
        receipt = {"key": key, "source": source, "requestUrl": url, "method": "POST" if data else "GET",
                   "requestFields": data, "asOf": self.as_of, **meta}
        try:
            response = self.session.request(receipt["method"], url, data=data, timeout=(10, 35), headers={"Referer": url})
            receipt.update(responseUrl=response.url, httpStatus=response.status_code,
                retrievedAt=dt.datetime.now(dt.timezone.utc).isoformat(), responseDateHeader=response.headers.get("Date"),
                sha256=digest(response.content), bytes=len(response.content))
            raw_path = self.root / "responses" / (receipt["sha256"] + ".gz")
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            if not raw_path.exists():
                raw_path.write_bytes(gzip.compress(response.content, mtime=0))
            receipt["rawFile"] = raw_path.relative_to(self.root).as_posix()
            response.raise_for_status()
            rows, bounds = PARSERS[source](response.content, receipt)
            receipt.update(status="verified_response", records=len(rows), bounds=bounds)
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            receipt.update(status="source_unavailable_not_verified", error=str(exc),
                retrievedAt=receipt.get("retrievedAt") or dt.datetime.now(dt.timezone.utc).isoformat())
        if old:
            self.manifest["accessAttempts"].append(old)
        self.manifest["cohorts"][key] = receipt
        self.save()
        print(key, receipt["status"], receipt.get("records", receipt.get("error")), flush=True)
        time.sleep(.25)
        return receipt

    def sebi(self):
        for register, (smid, label) in SEBI_REGISTERS.items():
            url = SEBI + "/sebiweb/home/HomeAction.do?" + urlencode({"doListing": "yes", "sid": 3, "smid": smid, "ssid": 15})
            first = self.fetch(f"SEBI-{register}-0000", "SEBI", url, register=register, page=0)
            if not first or first["status"] != "verified_response":
                continue
            for page in range(1, first["bounds"]["pages"]):
                fields = {"nextValue": str(page), "next": "n", "search": "", "fromDate": "", "toDate": "",
                    "fromYear": "", "toYear": "", "deptId": "-1", "sid": "3", "ssid": "15", "smid": str(smid),
                    "ssidhidden": "15", "intmid": "-1", "sText": "Filings", "ssText": "Public Issues", "smText": label, "doDirect": str(page)}
                self.fetch(f"SEBI-{register}-{page:04}", "SEBI", SEBI + "/sebiweb/ajax/home/getnewslistinfo.jsp", data=fields, register=register, page=page)
                if self.count >= self.max_new:
                    break

    def nse(self, start_year, period="year"):
        # Public cookie priming only. Failures never replace a known response.
        try:
            self.session.get("https://www.nseindia.com", timeout=(10, 20))
        except requests.RequestException:
            pass
        for kind, path in (("current", "ipo-current-issue"), ("upcoming", "all-upcoming-issues?category=ipo")):
            self.fetch("NSE-" + kind, "NSE", "https://www.nseindia.com/api/" + path, register=kind)
        end_date = dt.date.fromisoformat(self.as_of)
        for year in range(end_date.year, start_year - 1, -1):
            for quarter, month in enumerate((1,) if period == "year" else (1, 4, 7, 10), 1):
                start = dt.date(year, month, 1)
                end = dt.date(year + 1, 1, 1) - dt.timedelta(days=1) if month == 10 or period == "year" else dt.date(year, month + 3, 1) - dt.timedelta(days=1)
                if start > end_date:
                    continue
                end = min(end, end_date)
                url = "https://www.nseindia.com/api/public-past-issues?" + urlencode({"from_date": start.strftime("%d-%m-%Y"), "to_date": end.strftime("%d-%m-%Y")})
                key = f"NSE-{year}" if period == "year" else f"NSE-{year}-Q{quarter}"
                self.fetch(key, "NSE", url, register="historical", fromDate=start.isoformat(), toDate=end.isoformat())
                if self.count >= self.max_new:
                    return

    def bse(self):
        for host in ("www", "beta"):
            for register, pageid in (("current", 1), ("historical", 2)):
                url = f"https://{host}.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id={pageid}&Type=P"
                first = self.fetch(f"BSE-{host}-{register}-get", "BSE", url, register=register, issueTypeLabel="unfiltered form")
                if not first or "rawFile" not in first or first.get("httpStatus") != 200:
                    continue
                raw = gzip.decompress((self.root / first["rawFile"]).read_bytes())
                # BSE repeats name= on controls. HTML/browser semantics retain
                # the first ASP.NET name, not the trailing display alias.
                soup = BeautifulSoup(raw, "html.parser", on_duplicate_attribute="ignore")
                selector = next((s for s in soup.select("select[name]") if any("Public Issue-Book Building" in o.get_text() for o in s.select("option"))), None)
                if selector is None:
                    continue
                for option in selector.select("option"):
                    label = option.get_text(" ", strip=True)
                    if label not in {"Public Issue-Book Building", "Public Issue-Fixed Price"}:
                        continue
                    fields = {i["name"]: i.get("value", "") for i in soup.select("input[type=hidden][name]")}
                    fields[selector["name"]] = option["value"]
                    submit = soup.select_one("input[type=submit][name]")
                    if submit:
                        fields[submit["name"]] = submit.get("value", "Submit")
                    self.fetch(f"BSE-{host}-{register}-{option['value']}", "BSE", url, data=fields, register=register, issueTypeLabel=label)


def load_observations(root):
    manifest = json.loads((root / "capture.json").read_text(encoding="utf-8"))
    records, gaps = [], []
    for receipt in manifest["cohorts"].values():
        if receipt["status"] != "verified_response":
            gaps.append({k: receipt.get(k) for k in ("key", "source", "requestUrl", "responseUrl", "retrievedAt", "httpStatus", "error")})
            continue
        content = gzip.decompress((root / receipt["rawFile"]).read_bytes())
        if digest(content) != receipt["sha256"]:
            raise ValueError("Source response digest mismatch: " + receipt["key"])
        rows, bounds = PARSERS[receipt["source"]](content, receipt)
        if len(rows) != receipt["records"] or bounds != receipt["bounds"]:
            raise ValueError("Replay differs from retained capture: " + receipt["key"])
        records.extend(rows)
    return manifest, records, gaps


def reconcile(records, tracker, aliases):
    by_key = collections.defaultdict(list)
    by_symbol = collections.defaultdict(list)
    by_document = collections.defaultdict(list)
    by_id = {r["id"]: r for r in tracker}
    if len(by_id) != len(tracker):
        raise ValueError("Duplicate tracker IDs")
    for row in tracker:
        by_key[normalize_name(row["company"])].append(row)
        if row.get("symbol"):
            by_symbol[str(row["symbol"]).upper()].append(row)
        for document in row.get("documents", []):
            if document.get("url"):
                by_document[document["url"]].append(row)
    alias_map = {}
    for alias in aliases:
        if alias.get("trackerId") not in by_id or urlparse(alias.get("sourceUrl", "")).hostname not in {
                "www.sebi.gov.in", "www.nseindia.com", "nsearchives.nseindia.com", "www.bseindia.com", "beta.bseindia.com"} or not alias.get("evidence"):
            raise ValueError("Alias lacks tracker/source evidence")
        key = normalize_name(alias["name"])
        if key in alias_map:
            raise ValueError("Ambiguous alias key")
        alias_map[key] = alias
    matched_ids, results = set(), []
    for row in records:
        key = row["normalizedName"]
        candidates = by_key.get(key, [])
        classification, reason = "genuinely_missing", "No deterministic tracker name/alias match in this snapshot"
        if candidates:
            classification = "exact_match" if len(candidates) == 1 and candidates[0]["company"] == row["issuerName"] else "normalized_match"
        elif key in alias_map:
            candidates = [by_id[alias_map[key]["trackerId"]]]
            classification, reason = "known_alias", alias_map[key]["evidence"]
        if candidates:
            if len(candidates) > 1:
                classification, reason = "possible_duplicate_requires_review", "Multiple tracker records share this normalized name"
            else:
                candidate = candidates[0]
                if row.get("board") and candidate.get("board") and row["board"] != candidate["board"]:
                    classification, reason = "possible_duplicate_requires_review", "Source/tracker board disagreement; migration/identity needs evidence"
                elif row.get("issueOpenDate") and candidate.get("openDate") and row["issueOpenDate"] != candidate["openDate"]:
                    classification, reason = "possible_duplicate_requires_review", "Different issue dates; name coverage does not identify this offer"
                elif row["source"] == "NSE" and row.get("officialIdentifier") and candidate.get("symbol") and str(row["officialIdentifier"]).upper() != str(candidate["symbol"]).upper():
                    classification, reason = "possible_duplicate_requires_review", "Name matches but official/tracker symbols disagree"
                elif classification != "known_alias":
                    reason = "Unique compatible issuer name; does not establish numerical or filing coverage"
        if not candidates:
            identified = by_symbol.get(str(row.get("officialIdentifier") or "").upper(), []) if row["source"] == "NSE" else by_document.get(row["url"], []) if row["source"] == "SEBI" else []
            if identified:
                candidates = list({r["id"]: r for r in identified}.values())
                classification, reason = "possible_duplicate_requires_review", "Official symbol or retained filing links a differently named tracker issuer; alias/identity review required"
        if not candidates:
            # Suggestions can only create a review, never a match or canonical edit.
            close_keys = difflib.get_close_matches(key, [k for k in by_key if k[:2] == key[:2]], n=3, cutoff=.9)
            if close_keys:
                candidates = [r for k in close_keys for r in by_key[k]]
                classification, reason = "possible_duplicate_requires_review", "Similar name candidates only; no fuzzy merge accepted"
        if row.get("identityFlags") and classification == "genuinely_missing":
            classification, reason = "source_unavailable_not_verified", "Issuer boundary/rename requires manual document review"
        if classification in MATCHED:
            matched_ids.update(r["id"] for r in candidates)
        results.append({**row, "classification": classification, "matchReason": reason,
            "trackerIds": [r["id"] for r in candidates],
            "filingLinkedInTracker": any(row["url"] == d.get("url") for r in candidates for d in r.get("documents", [])) if row["source"] == "SEBI" and classification in MATCHED else None})
    tracker_only = [{"trackerId": r["id"], "issuerName": r["company"], "board": r.get("board"),
        "classification": "tracker_only", "meaning": "Not safely matched in the captured cohorts; not proof of invalidity"}
        for r in tracker if r["id"] not in matched_ids]
    return results, tracker_only


def summarize(rows, fields):
    groups = collections.defaultdict(list)
    for row in rows:
        values = tuple(row.get(f) or "unknown" for f in fields)
        groups[values].append(row)
    return [{**dict(zip(fields, key)), "sourceRecords": len(group),
             "uniqueNormalizedNames": len({r["normalizedName"] for r in group}),
             "distinctSourceRecords": len({source_identity(r) for r in group}),
             "matchedRecords": sum(r["classification"] in MATCHED for r in group),
             "classifications": dict(sorted(collections.Counter(r["classification"] for r in group).items()))}
            for key, group in sorted(groups.items())]


def source_identity(row):
    """Deduplicate observations only for reporting; every source row survives."""
    if row["source"] == "SEBI":
        return (row["source"], row["url"])
    return (row["source"], row["officialIdentifier"], row["normalizedName"], row["board"], row["issueOpenDate"], row["issueCloseDate"])


def build(root, tracker_path, aliases_path, report_dir=None):
    report_dir = report_dir or root
    report_dir.mkdir(parents=True, exist_ok=True)
    manifest, rows, gaps = load_observations(root)
    tracker_bytes = tracker_path.read_bytes()
    aliases = json.loads(aliases_path.read_text(encoding="utf-8")) if aliases_path else []
    validate_alias_evidence(root, aliases, json.loads(tracker_bytes)["ipos"])
    results, tracker_only = reconcile(rows, json.loads(tracker_bytes)["ipos"], aliases)
    for row in results:
        row["periodYear"] = (row.get("filingDate") or row.get("issueOpenDate") or "unknown")[:4]
    progress = []
    for register in SEBI_REGISTERS:
        cohorts = [c for c in manifest["cohorts"].values() if c["source"] == "SEBI" and c["register"] == register and c["status"] == "verified_response"]
        first = next((c for c in cohorts if c["page"] == 0), None)
        total = first["bounds"]["reportedTotal"] if first else None
        expected = set(range(first["bounds"]["pages"])) if first else set()
        missing = sorted(expected - {c["page"] for c in cohorts})
        same_total = bool(first) and all(c["bounds"]["reportedTotal"] == total for c in cohorts)
        register_rows = [r for r in results if r["source"] == "SEBI" and r["register"] == register]
        urls = [r["url"] for r in register_rows]
        duplicate_urls = len(urls) - len(set(urls))
        progress.append({"register": register, "reportedRows": total, "capturedRows": len(urls),
            "verifiedPages": len(cohorts), "missingPages": missing, "duplicatePrimaryUrls": duplicate_urls,
            "completeRegisterTraversal": bool(first) and same_total and not missing and len(urls) == total and duplicate_urls == 0})
    duplicates = []
    by_identity = collections.defaultdict(list)
    for row in results:
        by_identity[(row["source"], row["normalizedName"])].append(row)
    for (source, name), group in sorted(by_identity.items()):
        if len(group) > 1:
            duplicates.append({"source": source, "normalizedName": name, "recordIds": [r["recordId"] for r in group],
                "stages": sorted({r["lifecycleStage"] for r in group}), "boards": sorted({r["board"] or "unknown" for r in group}),
                "meaning": "Repeated name observations retained; filings/offers not merged"})
    report = {"schemaVersion": 1, "toolVersion": VERSION, "asOf": manifest["asOf"],
        "trackerSha256": digest(tracker_bytes), "trackerRecords": len(json.loads(tracker_bytes)["ipos"]),
        "globalCompleteness": False, "recordsAdded": sum((r.get("universeAdmission") or {}).get("recordId") in {x["recordId"] for x in rows} for r in json.loads(tracker_bytes)["ipos"]),
        "denominatorMeaning": "Official source rows, not unique IPOs. Name matches do not verify terms, board, current lifecycle or all historical offers.",
        "bySource": summarize(results, ["source"]), "bySourcePeriodBoardStage": summarize(results, ["source", "periodYear", "board", "lifecycleStage"]),
        "byScope": summarize(results, ["source", "scope"]), "sebiTraversal": progress,
        "sourceAccessGaps": gaps, "repeatedNameGroups": duplicates, "trackerOnly": tracker_only}
    report["auxiliaryAccessAttempts"] = manifest.get("accessAttempts", [])
    eligible = [r for r in results if r["scope"] == "equity_public_issue_candidate"]
    distinct = {}
    for row in eligible:
        key = source_identity(row)
        old = distinct.get(key)
        # Do not improve coverage by selecting the successful side of a disagreement.
        if old is None or old["classification"] in MATCHED and row["classification"] not in MATCHED:
            distinct[key] = row
    report["eligibleDistinctBySource"] = summarize(list(distinct.values()), ["source"])
    report["eligibleDistinctBySourcePeriodBoardStage"] = summarize(list(distinct.values()), ["source", "periodYear", "board", "lifecycleStage"])
    report["historicalDateRangeIssues"] = [r["recordId"] for r in results if "historical_row_outside_requested_dates_or_undated" in r["identityFlags"]]
    missing_names = collections.defaultdict(list)
    for row in eligible:
        if row["classification"] == "genuinely_missing":
            missing_names[row["normalizedName"]].append(row)
    missing_issuers = [{"normalizedName": key, "publishedNames": sorted({r["issuerName"] for r in group}),
        "sources": sorted({r["source"] for r in group}), "stages": sorted({r["lifecycleStage"] for r in group}),
        "recordIds": [r["recordId"] for r in group],
        "admission": "Identity review required before canonical addition; public-issue registers may include follow-on offers"}
        for key, group in sorted(missing_names.items())]
    report["missingCandidateNames"] = len(missing_issuers)
    report["acceptedAliases"] = aliases
    report["sourceDateRanges"] = [{"source": source,
        "earliestRecordDate": min((r.get("filingDate") or r.get("issueOpenDate")) for r in results if r["source"] == source and (r.get("filingDate") or r.get("issueOpenDate"))),
        "latestRecordDate": max((r.get("filingDate") or r.get("issueOpenDate")) for r in results if r["source"] == source and (r.get("filingDate") or r.get("issueOpenDate")))}
        for source in sorted({r["source"] for r in results}) if any(r["source"] == source and (r.get("filingDate") or r.get("issueOpenDate")) for r in results)]
    dump(report_dir / "missing-issuers.json", missing_issuers)
    dump(report_dir / "audit.json", report)
    for name, selected in (("records.jsonl", results), ("missing.jsonl", [r for r in results if r["classification"] == "genuinely_missing"]),
                           ("identity-review.jsonl", [r for r in results if r["classification"] in {"possible_duplicate_requires_review", "source_unavailable_not_verified"}])):
        (report_dir / name).write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in selected), encoding="utf-8", newline="\n")
    print(json.dumps({"bySource": report["bySource"], "sebiTraversal": progress, "gaps": len(gaps), "trackerOnly": len(tracker_only)}, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("collect", "reconcile", "prepare-admissions"))
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--as-of", default=dt.date.today().isoformat())
    parser.add_argument("--sources", default="NSE,BSE,SEBI")
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--nse-period", choices=("year", "quarter"), default="year")
    parser.add_argument("--max-new-cohorts", type=int, default=500)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--tracker", type=Path, default=ROOT / "data/ipos.json")
    parser.add_argument("--aliases", type=Path)
    parser.add_argument("--admissions", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args()
    if args.command == "prepare-admissions":
        if not args.admissions or not args.output or args.output.resolve() == (ROOT / "data/ipos.json").resolve():
            parser.error("Explicit --admissions and a separate proposal --output are required")
        plan = json.loads(args.admissions.read_text(encoding="utf-8"))
        aliases = json.loads(args.aliases.read_text(encoding="utf-8")) if args.aliases else []
        dump(args.output, prepare_admissions(args.snapshot, args.tracker, plan, aliases))
    elif args.command == "reconcile":
        build(args.snapshot, args.tracker, args.aliases, args.report_dir)
    else:
        capture = Capture(args.snapshot, args.as_of, args.max_new_cohorts, args.retry_failed)
        for source in args.sources.split(","):
            if source == "NSE":
                capture.nse(args.start_year, args.nse_period)
            elif source == "BSE":
                capture.bse()
            elif source == "SEBI":
                capture.sebi()
            else:
                raise ValueError("Unknown source " + source)


if __name__ == "__main__":
    main()
