import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import final_prospectus_policy as policy


class FinalProspectusFinancialGuardTests(unittest.TestCase):
    def parsed(self, key, values):
        periods = []
        evidence = {}
        for year, value in zip((2025, 2024), values):
            period = f"FY{year}"
            periods.append({"period": period, key: value, "revenueCr": 100.0 - (2025 - year) * 10})
            evidence[f"{period}.{key}"] = {"normalizedValue": value, "page": 40}
            evidence[f"{period}.revenueCr"] = {
                "normalizedValue": 100.0 - (2025 - year) * 10,
                "page": 40,
            }
        return {
            "financials": {"unit": "₹ crore", "periods": periods},
            "fieldEvidence": {"financials": evidence},
        }

    def test_five_digit_eps_is_rejected_even_when_evidence_matches(self):
        record = {"openDate": "2026-04-01"}
        self.assertFalse(
            policy._financial_evidence_supported(
                record,
                self.parsed("eps", [124420.48, -65000.0]),
            )
        )

    def test_year_shaped_percentage_is_rejected(self):
        record = {"openDate": "2026-04-01"}
        self.assertFalse(
            policy._financial_evidence_supported(
                record,
                self.parsed("ronwPct", [2026.0, 2025.0]),
            )
        )

    def test_reasonable_eps_with_exact_evidence_is_allowed(self):
        record = {"openDate": "2026-04-01"}
        self.assertTrue(
            policy._financial_evidence_supported(
                record,
                self.parsed("eps", [18.4, 12.7]),
            )
        )


if __name__ == "__main__":
    unittest.main()
