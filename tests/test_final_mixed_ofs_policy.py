import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_parser as parser
import final_prospectus_policy as policy
import run_offer_documents as documents
from issue_composition_checks import COMPOSITION_FIELDS, record_composition_problems
from objects_evidence_fixtures import objects_parsed


SOURCE_URL = "https://nsearchives.nseindia.com/corporate/FP_INE1C6T01020_14NOV2025.pdf"
SOURCE_HASH = "85eb9319dc01027821813c71d3702164911442a14547ad72cc04270ea6612eda"
DOC = {"type": "PROSPECTUS", "title": "Final Prospectus", "url": SOURCE_URL,
       "filedDate": "2025-11-14", "source": "NSE"}
CHECKED_AT = "2026-09-17T14:00:00Z"
LEGACY = {"freshShares": 34_845_069, "ofsShares": 17_422_535,
          "freshIssueCr": 378.069, "ofsCr": 378.069, "totalIssueSizeCr": 756.138}


class FinalMixedOfsPolicyTests(unittest.TestCase):
    def source(self):
        return (ROOT / "tests/fixtures/issue_composition/emmvee-final-offer.txt").read_text()

    def record(self):
        record = {
            "id": "emmvee", "company": "Emmvee Photovoltaic Power Limited",
            "openDate": "2025-11-11", "documents": [copy.deepcopy(DOC)],
            "issueComposition": copy.deepcopy(LEGACY), "issueSizeCr": 756.138,
            "freshIssueCr": 378.069, "ofsCr": 378.069,
            "listing": {"issuePrice": 217.0, "gainPct": None},
            "financials": {"unit": "₹ crore", "periods": []},
            "dataCorrections": [{"field": "promoters", "reason": "Earlier reviewed repair"}],
        }
        # Synthetic accepted table evidence isolates preservation of unrelated
        # objects. The complete source replay separately checks the actual table.
        retained = objects_parsed([
            {"purpose": "Repayment of borrowings", "amountCr": 1621.294},
            {"purpose": "General corporate purposes", "amountCr": 438.711},
        ])
        policy.apply_final_prospectus_static_fields(
            record, retained, DOC, sha256=SOURCE_HASH,
            parser_version=31, checked_at="2026-09-17T09:00:00Z",
        )
        for field in COMPOSITION_FIELDS:
            record["staticFieldProvenance"][field] = {
                "field": field, "value": copy.deepcopy(record[field]),
                "sourceUrl": SOURCE_URL, "sha256": SOURCE_HASH,
                "documentType": "PROSPECTUS", "parserVersion": 24,
                "checkedAt": "2026-09-16T17:02:50Z",
            }
        record["offerDocumentExtraction"] = {
            "status": "extracted", "documentType": "PROSPECTUS",
            "documentUrl": SOURCE_URL, "parserVersion": 31,
            "extractedFields": ["objectsOfIssue"],
            "canonicalFields": sorted(record["staticFieldProvenance"]),
        }
        return record

    def test_source_repair_replaces_complete_legacy_group_and_preserves_other_evidence(self):
        record = self.record()
        before = copy.deepcopy(record)
        parsed = parser.parse_document_text(self.source())
        with patch.object(documents, "timestamp", return_value=CHECKED_AT):
            changes = documents.correct_record(record, parsed, DOC, SOURCE_HASH, 511, 511)

        self.assertEqual(record["freshIssueCr"], 2143.862)
        self.assertEqual(record["ofsCr"], 756.138)
        self.assertEqual(record["issueSizeCr"], 2900.0)
        self.assertEqual(record["issueComposition"]["freshShares"], 98_795_483)
        self.assertEqual(record["issueComposition"]["ofsShares"], 34_845_069)
        self.assertEqual(record_composition_problems(record), [])
        self.assertEqual(set(COMPOSITION_FIELDS) & {c["field"] for c in changes}, set(COMPOSITION_FIELDS))
        for field in COMPOSITION_FIELDS:
            proof = record["staticFieldProvenance"][field]
            self.assertEqual(proof["value"], record[field])
            self.assertEqual(proof["sourceUrl"], SOURCE_URL)
            self.assertEqual(proof["sha256"], SOURCE_HASH)
            self.assertEqual(proof["parserVersion"], parser.PARSER_VERSION)
            self.assertEqual(proof["checkedAt"], CHECKED_AT)
            self.assertEqual(proof["evidence"], parsed["fieldEvidence"]["issueComposition"])
            correction = next(c for c in changes if c["field"] == field)
            self.assertEqual(correction["before"], before[field])
            self.assertEqual(correction["after"], record[field])
        for field in ("objectsOfIssue", "financials"):
            self.assertEqual(record[field], before[field])
        self.assertEqual(record["staticFieldProvenance"]["objectsOfIssue"],
                         before["staticFieldProvenance"]["objectsOfIssue"])
        self.assertEqual(record["listing"]["gainPct"], before["listing"]["gainPct"])
        self.assertEqual(record["dataCorrections"], before["dataCorrections"] + changes)
        self.assertIn("issueComposition", record["offerDocumentExtraction"]["extractedFields"])
        self.assertEqual(record["offerDocumentExtraction"]["parserVersion"], parser.PARSER_VERSION)

        accepted = copy.deepcopy(record)
        with patch.object(documents, "timestamp", return_value=CHECKED_AT):
            self.assertEqual(documents.correct_record(record, parsed, DOC, SOURCE_HASH, 511, 511), [])
        self.assertEqual(record["dataCorrections"], accepted["dataCorrections"])
        self.assertEqual(record["staticFieldProvenance"], accepted["staticFieldProvenance"])

    def test_incomplete_seller_list_cannot_replace_any_part_of_retained_group(self):
        record = self.record()
        before = copy.deepcopy(record)
        source = self.source().replace("AND 17,422,534 EQUITY SHARES^", "AND [●] EQUITY SHARES^")
        parsed = parser.parse_document_text(source)
        self.assertNotIn("issueComposition", parsed)
        self.assertNotIn("issueComposition", parsed["extractedFields"])
        with patch.object(documents, "timestamp", return_value=CHECKED_AT):
            changes = documents.correct_record(record, parsed, DOC, SOURCE_HASH, 511, 511)
        self.assertFalse(set(COMPOSITION_FIELDS) & {c["field"] for c in changes})
        for field in COMPOSITION_FIELDS:
            self.assertEqual(record[field], before[field])
            self.assertEqual(record["staticFieldProvenance"][field], before["staticFieldProvenance"][field])

    def test_partial_new_component_cannot_mix_with_old_aliases_and_proofs(self):
        record = self.record()
        before = copy.deepcopy(record)
        parsed = {"issueComposition": {"freshShares": 98_795_483, "freshIssueCr": 2143.862}}
        changes = policy.apply_final_prospectus_static_fields(
            record, parsed, DOC, sha256=SOURCE_HASH, parser_version=parser.PARSER_VERSION,
            checked_at=CHECKED_AT,
        )
        self.assertEqual(changes, [])
        for field in COMPOSITION_FIELDS:
            self.assertEqual(record[field], before[field])
            self.assertEqual(record["staticFieldProvenance"][field], before["staticFieldProvenance"][field])


if __name__ == "__main__":
    unittest.main()
