import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_missing_queue as queue_builder
import final_prospectus_parser as parser
import final_prospectus_policy as policy


# Sunshine Pictures Final Prospectus, PDF page 13 (21 August 2026):
# https://sunshinepictures.in/wp-content/uploads/2026/08/FinalSunshineProspectus-GYR.pdf
SUNSHINE_BAND_DEFINITION = """
[PAGE 13]
“Price Band”        Price band of a minimum price of ₹ 342 per Equity Share (Floor Price) and the maximum price
                    of ₹ 360 per Equity Share (Cap Price) including any revisions thereof.
"""


class FinalProspectusPriceBandDefinitionTests(unittest.TestCase):
    def test_definition_after_cover_retains_explicit_floor_and_cap(self):
        text = "PROSPECTUS\n100% Book Built Offer\nOFFER PRICE: ₹ 360 PER EQUITY SHARE"
        text += "\f" * 12 + SUNSHINE_BAND_DEFINITION
        parsed = parser.parse_document_text(text)
        self.assertEqual(parsed["priceBand"], {"min": 342.0, "max": 360.0})
        self.assertEqual(parsed["issuePrice"], 360.0)
        self.assertEqual(parsed["fieldEvidence"]["priceBand"]["page"], 13)
        self.assertIn("Floor Price", parsed["fieldEvidence"]["priceBand"]["heading"])

    def test_explicit_band_repairs_legacy_one_point_value_with_own_provenance(self):
        record = {
            "id": "sunshine",
            "company": "Sunshine Pictures Limited",
            "openDate": "2026-08-18",
            "closeDate": "2026-08-20",
            "priceBand": {"min": 360, "max": 360},
            "staticSourcePolicy": {
                "policy": "final-prospectus-only",
                "pendingRevalidationFields": ["priceBand"],
            },
        }
        text = "OFFER PRICE: ₹ 360 PER EQUITY SHARE\f" + SUNSHINE_BAND_DEFINITION
        parsed = parser.parse_document_text(text)
        doc = {
            "type": "PROSPECTUS",
            "title": "Sunshine Pictures Limited Final Prospectus",
            "url": "https://sunshinepictures.in/wp-content/uploads/2026/08/FinalSunshineProspectus-GYR.pdf",
            "filedDate": "2026-08-21",
        }
        policy.apply_final_prospectus_static_fields(
            record, parsed, doc, sha256="verified-pdf", parser_version=parser.PARSER_VERSION,
        )
        self.assertEqual(record["priceBand"], {"min": 342.0, "max": 360.0})
        proof = record["staticFieldProvenance"]["priceBand"]
        self.assertEqual(proof["value"], record["priceBand"])
        self.assertEqual(proof["evidence"]["page"], 13)
        self.assertFalse(queue_builder.fixed_price_band_finally_verified(record))
        self.assertNotIn("priceBand", queue_builder.pending_final_prospectus_fields(record, date(2026, 9, 17)))

    def test_conflicting_explicit_ranges_stay_unresolved(self):
        text = SUNSHINE_BAND_DEFINITION + "\fThe Price Band was ₹ 330 to ₹ 360 per Equity Share."
        self.assertEqual(parser.extract_explicit_price_band(text), (None, {}))

    def test_reversed_or_incompletely_labelled_definition_is_not_a_band(self):
        cases = (
            SUNSHINE_BAND_DEFINITION.replace("₹ 342", "₹ 370"),
            SUNSHINE_BAND_DEFINITION.replace("(Floor Price)", "(Acquisition Price)"),
            SUNSHINE_BAND_DEFINITION.replace("(Cap Price)", "(Historical Price)"),
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(parser.extract_explicit_price_band(text), (None, {}))


if __name__ == "__main__":
    unittest.main()
