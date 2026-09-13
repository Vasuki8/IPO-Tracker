import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "enrich_sebi_priority_registers_v2.py"
spec = importlib.util.spec_from_file_location("enrich_sebi_priority_registers_v2", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class SebiPriorityRegisterV2Tests(unittest.TestCase):
    def test_search_parser_keeps_rhp_and_skips_drhp(self):
        html = """
        <table><tbody>
          <tr><td>Aug 19, 2026</td><td>Public Issues</td><td><a href="https://www.sebi.gov.in/filings/public-issues/aug-2026/example-rhp_2.html">EXAMPLE LIMITED - RHP EXAMPLE LIMITED - Abridged Prospectus</a></td></tr>
          <tr><td>Dec 24, 2025</td><td>Public Issues</td><td><a href="https://www.sebi.gov.in/filings/public-issues/dec-2025/example-drhp_1.html">Example Limited - DRHP</a></td></tr>
        </tbody></table>
        """
        rows = mod.parse_search_html(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["type"], "RHP")
        self.assertEqual(rows[0]["company"], "EXAMPLE LIMITED")
        self.assertEqual(rows[0]["filedDate"], "2026-08-19")

    def test_search_parser_accepts_final_prospectus(self):
        html = """
        <table><tbody><tr><td>Sep 04, 2026</td><td>Public Issues</td><td>
        <a href="/filings/public-issues/sep-2026/deepa-jewellers-limited-prospectus_1.html">Deepa Jewellers Limited - Prospectus</a>
        </td></tr></tbody></table>
        """
        rows = mod.parse_search_html(html)
        self.assertEqual(rows[0]["type"], "PROSPECTUS")
        self.assertIn("deepa-jewellers", rows[0]["url"])

    def test_search_parser_rejects_supplemental_notice(self):
        html = """
        <table><tbody><tr><td>Sep 04, 2026</td><td>Public Issues</td><td>
        <a href="/filings/public-issues/sep-2026/example-addendum.html">Example Limited - Addendum to RHP</a>
        </td></tr></tbody></table>
        """
        self.assertEqual(mod.parse_search_html(html), [])

    def test_primary_landing_detection_excludes_direct_pdf(self):
        record = {"documents": [{"type": "RHP", "url": "https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/rhp.pdf"}]}
        self.assertFalse(mod.has_primary_landing(record))
        record["documents"].append({"type": "RHP", "url": "https://www.sebi.gov.in/filings/public-issues/aug-2026/example-rhp.html"})
        self.assertTrue(mod.has_primary_landing(record))


if __name__ == "__main__":
    unittest.main()
