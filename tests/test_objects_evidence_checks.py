"""Source-cell evidence is checked independently of parser output."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from objects_of_issue_checks import objects_evidence_problems
from objects_evidence_fixtures import objects_evidence


class ObjectsEvidenceChecksTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"purpose": "Funding working capital", "amountCr": 12.5}]
        self.evidence = objects_evidence(self.rows)

    def assertRejected(self, evidence, rows=None):
        self.assertTrue(objects_evidence_problems(self.rows if rows is None else rows, evidence))

    def token_evidence(self, token, amount, unit="crore"):
        rows = [{"purpose": "Working capital", "amountCr": amount}]
        evidence = objects_evidence(rows)
        evidence.update(unit=unit, unitText=f"(Amount in {unit})")
        source = evidence["sourceRows"][0]
        text = f"Working capital    {token}"
        source["lines"][0]["text"] = text
        source["amountToken"] = token
        source["amountSpan"]["end"] = len(text)
        return rows, evidence

    def test_valid_explicit_source_rows_and_absence(self):
        self.assertEqual(objects_evidence_problems(self.rows, self.evidence), [])
        self.assertEqual(objects_evidence_problems(None, None), [])
        self.assertEqual(objects_evidence_problems([], {}), [])

    def test_legacy_normalized_envelope_is_not_source_evidence(self):
        for evidence in (None, {}, {"page": 100, "heading": "OBJECTS OF THE ISSUE",
                                    "unit": "crore", "rows": self.rows}):
            with self.subTest(evidence=evidence):
                self.assertRejected(evidence)
        for version in (None, 0, 2, "1", True, 1.0):
            with self.subTest(version=version):
                self.assertRejected({**self.evidence, "schemaVersion": version})

    def test_missing_or_invalid_pdf_pages_are_rejected(self):
        for page in (None, False, True, 0, -1, 1.5, "100"):
            for field in ("page", "unitPage"):
                with self.subTest(page=page, field=field):
                    self.assertRejected({**self.evidence, field: page})
            for field in ("tableHeaders", "sourceRows"):
                changed = copy.deepcopy(self.evidence)
                changed[field][0]["page"] = page
                self.assertRejected(changed)
            changed = copy.deepcopy(self.evidence)
            changed["sourceRows"][0]["lines"][0]["page"] = page
            self.assertRejected(changed)

    def test_heading_must_be_observed_and_standalone(self):
        for heading in ("See Objects of the Issue on page 100", "OBJECTS OF THE ISSUE 100",
                        "Proposed schedule of deployment", "OBJECTS OF THE ISSUE\nMore text"):
            with self.subTest(heading=heading):
                self.assertRejected({**self.evidence, "heading": heading, "headingRaw": heading})
        self.assertRejected({**self.evidence, "headingRaw": "Utilisation of Net Proceeds"})
        self.assertEqual(objects_evidence_problems(self.rows, {
            **self.evidence, "heading": "Utilisation of Net Proceeds",
            "headingRaw": "  Utilisation of Net Proceeds  ",
        }), [])

    def test_unit_must_be_explicit_and_consistent(self):
        for unit_text in ("", "Amount", "123 million", "(₹ in million)", "(₹ in crore) (Rs in lakh)"):
            with self.subTest(unit_text=unit_text):
                self.assertRejected({**self.evidence, "unitText": unit_text})
        for unit in (None, "rupee", True, []):
            self.assertRejected({**self.evidence, "unit": unit})

    def test_lakh_million_and_crore_source_conversions(self):
        for token, value, unit in (("2,005.77", 20.0577, "lakh"), ("2,150.00", 215, "million"),
                                   ("188.52", 18.852, "million"), ("12.5", 12.5, "crore")):
            with self.subTest(token=token, unit=unit):
                rows, evidence = self.token_evidence(token, value, unit)
                self.assertEqual(objects_evidence_problems(rows, evidence), [])
                evidence["sourceRows"][0]["normalizedValue"] = value + 1
                self.assertRejected(evidence, rows)

    def test_explicit_unknown_and_zero_semantics(self):
        for token, value in (("[●]", None), ("[*]", None), ("-", None), ("—", None),
                             ("0.00", 0), ("Nil", 0)):
            with self.subTest(token=token):
                rows, evidence = self.token_evidence(token, value)
                self.assertEqual(objects_evidence_problems(rows, evidence), [])
        for token in ("", "unknown", "nan", "inf", "-1", "1,2,3", "12 crore"):
            rows, evidence = self.token_evidence(token, None)
            self.assertRejected(evidence, rows)
        rows, evidence = self.token_evidence("[●]", 0)
        self.assertRejected(evidence, rows)
        rows, evidence = self.token_evidence("0", None)
        self.assertRejected(evidence, rows)

    def test_boolean_nonfinite_and_negative_values_are_rejected(self):
        for value in (True, False, float("nan"), float("inf"), -1, "12.5"):
            rows, evidence = self.token_evidence("12.5", value)
            self.assertRejected(evidence, rows)
        changed = copy.deepcopy(self.evidence)
        changed["sourceRows"][0]["normalizedValue"] = True
        self.assertRejected(changed)

    def test_headers_require_allocation_columns_without_fiscal_schedule(self):
        for header in ("Particulars", "Amount", "Particulars Amount FY2028",
                       "Particulars Amount 2028", "Particulars Deployment Amount",
                       "The amount for these purposes will be revised later.",
                       "Amount    Particulars", "Particulars    Loan balance    Amount"):
            changed = {**self.evidence, "tableHeaders": [{"page": 100, "text": header}]}
            with self.subTest(header=header):
                self.assertRejected(changed)
        for headers in (None, [], 1, True, [None], [{"page": 100, "text": "Particulars\nAmount"}]):
            self.assertRejected({**self.evidence, "tableHeaders": headers})

    def test_multiple_amount_columns_cannot_claim_single_allocation_evidence(self):
        self.assertRejected({**self.evidence, "tableHeaders": [{
            "page": 100, "text": "Particulars    Amount already spent    Amount required",
        }]})

    def test_source_pages_must_locate_the_same_table_after_the_heading(self):
        for field, page in (("page", 101), ("unitPage", 400), ("unitPage", 98)):
            self.assertRejected({**self.evidence, field: page})
        changed = copy.deepcopy(self.evidence)
        changed["tableHeaders"][0]["page"] = 300
        self.assertRejected(changed)
        changed["tableHeaders"][0]["page"] = 98
        self.assertRejected(changed)

    def test_every_accepted_row_needs_exactly_matching_value_evidence(self):
        for field in ("rows", "sourceRows"):
            for rows in ([], [None], self.evidence[field] * 2):
                self.assertRejected({**self.evidence, field: rows})
        changed = copy.deepcopy(self.evidence)
        changed["sourceRows"][0]["purpose"] = "General corporate purposes"
        self.assertRejected(changed)
        changed = copy.deepcopy(self.evidence)
        changed["sourceRows"][0]["amountToken"] = "12.50"
        self.assertRejected(changed)

    def test_span_bounds_types_and_overlaps_are_rejected(self):
        for span in (None, {}, {"line": 0, "start": 0, "end": True},
                     {"line": -1, "start": 0, "end": 10}, {"line": 5, "start": 0, "end": 10},
                     {"line": 0, "start": -1, "end": 10}, {"line": 0, "start": 0, "end": 500}):
            for field in ("amountSpan", "purposeSpans"):
                changed = copy.deepcopy(self.evidence)
                changed["sourceRows"][0][field] = [span] if field == "purposeSpans" else span
                self.assertRejected(changed)
        changed = copy.deepcopy(self.evidence)
        changed["sourceRows"][0]["amountSpan"] = changed["sourceRows"][0]["purposeSpans"][0]
        self.assertRejected(changed)

    def test_wrapped_purpose_retains_physical_lines_and_pages(self):
        rows = [{"purpose": "Funding working capital including maintenance", "amountCr": 12.5}]
        evidence = objects_evidence(rows)
        source = evidence["sourceRows"][0]
        first, second = "Funding working capital    12.5", "including maintenance"
        source.update(lines=[{"page": 100, "text": first}, {"page": 101, "text": second}],
                      purposeSpans=[{"line": 0, "start": 0, "end": 23},
                                    {"line": 1, "start": 0, "end": len(second)}],
                      amountSpan={"line": 0, "start": 27, "end": len(first)})
        self.assertEqual(objects_evidence_problems(rows, evidence), [])
        source["lines"][1]["page"] = 99
        self.assertRejected(evidence, rows)

    def test_spans_cannot_reorder_source_purpose(self):
        rows = [{"purpose": "capital Working", "amountCr": 12.5}]
        evidence = objects_evidence(rows)
        source = evidence["sourceRows"][0]
        source["lines"][0]["text"] = "Working capital    12.5"
        source["purposeSpans"] = [{"line": 0, "start": 8, "end": 15}, {"line": 0, "start": 0, "end": 7}]
        self.assertRejected(evidence, rows)

    def test_unexplained_columns_and_truncated_purposes_are_rejected(self):
        for extra in ("  90", "  50.0", "  FY2028", "  extra words"):
            changed = copy.deepcopy(self.evidence)
            changed["sourceRows"][0]["lines"][0]["text"] += extra
            self.assertRejected(changed)

    def test_percentage_requires_explicit_header_and_valid_single_cell(self):
        for token in ("50", "50.5", "50.5%"):
            changed = copy.deepcopy(self.evidence)
            changed["tableHeaders"] = [
                {"page": 100, "text": "% of Gross"},
                {"page": 100, "text": "S. N. Particulars Amount"},
                {"page": 100, "text": "Proceeds"},
            ]
            changed["sourceRows"][0]["lines"][0]["text"] += "    " + token
            self.assertEqual(objects_evidence_problems(self.rows, changed), [])
        for token in ("101", "-1", "50 60"):
            changed["sourceRows"][0]["lines"][0]["text"] = self.evidence["sourceRows"][0]["lines"][0]["text"] + "    " + token
            self.assertRejected(changed)

    def test_row_numbering_and_up_to_amount_are_not_extra_columns(self):
        changed = copy.deepcopy(self.evidence)
        source = changed["sourceRows"][0]
        original = source["lines"][0]["text"]
        amount_start = source["amountSpan"]["start"]
        source["lines"][0]["text"] = "1. " + original[:amount_start] + "Up to " + original[amount_start:]
        source["purposeSpans"][0]["start"] += 3
        source["purposeSpans"][0]["end"] += 3
        source["amountSpan"]["start"] += 9
        source["amountSpan"]["end"] += 9
        self.assertEqual(objects_evidence_problems(self.rows, changed), [])
        changed["tableHeaders"][0]["text"] += "    % of total issue size"
        source["lines"][0]["text"] += "    84.26%"
        self.assertEqual(objects_evidence_problems(self.rows, changed), [])

    def test_amount_cannot_be_swapped_with_a_percentage_column(self):
        rows, evidence = self.token_evidence("25.00", 25)
        source = evidence["sourceRows"][0]
        source["lines"][0]["text"] = "Working capital    10.00    25.00"
        source["amountSpan"] = {"line": 0, "start": 28, "end": 33}
        evidence["tableHeaders"][0]["text"] += "    % of Gross Proceeds"
        self.assertRejected(evidence, rows)

    def test_duplicate_allocations_are_not_independent_source_objects(self):
        rows = self.rows * 2
        self.assertRejected(objects_evidence(rows), rows)

    def with_total(self, evidence, label="Total", amount=None):
        evidence = copy.deepcopy(evidence)
        if amount is None:
            amount = sum(row["amountCr"] for row in evidence["rows"])
        evidence["tableTotal"] = objects_evidence([{"purpose": label, "amountCr": amount}])["sourceRows"][0]
        return evidence

    def gross_and_net(self):
        gross_rows = [
            {"purpose": "Working Capital Requirement", "amountCr": 12.5},
            {"purpose": "General Corporate Purposes", "amountCr": 2.5},
            {"purpose": "Issue Expenses", "amountCr": 1.0},
        ]
        gross = self.with_total(objects_evidence(gross_rows), "Gross Proceeds")
        gross["tableScope"] = "gross"
        net_rows = copy.deepcopy(gross_rows[:2])
        net_rows[0]["purpose"] = "Working Capital Expenditure Requirement"
        net = self.with_total(objects_evidence(net_rows), "Net Proceeds")
        net["tableScope"] = "net"
        gross["corroboratingSourceTables"] = [net]
        return gross_rows, gross

    def test_quoted_table_total_needs_exact_raw_evidence_and_reconciliation(self):
        evidence = self.with_total(self.evidence)
        self.assertEqual(objects_evidence_problems(self.rows, evidence), [])
        self.assertEqual(objects_evidence_problems(self.rows, self.with_total(self.evidence, "Total IPO Proceeds*")), [])
        evidence["tableTotal"]["normalizedValue"] = 13
        self.assertRejected(evidence)
        self.assertRejected(self.with_total(self.evidence, amount=13))
        self.assertRejected({**self.evidence, "tableTotal": copy.deepcopy(self.evidence["sourceRows"][0])})
        self.assertRejected(self.with_total(self.evidence, label="Interim borrowed funding"))
        for malformed in ({}, [], 12, "Total 12.5"):
            self.assertRejected({**self.evidence, "tableTotal": malformed})

    def test_net_and_gross_summaries_differ_only_by_explicit_issue_expenses(self):
        rows, evidence = self.gross_and_net()
        self.assertEqual(objects_evidence_problems(rows, evidence), [])
        self.assertEqual(evidence["rows"][0]["purpose"], "Working Capital Requirement")
        self.assertEqual(evidence["corroboratingSourceTables"][0]["rows"][0]["purpose"],
                         "Working Capital Expenditure Requirement")

    def test_other_scope_or_allocation_differences_are_rejected(self):
        rows, evidence = self.gross_and_net()
        for replacement in (
            [{"purpose": "Repayment of borrowings", "amountCr": 12.5},
             {"purpose": "General Corporate Purposes", "amountCr": 2.5}],
            [{"purpose": "Working Capital Requirement", "amountCr": 12.6},
             {"purpose": "General Corporate Purposes", "amountCr": 2.5}],
        ):
            changed = copy.deepcopy(evidence)
            net = self.with_total(objects_evidence(replacement), "Net Proceeds")
            net["tableScope"] = "net"
            changed["corroboratingSourceTables"] = [net]
            self.assertRejected(changed, rows)
        changed = copy.deepcopy(evidence)
        changed["corroboratingSourceTables"][0]["tableScope"] = "unspecified"
        self.assertRejected(changed, rows)

    def test_scope_cannot_be_inferred_from_an_unlabelled_total(self):
        for scope in ("net", "gross", "guessed"):
            self.assertRejected({**self.with_total(self.evidence), "tableScope": scope})
        changed = self.with_total(self.evidence, label="Net Proceeds")
        changed["tableScope"] = "gross"
        changed["tableHeaders"][0]["text"] += " % of Gross Proceeds"
        self.assertRejected(changed)

    def test_corroborating_tables_cannot_be_nested_or_unbounded(self):
        rows, evidence = self.gross_and_net()
        for corroboration in (None, {}, [], [None], evidence["corroboratingSourceTables"] * 4):
            if corroboration is None:
                continue  # No corroboration claim is valid for a standalone gross table.
            self.assertRejected({**evidence, "corroboratingSourceTables": corroboration}, rows)
        changed = copy.deepcopy(evidence)
        changed["corroboratingSourceTables"][0]["corroboratingSourceTables"] = [copy.deepcopy(evidence)]
        self.assertRejected(changed, rows)

    def test_scope_reconciliation_requires_disclosed_values_and_totals(self):
        rows, evidence = self.gross_and_net()
        changed = copy.deepcopy(evidence)
        changed.pop("tableTotal")
        self.assertRejected(changed, rows)
        changed = copy.deepcopy(evidence)
        changed["corroboratingSourceTables"][0].pop("tableTotal")
        self.assertRejected(changed, rows)
        changed_rows = copy.deepcopy(rows)
        changed_rows[0]["amountCr"] = None
        unknown = objects_evidence(changed_rows)
        unknown.update(tableScope="gross", tableTotal=evidence["tableTotal"],
                       corroboratingSourceTables=evidence["corroboratingSourceTables"])
        self.assertRejected(unknown, changed_rows)


if __name__ == "__main__":
    unittest.main()
