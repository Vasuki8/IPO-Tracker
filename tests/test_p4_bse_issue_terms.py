import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_p4_bse_issue_terms.py"
spec = importlib.util.spec_from_file_location("run_p4_bse_issue_terms", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class P4BseIssueTermsTests(unittest.TestCase):
    def test_targets_only_p4_issue_terms(self):
        queue = {
            "queue": [
                {"id": "lot", "priority": 4, "missingFields": ["exchange.lotSize"]},
                {"id": "size", "priority": 4, "missingFields": ["exchange.issueSizeCr"]},
                {"id": "composition", "priority": 4, "missingFields": ["exchange.issueComposition"]},
                {"id": "old", "priority": 5, "missingFields": ["exchange.issueSizeCr"]},
            ]
        }
        targets = mod.priority_targets(queue, 4)
        self.assertNotIn("lot", targets)
        self.assertEqual(targets["size"], {"exchange.issueSizeCr"})
        self.assertEqual(targets["composition"], {"exchange.issueComposition"})
        self.assertNotIn("old", targets)

    def test_symbol_conflict_is_rejected(self):
        self.assertFalse(mod.identity_ok({"symbol": "ABC"}, {"symbol": "XYZ", "isEquity": True}))
        self.assertTrue(mod.identity_ok({"symbol": "ABC"}, {"symbol": "ABC", "isEquity": True}))

    def test_detail_merge_fills_size_and_document_but_not_lot(self):
        record = {
            "symbol": "ABC",
            "issueSizeCr": None,
            "lotSize": None,
            "documents": [],
            "sources": [],
            "observations": {},
        }
        detail = {
            "symbol": "ABC",
            "isEquity": True,
            "issueSizeCr": 55.5,
            "lotSize": 1200,
            "sharesOffered": 5_000_000,
            "documents": [
                {
                    "type": "PROSPECTUS",
                    "title": "Prospectus & GID",
                    "url": "https://www.bseindia.com/downloads/ipo/example.pdf",
                    "source": "BSE",
                }
            ],
        }
        changed = mod.merge_bse_detail(record, detail, "https://www.bseindia.com/markets/PublicIssues/DisplayIPO.aspx?id=1")
        self.assertEqual(record["issueSizeCr"], 55.5)
        self.assertIsNone(record["lotSize"])
        self.assertIn("issueSizeCr", changed)
        self.assertIn("documents", changed)
        self.assertEqual(len(record["documents"]), 1)

    def test_pdf_merge_fills_composition_without_touching_lot(self):
        record = {
            "issueSizeCr": None,
            "lotSize": None,
            "sources": [],
            "observations": {},
        }
        doc = {"url": "https://www.bseindia.com/downloads/ipo/example.pdf"}
        parsed = {
            "freshIssueCr": 40.0,
            "ofsCr": 10.0,
            "totalIssueSizeCr": 50.0,
            "freshShares": 4_000_000,
            "ofsShares": 1_000_000,
        }
        with patch.object(mod.offer_terms.offer.base, "extract_issue_composition", return_value=parsed):
            changed = mod.merge_bse_pdf_terms(record, "ignored", doc)
        self.assertEqual(record["issueSizeCr"], 50.0)
        self.assertEqual(record["freshIssueCr"], 40.0)
        self.assertEqual(record["ofsCr"], 10.0)
        self.assertIsNone(record["lotSize"])
        self.assertIn("issueComposition", changed)
        self.assertNotIn("lotSize", changed)

    def test_non_bse_pdf_is_never_selected(self):
        record = {
            "documents": [
                {
                    "type": "PROSPECTUS",
                    "title": "Prospectus",
                    "url": "https://example.com/prospectus.pdf",
                }
            ]
        }
        self.assertIsNone(mod.choose_bse_offer_pdf(record))


if __name__ == "__main__":
    unittest.main()
