import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_identity as identity
import run_offer_documents as runner


class FinalProspectusIdentityTests(unittest.TestCase):
    def test_happy_steels_archive_url_is_strong_official_identity(self):
        record = {"company": "Happy Steels Limited", "openDate": "2026-07-09"}
        doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://nsearchives.nseindia.com/emerge/corporates/content/HappySteelsLimited_PROSP.pdf",
            "filedDate": "2026-07-14",
        }
        self.assertGreaterEqual(identity.official_identity_score(record, doc), 3)
        self.assertTrue(identity.official_identity_confirmed(record, doc))

    def test_stale_generic_sebi_attachment_is_not_a_candidate(self):
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
        self.assertEqual(identity.date_status(record, doc), "implausible")
        self.assertEqual(identity.official_identity_score(record, doc), 0)
        self.assertFalse(identity.candidate_acceptable(record, doc))
        self.assertIsNone(identity.choose_candidate(record, [doc]))

    def test_issuer_specific_official_page_can_rescue_observational_date(self):
        record = {
            "company": "Transrail Lighting Limited",
            "openDate": "2024-12-19",
            "closeDate": "2024-12-23",
        }
        doc = {
            "type": "PROSPECTUS",
            "title": "Transrail Lighting Limited - Prospectus",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1752651007576_865.pdf",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/jul-2025/transrail-lighting-limited-prospectus.html",
            "filedDate": "2025-07-16",
        }
        self.assertGreater(identity.official_identity_score(record, doc), 0)
        self.assertTrue(identity.candidate_acceptable(record, doc))

    def test_candidate_choice_prefers_issuer_identity_over_generic_recency(self):
        record = {"company": "Example Industries Limited", "openDate": "2026-08-01"}
        generic = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/999999.pdf",
            "filedDate": "2026-08-10",
        }
        issuer_specific = {
            "type": "PROSPECTUS",
            "title": "Example Industries Limited - Prospectus",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/888888.pdf",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/aug-2026/example-industries-limited-prospectus.html",
            "filedDate": "2026-08-08",
        }
        self.assertIs(identity.choose_candidate(record, [generic, issuer_specific]), issuer_specific)

    def test_previous_failed_candidate_rotates_to_other_eligible_final_prospectus(self):
        failed = {
            "type": "PROSPECTUS",
            "title": "Example Industries Limited - Prospectus",
            "url": "https://www.bseindia.com/downloads/ipo/example-primary.pdf",
            "filedDate": "2026-08-10",
        }
        alternate = {
            "type": "PROSPECTUS",
            "title": "Example Industries Limited - Prospectus",
            "url": "https://nsearchives.nseindia.com/corporate/FP_EXAMPLE_08AUG2026.pdf",
            "filedDate": "2026-08-08",
        }
        record = {
            "company": "Example Industries Limited",
            "openDate": "2026-08-01",
            "documentRepair": {
                "status": "source_blocked",
                "sourceUrl": failed["url"],
            },
        }

        self.assertIs(identity.choose_candidate(record, [failed, alternate]), alternate)

    def test_only_failed_candidate_remains_retryable(self):
        failed = {
            "type": "PROSPECTUS",
            "title": "Example Industries Limited - Prospectus",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/example.pdf",
            "filedDate": "2026-08-08",
        }
        record = {
            "company": "Example Industries Limited",
            "openDate": "2026-08-01",
            "documentRepair": {
                "status": "parse_failed",
                "sourceUrl": failed["url"],
            },
        }

        self.assertIs(identity.choose_candidate(record, [failed]), failed)

    def test_runner_uses_official_identity_when_pdf_opening_text_is_lossy(self):
        record = {"company": "Happy Steels Limited", "openDate": "2026-07-09", "priceBand": None}
        doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://nsearchives.nseindia.com/emerge/corporates/content/HappySteelsLimited_PROSP.pdf",
            "filedDate": "2026-07-14",
        }
        with (
            patch.object(runner, "pdf_bytes", return_value=b"%PDF-test"),
            patch.object(runner.parser, "extract_pdf_text", return_value=("scanned cover page", 1, 10)),
            patch.object(runner.parser, "parse_document_text", return_value={"extractedFields": []}) as parse_mock,
        ):
            parsed, digest, pages, count = runner.extract(record, doc)
        self.assertEqual(parsed, {"extractedFields": []})
        self.assertEqual(pages, 1)
        self.assertEqual(count, 10)
        self.assertTrue(digest)
        parse_mock.assert_called_once()

    def test_runner_still_rejects_unqualified_identity_mismatch(self):
        record = {"company": "Transrail Lighting Limited", "openDate": "2024-12-19", "closeDate": "2024-12-23"}
        doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1752651007576_865.pdf",
            "filedDate": "2025-07-16",
        }
        with (
            patch.object(runner, "pdf_bytes", return_value=b"%PDF-test"),
            patch.object(runner.parser, "extract_pdf_text", return_value=("some other issuer", 1, 10)),
        ):
            with self.assertRaisesRegex(ValueError, "Issuer identity not confirmed"):
                runner.extract(record, doc)


if __name__ == "__main__":
    unittest.main()
