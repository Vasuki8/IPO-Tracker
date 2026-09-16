#!/usr/bin/env python3
"""Mark canonical static IPO fields under the Final Prospectus source policy.

This is a non-destructive migration step. Existing mixed-source values are kept
visible temporarily, but are explicitly marked pending revalidation. New market
updates are prevented from writing these canonical fields by the policy-aware
updater and offer-document runners.

New extraction metadata distinguishes fields merely recognized by a parser from
fields actually accepted by the canonical policy. Legacy financial verification
is retained only when its exact source-table evidence still supports the current
canonical values.
"""
from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import final_prospectus_identity as identity
import final_prospectus_policy as policy

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"


def _document_level_financial_evidence(
    record: dict[str, Any], source_url: str | None
) -> dict[str, Any] | None:
    provenance = record.get("documentFieldProvenance") or {}
    if not isinstance(provenance, dict):
        return None
    if source_url and str(provenance.get("sourceUrl") or "") != str(source_url):
        return None
    evidence = provenance.get("evidence") or {}
    financial = evidence.get("financials") if isinstance(evidence, dict) else None
    return financial if isinstance(financial, dict) and financial else None


def _financial_provenance_valid(
    record: dict[str, Any], evidence: dict[str, Any] | None
) -> bool:
    if not isinstance(evidence, dict):
        return False
    if evidence.get("value") != record.get("financials"):
        return False
    detail = evidence.get("evidence")
    if not isinstance(detail, dict) or not detail:
        detail = _document_level_financial_evidence(record, evidence.get("sourceUrl"))
    if not detail:
        return False
    parsed = {
        "financials": copy.deepcopy(record.get("financials")),
        "fieldEvidence": {"financials": copy.deepcopy(detail)},
    }
    return policy._financial_evidence_supported(record, parsed)


def _extraction_fields(record: dict[str, Any], extraction: Any) -> set[str]:
    if not isinstance(extraction, dict):
        return set()
    if identity.known_non_final_document_url(record, extraction.get("documentUrl")):
        return set()
    doc = {
        "type": extraction.get("documentType"),
        "title": extraction.get("documentTitle"),
    }
    if extraction.get("status") != "extracted" or not policy.is_final_prospectus(doc):
        return set()

    # New runners explicitly separate parser recognition from canonical writes.
    # Never promote an unsupported parser result merely because it appeared in
    # ``extractedFields``.
    if isinstance(extraction.get("canonicalFields"), list):
        fields = {str(field) for field in extraction.get("canonicalFields") or []}
        return fields & set(policy.STATIC_CANONICAL_FIELDS)

    # Legacy extraction records predate canonicalFields. Keep the migration
    # compatibility for non-financial static fields, but financials require the
    # same cell-level evidence contract used by current Final Prospectus writes.
    fields = {str(field) for field in (extraction.get("extractedFields") or [])}
    if "issueComposition" in fields:
        fields.update({"issueSizeCr", "freshIssueCr", "ofsCr"})
    if "issuePrice" in fields:
        fields.add("listing.issuePrice")
    fields &= set(policy.STATIC_CANONICAL_FIELDS)
    if "financials" in fields:
        source_url = str(extraction.get("documentUrl") or "")
        static_evidence = (record.get("staticFieldProvenance") or {}).get("financials")
        if isinstance(static_evidence, dict):
            valid = _financial_provenance_valid(record, static_evidence)
        else:
            detail = _document_level_financial_evidence(record, source_url)
            fake = {
                "value": record.get("financials"),
                "sourceUrl": source_url,
                "evidence": detail,
            }
            valid = _financial_provenance_valid(record, fake)
        if not valid:
            fields.discard("financials")
    return fields


def _bootstrap_provenance(record: dict[str, Any], verified: set[str], checked_at: str) -> None:
    provenance = record.setdefault("staticFieldProvenance", {})
    for extraction_key in ("offerDocumentExtraction", "issuerDocumentExtraction"):
        extraction = record.get(extraction_key)
        fields = _extraction_fields(record, extraction)
        if not fields or not isinstance(extraction, dict):
            continue
        for field in fields:
            verified.add(field)
            if field in provenance:
                continue
            entry: dict[str, Any] = {
                "sourceUrl": extraction.get("documentUrl"),
                "documentType": "PROSPECTUS",
                "documentDate": extraction.get("documentFiledDate"),
                "sha256": extraction.get("sha256"),
                "parserVersion": extraction.get("parserVersion"),
                "checkedAt": extraction.get("extractedAt") or checked_at,
                "migratedFrom": extraction_key,
            }
            if field == "financials":
                detail = _document_level_financial_evidence(
                    record, str(extraction.get("documentUrl") or "")
                )
                if detail:
                    entry["value"] = copy.deepcopy(record.get("financials"))
                    entry["evidence"] = copy.deepcopy(detail)
            provenance[field] = entry


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
        final_doc = identity.choose_candidate(record, policy.final_prospectus_candidates(record))
        if final_doc:
            counts["withFinalProspectus"] += 1

        provenance = record.setdefault("staticFieldProvenance", {})
        verified: set[str] = set()
        for field, evidence in list(provenance.items()):
            if field not in policy.STATIC_CANONICAL_FIELDS or not isinstance(evidence, dict):
                continue
            if identity.known_non_final_document_url(record, evidence.get("sourceUrl")):
                provenance.pop(field, None)
                continue
            if not policy.is_final_prospectus(
                {"type": evidence.get("documentType"), "title": evidence.get("documentTitle")}
            ):
                continue
            if field == "financials" and not _financial_provenance_valid(record, evidence):
                # A legacy Final Prospectus marker without matching cell-level
                # table evidence cannot satisfy the canonical provenance gate.
                provenance.pop("financials", None)
                continue
            verified.add(field)

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
