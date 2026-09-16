import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from publish_transaction import merge_payload


class IssueTermsPublicationTests(unittest.TestCase):
    @staticmethod
    def verified_record(fresh=60, ofs=40, source="original"):
        total = fresh + ofs
        url = f"https://example.test/{source}-prospectus.pdf"
        composition = {
            "freshShares": fresh * 100000,
            "ofsShares": ofs * 100000,
            "freshIssueCr": fresh,
            "ofsCr": ofs,
            "totalIssueSizeCr": total,
            "valuationPriceUsed": 100,
        }
        values = {
            "issueComposition": composition,
            "issueSizeCr": total,
            "freshIssueCr": fresh,
            "ofsCr": ofs,
        }
        return {
            "id": "issuer",
            "company": "Issuer Limited",
            "openDate": "2026-09-01",
            "status": "closed",
            **values,
            "staticFieldProvenance": {
                field: {
                    "source": "Final Prospectus",
                    "sourceUrl": url,
                    "documentType": "PROSPECTUS",
                    "value": copy.deepcopy(value),
                }
                for field, value in values.items()
            },
            "staticSourcePolicy": {
                "status": "verified",
                "verifiedFields": sorted(values),
                "pendingRevalidationFields": [],
            },
            "documentFieldProvenance": {
                "sourceUrl": url,
                "evidence": {"issueComposition": copy.deepcopy(composition)},
            },
            "offerDocumentExtraction": {
                "documentUrl": url,
                "canonicalFields": sorted(values),
            },
            "issuerDocumentExtraction": {
                "documentUrl": url,
                "canonicalFields": sorted(values),
            },
            "dataCorrections": [],
        }

    @staticmethod
    def quarantined_record(before):
        record = copy.deepcopy(before)
        fields = ["issueComposition", "issueSizeCr", "freshIssueCr", "ofsCr"]
        record["dataCorrections"].append({
            "field": "issueComposition",
            "before": {field: copy.deepcopy(record[field]) for field in fields},
            "sourceEvidence": copy.deepcopy(record["staticFieldProvenance"]),
            "reason": "Issue amounts contradict the Final Prospectus share evidence",
            "after": None,
        })
        record.update({field: None for field in fields})
        record["issueCompositionReview"] = {
            "status": "quarantined",
            "fields": fields,
            "reasons": ["Share counts and offer amounts disagree"],
            "checkedAt": "2026-09-16T12:00:00+00:00",
        }
        record["staticFieldProvenance"] = {}
        record["staticSourcePolicy"] = {
            "status": "pending-revalidation",
            "verifiedFields": [],
            "pendingRevalidationFields": fields,
        }
        record["documentFieldProvenance"]["evidence"] = {}
        record["offerDocumentExtraction"]["canonicalFields"] = []
        record["issuerDocumentExtraction"]["canonicalFields"] = []
        return record

    @staticmethod
    def merge(before, proposed, current):
        output, conflicts = merge_payload(
            {"ipos": [before]}, {"ipos": [proposed]}, {"ipos": [current]},
        )
        return output["ipos"][0], conflicts

    def test_competing_compositions_keep_accepted_amounts_and_source_together(self):
        before = self.verified_record()
        proposed = self.verified_record(fresh=90, ofs=30, source="proposed")
        current = self.verified_record(fresh=80, ofs=40, source="accepted")
        proposed["closeDate"] = "2026-09-05"
        current["status"] = "listed"

        record, conflicts = self.merge(before, proposed, current)

        self.assertEqual(record["issueComposition"], current["issueComposition"])
        self.assertEqual((record["issueSizeCr"], record["freshIssueCr"], record["ofsCr"]), (120, 80, 40))
        self.assertEqual(record["staticFieldProvenance"], current["staticFieldProvenance"])
        self.assertEqual(record["documentFieldProvenance"], current["documentFieldProvenance"])
        self.assertEqual(record["offerDocumentExtraction"], current["offerDocumentExtraction"])
        self.assertEqual(record["issuerDocumentExtraction"], current["issuerDocumentExtraction"])
        self.assertEqual(record["staticSourcePolicy"], current["staticSourcePolicy"])
        self.assertEqual(record["closeDate"], "2026-09-05")
        self.assertEqual(record["status"], "listed")
        self.assertEqual([item["path"] for item in conflicts], [["ipos", "issuer", "documentFields"]])
        self.assertEqual(conflicts[0]["proposed"]["freshIssueCr"], 90)

    def test_proposed_quarantine_cannot_attach_to_concurrently_accepted_repair(self):
        before = self.verified_record()
        proposed = self.quarantined_record(before)
        current = self.verified_record(fresh=80, ofs=40, source="accepted")

        record, conflicts = self.merge(before, proposed, current)

        self.assertEqual(record["issueComposition"], current["issueComposition"])
        self.assertEqual((record["issueSizeCr"], record["freshIssueCr"], record["ofsCr"]), (120, 80, 40))
        self.assertNotIn("issueCompositionReview", record)
        self.assertEqual(record["staticFieldProvenance"], current["staticFieldProvenance"])
        self.assertEqual(record["staticSourcePolicy"]["status"], "verified")
        self.assertEqual(conflicts[0]["proposed"]["issueCompositionReview"]["status"], "quarantined")
        self.assertIsNone(conflicts[0]["proposed"]["issueComposition"])

    def test_current_quarantine_cannot_be_detached_by_competing_document_repair(self):
        before = self.verified_record()
        current = self.quarantined_record(before)
        proposed = self.verified_record(fresh=90, ofs=30, source="proposed")
        proposed["closeDate"] = "2026-09-05"

        record, conflicts = self.merge(before, proposed, current)

        for field in ("issueComposition", "issueSizeCr", "freshIssueCr", "ofsCr"):
            self.assertIsNone(record[field])
        self.assertEqual(record["issueCompositionReview"], current["issueCompositionReview"])
        self.assertEqual(record["staticFieldProvenance"], {})
        self.assertEqual(record["staticSourcePolicy"]["status"], "pending-revalidation")
        self.assertEqual(record["offerDocumentExtraction"]["canonicalFields"], [])
        self.assertEqual(record["issuerDocumentExtraction"]["canonicalFields"], [])
        self.assertEqual(record["dataCorrections"], current["dataCorrections"])
        self.assertEqual(record["closeDate"], "2026-09-05")
        self.assertEqual(len(conflicts), 1)

    def test_quarantine_merges_with_independent_updates_and_preserves_both_audits(self):
        before = self.verified_record()
        proposed = self.quarantined_record(before)
        current = copy.deepcopy(before)
        current["status"] = "listed"
        current["dataCorrections"].append({"field": "status", "before": "closed", "after": "listed"})

        record, conflicts = self.merge(before, proposed, current)

        for field in ("issueComposition", "issueSizeCr", "freshIssueCr", "ofsCr"):
            self.assertIsNone(record[field])
        self.assertEqual(record["issueCompositionReview"], proposed["issueCompositionReview"])
        self.assertEqual(record["staticFieldProvenance"], {})
        self.assertEqual(record["staticSourcePolicy"]["status"], "pending-revalidation")
        self.assertEqual(record["status"], "listed")
        self.assertEqual(record["dataCorrections"], current["dataCorrections"] + proposed["dataCorrections"])
        self.assertEqual(conflicts, [])


if __name__ == "__main__":
    unittest.main()
