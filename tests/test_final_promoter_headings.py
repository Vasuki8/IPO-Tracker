"""Final promoter lists must stay complete across cover and definition layouts."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import final_prospectus_parser as parser
import p4_offer_layouts as residual


# Cover headings and wrapped glossary rows from the issuer Final Prospectuses.
# Sunshine: FinalSunshineProspectus-GYR.pdf, August 21, 2026.
# Orkla: Orkla-India-Limited-Prospectus.pdf, October 31, 2025.
SUNSHINE = """[PAGE 1]
SUNSHINE PICTURES LIMITED
OUR PROMOTERS: VIPUL AMRUTLAL SHAH, SHEFALI VIPUL SHAH, ARYAMAN VIPUL SHAH AND MAURYA VIPUL SHAH
DETAILS OF THE OFFER TO THE PUBLIC
DETAILS OF THE SELLING SHAREHOLDERS
Vipul Amrutlal Shah       Promoter Selling Shareholder
Shefali Vipul Shah        Promoter Selling Shareholder
\f[PAGE 5]
DEFINITIONS AND ABBREVIATIONS
“Promoter(s)”    The Promoters of our Company, being Vipul Amrutlal Shah, Shefali Vipul Shah,
                Aryaman Vipul Shah and Maurya Vipul Shah. For further details, see “Our Promoters
                and Promoter Group” on page 245.
"""
SUNSHINE_NAMES = ["VIPUL AMRUTLAL SHAH", "SHEFALI VIPUL SHAH", "ARYAMAN VIPUL SHAH", "MAURYA VIPUL SHAH"]

ORKLA = """[PAGE 1]
ORKLA INDIA LIMITED
OUR PROMOTERS: ORKLA ASA, ORKLA ASIA HOLDING AS AND ORKLA ASIA PACIFIC PTE. LTD.
DETAILS OF THE OFFER TO PUBLIC
DETAILS OF THE SELLING SHAREHOLDERS
Orkla Asia Pacific Pte. Ltd.       Promoter Selling Shareholder
Navas Meeran                      Other Selling Shareholder
Feroz Meeran                      Other Selling Shareholder
\f[PAGE 5]
DEFINITIONS AND ABBREVIATIONS
Promoters    The Promoters of our Company, being, Orkla ASA, Orkla Asia Holding AS and Orkla
             Asia Pacific Pte. Ltd. For further details, see “Our Promoters and Promoter Group – Our
             Promoters” on page 254
"""
ORKLA_NAMES = ["ORKLA ASA", "ORKLA ASIA HOLDING AS", "ORKLA ASIA PACIFIC PTE. LTD."]


class FinalPromoterHeadingTests(unittest.TestCase):
    def test_sunshine_complete_cover_list_outranks_wrapped_definition_and_seller_subset(self):
        names, evidence = parser.extract_final_promoters(SUNSHINE)
        self.assertEqual(names, SUNSHINE_NAMES)
        self.assertEqual(evidence["promoters"]["page"], 1)
        self.assertEqual(evidence["promoters"]["entities"], names)
        self.assertEqual(evidence["promoters"]["method"], "bounded-promoter-heading-v1")
        self.assertTrue(all("being" not in name.casefold() for name in names))

    def test_orkla_corporate_legal_forms_and_final_entity_are_preserved(self):
        names, evidence = parser.extract_final_promoters(ORKLA)
        self.assertEqual(names, ORKLA_NAMES)
        self.assertEqual(evidence["promoters"]["page"], 1)
        self.assertIn("PTE. LTD.", evidence["promoters"]["rows"][0])

    def test_same_cover_names_on_multiple_pages_are_not_a_conflict(self):
        first = ORKLA.split("\f")[0]
        names, evidence = parser.extract_final_promoters(first + "\f" + first.replace("[PAGE 1]", "[PAGE 3]"))
        self.assertEqual(names, ORKLA_NAMES)
        self.assertEqual(evidence["promoters"]["page"], 1)

    def test_wrapped_person_and_entity_names_are_joined_within_the_heading(self):
        text = """[PAGE 3]
