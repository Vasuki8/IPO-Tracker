import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_sebi_document_links.py"
spec = importlib.util.spec_from_file_location("enrich_sebi_document_links", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class SebiDocumentLinkTests(unittest.TestCase):
    def test_viewer_url_resolves_direct_pdf(self):
        url = (
            "https://www.sebi.gov.in/web/?file="
            "https%3A%2F%2Fwww.sebi.gov.in%2Fsebi_data%2Fattachdocs%2Fsep-2026%2F123.pdf"
        )
        self.assertEqual(
            mod.direct_pdf_from_url(url),
            "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/123.pdf",
        )

    def test_extracts_abridged_and_full_rhp(self):
        html = """
        <html><body>
          <a href="https://www.sebi.gov.in/sebi_data/commondocs/sep-2026/Example-AP_p.pdf">Example Limited - Abridged Prospectus</a>
          <a href="https://www.sebi.gov.in/web/?file=https%3A%2F%2Fwww.sebi.gov.in%2Fsebi_data%2Fattachdocs%2Fsep-2026%2F999.pdf">Example Limited - RHP</a>
        </body></html>
        """
        docs = mod.extract_pdf_links(
            html,
            "https://www.sebi.gov.in/filings/public-issues/sep-2026/example-rhp.html",
            fallback_type="RHP",
        )
        self.assertEqual(len(docs), 2)
        self.assertTrue(all(d["type"] == "RHP" for d in docs))
        self.assertTrue(any("AP_p.pdf" in d["url"] for d in docs))
        self.assertTrue(any("/attachdocs/" in d["url"] for d in docs))

    def test_non_sebi_pdf_is_rejected(self):
        self.assertIsNone(mod.direct_pdf_from_url("https://example.com/fake.pdf"))


if __name__ == "__main__":
    unittest.main()
