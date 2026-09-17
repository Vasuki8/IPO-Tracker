import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apply_corrections as corrections
import build_company_pages as pages
import build_missing_queue as queue_builder
import final_prospectus_parser as parser
import run_offer_documents as primary
import run_p4_offer_residuals as residual


SOURCE_URL = "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1788323000985.pdf"
SOURCE_HASH = "cd3026b4bc426e5ba3a455e10ef4b6d0de0d0b393ee0db3590dba6cd45e8efed"
LEGACY_FINANCIALS = {
    "unit": "₹ crore",
    "periods": [
        {"period": "FY2026", "revenueCr": 1467.26, "ebitdaCr": 10.26, "roePct": 4.55,
         "patCr": 3.103, "netWorthCr": 1.273, "ronwPct": 12.73, "eps": 2013.0},
        {"period": "FY2025", "revenueCr": 5389.49, "ebitdaCr": 2.86, "roePct": 14.49,
         "patCr": 202.4, "netWorthCr": 1.002, "ronwPct": 10.02, "eps": 3.0},
        {"period": "FY2024", "revenueCr": 4354.95, "ebitdaCr": 4.89, "roePct": 10.53,
         "patCr": 2.5, "netWorthCr": 0.444, "ronwPct": 4.44, "eps": 133.0},
    ],
}

# Actual Priority Final Prospectus definitions, PDF page 11 (printed page 7).
# The pre-IPO placement and public issue use different prices. The retained
# one-point legacy band must not turn the placement into the final issue price.
PRIORITY_BAND = """[PAGE 11]
Price Band        Price band of a minimum price of ₹190 per Equity Share (i.e., the Floor Price) and the maximum
                  price of ₹200 per Equity Share (i.e., the Cap Price) including any revisions thereof.
"""
PRIORITY_FRONT = """[PAGE 1]
PROSPECTUS
Dated: September 01, 2026
100% Book Built Offer
PRIORITY JEWELS LIMITED
CORPORATE IDENTITY NUMBER: U52393MH2007PLC174977
REGISTERED AND CORPORATE OFFICE
Mumbai, Maharashtra
""" + "\f" + """[PAGE 3]
INITIAL PUBLIC OFFERING OF 45,75,000 EQUITY SHARES OF FACE VALUE OF ₹10 EACH
OF PRIORITY JEWELS LIMITED FOR CASH AT A PRICE OF ₹ 200 PER EQUITY SHARE
(INCLUDING A PREMIUM OF ₹ 190 PER EQUITY SHARE) ("ISSUE PRICE") AGGREGATING TO ₹ 915.00 MILLION.
OUR COMPANY HAD UNDERTAKEN A PRE-IPO PLACEMENT OF 8,25,000 EQUITY SHARES
AT AN ISSUE PRICE OF ₹ 190.00 PER EQUITY SHARE.
""" + "\f" * 9 + PRIORITY_BAND

# Bounded source layout from PDF page 105 (printed page 101). These four
# numeric columns start with an interim quarter. The old canonical values
# also confused the Net Debt/EBITDA ratio with the separate monetary metric.
PRIORITY_FINANCIAL_TABLE = """[PAGE 105]
                  Financial KPIs:

                                                                                                                                          (in ₹ million unless otherwise indicated)
                                        Particulars                Three months ended                    Fiscal 2026                   Fiscal 2025                  Fiscal 2024
                                                                       June 30, 2026
                   Revenue from operations(i)                                        1,467.26                        5,389.49                   4,354.95                      4,105.05
                   Earnings       before     Interest,     tax,                        102.92                          336.23                     242.80                        193.48
                   depreciation         &       amortisation
                   (EBITDA)(iv)
                   EBITDA Margin(v) (in %)                                                7.01                            6.24                       5.58                           4.71
                   PAT(vi)                                                              64.77                          176.48                     105.12                          71.48
                   PAT Margin(vii) (in %)                                                 4.39                            3.27                       2.41                           1.74
                   Return on Equity (RoE)(viii) (in %)                                  4.55*                           14.49                      10.53                            7.35
                   Net Debt to EBITDA(xi)                                              10.26*                             2.86                       4.89                           5.68
                  *Not annualised
"""


def priority_registry():
    registry = json.loads((ROOT / "data/verified_corrections.json").read_text())
    return {"revision": registry["revision"],
            "changes": [entry for entry in registry["changes"] if entry["id"] == "priority"]}


