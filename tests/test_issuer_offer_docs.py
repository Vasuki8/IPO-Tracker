import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_issuer_offer_docs.py"
spec = importlib.util.spec_from_file_location("enrich_issuer_offer_docs", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def load_runner():
    runner_path = Path(__file__).resolve().parents[1] / "scripts" / "run_issuer_offer_docs.py"
    runner_spec = importlib.util.spec_from_file_location("run_issuer_offer_docs", runner_path)
    runner = importlib.util.module_from_spec(runner_spec)
    sys.modules[runner_spec.name] = runner
    runner_spec.loader.exec_module(runner)
    return runner


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

    def test_deep_scan_only_targets_requested_unparsed_sections(self):
        item = {
            "missingFields": [
                "offer.financials",
                "offer.promoterShareholding",
                "exchange.issueComposition",
            ]
        }
        self.assertEqual(
            mod._needs_deep_scan(item, {"financials": None, "shareholding": None}),
            (True, True),
        )
        self.assertEqual(
            mod._needs_deep_scan(item, {"financials": {"periods": [{}]}, "shareholding": None}),
            (False, True),
        )
        self.assertEqual(
            mod._needs_deep_scan(
                {"missingFields": ["exchange.issueComposition"]},
                {"financials": None, "shareholding": None},
            ),
            (False, False),
        )

    def test_deep_section_markers_cover_financial_and_shareholding_headings(self):
        self.assertTrue(mod._FINANCIAL_MARKERS.search("Summary of Restated Financial Information"))
        self.assertTrue(mod._FINANCIAL_MARKERS.search("KEY PERFORMANCE INDICATORS"))
        self.assertTrue(mod._SHAREHOLDING_MARKERS.search("Pre and Post-Issue Shareholding"))
        self.assertTrue(mod._SHAREHOLDING_MARKERS.search("Promoters and Promoter Group"))

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

    def test_runner_registers_official_shakti_drhp(self):
        runner = load_runner()
        entry = runner.base.ISSUER_DOCUMENTS["shakti-polytarp-limited"]
        self.assertEqual(entry["host"], "shaktipolytarp.com")
        self.assertEqual(entry["type"], "DRHP")
        self.assertTrue(mod._host_matches(entry["url"], entry["host"]))
        self.assertIn("DRHP_Shakti_29092025.pdf", entry["url"])

    def test_runner_registers_current_vama_rhp(self):
        runner = load_runner()
        entry = runner.base.ISSUER_DOCUMENTS["vama-wovenfab-limited"]
        self.assertEqual(entry["host"], "vamawoven.com")
        self.assertEqual(entry["type"], "RHP")
        self.assertTrue(mod._host_matches(entry["url"], entry["host"]))
        self.assertIn("RHP_VamaWovenfabLimited-2.pdf", entry["url"])
        self.assertEqual(entry["sourcePage"], "https://vamawoven.com/rhp/")

    def test_injecto_registrar_fallback_keeps_registrar_provenance(self):
        runner = load_runner()
        entry = runner.base.ISSUER_DOCUMENTS["injecto-polymers-limited"]
        self.assertEqual(entry["host"], "ipostatus.integratedregistry.in")
        self.assertEqual(entry["extractionSource"], "Registrar website")
        self.assertEqual(entry["sourceKind"], "registrar-filing")

        record = {
            "company": "INJECTO POLYMERS LIMITED",
            "sources": [],
            "documents": [],
        }
        parsed = {
            "issueComposition": {},
            "registrar": None,
            "leadManagers": [],
            "promoters": [],
            "financials": None,
            "objectsOfIssue": [],
            "shareholding": {"promoters": [], "promoterPreIssuePct": 88.14},
            "extractedFields": ["shareholding"],
        }
        changed = runner.merge_validated_offer_enrichment(
            record,
            parsed,
            entry,
            pdf_hash="abc",
            pages_read=120,
            page_count=400,
        )
        self.assertIn("shareholding", changed)
        self.assertEqual(record["issuerDocumentExtraction"]["source"], "Registrar website")
        matching_docs = [d for d in record["documents"] if d.get("url") == entry["url"]]
        self.assertEqual(matching_docs[0]["source"], "Integrated Registry")
        matching_sources = [s for s in record["sources"] if s.get("url") == entry["sourcePage"]]
        self.assertEqual(matching_sources[0]["name"], "Integrated Registry offer document")
        self.assertEqual(matching_sources[0]["kind"], "registrar-filing")


if __name__ == "__main__":
    unittest.main()
