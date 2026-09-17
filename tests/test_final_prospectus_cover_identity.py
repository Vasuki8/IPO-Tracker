import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_identity as identity
import run_offer_documents as primary
import run_p4_offer_residuals as residual


# The Happy NSE archive route actually served this Laser cover in source QA.
# Keep the observed legal title and its adjacent CIN label together: the URL
# and official metadata alone incorrectly accepted this PDF for Happy.
LASER_COVER = """[PAGE 1]
(Please scan this QR code to view this
Prospectus and the Abridged Prospectus)

      LASER POWER & INFRA LIMITED

CORPORATE IDENTITY NUMBER: U14220WB1988PLC043591

REGISTERED OFFICE CORPORATE OFFICE CONTACT PERSON TELEPHONE AND E-MAIL WEBSITE
4A, Pollock Street, 3rd Floor
Kolkata 700 001
OUR PROMOTERS: DEEPAK GOEL, DEVESH GOEL, AKSHAT GOEL AND RAKHI GOEL
DETAILS OF THE OFFER
"""
# Same cover extracted with the production Poppler -layout -fixed 3 flags.
LASER_LAYOUT_COVER = """[PAGE 1]
                                                                                                                                                                               PROSPECTUS
                                                                                                                                                                           Dated July 13, 2026
                                                                                                                                        (Please read Section 26 of the Companies Act, 2013)
                                                                                                                                                                      100% Book Built Offer



        (Please scan this QR code to view this                          LASER POWER & INFRA LIMITED
      Prospectus and the Abridged Prospectus)
                                                         CORPORATE IDENTITY NUMBER: U14220WB1988PLC043591
         REGISTERED OFFICE                      CORPORATE OFFICE                     CONTACT PERSON                     TELEPHONE AND E-MAIL                              WEBSITE
"""
HAPPY = {"company": "Happy Steels Limited", "openDate": "2026-07-09", "priceBand": None}
HAPPY_DOC = {
    "type": "PROSPECTUS",
    "title": "Happy Steels Limited - Final Prospectus",
    "company": "Happy Steels Limited",
    "url": "https://nsearchives.nseindia.com/emerge/corporates/content/HappySteelsLimited_PROSP.pdf",
    "filedDate": "2026-07-14",
}


class CoverIssuerIdentityTests(unittest.TestCase):
    def test_actual_cover_contradicts_matching_official_happy_metadata(self):
        self.assertTrue(identity.official_identity_confirmed(HAPPY, HAPPY_DOC))
        self.assertEqual(identity.explicit_cover_issuers(LASER_COVER), ["LASER POWER & INFRA LIMITED"])
        self.assertEqual(identity.contradictory_cover_issuer(HAPPY, LASER_COVER), "LASER POWER & INFRA LIMITED")

    def test_actual_cover_matches_correct_laser_issuer(self):
        self.assertIsNone(identity.contradictory_cover_issuer({"company": "Laser Power & Infra Limited"}, LASER_COVER))

    def test_actual_layout_cover_ignores_qr_caption_beside_issuer_title(self):
        self.assertEqual(identity.explicit_cover_issuers(LASER_LAYOUT_COVER), ["LASER POWER & INFRA LIMITED"])
        self.assertEqual(identity.contradictory_cover_issuer(HAPPY, LASER_LAYOUT_COVER), "LASER POWER & INFRA LIMITED")
        self.assertIsNone(identity.contradictory_cover_issuer({"company": "Laser Power & Infra Limited"}, LASER_LAYOUT_COVER))

    def test_spacing_ampersand_and_legal_abbreviation_preserve_identity(self):
        cover = "\n  Laser   Power  AND  Infra  Ltd.  \n  CIN : U14220WB1988PLC043591\n"
        self.assertEqual(identity.explicit_cover_issuers(cover), ["Laser Power AND Infra Ltd."])
        self.assertIsNone(identity.contradictory_cover_issuer({"company": "Laser Power & Infra Limited"}, cover))

    def test_registered_office_label_can_anchor_a_cover_title(self):
        cover = "\nLASER POWER & INFRA LIMITED\nRegistered Office: 4A, Pollock Street\n"
        self.assertEqual(identity.contradictory_cover_issuer(HAPPY, cover), "LASER POWER & INFRA LIMITED")

    def test_former_name_annotation_does_not_replace_current_title(self):
        cover = "\nORKLA INDIA LIMITED\n(Formerly known as MTR Foods Private Limited)\nCORPORATE IDENTITY NUMBER: U15136KA1996PLC021007\n"
        self.assertEqual(identity.explicit_cover_issuers(cover), ["ORKLA INDIA LIMITED"])
        self.assertIsNone(identity.contradictory_cover_issuer({"company": "Orkla India Limited"}, cover))
        self.assertEqual(identity.contradictory_cover_issuer({"company": "MTR Foods Private Limited"}, cover), "ORKLA INDIA LIMITED")

    def test_title_with_explicit_line_continuation_is_joined(self):
        for title in ("LASER POWER &\nINFRA LIMITED", "LASER POWER & INFRA\nLIMITED"):
            with self.subTest(title=title):
                cover = "\n" + title + "\nCORPORATE IDENTITY NUMBER: U14220WB1988PLC043591\n"
                self.assertEqual(identity.explicit_cover_issuers(cover), ["LASER POWER & INFRA LIMITED"])

    def test_ambiguous_tagline_or_unpunctuated_wrapping_does_not_invent_a_contradiction(self):
        for title in ("A WORLD OF POSSIBILITIES\nHAPPY STEELS LIMITED", "HAPPY\nSTEELS LIMITED"):
            with self.subTest(title=title):
                cover = title + "\nCIN: U12345MH2000PLC123456\n"
                self.assertEqual(identity.explicit_cover_issuers(cover), [])
                self.assertIsNone(identity.contradictory_cover_issuer(HAPPY, cover))

    def test_intermediary_address_on_following_page_is_not_a_cover_issuer(self):
        cover = "HAPPY STEELS LIMITED\nCIN: U12345MH2000PLC123456\n"
        for role in ("LEAD MANAGER", "LEAD MANAGERS TO THE ISSUE", "BOOK RUNNING LEAD MANAGERS", "REGISTRAR TO THE ISSUE", "LEGAL ADVISORS", "BANKERS TO THE ISSUE", "AUDITORS"):
            with self.subTest(role=role):
                text = cover + "\f" + role + "\nEXAMPLE CAPITAL LIMITED\nREGISTERED OFFICE: Example Street\n"
                self.assertEqual(identity.explicit_cover_issuers(text), ["HAPPY STEELS LIMITED"])
                self.assertIsNone(identity.contradictory_cover_issuer(HAPPY, text))

    def test_body_company_names_and_addresses_after_cover_section_are_not_identity(self):
        text = "\nOUR PROMOTERS: JOHN DOE AND JANE SMITH\n\nEXAMPLE CAPITAL LIMITED\nRegistered Office: Example Street\n"
        self.assertEqual(identity.explicit_cover_issuers(text), [])

    def test_opaque_or_unanchored_text_keeps_metadata_fallback_available(self):
        for text in ("scanned cover page", "LASER POWER & INFRA LIMITED", "[PAGE 1]\nCORPORATE IDENTITY NUMBER: U14220WB1988PLC043591\n"):
            with self.subTest(text=text):
                self.assertIsNone(identity.contradictory_cover_issuer(HAPPY, text))

    def test_cover_scan_is_bounded_to_opening_pages(self):
        text = "opaque cover\fcontents\foffer summary\f" + LASER_COVER
        self.assertIsNone(identity.contradictory_cover_issuer(HAPPY, text))


