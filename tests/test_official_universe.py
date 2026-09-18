import copy
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("official_universe", ROOT / "tools/audit_ipo_universe.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def receipt(source="SEBI", **kw):
    return {"key": "test", "source": source, "responseUrl": "https://www.sebi.gov.in/register",
            "retrievedAt": "2026-09-18T22:00:00+00:00", "sha256": "a" * 64,
            "asOf": "2026-09-18", "register": "draft", "page": 0, **kw}


def row(name="Example Limited", **kw):
    return audit.record_base(receipt(), 1, name, "https://www.sebi.gov.in/filings/example.html", **kw)


class UniverseIdentityTests(unittest.TestCase):
    def test_deterministic_legal_punctuation_case_spacing(self):
        for name in ("A. B. & Co Limited", "A B and CO LTD.", "  A.B. & Co. Ltd  "):
            self.assertEqual(audit.normalize_name(name), "abandco")

    def test_meaningful_company_words_are_not_erased(self):
        self.assertNotEqual(audit.normalize_name("Acme Private Limited"), audit.normalize_name("Acme Limited"))
        self.assertNotEqual(audit.normalize_name("Final Offer Corporation Limited"), audit.normalize_name("Limited"))

    def test_anchored_filing_annotations_and_rename_flag(self):
        for title in ("Example Limited - Addendum II to DRHP", "Example Ltd. – RHP", "Corrigendum to Example Limited"):
            self.assertEqual(audit.normalize_name(audit.issuer_from_title(title)[0]), "example")
        name, flags = audit.issuer_from_title("New Name Limited (formerly Old Name Limited) - DRHP")
        self.assertEqual(name, "New Name Limited")
        self.assertIn("published_rename_requires_alias_review", flags)
        self.assertEqual(audit.issuer_from_title("Draft Systems Limited - DRHP")[0], "Draft Systems Limited")

    def test_exact_and_normalized_names(self):
        tracker = [{"id": "e", "company": "Example Limited"}]
        result, remaining = audit.reconcile([row(), row("EXAMPLE LTD.")], tracker, [])
        self.assertEqual([r["classification"] for r in result], ["exact_match", "normalized_match"])
        self.assertEqual(remaining, [])

    def test_alias_requires_explicit_source_evidence(self):
        tracker = [{"id": "new", "company": "New Company Limited"}]
        alias = {"name": "Old Company Limited", "trackerId": "new", "sourceUrl": "https://www.sebi.gov.in/filings/rename.html", "evidence": "Official issuer title states formerly Old Company Limited"}
        result, _ = audit.reconcile([row("Old Company Limited")], tracker, [alias])
        self.assertEqual(result[0]["classification"], "known_alias")
        with self.assertRaises(ValueError):
            audit.reconcile([row()], tracker, [{**alias, "evidence": ""}])
        with self.assertRaises(ValueError):
            audit.reconcile([row()], tracker, [alias, alias])

    def test_normalization_collision_cannot_prefer_an_exact_record(self):
        tracker = [{"id": "a", "company": "A B Limited"}, {"id": "b", "company": "AB Ltd"}]
        result, _ = audit.reconcile([row("A B Limited")], tracker, [])
        self.assertEqual(result[0]["classification"], "possible_duplicate_requires_review")
        self.assertEqual(result[0]["trackerIds"], ["a", "b"])

    def test_multiple_filing_stages_remain_separate(self):
        rows = [row(lifecycleStage=s, recordId=s) for s in ("draft", "rhp", "final_prospectus")]
        result, _ = audit.reconcile(rows, [{"id": "e", "company": "Example Limited"}], [])
        self.assertEqual(len(result), 3)
        self.assertEqual([r["lifecycleStage"] for r in result], ["draft", "rhp", "final_prospectus"])
        self.assertTrue(all(r["filingLinkedInTracker"] is False for r in result))

    def test_sme_mainboard_overlap_is_review_not_auto_migration(self):
        result, _ = audit.reconcile([row(board="SME")], [{"id": "e", "company": "Example Limited", "board": "Mainboard"}], [])
        self.assertEqual(result[0]["classification"], "possible_duplicate_requires_review")

    def test_same_name_different_offer_dates_require_review(self):
        result, _ = audit.reconcile([row(issueOpenDate="2020-01-01")], [{"id": "e", "company": "Example Limited", "openDate": "2026-01-01"}], [])
        self.assertEqual(result[0]["classification"], "possible_duplicate_requires_review")

    def test_fuzzy_candidate_never_matches(self):
        result, remaining = audit.reconcile([row("Example Industries Limited")], [{"id": "e", "company": "Example Industrie Limited"}], [])
        self.assertEqual(result[0]["classification"], "possible_duplicate_requires_review")
        self.assertEqual(remaining[0]["classification"], "tracker_only")

    def test_unknown_issuer_boundary_is_not_confirmed_missing(self):
        result, _ = audit.reconcile([row("Public announcement", identityFlags=["issuer_boundary_requires_review"])], [], [])
        self.assertEqual(result[0]["classification"], "source_unavailable_not_verified")

    def test_inputs_not_mutated_and_nulls_preserved(self):
        rows, tracker = [row()], [{"id": "e", "company": "Other Limited", "openDate": None}]
        before = copy.deepcopy((rows, tracker))
        result, _ = audit.reconcile(rows, tracker, [])
        self.assertEqual((rows, tracker), before)
        self.assertIsNone(result[0]["board"])
        self.assertIsNone(result[0]["issueOpenDate"])


class UniverseSourceTests(unittest.TestCase):
    def sebi_html(self, title="Example Limited - DRHP"):
        return (f'<div>1 to 1 of 1 records</div><table><tr><td>Sep 18, 2026</td><td><a href="/filings/public-issues/example_1.html">{title}</a><a href="/filings/public-issues/abridged_2.html">Example Limited - Draft Abridged Prospectus</a></td></tr></table>').encode()

    def test_register_row_denominator_not_attachment_count(self):
        rows, bounds = audit.parse_sebi(self.sebi_html(), receipt())
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]["linkedDocuments"]), 2)
        self.assertEqual(bounds["reportedTotal"], 1)
        self.assertEqual(rows[0]["issuerName"], "Example Limited")
        self.assertEqual(rows[0]["lifecycleStage"], "draft")
        self.assertIsNone(rows[0]["board"])

    def test_register_membership_does_not_override_explicit_rhp(self):
        rows, _ = audit.parse_sebi(self.sebi_html("Example Limited - RHP"), receipt())
        self.assertEqual(rows[0]["lifecycleStage"], "rhp")

    def test_addendum_is_retained_not_an_extra_ipo(self):
        rows, _ = audit.parse_sebi(self.sebi_html("Example Limited - Addendum to DRHP"), receipt())
        self.assertEqual(rows[0]["documentRole"], "supplemental")
        self.assertEqual(rows[0]["issuerName"], "Example Limited")

    def test_wrong_or_repeated_page_and_truncated_table_fail_closed(self):
        with self.assertRaises(ValueError):
            audit.parse_sebi(self.sebi_html(), receipt(page=1))
        with self.assertRaises(ValueError):
            audit.parse_sebi(self.sebi_html().replace(b"1 to 1 of 1", b"1 to 25 of 100"), receipt())

    def test_nse_history_does_not_invent_listing_or_board(self):
        raw = [{"companyName": "Example Limited", "issueStartDate": "01-Jan-2020", "issueEndDate": "03-Jan-2020"}]
        rows, _ = audit.parse_nse(json.dumps(raw).encode(), receipt("NSE", register="historical"))
        self.assertEqual(rows[0]["lifecycleStage"], "completed_issue_listing_unverified")
        self.assertIsNone(rows[0]["listingDate"])
        self.assertIsNone(rows[0]["board"])

    def test_nse_current_and_explicit_cancelled_status(self):
        raw = [{"companyName": "Example Limited", "series": "SME", "issueStartDate": "17-Sep-2026", "issueEndDate": "21-Sep-2026"}]
        rows, _ = audit.parse_nse(json.dumps(raw).encode(), receipt("NSE", register="current"))
        self.assertEqual(rows[0]["lifecycleStage"], "open")
        self.assertEqual(rows[0]["board"], "SME")
        raw[0]["status"] = "Withdrawn"
        rows, _ = audit.parse_nse(json.dumps(raw).encode(), receipt("NSE", register="current"))
        self.assertEqual(rows[0]["lifecycleStage"], "withdrawn_or_cancelled")

    def test_nse_unknown_schema_not_empty_success(self):
        with self.assertRaises(ValueError):
            audit.parse_nse(b'{"error":"denied"}', receipt("NSE"))

    def test_historical_keys_and_non_equity_series(self):
        raw = [{"company": "Example Limited", "ipoStartDate": "01-JAN-2025", "ipoEndDate": "03-JAN-2025", "securityType": "SME"},
               {"company": "Bond issuer", "securityType": "N0"}, {"company": "Trust", "securityType": "RR"}]
        rows, _ = audit.parse_nse(json.dumps(raw).encode(), receipt("NSE", register="historical"))
        self.assertEqual(rows[0]["issueOpenDate"], "2025-01-01")
        self.assertEqual(rows[0]["board"], "SME")
        self.assertEqual([r["scope"] for r in rows[1:]], ["other_public_issue", "other_public_issue"])

    def test_upcoming_feed_does_not_override_closed_status(self):
        raw = [{"companyName": "Example Limited", "status": "Closed", "issueStartDate": "16-Sep-2026", "issueEndDate": "18-Sep-2026"}]
        rows, _ = audit.parse_nse(json.dumps(raw).encode(), receipt("NSE", register="upcoming"))
        self.assertEqual(rows[0]["lifecycleStage"], "closed")

    def test_withdrawal_option_is_not_a_cancelled_ipo(self):
        self.assertEqual(audit.filing_stage("Example Limited - Special Withdrawal Option", "other"), "withdrawal_option_notice")

    def test_bse_fixed_price_code_is_not_assumed_follow_on(self):
        html = b'<table><tr><td><a href="IPODisplay.aspx?scripcd=123&amp;type=FPO">Example Limited</a></td><td>SME</td><td>01-01-2020</td><td>03-01-2020</td><td>10</td></tr></table>'
        rows, _ = audit.parse_bse(html, receipt("BSE", responseUrl="https://beta.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx", register="historical", issueTypeLabel="Public Issue-Fixed Price"))
        self.assertEqual(rows[0]["scope"], "equity_public_issue_candidate")
        self.assertEqual(rows[0]["officialIdentifier"], "123")
        self.assertEqual(rows[0]["board"], "SME")

    def test_bse_shell_does_not_prove_zero_issues(self):
        with self.assertRaises(ValueError):
            audit.parse_bse(b"<html><form>Select issue type</form></html>", receipt("BSE"))

    def test_offline_replay_rejects_tampered_response(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "raw.gz").write_bytes(gzip.compress(self.sebi_html()))
            r = receipt(status="verified_response", rawFile="raw.gz", records=1, bounds={})
            (root / "capture.json").write_text(json.dumps({"cohorts": {"test": r}}))
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                audit.load_observations(root)

    def test_verified_capture_is_reused_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = audit.Capture(root, "2026-09-18")
            capture.manifest["cohorts"]["old"] = {"status": "verified_response", "records": 12}
            capture.session.request = lambda *a, **k: self.fail("Repeated a verified cohort")
            self.assertEqual(capture.fetch("old", "NSE", "https://www.nseindia.com/api/test")["records"], 12)


