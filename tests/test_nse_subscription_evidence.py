"""Replay official NSE layouts without permitting a graph/series substitution."""
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nse_subscription_evidence", ROOT / "scripts/track_subscriptions.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
CASES = {case["name"]: case for case in json.loads(
    (ROOT / "tests/fixtures/nse_subscription_detail_20260918.json").read_text(encoding="utf-8")
)["cases"]}


class NSESubscriptionEvidenceTests(unittest.TestCase):
    def case(self, name="nse-detail-sona-eq"):
        case = copy.deepcopy(CASES[name])
        record = case["record"]
        record.update({
            "subscription": {"total": 18.43},
            "subscriptionSource": "Earlier source",
            "subscriptionSourceUrl": "https://example.test/earlier",
            "subscriptionAsOf": "2026-09-18T12:00:00+05:30",
            "subscriptionObservedAt": None,
            "subscriptionHistory": [{"total": 18.43, "capturedAt": "2026-09-18T12:00:00+05:30"}],
            "sources": [{"name": "Earlier source", "url": "https://example.test/earlier"}],
        })
        return record, case["payload"], case["series"]

    def assert_rejected_unchanged(self, record, payload, series, reason):
        before = copy.deepcopy(record)
        with self.assertRaisesRegex(ValueError, reason):
            mod.update_record(record, payload, series=series)
        self.assertEqual(record, before)

    def test_real_sme_bid_count_layout_does_not_import_graph_total(self):
        record, payload, series = self.case("nse-detail-sme")
        self.assertEqual(payload["demandGraph"]["noOfTimesIssueSubscribed"], "18.43")
        self.assert_rejected_unchanged(record, payload, series, "no denominator-backed headline")

    def test_real_eq_placeholder_cannot_be_used_for_sme(self):
        record, payload, series = self.case("nse-detail-eq")
        # Before this guard the permissive low-level parser yielded these zeros.
        self.assertEqual(mod.parse_bid_details(payload), {"qib": 0, "nii": 0, "retail": None, "total": 0})
        self.assert_rejected_unchanged(record, payload, series, "series does not match")

    def test_zero_denominators_stay_invalid_even_with_matching_issue_identity(self):
        record, payload, series = self.case("nse-detail-sme")
        payload["bidDetails"] = copy.deepcopy(CASES["nse-detail-eq"]["payload"]["bidDetails"])
        self.assert_rejected_unchanged(record, payload, series, "bid/denominator evidence")

    def test_two_real_mainboard_responses_keep_their_reported_multiples(self):
        for name in ("nse-detail-sona-eq", "nse-detail-jsipl-eq"):
            with self.subTest(name=name):
                record, payload, series = self.case(name)
                expected = mod.parse_bid_details(payload)
                self.assertTrue(mod.update_record(record, payload, series=series))
                self.assertEqual(record["subscription"], expected)
                self.assertEqual(record["subscriptionHistory"][-1]["total"], expected["total"])
                self.assertEqual(record["subscriptionSource"], "NSE subscription detail")
                self.assertIn("series=EQ", record["subscriptionSourceUrl"])

    def test_missing_identity_is_rejected_before_any_mutation(self):
        for missing in ("issueInfo", "symbol", "company", "period"):
            with self.subTest(missing=missing):
                record, payload, series = self.case()
                if missing == "issueInfo":
                    payload[missing] = {}
                elif missing == "symbol":
                    payload["issueInfo"].pop("symbol")
                elif missing == "company":
                    payload["issueInfo"]["dataList"].pop(0)
                else:
                    payload["issueInfo"]["dataList"] = [row for row in payload["issueInfo"]["dataList"]
                                                          if row["title"] != "Issue Period"]
                self.assert_rejected_unchanged(record, payload, series, "identity|symbol|issuer|offer dates")

    def test_another_issuer_symbol_or_offer_cannot_be_relabelled(self):
        for field, value in (("company", "Another Limited"), ("symbol", "OTHER"),
                             ("openDate", "2025-09-17"), ("closeDate", "2026-09-22")):
            with self.subTest(field=field):
                record, payload, series = self.case()
                record[field] = value
                self.assert_rejected_unchanged(record, payload, series, "symbol|issuer|offer dates")

    def test_absent_zero_negative_nonfinite_or_partial_denominator_is_rejected(self):
        for offered in (None, "", "0", "-1", "nan", "Infinity", "1e309", "2860000 shares", "2860000.5"):
            with self.subTest(offered=offered):
                record, payload, series = self.case()
                payload["bidDetails"][0]["noOfSharesOffered"] = offered
                self.assert_rejected_unchanged(record, payload, series, "bid/denominator evidence")

    def test_invalid_bid_counts_or_disagreeing_reported_multiple_are_rejected(self):
        for field, value in (("noOfsharesBid", None), ("noOfsharesBid", "-1"),
                             ("noOfsharesBid", "0.5"), ("noOfTime", "nan"),
                             ("noOfTime", "-0.5"), ("noOfTime", "3.2x"), ("noOfTime", "99")):
            with self.subTest(field=field, value=value):
                record, payload, series = self.case()
                payload["bidDetails"][0][field] = value
                self.assert_rejected_unchanged(record, payload, series, "bid/denominator|disagrees")

    def test_real_zero_with_positive_denominator_is_preserved(self):
        record, payload, series = self.case()
        payload["bidDetails"][0].update(noOfsharesBid="0", noOfTime="0.00")
        mod.update_record(record, payload, series=series)
        self.assertEqual(record["subscription"]["qib"], 0)

    def test_scientific_share_counts_and_rounded_multiple_are_supported(self):
        record, payload, series = self.case("nse-detail-jsipl-eq")
        total = next(row for row in payload["bidDetails"] if row["category"] == "Total")
        self.assertEqual(total["noOfsharesBid"], "1.175898276E9")
        total["noOfTime"] = "125.10"
        mod.update_record(record, payload, series=series)
        self.assertEqual(record["subscription"]["total"], 125.10)

    def test_root_total_cannot_replace_missing_denominator_backed_total(self):
        record, payload, series = self.case()
        payload["bidDetails"] = [row for row in payload["bidDetails"] if row["category"] != "Total"]
        payload["noOfTime"] = "18.43"
        self.assert_rejected_unchanged(record, payload, series, "Incomplete subscription response")

    def test_missing_category_remains_null_without_inventing_a_zero(self):
        record, payload, series = self.case()
        payload["bidDetails"] = [row for row in payload["bidDetails"] if row.get("srNo") != "3"]
        mod.update_record(record, payload, series=series)
        self.assertIsNone(record["subscription"]["retail"])


