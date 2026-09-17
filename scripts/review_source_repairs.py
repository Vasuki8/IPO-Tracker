"""Read-only CI collection preview; output is an artifact, never a publication."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import apply_corrections as corrections
import build_missing_queue as missing_queue
import enforce_final_prospectus_policy as final_policy
import run_p4_offer_residuals as residuals
import run_offer_documents as documents
import offer_parser as parser
from validate_data import validate_payload

ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC_PAGE_LIMIT = 45


def _review_value(record):
    # Policy enforcement updates this clock for every record. Keep actual
    # policy/proof/quarantine changes visible without diagnosing untouched rows.
    policy = record.get("staticSourcePolicy")
    if isinstance(policy, dict):
        return {**record, "staticSourcePolicy": {key: value for key, value in policy.items() if key != "checkedAt"}}
    return record


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--limit", type=int, default=100)
    cli.add_argument("--residual-limit", type=int, default=0)
    args = cli.parse_args()
    if not 0 <= args.residual_limit <= 30:
        cli.error("--residual-limit must be between 0 and 30")
    payload = json.loads(documents.DATA_FILE.read_text())
    before = copy.deepcopy(payload)
    prior = {row["id"]: row for row in before["ipos"]}
    documents.run(payload, limit=args.limit, workers=4, checkpoint=documents.atomic_save)
    documents.atomic_save(payload)
    residual_health = None
    if args.residual_limit:
        final_policy.apply_policy(payload)
        today = datetime.now(missing_queue.IST).date()
        queue = {"queue": missing_queue.build_queue(payload["ipos"], today)}
        residual_health = residuals.run(
            payload, limit=args.residual_limit, workers=3,
            checkpoint=documents.atomic_save, queue_payload=queue,
        )
    # A previously empty field may first be extracted in either collection
    # pass. Apply the publication review registry before saving its final
    # policy, queue and validation result.
    corrections.apply(payload, json.loads((ROOT / "data/verified_corrections.json").read_text()))
    final_policy.apply_policy(payload)
    documents.atomic_save(payload)
    missing_queue.main(payload=payload, output_file=ROOT / "data/missing_queue.json")
    report = validate_payload(payload)
    review_ids = {item["id"] for item in report["issues"]}
    results = []
    changed_records = []
    for record in payload["ipos"]:
        old = prior.get(record["id"], {})
        if _review_value(old) == _review_value(record):
            continue
        result = {"id": record["id"], "company": record.get("company"), "repair": record.get("documentRepair"), "residualRepair": record.get("p4OfferResidualRepair"), "objectsOfIssue": record.get("objectsOfIssue"), "financials": record.get("financials"), "leadManagers": record.get("leadManagers"), "registrar": record.get("registrar"), "evidence": record.get("documentFieldProvenance"), "conflicts": (record.get("offerDocumentExtraction") or {}).get("conflicts")}
        results.append(result)
        changed_records.append(record)

    # The completed collection and validation must survive interruption of the
    # optional PDF excerpts below, just as the canonical data checkpoint does.
    out = ROOT / "data/source_review.json"
    out.write_text(json.dumps({"before": validate_payload(before), "after": report, "records": results, "residuals": residual_health}, ensure_ascii=False, indent=2) + "\n")
    print("SOURCE_REVIEW_SUMMARY " + json.dumps({key: value for key, value in report.items() if key != "issues"}), flush=True)

    for record, result in zip(changed_records, results):
        print("SOURCE_REVIEW " + json.dumps(result), flush=True)
        if record["id"] in review_ids:
            doc = documents.document_for(record)
            if doc and (documents.CACHE / (hashlib.sha256(doc["url"].encode()).hexdigest() + ".pdf")).exists():
                try:
                    text, _, _ = parser.extract_pdf_text(documents.pdf_bytes(doc), page_limit=DIAGNOSTIC_PAGE_LIMIT)
                    snippets = []
                    for page in text.split("\f")[:DIAGNOSTIC_PAGE_LIMIT]:
                        lines = page.splitlines()
                        for i, line in enumerate(lines):
                            if parser._HEADING.search(line) and not re.search(r"\.{3,}", line):
                                snippets.append("\n".join(lines[max(0, i - 2):i + 35]))
                                if len(snippets) == 3:
                                    break
                        if len(snippets) == 3:
                            break
                    print("SOURCE_LAYOUT " + json.dumps({"id": record["id"], "snippets": snippets}), flush=True)
                except Exception as exc:
                    print("Source layout unavailable: " + str(exc)[:200], flush=True)
    return int(report["errorCount"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
