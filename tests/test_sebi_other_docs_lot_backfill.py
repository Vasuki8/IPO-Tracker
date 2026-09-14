import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "backfill_recent_sebi_other_docs_lot_sizes.py"
spec = importlib.util.spec_from_file_location("backfill_recent_sebi_other_docs_lot_sizes", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class SebiOtherDocsLotBackfillTests(unittest.TestCase):
    def test_identity_matches_company_inside_long_document_text(self):
        text = "Price Band Advertisement " + ("x " * 200) + "Vinit Mobile Limited" + (" y" * 200)
        self.assertEqual(mod.identity_score("Vinit Mobile Limited", text), 1.0)

    def test_identity_rejects_different_issuer(self):
        self.assertLess(mod.identity_score("Vinit Mobile Limited", "Some Other Industries Limited"), 0.90)

    def test_queue_targets_only_actionable_p4_lot_gaps(self):
        queue = {"queue": [
            {"id": "a", "priorityLabel": "P4 recent history (2y)", "missingFields": ["exchange.lotSize"]},
            {"id": "b", "priorityLabel": "P4 recent history (2y)", "missingFields": ["exchange.issueSizeCr"]},
            {"id": "c", "priorityLabel": "P5 historical", "missingFields": ["exchange.lotSize"]},
        ]}
        self.assertEqual(mod.p4_targets(queue), {"a"})

    def test_apply_lot_is_fill_only_and_adds_minimum_investment(self):
        record = {
            "id": "vmobile", "company": "Vinit Mobile Limited", "lotSize": None,
            "minInvestment": None, "priceBand": {"min": 100, "max": 110},
            "sources": [], "documents": [], "observations": {},
        }
        doc = {
            "title": "Price Band Advertisement", "url": "https://www.sebi.gov.in/test.pdf",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/test.html", "filedDate": "2026-09-03",
        }
        changed = mod.apply_lot(record, 1200, doc, 3, 4)
        self.assertEqual(record["lotSize"], 1200)
        self.assertEqual(record["minInvestment"], 132000.0)
        self.assertIn("lotSize", changed)
        self.assertEqual(mod.apply_lot(record, 1000, doc, 3, 4), [])
        self.assertEqual(record["lotSize"], 1200)

    def test_reuses_strict_lot_parser(self):
        self.assertEqual(
            mod.terms.extract_lot_size("The minimum Bid Lot is 1,200 Equity Shares and in multiples thereafter."),
            1200,
        )
        self.assertIsNone(mod.terms.extract_lot_size("The minimum Bid Lot is [●] Equity Shares."))

    def test_discovers_pdf_hidden_in_onclick_javascript(self):
        html = '''
        <html><body>
          <button onclick="window.open('/sebi_data/attachdocs/sep-2026/vinit-price-band.pdf')">
            Price Band Advertisement
          </button>
        </body></html>
        '''
        docs = mod.extract_document_candidates(
            html,
            "https://www.sebi.gov.in/filings/public-issues/sep-2026/vinit-mobile-limited_104253.html",
        )
        self.assertEqual(len(docs), 1)
        self.assertEqual(
            docs[0]["url"],
            "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/vinit-price-band.pdf",
        )
        self.assertEqual(docs[0]["rank"], 0)

    def test_discovers_escaped_absolute_pdf_url(self):
        html = r'''<script>var file="https:\/\/www.sebi.gov.in\/sebi_data\/attachdocs\/offer.pdf";</script>'''
        docs = mod.extract_document_candidates(html, "https://www.sebi.gov.in/filings/public-issues/x.html")
        self.assertEqual([d["url"] for d in docs], ["https://www.sebi.gov.in/sebi_data/attachdocs/offer.pdf"])


if __name__ == "__main__":
    unittest.main()
