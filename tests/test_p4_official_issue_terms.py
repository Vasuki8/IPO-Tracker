import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_p4_official_issue_terms.py"
spec = importlib.util.spec_from_file_location("run_p4_official_issue_terms", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class P4OfficialIssueTermsTests(unittest.TestCase):
    def test_targets_only_issue_size_and_composition(self):
        queue = {
            "queue": [
                {
                    "id": "lot-only",
                    "priority": 4,
                    "missingFields": ["exchange.lotSize"],
                },
                {
                    "id": "issue-size",
                    "priority": 4,
                    "missingFields": ["exchange.issueSizeCr", "exchange.lotSize"],
                },
                {
                    "id": "composition",
                    "priority": 4,
                    "missingFields": ["exchange.issueComposition"],
                },
                {
                    "id": "p5",
                    "priority": 5,
                    "missingFields": ["exchange.issueSizeCr", "exchange.issueComposition"],
                },
            ]
        }
        targets = mod.priority_targets(queue, 4)
        self.assertNotIn("lot-only", targets)
        self.assertEqual(targets["issue-size"], {"exchange.issueSizeCr"})
        self.assertEqual(targets["composition"], {"exchange.issueComposition"})
        self.assertNotIn("p5", targets)

    def test_merge_fills_issue_terms_without_touching_lot_size(self):
        record = {
            "id": "example",
            "company": "Example Limited",
            "symbol": "EXAMPLE",
            "priceBand": {"min": 100, "max": 110},
            "lotSize": None,
            "issueSizeCr": None,
            "sources": [],
            "observations": {},
        }
        doc = {
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/example.pdf",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/sep-2026/example.html",
            "filedDate": "2026-09-01",
        }
        parsed = {
            "freshIssueCr": 80.0,
            "ofsCr": 20.0,
            "totalIssueSizeCr": 100.0,
            "freshShares": 7_272_727,
            "ofsShares": 1_818_182,
        }
        with patch.object(mod.base.offer.base, "extract_issue_composition", return_value=parsed):
            changed = mod.merge_issue_terms(record, "Bid Lot 100 Equity Shares", doc)

        self.assertIsNone(record["lotSize"])
        self.assertEqual(record["issueSizeCr"], 100.0)
        self.assertEqual(record["freshIssueCr"], 80.0)
        self.assertEqual(record["ofsCr"], 20.0)
        self.assertIn("issueComposition", changed)
        self.assertNotIn("lotSize", changed)
        self.assertEqual(record["issueComposition"]["freshShares"], 7_272_727)
        self.assertEqual(record["observations"]["SEBIOfferIssueTerms"]["totalIssueSizeCr"], 100.0)
        self.assertNotIn("lotSize", record["observations"]["SEBIOfferIssueTerms"])

    def test_merge_is_fill_only(self):
        record = {
            "issueSizeCr": 125.0,
            "freshIssueCr": 125.0,
            "ofsCr": None,
            "issueComposition": {"freshValueCr": 125.0},
            "sources": [],
            "observations": {},
        }
        doc = {"url": "https://www.sebi.gov.in/sebi_data/attachdocs/example.pdf"}
        parsed = {
            "freshIssueCr": 90.0,
            "ofsCr": 10.0,
            "totalIssueSizeCr": 100.0,
        }
        with patch.object(mod.base.offer.base, "extract_issue_composition", return_value=parsed):
            changed = mod.merge_issue_terms(record, "ignored", doc)

        self.assertEqual(record["issueSizeCr"], 125.0)
        self.assertEqual(record["freshIssueCr"], 125.0)
        self.assertEqual(record["ofsCr"], 10.0)
        self.assertEqual(record["issueComposition"], {"freshValueCr": 125.0})
        self.assertEqual(changed, ["ofsCr"])


if __name__ == "__main__":
    unittest.main()
