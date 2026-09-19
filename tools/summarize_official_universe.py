#!/usr/bin/env python3
"""Write compact, resumable coverage outputs from an official-universe audit."""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def pct(numerator: int, denominator: int) -> float:
    return round(numerator / denominator * 100, 2) if denominator else 0.0


def compact_group(row: dict) -> dict:
    denominator = int(row.get("sourceRecords") or 0)
    matched = int(row.get("matchedRecords") or 0)
    classifications = row.get("classifications") or {}
    return {
        **{key: row[key] for key in ("source", "periodYear", "board", "lifecycleStage") if key in row},
        "denominator": denominator,
        "matched": matched,
        "matchRatePct": pct(matched, denominator),
        "exactMatch": int(classifications.get("exact_match") or 0),
        "normalizedMatch": int(classifications.get("normalized_match") or 0),
        "knownAlias": int(classifications.get("known_alias") or 0),
        "possibleDuplicateReview": int(classifications.get("possible_duplicate_requires_review") or 0),
        "genuinelyMissing": int(classifications.get("genuinely_missing") or 0),
        "sourceUnavailableNotVerified": int(classifications.get("source_unavailable_not_verified") or 0),
    }


def next_bse_cohort(missing_path: Path, current_review: dict, limit: int) -> dict:
    current_dates = [
        row.get("identity", {}).get("openDate")
        for row in current_review.get("records") or []
        if row.get("identity", {}).get("openDate")
    ]
    if not current_dates:
        raise ValueError("Current review has no issue-open dates")
    before = min(current_dates)
    rows = []
    for raw in missing_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        if (
            row.get("source") == "BSE"
            and row.get("classification") == "genuinely_missing"
            and row.get("scope") == "equity_public_issue_candidate"
            and row.get("board") in {"Mainboard", "SME"}
            and row.get("issueOpenDate")
            and row["issueOpenDate"] < before
            and row.get("url")
        ):
            rows.append(row)
    if not rows:
        return {"schemaVersion": 1, "source": "BSE", "admissionApproved": False,
                "selection": {"beforeIssueOpenDate": before, "limit": limit},
                "candidateCount": 0, "candidates": []}
    rows.sort(key=lambda row: (row["issueOpenDate"], row.get("issueCloseDate") or "", row.get("recordId") or ""), reverse=True)
    month = rows[0]["issueOpenDate"][:7]
    month_rows = [row for row in rows if row["issueOpenDate"].startswith(month)]
    selected = month_rows[:limit]
    keep = ("recordId","source","issuerName","normalizedName","url","sourceUrl","retrievedAt","responseSha256",
            "issueOpenDate","issueCloseDate","listingDate","board","officialIdentifier","lifecycleStage","category",
            "identifierType","sourceIssueType","sourceStatus","classification","matchReason","trackerIds","periodYear")
    return {
        "schemaVersion": 1,
        "source": "BSE",
        "purpose": "Next bounded identity/source-review cohort; no automatic admission",
        "admissionApproved": False,
        "selection": {"periodMonth": month, "beforeIssueOpenDate": before, "limit": limit,
                      "eligibleInMonth": len(month_rows),
                      "remainingInMonthAfterThisCohort": max(0, len(month_rows)-len(selected))},
        "candidateCount": len(selected),
        "candidates": [{key: row.get(key) for key in keep} for row in selected],
    }


