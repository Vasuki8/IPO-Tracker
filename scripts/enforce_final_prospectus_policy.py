#!/usr/bin/env python3
"""Mark canonical static IPO fields under the Final Prospectus source policy.

Existing mixed-source values are marked pending revalidation. Objects of issue
without matching source-table evidence are withheld with their original values
and proofs retained in an audit snapshot. Missing evidence does not establish
that those values are wrong. New market updates are prevented from writing
canonical fields by the policy-aware updater and offer-document runners.

New extraction metadata distinguishes fields merely recognized by a parser from
fields actually accepted by the canonical policy. Legacy financial verification
is retained only when its exact source-table evidence still supports the current
canonical values.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import final_prospectus_identity as identity
import final_prospectus_policy as policy
from issue_composition_checks import COMPOSITION_FIELDS, quarantined_fields, record_composition_problems
from objects_of_issue_checks import objects_evidence_problems, objects_problems, objects_quarantined

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ipos.json"


def _legacy_generic_issue_price(record: dict[str, Any]) -> bool:
    """Old generic PRICE OF evidence cannot prove the transaction was this IPO."""
    proofs = [
        (record.get("staticFieldProvenance") or {}).get("listing.issuePrice"),
        (record.get("listing") or {}).get("issuePriceEvidence"),
    ]
    for proof in proofs:
        if not isinstance(proof, dict):
            continue
        detail = proof.get("evidence") or {}
        if isinstance(detail, dict) and detail.get("method") != "final-offer-price-v2" and re.match(
            r"^\s*PRICE\s+OF\b", str(detail.get("heading") or ""), re.I
        ):
            return True
    return False


def _quarantine_inconsistent_composition(record: dict[str, Any], checked_at: str) -> None:
    """Withdraw contradictory canonical claims without losing their evidence."""
    problems = record_composition_problems(record)
    provenance = record.get("staticFieldProvenance") or {}
    canonical = any(
        isinstance(provenance.get(field), dict)
        and policy.is_final_prospectus({"type": provenance[field].get("documentType")})
        for field in COMPOSITION_FIELDS
    )
    if problems and canonical:
        before = {field: copy.deepcopy(record.get(field)) for field in COMPOSITION_FIELDS}
        source_evidence = {field: copy.deepcopy(provenance[field]) for field in COMPOSITION_FIELDS if field in provenance}
        snapshot = {
            "field": "issueComposition",
            "before": before,
            "after": {field: None for field in COMPOSITION_FIELDS},
            "reason": "Inconsistent canonical issue amounts/counts quarantined pending Final Prospectus revalidation",
            "findings": [{"field": field, "reason": reason} for field, reason in problems],
            "sourceEvidence": source_evidence,
            "correctedAt": checked_at,
        }
        record.setdefault("dataCorrections", []).append(copy.deepcopy(snapshot))
        record["issueCompositionReview"] = {
            "status": "quarantined",
            "fields": list(COMPOSITION_FIELDS),
            "checkedAt": checked_at,
            "snapshot": snapshot,
        }
        for field in COMPOSITION_FIELDS:
            record[field] = None

    held = quarantined_fields(record)
    if not held:
        return
    for field in held:
        provenance.pop(field, None)
    # Neither legacy extractedFields nor a later enforcement pass may revive
    # verification for a value withdrawn by this review.
    for key in ("offerDocumentExtraction", "issuerDocumentExtraction"):
        extraction = record.get(key)
        if not isinstance(extraction, dict):
            continue
        for field_list in ("canonicalFields", "extractedFields"):
            if isinstance(extraction.get(field_list), list):
                extraction[field_list] = [field for field in extraction[field_list] if field not in held]
    detail = (record.get("documentFieldProvenance") or {}).get("evidence")
    if isinstance(detail, dict) and "issueComposition" in held:
        detail.pop("issueComposition", None)


def _document_level_objects_evidence(
    record: dict[str, Any], source_url: Any, sha256: Any
) -> dict[str, Any] | None:
    """Use document evidence only for the exact bytes identified by a proof."""
    document = record.get("documentFieldProvenance")
    if not isinstance(document, dict) or not source_url or not sha256:
        return None
    if document.get("sourceUrl") != source_url or document.get("sha256") != sha256:
        return None
    if not policy.is_final_prospectus({
        "type": document.get("documentType"), "url": document.get("sourceUrl")
    }):
        return None
    evidence = document.get("evidence")
    detail = evidence.get("objectsOfIssue") if isinstance(evidence, dict) else None
    return detail if isinstance(detail, dict) and detail else None


def _objects_provenance_problems(record: dict[str, Any], proof: Any) -> list[str]:
    """Revalidate the source identity, stored value and every source-table row."""
    if record.get("objectsOfIssue") in (None, []):
        return ["Objects of issue have no current disclosed rows to verify"]
    if not isinstance(proof, dict):
        return ["Objects of issue have no Final Prospectus source proof"]
    source_url = proof.get("sourceUrl")
    if not source_url or not proof.get("sha256"):
        return ["Objects-of-issue source proof needs its document URL and SHA-256"]
    if identity.known_non_final_document_url(record, source_url) or not policy.is_final_prospectus({
        "type": proof.get("documentType"), "title": proof.get("documentTitle"), "url": source_url
    }):
        return ["Objects-of-issue source proof does not identify a Final Prospectus"]
    if proof.get("value") != record.get("objectsOfIssue"):
        return ["Objects-of-issue source proof does not match the current disclosed rows"]
    detail = proof.get("evidence")
    if detail in (None, {}, []):
        detail = _document_level_objects_evidence(record, source_url, proof.get("sha256"))
    return objects_evidence_problems(record.get("objectsOfIssue"), detail)


def _objects_proof_from_extraction(record: dict[str, Any], extraction: Any) -> dict[str, Any] | None:
    """A marker may migrate complete same-document evidence, never invent it."""
    if not isinstance(extraction, dict) or extraction.get("status") != "extracted":
        return None
    field_key = "canonicalFields" if isinstance(extraction.get("canonicalFields"), list) else "extractedFields"
    if "objectsOfIssue" not in (extraction.get(field_key) or []):
        return None
    proof = {
        "documentType": extraction.get("documentType"),
        "documentTitle": extraction.get("documentTitle"),
        "sourceUrl": extraction.get("documentUrl"),
        "sha256": extraction.get("sha256"),
        "value": copy.deepcopy(record.get("objectsOfIssue")),
        "evidence": _document_level_objects_evidence(
            record, extraction.get("documentUrl"), extraction.get("sha256")
        ),
    }
    return proof if not _objects_provenance_problems(record, proof) else None


def _retained_objects_proof(record: dict[str, Any]) -> dict[str, Any] | None:
    proof = (record.get("staticFieldProvenance") or {}).get("objectsOfIssue")
    if proof is not None:
        return proof if not _objects_provenance_problems(record, proof) else None
    for key in ("offerDocumentExtraction", "issuerDocumentExtraction"):
        proof = _objects_proof_from_extraction(record, record.get(key))
        if proof:
            return proof
    return None


def _quarantine_invalid_objects(record: dict[str, Any], checked_at: str) -> None:
    """Withhold unsupported allocations while retaining evidence for re-reading."""
    value = record.get("objectsOfIssue")
    invalid = objects_problems(value)
    provenance = record.get("staticFieldProvenance") or {}
    unsupported = value not in (None, []) and (
        objects_quarantined(record) or not _retained_objects_proof(record)
    )
    if invalid or unsupported:
        document = record.get("documentFieldProvenance") or {}
        detail = document.get("evidence") or {}
        source_proof = provenance.get("objectsOfIssue")
        source_proof = source_proof if isinstance(source_proof, dict) else {}
        extraction = record.get("offerDocumentExtraction") or record.get("issuerDocumentExtraction") or {}
        problems = invalid or _objects_provenance_problems(record, provenance.get("objectsOfIssue")) or [
            "Objects of issue remain subject to an unresolved source review"
        ]
        snapshot = {
            "field": "objectsOfIssue",
            "before": copy.deepcopy(value),
            "after": None,
            "reason": (
                "Invalid objects of issue quarantined pending Final Prospectus revalidation"
                if invalid else
                "Objects of issue lack matching source-table evidence; withheld pending Final Prospectus revalidation"
            ),
            "reviewKind": "invalid-values" if invalid else "source-evidence-required",
            "findings": problems,
            "sourceEvidence": copy.deepcopy(provenance.get("objectsOfIssue")),
            "documentEvidence": copy.deepcopy(detail.get("objectsOfIssue")),
            "documentProvenance": copy.deepcopy(document),
            "extractionEvidence": {
                key: copy.deepcopy(record[key])
                for key in ("offerDocumentExtraction", "issuerDocumentExtraction")
                if isinstance(record.get(key), dict)
            },
            "sourceUrl": source_proof.get("sourceUrl") or document.get("sourceUrl") or extraction.get("documentUrl"),
            "sha256": source_proof.get("sha256") or document.get("sha256") or extraction.get("sha256"),
            "correctedAt": checked_at,
        }
        record.setdefault("dataCorrections", []).append(copy.deepcopy(snapshot))
        record["objectsOfIssueReview"] = {
            "status": "quarantined", "reviewKind": snapshot["reviewKind"],
            "checkedAt": checked_at, "snapshot": snapshot,
        }
        record["objectsOfIssue"] = None
    if not objects_quarantined(record):
        return
    provenance.pop("objectsOfIssue", None)
    for key in ("offerDocumentExtraction", "issuerDocumentExtraction"):
        extraction = record.get(key)
        if not isinstance(extraction, dict):
            continue
        for field_list in ("canonicalFields", "extractedFields"):
            if isinstance(extraction.get(field_list), list):
                extraction[field_list] = [field for field in extraction[field_list] if field != "objectsOfIssue"]
    detail = (record.get("documentFieldProvenance") or {}).get("evidence")
    if isinstance(detail, dict):
        detail.pop("objectsOfIssue", None)


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
    from review_financial_tables import has_reviewed_financial_evidence
    if has_reviewed_financial_evidence(record):
        return True
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
    blocked = quarantined_fields(record)
    if objects_quarantined(record) or not _retained_objects_proof(record):
        blocked.add("objectsOfIssue")
    if _legacy_generic_issue_price(record):
        blocked.add("listing.issuePrice")
    if record_composition_problems(record):
        blocked |= set(COMPOSITION_FIELDS)

    # New runners explicitly separate parser recognition from canonical writes.
    # Never promote an unsupported parser result merely because it appeared in
    # ``extractedFields``.
    if isinstance(extraction.get("canonicalFields"), list):
        fields = {str(field) for field in extraction.get("canonicalFields") or []}
        return (fields & set(policy.STATIC_CANONICAL_FIELDS)) - blocked

    # Legacy extraction records predate canonicalFields. Keep the migration
    # compatibility for other static fields. Objects were blocked above unless
    # exact source-table evidence is present; financials need matching cells.
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
    return fields - blocked


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
            if field == "objectsOfIssue":
                proof = _objects_proof_from_extraction(record, extraction)
                if not proof:
                    verified.discard(field)
                    continue
                entry["value"] = copy.deepcopy(proof["value"])
                entry["evidence"] = copy.deepcopy(proof["evidence"])
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
        _quarantine_inconsistent_composition(record, checked_at)
        _quarantine_invalid_objects(record, checked_at)
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
            if field == "objectsOfIssue":
                if _objects_provenance_problems(record, evidence):
                    provenance.pop(field, None)
                    continue
                if evidence.get("evidence") in (None, {}, []):
                    # Preserve the matching raw evidence with the field before
                    # another partial extraction replaces document metadata.
                    evidence["evidence"] = copy.deepcopy(_document_level_objects_evidence(
                        record, evidence.get("sourceUrl"), evidence.get("sha256")
                    ))
            if field == "listing.issuePrice" and _legacy_generic_issue_price(record):
                provenance.pop(field, None)
                continue
            verified.add(field)

        _bootstrap_provenance(record, verified, checked_at)

        pending = sorted({
            field
            for field in policy.STATIC_CANONICAL_FIELDS
            if policy.field_value(record, field) not in (None, "", [], {})
            and field not in verified
        } | quarantined_fields(record) | ({"objectsOfIssue"} if objects_quarantined(record) else set()))

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
