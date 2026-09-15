import inspect
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

MODULE = SCRIPTS / "enrich_issuer_offer_docs.py"
spec = importlib.util.spec_from_file_location("enrich_issuer_offer_docs", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def load_runner():
    runner_path = SCRIPTS / "run_issuer_offer_docs.py"
    runner_spec = importlib.util.spec_from_file_location("run_issuer_offer_docs", runner_path)
    runner = importlib.util.module_from_spec(runner_spec)
    sys.modules[runner_spec.name] = runner
    runner_spec.loader.exec_module(runner)
    return runner


class IssuerOfferDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner()

    def test_registry_uses_exact_whitelisted_hosts(self):
        for entry in mod.ISSUER_DOCUMENTS.values():
            self.assertTrue(mod._host_matches(entry["url"], entry["host"]))
        for entry in self.runner.base.ISSUER_DOCUMENTS.values():
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

    def test_base_merge_fills_missing_values_without_overwriting_primary_values(self):
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

    def test_canonical_runner_uses_final_parser_and_deep_scan_contract(self):
        self.assertEqual(self.runner.base.PARSER_VERSION, 14)
        self.assertEqual(self.runner.parser.PARSER_VERSION, 14)
        params = inspect.signature(self.runner.base._extract_targeted_full_text).parameters
        self.assertIn("need_financials", params)
        self.assertIn("need_shareholding", params)
        self.assertIn("max_scan_pages", params)

    def test_runner_registers_current_verified_fallbacks(self):
        shakti = self.runner.base.ISSUER_DOCUMENTS["shakti-polytarp-limited"]
        self.assertEqual(shakti["host"], "shaktipolytarp.com")
        self.assertEqual(shakti["type"], "DRHP")
        self.assertIn("DRHP_Shakti_29092025.pdf", shakti["url"])

        vama = self.runner.base.ISSUER_DOCUMENTS["vama-wovenfab-limited"]
        self.assertEqual(vama["host"], "vamawoven.com")
        self.assertEqual(vama["type"], "RHP")
        self.assertIn("RHP_VamaWovenfabLimited-2.pdf", vama["url"])
        self.assertEqual(vama["sourcePage"], "https://vamawoven.com/rhp/")

    def test_p4_sebi_fallbacks_are_explicit_and_regulator_hosted(self):
        expected = {
            "leap": "Leap India Limited",
            "propshop": "Propshop Events and Exhibitions Limited",
            "alpinetex": "Alpine Texworld Limited",
            "aastha": "Aastha Spintex Limited",
            "rambhajo": "Advit Jewels Limited",
            "csm": "CSM Technologies Limited",
            "cleanmax": "Clean Max Enviro Energy Solutions Limited",
            "gspcrop": "GSP Crop Science Limited",
            "hexagon": "Hexagon Nutrition Limited",
            "cmpdi": "Central Mine Planning & Design Institute Limited",
            "innovision": "Innovision Limited",
            "jnpr": "Juniper Green Energy Limited",
            "aye": "Aye Finance Limited",
            "cmll": "Caliber Mining and Logistics Limited",
            "lcl": "Lohia Corp Limited",
            "mvelectro": "MV Electrosystems Limited",
            "manipalhos": "Manipal Health Enterprises Limited",
            "ompower": "Om Power Transmission Limited",
            "kissht": "Onemi Technology Solutions Limited",
            "kusumgar": "Kusumgar Limited",
            "knack": "Knack Packaging Limited",
            "pngsreva": "PNGS Reva Diamond Jewellery Limited",
        }
        for record_id, company in expected.items():
            doc = self.runner.base.ISSUER_DOCUMENTS[record_id]
            self.assertEqual(doc["company"], company)
            self.assertEqual(doc["host"], "www.sebi.gov.in")
            self.assertTrue(doc["url"].startswith("https://www.sebi.gov.in/sebi_data/attachdocs/"))
            self.assertEqual(doc["type"], "Prospectus")
            self.assertEqual(doc["extractionSource"], "SEBI")
            self.assertEqual(doc["documentSource"], "SEBI")
            self.assertEqual(doc["sourceKind"], "regulatory-filing")
            self.assertTrue(doc["sourcePage"].startswith("https://www.sebi.gov.in/filings/public-issues/"))

    def test_final_sebi_and_nse_fallbacks_are_retained(self):
        sebi = {
            "indomim": ("INDO-MIM Limited", "RHP", "1784523106091.pdf"),
            "omni": ("Omnitech Engineering Limited", "RHP", "1771933506852.pdf"),
            "rsl": ("Rajputana Stainless Limited", "Prospectus", "1775629467259.pdf"),
        }
        for record_id, (company, doc_type, pdf_name) in sebi.items():
            entry = self.runner.base.ISSUER_DOCUMENTS[record_id]
            self.assertEqual(entry["company"], company)
            self.assertEqual(entry["host"], "www.sebi.gov.in")
            self.assertEqual(entry["type"], doc_type)
            self.assertEqual(entry["extractionSource"], "SEBI")
            self.assertEqual(entry["documentSource"], "SEBI")
            self.assertEqual(entry["sourceKind"], "regulatory-filing")
            self.assertTrue(entry["url"].endswith(pdf_name))

        nse = {
            "ardee": ("Ardee Industries Limited", "FP_INE0XNF01022_10AUG2026.pdf"),
            "powerica": ("Powerica Limited", "FP_INE921L01032_30MAR2026.pdf"),
        }
        for record_id, (company, pdf_name) in nse.items():
            entry = self.runner.base.ISSUER_DOCUMENTS[record_id]
            self.assertEqual(entry["company"], company)
            self.assertEqual(entry["host"], "nsearchives.nseindia.com")
            self.assertEqual(entry["type"], "Prospectus")
            self.assertEqual(entry["extractionSource"], "NSE")
            self.assertEqual(entry["documentSource"], "NSE")
            self.assertEqual(entry["sourceKind"], "exchange-filing")
            self.assertTrue(entry["url"].endswith(pdf_name))
            self.assertEqual(entry["sourcePage"], entry["url"])

    def test_validated_terms_are_fill_only_and_observed(self):
        doc = {
            "url": "https://www.bseindia.com/example.pdf",
            "sourcePage": "https://www.bseindia.com/example.pdf",
            "host": "www.bseindia.com",
            "type": "Prospectus",
            "title": "Prospectus",
            "extractionSource": "BSE",
            "documentSource": "BSE",
            "sourceName": "BSE final Prospectus",
            "sourceKind": "exchange-filing",
        }
        record = {
            "lotSize": 50,
            "priceBand": None,
            "sources": [],
            "documents": [],
            "observations": {},
        }
        parsed = {
            "issueComposition": {},
            "leadManagers": [],
            "registrar": None,
            "promoters": [],
            "financials": None,
            "objectsOfIssue": [],
            "shareholding": None,
            "lotSize": 100,
            "priceBand": {"min": 80.0, "max": 85.0},
            "extractedFields": ["lotSize", "priceBand"],
        }
        changed = self.runner.merge_validated_offer_enrichment(
            record,
            parsed,
            doc,
            pdf_hash="abc",
            pages_read=12,
            page_count=20,
        )
        self.assertEqual(record["lotSize"], 50)
        self.assertEqual(record["priceBand"], {"min": 80.0, "max": 85.0})
        self.assertIn("priceBand", changed)
        self.assertNotIn("lotSize", changed)
        self.assertEqual(record["observations"]["Offer-document"]["lotSize"], 100)
        self.assertEqual(record["observations"]["Offer-document"]["source"], "BSE")
        self.assertEqual(record["issuerDocumentExtraction"]["parserVersion"], 14)

    def test_registrar_fallback_keeps_registrar_provenance(self):
        entry = self.runner.base.ISSUER_DOCUMENTS["injecto-polymers-limited"]
        self.assertEqual(entry["host"], "ipostatus.integratedregistry.in")
        self.assertEqual(entry["extractionSource"], "Registrar website")
        self.assertEqual(entry["sourceKind"], "registrar-filing")
        record = {"company": "INJECTO POLYMERS LIMITED", "sources": [], "documents": []}
        parsed = {
            "issueComposition": {},
            "registrar": None,
            "leadManagers": [],
            "promoters": [],
            "financials": None,
            "objectsOfIssue": [],
            "shareholding": {"promoters": [], "promoterPreIssuePct": 88.14},
            "lotSize": None,
            "priceBand": None,
            "extractedFields": ["shareholding"],
        }
        changed = self.runner.merge_validated_offer_enrichment(
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

    def test_duplicate_id_selects_exact_registered_issuer(self):
        payload = {
            "ipos": [
                {"id": "rsl", "company": "Rajputana Stainless Limited", "stage": "listed"},
                {
                    "id": "rsl",
                    "company": "Rajputana Stainless Limited-Special Withdrawal Option",
                    "stage": "closed",
                },
            ]
        }
        queue = {
            "queue": [
                {
                    "id": "rsl",
                    "company": "Rajputana Stainless Limited",
                    "priority": 4,
                    "missingFields": ["offer.registrar"],
                },
                {
                    "id": "rsl",
                    "company": "Rajputana Stainless Limited-Special Withdrawal Option",
                    "priority": 4,
                    "missingFields": ["exchange.issueSizeCr"],
                },
            ]
        }
        targets = self.runner._identity_safe_targets(payload, queue, priority_max=4, limit=10)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0][0]["company"], "Rajputana Stainless Limited")

    def test_ambiguous_same_issuer_duplicates_are_not_guessed(self):
        payload = {
            "ipos": [
                {"id": "rsl", "company": "Rajputana Stainless Limited"},
                {"id": "rsl", "company": "Rajputana Stainless Limited"},
            ]
        }
        queue = {
            "queue": [
                {
                    "id": "rsl",
                    "company": "Rajputana Stainless Limited",
                    "priority": 4,
                    "missingFields": ["offer.registrar"],
                }
            ]
        }
        self.assertEqual(self.runner._identity_safe_targets(payload, queue, 4, 10), [])

    def test_current_success_is_skipped_but_parser_or_document_change_reenables(self):
        spec_entry = self.runner.base.ISSUER_DOCUMENTS["ardee"]
        queue = {
            "queue": [
                {
                    "id": "ardee",
                    "company": "Ardee Industries Limited",
                    "priority": 4,
                    "missingFields": ["offer.financials"],
                }
            ]
        }
        current = {
            "ipos": [
                {
                    "id": "ardee",
                    "company": "Ardee Industries Limited",
                    "issuerDocumentExtraction": {
                        "status": "extracted",
                        "parserVersion": 14,
                        "documentUrl": spec_entry["url"],
                    },
                }
            ]
        }
        self.assertEqual(self.runner._identity_safe_targets(current, queue, 4, 10), [])

        old_parser = current["ipos"][0]["issuerDocumentExtraction"]
        old_parser["parserVersion"] = 13
        self.assertEqual(len(self.runner._identity_safe_targets(current, queue, 4, 10)), 1)

        old_parser["parserVersion"] = 14
        old_parser["documentUrl"] = "https://example.invalid/old.pdf"
        self.assertEqual(len(self.runner._identity_safe_targets(current, queue, 4, 10)), 1)

    def test_previous_failure_moves_behind_fresh_candidate(self):
        payload = {
            "meta": {"issuerOfferDocumentHealth": {"errors": ["Ardee Industries Limited: read timeout"]}},
            "ipos": [
                {"id": "ardee", "company": "Ardee Industries Limited"},
                {"id": "indomim", "company": "INDO-MIM Limited"},
            ],
        }
        queue = {
            "queue": [
                {
                    "id": "ardee",
                    "company": "Ardee Industries Limited",
                    "priority": 4,
                    "missingFields": ["offer.financials"],
                },
                {
                    "id": "indomim",
                    "company": "INDO-MIM Limited",
                    "priority": 4,
                    "missingFields": ["offer.financials"],
                },
            ]
        }
        targets = self.runner._identity_safe_targets(payload, queue, priority_max=4, limit=1)
        self.assertEqual(targets[0][0]["id"], "indomim")


if __name__ == "__main__":
    unittest.main()
