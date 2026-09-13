import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_sebi_priority_registers.py"
spec = importlib.util.spec_from_file_location("enrich_sebi_priority_registers", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class SebiPriorityRegisterTests(unittest.TestCase):
    def test_register_parser_extracts_primary_filing_and_skips_addendum(self):
        html = """
        <table><tbody>
          <tr><td>Sep 04, 2026</td><td><a href="/filings/public-issues/sep-2026/example-limited-rhp_1.html">Example Limited - RHP</a></td></tr>
          <tr><td>Sep 05, 2026</td><td><a href="/filings/public-issues/sep-2026/example-limited-addendum_2.html">Example Limited - Addendum to RHP</a></td></tr>
        </tbody></table>
        """
        rows = mod.parse_register_html(html, mod.REGISTER_URLS["RHP"], "RHP")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "Example Limited")
        self.assertEqual(rows[0]["filedDate"], "2026-09-04")
        self.assertEqual(rows[0]["type"], "RHP")

    def test_exact_normalized_company_match_respects_date_window(self):
        candidates = [
            {
                "companyKey": mod.core.canonical_company("Deepa Jewellers Limited"),
                "company": "Deepa Jewellers Limited",
                "filedDate": "2026-08-28",
                "url": "https://www.sebi.gov.in/filings/public-issues/aug-2026/deepa-rhp.html",
                "type": "RHP",
                "title": "Deepa Jewellers Limited - RHP",
            }
        ]
        record = {"company": "Deepa Jewellers Limited", "openDate": "2026-09-01"}
        self.assertEqual(len(mod.match_record(record, candidates)), 1)
        record["openDate"] = "2025-01-01"
        self.assertEqual(mod.match_record(record, candidates), [])

    def test_fuzzy_fallback_is_tight(self):
        candidates = [
            {
                "companyKey": mod.core.canonical_company("Asset Reconstruction Company India Limited"),
                "company": "Asset Reconstruction Company India Limited",
                "filedDate": "2026-09-02",
                "url": "https://www.sebi.gov.in/filings/public-issues/sep-2026/arcil-rhp.html",
                "type": "RHP",
                "title": "Asset Reconstruction Company India Limited - RHP",
            }
        ]
        close = {"company": "Asset Reconstruction Company (India) Limited", "openDate": "2026-09-09"}
        unrelated = {"company": "Asset Reconstruction Holdings Limited", "openDate": "2026-09-09"}
        self.assertEqual(len(mod.match_record(close, candidates)), 1)
        self.assertEqual(mod.match_record(unrelated, candidates), [])

    def test_title_company_removes_offer_document_suffix(self):
        self.assertEqual(
            mod.title_company("ESDS Software Solution Limited - RHP ESDS Software Solution Limited - Abridged Prospectus"),
            "ESDS Software Solution Limited",
        )
        self.assertEqual(mod.title_company("ANNU PROJECTS LIMITED - PROSPECTUS"), "ANNU PROJECTS LIMITED")


if __name__ == "__main__":
    unittest.main()
