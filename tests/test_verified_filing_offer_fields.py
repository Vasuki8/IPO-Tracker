import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "apply_verified_filing_offer_fields.py"
spec = importlib.util.spec_from_file_location("apply_verified_filing_offer_fields", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class VerifiedFilingOfferFieldTests(unittest.TestCase):
    def filing_record(self, record_id, company):
        return {
            "id": record_id,
            "company": company,
            "documents": [{"type": "DRHP", "url": "https://www.sebi.gov.in/example.pdf"}],
            "lifecycle": {"stage": "drhp"},
            "sources": [],
            "observations": {},
        }

    def test_registry_covers_current_p3_records(self):
        self.assertEqual(
            set(mod.VERIFIED_FILING_OFFER_FIELDS),
            {
                "national-stock-exchange-of-india-limited",
                "m-k-c-agro-fresh-limited",
                "nopaperforms-solutions-limited",
                "torrent-gas-limited",
            },
        )

    def test_expected_shareholding_values(self):
        expected = {
            "national-stock-exchange-of-india-limited": 0.0,
            "m-k-c-agro-fresh-limited": 28.54,
            "nopaperforms-solutions-limited": 30.19,
            "torrent-gas-limited": 100.0,
        }
        for record_id, value in expected.items():
            fields = mod.VERIFIED_FILING_OFFER_FIELDS[record_id]["fields"]
            self.assertEqual(fields["shareholding"]["promoterPreIssuePct"], value)

    def test_nse_retains_no_promoter_semantics_and_all_brlms(self):
        fields = mod.VERIFIED_FILING_OFFER_FIELDS["national-stock-exchange-of-india-limited"]["fields"]
        self.assertEqual(fields["shareholding"]["promoterPreIssuePct"], 0.0)
        self.assertEqual(fields["shareholding"]["promoterStatus"], "No identifiable promoter")
        self.assertEqual(len(fields["leadManagers"]), 20)
        self.assertIn("SBI Capital Markets Limited", fields["leadManagers"])
        self.assertIn("360 ONE WAM Limited", fields["leadManagers"])

    def test_fill_only_with_strict_identity_and_filing_stage(self):
        entry = mod.VERIFIED_FILING_OFFER_FIELDS["m-k-c-agro-fresh-limited"]
        record = self.filing_record("m-k-c-agro-fresh-limited", "M K C AGRO FRESH LIMITED")
        changed = mod.apply_verified_filing_offer_fields(record, entry)
        self.assertEqual(changed, ["shareholding"])
        self.assertEqual(record["shareholding"]["promoterPreIssuePct"], 28.54)
        self.assertIn("VerifiedFilingOfferFields", record["observations"])

        record["shareholding"]["promoterPreIssuePct"] = 41.0
        self.assertEqual(mod.apply_verified_filing_offer_fields(record, entry), [])
        self.assertEqual(record["shareholding"]["promoterPreIssuePct"], 41.0)

    def test_wrong_company_or_non_filing_record_is_rejected(self):
        entry = mod.VERIFIED_FILING_OFFER_FIELDS["torrent-gas-limited"]
        wrong_company = self.filing_record("torrent-gas-limited", "Different Gas Limited")
        self.assertEqual(mod.apply_verified_filing_offer_fields(wrong_company, entry), [])

        listed = {
            "id": "torrent-gas-limited",
            "company": "Torrent Gas Limited",
            "openDate": "2026-08-01",
            "closeDate": "2026-08-05",
            "listingDate": "2026-08-10",
            "documents": [{"type": "DRHP", "url": "https://www.sebi.gov.in/example.pdf"}],
        }
        self.assertEqual(mod.apply_verified_filing_offer_fields(listed, entry), [])

    def test_zero_shareholding_is_treated_as_real_value(self):
        entry = mod.VERIFIED_FILING_OFFER_FIELDS["national-stock-exchange-of-india-limited"]
        record = self.filing_record(
            "national-stock-exchange-of-india-limited",
            "National Stock Exchange of India Limited",
        )
        changed = mod.apply_verified_filing_offer_fields(record, entry)
        self.assertIn("shareholding", changed)
        self.assertIn("leadManagers", changed)
        self.assertEqual(record["shareholding"]["promoterPreIssuePct"], 0.0)
        self.assertEqual(record["shareholding"]["promoterStatus"], "No identifiable promoter")


if __name__ == "__main__":
    unittest.main()
