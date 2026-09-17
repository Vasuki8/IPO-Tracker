"""Mixed fresh/OFS seller lists must be complete, quoted and independently consistent."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_parser as parser
from issue_composition_checks import composition_problems


EXPECTED = {
    "freshShares": 98_795_483,
    "ofsShares": 34_845_069,
    "freshIssueCr": 2143.862,
    "ofsCr": 756.138,
    "totalIssueSizeCr": 2900.0,
    "valuationPriceUsed": 217.0,
}
FIRST = (
    "17,422,535 EQUITY SHARES^ OF FACE VALUE OF ₹2 EACH AGGREGATING TO "
    "₹3,780.69 MILLION BY MANJUNATHA DONTHI VENKATARATHNAIAH"
)
SECOND = (
    "17,422,534 EQUITY SHARES^ OF FACE VALUE OF ₹2 EACH AGGREGATING TO "
    "₹3,780.69 MILLION BY SHUBHA MANJUNATHA DONTHI"
)


class FinalMixedOFSSellerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "tests/fixtures/issue_composition/emmvee-final-offer.txt").read_text()
        cls.cover, cls.definitions = (" ".join(page.split()) for page in cls.source.split("\f"))

    def assert_unresolved_cover(self, cover):
        # Agreement elsewhere cannot rescue an incomplete or contradictory
        # cover, nor can omitting that independent definition accept a prefix.
        for text in (cover, cover + "\f" + self.definitions):
            with self.subTest(independent_definition="[PAGE 11]" in text):
                self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_exact_source_repairs_composition_with_complete_seller_evidence(self):
        parsed = parser.parse_document_text(self.source)
        self.assertEqual(parsed["finalProspectusParserVersion"], 32)
        self.assertEqual(parsed["issuePrice"], 217.0)
        self.assertEqual(parsed["issueComposition"], EXPECTED)
        self.assertIn("issueComposition", parsed["extractedFields"])
        self.assertEqual(composition_problems(parsed["issueComposition"]), [])
        proof = parsed["fieldEvidence"]["issueComposition"]
        self.assertEqual(proof["totalShares"], 133_640_552)
        self.assertEqual(proof["page"], 3)
        for field in ("ofsShares", "ofsCr"):
            evidence = proof["fields"][field]
            self.assertEqual(evidence["page"], 3)
            self.assertEqual(evidence["normalizedValue"], EXPECTED[field])
            self.assertIn("sum of complete named OFS seller clauses", evidence["basis"])
            self.assertIn(FIRST, evidence["row"])
            self.assertIn(SECOND, evidence["row"])
            self.assertIn('THE “PROMOTER SELLING SHAREHOLDERS”', evidence["row"])
            self.assertNotIn("THE FACE VALUE", evidence["row"])
        self.assertIn("98,795,483 EQUITY SHARES^", proof["fields"]["freshShares"]["row"])
        self.assertIn("₹21,438.62 MILLION", proof["fields"]["freshIssueCr"]["row"])
        self.assertIn("₹29,000.00 MILLION", proof["fields"]["totalIssueSizeCr"]["row"])

    def test_cover_sum_and_independent_aggregate_agree(self):
        cover, _ = parser.extract_final_issue_composition(self.cover)
        defined, evidence = parser.extract_final_issue_composition(self.definitions)
        self.assertEqual(cover, EXPECTED)
        self.assertEqual(defined["ofsShares"], cover["ofsShares"])
        self.assertEqual(defined["ofsCr"], cover["ofsCr"])
        self.assertEqual(evidence["issueComposition"]["fields"]["ofsShares"]["page"], 11)
        self.assertIn("34,845,069", evidence["issueComposition"]["fields"]["ofsShares"]["row"])
        self.assertEqual(parser.extract_final_issue_composition(self.source + "\f" + self.source)[0], EXPECTED)

    def test_missing_seller_cannot_be_replaced_by_a_first_seller_prefix(self):
        self.assert_unresolved_cover(self.cover.replace(" AND " + SECOND, ""))
        self.assert_unresolved_cover(self.cover.replace(FIRST + " AND ", ""))

    def test_every_seller_requires_explicit_named_ownership(self):
        for original in (FIRST, SECOND):
            owner = original.split(" BY ")[1]
            for replacement in (owner, "BY", "BY ELIGIBLE EMPLOYEES", "BY OUR COMPANY", "BY THE PROMOTER SELLING SHAREHOLDERS"):
                with self.subTest(seller=owner, replacement=replacement):
                    altered = original.replace("BY " + owner, replacement)
                    self.assert_unresolved_cover(self.cover.replace(original, altered))

    def test_every_seller_requires_its_own_complete_quoted_amount(self):
        for original in (FIRST, SECOND):
            for replacement in ("", "AGGREGATING TO ₹[●] MILLION ", "AGGREGATING TO ₹3,780.69 "):
                with self.subTest(seller=original, replacement=replacement):
                    altered = original.replace("AGGREGATING TO ₹3,780.69 MILLION ", replacement)
                    self.assert_unresolved_cover(self.cover.replace(original, altered))

    def test_changed_seller_counts_and_amounts_reject_the_complete_candidate(self):
        for original, altered in (
            (FIRST, FIRST.replace("17,422,535", "17,422,536")),
            (SECOND, SECOND.replace("17,422,534", "17,422,533")),
            (FIRST, FIRST.replace("₹3,780.69", "₹4,780.69")),
            (SECOND, SECOND.replace("₹3,780.69", "₹2,780.69")),
        ):
            with self.subTest(altered=altered):
                self.assert_unresolved_cover(self.cover.replace(original, altered))

    def test_missing_or_malformed_seller_quantity_stays_unresolved(self):
        for replacement in ("17,422,534 SHARES^", "[●] EQUITY SHARES^", "17,422,534 EQUITY SHARES^^"):
            with self.subTest(replacement=replacement):
                self.assert_unresolved_cover(self.cover.replace("17,422,534 EQUITY SHARES^", replacement))

    def test_post_share_caret_is_supported_without_broad_footnote_consumption(self):
        self.assertEqual(parser.extract_final_issue_composition(self.cover.replace("EQUITY SHARES^", "EQUITY SHARES"))[0], EXPECTED)
        for marker in ("*", "#", "^^", "^NOTE"):
            with self.subTest(marker=marker):
                altered = SECOND.replace("EQUITY SHARES^", "EQUITY SHARES" + marker)
                self.assert_unresolved_cover(self.cover.replace(SECOND, altered))

    def test_a_full_ofs_first_seller_cannot_hide_additional_or_incomplete_sellers(self):
        full_first = FIRST.replace("17,422,535", "34,845,069").replace("₹3,780.69", "₹7,561.38")
        cover = self.cover.replace(FIRST, full_first)
        for text in (
            cover,
            cover.replace(full_first, full_first + " INCLUDING"),
            cover.replace(full_first, full_first + ' (THE “OFFER FOR SALE”)'),
            cover.replace("17,422,534 EQUITY SHARES^", "17,422,534 SHARES^"),
            cover.replace(SECOND, "BY SHUBHA MANJUNATHA DONTHI"),
            cover.replace("AGGREGATING TO ₹29,000.00 MILLION ", ""),
            cover.replace("AGGREGATING TO ₹21,438.62 MILLION ", ""),
        ):
            with self.subTest(text=text):
                self.assert_unresolved_cover(text)

    def test_reservations_pre_ipo_and_sentence_breaks_cannot_complete_a_seller_list(self):
        for separator in (
            ". ", "; ", ". ANOTHER TRANSACTION INVOLVED ",
            " AND A PRE-IPO PLACEMENT OF ", " AND A RESERVATION OF ",
            ". THE OFFER INCLUDED A RESERVATION OF ",
        ):
            with self.subTest(separator=separator):
                self.assert_unresolved_cover(self.cover.replace(" AND " + SECOND, separator + SECOND))
        for phrase in ("FOR SUBSCRIPTION ", "RESERVED FOR PURCHASE ", "FOR ALLOTMENT "):
            with self.subTest(phrase=phrase):
                altered = SECOND.replace("BY SHUBHA", phrase + "BY SHUBHA")
                self.assert_unresolved_cover(self.cover.replace(SECOND, altered))

    def test_initial_total_and_fresh_amounts_must_be_explicit_and_consistent(self):
        for original, replacement in (
            ("AGGREGATING TO ₹29,000.00 MILLION ", ""),
            ("AGGREGATING TO ₹21,438.62 MILLION ", ""),
            ("133,640,552", "133,640,553"),
            ("₹29,000.00", "₹39,000.00"),
            ("98,795,483", "98,795,484"),
            ("₹21,438.62", "₹11,438.62"),
        ):
            with self.subTest(original=original, replacement=replacement):
                self.assert_unresolved_cover(self.cover.replace(original, replacement))

    def test_independently_quoted_aggregate_and_total_conflicts_remain_unresolved(self):
        for original, replacement in (
            ("34,845,069", "34,845,070"),
            ("₹7,561.38", "₹7,561.39"),
            ("133,640,552", "133,640,553"),
            ("₹29,000.00", "₹29,000.01"),
        ):
            with self.subTest(original=original, replacement=replacement):
                terms = self.definitions.replace(original, replacement)
                self.assertEqual(parser.extract_final_issue_composition(self.cover + "\f" + terms), (None, {}))

    def test_separate_repeated_component_clauses_are_still_observed(self):
        for repeated in (
            "OFFER FOR SALE OF 17,422,535 EQUITY SHARES AGGREGATING TO ₹378.069 CRORE. ",
            "OFFER FOR SALE OF 34,845,069 EQUITY SHARES AGGREGATING TO ₹756.139 CRORE. ",
            "FRESH ISSUE OF 98,795,484 EQUITY SHARES AGGREGATING TO ₹2143.862 CRORE. ",
        ):
            with self.subTest(repeated=repeated):
                self.assert_unresolved_cover(self.cover.replace("THE FACE VALUE OF EQUITY SHARES IS", repeated + "THE FACE VALUE OF EQUITY SHARES IS"))

    def offer(self, sellers=None, *, discount=False):
        if sellers is None:
            sellers = (
                "1,000,000 EQUITY SHARES^ AGGREGATING TO ₹10 CRORE BY ALPHA LIMITED, "
                "2,000,000 EQUITY SHARES^ AGGREGATING TO ₹20 CRORE BY BETA LIMITED AND "
                "3,000,000 EQUITY SHARES^ AGGREGATING TO ₹30 CRORE BY GAMMA LIMITED."
            )
        text = (
            "[PAGE 3] ISSUE PRICE IS ₹100 PER EQUITY SHARE. "
            "INITIAL PUBLIC OFFER OF 10,000,000 EQUITY SHARES AGGREGATING TO ₹100 CRORE "
            "COMPRISING A FRESH ISSUE OF 4,000,000 EQUITY SHARES AGGREGATING TO ₹40 CRORE "
            "BY OUR COMPANY AND AN OFFER FOR SALE OF " + sellers
        )
        if discount:
            text = "An employee discount applies. " + text.replace("₹100 CRORE", "₹98 CRORE").replace("₹30 CRORE", "₹28 CRORE")
        return text

    def test_generic_named_list_can_have_three_sellers_or_one_complete_seller(self):
        expected = {
            "freshShares": 4_000_000, "ofsShares": 6_000_000,
            "freshIssueCr": 40.0, "ofsCr": 60.0, "totalIssueSizeCr": 100.0,
            "valuationPriceUsed": 100.0,
        }
        single = "6,000,000 EQUITY SHARES^ AGGREGATING TO ₹60 CRORE BY ALPHA LIMITED."
        for text in (self.offer(), self.offer(single)):
            with self.subTest(text=text):
                self.assertEqual(parser.extract_final_issue_composition(text)[0], expected)

    def test_unrelated_quantities_after_a_complete_list_do_not_join_its_sum(self):
        text = self.offer() + (
            " THE OFFER INCLUDED A RESERVATION OF 100,000 EQUITY SHARES "
            "AGGREGATING TO ₹1 CRORE FOR EMPLOYEES."
        )
        composition, evidence = parser.extract_final_issue_composition(text)
        self.assertEqual(composition["ofsShares"], 6_000_000)
        self.assertEqual(composition["ofsCr"], 60.0)
        self.assertNotIn("100,000", evidence["issueComposition"]["fields"]["ofsShares"]["row"])

    def test_quoted_discounted_seller_amounts_preserve_discount_behavior(self):
        composition, evidence = parser.extract_final_issue_composition(self.offer(discount=True))
        self.assertEqual(composition["ofsShares"], 6_000_000)
        self.assertEqual(composition["ofsCr"], 58.0)
        self.assertEqual(composition["totalIssueSizeCr"], 98.0)
        self.assertNotIn("valuationPriceUsed", composition)
        self.assertNotIn("valuationPriceUsed", evidence["issueComposition"]["fields"])


if __name__ == "__main__":
    unittest.main()
