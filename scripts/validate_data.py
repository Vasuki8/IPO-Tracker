"""Semantic validation independent of missing-field completeness."""
from __future__ import annotations

import argparse
import copy
import json
import math
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from offer_parser import valid_manager, valid_registrar, PARSER_VERSION
import final_prospectus_identity as final_identity
from final_prospectus_policy import is_final_prospectus
from performance_metrics import refresh_returns
from issue_composition_checks import COMPOSITION_FIELDS, quarantined_fields, record_composition_problems
from objects_of_issue_checks import objects_problems, objects_evidence_problems, objects_quarantined
from source_review_holds import active_hold_reviews

ROOT = Path(__file__).resolve().parents[1]


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_record(record, *, holds=None):
    issues = []
    def add(field, reason, severity="error"):
        issues.append({"id": record.get("id"), "field": field, "severity": severity, "reason": reason})
    provenance = record.get("staticFieldProvenance") or {}
    for reason in objects_problems(record.get("objectsOfIssue")):
        add("objectsOfIssue", reason)
    if record.get("objectsOfIssue") and not objects_problems(record["objectsOfIssue"]):
        proof = provenance.get("objectsOfIssue")
        if not isinstance(proof, dict):
            proof = {}
        if (proof.get("value") != record["objectsOfIssue"] or not proof.get("sourceUrl") or not proof.get("sha256")
                or not is_final_prospectus({"type": proof.get("documentType"), "url": proof.get("sourceUrl")})
                or final_identity.known_non_final_document_url(record, proof.get("sourceUrl"))):
            add("objectsOfIssue", "Allocations need matching values and an identified Final Prospectus source")
        for reason in objects_evidence_problems(record["objectsOfIssue"], proof.get("evidence")):
            add("objectsOfIssue", reason)
    if objects_quarantined(record):
        add("objectsOfIssue", "Objects withheld pending Final Prospectus source-table revalidation", "review")
    claims_verified = any(field in provenance for field in COMPOSITION_FIELDS)
    for field, reason in record_composition_problems(record):
        add(field, reason, "error" if claims_verified else "review")
    if quarantined_fields(record):
        add("issueComposition", "Contradictory issue terms quarantined; Final Prospectus revalidation is still required", "review")
    for field, reason in (record.get('dataReview') or {}).items():
        if not record.get(field):
            add(field, str(reason), 'review')
    if record.get('registrar') and not valid_registrar(record['registrar']):
        add('registrar', 'Invalid intermediary entity: ' + str(record['registrar']))
    for field in (record.get('offerDocumentExtraction') or {}).get('conflicts', []):
        add('financials.' + field, 'Source tables disagree; conflicting metric excluded pending review', 'review')
    if record.get('documentRepair'):
        role_evidence = (record.get('documentFieldProvenance') or {}).get('evidence', {})
        for field in ('leadManagers', 'registrar'):
            if record.get(field) and not role_evidence.get(field):
                add(field, 'Existing disclosure retained; no supported source-role table was extracted', 'review')
    for name in record.get("leadManagers") or []:
        if not valid_manager(name):
            add("leadManagers", "Invalid intermediary entity: " + str(name))
    for field in ("lotSize", "issueSizeCr", "freshIssueCr", "ofsCr"):
        value = record.get(field)
        if value is not None and (not numeric(value) or value < 0):
            add(field, "Expected a finite non-negative number")
    lot = record.get("lotSize")
    if numeric(lot) and (lot <= 0 or lot != int(lot)):
        add("lotSize", "Bid lot must be a positive integer")
    for field in ("lotSize", "listingDate"):
        evidence = record.get(field + "Evidence") or {}
        if evidence and (evidence.get("value") != record.get(field) or not evidence.get("sourceUrl") or evidence.get("issueOpenDate") != record.get("openDate")):
            add(field, "Value does not match the retained issue-specific source evidence")
    band = record.get("priceBand") or {}
    for key in ("min", "max"):
        if band.get(key) is not None and (not numeric(band[key]) or band[key] <= 0):
            add("priceBand." + key, "Price must be a finite positive number")
    if numeric(band.get("min")) and numeric(band.get("max")) and band["min"] > band["max"]:
        add("priceBand", "Floor exceeds cap")
    listing = record.get("listing") or {}
    if listing.get("priceConflicts"):
        add("listing", "Official listing-day prices disagree with retained values; source review required", "review")
    for key in ("issuePrice", "listPrice", "closePrice"):
        value = listing.get(key)
        if value is not None and (not numeric(value) or value <= 0):
            add("listing." + key, "Listing price must be finite and positive")
    final_price = listing.get("issuePrice")
    final_evidence = listing.get("issuePriceEvidence") or {}
    if final_price is not None:
        if not final_evidence:
            add("listing.issuePrice", "Final issue price needs source evidence", "review")
        elif final_evidence.get("value") != final_price or not final_evidence.get("sourceUrl") or final_evidence.get("issueOpenDate") != record.get("openDate"):
            add("listing.issuePrice", "Final issue price does not match its source evidence")
    dates = {}
    for field in ("openDate", "closeDate", "listingDate", "allotmentDate"):
        if record.get(field):
            try:
                dates[field] = date.fromisoformat(str(record[field]))
            except ValueError:
                add(field, "Expected an ISO calendar date")
    if "openDate" in dates and "closeDate" in dates and dates["openDate"] > dates["closeDate"]:
        add("closeDate", "Issue closes before it opens")
    if "listingDate" in dates and "openDate" in dates and dates["listingDate"] < dates["openDate"]:
        add("listingDate", "Listing precedes issue opening")
    performance = record.get("performance") or {}
    latest = performance.get("latest") or {}
    observations = performance.get("observations") or []
    for observation in observations + ([latest] if latest else []):
        if not numeric(observation.get("price")) or observation["price"] <= 0:
            add("performance.observations", "Observed price must be finite and positive")
        try:
            observed = datetime.fromisoformat(str(observation.get("observedAt")))
            if "listingDate" in dates and observed.date() < dates["listingDate"]:
                add("performance.observations", "Price observation precedes this IPO listing")
        except ValueError:
            add("performance.observations", "Price observation needs an ISO source date or timestamp")
        if not observation.get("sourceUrl"):
            add("performance.observations", "Price observation needs source evidence")
    expected = copy.deepcopy(record)
    refresh_returns(expected)
    for section, fields in (("listing", ("gainPct",)), ("performance", ("returnSinceIssuePct", "benchmarkExcessReturnPct"))):
        for field in fields:
            value = (record.get(section) or {}).get(field)
            if value is not None and (not numeric(value) or value != (expected.get(section) or {}).get(field)):
                add(section + "." + field, "Return does not match its source prices and dated baselines")
    financials = record.get("financials") or {}
    evidence = (record.get("documentFieldProvenance") or {}).get("evidence", {}).get("financials", {})
    seen = set()
    for row in financials.get("periods", []):
        period = row.get("period")
        if not isinstance(period, str) or not period.startswith("FY") or not period[2:].isdigit() or period in seen:
            add("financials.periods", "Invalid or duplicate fiscal period")
        seen.add(period)
        for key, value in row.items():
            if key == "period" or value is None:
                continue
            path = str(period) + "." + key
            if not numeric(value):
                add("financials." + path, "Expected a finite numeric metric")
            if path not in evidence:
                add("financials." + path, "Source table/period evidence has not been revalidated", "review")
            elif evidence[path].get('normalizedValue') != value:
                add("financials." + path, "Value does not match the retained source-table evidence")
        nw, ronw = row.get("netWorthCr"), row.get("ronwPct")
        if numeric(nw) and numeric(ronw) and ronw and abs(nw * 10 - ronw) < 1e-8:
            add("financials." + str(period) + ".netWorthCr", "Possible percentage-to-currency extraction contamination; verify source row", "review")
    for key, value in (record.get("subscription") or {}).items():
        if value is not None and (not numeric(value) or value < 0):
            add("subscription." + key, "Subscription multiple must be finite and non-negative")
    # A fresh extraction can repopulate a held field without resolving the
    # underlying source review. Keep those reviews in the queue and phase gate.
    for issue in active_hold_reviews(record, holds):
        if issue not in issues:
            issues.append(issue)
    return issues


