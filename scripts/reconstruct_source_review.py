"""Reconstruct the missing seven-record proposal as a NEW, UNACCEPTED lineage.

Run with the repository's frozen uv environment. Inputs, code and canonical data
are read-only; output must be outside the checkout. This is an offline diagnostic,
not a publisher or an acceptance transport. Teamtech's unresolved source-unit
conflict unconditionally blocks seven-record acceptance, including when its
structural parser checks pass. An independent Emmvee-only source-check candidate
is emitted separately; it is not a substitute for seven-record acceptance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ORIGINAL_UNRECOVERED_SHA = "5516b3ad6ba4345abc25d7a9b2771eb5c3b32f00e9163f30167da9d6b80cf6f6"
BASE_SHA = "29e2c170165e9dad215f786b1805fb8e18680dd43b219a59c29a5954a4160e5c"
PARSER_FILES = {
    "scripts/final_prospectus_parser.py": "503750e3c3d935af98037abd86f8ff647a46ca72d29db93b35944ab4bd2bafe0",
    "scripts/offer_parser.py": "e8d2655ab28230bb9504f6f6896364e29ec2358fe3d37304556b24f7968f6574",
    "scripts/p4_offer_parser.py": "5d65cdcb264f97a555b72407403b8d352de866a2bf7c0a65f56dc4572575a4ea",
    "scripts/objects_of_issue_checks.py": "1d0f1d5813a8dd93773769c41249ef891100c3482952c050aae6e1f919537f0f",
    "scripts/issue_composition_checks.py": "1aeaed38bc3df2ed8009c9bb0a08c249a37cb999fefc11b99dfffde11063f891",
}
TARGETS = {"emmvee", "teamtech", "unimech", "blackbuck", "mbel", "shriahimsa", "genxai"}
HOLDS = TARGETS - {"emmvee", "teamtech"}
FIELDS = ("issueComposition", "issueSizeCr", "freshIssueCr", "ofsCr")
EMMVEE = {"freshShares": 98795483, "ofsShares": 34845069,
          "freshIssueCr": 2143.862, "ofsCr": 756.138,
          "totalIssueSizeCr": 2900.0, "valuationPriceUsed": 217.0}
SOURCES = {
    "emmvee": {"url": "https://nsearchives.nseindia.com/corporate/FP_INE1C6T01020_14NOV2025.pdf",
               "sha256": "85eb9319dc01027821813c71d3702164911442a14547ad72cc04270ea6612eda",
               "date": "2025-11-14", "pageCount": 511},
    "teamtech": {"url": "https://nsearchives.nseindia.com/emerge/corporates/content/TeamtechFormworkSolutionsLimited_PROSP.pdf",
                 "sha256": "985909fbad119ffa02604f6fbb2895387a98d817a1fa8b486a7806ac18b537e8",
                 "date": "2026-05-22", "pageCount": 372},
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git(code, *args):
    return subprocess.check_output(["git", "-C", str(code), *args])


def diff(before, after, path=""):
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        rows = []
        for key in sorted(before.keys() | after.keys()):
            part = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in before:
                rows.append({"path": part, "operation": "add", "after": after[key]})
            elif key not in after:
                rows.append({"path": part, "operation": "remove", "before": before[key]})
            else:
                rows.extend(diff(before[key], after[key], part))
        return rows
    return [{"path": path, "operation": "replace", "before": before, "after": after}]


def main():
    reconstruction_script_sha = sha(Path(__file__).read_bytes())
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--code", type=Path, required=True)
    cli.add_argument("--expected-code-commit", required=True,
                     help="Full actual HEAD SHA reviewed for this NEW execution; never an equal-tree substitute")
    cli.add_argument("--expected-base-commit", required=True,
                     help="Full immutable main/base SHA whose canonical payload is being reconstructed")
    cli.add_argument("--expected-registry-sha256", required=True,
                     help="Exact reviewed data/verified_corrections.json SHA-256 for this execution")
    cli.add_argument("--emmvee-pdf", type=Path, required=True)
    cli.add_argument("--teamtech-pdf", type=Path, required=True)
    cli.add_argument("--retained-pdf-dir", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--reviewed-at", help="Reuse timestamp for identical candidate bytes; validation report generation time remains current")
    args = cli.parse_args()
    code, out = args.code.resolve(), args.out.resolve()
    if out == code or code in out.parents or out.exists():
        cli.error("Use a new output directory outside the repository")
    if (not re.fullmatch(r"[0-9a-f]{40}", args.expected_code_commit)
            or not re.fullmatch(r"[0-9a-f]{40}", args.expected_base_commit)
            or not re.fullmatch(r"[0-9a-f]{64}", args.expected_registry_sha256)):
        cli.error("Expected code/base commits and registry SHA-256 must be full lowercase hexadecimal digests")
    out.mkdir(parents=True)
    checked_at = args.reviewed_at or datetime.now(timezone.utc).isoformat()
    checks = []

    def check(ok, name, detail=None):
        checks.append({"name": name, "passed": bool(ok), "detail": detail})
        if not ok:
            save(out / "rejected-technical-checks.json", checks)
            raise AssertionError(name)

    code_commit = git(code, "rev-parse", "HEAD").decode().strip()
    code_tree = git(code, "rev-parse", "HEAD^{tree}").decode().strip()
    base_commit = args.expected_base_commit
    check(code_commit == args.expected_code_commit,
          "Exact observed code commit; never substitute an equal-tree remote commit")
    check(subprocess.run(["git", "-C", str(code), "merge-base", "--is-ancestor", base_commit, code_commit],
                         check=False).returncode == 0, "Pinned base is an ancestor of the actual reviewed code")
    check(not git(code, "diff", "HEAD", "--"), "Tracked code and data are unmodified")
    base_bytes = git(code, "show", base_commit + ":data/ipos.json")
    canonical_path = code / "data/ipos.json"
    check(sha(base_bytes) == BASE_SHA and canonical_path.read_bytes() == base_bytes,
          "Current canonical payload exactly matches the recorded main base", BASE_SHA)
    registry_bytes = (code / "data/verified_corrections.json").read_bytes()
    registry_sha = sha(registry_bytes)
    check(registry_sha == args.expected_registry_sha256, "Exact explicitly pinned correction registry", registry_sha)
    for name, digest in PARSER_FILES.items():
        check(sha((code / name).read_bytes()) == digest, "Immutable reviewed parser/structural-check file: " + name)
    observed_files = {
        name: sha((code / name).read_bytes())
        for name in git(code, "ls-files").decode().splitlines()
        if name.startswith(("scripts/", "schemas/", ".github/workflows/"))
        or name in {"pyproject.toml", "uv.lock", "data/verified_corrections.json", "data/public_display_holds.json"}
    }
    sys.path.insert(0, str(code / "scripts"))
    import run_offer_documents as runner
    import final_prospectus_policy as policy
    import apply_corrections as corrections
    from enforce_final_prospectus_policy import apply_policy
    from issue_composition_checks import record_composition_problems
    from objects_of_issue_checks import objects_evidence_problems
    from validate_data import validate_payload

    check(runner.parser.PARSER_VERSION == 33, "Current producer is parser 33")
    base = json.loads(base_bytes)
    before_rows = {r["id"]: r for r in base["ipos"]}
    check(len(base["ipos"]) == len(before_rows) == 1366, "Exact unique base record count")
    registry = json.loads(registry_bytes)
    entries = {e["identity"]["id"]: e for e in registry["reviewedObjects"]}
    retained = {}
    for identifier in sorted(HOLDS):
        entry = entries[identifier]
        pdf_path = args.retained_pdf_dir / (identifier + ".pdf")
        if pdf_path.exists():
            digest = sha(pdf_path.read_bytes())
            check(digest == entry["evidence"]["sha256"], "Recovered retained-hold PDF hash: " + identifier)
            state = "exact bytes recovered and hash-checked; full source not re-reviewed in this reconstruction"
        else:
            digest = None
            state = "full PDF unavailable here; preserving existing reviewed hold, not claiming new source acceptance"
        retained[identifier] = {"url": entry["source"]["url"],
                                "registryPdfSha256": entry["evidence"]["sha256"],
                                "recoveredPdfSha256": digest, "verification": state,
                                "scope": entry.get("scope", "value")}

    parsed, documents, source_receipts, extracted_text = {}, {}, {}, {}
    real_extract_text = runner.parser.extract_pdf_text
    for identifier, pdf_path in (("emmvee", args.emmvee_pdf), ("teamtech", args.teamtech_pdf)):
        source = SOURCES[identifier]
        data = pdf_path.read_bytes()
        check(sha(data) == source["sha256"], "Exact source PDF hash: " + identifier)
        matches = [d for d in policy.final_prospectus_candidates(before_rows[identifier]) if d.get("url") == source["url"]]
        check(len(matches) == 1, "Exact Final Prospectus link: " + identifier)
        doc = copy.deepcopy(matches[0])
        check(doc.get("sha256") in (None, source["sha256"]), "No contradictory linked PDF hash: " + identifier)
        check(doc.get("filedDate") == source["date"], "Exact Final Prospectus reporting date: " + identifier)
        doc["sha256"] = source["sha256"]
        documents[identifier] = doc

        def capture_text(data):
            result = real_extract_text(data)
            extracted_text[identifier] = result[0]
            return result

        with patch("socket.socket.connect", side_effect=AssertionError("Network forbidden")) as sock, \
             patch("socket.create_connection", side_effect=AssertionError("Network forbidden")) as conn, \
             patch("requests.sessions.Session.request", side_effect=AssertionError("Network forbidden")) as req, \
             patch.object(runner, "pdf_bytes", return_value=data) as pdf_read, \
             patch.object(runner.parser, "extract_pdf_text", side_effect=capture_text) as text_read:
            result, digest, pages_read, page_count = runner.extract(before_rows[identifier], doc, cached_only=True)
            check(sock.call_count == conn.call_count == req.call_count == 0, "No network calls: " + identifier)
            check(pdf_read.call_count == text_read.call_count == 1, "One actual complete-PDF extraction: " + identifier)
        check(digest == source["sha256"] and pages_read == page_count == source["pageCount"],
              "Full source pages consumed by current parser: " + identifier)
        text = extracted_text[identifier]
        markers = [re.match(r"\[PAGE (\d+)\]\n", page) for page in text.split("\f")]
        check(all(markers) and [int(m[1]) for m in markers] == list(range(1, page_count + 1)),
              "Ordered complete physical-page markers: " + identifier)
        (out / (identifier + "-production-text.txt")).write_text(text, encoding="utf-8")
        save(out / (identifier + "-full-parser-diagnostic.json"), result)
        parsed[identifier] = result
        source_receipts[identifier] = {**source, "bytes": len(data), "pagesRead": pages_read,
                                      "textSha256": sha(text.encode()), "networkRequests": 0,
                                      "newDownloads": 0, "identityCheck": "runner.extract passed"}

    emmvee = parsed["emmvee"]
    check(emmvee.get("issueComposition") == EMMVEE, "Source-confirmed full Emmvee composition", emmvee.get("issueComposition"))
    emmvee_pages = extracted_text["emmvee"].split("\f")
    compact = {i: " ".join(p.replace("\u00a0", " ").split()) for i, p in enumerate(emmvee_pages, 1)}
    composition_detail = emmvee["fieldEvidence"]["issueComposition"]
    for field, cell in composition_detail["fields"].items():
        raw = cell.get("row") or cell.get("heading")
        check(bool(raw) and " ".join(raw.split()) in compact.get(cell.get("page"), ""),
              "Exact claimed-page composition source text: " + field)
    for field in ("ofsShares", "ofsCr"):
        cell = composition_detail["fields"][field]
        row = cell.get("row", "")
        check(cell.get("page") == 3 and row.count("₹3,780.69 MILLION BY") == 2
              and "17,422,535 EQUITY SHARES^" in row and "17,422,534 EQUITY SHARES^" in row
              and "sum of complete named OFS seller clauses" in cell.get("basis", ""),
              "Both named seller clauses, amounts and summation basis retained: " + field)
    p11, _ = runner.parser.extract_final_issue_composition(emmvee_pages[10])
    check(p11 and p11.get("ofsShares") == 34845069 and p11.get("ofsCr") == 756.138
          and p11.get("totalIssueSizeCr") == 2900.0, "Independent physical page 11 aggregate corroboration")

    # Generate only supported composition values/proofs with the existing policy.
    # Preserve older whole-document metadata and every unrelated field proof:
    # this bounded field repair does not represent a fresh whole-record refresh.
    one = copy.deepcopy(base)
    one_rows = {r["id"]: r for r in one["ipos"]}
    record = one_rows["emmvee"]
    prior = copy.deepcopy(record)
    changes = policy.apply_final_prospectus_static_fields(
        record, {"issueComposition": emmvee["issueComposition"],
                 "fieldEvidence": {"issueComposition": composition_detail}}, documents["emmvee"],
        sha256=SOURCES["emmvee"]["sha256"], parser_version=33, checked_at=checked_at)
    record["documentFieldProvenance"] = copy.deepcopy(prior["documentFieldProvenance"])
    record["staticSourcePolicy"] = copy.deepcopy(prior["staticSourcePolicy"])
    record.setdefault("dataCorrections", []).extend(changes)
    check([c["field"] for c in changes] == list(FIELDS), "Exactly four Emmvee correction events")
    check(not record_composition_problems(record), "Emmvee composition consistency")
    check(record["objectsOfIssue"] == prior["objectsOfIssue"] and
          record["staticFieldProvenance"]["objectsOfIssue"] == prior["staticFieldProvenance"]["objectsOfIssue"],
          "Emmvee allocations and complete allocation proof preserved exactly")
    for field in FIELDS:
        proof = record["staticFieldProvenance"][field]
        check(proof["value"] == record[field] and proof["sourceUrl"] == SOURCES["emmvee"]["url"]
              and proof["sha256"] == SOURCES["emmvee"]["sha256"] and proof["evidence"] == composition_detail
              and proof["parserVersion"] == 33 and proof["issueOpenDate"] == record["openDate"],
              "Source-bound field proof: " + field)
    allowed_top = set(FIELDS) | {"staticFieldProvenance", "dataCorrections"}
    check(all(prior.get(k) == record.get(k) for k in prior.keys() | record.keys() if k not in allowed_top),
          "All unrelated Emmvee fields and whole-document metadata preserved")
    check(all(v == record["staticFieldProvenance"].get(k) for k, v in prior["staticFieldProvenance"].items() if k not in FIELDS),
          "All unrelated Emmvee field proofs preserved")
    check(record["dataCorrections"][:len(prior["dataCorrections"])] == prior["dataCorrections"],
          "Complete prior Emmvee correction history preserved")

    # The seven-record scope is reconstructed for diagnosis only. Current policy
    # may hold Teamtech rather than emit the historical four-row replacement.
    # Neither disposition grants source acceptance to the raw four-row parse.
    seven = copy.deepcopy(one)
    rows = {r["id"]: r for r in seven["ipos"]}
    applied, conflicts = corrections.quarantine_reviewed_objects(
        rows, [entries[i] for i in sorted(TARGETS - {"emmvee"})])
    check(applied == 6 and not conflicts, "Existing registry applies exact six retained-value holds", {"applied": applied, "conflicts": conflicts})
    teamtech = parsed["teamtech"]
    allocations = teamtech.get("objectsOfIssue")
    teamtech_evidence = teamtech.get("fieldEvidence", {}).get("objectsOfIssue")
    check(allocations == entries["teamtech"]["evidence"]["completeSourceAllocations"],
          "Teamtech parser retains exact four table-purpose strings and amounts")
    check(sum(Decimal(str(r["amountCr"])) for r in allocations) == Decimal("45.4859")
          and not objects_evidence_problems(allocations, teamtech_evidence), "Teamtech structural table check only")
    team_prior = copy.deepcopy(rows["teamtech"])
    team_changes = policy.apply_final_prospectus_static_fields(
        rows["teamtech"], {"objectsOfIssue": allocations, "fieldEvidence": {"objectsOfIssue": teamtech_evidence}},
        documents["teamtech"], sha256=SOURCES["teamtech"]["sha256"], parser_version=33, checked_at=checked_at)
    rows["teamtech"]["documentFieldProvenance"] = team_prior["documentFieldProvenance"]
    rows["teamtech"].setdefault("dataCorrections", []).extend(team_changes)
    if entries["teamtech"].get("scope", "value") == "document":
        teamtech_disposition = "held by current document-scoped policy; raw four-row parse remains UNACCEPTED"
        check(not team_changes and rows["teamtech"].get("objectsOfIssue") is None
              and rows["teamtech"]["objectsOfIssueReview"]["status"] == "quarantined",
              "Current document-scoped policy blocks same-document Teamtech restoration")
    else:
        teamtech_disposition = "historical value-scoped policy permits diagnostic replacement; source acceptance remains BLOCKED"
        check([x["field"] for x in team_changes] == ["objectsOfIssue"],
              "Historical value-scoped policy permits diagnostic replacement; not source acceptance")
    # Derive pending/verified state with the real policy on selected records only.
    # Its synthetic payload-level counters are discarded; base metadata stays exact.
    class ReviewClock(datetime):
        @classmethod
        def now(cls, tz=None):
            value = datetime.fromisoformat(checked_at)
            return value.astimezone(tz) if tz else value.replace(tzinfo=None)

    with patch("enforce_final_prospectus_policy.datetime", ReviewClock):
        apply_policy({"ipos": [rows[i] for i in sorted(TARGETS - {"emmvee"})]})
    current_held_ids = HOLDS | ({"teamtech"} if entries["teamtech"].get("scope", "value") == "document" else set())
    for identifier in sorted(current_held_ids):
        row, old = rows[identifier], before_rows[identifier]
        snap = row["objectsOfIssueReview"]["snapshot"]
        check(row.get("objectsOfIssue") is None and row["objectsOfIssueReview"]["status"] == "quarantined"
              and snap["before"] == old["objectsOfIssue"]
              and snap["sourceEvidence"] == old["staticFieldProvenance"]["objectsOfIssue"]
              and "objectsOfIssue" not in row.get("staticFieldProvenance", {})
              and "objectsOfIssue" not in row.get("documentFieldProvenance", {}).get("evidence", {})
              and "objectsOfIssue" not in row.get("offerDocumentExtraction", {}).get("canonicalFields", [])
              and "objectsOfIssue" in row["staticSourcePolicy"]["pendingRevalidationFields"],
              "Continuing hold preserves exact value, source proof and pending state: " + identifier)
        check(row["dataCorrections"][:len(old.get("dataCorrections", []))] == old.get("dataCorrections", []),
              "Prior correction history retained: " + identifier)

    outputs = {}
    for name, payload, expected_ids in (("SOURCE_CHECK_PASSED-emmvee-only-ipos.json", one, {"emmvee"}),
                                        ("UNACCEPTED-seven-record-ipos.json", seven, TARGETS)):
        actual_ids = {old["id"] for old, new in zip(base["ipos"], payload["ipos"]) if old != new}
        check(len(payload["ipos"]) == 1366 and [r["id"] for r in payload["ipos"]] == [r["id"] for r in base["ipos"]]
              and actual_ids == expected_ids, "Exact record scope: " + name, sorted(actual_ids))
        check({k: v for k, v in payload.items() if k != "ipos"} == {k: v for k, v in base.items() if k != "ipos"},
              "All payload metadata preserved: " + name)
        validation = validate_payload(payload)
        check(validation["errorCount"] == 0, "Strict whole-payload validation: " + name, validation["errorCount"])
        save(out / name, payload)
        check(sha((out / name).read_bytes()) != ORIGINAL_UNRECOVERED_SHA, "New lineage is not relabeled as missing original: " + name)
        changes_by_id = {r["id"]: diff(before_rows[r["id"]], r) for r in payload["ipos"] if r["id"] in actual_ids}
        diff_name = name.replace("-ipos.json", "-exact-diff.json")
        save(out / diff_name, changes_by_id)
        save(out / name.replace("-ipos.json", "-validation.json"), validation)
        outputs[name] = {"sha256": sha((out / name).read_bytes()), "changedIds": sorted(actual_ids),
                         "unchangedOtherRecords": 1366 - len(actual_ids), "metadataPreserved": True,
                         "strictErrors": validation["errorCount"], "reviewCount": validation["reviewCount"],
                         "exactDiff": diff_name, "exactDiffSha256": sha((out / diff_name).read_bytes())}

    save(out / "teamtech-UNACCEPTED-parser-evidence.json", {
        "status": "UNACCEPTED", "canonicalAcceptance": False,
        "identity": entries["teamtech"]["identity"], "source": source_receipts["teamtech"],
        "parserVersion": 33, "field": "objectsOfIssue", "value": allocations,
        "evidence": teamtech_evidence, "currentPolicyDisposition": teamtech_disposition,
    })
    save(out / "emmvee-source-checked-field-proofs.json", {f: record["staticFieldProvenance"][f] for f in FIELDS})
    check(canonical_path.read_bytes() == base_bytes and (code / "data/verified_corrections.json").read_bytes() == registry_bytes,
          "Input canonical payload and review registry were not modified")
    check(all(sha((code / name).read_bytes()) == digest for name, digest in observed_files.items()),
          "Observed code and policy files were not modified")
    check(not git(code, "diff", "HEAD", "--"), "No tracked checkout changes")
    check(sha(Path(__file__).read_bytes()) == reconstruction_script_sha,
          "Reconstruction helper bytes unchanged during execution")
    receipt = {
        "schemaVersion": 1, "status": "UNACCEPTED", "publicationAllowed": False,
        "reconstructionScriptSha256": reconstruction_script_sha,
        "reviewedAt": checked_at, "newLineage": True, "originalProposalRecovered": False,
        "originalProposalSha256": ORIGINAL_UNRECOVERED_SHA,
        "originalProposalAssessment": "Missing immutable working artifact; this reconstruction does not invalidate or recreate its identity.",
        "baseCommit": base_commit, "basePayloadSha256": BASE_SHA,
        "observedCodeCommit": code_commit, "observedCodeTree": code_tree,
        "codeCommitAvailability": "Caller-pinned exact checkout; remote publication is not checked by this offline harness",
        "registrySha256": registry_sha, "immutableParserFiles": PARSER_FILES,
        "parserVersion": 33, "recordCount": 1366, "outputs": outputs,
        "sources": source_receipts, "retainedHolds": retained,
        "emmveeComposition": {"sourceCheck": "passed", "publication": "blocked pending separately frozen current code, base and targeted transport",
                              "expected": EMMVEE, "physicalPagesVisuallyReviewed": [3, 11, 21, 117],
                              "printedPageMapping": {"3": "unnumbered cover", "11": 6, "21": 16, "117": 112},
                              "context": "Both named OFS sellers on cover; aggregate definition p11; full offer-size table p21; fresh gross/net and allocations p117; deployment text p118.",
                              "basisOfAllotmentFootnote": "Final Prospectus amounts marked subject to finalisation of Basis of Allotment; exact source wording retained, no later allotment outcome claimed.",
                              "preservedObjectsCr": [1621.294, 438.711], "completeObjectsProofPreserved": True,
                              "wholeDocumentMetadata": "Preserved unchanged; new parser-33 provenance is field-specific for the four composition fields."},
        "teamtechAllocations": {"sourceCheck": "blocked", "structuralCheck": "passed, insufficient for source acceptance",
                                "currentPolicyDisposition": teamtech_disposition,
                                "expectedRows": allocations, "expectedTotalCr": 45.4859,
                                "physicalAndPrintedPages": [22, 23, 87, 88, 89, 90, 91, 92],
                                "conflict": "Physical/printed p89 MEANS OF FINANCE numeric heading Amount in Crores applies to Net Proceeds 4,548.59 and TOTAL 4,548.59; pp22-23/87 state the same budget in lakhs (45.4859 crore).",
                                "secondaryDiscrepancy": "p90 quotation footnote 1,192.36 lakh differs from itemized and printed subtotal 1,192.35 lakh on pp91-92; no partial-spend reconciliation found.",
                                "notAnAcceptedCorrection": "The four-row candidate remains diagnostic. No inferred unit typo, adjusted amount, or purpose rewrite resolves the source contradiction."},
        "blockingRequirements": [
            "Authoritative reconciliation or explicit supersession of Teamtech's source-unit contradiction; retain a document-scoped hold meanwhile.",
            "Refreeze actual current main base, combined code commit/tree and complete publication transport after the independent source guard and public-hold releases.",
            "Do not publish the broad automatic repair preview: its scope is not this seven-record proposal.",
            "Original proposal and transport unavailable; any accepted replacement must retain a distinct new lineage and exact scope.",
            "P4 correctness gate remains blocked; no P5 or performance expansion is enabled by these structural checks."
        ],
        "observedCodeFiles": observed_files, "checks": checks,
        "actions": {"canonicalWrites": False, "codeEdits": False, "networkRequests": 0,
                    "workflowDispatches": False, "commits": False, "publication": False},
    }
    save(out / "source-acceptance-receipt.json", receipt)
    print(json.dumps({"status": receipt["status"], "emmveeSourceCheck": "passed", "teamtechSourceCheck": "blocked",
                      "baseCommit": base_commit, "observedCodeCommit": code_commit,
                      "outputs": outputs, "receiptSha256": sha((out / "source-acceptance-receipt.json").read_bytes())}))


if __name__ == "__main__":
    main()