class CoverIssuerRunnerTests(unittest.TestCase):
    def test_primary_and_residual_reject_wrong_cover_before_any_field_parser(self):
        for runner in (primary, residual):
            for cover in (LASER_COVER, LASER_LAYOUT_COVER):
                for incidental_mention in ("", "Happy Steels Limited is mentioned as an industry peer.\n"):
                    with self.subTest(runner=runner.__name__, layout=cover is LASER_LAYOUT_COVER, incidental=bool(incidental_mention)):
                        text = cover + incidental_mention
                        with (
                            patch.object(primary, "pdf_bytes", return_value=b"%PDF-mocked"),
                            patch.object(primary.parser, "extract_pdf_text", return_value=(text, 1, 535)),
                            patch.object(primary.parser, "parse_document_text") as parse_primary,
                            patch.object(residual.residual, "parse_document_text") as parse_residual,
                        ):
                            with self.assertRaisesRegex(ValueError, "cover issuer.*LASER POWER.*contradicts.*Happy Steels"):
                                runner.extract(HAPPY, HAPPY_DOC)
                        parse_primary.assert_not_called()
                        parse_residual.assert_not_called()

    def test_primary_and_residual_accept_correct_cover_without_metadata_hint(self):
        record = {"company": "Laser Power & Infra Limited", "priceBand": None}
        doc = {"type": "PROSPECTUS", "url": "https://nsearchives.nseindia.com/corporate/FP_INE17IR01028_14JUL2026.pdf"}
        self.assertFalse(identity.official_identity_confirmed(record, doc))
        for runner in (primary, residual):
            with self.subTest(runner=runner.__name__):
                parsed_value = {"issuePrice": 214.0, "extractedFields": ["issuePrice"]}
                with (
                    patch.object(primary, "pdf_bytes", return_value=b"%PDF-mocked"),
                    patch.object(primary.parser, "extract_pdf_text", return_value=(LASER_COVER, 1, 535)),
                    patch.object(primary.parser, "parse_document_text", return_value=parsed_value) as parse_primary,
                    patch.object(residual.residual, "parse_document_text", return_value={}),
                ):
                    parsed, digest, pages, count = runner.extract(record, doc)
                self.assertEqual(parsed["issuePrice"], 214.0)
                self.assertTrue(digest)
                self.assertEqual((pages, count), (1, 535))
                parse_primary.assert_called_once_with(LASER_COVER, None)

    def test_primary_and_residual_keep_opaque_cover_metadata_fallback(self):
        for runner in (primary, residual):
            with self.subTest(runner=runner.__name__):
                with (
                    patch.object(primary, "pdf_bytes", return_value=b"%PDF-mocked"),
                    patch.object(primary.parser, "extract_pdf_text", return_value=("scanned cover page", 1, 535)),
                    patch.object(primary.parser, "parse_document_text", return_value={"extractedFields": []}) as parse_primary,
                    patch.object(residual.residual, "parse_document_text", return_value={}),
                ):
                    parsed, digest, pages, count = runner.extract(HAPPY, HAPPY_DOC)
                self.assertEqual(parsed["extractedFields"], [])
                self.assertTrue(digest)
                self.assertEqual((pages, count), (1, 535))
                parse_primary.assert_called_once_with("scanned cover page", None)


if __name__ == "__main__":
    unittest.main()
