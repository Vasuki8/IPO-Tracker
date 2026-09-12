import importlib.util
import sys
import unittest
from pathlib import Path

import requests

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v4.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v4", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OfferDocsV4Tests(unittest.TestCase):
    def test_upto_fresh_and_ofs_share_counts_are_parsed(self):
        text = """
        DETAILS OF THE OFFER
        The Public Offer comprises a Fresh Issue of upto 34,46,400 Equity Shares
        aggregating up to Rs. 64.10 Crores and an Offer for Sale of upto 8,61,600
        Equity Shares aggregating up to Rs. 16.03 Crores.
        GENERAL RISK
        """
        parsed = mod.extract_issue_composition(text, {"min": 177, "max": 186})
        self.assertEqual(parsed["freshShares"], 3_446_400)
        self.assertEqual(parsed["ofsShares"], 861_600)
        self.assertAlmostEqual(parsed["freshIssueCr"], 64.1, places=2)
        self.assertAlmostEqual(parsed["ofsCr"], 16.03, places=2)

    def test_explicit_monetary_amounts_work_without_share_counts(self):
        text = """
        DETAILS OF THE ISSUE
        The Offer comprises a Fresh Issue aggregating up to INR 120.50 Crores
        and an Offer for Sale aggregating up to Rs. 24.75 Crores.
        GENERAL RISK
        """
        parsed = mod.extract_issue_composition(text, None)
        self.assertAlmostEqual(parsed["freshIssueCr"], 120.50, places=2)
        self.assertAlmostEqual(parsed["ofsCr"], 24.75, places=2)
        self.assertAlmostEqual(parsed["totalIssueSizeCr"], 145.25, places=2)

    def test_million_and_lakh_amounts_convert_to_crore(self):
        self.assertAlmostEqual(
            mod._money_cr_near("Fresh\\s+Issue", "Fresh Issue aggregating up to ₹ 945.0 million"),
            94.5,
            places=2,
        )
        self.assertAlmostEqual(
            mod._money_cr_near("Offer\\s+for\\s+Sale", "Offer for Sale amounting to Rs. 2,500 lakhs"),
            25.0,
            places=2,
        )

    def test_explicit_fresh_only_sets_zero_ofs(self):
        text = """
        DETAILS OF THE ISSUE
        The Issue comprises solely of a Fresh Issue of up to 15,000,000 Equity Shares.
        GENERAL RISK
        """
        parsed = mod.extract_issue_composition(text, {"min": 130, "max": 140})
        self.assertEqual(parsed["freshShares"], 15_000_000)
        self.assertEqual(parsed["ofsShares"], 0)
        self.assertEqual(parsed["ofsCr"], 0.0)
        self.assertAlmostEqual(parsed["freshIssueCr"], 210.0, places=2)
        self.assertAlmostEqual(parsed["totalIssueSizeCr"], 210.0, places=2)

    def test_promoter_holding_pattern_table_parses_pre_issue_pct(self):
        text = """
        SHAREHOLDING PATTERN
        Particulars  Pre IPO Shares  Pre IPO % Shares  Post IPO Shares  Post IPO % Shares
        Promoter and Promoter Group  6,449,280  100%  6,449,280  73.61%
        Others  -  0%  2,312,000  26.39%
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 100.0, places=2)

    def test_promoter_narrative_pre_offer_pct_is_parsed(self):
        text = """
        PRE-OFFER SHAREHOLDING
        Our Promoters collectively hold 12,000,000 Equity Shares constituting
        74.25% of the pre-Offer share capital of our Company.
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 74.25, places=2)

    def test_promoter_contribution_lock_in_is_not_treated_as_pre_issue_holding(self):
        text = """
        CAPITAL STRUCTURE
        The pre-Issue paid-up capital consists of 10,000,000 Equity Shares.
        Promoters Contribution 20% of the post-Issue capital shall be locked in.
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNone(parsed)

    def test_transport_failure_is_retried(self):
        calls = []
        original = mod._ORIGINAL_DOWNLOAD_PDF
        original_sleep = mod.time.sleep

        def flaky(session, url):
            calls.append(url)
            if len(calls) < 3:
                raise requests.exceptions.ChunkedEncodingError("incomplete read")
            return b"%PDF-success"

        try:
            mod._ORIGINAL_DOWNLOAD_PDF = flaky
            mod.time.sleep = lambda _: None
            data = mod.download_pdf(object(), "https://www.sebi.gov.in/test.pdf", attempts=3)
        finally:
            mod._ORIGINAL_DOWNLOAD_PDF = original
            mod.time.sleep = original_sleep

        self.assertEqual(data, b"%PDF-success")
        self.assertEqual(len(calls), 3)

    def test_semantic_validation_error_is_not_retried(self):
        calls = []
        original = mod._ORIGINAL_DOWNLOAD_PDF

        def invalid(session, url):
            calls.append(url)
            raise ValueError("URL did not return a PDF")

        try:
            mod._ORIGINAL_DOWNLOAD_PDF = invalid
            with self.assertRaises(ValueError):
                mod.download_pdf(object(), "https://www.sebi.gov.in/test.pdf", attempts=3, retry_delay=0)
        finally:
            mod._ORIGINAL_DOWNLOAD_PDF = original

        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
