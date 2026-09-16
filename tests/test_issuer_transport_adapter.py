import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_issuer_offer_docs as runner


class IssuerTransportAdapterTests(unittest.TestCase):
    def test_current_parser_exposes_bounded_transport_contract(self):
        self.assertTrue(hasattr(runner.parser.base, "MAX_PDF_BYTES"))
        original_transport_cap = runner.parser.legacy.base.MAX_PDF_BYTES
        original_current_cap = runner.parser.base.MAX_PDF_BYTES
        seen = {}
        try:
            runner.parser.base.MAX_PDF_BYTES = 35 * 1024 * 1024

            def fake_download(session, url):
                seen["limit"] = runner.parser.legacy.base.MAX_PDF_BYTES
                seen["url"] = url
                return b"%PDF-test"

            with mock.patch.object(runner.parser.legacy, "download_pdf", side_effect=fake_download):
                data = runner._bounded_download_pdf(object(), "https://www.sebi.gov.in/example.pdf")

            self.assertEqual(data, b"%PDF-test")
            self.assertEqual(seen["limit"], 35 * 1024 * 1024)
            self.assertEqual(seen["url"], "https://www.sebi.gov.in/example.pdf")
            self.assertEqual(runner.parser.legacy.base.MAX_PDF_BYTES, original_transport_cap)
        finally:
            runner.parser.base.MAX_PDF_BYTES = original_current_cap
            runner.parser.legacy.base.MAX_PDF_BYTES = original_transport_cap


if __name__ == "__main__":
    unittest.main()
