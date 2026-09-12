import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_issuer_offer_docs.py"
spec = importlib.util.spec_from_file_location("enrich_issuer_offer_docs", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class IssuerOfferDocumentTests(unittest.TestCase):
    def test_registry_uses_exact_whitelisted_hosts(self):
        for entry in mod.ISSUER_DOCUMENTS.values():
            self.assertTrue(mod._host_matches(entry["url"], entry["host"]))
        self.assertFalse(
            mod._host_matches(
                "https://evil.example/raksantransformers.com/rhp.pdf",
                "raksantransformers.com",
            )
        )

    def test_identity_requires_expected_issuer(self):
        self.assertTrue(
            mod._identity_matches(
                "Raksan Transformers Limited",
                "RED HERRING PROSPECTUS\nRAKSAN TRANSFORMERS LIMITED\nDETAILS OF THE OFFER",
            )
        )
        self.assertFalse(
            mod._identity_matches(
                "Raksan Transformers Limited",
                "RED HERRING PROSPECTUS\nUNRELATED INDUSTRIES LIMITED",
            )
        )

    def test_merge_fills_missing_values_without_overwriting_primary_values(self):
        record = {
            "company": "Example Limited",
            "freshIssueCr": 50.0,
            "registrar": "Primary Registrar",
            "priceBand": {"min": 90, "max": 100},
            "sources": [],
            "documents": [],
        }
        parsed = {
            "issueComposition": {
                "freshShares": 6_000_000,
                "freshIssueCr": 60.0,
                "ofsShares": 1_000_000,
                "ofsCr": 10.0,
                "totalIssueSizeCr": 70.0,
            },
            "registrar": "Issuer PDF Registrar",
            "leadManagers": ["Example Capital Limited"],
            "promoters": [],
            "financials": None,
            "objectsOfIssue": [],
            "shareholding": None,
            "extractedFields": ["issueComposition", "leadManagers", "registrar"],
        }
        doc = {
            "url": "https://example.com/rhp.pdf",
            "type": "RHP",
            "title": "Red Herring Prospectus",
            "sourcePage": "https://example.com/investors/",
        }
        changed = mod.merge_issuer_enrichment(
            record,
            parsed,
            doc,
            pdf_hash="abc",
            pages_read=30,
            page_count=300,
        )
        self.assertEqual(record["freshIssueCr"], 50.0)
        self.assertEqual(record["registrar"], "Primary Registrar")
        self.assertEqual(record["ofsCr"], 10.0)
        self.assertEqual(record["issueSizeCr"], 70.0)
        self.assertEqual(record["leadManagers"], ["Example Capital Limited"])
        self.assertIn("issueComposition", changed)
        self.assertEqual(record["issuerDocumentExtraction"]["source"], "Issuer website")
        self.assertEqual(record["sources"][0]["kind"], "issuer-filing")

    def test_zero_ofs_is_preserved(self):
        merged = mod._merge_dict_missing(
            {"freshShares": 2_000_000},
            {"freshShares": 2_100_000, "ofsShares": 0, "ofsCr": 0.0},
        )
        self.assertEqual(merged["freshShares"], 2_000_000)
        self.assertEqual(merged["ofsShares"], 0)
        self.assertEqual(merged["ofsCr"], 0.0)

    def test_queue_targets_only_registered_priority_gaps(self):
        payload = {
            "ipos": [
                {"id": "raksan-transformers-limited", "company": "Raksan Transformers Limited"},
                {"id": "other", "company": "Other Limited"},
            ]
        }
        queue = {
            "queue": [
                {
                    "id": "raksan-transformers-limited",
                    "priority": 0,
                    "missingFields": ["exchange.issueComposition"],
                },
                {
                    "id": "other",
                    "priority": 0,
                    "missingFields": ["exchange.issueComposition"],
                },
            ]
        }
        targets = mod._targets(payload, queue, priority_max=1, limit=10)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0][0]["id"], "raksan-transformers-limited")


if __name__ == "__main__":
    unittest.main()