def report_markdown(summary: dict) -> str:
    lines = [
        "# Official IPO-universe coverage — continuation checkpoint", "",
        f"Generated from retained official-source evidence as of **{summary['asOf']}**. "
        "Coverage remains bounded by the source-access ranges below; this is not a claim of complete all-time NSE/BSE/SEBI coverage.",
        "", "## Source denominators", "",
        "| Source | Candidate denominator | Matched | Match rate | Exact | Normalized | Alias | Duplicate review | Missing | Unverified |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["bySource"]:
        lines.append(
            f"| {row['source']} | {row['denominator']} | {row['matched']} | {row['matchRatePct']:.2f}% | "
            f"{row['exactMatch']} | {row['normalizedMatch']} | {row['knownAlias']} | "
            f"{row['possibleDuplicateReview']} | {row['genuinelyMissing']} | {row['sourceUnavailableNotVerified']} |"
        )
    lines += ["", "## Exact period / board / lifecycle denominators", "",
              "| Source | Year | Board | Lifecycle stage | Denominator | Matched | Match rate | Missing | Duplicate review | Unverified |",
              "|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in summary["bySourcePeriodBoardStage"]:
        lines.append(
            f"| {row['source']} | {row.get('periodYear','unknown')} | {row.get('board','unknown')} | "
            f"{row.get('lifecycleStage','unknown')} | {row['denominator']} | {row['matched']} | "
            f"{row['matchRatePct']:.2f}% | {row['genuinelyMissing']} | {row['possibleDuplicateReview']} | "
            f"{row['sourceUnavailableNotVerified']} |"
        )
    lines += ["", "## Source-access bounds", ""]
    for row in summary["sourceDateRanges"]:
        lines.append(f"- **{row['source']}** retained records span {row.get('earliestRecordDate') or 'unknown'} to {row.get('latestRecordDate') or 'unknown'}.")
    if summary["sourceAccessGaps"]:
        lines += ["", "Unverified/access gaps are retained explicitly:"]
        for gap in summary["sourceAccessGaps"]:
            lines.append(f"- {gap.get('source','unknown')} {gap.get('key','unknown')}: {gap.get('httpStatus') or gap.get('error') or 'not verified'}")
    next_cohort = summary["nextCohort"]
    lines += ["", "## Continuation", "",
              f"- Missing normalized candidate names: **{summary['missingCandidateNames']}**.",
              f"- Tracker-only records against this bounded evidence set: **{summary['trackerOnlyCount']}**.",
              f"- Accepted alias rules retained: **{summary['acceptedAliasCount']}**.",
              f"- Next BSE cohort: **{next_cohort['candidateCount']}** candidates in **{next_cohort.get('selection',{}).get('periodMonth','none')}**, source-review only.",
              "- The inherited Dhanwel June/August spelling/lifecycle collision remains review-only; no fuzzy merge is authorized.",
              "- NSE historical timeout cohorts and SEBI pre-2004/dedicated-SME/cancellation scope gaps remain open coverage limitations.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--missing", type=Path, required=True)
    parser.add_argument("--current-review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--next-cohort", type=Path, required=True)
    parser.add_argument("--next-limit", type=int, default=25)
    args = parser.parse_args()
    audit = load_json(args.audit)
    current_review = load_json(args.current_review)
    next_cohort = next_bse_cohort(args.missing, current_review, args.next_limit)
    by_source = [compact_group(row) for row in audit.get("eligibleDistinctBySource") or []]
    by_breakdown = [compact_group(row) for row in audit.get("eligibleDistinctBySourcePeriodBoardStage") or []]
    summary = {
        "schemaVersion": 1, "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(), "asOf": audit.get("asOf"),
        "bySource": by_source, "bySourcePeriodBoardStage": by_breakdown,
        "missingCandidateNames": int(audit.get("missingCandidateNames") or 0),
        "trackerOnlyCount": len(audit.get("trackerOnly") or []),
        "acceptedAliasCount": len(audit.get("acceptedAliases") or []),
        "sourceDateRanges": audit.get("sourceDateRanges") or [],
        "sourceAccessGaps": audit.get("sourceAccessGaps") or [],
        "nextCohort": {"candidateCount": next_cohort["candidateCount"], "selection": next_cohort.get("selection") or {},
                       "path": args.next_cohort.as_posix()},
    }
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.next_cohort.write_text(json.dumps(next_cohort, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.report.write_text(report_markdown(summary), encoding="utf-8")
    print(json.dumps({"bySource": by_source, "nextCohort": {**next_cohort["selection"], "candidateCount": next_cohort["candidateCount"]}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