OUR PROMOTERS: ALPHA BETA, GAMMA DELTA AND EXAMPLE HOLDINGS
PRIVATE LIMITED
INITIAL PUBLIC OFFER OF 10,000 EQUITY SHARES
"""
        names, evidence = parser.extract_final_promoters(text)
        self.assertEqual(names, ["ALPHA BETA", "GAMMA DELTA", "EXAMPLE HOLDINGS PRIVATE LIMITED"])
        self.assertEqual(evidence["promoters"]["page"], 3)
        self.assertEqual(len(evidence["promoters"]["rows"]), 2)

    def test_existing_person_sentence_and_legacy_heading_layouts_remain_supported(self):
        cases = [
            ("NAMES OF PROMOTERS OF THE COMPANY\nThe Promoters of our Company are being Mr. Kamleshkumar Jayantilal Patel, Mr. Alpeshbhai Jayantilal Patel and Mr. Meet Kamleshkumar Patel.\nDETAILS OF THE ISSUE",
             ["Kamleshkumar Jayantilal Patel", "Alpeshbhai Jayantilal Patel", "Meet Kamleshkumar Patel"]),
            ("OUR PROMOTERS\nPromoters of Our Company are Mr. Anuj Dosajh, Mr. Ramakrishnan Balasundaram Aiyer, Mr. Ajay Raina and Mr. Lalit Mohan Datta. For details of our Promoters please see page 181.\nDETAILS OF THE ISSUE",
             ["Anuj Dosajh", "Ramakrishnan Balasundaram Aiyer", "Ajay Raina", "Lalit Mohan Datta"]),
            ("THE PROMOTERS OF OUR COMPANY\nALPHA SHAH, BETA SHAH AND EXAMPLE HOLDINGS PRIVATE LIMITED\nDETAILS OF THE ISSUE",
             ["ALPHA SHAH", "BETA SHAH", "EXAMPLE HOLDINGS PRIVATE LIMITED"]),
            ("OUR PROMOTERS\nOur Promoters are ARUN KUMAR, BINA KUMAR and EXAMPLE HOLDINGS PRIVATE LIMITED.\nISSUE DETAILS",
             ["ARUN KUMAR", "BINA KUMAR", "EXAMPLE HOLDINGS PRIVATE LIMITED"]),
        ]
        for text, expected in cases:
            with self.subTest(heading=text.splitlines()[0]):
                self.assertEqual(parser.extract_final_promoters(text)[0], expected)

    def test_numeric_corporate_names_and_long_person_names_remain_supported(self):
        text = """OUR PROMOTERS: C2C INNOVATIONS PRIVATE LIMITED, PVR MULTIMEDIA PRIVATE LIMITED, LAKSHMI CHANDRA, MAYA CHANDRA, SUBRAHMANYA SRINIVASA NARENDRA LANKA, KURIYEDATH RAMESH AND MURTAZA ALI SOOMAR
DETAILS OF THE ISSUE
"""
        self.assertEqual(parser.extract_final_promoters(text)[0], [
            "C2C INNOVATIONS PRIVATE LIMITED", "PVR MULTIMEDIA PRIVATE LIMITED", "LAKSHMI CHANDRA",
            "MAYA CHANDRA", "SUBRAHMANYA SRINIVASA NARENDRA LANKA", "KURIYEDATH RAMESH", "MURTAZA ALI SOOMAR",
        ])

    def test_conflicting_complete_cover_lists_fail_closed(self):
        text = "OUR PROMOTERS: ALPHA BETA AND GAMMA DELTA\nDETAILS OF THE ISSUE\fOUR PROMOTERS: ALPHA BETA AND OTHER PERSON\nDETAILS OF THE ISSUE"
        self.assertEqual(parser.extract_final_promoters(text), ([], {}))
        parsed = parser.parse_document_text(text)
        self.assertFalse(parsed.get("promoters"))
        self.assertNotIn("promoters", parsed["extractedFields"])
        self.assertNotIn("promoters", parsed["fieldEvidence"])

    def test_one_junk_fragment_rejects_the_whole_list_instead_of_returning_a_subset(self):
        for names in ("being, ALPHA BETA AND Mr", "ALPHA BETA, ORKLA AND GAMMA DELTA", "ALPHA BETA AND 2,000 Equity Shares"):
            with self.subTest(names=names):
                text = "OUR PROMOTERS: " + names + "\nDETAILS OF THE ISSUE"
                self.assertEqual(parser.extract_final_promoters(text), ([], {}))

    def test_page_end_cannot_truncate_a_list_that_continues_on_the_next_page(self):
        text = "OUR PROMOTERS: JOHN DOE AND JANE SMITH\fAND JAMES BLACK\nINITIAL PUBLIC OFFER"
        self.assertEqual(parser.extract_final_promoters(text), ([], {}))

    def test_singular_corporate_heading_preserves_and_inside_the_entity(self):
        text = "OUR PROMOTER: JOHN DOE AND SONS LIMITED\nINITIAL PUBLIC OFFER"
        self.assertEqual(parser.extract_final_promoters(text)[0], ["JOHN DOE AND SONS LIMITED"])
        ambiguous = "OUR PROMOTER: JOHN DOE AND JANE SMITH\nINITIAL PUBLIC OFFER"
        self.assertEqual(parser.extract_final_promoters(ambiguous), ([], {}))

    def test_ambiguous_corporate_and_boundaries_cannot_split_or_combine_entities(self):
        cases = [
            "OUR PROMOTERS: JOHN DOE AND SONS LIMITED AND JANE SMITH\nINITIAL PUBLIC OFFER",
            "OUR PROMOTER: ABC LIMITED AND XYZ LIMITED\nINITIAL PUBLIC OFFER",
        ]
        for text in cases:
            with self.subTest(heading=text.splitlines()[0]):
                self.assertEqual(parser.extract_final_promoters(text), ([], {}))

    def test_undelimited_complete_name_rows_cannot_be_joined_as_one_person(self):
        text = "OUR PROMOTERS\nJohn Doe\nJane Smith\nDETAILS OF THE OFFER"
        self.assertEqual(parser.extract_final_promoters(text), ([], {}))

    def test_contents_and_promoter_group_headings_are_not_name_lists(self):
        text = """TABLE OF CONTENTS
