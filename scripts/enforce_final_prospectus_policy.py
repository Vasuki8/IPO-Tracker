#!/usr/bin/env python3
"""Mark canonical static IPO fields under the Final Prospectus source policy.

This is a non-destructive migration step. Existing mixed-source values are kept
visible temporarily, but are explicitly marked pending revalidation. New market
updates are prevented from writing these canonical fields by the policy-aware
updater and offer-document runners.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import final_prospectus_policy as policy

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"


def _extraction_fields(extraction: Any) -> set[str]:
    if not isinstance(extraction, dict):
        return set()
    doc = {
        "type": extraction.get("documentType"),
        "title": extraction.get("documentTitle"),
    }
    if extraction.get("status") != "extracted" or not policy.is_final_prospectus(doc):
        return set()
    fields = {str(field) for field in (extraction.get("extractedFields") or [])}
    if "issueComposition" in fields:
        fields.update({"issueSizeCr", "freshIssueCr", "ofsCr"})
    if "issuePrice" in fields:
        fields.add("listing.issuePrice")
    return fields & set(policy.STATIC_CANONICAL_FIELDS)


def _bootstrap_provenance(record: dict[str, Any], verified: set[str], checked_at: str) -> None:
    provenance = record.setdefault("staticFieldProvenance", {})
    for extraction_key in ("offerDocumentExtraction", "issuerDocumentExtraction"):
        extraction = record.get(extraction_key)
        fields = _extraction_fields(extraction)
        if not fields or not isinstance(extraction, dict):
            continue
        for field in fields:
            verified.add(field)
            provenance.setdefault(
                field,
                {
                    "sourceUrl": extraction.get("documentUrl"),
                    "documentType": "PROSPECTUS",
                    "documentDate": extraction.get("documentFiledDate"),
                    "sha256": extraction.get("sha256"),
                    "parserVersion": extraction.get("parserVersion"),
                    "checkedAt": extraction.get("extractedAt") or checked_at,
                    "migratedFrom": extraction_key,
                },
            )


def apply_policy(payload: dict[str, Any]) -> dict[str, int]:
    checked_at = datetime.now(timezone.utc).isoformat()
    counts = {
        "records": 0,
        "withFinalProspectus": 0,
        "fullyVerified": 0,
        "pendingRevalidation": 0,
        "awaitingFinalProspectus": 0,
    }

    for record in payload.get("ipos") or []:
        if not isinstance(record, dict):
            continue
        counts["records"] += 1
        final_doc = policy.choose_final_prospectus(record)
        if final_doc:
            counts["withFinalProspectus"] += 1

        verified = {
            field
            for field, evidence in (record.get("staticFieldProvenance") or {}).items()
            if field in policy.STATIC_CANONICAL_FIELDS
            and isinstance(evidence, dict)
            and policy.is_final_prospectus(
                {"type": evidence.get("documentType"), "title": evidence.get("documentTitle")}
            )
        }
        _bootstrap_provenance(record, verified, checked_at)

        pending = sorted(
            field
            for field in policy.STATIC_CANONICAL_FIELDS
            if policy.field_value(record, field) not in (None, "", [], {})
            and field not in verified
        )

        if final_doc and not pending:
            status = "verified"
            counts["fullyVerified"] += 1
        elif final_doc:
            status = "pending-revalidation"
            counts["pendingRevalidation"] += 1
        else:
            status = "awaiting-final-prospectus"
            counts["awaitingFinalProspectus"] += 1

        existing = dict(record.get("staticSourcePolicy") or {})
        record["staticSourcePolicy"] = {
            **existing,
            "policy": "final-prospectus-only",
            "status": status,
            "documentUrl": final_doc.get("url") if final_doc else None,
            "documentType": "PROSPECTUS" if final_doc else None,
            "checkedAt": checked_at,
            "verifiedFields": sorted(verified),
            "pendingRevalidationFields": pending,
            "marketStaticTerms": "observation-only",
        }

    payload.setdefault("meta", {})["finalProspectusSourcePolicy"] = {
        **counts,
        "policy": "final-prospectus-only",
        "checkedAt": checked_at,
    }
    return counts


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--data", type=Path, default=DATA_FILE)
    args = cli.parse_args()
    payload = json.loads(args.data.read_text(encoding="utf-8"))
    counts = apply_policy(payload)
    args.data.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