class NSESubscriptionRoutingTests(unittest.TestCase):
    def test_only_the_board_compatible_api_route_is_requested(self):
        for board, name, expected in (("SME", "nse-detail-sme", "SME"),
                                      ("Mainboard", "nse-detail-sona-eq", "EQ")):
            with self.subTest(board=board):
                client = mod.NSESubscriptionClient()
                client._prime = Mock()
                client.s = Mock()
                payload = CASES[name]["payload"]
                client.s.get.return_value.json.return_value = payload
                result, series = client.detail(CASES[name]["record"]["symbol"], board)
                self.assertEqual((result, series), (payload, expected))
                self.assertEqual(client.s.get.call_count, 1)
                self.assertEqual(client.s.get.call_args.kwargs["params"]["series"], expected)

    def test_unavailable_sme_does_not_try_eq_as_a_fallback(self):
        client = mod.NSESubscriptionClient()
        client._prime = Mock()
        client.s = Mock()
        client.s.get.side_effect = mod.requests.RequestException("unavailable")
        with self.assertRaisesRegex(mod.requests.RequestException, "unavailable"):
            client.detail("SPECTRAA", "SME")
        self.assertEqual(client.s.get.call_count, 1)

    def test_unknown_board_does_not_guess_a_route(self):
        client = mod.NSESubscriptionClient()
        client._prime = Mock()
        client.s = Mock()
        for board in (None, "", "unknown"):
            with self.subTest(board=board), self.assertRaisesRegex(ValueError, "explicit supported board"):
                client.detail("SPECTRAA", board)
        client.s.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