OUR PROMOTERS ...................................... 181
OUR PROMOTERS AND PROMOTER GROUP
ALPHA BETA AND GAMMA DELTA
DETAILS OF THE ISSUE
"""
        self.assertEqual(parser.extract_final_promoters(text), ([], {}))

    def test_heading_cannot_borrow_names_from_a_different_page_or_unbounded_block(self):
        cases = [
            "OUR PROMOTERS\fALPHA BETA AND GAMMA DELTA\nDETAILS OF THE ISSUE",
            "OUR PROMOTERS\n" + "ALPHA BETA,\n" * 10 + "GAMMA DELTA\nDETAILS OF THE ISSUE",
            "\f".join(["Unrelated page"] * 12 + ["OUR PROMOTERS: ALPHA BETA AND GAMMA DELTA\nDETAILS OF THE ISSUE"]),
        ]
        for text in cases:
            with self.subTest(length=len(text)):
                self.assertEqual(parser.extract_final_promoters(text), ([], {}))

    def test_unsupported_definition_cannot_keep_legacy_value_evidence_or_recognition(self):
        legacy = {"promoters": ["being", "Orkla"], "fieldEvidence": {"promoters": {"heading": "Legacy definition"}}, "extractedFields": ["promoters"]}
        with patch.object(parser.base, "parse_document_text", return_value=copy.deepcopy(legacy)):
            parsed = parser.parse_document_text("DEFINITIONS\nPromoters    The Promoters of our Company, being, Orkla")
        self.assertFalse(parsed.get("promoters"))
        self.assertNotIn("promoters", parsed["fieldEvidence"])
        self.assertNotIn("promoters", parsed["extractedFields"])
        self.assertEqual(parsed["finalPromoterAssessment"], "unresolved")

    def test_full_parser_and_residual_merge_keep_complete_source_names_and_proof(self):
        for text, expected in ((SUNSHINE, SUNSHINE_NAMES), (ORKLA, ORKLA_NAMES)):
            with self.subTest(issuer=expected[0]):
                parsed = parser.parse_document_text(text)
                merged = residual.merge_parsed(parsed, residual.parse_document_text(text))
                self.assertEqual(merged["promoters"], expected)
                self.assertEqual(merged["fieldEvidence"]["promoters"], parsed["fieldEvidence"]["promoters"])
                self.assertIn("promoters", merged["extractedFields"])
                self.assertEqual(parsed["finalPromoterAssessment"], "accepted")

    def test_residual_cannot_refill_a_rejected_list_but_can_supply_other_fields(self):
        text = "OUR PROMOTERS: ALPHA BETA AND GAMMA DELTA\nDETAILS OF THE ISSUE\fOUR PROMOTERS: ALPHA BETA AND OTHER PERSON\nDETAILS OF THE ISSUE"
        primary = parser.parse_document_text(text)
        supplement = residual.parse_document_text(text)
        self.assertTrue(supplement["promoters"])
        supplement.update(registrar="Valid Registrar Limited")
        merged = residual.merge_parsed(primary, supplement)
        self.assertFalse(merged.get("promoters"))
        self.assertNotIn("promoters", merged["fieldEvidence"])
        self.assertNotIn("promoters", merged["extractedFields"])
        self.assertEqual(merged["registrar"], "Valid Registrar Limited")

    def test_residual_compatibility_without_final_assessment_is_preserved(self):
        supplement = {"promoters": ["Alpha Beta"], "fieldEvidence": {"promoters": {"heading": "OUR PROMOTERS"}}}
        merged = residual.merge_parsed({}, supplement)
        self.assertEqual(merged["promoters"], ["Alpha Beta"])
        self.assertEqual(merged["fieldEvidence"]["promoters"], supplement["fieldEvidence"]["promoters"])

    def test_parser_version_schedules_semantic_promoter_revalidation(self):
        self.assertEqual(parser.PARSER_VERSION, parser.base.PARSER_VERSION + 7)


if __name__ == "__main__":
    unittest.main()