class RealUniverseEvidenceTests(unittest.TestCase):
    snapshot = ROOT / "docs/audits/official-universe/2026-09-18"

    def test_multiple_real_bse_layouts_replay_identity_without_terms(self):
        receipts = json.loads((self.snapshot / "admission-source-receipts.json").read_text(encoding="utf-8"))
        self.assertEqual(len(receipts), 8)
        for r in receipts:
            with self.subTest(issuer=r["issuerName"]):
                identity = audit.bse_identity(audit.read_bound_response(self.snapshot, r))
                self.assertEqual(identity["issuerName"], r["issuerName"])
                self.assertEqual(identity["securityType"], "Equity")
                self.assertLessEqual(identity["openDate"], identity["closeDate"])
                self.assertEqual(set(identity), {"issuerName", "securityType", "symbol", "openDate", "closeDate"})

    def test_reviewed_aliases_have_exact_source_symbol_and_dates(self):
        aliases = json.loads((self.snapshot / "aliases.json").read_text(encoding="utf-8"))
        tracker = json.loads((ROOT / "data/ipos.json").read_text(encoding="utf-8"))["ipos"]
        self.assertEqual(len(aliases), 5)
        audit.validate_alias_evidence(self.snapshot, aliases, tracker)
        bad = copy.deepcopy(aliases)
        bad[0]["sourceIdentity"]["symbol"] = "UNRELATED"
        with self.assertRaises(ValueError):
            audit.validate_alias_evidence(self.snapshot, bad, tracker)

    def test_real_nse_sme_listing_is_explicit(self):
        manifest = json.loads((self.snapshot / "capture.json").read_text(encoding="utf-8"))
        r = manifest["cohorts"]["NSE-2026"]
        rows, _ = audit.parse_nse(audit.read_bound_response(self.snapshot, r), r)
        vinod = next(x for x in rows if x["issuerName"] == "Vinod Texworld Limited")
        self.assertEqual((vinod["board"], vinod["officialIdentifier"], vinod["listingDate"]), ("SME", "VINOD", "2026-09-17"))

    def test_admission_preserves_unrelated_data_and_null_terms(self):
        manifest = json.loads((self.snapshot / "capture.json").read_text(encoding="utf-8"))
        receipt = manifest["cohorts"]["NSE-2026"]
        rows, _ = audit.parse_nse(audit.read_bound_response(self.snapshot, receipt), receipt)
        vinod = next(x for x in rows if x["issuerName"] == "Vinod Texworld Limited")
        with tempfile.TemporaryDirectory() as directory:
            tracker = Path(directory) / "tracker.json"
            original = {"meta": {"keep": True}, "ipos": [{"id": "old", "company": "Unrelated Limited", "dataReview": {"financials": "unresolved"}}]}
            tracker.write_text(json.dumps(original), encoding="utf-8")
            plan = {"baselineSha256": audit.digest(tracker.read_bytes()), "reviewedAt": "2026-09-18T22:00:00+00:00", "records": [{"recordId": vinod["recordId"], "id": "vinod"}]}
            with patch.object(audit, "load_observations", return_value=(manifest, [vinod], [])):
                proposed = audit.prepare_admissions(self.snapshot, tracker, plan, [])
                self.assertTrue(proposed["meta"]["keep"])
                self.assertEqual(proposed["meta"]["recordCount"], 2)
                self.assertEqual(proposed["meta"]["generatedAt"], plan["reviewedAt"])
                self.assertEqual(proposed["ipos"][0], original["ipos"][0])
                new = proposed["ipos"][1]
                self.assertEqual(new["status"], "listed")
                self.assertIsNone(new["source"]["asOf"])
                self.assertEqual(new["source"]["collectedAt"], vinod["retrievedAt"])
                self.assertEqual(new["source"]["timeBasis"], "collection_only")
                self.assertIsNone(new["observations"]["NSE"]["observedAt"])
                self.assertEqual(new["observations"]["NSE"]["collectedAt"], vinod["retrievedAt"])
                for field in ("priceBand", "lotSize", "issueSizeCr", "financials", "subscription", "listing", "registrar"):
                    self.assertIsNone(new[field])
                self.assertEqual(json.loads(tracker.read_text()), original)
                plan["records"].append(plan["records"][0])
                with self.assertRaises(ValueError):
                    audit.prepare_admissions(self.snapshot, tracker, plan, [])
                plan["baselineSha256"] = "0" * 64
                with self.assertRaisesRegex(ValueError, "baseline changed"):
                    audit.prepare_admissions(self.snapshot, tracker, plan, [])


if __name__ == "__main__":
    unittest.main()
