"""Read-only CI collection preview; output is an artifact, never a publication."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

import run_offer_documents as documents
import offer_parser as parser
from validate_data import validate_payload

ROOT = Path(__file__).resolve().parents[1]


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--limit", type=int, default=100)
    args = cli.parse_args()
    payload = json.loads(documents.DATA_FILE.read_text())
    before = copy.deepcopy(payload)
    prior = {row["id"]: row for row in before["ipos"]}
    documents.run(payload, limit=args.limit, workers=4, checkpoint=documents.atomic_save)
    documents.atomic_save(payload)
    report = validate_payload(payload)
    review_ids = {item["id"] for item in report["issues"]}
    results = []
    for record in payload["ipos"]:
        old = prior.get(record["id"], {})
        if old == record:
            continue
        result = {"id": record["id"], "company": record.get("company"), "repair": record.get("documentRepair"), "financials": record.get("financials"), "leadManagers": record.get("leadManagers"), "registrar": record.get("registrar"), "evidence": record.get("documentFieldProvenance"), "conflicts": (record.get("offerDocumentExtraction") or {}).get("conflicts")}
        results.append(result)
        print("SOURCE_REVIEW " + json.dumps(result), flush=True)
        if record["id"] in review_ids:
            doc = documents.document_for(record)
            if doc and (documents.CACHE / (hashlib.sha256(doc["url"].encode()).hexdigest() + ".pdf")).exists():
                try:
                    text, _, _ = parser.extract_pdf_text(documents.pdf_bytes(doc))
                    snippets = []
                    for page in text.split("\f")[:45]:
                        lines = page.splitlines()
                        for i, line in enumerate(lines):
                            if parser._HEADING.search(line) and not re.search(r"\.{3,}", line):
                                snippets.append("\n".join(lines[max(0, i - 2):i + 35]))
                    print("SOURCE_LAYOUT " + json.dumps({"id": record["id"], "snippets": snippets[:3]}), flush=True)
                except Exception as exc:
                    print("Source layout unavailable: " + str(exc)[:200], flush=True)
    out = ROOT / "data/source_review.json"
    out.write_text(json.dumps({"before": validate_payload(before), "after": report, "records": results}, ensure_ascii=False, indent=2) + "\n")
    print("SOURCE_REVIEW_SUMMARY " + json.dumps({key: value for key, value in report.items() if key != "issues"}), flush=True)
    return int(report["errorCount"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
