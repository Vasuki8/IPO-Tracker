import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v14.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v14", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OfferDocsV14Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 14)

    def test_csm_style_abbreviated_cover_headers_recover_intermediaries(self):
        text = """
        CSM TECHNOLOGIES LIMITED
        BOOK RUNNING LEAD MANAGER
        NAME AND LOGO OF BRLM CONTACT PERSON EMAIL AND TELEPHONE
        Keynote Financial Services Limited
        Virendra Chaurasia / Sunu Thomas
        E-mail: mbd@keynoteindia.net
        Tel: +91 22 6826 6000
        REGISTRAR TO THE ISSUE
        NAME AND LOGO OF THE REGISTRAR CONTACT PERSON EMAIL AND TELEPHONE
        KFin Technologies Limited
        M. Murali Krishna
        E-mail: csmtechnologies.ipo@kfintech.com
        Tel.: +91 040-67162222
        BID/ISSUE PERIOD
        """
        parsed = mod.parse_document_text(text)
        self.assertEqual(parsed["leadManagers"], ["Keynote Financial Services Limited"])
        self.assertEqual(parsed["registrar"], "KFin Technologies Limited")
        self.assertIn("leadManagers", parsed["extractedFields"])
        self.assertIn("registrar", parsed["extractedFields"])

    def test_normalizer_does_not_remove_entity_names_or_section_boundaries(self):
        text = """
        BOOK RUNNING LEAD MANAGER
        NAME AND LOGO OF BRLM CONTACT PERSON EMAIL AND TELEPHONE
        Alpha Capital Limited
        REGISTRAR TO THE ISSUE
        NAME AND LOGO OF THE REGISTRAR CONTACT PERSON EMAIL AND TELEPHONE
        Beta Registry Private Limited
        BID/ISSUE PERIOD
        """
        cleaned = mod.normalize_cover_intermediary_headers(text)
        self.assertIn("BOOK RUNNING LEAD MANAGER", cleaned)
        self.assertIn("REGISTRAR TO THE ISSUE", cleaned)
        self.assertIn("Alpha Capital Limited", cleaned)
        self.assertIn("Beta Registry Private Limited", cleaned)
        self.assertNotIn("NAME AND LOGO OF BRLM", cleaned)
        self.assertNotIn("NAME AND LOGO OF THE REGISTRAR", cleaned)


if __name__ == "__main__":
    unittest.main()