def validate_payload(payload):
    rows = payload.get("ipos", [])
    issues = [issue for record in rows for issue in validate_record(record)]
    counts = Counter(record.get("id") for record in rows)
    for key, count in counts.items():
        if not key or count > 1:
            issues.append({"id": key, "field": "id", "severity": "error", "reason": "Missing or duplicate issue identifier"})
    errors = [item for item in issues if item["severity"] == "error"]
    reviews = [item for item in issues if item["severity"] == "review"]
    official, secondary, unknown_time = 0, 0, 0
    for record in rows:
        if record.get("subscription"):
            if "secondary" in str(record.get("subscriptionSource", "")).lower():
                secondary += 1
            elif record.get("subscriptionSource"):
                official += 1
            if not record.get("subscriptionObservedAt"):
                unknown_time += 1
    return {"schemaVersion": 1, "generatedAt": datetime.now(timezone.utc).isoformat(), "parserVersion": PARSER_VERSION, "recordCount": len(rows), "errorCount": len(errors), "reviewCount": len(reviews), "invalidRecordCount": len({item['id'] for item in errors}), "reviewRecordCount": len({item['id'] for item in reviews}), "subscriptionAuthority": {"officialRecords": official, "secondaryRecords": secondary, "sourceTimeUnknown": unknown_time}, "issues": issues}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--strict", action="store_true")
    cli.add_argument("--input", type=Path, default=ROOT / "data/ipos.json")
    cli.add_argument("--output", type=Path, default=ROOT / "data/validation.json")
    args = cli.parse_args()
    report = validate_payload(json.loads(args.input.read_text()))
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "issues"}))
    return int(args.strict and report["errorCount"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
