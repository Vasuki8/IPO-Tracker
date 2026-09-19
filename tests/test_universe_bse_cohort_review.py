import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("review_bse_universe_cohort", ROOT / "tools/review_bse_universe_cohort.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def row(**updates):
    value = {
        "recordId": "BSE-beta-historical-IPO:1",
        "issuerName": "Example Industries Limited",
        "normalizedName": "exampleindustries",
        "board": "SME",
        "sourceStatus": "H",
        "issueOpenDate": "2026-06-01",
        "issueCloseDate": "2026-06-03",
        "sourceIssueType": "IPO",
    }
    value.update(updates)
    return value


def receipt(**updates):
    value = {
        "recordId": "BSE-beta-historical-IPO:1",
        "status": "identity_replayed",
        "identityMatchesRegister": True,
        "identity": {
            "issuerName": "Example Industries Limited",
            "securityType": "Equity",
            "symbol": "EXAMPLE",
            "openDate": "2026-06-01",
            "closeDate": "2026-06-03",
        },
    }
    value.update(updates)
    return value


class BseUniverseCohortReviewTests(unittest.TestCase):
    def test_slug_is_deterministic_and_only_drops_legal_suffix(self):
        self.assertEqual(review.slugify_issuer("Horizon Reclaim (India) Limited"), "horizon-reclaim-india")
        self.assertEqual(review.slugify_issuer("ATHARVA POLY-PLAST LIMITED"), "atharva-poly-plast")
        self.assertEqual(review.slugify_issuer("UHM VACATION LIMITED"), "uhm-vacation")

    def test_exact_detail_identity_can_be_proposed_without_terms(self):
        decision, reason, matches, slug = review.classify_candidate(
            row(), receipt(), [{"id": "existing", "symbol": "OTHER"}],
            {"classification": "genuinely_missing"}, set()
        )
        self.assertEqual(decision, review.ACCEPT)
        self.assertEqual(matches, [])
        self.assertEqual(slug, "example-industries")
        self.assertIn("identity", reason)

    def test_symbol_collision_never_auto_merges(self):
        decision, _, matches, slug = review.classify_candidate(
            row(), receipt(), [{"id": "different-company", "symbol": "EXAMPLE"}],
            {"classification": "genuinely_missing"}, set()
        )
        self.assertEqual(decision, review.REVIEW)
        self.assertEqual(matches, ["different-company"])
        self.assertIsNone(slug)

    def test_detail_disagreement_requires_review(self):
        bad = receipt(status="identity_mismatch_requires_review", identityMatchesRegister=False)
        decision, _, _, slug = review.classify_candidate(
            row(), bad, [], {"classification": "genuinely_missing"}, set()
        )
        self.assertEqual(decision, review.REVIEW)
        self.assertIsNone(slug)

    def test_unavailable_source_is_not_an_admission(self):
        bad = receipt(status=review.UNAVAILABLE, identity=None)
        decision, _, _, slug = review.classify_candidate(
            row(), bad, [], {"classification": "genuinely_missing"}, set()
        )
        self.assertEqual(decision, review.UNAVAILABLE)
        self.assertIsNone(slug)

    def test_current_deterministic_match_is_not_readded(self):
        decision, _, _, slug = review.classify_candidate(
            row(), receipt(), [], {"classification": "known_alias"}, set()
        )
        self.assertEqual(decision, "known_alias")
        self.assertIsNone(slug)

    def test_bse_fixed_price_fpo_code_does_not_block_identity_review(self):
        decision, _, _, slug = review.classify_candidate(
            row(sourceIssueType="FPO"), receipt(), [],
            {"classification": "genuinely_missing"}, set()
        )
        self.assertEqual(decision, review.ACCEPT)
        self.assertEqual(slug, "example-industries")


if __name__ == "__main__":
    unittest.main()
