"""Regression evidence for reviewed allocation-scope and source-budget defects."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import p4_offer_parser as parser
from objects_of_issue_checks import objects_evidence_problems

FIXTURES = Path(__file__).parent / "fixtures" / "objects-source-acceptance"


def fixture(name):
    return (FIXTURES / f"{name}.txt").read_text()


def physical_page(text, number):
    return next(page for page in text.split("\f") if page.startswith(f"[PAGE {number}]"))


def budget_table(*, expenses="10.00", net="90.00", second="30.00", include_expense=False):
    rows = ["1. Working capital requirements 60.00", f"2. General corporate purposes {second}"]
    if include_expense:
        rows.append(f"3. Issue Related Expenses {expenses}")
    total = 60 + float(second) + (float(expenses) if include_expense else 0)
    return "\n".join([
        "[PAGE 1]", "OBJECTS OF THE ISSUE", "(Rs. in Crores)", "Particulars Amount",
        "Gross Issue Proceeds 100.00", f"Less: Public Issue Related Expenses {expenses}",
        f"Net Issue Proceeds {net}", "Utilization of Net Issue Proceeds", "(Rs. in Crores)",
        "Particulars Amount", *rows, f"Total {total:.2f}",
    ])


class ObjectsSourceAcceptanceTests(unittest.TestCase):
    def accepted(self, text):
        rows, details = parser.extract_objects(text)
        self.assertTrue(rows)
        proof = details["objectsOfIssue"]
        self.assertEqual(objects_evidence_problems(rows, proof), [])
        return rows, proof

    def test_teamtech_recovers_complete_net_allocation_across_summary_and_full_section(self):
        rows, proof = self.accepted(fixture("teamtech"))
        self.assertEqual(rows, [
            {"purpose": "Funding of Capital Expenditure towards purchase of Plant and Machineries for new manufacturing unit", "amountCr": 11.9235},
            {"purpose": "Repayment/prepayment of all or certain of our borrowing availed by your company.", "amountCr": 15.5},
            {"purpose": "To meet the working capital requirements", "amountCr": 13.7688},
            {"purpose": "General Corporate Purpose*", "amountCr": 4.2936},
        ])
        self.assertAlmostEqual(sum(row["amountCr"] for row in rows), 45.4859)
        self.assertEqual(proof["tableTotal"]["normalizedValue"], 45.4859)
        # 90.70% of gross is a denominator, not proof of a gross allocation.
        self.assertEqual(proof["tableScope"], "unspecified")
        reconciliation = proof["proceedsReconciliation"][0]
        self.assertEqual([row["amountCr"] for row in reconciliation["rows"]], [50.148, 4.6621, 45.4859])
        self.assertEqual([row["page"] for row in reconciliation["sourceRows"]], [22, 22, 23])
        self.assertTrue(all(row["page"] == 23 for row in proof["sourceRows"]))

    def test_teamtech_stacked_unit_and_centred_amount_keep_physical_source_spans(self):
        rows, proof = self.accepted(physical_page(fixture("teamtech"), 87))
        self.assertEqual(proof["unitText"], "Amount(₹ in Lakhs)")
        self.assertEqual(len(proof["unitSpans"]), 2)
        self.assertEqual(len(proof["sourceRows"][0]["lines"]), 3)
        self.assertEqual(proof["sourceRows"][0]["amountSpan"]["line"], 1)
        self.assertEqual(rows[0]["amountCr"], 11.9235)
        self.assertNotIn("1.", rows[0]["purpose"])

    def test_teamtech_detailed_project_cost_table_is_never_an_allocation_candidate(self):
        text = "\f".join(physical_page(fixture("teamtech"), page) for page in (89, 90))
        self.assertEqual(parser.extract_objects(text), ([], {}))
        # Removing the longer narrative still leaves the explicit project-cost
        # introducer as a boundary underneath an objects heading.
        project = text[text.index("The estimated cost of setting up"):]
        self.assertEqual(parser.extract_objects("[PAGE 90]\nOBJECTS OF THE ISSUE\n" + project), ([], {}))

    def test_unimech_parent_scope_is_retained_for_every_subsidiary_child(self):
        rows, proof = self.accepted(physical_page(fixture("unimech"), 19))
        self.assertEqual([row["amountCr"] for row in rows], [36.366, 25.285, 43.891, 44.715, 40, 40.654])
        self.assertEqual(rows[1]["purpose"], "Funding working capital requirements of our Company;")
        for index in (2, 3, 4):
            self.assertTrue(rows[index]["purpose"].startswith("Investment in our Material Subsidiary for: "))
            self.assertEqual(proof["sourceRows"][index]["lines"][0]["text"].strip(),
                             "Investment in our Material Subsidiary for:")
        self.assertNotIn("Subsidiary", rows[-1]["purpose"])

    def test_unimech_unsupported_wrapped_reconciliation_keeps_full_document_unresolved(self):
        self.assertEqual(parser.extract_objects(fixture("unimech")), ([], {}))

    def test_ambiguous_child_after_established_parent_cannot_lose_ownership_scope(self):
        source = physical_page(fixture("unimech"), 19)
        source = source.replace("b.    funding its working capital requirements;", "      funding its working capital requirements;")
        self.assertEqual(parser.extract_objects(source), ([], {}))

    def test_blackbuck_and_mbel_source_net_proceeds_contradictions_are_withheld(self):
        for name in ("blackbuck", "mbel", "shriahimsa"):
            with self.subTest(name=name):
                self.assertEqual(parser.extract_objects(fixture(name)), ([], {}))

    def test_existing_issue_and_fresh_issue_tables_preserve_allocations(self):
        for name, amounts in (("emmvee", [1621.294, 438.711]),
                              ("belrise", [1618.127, 410.485]),
                              ("chamunda", [1.2051, 5.5, 2.8507, 3.5819]),
                              ("etml", [36.3349, 8.5071]),
                              ("capillary", [143, 71.581, 10.342, 97.985])):
            with self.subTest(name=name):
                rows, proof = self.accepted(fixture(name))
                self.assertEqual([row["amountCr"] for row in rows], amounts)
                self.assertTrue(proof["proceedsReconciliation"])
        _, proof = self.accepted(fixture("emmvee"))
        budget = proof["proceedsReconciliation"][0]
        self.assertEqual(budget["page"], 117)
        self.assertEqual(budget["rows"][1]["purpose"], "(Less) Expenses in relation to the Fresh Issue((1)")
        self.assertEqual([row["amountCr"] for row in budget["rows"]], [2143.862, 83.857, 2060.005])

    def test_offer_or_abbreviated_budget_labels_keep_observed_fresh_issue_context(self):
        for name, total in (("anawil", 118.6384), ("genxai", 46.2138)):
            with self.subTest(name=name):
                rows, proof = self.accepted(fixture(name))
                self.assertAlmostEqual(sum(row["amountCr"] for row in rows), total)
                budget = proof["proceedsReconciliation"][0]
                self.assertTrue(budget["issuerProceedsContext"])
                changed = copy.deepcopy(proof)
                del changed["proceedsReconciliation"][0]["issuerProceedsContext"]
                self.assertTrue(objects_evidence_problems(rows, changed))
                changed["proceedsReconciliation"][0]["issuerProceedsContext"] = [
                    {"page": budget["page"], "text": "Offer for Sale"},
                ]
                self.assertTrue(objects_evidence_problems(rows, changed))

    def test_equivalent_gcp_labels_keep_actual_source_wording(self):
        rows, proof = self.accepted(fixture("avience"))
        self.assertEqual(sum(row["amountCr"] for row in rows), 26.2674)
        self.assertEqual(rows[-1]["purpose"], "General Corporate Purpose#")
        self.assertEqual(proof["sourceRows"][-1]["purpose"], "General Corporate Purpose#")

    def test_annotated_gross_amounts_cannot_bypass_budget_validation(self):
        for marker in ("*", "(1)", "((1)", "(1)(2)"):
            with self.subTest(marker=marker):
                good = budget_table().replace("Gross Issue Proceeds 100.00", f"Gross Issue Proceeds 100.00{marker}")
                rows, proof = self.accepted(good)
                self.assertTrue(proof["proceedsReconciliation"][0]["sourceRows"][0]["amountAnnotationSpans"])
                bad = budget_table(second="40.00").replace("Gross Issue Proceeds 100.00", f"Gross Issue Proceeds 100.00{marker}")
                self.assertEqual(parser.extract_objects(bad), ([], {}))
                actual = fixture("blackbuck").replace("5,500.00\n", f"5,500.00{marker}\n", 1)
                self.assertEqual(parser.extract_objects(actual), ([], {}))

    def test_unreadable_or_missing_gross_amount_never_skips_an_explicit_budget(self):
        for amount in ("unreadable", "", "100.00unknown"):
            source = budget_table(second="40.00").replace("Gross Issue Proceeds 100.00", "Gross Issue Proceeds " + amount)
            with self.subTest(amount=amount):
                self.assertEqual(parser.extract_objects(source), ([], {}))

    def test_source_amount_annotation_cannot_hide_an_extra_numeric_column(self):
        source = budget_table().replace("Gross Issue Proceeds 100.00", "Gross Issue Proceeds 100.00(1)")
        rows, proof = self.accepted(source)
        changed = copy.deepcopy(proof)
        row = changed["proceedsReconciliation"][0]["sourceRows"][0]
        row["amountAnnotationSpans"][0]["start"] = row["amountSpan"]["start"]
        self.assertTrue(objects_evidence_problems(rows, changed))
        row["amountSpan"]["end"] = None
        self.assertTrue(objects_evidence_problems(rows, changed))

    def test_reconciliation_arithmetic_and_allocation_budget_both_must_agree(self):
        self.accepted(budget_table())
        for source in (budget_table(expenses="9.00"), budget_table(second="40.00"),
                       budget_table(net="[●]"),
                       budget_table().replace("Gross Issue Proceeds", "Gross Proceeds from the Offer for Sale")):
            with self.subTest(source=source):
                self.assertEqual(parser.extract_objects(source), ([], {}))

    def test_explicit_issue_expenses_are_excluded_once_from_net_allocation_sum(self):
        rows, proof = self.accepted(budget_table(include_expense=True))
        self.assertEqual(sum(row["amountCr"] for row in rows), 100)
        self.assertEqual(proof["proceedsReconciliation"][0]["rows"][-1]["amountCr"], 90)

    def test_reconciliation_proofs_cannot_be_forged_or_recursively_nested(self):
        rows, proof = self.accepted(budget_table())
        candidates = []
        for value in (None, [], [proof["proceedsReconciliation"][0]] * 4):
            changed = copy.deepcopy(proof)
            changed["proceedsReconciliation"] = value
            candidates.append(changed)
        changed = copy.deepcopy(proof)
        changed["proceedsReconciliation"][0]["rows"][2]["amountCr"] = 100
        candidates.append(changed)
        changed = copy.deepcopy(proof)
        changed["proceedsReconciliation"][0]["proceedsReconciliation"] = []
        candidates.append(changed)
        changed = copy.deepcopy(proof)
        changed["proceedsReconciliation"][0]["tableTotal"] = copy.deepcopy(proof["tableTotal"])
        candidates.append(changed)
        for changed in candidates:
            with self.subTest(proof=changed):
                self.assertTrue(objects_evidence_problems(rows, changed))

    def test_wrapped_unit_requires_matching_ordered_header_spans(self):
        rows, proof = self.accepted(physical_page(fixture("teamtech"), 87))
        for mutation in ("missing", "outside", "overlap", "reordered", "text", "page"):
            changed = copy.deepcopy(proof)
            if mutation == "missing":
                del changed["unitSpans"]
            elif mutation == "outside":
                changed["unitSpans"][0]["end"] = 9999
            elif mutation == "overlap":
                changed["unitSpans"].append(copy.deepcopy(changed["unitSpans"][0]))
            elif mutation == "reordered":
                changed["unitSpans"].reverse()
            elif mutation == "text":
                changed["unitSourceLines"][0]["text"] += " modified"
            else:
                changed["unitPage"] += 1
            with self.subTest(mutation=mutation):
                self.assertTrue(objects_evidence_problems(rows, changed))


if __name__ == "__main__":
    unittest.main()
