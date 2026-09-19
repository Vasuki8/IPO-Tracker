import json
from pathlib import Path
import tempfile
import unittest
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import summarize_official_universe as summary

class OfficialUniverseSummaryTests(unittest.TestCase):
    def test_compact_group_uses_candidate_source_records_as_denominator(self):
        row={"source":"BSE","sourceRecords":10,"matchedRecords":6,"classifications":{"exact_match":2,"normalized_match":3,"known_alias":1,"genuinely_missing":3,"possible_duplicate_requires_review":1}}
        out=summary.compact_group(row)
        self.assertEqual(out["denominator"],10)
        self.assertEqual(out["matched"],6)
        self.assertEqual(out["matchRatePct"],60.0)
        self.assertEqual(out["genuinelyMissing"],3)

    def test_next_cohort_moves_backward_and_stays_in_one_month(self):
        review={"records":[{"identity":{"openDate":"2026-06-01"}}]}
        rows=[
          {"recordId":"a","source":"BSE","classification":"genuinely_missing","scope":"equity_public_issue_candidate","board":"SME","issueOpenDate":"2026-05-30","url":"https://beta.bseindia.com/x"},
          {"recordId":"b","source":"BSE","classification":"genuinely_missing","scope":"equity_public_issue_candidate","board":"Mainboard","issueOpenDate":"2026-05-10","url":"https://beta.bseindia.com/y"},
          {"recordId":"c","source":"BSE","classification":"genuinely_missing","scope":"equity_public_issue_candidate","board":"SME","issueOpenDate":"2026-04-30","url":"https://beta.bseindia.com/z"},
          {"recordId":"d","source":"BSE","classification":"possible_duplicate_requires_review","scope":"equity_public_issue_candidate","board":"SME","issueOpenDate":"2026-05-20","url":"https://beta.bseindia.com/q"}]
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"missing.jsonl"
            path.write_text("".join(json.dumps(r)+"\n" for r in rows),encoding="utf-8")
            out=summary.next_bse_cohort(path,review,25)
        self.assertEqual(out["selection"]["periodMonth"],"2026-05")
        self.assertEqual([r["recordId"] for r in out["candidates"]],["a","b"])

    def test_next_cohort_excludes_current_date(self):
        review={"records":[{"identity":{"openDate":"2026-06-01"}}]}
        rows=[
          {"recordId":"same","source":"BSE","classification":"genuinely_missing","scope":"equity_public_issue_candidate","board":"SME","issueOpenDate":"2026-06-01","url":"https://beta.bseindia.com/x"},
          {"recordId":"older","source":"BSE","classification":"genuinely_missing","scope":"equity_public_issue_candidate","board":"SME","issueOpenDate":"2026-05-31","url":"https://beta.bseindia.com/y"}]
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"missing.jsonl"
            path.write_text("".join(json.dumps(r)+"\n" for r in rows),encoding="utf-8")
            out=summary.next_bse_cohort(path,review,25)
        self.assertEqual([r["recordId"] for r in out["candidates"]],["older"])

if __name__=="__main__":
    unittest.main()
