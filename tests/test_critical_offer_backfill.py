import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_critical_offer_backfill.py"
spec = importlib.util.spec_from_file_location("run_critical_offer_backfill", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class CriticalOfferBackfillTests(unittest.TestCase):
    def test_html_filing_page_is_not_eligible(self):
        record = {"documents": [{
            "type": "RHP",
            "title": "RHP filing page",
            "url": "https://www.sebi.gov.in/filings/public-issues/sep-2026/example-rhp.html",
        }]}
        self.assertIsNone(mod.safe_choose_fallback_document(record))

    def test_direct_official_pdf_is_eligible(self):
        record = {"documents": [{
            "type": "RHP",
            "title": "Abridged Prospectus",
            "url": "https://www.sebi.gov.in/sebi_data/commondocs/sep-2026/example_AP_p.pdf",
        }]}
        chosen = mod.safe_choose_fallback_document(record)
        self.assertTrue(chosen["url"].endswith("example_AP_p.pdf"))

    def test_sebi_viewer_is_resolved_to_pdf(self):
        record = {"documents": [{
            "type": "RHP",
            "title": "RHP",
            "url": "https://www.sebi.gov.in/web/?file=https%3A%2F%2Fwww.sebi.gov.in%2Fsebi_data%2Fattachdocs%2Fsep-2026%2Ffull.pdf",
        }]}
        chosen = mod.safe_choose_fallback_document(record)
        self.assertEqual(chosen["url"], "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/full.pdf")


if __name__ == "__main__":
    unittest.main()