def priority_record():
    # This fixture also includes a valid market issue price to prove that the
    # quarantine and ambiguous historical placement do not overwrite it.
    role_proof = {"sourceUrl": SOURCE_URL, "sha256": SOURCE_HASH,
                  "value": ["Mefcom Capital Markets Limited"]}
    return {
        "id": "priority", "company": "Priority Jewels Limited", "symbol": "PRIORITY",
        "openDate": "2026-08-28", "closeDate": "2026-09-01", "listingDate": "2026-09-04",
        "financials": copy.deepcopy(LEGACY_FINANCIALS),
        "priceBand": {"min": 190.0, "max": 190.0},
        "listing": {"issuePrice": 200.0, "issuePriceSource": {"name": "NSE monthly report"}},
        "leadManagers": ["Mefcom Capital Markets Limited"],
        "registrar": "MUFG Intime India Private Limited",
        "documents": [{"type": "PROSPECTUS", "title": "Priority Jewels Limited Final Prospectus",
                       "url": SOURCE_URL, "filedDate": "2026-09-02", "source": "SEBI"}],
        "staticFieldProvenance": {"leadManagers": role_proof},
        "documentFieldProvenance": {"sourceUrl": SOURCE_URL, "sha256": SOURCE_HASH,
                                    "evidence": {"leadManagers": {"page": 2}}},
        "documentRepair": {"financialStatus": "needs_review"},
        "staticSourcePolicy": {"policy": "final-prospectus-only",
                               "pendingRevalidationFields": ["financials"]},
        "dataCorrections": [{"field": "leadManagers", "reason": "Earlier accepted source repair"}],
    }


class PriorityReviewedQuarantineTests(unittest.TestCase):
    def test_registry_retires_stale_group_and_records_exact_review_evidence(self):
        entries = priority_registry()["changes"]
        self.assertEqual([entry["field"] for entry in entries], ["financials"])
        entry = entries[0]
        self.assertIsNone(entry["after"])
        self.assertEqual(entry["beforeHash"], corrections.fingerprint(LEGACY_FINANCIALS))
        self.assertEqual(entry["source"]["url"], SOURCE_URL)
        self.assertEqual(entry["evidence"]["sha256"], SOURCE_HASH)
        self.assertEqual(entry["evidence"]["cin"], "U52393MH2007PLC174977")
        self.assertEqual(entry["evidence"]["financialScopeByPeriod"], {
            "FY2026": "consolidated", "FY2025": "standalone", "FY2024": "standalone",
        })

    def test_exact_financial_payload_is_quarantined_without_reverting_newer_repairs(self):
        record = priority_record()
        other = {"id": "unrelated", "company": "Unrelated Limited", "financials": {"periods": []}}
        before, other_before = copy.deepcopy(record), copy.deepcopy(other)
        self.assertNotIn("financials", record["staticFieldProvenance"])
        self.assertEqual(corrections.apply({"ipos": [record, other]}, priority_registry()), (1, []))
        self.assertIsNone(record["financials"])
        self.assertEqual(other, other_before)
        for field in before.keys() - {"financials", "dataCorrections"}:
            self.assertEqual(record[field], before[field], field)
        self.assertEqual(record["dataCorrections"][:-1], before["dataCorrections"])
        audit = record["dataCorrections"][-1]
        self.assertEqual(audit["before"], LEGACY_FINANCIALS)
        self.assertIsNone(audit["after"])
        self.assertEqual(audit["evidence"]["sha256"], SOURCE_HASH)

    def test_reapplying_review_does_not_duplicate_audit_or_source(self):
        payload = {"ipos": [priority_record()]}
        self.assertEqual(corrections.apply(payload, priority_registry()), (1, []))
        once = copy.deepcopy(payload["ipos"])
        self.assertEqual(corrections.apply(payload, priority_registry()), (0, []))
        self.assertEqual(payload["ipos"], once)

    def test_changed_issuer_or_offer_identity_refuses_correction(self):
        for field in ("id", "company", "symbol", "openDate"):
            with self.subTest(field=field):
                record = priority_record()
                record[field] = "2026-08-27" if field == "openDate" else "different"
                before = copy.deepcopy(record)
                applied, conflicts = corrections.apply({"ipos": [record]}, priority_registry())
                self.assertEqual(applied, 0)
                self.assertTrue(conflicts)
                self.assertEqual(record, before)

    def test_changed_financial_hash_preserves_competing_source_repair(self):
        record = priority_record()
        record["financials"] = {"unit": "₹ crore", "periods": [{"period": "FY2026", "revenueCr": 538.949}]}
        record["staticFieldProvenance"]["financials"] = {
            "sourceUrl": SOURCE_URL, "sha256": "later-verified-source",
            "value": copy.deepcopy(record["financials"]),
        }
        before = copy.deepcopy(record)
        applied, conflicts = corrections.apply({"ipos": [record]}, priority_registry())
        self.assertEqual(applied, 0)
        self.assertTrue(conflicts)
        self.assertEqual(record, before)

    def test_quarantine_remains_actionable_and_is_not_embedded_as_public_financials(self):
        record = priority_record()
        corrections.apply({"ipos": [record]}, priority_registry())
        entry = queue_builder.queue_entry(record, date(2026, 9, 17))
        self.assertEqual(entry["priority"], 2)
        self.assertIn("offer.financials", entry["missingFields"])
        profile = pages.public_profile_record(record)
        self.assertFalse((profile.get("financials") or {}).get("periods"))
        self.assertNotIn("dataCorrections", profile)


