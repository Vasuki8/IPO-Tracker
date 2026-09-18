"""Source excerpts and adversarial boundaries for allocation-table recognition."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import p4_offer_layouts as parser
from objects_of_issue_checks import objects_evidence_problems

FIXTURES = Path(__file__).parent / "fixtures" / "objects_of_issue"


def compact(body, unit="(Rs. in Crores)", header="Sr. No. Particulars Amount", total=True):
    return "\n".join(("[PAGE 10]", "OBJECTS OF THE ISSUE", unit, header, body,
                      "Note: subject to final allotment" if total else ""))


def fixed(body, total=True):
    return "\n".join(("[PAGE 10]", "Utilisation of Net Proceeds", "(in ₹ million)",
                      "Sr. No.       Particulars                                 Estimated Amount", body,
                      "Note: subject to final allotment" if total else ""))


def line(marker, purpose, amount=""):
    return f"{marker:<14}{purpose:<54}{amount:>10}"


class ObjectsTableParserTests(unittest.TestCase):
    def parsed(self, text):
        rows, details = parser.extract_objects(text)
        self.assertTrue(rows, "No bounded allocation table accepted")
        self.assertEqual(objects_evidence_problems(rows, details.get("objectsOfIssue")), [])
        return {"objectsOfIssue": rows, "fieldEvidence": details, "residualParserVersion": 4}

    def assert_rejected(self, text):
        self.assertEqual(parser.extract_objects(text), ([], {}))

    def test_actual_priority_keeps_wrapped_purpose_and_stops_before_repeated_debt(self):
        text = (FIXTURES / "priority-allocation-table.txt").read_text()
        result = self.parsed(text)
        self.assertEqual(result["objectsOfIssue"], [
            {"purpose": "Repayment / pre-payment, in full or in part, of certain working capital borrowings availed by our Company", "amountCr": 75.0},
            {"purpose": "General corporate purposes (1)(2)", "amountCr": 18.852},
        ])
        proof = result["fieldEvidence"]["objectsOfIssue"]
        self.assertEqual(proof["page"], 96)
        self.assertEqual(len(proof["sourceRows"][0]["lines"]), 2)
        self.assertIn("borrowings availed by our Company", proof["sourceRows"][0]["lines"][1]["text"])

    def test_actual_deepa_summary_excludes_fiscal_deployment_amount(self):
        result = self.parsed((FIXTURES / "deepa-allocation-table.txt").read_text())
        self.assertEqual(result["objectsOfIssue"], [
            {"purpose": "Funding long-term working capital requirements towards procurement, maintenance and scaling up of inventory by our Company", "amountCr": 215.0},
            {"purpose": "General corporate purposes(1)", "amountCr": 12.148},
        ])
        self.assertEqual(result["fieldEvidence"]["objectsOfIssue"]["page"], 105)
        self.assertTrue(all(row["page"] == 105 for row in result["fieldEvidence"]["objectsOfIssue"]["sourceRows"]))

    def test_actual_sheel_retains_issue_expenses_and_percentage_header(self):
        result = self.parsed((FIXTURES / "sheel-allocation-table.txt").read_text())
        self.assertEqual(result["objectsOfIssue"], [
            {"purpose": "Capital Expenditure Requirement", "amountCr": 9.1195},
            {"purpose": "Working Capital Requirement", "amountCr": 15.88},
            {"purpose": "General Corporate Purposes**", "amountCr": 4.768},
            {"purpose": "Issue Expense", "amountCr": 4.2525},
        ])
        proof = result["fieldEvidence"]["objectsOfIssue"]
        self.assertEqual(proof["page"], 117)
        self.assertEqual(len(proof["tableHeaders"]), 3)
        self.assertIn("% of Gross", proof["tableHeaders"][0]["text"])
        self.assertIn("Amount in Lakh", proof["unitText"])
        self.assertEqual(proof["tableScope"], "gross")
        self.assertEqual(proof["tableTotal"]["normalizedValue"], 34.02)
        self.assertEqual(proof["tableTotal"]["page"], 118)
        self.assertEqual(len(proof["corroboratingSourceTables"]), 1)
        net = proof["corroboratingSourceTables"][0]
        self.assertEqual(net["page"], 24)
        self.assertEqual(net["tableScope"], "net")
        self.assertEqual(net["tableTotal"]["normalizedValue"], 29.7675)

    def test_actual_dhanlaxmi_wrapped_headers_and_up_to_qualifier(self):
        result = self.parsed((FIXTURES / "dhanlaxmi-allocation-table.txt").read_text())
        self.assertEqual(result["objectsOfIssue"], [
            {"purpose": "Working Capital Requirements", "amountCr": 20.0577},
            {"purpose": "Issue Related Expenses*", "amountCr": 2.2463},
            {"purpose": "General Corporate Expenses*", "amountCr": 1.5},
        ])
        proof = result["fieldEvidence"]["objectsOfIssue"]
        self.assertEqual(proof["page"], 89)
        self.assertEqual(len(proof["tableHeaders"]), 3)
        self.assertIn("Up to 2,005.77", proof["sourceRows"][0]["lines"][0]["text"])
        self.assertEqual(proof["sourceRows"][0]["amountToken"], "2,005.77")

    def test_capillary_header_like_continuation_keeps_full_purpose_and_total(self):
        parsed = self.parsed((FIXTURES / "capillary-boundary-table.txt").read_text())
        self.assertEqual([row["amountCr"] for row in parsed["objectsOfIssue"]], [143.0, 71.581, 10.342, 97.985])
        self.assertEqual(parsed["objectsOfIssue"][-1]["purpose"],
                         "Funding inorganic growth through unidentified acquisitions and general corporate purposes*")
        proof = parsed["fieldEvidence"]["objectsOfIssue"]
        self.assertEqual(proof["tableTotal"]["normalizedValue"], 322.908)
        self.assertEqual(proof["tableTotal"]["page"], 27)
        self.assertEqual(proof["sourceRows"][-1]["lines"][-1]["text"].strip(), "purposes*")

    def test_alpine_floating_footnote_cannot_drop_third_allocation(self):
        self.assert_rejected((FIXTURES / "alpinetex-boundary-table.txt").read_text())

    def test_solarworld_repeated_header_cannot_close_table_prefix(self):
        self.assert_rejected((FIXTURES / "solarworld-boundary-table.txt").read_text())

    def test_repeated_header_cannot_hide_an_inconsistent_final_total(self):
        body = line("1.", "Funding working capital requirements", "200.00")
        source = fixed(body, total=False) + "\n\f[PAGE 11]\n"
        source += "Sr. No.       Particulars                                 Estimated Amount\n"
        source += line("", "Total", "300.00")
        self.assert_rejected(source)

    def test_bare_footnote_needs_real_note_text_or_strong_boundary(self):
        source = fixed(line("1.", "Funding working capital requirements", "200.00"), total=False)
        for marker in ("(1)", "*", "^"):
            with self.subTest(marker=marker):
                self.assert_rejected(source + "\n" + marker)
                self.assert_rejected(source + "\n" + marker + "\n" + line("2.", "General corporate purposes", "100.00"))
                parsed = self.parsed(source + "\n" + marker + "\nThe amount utilised for general corporate purposes shall not exceed 25%.")
                self.assertEqual(len(parsed["objectsOfIssue"]), 1)
                self.parsed(source + "\n" + marker + "\nProposed schedule of implementation and deployment of Net Proceeds")

    def test_footnote_prefixed_allocation_cannot_close_an_incomplete_prefix(self):
        source = fixed(line("1.", "Funding working capital requirements", "200.00"), total=False)
        for marker in ("(3)", "*", "^"):
            with self.subTest(marker=marker):
                next_row = line("", marker + " General corporate purposes", "100.00")
                self.assert_rejected(source + "\n" + next_row + "\n" + line("", "Total", "300.00"))

    def test_requires_standalone_heading_and_identifiable_columns(self):
        source = compact("A. Working capital requirements 20.00")
        for replacement in ("For objects of the issue see page 10", "OBJECTS OF THE ISSUE 10", ""):
            with self.subTest(replacement=replacement):
                self.assert_rejected(source.replace("OBJECTS OF THE ISSUE", replacement))
        self.assert_rejected(source.replace("Sr. No. Particulars Amount", ""))
        self.assert_rejected(source.replace("Sr. No. Particulars Amount", "The Particulars include an Amount stated below"))

    def test_explicit_unit_required_without_crore_default(self):
        self.assert_rejected(compact("A. Working capital requirements 20.00", unit=""))
        self.assert_rejected(compact("A. Working capital requirements 20.00", unit="Capital requirements are 30 crore"))
        self.assert_rejected(compact("A. Working capital requirements 20.00", unit="(in million or in crore)"))

    def test_explicit_units_convert_to_crore(self):
        for unit, expected in (("(₹ in Lakhs)", 0.123456), ("(INR million)", 1.23456), ("(in crore)", 12.3456)):
            with self.subTest(unit=unit):
                parsed = self.parsed(compact("A. Working capital requirements 12.3456", unit=unit))
                self.assertEqual(parsed["objectsOfIssue"][0]["amountCr"], expected)

    def test_zero_nil_and_explicit_undisclosed_cells_are_preserved(self):
        for token, expected in (("0.00", 0.0), ("Nil", 0.0), ("[●]", None), ("[*]", None), ("—", None), ("-", None)):
            with self.subTest(token=token):
                parsed = self.parsed(compact(f"A. Working capital requirements {token}"))
                self.assertEqual(parsed["objectsOfIssue"][0]["amountCr"], expected)
                self.assertEqual(parsed["fieldEvidence"]["objectsOfIssue"]["sourceRows"][0]["amountToken"], token)

    def test_currency_and_up_to_remain_outside_purpose_and_amount_spans(self):
        for prefix in ("₹", "Rs.", "INR ", "Up to ", "Up to ₹"):
            with self.subTest(prefix=prefix):
                parsed = self.parsed(compact(f"A. Working capital requirements {prefix}20.00"))
                self.assertEqual(parsed["objectsOfIssue"], [{"purpose": "Working capital requirements", "amountCr": 20.0}])

    def test_fixed_layout_purpose_can_continue_on_next_pdf_page(self):
        body = "\n".join((line("1.", "Funding working capital requirements", "200.00"), "Page 6 of 100",
                          "\f[PAGE 11]", line("", "towards procurement and inventory"),
                          line("2.", "General corporate purposes", "100.00")))
        parsed = self.parsed(fixed(body))
        self.assertEqual(parsed["objectsOfIssue"][0]["purpose"], "Funding working capital requirements towards procurement and inventory")
        rows = parsed["fieldEvidence"]["objectsOfIssue"]["sourceRows"]
        self.assertEqual([part["page"] for part in rows[0]["lines"]], [10, 11])
        self.assertEqual(rows[1]["page"], 11)

    def test_misaligned_continuation_does_not_publish_a_truncated_purpose(self):
        body = line("1.", "Funding working capital requirements", "200.00") + "\n" + "                 towards procurement and inventory"
        self.assert_rejected(fixed(body))

    def test_missing_amount_in_later_row_rejects_entire_table(self):
        self.assert_rejected(compact("A. Working capital requirements 20.00\nB. General corporate purposes"))
        self.assert_rejected(fixed(line("1.", "Funding working capital", "200.00") + "\n" + line("2.", "General corporate purposes")))

    def test_unexplained_line_cannot_close_and_publish_partial_table(self):
        self.assert_rejected(compact("A. Working capital requirements 20.00\nGeneral corporate purposes not disclosed"))

    def test_explicit_percentage_column_accepts_number_or_percent(self):
        for suffix in ("66.67%", "66.67"):
            with self.subTest(suffix=suffix):
                parsed = self.parsed(compact(f"A. Working capital requirements 20.00 {suffix}", header="Sr. No. Particulars Amount Percentage"))
                self.assertEqual(parsed["objectsOfIssue"][0]["amountCr"], 20.0)

    def test_extra_numeric_columns_and_unlabelled_percentages_are_rejected(self):
        for suffix in ("20.00 10.00", "20.00 100", "20.00 66.67%"):
            with self.subTest(suffix=suffix):
                self.assert_rejected(compact("A. Working capital requirements " + suffix))
        for suffix in ("20.00 66.67% 66.67%", "20.00 101%"):
            with self.subTest(suffix=suffix):
                self.assert_rejected(compact("A. Working capital requirements " + suffix, header="Sr. No. Particulars Amount Percentage"))

    def test_fiscal_schedule_or_multiple_amount_headers_cannot_supply_objects(self):
        for header in ("Sr. No. Particulars Amount FY2027 FY2028", "Sr. No. Particulars Amount Amount", "Sr. No. Particulars Amount Estimated deployment"):
            with self.subTest(header=header):
                self.assert_rejected(compact("A. Working capital requirements 20.00 10.00", header=header))

    def test_reconciliation_table_cannot_promote_issue_expenses_alone(self):
        self.assert_rejected(compact("A. Gross Issue Proceeds 30.00\nB. Issue Related Expenses 2.00\nC. Net Proceeds 28.00"))

    def test_known_boundaries_stop_before_later_allocations(self):
        body = "A. Working capital requirements 20.00"
        for boundary in ("Total 20.00", "Proposed schedule of implementation and deployment of Net Proceeds",
                         "Means of finance", "Details of Objects", "Note: subject to final allotment"):
            with self.subTest(boundary=boundary):
                parsed = self.parsed(compact(body + "\n" + boundary + "\nB. General corporate purposes 999.00", total=False))
                self.assertEqual(len(parsed["objectsOfIssue"]), 1)

    def test_agreeing_duplicates_are_deduplicated_with_original_physical_proof(self):
        parsed = self.parsed(compact("A. Working capital requirements 20.00\nB. Working capital requirements 20.00"))
        self.assertEqual(len(parsed["objectsOfIssue"]), 1)
        self.assertEqual(len(parsed["fieldEvidence"]["objectsOfIssue"]["sourceRows"]), 1)
        source = compact("A. Working capital requirements 20.00")
        self.assertEqual(self.parsed(source + "\n" + source)["objectsOfIssue"], parsed["objectsOfIssue"])

    def test_conflicting_duplicate_purposes_and_candidates_are_rejected(self):
        self.assert_rejected(compact("A. Working capital requirements 20.00\nB. Working capital requirements 21.00"))
        self.assert_rejected(compact("A. General corporate purposes(1) 20.00\nB. General corporate purposes(2) 21.00"))
        source = compact("A. Working capital requirements 20.00")
        self.assert_rejected(source + "\n" + source.replace("20.00", "21.00"))
        self.assert_rejected(source + "\n" + source.replace("Working capital requirements", "General corporate purposes"))

    def test_explicit_total_must_reconcile_when_all_rows_are_numeric(self):
        body = "A. Working capital requirements 20.00\nB. General corporate purposes 10.00"
        self.parsed(compact(body, total=False) + "\nTotal 30.00")
        self.assert_rejected(compact(body, total=False) + "\nTotal 31.00")
        self.assert_rejected(compact(body, total=False) + "\n3. Total 31.00")
        unknown = self.parsed(compact("A. Working capital requirements [●]", total=False) + "\nTotal 30.00")
        self.assertIsNone(unknown["objectsOfIssue"][0]["amountCr"])

    def test_net_and_gross_tables_reconcile_only_explicit_issue_expenses(self):
        net = compact("A. Working capital expenditure requirements 10.00\nB. General corporate purposes(1) 2.00", total=False) + "\nNet Proceeds 12.00"
        gross = compact("A. Working capital requirement 10.00 50.00%\nB. General corporate purposes** 2.00 10.00%\nC. Issue Related Expenses 8.00 40.00%",
                        header="Sr. No. Particulars Amount % of Gross Proceeds", total=False) + "\nTotal 20.00 100.00%"
        for source in (net + "\n" + gross, gross + "\n" + net):
            with self.subTest(source_order=source[:100]):
                parsed = self.parsed(source)
                self.assertEqual(len(parsed["objectsOfIssue"]), 3)
                self.assertEqual(parsed["objectsOfIssue"][2]["purpose"], "Issue Related Expenses")
                proof = parsed["fieldEvidence"]["objectsOfIssue"]
                self.assertEqual(proof["tableScope"], "gross")
                self.assertEqual(proof["corroboratingSourceTables"][0]["tableScope"], "net")
        for changed in (gross.replace("Issue Related Expenses", "Capital expenditure"),
                        gross.replace("10.00 50.00%", "11.00 55.00%").replace("Total 20.00", "Total 21.00"),
                        gross.replace("% of Gross Proceeds", "Percentage"),
                        gross.replace("Total 20.00", "Total 21.00"),
                        gross.replace("Working capital requirement", "Working capital expansion")):
            with self.subTest(changed=changed):
                self.assert_rejected(net + "\n" + changed)

    def test_huge_or_negative_amounts_fail_closed_without_crashing(self):
        for token in ("9" * 30, "-20.00", "(20.00)", "NaN", "inf"):
            with self.subTest(token=token):
                self.assert_rejected(compact("A. Working capital requirements " + token))

    def test_table_scope_limit_cannot_return_truncated_rows(self):
        body = line("1.", "Funding working capital requirements", "200.00")
        body += "\n" + "\n".join(line("", "and additional inventory") for _ in range(75))
        self.assert_rejected(fixed(body))
        self.assert_rejected(fixed(line("1.", "Funding working capital", "200.00") + "\n\f[PAGE 12]\n" + line("2.", "General corporate purposes", "100.00")))

    def test_merge_replaces_weak_primary_value_and_its_proof_as_a_pair(self):
        supplement = self.parsed(compact("A. Working capital requirements 20.00"))
        primary = {"objectsOfIssue": [{"purpose": "General corporate purposes", "amountCr": 99.0}],
                   "fieldEvidence": {"objectsOfIssue": {"page": 1, "rows": []}}}
        original = copy.deepcopy(primary)
        merged = parser.merge_parsed(primary, supplement)
        self.assertEqual(merged["objectsOfIssue"], supplement["objectsOfIssue"])
        self.assertEqual(merged["fieldEvidence"]["objectsOfIssue"], supplement["fieldEvidence"]["objectsOfIssue"])
        self.assertEqual(primary, original)

    def test_merge_retains_supported_primary_with_its_own_proof(self):
        primary = self.parsed(compact("A. Working capital requirements 20.00"))
        supplement = self.parsed(compact("A. General corporate purposes 10.00").replace("PAGE 10", "PAGE 20"))
        merged = parser.merge_parsed(primary, supplement)
        self.assertEqual(merged["objectsOfIssue"], primary["objectsOfIssue"])
        self.assertEqual(merged["fieldEvidence"]["objectsOfIssue"], primary["fieldEvidence"]["objectsOfIssue"])

    def test_merge_cannot_attach_proof_to_a_different_retained_value(self):
        source = self.parsed(compact("A. Working capital requirements 20.00"))
        supplement = copy.deepcopy(source)
        supplement["objectsOfIssue"][0]["amountCr"] = 999.0
        primary = {"objectsOfIssue": [{"purpose": "General corporate purposes", "amountCr": 10.0}], "fieldEvidence": {}}
        merged = parser.merge_parsed(primary, supplement)
        self.assertEqual(merged["objectsOfIssue"], primary["objectsOfIssue"])
        self.assertNotIn("objectsOfIssue", merged["fieldEvidence"])
        self.assertEqual(parser.merge_parsed(source, supplement)["fieldEvidence"], source["fieldEvidence"])

    def test_residual_version_advances_for_existing_record_retries(self):
        self.assertEqual(parser.PARSER_VERSION, 5)


if __name__ == "__main__":
    unittest.main()
