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

    def test_rhp_landing_does_not_stop_final_prospectus_search(self):
        record = {"company": "Example Limited", "openDate": "2026-08-20", "documents": [{"type": "RHP", "title": "Example Limited - RHP", "url": "https://www.sebi.gov.in/filings/public-issues/aug-2026/example-rhp.html"}]}
        self.assertTrue(mod.has_primary_landing(record))
        self.assertFalse(mod.has_final_prospectus_landing(record))

    def test_final_prospectus_landing_stops_repeat_search_when_issuer_qualified(self):
        record = {"company": "Example Limited", "openDate": "2026-09-01", "documents": [{"type": "PROSPECTUS", "title": "Example Limited - Prospectus", "url": "https://www.sebi.gov.in/filings/public-issues/sep-2026/example-limited-prospectus.html", "filedDate": "2026-09-08"}]}
        self.assertTrue(mod.has_final_prospectus_landing(record))

    def test_direct_final_prospectus_stops_repeat_search_when_url_names_issuer(self):
        record = {"company": "Happy Steels Limited", "openDate": "2026-07-09", "documents": [{"type": "PROSPECTUS", "title": "Final Prospectus", "url": "https://nsearchives.nseindia.com/emerge/corporates/content/HappySteelsLimited_PROSP.pdf", "filedDate": "2026-07-14"}]}
        self.assertTrue(mod.has_final_prospectus_landing(record))

    def test_generic_unqualified_final_pdf_does_not_stop_repeat_search(self):
        record = {"company": "Transrail Lighting Limited", "openDate": "2024-12-19", "closeDate": "2024-12-23", "documents": [{"type": "PROSPECTUS", "title": "Final Prospectus", "url": "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1752651007576_865.pdf", "filedDate": "2025-07-16"}]}
        self.assertFalse(mod.has_final_prospectus_landing(record))

    def test_final_match_filter_rejects_rhp_for_same_issuer(self):
        record = {"company": "Example Limited", "openDate": "2026-09-01"}
        candidates = [
            {"type": "RHP", "title": "Example Limited - RHP", "company": "Example Limited", "companyKey": mod.core.canonical_company("Example Limited"), "url": "https://www.sebi.gov.in/filings/public-issues/aug-2026/example-rhp.html", "filedDate": "2026-08-28"},
            {"type": "PROSPECTUS", "title": "Example Limited - Prospectus", "company": "Example Limited", "companyKey": mod.core.canonical_company("Example Limited"), "url": "https://www.sebi.gov.in/filings/public-issues/sep-2026/example-prospectus.html", "filedDate": "2026-09-08"},
        ]
        matches = mod.final_prospectus_matches(record, candidates)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["type"], "PROSPECTUS")

    def test_attach_matches_refuses_rhp_even_if_called_directly(self):
        record = {"documents": []}
        added = mod._attach_matches(record, [{"type": "RHP", "title": "Example Limited - RHP", "url": "https://www.sebi.gov.in/filings/public-issues/aug-2026/example-rhp.html", "filedDate": "2026-08-28", "sourcePage": mod.SEARCH_URL}])
        self.assertEqual(added, 0)
        self.assertEqual(record["documents"], [])

    def test_bounded_search_rotates_unattempted_then_oldest_attempts(self):
        records = [
            {"id": "new-attempt", "openDate": "2026-08-20", mod.ATTEMPT_KEY: {"lastAttemptAt": "2026-09-13T12:00:00+05:30"}},
            {"id": "older-unattempted", "openDate": "2026-07-01"},
            {"id": "old-attempt", "openDate": "2026-08-10", mod.ATTEMPT_KEY: {"lastAttemptAt": "2026-09-12T12:00:00+05:30"}},
            {"id": "newer-unattempted", "openDate": "2026-08-01"},
        ]
        ordered = sorted(records, key=mod.search_candidate_sort_key)
        self.assertEqual([row["id"] for row in ordered], ["newer-unattempted", "older-unattempted", "old-attempt", "new-attempt"])


if __name__ == "__main__":
    unittest.main()
