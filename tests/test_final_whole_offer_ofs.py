"""Whole-offer OFS definitions must not bind a seller or reservation quantity."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_parser as parser
import final_prospectus_policy as policy
from issue_composition_checks import COMPOSITION_FIELDS, composition_problems


class FinalWholeOfferOFSTests(unittest.TestCase):
    def source(self, issuer="orkla"):
        return (ROOT / f"tests/fixtures/issue_composition/{issuer}-final-offer.txt").read_text()

    def offer(self, *, total=10_000_000, amount="98", qualifier="THROUGH"):
        return (
            "[PAGE 3]\nISSUE PRICE IS ₹100 PER EQUITY SHARE\n"
            "An employee discount of ₹20 per Equity Share applies.\n"
            f"INITIAL PUBLIC OFFER OF {total:,} EQUITY SHARES "
            f"AGGREGATING TO ₹{amount} CRORE {qualifier} AN OFFER FOR SALE "
            '(THE "OFFER" OR "OFFER FOR SALE") OF 6,000,000 EQUITY SHARES '
            "BY ALPHA LIMITED AND 4,000,000 EQUITY SHARES BY BETA LIMITED.\n"
        )

    def test_actual_orkla_offer_preserves_quoted_aggregate_and_whole_offer_shares(self):
        composition, evidence = parser.extract_final_issue_composition(self.source())
        self.assertEqual(composition, {
            "freshShares": 0,
            "ofsShares": 22_843_004,
            "freshIssueCr": 0.0,
            "ofsCr": 1667.33,
            "totalIssueSizeCr": 1667.33,
        })
        self.assertEqual(composition_problems(composition), [])
        fields = evidence["issueComposition"]["fields"]
        for field, value in composition.items():
            self.assertEqual(fields[field]["normalizedValue"], value)
            self.assertEqual(fields[field]["page"], 3)
        for field in ("ofsShares", "ofsCr"):
            self.assertIn("22,843,004", fields[field]["row"])
            self.assertIn("THROUGH AN OFFER FOR SALE", fields[field]["row"])
            self.assertNotIn("20,560,768", fields[field]["row"])
            self.assertNotIn("30,000", fields[field]["row"])
        self.assertNotIn("valuationPriceUsed", composition)
        self.assertNotIn("valuationPriceUsed", fields)

    def test_seller_and_employee_quantities_do_not_replace_whole_offer(self):
        text = self.offer() + (
            "THE OFFER INCLUDED A RESERVATION OF 100,000 EQUITY SHARES "
            "AGGREGATING TO ₹0.8 CRORE FOR ELIGIBLE EMPLOYEES."
        )
        composition, _ = parser.extract_final_issue_composition(text)
        self.assertEqual(composition["ofsShares"], 10_000_000)
        self.assertEqual(composition["ofsCr"], 98.0)
        self.assertEqual(composition["freshShares"], 0)
        self.assertNotIn("valuationPriceUsed", composition)

    def test_actual_alias_before_through_keeps_initial_total_for_multiple_sellers(self):
        composition, evidence = parser.extract_final_issue_composition(self.source("sbifunds"))
        self.assertEqual(composition, {
            "freshShares": 0, "ofsShares": 170_956_631,
            "freshIssueCr": 0.0, "ofsCr": 9795.321, "totalIssueSizeCr": 9795.321,
        })
        fields = evidence["issueComposition"]["fields"]
        for field in ("ofsShares", "ofsCr"):
            self.assertIn("170,956,631", fields[field]["row"])
            self.assertNotIn("99,501,649", fields[field]["row"])
            self.assertEqual(fields[field]["page"], 3)
        self.assertNotIn("valuationPriceUsed", fields)

    def test_actual_single_seller_equal_to_whole_offer_remains_supported(self):
        composition, _ = parser.extract_final_issue_composition(self.source("vmm"))
        self.assertEqual(composition, {
            "freshShares": 0, "ofsShares": 1_025_641_025,
            "freshIssueCr": 0.0, "ofsCr": 8000.0, "totalIssueSizeCr": 8000.0,
            "valuationPriceUsed": 78.0,
        })

    def test_single_seller_equal_to_whole_offer_cannot_contradict_its_amount(self):
        text = self.source("vmm").replace(
            "₹80,000 MILLION BY SAMAYAT", "₹70,000 MILLION BY SAMAYAT",
        )
        self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_disclosed_seller_aggregates_must_match_the_quoted_whole_offer(self):
        for issuer, original, conflicting in (
            ("orkla", "₹15,007.5 MILLION", "₹25,007.5 MILLION"),
            ("sbifunds", "₹ 57,011.57 MILLION", "₹ 67,011.57 MILLION"),
        ):
            with self.subTest(issuer=issuer):
                text = self.source(issuer).replace(original, conflicting)
                self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_rounded_seller_aggregates_do_not_replace_the_initial_quote(self):
        text = self.source().replace("₹15,007.5 MILLION", "₹15,007.49 MILLION")
        composition, _ = parser.extract_final_issue_composition(text)
        self.assertEqual(composition["ofsCr"], 1667.33)
        self.assertEqual(composition["totalIssueSizeCr"], 1667.33)

    def test_one_disclosed_seller_amount_cannot_exceed_the_whole_offer(self):
        text = self.offer().replace(
            "EQUITY SHARES BY ALPHA", "EQUITY SHARES AGGREGATING TO ₹999 CRORE BY ALPHA",
        )
        self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_seller_currency_markers_preserve_equivalent_disclosed_amounts(self):
        for currency in ("₹", "INR ", "Rs. ", "Rs."):
            for first, second, unit in (("60", "38", "CRORE"), ("600", "380", "MILLION"), ("6,000", "3,800", "LAKH")):
                with self.subTest(currency=currency, unit=unit):
                    text = self.offer().replace(
                        "EQUITY SHARES BY ALPHA", f"EQUITY SHARES AGGREGATING TO {currency}{first} {unit} BY ALPHA",
                    ).replace(
                        "EQUITY SHARES BY BETA", f"EQUITY SHARES AGGREGATING TO {currency}{second} {unit} BY BETA",
                    )
                    composition, _ = parser.extract_final_issue_composition(text)
                    self.assertEqual(composition["ofsCr"], 98.0)
                    self.assertEqual(composition["totalIssueSizeCr"], 98.0)

    def test_seller_currency_markers_cannot_hide_amount_contradictions(self):
        for currency in ("₹", "INR ", "Rs. ", "Rs."):
            for first, second in ((999, None), (60, 60)):
                with self.subTest(currency=currency, first=first, second=second):
                    text = self.offer().replace(
                        "EQUITY SHARES BY ALPHA", f"EQUITY SHARES AGGREGATING TO {currency}{first} CRORE BY ALPHA",
                    )
                    if second is not None:
                        text = text.replace(
                            "EQUITY SHARES BY BETA", f"EQUITY SHARES AGGREGATING TO {currency}{second} CRORE BY BETA",
                        )
                    self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_known_seller_subtotal_cannot_exceed_whole_offer_when_an_amount_is_missing(self):
        text = self.offer().replace(
            "OF 6,000,000 EQUITY SHARES BY ALPHA LIMITED AND 4,000,000 EQUITY SHARES BY BETA LIMITED.",
            "OF 6,000,000 EQUITY SHARES AGGREGATING TO ₹60 CRORE BY ALPHA LIMITED, "
            "2,000,000 EQUITY SHARES AGGREGATING TO ₹60 CRORE BY BETA LIMITED AND "
            "2,000,000 EQUITY SHARES BY GAMMA LIMITED.",
        )
        self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_missing_seller_amount_does_not_invent_an_amount_from_other_sellers(self):
        text = self.offer().replace(
            "EQUITY SHARES BY ALPHA", "EQUITY SHARES AGGREGATING TO ₹60 CRORE BY ALPHA",
        )
        composition, _ = parser.extract_final_issue_composition(text)
        self.assertEqual(composition["ofsCr"], 98.0)
        self.assertEqual(composition["totalIssueSizeCr"], 98.0)
        self.assertNotIn("valuationPriceUsed", composition)

    def test_both_alias_positions_require_a_complete_matching_seller_list(self):
        for before in (False, True):
            source = self.offer()
            if before:
                source = source.replace(
                    'THROUGH AN OFFER FOR SALE (THE "OFFER" OR "OFFER FOR SALE")',
                    '(THE "OFFER"), THROUGH AN OFFER FOR SALE',
                )
            for replacement in (
                "BY ALPHA LIMITED.",
                "BY ALPHA LIMITED AND 3,000,000 EQUITY SHARES BY BETA LIMITED.",
                "BY ALPHA LIMITED AND 4,000,000 EQUITY SHARES.",
            ):
                with self.subTest(before=before, replacement=replacement):
                    text = source.replace(
                        "BY ALPHA LIMITED AND 4,000,000 EQUITY SHARES BY BETA LIMITED.", replacement,
                    )
                    self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_employee_reservation_cannot_complete_a_partial_seller_list(self):
        text = self.offer().replace(
            "AND 4,000,000 EQUITY SHARES BY BETA LIMITED.",
            ". THE OFFER INCLUDED A RESERVATION OF 4,000,000 EQUITY SHARES BID BY EMPLOYEES.",
        )
        self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_generic_reservation_or_subscription_cannot_supply_a_missing_seller(self):
        for before in (False, True):
            source = self.offer()
            if before:
                source = source.replace(
                    'THROUGH AN OFFER FOR SALE (THE "OFFER" OR "OFFER FOR SALE")',
                    '(THE "OFFER") THROUGH AN OFFER FOR SALE',
                )
            for reservation in (
                'A RESERVATION OF 4,000,000 EQUITY SHARES FOR SUBSCRIPTION BY ELIGIBLE EMPLOYEES ("EMPLOYEE RESERVATION PORTION").',
                "4,000,000 EQUITY SHARES FOR SUBSCRIPTION BY ELIGIBLE EMPLOYEES.",
                "4,000,000 EQUITY SHARES RESERVED FOR PURCHASE BY ELIGIBLE EMPLOYEES.",
                "4,000,000 EQUITY SHARES FOR ALLOTMENT BY ELIGIBLE EMPLOYEES.",
            ):
                with self.subTest(before=before, reservation=reservation):
                    text = source.replace("AND 4,000,000 EQUITY SHARES BY BETA LIMITED.", ". " + reservation)
                    self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_unrelated_pre_ipo_or_post_offer_quantities_cannot_complete_seller_list(self):
        for before in (False, True):
            source = self.offer()
            if before:
                source = source.replace(
                    'THROUGH AN OFFER FOR SALE (THE "OFFER" OR "OFFER FOR SALE")',
                    '(THE "OFFER") THROUGH AN OFFER FOR SALE',
                )
            for unrelated in (
                "A PRE-IPO PLACEMENT OF 4,000,000 EQUITY SHARES WAS MADE BY OUR COMPANY.",
                "A PRE-IPO PLACEMENT OF 4,000,000 EQUITY SHARES BY BETA LIMITED.",
                "FOLLOWING THE OFFER, 4,000,000 EQUITY SHARES WILL BE HELD BY BETA LIMITED.",
            ):
                with self.subTest(before=before, unrelated=unrelated):
                    text = source.replace("AND 4,000,000 EQUITY SHARES BY BETA LIMITED.", ". " + unrelated)
                    self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_explicit_nil_fresh_issue_does_not_contradict_whole_ofs(self):
        for empty in ("IS NOT APPLICABLE", "NIL", "IS NONE"):
            with self.subTest(empty=empty):
                text = self.source("vmm").replace("THE OFFER SHALL", f"FRESH ISSUE {empty}. THE OFFER SHALL")
                composition, _ = parser.extract_final_issue_composition(text)
                self.assertEqual(composition["freshShares"], 0)
                self.assertEqual(composition["freshIssueCr"], 0.0)
                self.assertEqual(composition["ofsCr"], 8000.0)

    def test_alias_before_through_cannot_suppress_a_separate_conflicting_ofs_clause(self):
        text = self.offer().replace(
            'THROUGH AN OFFER FOR SALE (THE "OFFER" OR "OFFER FOR SALE")',
            '(THE "OFFER") THROUGH AN OFFER FOR SALE',
        )
        text += "OFFER FOR SALE OF 5,000,000 EQUITY SHARES AGGREGATING TO ₹50 CRORE"
        self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_whole_offer_alias_must_immediately_follow_the_quoted_aggregate(self):
        for qualifier in ("PARTLY THROUGH", "INCLUDING", ". ANOTHER OFFER WAS THROUGH"):
            with self.subTest(qualifier=qualifier):
                self.assertEqual(
                    parser.extract_final_issue_composition(self.offer(qualifier=qualifier)),
                    (None, {}),
                )

    def test_unbound_alias_cannot_define_an_earlier_offer(self):
        text = (
            "INITIAL PUBLIC OFFER OF 10,000,000 EQUITY SHARES AGGREGATING TO ₹98 CRORE.\n"
            'THROUGH AN OFFER FOR SALE (THE "OFFER" OR "OFFER FOR SALE") '
            "OF 6,000,000 EQUITY SHARES BY ALPHA LIMITED."
        )
        self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_component_alias_cannot_stand_in_for_whole_offer_alias(self):
        for alias in ('(THE "OFFER FOR SALE")', '(THE "OFFERED SHARES")', ''):
            with self.subTest(alias=alias):
                text = self.offer().replace('(THE "OFFER" OR "OFFER FOR SALE")', alias)
                composition, _ = parser.extract_final_issue_composition(text)
                if composition:
                    self.assertNotEqual(composition.get("ofsShares"), 10_000_000)
                    self.assertNotIn("freshShares", composition)
                else:
                    self.assertIsNone(composition)

    def test_absent_aggregate_cannot_be_inferred_from_headline_price_or_seller_amount(self):
        for replacement in ("", "AGGREGATING TO ₹[●] CRORE "):
            with self.subTest(replacement=replacement):
                text = self.offer().replace("AGGREGATING TO ₹98 CRORE ", replacement)
                text += "An employee reservation aggregated to ₹0.8 crore."
                self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_mixed_fresh_issue_clause_rejects_whole_offer_classification(self):
        for clause in (
            "AND A FRESH ISSUE OF 2,000,000 EQUITY SHARES AGGREGATING TO ₹20 CRORE",
            "AND A FRESH ISSUE AGGREGATING TO ₹20 CRORE",
            "AND A FRESH ISSUE WITH TERMS TO BE DETERMINED",
        ):
            with self.subTest(clause=clause):
                text = self.offer().replace("BY BETA LIMITED.", "BY BETA LIMITED " + clause)
                self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_conflicting_repeated_totals_remain_unresolved(self):
        for other in (self.offer(total=11_000_000), self.offer(amount="99")):
            with self.subTest(other=other):
                self.assertEqual(
                    parser.extract_final_issue_composition(self.offer() + "\f" + other),
                    (None, {}),
                )

    def test_conflicting_explicit_ofs_component_remains_unresolved(self):
        text = self.offer() + "OFFER FOR SALE OF 6,000,000 EQUITY SHARES AGGREGATING TO ₹60 CRORE"
        self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_matching_repeated_whole_offers_are_supported(self):
        composition, _ = parser.extract_final_issue_composition(self.offer() + "\f" + self.offer())
        self.assertEqual(composition["ofsShares"], 10_000_000)
        self.assertEqual(composition["ofsCr"], 98.0)

    def test_unrecognized_cover_columns_stay_unresolved(self):
        text = (
            "DETAILS OF THE OFFER\n"
            "Fresh Issue                 Offer for Sale\n"
            "4,000,000 Equity Shares     6,000,000 Equity Shares\n"
            "aggregating to ₹40 crore    aggregating to ₹60 crore\n"
            'THROUGH AN OFFER FOR SALE (THE "OFFER" OR "OFFER FOR SALE")'
        )
        self.assertEqual(parser.extract_final_issue_composition(text), (None, {}))

    def test_quoted_discounted_amount_promotes_all_four_canonical_fields_with_evidence(self):
        composition, evidence = parser.extract_final_issue_composition(self.source())
        record = {
            "id": "orklaindia", "openDate": "2025-10-29",
            "issueSizeCr": 1667.5393, "freshIssueCr": 0, "ofsCr": 1667.5393,
            "issueComposition": {"ofsShares": 22_843_004, "valuationPriceUsed": 730},
            "issueCompositionReview": {"status": "quarantined", "fields": list(COMPOSITION_FIELDS)},
        }
        doc = {
            "type": "PROSPECTUS", "filedDate": "2025-10-31",
            "url": "https://www.orklaindia.com/wp-content/uploads/sites/3/2025/11/Orkla-India-Limited-Prospectus.pdf",
        }
        pdf_hash = "1a3e82f54f7b624901b47632b9c5307da6c2905455278a311cd9db3872d2e7fe"
        parsed = {"issueComposition": composition, "fieldEvidence": evidence}
        policy.apply_final_prospectus_static_fields(
            record, parsed, doc, sha256=pdf_hash,
            parser_version=parser.PARSER_VERSION, checked_at="2026-09-17T07:00:00Z",
        )
        self.assertEqual(record["issueSizeCr"], 1667.33)
        self.assertEqual(record["ofsCr"], 1667.33)
        self.assertEqual(record["freshIssueCr"], 0.0)
        self.assertEqual(record["issueComposition"], composition)
        self.assertEqual(record["issueCompositionReview"]["status"], "resolved")
        for field in COMPOSITION_FIELDS:
            proof = record["staticFieldProvenance"][field]
            self.assertEqual(proof["value"], record[field])
            self.assertEqual(proof["documentType"], "PROSPECTUS")
            self.assertEqual(proof["sourceUrl"], doc["url"])
            self.assertEqual(proof["sha256"], pdf_hash)
            self.assertEqual(proof["parserVersion"], 30)
            self.assertEqual(proof["evidence"], evidence["issueComposition"])
        before = copy.deepcopy(record)
        changes = policy.apply_final_prospectus_static_fields(
            record, parsed, doc, sha256=pdf_hash,
            parser_version=parser.PARSER_VERSION, checked_at="2026-09-17T07:00:00Z",
        )
        self.assertEqual(changes, [])
        self.assertEqual(record, before)


if __name__ == "__main__":
    unittest.main()
