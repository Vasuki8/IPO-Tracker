import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_p4_offer_residuals as runner


class P4ResidualIdentityTests(unittest.TestCase):
    def test_official_identity_allows_lossy_opening_text(self):
        record = {
            "company": "Happy Steels Limited",
            "openDate": "2026-07-09",
            "priceBand": None,
        }
        doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://nsearchives.nseindia.com/emerge/corporates/content/HappySteelsLimited_PROSP.pdf",
            "filedDate": "2026-07-14",
        }
        primary = {"extractedFields": []}

        with (
            patch.object(runner.base, "pdf_bytes", return_value=b"%PDF-test"),
            patch.object(runner.parser, "extract_pdf_text", return_value=("scanned cover page", 1, 10)),
            patch.object(runner.parser, "parse_document_text", return_value=primary) as primary_mock,
            patch.object(runner.residual, "parse_document_text", return_value={}),
            patch.object(runner.residual, "merge_parsed", return_value=primary),
        ):
            parsed, digest, pages, count = runner.extract(record, doc)

        self.assertEqual(parsed, primary)
        self.assertTrue(digest)
        self.assertEqual((pages, count), (1, 10))
        primary_mock.assert_called_once_with("scanned cover page", None)

    def test_unqualified_identity_mismatch_still_fails_closed(self):
        record = {
            "company": "Transrail Lighting Limited",
            "openDate": "2024-12-19",
            "closeDate": "2024-12-23",
        }
        doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1752651007576_865.pdf",
            "filedDate": "2025-07-16",
        }

        with (
            patch.object(runner.base, "pdf_bytes", return_value=b"%PDF-test"),
            patch.object(runner.parser, "extract_pdf_text", return_value=("some other issuer", 1, 10)),
        ):
            with self.assertRaisesRegex(ValueError, "Issuer identity not confirmed"):
                runner.extract(record, doc)


if __name__ == "__main__":
    unittest.main()
