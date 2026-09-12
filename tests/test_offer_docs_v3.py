import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v3.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v3", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


MODERN = """
EXAMPLE TECHNOLOGIES LIMITED
OUR PROMOTERS
Our Promoters are ARUN KUMAR, BINA KUMAR and EXAMPLE HOLDINGS PRIVATE LIMITED.

ISSUE DETAILS
Fresh Issue: up to 2,000,000 Equity Shares aggregating up to ₹ 24.00 crore
Offer for Sale: up to 500,000 Equity Shares aggregating up to ₹ 6.00 crore
Total Issue Size aggregating up to ₹ 30.00 crore

BOOK RUNNING LEAD MANAGER TO THE OFFER
Alpha Capital Markets Private Limited
REGISTRAR TO THE OFFER
Bigshare Services Private Limited
ISSUE OPENS September 20, 2026

Objects of the Offer
(₹ in crore)
1. Funding working capital requirements 10.00
2. Repayment of identified borrowings 8.00
3. General corporate purposes [●]

Restated Standalone Financial Information
(₹ in crore except percentages and per share data)
Particulars March 31, 2026 March 31, 2025 March 31, 2024
Revenue from Operations 125.00 100.00 80.00
EBITDA 25.00 20.00 14.00
Profit for the year 12.50 10.00 7.00
Net Worth 60.00 45.00 35.00

Key Performance Indicators (KPIs)
Particulars March 31, 2026 March 31, 2025 March 31, 2024
Return on Equity 20.83% 22.22% 20.00%
Basic EPS 5.00 4.00 2.80
Risk Factors
"""


class OfferDocumentV3Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 3)
        self.assertEqual(mod.base.PARSER_VERSION, 3)

    def test_explicit_document_amounts_override_derived_estimates(self):
        issue = mod.extract_issue_composition(MODERN, {"min": 10, "max": 12})
        self.assertEqual(issue["freshShares"], 2_000_000)
        self.assertEqual(issue["ofsShares"], 500_000)
        self.assertEqual(issue["freshIssueCr"], 24.0)
        self.assertEqual(issue["ofsCr"], 6.0)
        self.assertEqual(issue["totalIssueSizeCr"], 30.0)

    def test_brlm_header_prefix_is_not_part_of_entity_name(self):
        leads, registrar = mod.extract_intermediaries(MODERN)
        self.assertIn("Alpha Capital Markets Private Limited", leads)
        self.assertNotIn("TO THE OFFER Alpha Capital Markets Private Limited", leads)
        self.assertEqual(registrar, "Bigshare Services Private Limited")

    def test_prefers_abridged_but_allows_direct_official_rhp_fallback(self):
        fallback_only = {
            "documents": [
                {
                    "type": "RHP",
                    "title": "Example Red Herring Prospectus",
                    "url": "https://www.sebi.gov.in/sebi_data/attachdocs/example-rhp.pdf",
                    "filedDate": "2026-09-10",
                }
            ]
        }
        self.assertEqual(
            mod.choose_document(fallback_only)["url"],
            "https://www.sebi.gov.in/sebi_data/attachdocs/example-rhp.pdf",
        )

        with_ap = {
            "documents": fallback_only["documents"]
            + [
                {
                    "type": "RHP",
                    "title": "Example Abridged Prospectus",
                    "url": "https://www.sebi.gov.in/sebi_data/attachdocs/example_AP_p.pdf",
                    "filedDate": "2026-09-09",
                }
            ]
        }
        self.assertIn("AP_p.pdf", mod.choose_document(with_ap)["url"])

    def test_rejects_non_sebi_pdf_fallback(self):
        record = {
            "documents": [
                {
                    "type": "RHP",
                    "title": "Third-party copy",
                    "url": "https://example.com/rhp.pdf",
                }
            ]
        }
        self.assertIsNone(mod.choose_document(record))


if __name__ == "__main__":
    unittest.main()
