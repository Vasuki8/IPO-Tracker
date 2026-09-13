import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_offer_docs_v8.py"
spec = importlib.util.spec_from_file_location("run_offer_docs_v8", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class _FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class _FakeReader:
    is_encrypted = False

    def __init__(self, _stream):
        pages = [_FakePage("") for _ in range(30)]
        pages.append(
            _FakePage(
                "SUMMARY OF FINANCIAL INFORMATION FY2026 FY2025 "
                "Revenue from Operations 100 90 Profit after Tax 20 18 Net Worth 50 40"
            )
        )
        pages.append(
            _FakePage(
                "Shareholding Pattern of our Company "
                "(A) Promoter and Promoter Group 9 52,071,136 61.53% "
                "(B) Public 12 32,567,414 38.47%"
            )
        )
        self.pages = pages


class OfferDocsV8Tests(unittest.TestCase):
    def test_parser_version_is_bumped(self):
        self.assertEqual(mod.PARSER_VERSION, 8)
        self.assertEqual(mod.base.PARSER_VERSION, 8)

    def test_explicit_combined_shareholding_page_gets_selection_bonus(self):
        generic = "Shareholding Pattern pre-Offer Promoter Group 60.00%"
        combined = (
            "Shareholding Pattern of our Company "
            "(A) Promoter and Promoter Group 9 52,071,136 61.53%"
        )
        self.assertGreater(mod._shareholding_page_score(combined), mod._shareholding_page_score(generic))

    def test_financial_and_shareholding_pages_get_independent_quotas(self):
        original = mod.PdfReader
        mod.PdfReader = _FakeReader
        try:
            text, pages_read, page_count = mod.extract_targeted_pdf_text(
                b"fake",
                "BASE",
                need_financials=True,
                need_shareholding=True,
                max_hits=1,
                context_pages=0,
            )
        finally:
            mod.PdfReader = original

        self.assertIn("SUMMARY OF FINANCIAL INFORMATION", text)
        self.assertIn("(A) Promoter and Promoter Group", text)
        self.assertEqual(pages_read, 32)
        self.assertEqual(page_count, 32)

    def test_v7_real_layout_parser_remains_active(self):
        text = """
        Pre-Offer shareholding as at the date of the Red Herring Prospectus
        Promoter
        1. Siddharth Gunvant Shah 33,608,600 51.03 [●] [●]
        Sub-total (A) 49,858,600 75.70 [●] [●]
        Promoter Group (Other than our Promoters)
        1. Kishor Ratilal Parekh 25,000 0.04 [●] [●]
        Sub-total (B) 25,000 0.04 [●] [●]
        Additional top 10 Shareholders
        """
        parsed = mod.extract_promoter_shareholding(text)
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed["promoterPreIssuePct"], 75.74, places=2)


if __name__ == "__main__":
    unittest.main()
