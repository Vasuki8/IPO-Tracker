#!/usr/bin/env python3
"""Review one bounded BSE official-universe cohort without mutating canonical data.

The retained archive row is only the candidate list. Every proposed admission
requires an independent BSE detail response whose issuer, Equity security type,
symbol and issue period can be replayed from retained source bytes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse

import requests

import audit_ipo_universe as audit

REVIEW_VERSION = "official-universe-bse-cohort-v1"
ACCEPT = "accept_identity_only"
REVIEW = "possible_duplicate_requires_review"
UNAVAILABLE = "source_unavailable_not_verified"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def slugify_issuer(name: str) -> str:
    value = unicodedata.normalize("NFKD", name)
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    value = re.sub(r"\b(?:limited|ltd)\.?\s*$", "", value).strip()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if not value or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError(f"Cannot derive safe issuer slug: {name!r}")
    return value


def save_response(snapshot: Path, content: bytes) -> tuple[str, str]:
    sha = audit.digest(content)
    path = snapshot / "responses" / f"{sha}.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(gzip.compress(content, mtime=0))
    return sha, path.relative_to(snapshot).as_posix()


def fetch_detail(session: requests.Session, snapshot: Path, row: dict) -> dict:
    url = row["url"]
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"beta.bseindia.com", "www.bseindia.com"}:
        raise ValueError(f"Non-official BSE detail URL: {url}")
    if "displayipo" not in parsed.path.casefold():
        raise ValueError(f"Unexpected BSE detail path: {url}")

    receipt = {
        "recordId": row["recordId"],
        "url": url,
        "registerRow": row,
        "attemptStartedAt": utc_now(),
    }
    try:
        response = session.get(
            url,
            timeout=(10, 35),
            headers={"Referer": row.get("sourceUrl") or "https://www.bseindia.com/"},
        )
        sha, raw_file = save_response(snapshot, response.content)
        receipt.update(
            httpStatus=response.status_code,
            sha256=sha,
            rawFile=raw_file,
            responseUrl=response.url,
            retrievedAt=utc_now(),
            responseDateHeader=response.headers.get("Date"),
        )
        response.raise_for_status()
        identity = audit.bse_identity(response.content)
        receipt["identity"] = identity
        receipt["identityMatchesRegister"] = (
            identity["issuerName"] == row["issuerName"]
            and identity["securityType"] == "Equity"
            and identity["openDate"] == row["issueOpenDate"]
            and identity["closeDate"] == row["issueCloseDate"]
        )
        receipt["status"] = "identity_replayed" if receipt["identityMatchesRegister"] else "identity_mismatch_requires_review"
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        receipt.update(
            status=UNAVAILABLE,
            retrievedAt=receipt.get("retrievedAt") or utc_now(),
            error=str(exc),
        )
    return receipt


def classify_candidate(row: dict, receipt: dict, tracker: list[dict], before: dict, used_ids: set[str]) -> tuple[str, str, list[str], str | None]:
    tracker_symbol_matches = [
        record["id"] for record in tracker
        if str(record.get("symbol") or "").upper()
        and str(record.get("symbol") or "").upper() == str((receipt.get("identity") or {}).get("symbol") or "").upper()
    ]
    receipt["trackerSymbolMatches"] = tracker_symbol_matches

    if receipt.get("status") == UNAVAILABLE:
        return UNAVAILABLE, "Official BSE detail source unavailable or not verifiable in this run", tracker_symbol_matches, None
    if receipt.get("status") != "identity_replayed" or not receipt.get("identityMatchesRegister"):
        return REVIEW, "Archive/detail issuer, Equity type or issue dates do not agree exactly", tracker_symbol_matches, None
    if before.get("classification") in audit.MATCHED:
        return before["classification"], "Current tracker already has a deterministic name/approved-alias match", tracker_symbol_matches, None
    if before.get("classification") != "genuinely_missing":
        return REVIEW, "Current reconciliation does not classify the source record as genuinely missing", tracker_symbol_matches, None
    if row.get("board") not in {"Mainboard", "SME"} or row.get("sourceStatus") != "H":
        return REVIEW, "Historical archive row lacks the required explicit board/status identity", tracker_symbol_matches, None
    if not row.get("issueOpenDate") or not row.get("issueCloseDate"):
        return REVIEW, "Historical archive row lacks an exact issue period", tracker_symbol_matches, None
    if tracker_symbol_matches:
        return REVIEW, "Official BSE symbol already exists in the tracker and requires alias/lifecycle review", tracker_symbol_matches, None

    slug = slugify_issuer(receipt["identity"]["issuerName"])
    tracker_ids = {record["id"] for record in tracker}
    if slug in tracker_ids or slug in used_ids:
        return REVIEW, "Deterministic issuer id collides with an existing/proposed tracker id", tracker_symbol_matches, None
    return ACCEPT, "Exact official archive/detail identity agrees; admit closed issue identity only", tracker_symbol_matches, slug


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-snapshot", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--tracker", type=Path, required=True)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()

    if args.snapshot.exists():
        raise SystemExit("Refusing to replace an existing continuation snapshot")
    audit.fork_snapshot(args.base_snapshot, args.snapshot, args.as_of)

    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    candidates = cohort.get("candidates") or []
    if cohort.get("admissionApproved") is not False or not candidates:
        raise SystemExit("Expected a non-approved, non-empty source-review cohort")

    tracker_bytes = args.tracker.read_bytes()
    tracker_payload = json.loads(tracker_bytes)
    tracker = tracker_payload["ipos"]
    aliases_path = args.snapshot / "aliases.json"
    aliases = json.loads(aliases_path.read_text(encoding="utf-8")) if aliases_path.exists() else []

    manifest, observations, _ = audit.load_observations(args.snapshot)
    reconciled, _ = audit.reconcile(observations, tracker, aliases)
    by_record = {row["recordId"]: row for row in reconciled}

    prior_receipts_path = args.snapshot / "admission-source-receipts.json"
    prior_receipts = json.loads(prior_receipts_path.read_text(encoding="utf-8")) if prior_receipts_path.exists() else []
    prior_ids = {row["recordId"] for row in prior_receipts}

    session = requests.Session()
    session.headers.update(audit.HEADERS)
    reviewed_at = utc_now()
    current_receipts = []
    reviews = []
    admission_records = []
    used_ids: set[str] = set()

    for source_row in candidates:
        record_id = source_row["recordId"]
        if record_id not in by_record:
            raise SystemExit(f"Cohort record absent from inherited official capture: {record_id}")
        row = by_record[record_id]
        # Bind collection to the inherited official archive row rather than trusting
        # a hand-edited next-cohort copy.
        if any(row.get(key) != source_row.get(key) for key in (
            "issuerName", "normalizedName", "url", "issueOpenDate", "issueCloseDate",
            "board", "officialIdentifier", "sourceStatus"
        )):
            raise SystemExit(f"Next-cohort identity drift: {record_id}")

        receipt = fetch_detail(session, args.snapshot, row)
        decision, reason, symbol_matches, slug = classify_candidate(
            row, receipt, tracker, by_record[record_id], used_ids
        )
        receipt.update(
            issuerName=row["issuerName"],
            reviewedAt=reviewed_at,
            reviewVersion=REVIEW_VERSION,
            reviewDecision=decision,
            evidence=reason,
        )
        current_receipts.append(receipt)

        review = {
            "recordId": record_id,
            "issuerName": row["issuerName"],
            "normalizedName": row["normalizedName"],
            "board": row["board"],
            "sourceIssueType": row.get("sourceIssueType"),
            "sourceUrl": row["url"],
            "archiveRetrievedAt": row["retrievedAt"],
            "archiveResponseSha256": row["responseSha256"],
            "detailRetrievedAt": receipt.get("retrievedAt"),
            "detailResponseSha256": receipt.get("sha256"),
            "identity": receipt.get("identity"),
            "trackerSymbolMatches": symbol_matches,
            "classificationBeforeDetail": by_record[record_id]["classification"],
            "decision": decision,
            "reason": reason,
            "proposedId": slug,
        }
        reviews.append(review)
        if decision == ACCEPT:
            admission_records.append({"recordId": record_id, "id": slug})
            used_ids.add(slug)

    if len(current_receipts) != len(candidates):
        raise SystemExit("Did not review every cohort record")
    if prior_ids.intersection({r["recordId"] for r in current_receipts}):
        raise SystemExit("Current detail cohort overlaps a prior retained admission receipt")

    audit.dump(prior_receipts_path, prior_receipts + current_receipts)
    audit.dump(args.snapshot / "admission-review.json", {
        "schemaVersion": 1,
        "reviewVersion": REVIEW_VERSION,
        "reviewedAt": reviewed_at,
        "candidateCount": len(candidates),
        "acceptedCount": len(admission_records),
        "reviewCount": sum(r["decision"] == REVIEW for r in reviews),
        "sourceUnavailableCount": sum(r["decision"] == UNAVAILABLE for r in reviews),
        "records": reviews,
    })
    plan = {
        "schemaVersion": 1,
        "baselineCommit": args.baseline_commit,
        "baselineSha256": audit.digest(tracker_bytes),
        "reviewedAt": reviewed_at,
        "records": admission_records,
    }
    audit.dump(args.snapshot / "admissions.json", plan)
    audit.dump(args.snapshot / "missing-before-admissions.json", [by_record[r["recordId"]] for r in candidates])

    previous_collision = None
    previous_collision_path = args.base_snapshot / "collision-review.json"
    if previous_collision_path.exists():
        previous_collision = json.loads(previous_collision_path.read_text(encoding="utf-8"))
    audit.dump(args.snapshot / "collision-review.json", {
        "inheritedReview": previous_collision,
        "currentCohort": [r for r in reviews if r["decision"] == REVIEW],
        "instruction": "Do not fuzzy-merge. Keep the inherited June/August Dhanwel lifecycle collision separate until explicit official lifecycle evidence resolves it.",
    })

    proposed = audit.prepare_admissions(args.snapshot, args.tracker, plan, aliases)
    if proposed["ipos"][:len(tracker)] != tracker:
        raise SystemExit("Admission proposal altered pre-existing tracker records")
    if len(proposed["ipos"]) != len(tracker) + len(admission_records):
        raise SystemExit("Admission proposal count differs from reviewed acceptances")

    summary = {
        "candidateCount": len(candidates),
        "acceptedCount": len(admission_records),
        "reviewCount": sum(r["decision"] == REVIEW for r in reviews),
        "sourceUnavailableCount": sum(r["decision"] == UNAVAILABLE for r in reviews),
        "acceptedIds": [r["id"] for r in admission_records],
        "reviewRecordIds": [r["recordId"] for r in reviews if r["decision"] == REVIEW],
        "unavailableRecordIds": [r["recordId"] for r in reviews if r["decision"] == UNAVAILABLE],
        "canonicalDataModified": False,
        "baselineCommit": args.baseline_commit,
        "baselineSha256": plan["baselineSha256"],
        "reviewedAt": reviewed_at,
    }
    audit.dump(args.snapshot / "source-review-summary.json", summary)

    rows = "\n".join(
        f"| {r['issuerName']} | {r['board'] or 'unknown'} | {r['identity']['symbol'] if r.get('identity') else '—'} | {r['decision']} |"
        for r in reviews
    )
    report = f"""# BSE June 2026 official-universe source review

This is an identity/lifecycle review only. It continues the released official-universe snapshot without recrawling completed NSE/SEBI/BSE archive cohorts. Canonical `data/ipos.json` is not changed by this stage.

- Base snapshot: `{args.base_snapshot.as_posix()}`
- Baseline commit: `{args.baseline_commit}`
- Candidate records: **{len(candidates)}**
- Unambiguous identity-only admissions proposed: **{len(admission_records)}**
- Possible duplicates/collisions requiring review: **{summary['reviewCount']}**
- Source unavailable / not verified: **{summary['sourceUnavailableCount']}**
- Review version: `{REVIEW_VERSION}`

| Official issuer | Board | BSE symbol | Decision |
|---|---|---|---|
{rows}

Every accepted proposal has an independent retained BSE detail response with exact issuer header, Equity security type, symbol and issue period matching the retained historical archive row. Listing dates and all numerical/financial/offer fields remain unknown unless separately evidenced. No fuzzy merge is performed.

The inherited Dhanwel June/August collision remains unresolved and is not included in these admissions. See `collision-review.json`. The next stage may promote only `accept_identity_only` records after reviewing this evidence; all other decisions remain non-admissions.
"""
    (args.snapshot / "REPORT.md").write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
