import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v9.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v9", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OfferDocsV9Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 9)
        self.assertEqual(mod.base.PARSER_VERSION, 9)

    def test_newer_addendum_does_not_outrank_real_rhp(self):
        record = {
            "documents": [
                {
                    "type": "RHP",
                    "title": "Rentomojo Limited - RHP",
                    "url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1788501645342.pdf",
                    "filedDate": "2026-09-04",
                    "source": "SEBI",
                },
                {
                    "type": "RHP",
                    "title": "Rentomojo Limited - Addendum to RHP",
                    "url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1788934492263.pdf",
                    "filedDate": "2026-09-09",
                    "source": "SEBI",
                },
            ]
        }
        chosen = mod.choose_document(record)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen["url"], record["documents"][0]["url"])

    def test_abridged_rhp_remains_preferred_over_full_rhp(self):
        record = {
            "documents": [
                {
                    "type": "RHP",
                    "title": "Prasol Chemicals Limited - RHP",
                    "url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1788411848709.pdf",
                    "filedDate": "2026-09-03",
                    "source": "SEBI",
                },
                {
                    "type": "RHP",
                    "title": "Prasol Chemicals Limited - Abridged Prospectus",
                    "url": "https://www.sebi.gov.in/sebi_data/commondocs/sep-2026/Prasol%20Chemicals%20Limited%20-%20AP_p.pdf",
                    "filedDate": "2026-09-03",
                    "source": "SEBI",
                },
            ]
        }
        chosen = mod.choose_document(record)
        self.assertIsNotNone(chosen)
        self.assertIn("AP_p.pdf", chosen["url"])

    def test_only_supplemental_notice_returns_no_offer_document(self):
        record = {
            "documents": [
                {
                    "type": "RHP",
                    "title": "Prasol Chemicals Limited - Addendum to RHP",
                    "url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/addendum.pdf",
                    "source": "SEBI",
                }
            ]
        }
        self.assertIsNone(mod.choose_document(record))

    def test_explicit_addendum_type_is_supplemental(self):
        self.assertTrue(
            mod.is_supplemental_document(
                {"type": "ADDENDUM", "title": "Supplement to offer document"}
            )
        )

    def test_v8_shareholding_parser_remains_active(self):
        text = """
        Shareholding Pattern of our Company
        (A) Promoter and Promoter Group 9 52,071,136 61.53%
        (B) Public 12 32,567,414 38.47%
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 61.53, places=2)


if __name__ == "__main__":
    unittest.main()