class PriorityPriceBandAndCollectionTests(unittest.TestCase):
    def test_parenthetical_definition_repairs_band_with_final_source_evidence(self):
        record = priority_record()
        parsed = parser.parse_document_text(PRIORITY_FRONT)
        doc = record["documents"][0]
        primary.correct_record(record, parsed, doc, SOURCE_HASH, 11, 387)
        self.assertEqual(record["priceBand"], {"min": 190.0, "max": 200.0})
        self.assertEqual(record["listing"]["issuePrice"], 200.0)
        proof = record["staticFieldProvenance"]["priceBand"]
        self.assertEqual(proof["value"], record["priceBand"])
        self.assertEqual(proof["sourceUrl"], SOURCE_URL)
        self.assertEqual(proof["sha256"], SOURCE_HASH)
        self.assertEqual(proof["evidence"]["page"], 11)
        self.assertFalse(queue_builder.fixed_price_band_finally_verified(record))

    def test_placement_does_not_win_over_ambiguous_final_price(self):
        self.assertEqual(parser.extract_final_issue_price(PRIORITY_FRONT), (None, {}))
        self.assertNotIn("issuePrice", parser.parse_document_text(PRIORITY_FRONT))

    def test_parenthetical_labels_and_unambiguous_range_are_still_required(self):
        cases = (
            PRIORITY_BAND.replace("Floor Price", "Acquisition Price"),
            PRIORITY_BAND.replace("Cap Price", "Historical Price"),
            PRIORITY_BAND.replace("₹190", "₹210"),
            PRIORITY_BAND + "\fThe Price Band was ₹ 180 to ₹ 200 per Equity Share.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(parser.extract_explicit_price_band(text), (None, {}))

    def test_cached_primary_and_residual_collection_do_not_restore_unverified_financials(self):
        record = priority_record()
        payload = {"ipos": [record]}
        corrections.apply(payload, priority_registry())
        queue_payload = {"queue": [queue_builder.queue_entry(record, date(2026, 9, 17))]}
        text = PRIORITY_FRONT + "\f" + PRIORITY_FINANCIAL_TABLE
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        pdf = io.BytesIO()
        writer.write(pdf)
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            (cache / (hashlib.sha256(SOURCE_URL.encode()).hexdigest() + ".pdf")).write_bytes(pdf.getvalue())
            queue_file = cache / "queue.json"
            queue_file.write_text(json.dumps(queue_payload))
            with (
                patch.object(primary, "CACHE", cache),
                patch.object(primary, "QUEUE_FILE", queue_file),
                patch.object(parser, "extract_pdf_text", return_value=(text, 12, 387)),
                patch.object(primary, "_download_pdf_once", side_effect=AssertionError("Unexpected network request")) as network,
                redirect_stdout(io.StringIO()),
            ):
                main_health = primary.run(payload, limit=1, force=True, workers=1, cached_only=True, priority_max=4)
                self.assertEqual(main_health["attempted"], 1)
                self.assertEqual(main_health["failed"], 0)
                self.assertIsNone(record["financials"])
                residual_health = residual.run(payload, limit=1, force=True, workers=1, queue_payload=queue_payload)
                self.assertEqual(residual_health["attempted"], 1)
                self.assertEqual(residual_health["failed"], 0)
                network.assert_not_called()
        self.assertIsNone(record["financials"])
        self.assertNotIn("financials", record["staticFieldProvenance"])
        self.assertNotIn("financials", record["documentFieldProvenance"]["evidence"])
        self.assertEqual(record["documentRepair"]["financialStatus"], "needs_review")
        self.assertEqual(record["priceBand"], {"min": 190.0, "max": 200.0})
        self.assertEqual(record["listing"]["issuePrice"], 200.0)
        self.assertEqual(record["leadManagers"], ["Mefcom Capital Markets Limited"])
        self.assertEqual(record["registrar"], "MUFG Intime India Private Limited")
        self.assertIn("offer.financials", queue_builder.queue_entry(record, date(2026, 9, 17))["missingFields"])


if __name__ == "__main__":
    unittest.main()
