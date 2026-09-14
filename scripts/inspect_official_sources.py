"""Bounded diagnostics for the NSE issuer-document integration."""
from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import update_data as core

PAGE = "https://www.nseindia.com/companies-listing/corporate-filings-offer-documents"


def main():
    session = requests.Session()
    session.headers.update(core.HEADERS)
    response = session.get(PAGE, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    scripts = list(dict.fromkeys(urljoin(PAGE, node["src"]) for node in soup.select("script[src]")))
    candidates = [url for url in scripts if urlparse(url).hostname == "www.nseindia.com" and re.search(r"offer|corporate|issuer", url, re.I)]
    report = {"page": PAGE, "scripts": scripts, "integrationScripts": []}
    for url in candidates[:5]:
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            content = response.text[:2_000_000]
            routes = sorted({route for route in re.findall(r"/api/[A-Za-z0-9_/?=&.-]+", content) if "offer" in route.lower()})
            contexts = []
            for match in re.finditer(r"offer-documents\?|offer-documents-abridged|offerdocs/equity/companylist|offerdocs/sme/companylist|pan_no|marketLot|finalIssuePrice", content, re.I):
                contexts.append(content[max(0, match.start() - 200):match.end() + 300])
                if len(contexts) >= 24:
                    break
            report["integrationScripts"].append({"url": url, "apiRoutes": routes, "contexts": contexts})
        except Exception as exc:
            report["integrationScripts"].append({"url": url, "error": str(exc)[:250]})
    report["companyLists"] = []
    for route in ("/api/corporates/offerdocs/equity/companylist", "/api/corporates/offerdocs/sme/companylist", "/api/corporates/offerdocs/companylist"):
        url = "https://www.nseindia.com" + route
        try:
            response = session.get(url, timeout=30, headers={"Referer": PAGE})
            response.raise_for_status()
            payload = response.json()
            records = payload if isinstance(payload, list) else payload.get("data", [])
            matches = [row for row in records if re.search(r"ANB Metal|Aaradhya Disposal|National Securities Depository|Acetech", json.dumps(row), re.I)]
            report["companyLists"].append({"url": url, "keys": list(payload)[:10] if isinstance(payload, dict) else None, "count": len(records), "samples": records[:2], "matches": matches[:10]})
        except Exception as exc:
            report["companyLists"].append({"url": url, "error": str(exc)[:250]})
    print("OFFICIAL_SOURCE_DIAGNOSTIC " + json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
