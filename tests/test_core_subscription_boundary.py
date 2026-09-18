"""Replay the core entrypoint without borrowing another collector's evidence.

The eight ratios come from an immutable publication diagnostic. NSE input rows
and issuer shells below are synthetic reproductions, not retained HTTP responses.
"""
import copy
from datetime import datetime
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "docs/releases/2026-09-18-bse-source-authority.json"
NOW = datetime.fromisoformat("2026-09-18T23:00:00+05:30")


def subscription_family(row):
    return {key: value for key, value in row.items() if key.startswith("subscription")}


def replay_core():
    # A fresh interpreter exercises the same wrapper chain as run_pipeline.py.
    # It also avoids mutating the module-level wrappers used by other tests.
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_update_final_policy as entry
    from publish_transaction import merge_payload
    from public_quality import project_record

    diagnostic = json.loads(RECEIPT.read_text())["nextRepairDiagnostic"]
    assert diagnostic["beforeCommit"] == "70a5133f11bce99f9e432c1ae56b52c29b012593"
    assert diagnostic["afterCommit"] == "eec88efb37a238ee862a7d21a8bfa84f940fcaae"
    rows, incoming = [], []
    for change in diagnostic["changes"]:
        identity = {"id": change["id"], "company": "Fixture " + change["id"] + " Limited",
                    "symbol": change["id"].upper(), "openDate": "2026-09-16"}
        values = {**change["unchangedCategories"], "total": change["beforeTotal"]}
        metadata = copy.deepcopy(change["unchangedSnapshotMetadata"])
        row = {**identity, **metadata, "closeDate": "2026-09-21", "status": "open",
               "subscription": values, "subscriptionAsOf": metadata["subscriptionCollectedAt"],
               "subscriptionDegraded": {"reason": "retained source diagnostic"},
               "subscriptionHistory": [{**values, "source": metadata["subscriptionSource"],
                   "sourceUrl": metadata["subscriptionSourceUrl"],
                   "capturedAt": metadata["subscriptionCollectedAt"],
                   "observedAt": metadata["subscriptionObservedAt"]}],
               "dataCorrections": [{"reason": "retained correction"}],
               "sources": [{"name": "NSE current", "url": "https://www.nseindia.com"}]}
        rows.append(row)
        incoming.append({"companyName": identity["company"], "symbol": identity["symbol"],
                         "issueStartDate": "16-Sep-2026", "issueEndDate": "22-Sep-2026",
                         "noOfTime": change["afterTotal"], "noOfsharesBid": 45,
                         "issueSize": 100, "status": "open"})
    incoming.append({"companyName": "New Fixture Limited", "symbol": "NEWFIXTURE",
                     "issueStartDate": "16-Sep-2026", "issueEndDate": "22-Sep-2026",
                     "noOfTime": 0, "qib": 0, "noOfsharesBid": 0})
    before = {"meta": {}, "ipos": copy.deepcopy(rows)}

    class FakeNSE:
        def current(self):
            return copy.deepcopy(incoming)

        def upcoming(self):
            return []

        def past(self, start, end):
            return []

    core = entry.core
    with tempfile.TemporaryDirectory() as directory:
        data = Path(directory) / "ipos.json"
        data.write_text(json.dumps(before))
        with (patch.object(core, "DATA_FILE", data),
              patch.object(core, "NSEClient", FakeNSE),
              patch.object(core, "now_ist", return_value=NOW),
              patch.object(core.time, "sleep"),
              patch.object(sys, "argv", ["run_update_final_policy.py", "--history-days", "1",
                                        "--skip-sebi", "--skip-bse"]),
              redirect_stdout(io.StringIO())):
            assert entry.main() == 0
        proposed = json.loads(data.read_text())

    # Simulate a concurrent accepted detail snapshot. The generic observation
    # may merge, but cannot conflict with or append to that accepted history.
    current = copy.deepcopy(before)
    accepted = current["ipos"][0]
    accepted["subscription"] = {"qib": 0, "nii": 4, "retail": 3, "total": 2}
    accepted["subscriptionSource"] = "NSE subscription detail"
    accepted["subscriptionSourceUrl"] = "https://www.nseindia.com/api/ipo-detail?symbol=SONA&series=EQ"
    accepted["subscriptionCollectedAt"] = NOW.isoformat()
    accepted["subscriptionAsOf"] = NOW.isoformat()
    accepted["subscriptionObservedAt"] = None
    accepted["subscriptionTimeBasis"] = "collection-only"
    accepted["subscriptionHistory"].append({**accepted["subscription"], "capturedAt": NOW.isoformat(),
        "observedAt": None, "source": "NSE ipo-detail", "sourceUrl": accepted["subscriptionSourceUrl"]})
    published, conflicts = merge_payload(before, proposed, current)

    # Defensive merge boundary also refuses a caller supplying canonical fields.
    attempts = {"subscription": {"total": 999}, "subscriptionSource": "Wrong source",
                "subscriptionSourceUrl": "https://example.invalid/wrong",
                "subscriptionCollectedAt": NOW.isoformat(), "subscriptionObservedAt": NOW.isoformat(),
                "subscriptionTimeBasis": "source-observation", "subscriptionAsOf": NOW.isoformat(),
                "subscriptionHistory": [{"total": 999}], "subscriptionDegraded": None,
                "subscriptionFinal": True, "closeDate": "2026-09-22"}
    guarded = core.merge_non_null(copy.deepcopy(rows[0]), copy.deepcopy(attempts))
    blank_guarded = core.merge_non_null({"id": "blank"}, copy.deepcopy(attempts))
    normalized = {}
    for kind in ("current", "upcoming", "historical"):
        normalized[kind] = core.normalize_nse_record(incoming[-1], kind)
    unsupported = core.normalize_nse_record({**incoming[-1], "noOfTime": "not disclosed", "qib": None}, "current")
    return {"before": before, "proposed": proposed, "current": current, "published": published,
            "conflicts": conflicts, "guarded": guarded, "blankGuarded": blank_guarded,
            "normalized": normalized, "unsupported": unsupported,
            "publicBefore": project_record(rows[0], today=NOW.date(), holds=[]),
            "publicAfter": project_record(next(row for row in proposed["ipos"] if row["id"] == rows[0]["id"]),
                                          today=NOW.date(), holds=[])}


class CoreSubscriptionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--replay"],
                                cwd=ROOT, capture_output=True, text=True, timeout=45)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        cls.result = json.loads(result.stdout)

    def test_recorded_eight_deltas_cannot_mix_values_with_previous_source_clocks(self):
        result = self.result
        proposed = {row["id"]: row for row in result["proposed"]["ipos"]}
        changes = json.loads(RECEIPT.read_text())["nextRepairDiagnostic"]["changes"]
        self.assertEqual(len(changes), 8)
        for before, change in zip(result["before"]["ipos"], changes):
            with self.subTest(id=before["id"]):
                after = proposed[before["id"]]
                self.assertEqual(subscription_family(after), subscription_family(before))
                self.assertEqual(after["dataCorrections"], before["dataCorrections"])
                self.assertEqual(after["closeDate"], "2026-09-22")
                observation = after["observations"]["NSE"]["subscriptionSummary"]
                self.assertEqual(observation["values"]["total"], change["afterTotal"])
                self.assertEqual(observation["rawFields"]["noOfTime"], change["afterTotal"])
                self.assertEqual(observation["rawFields"]["issueSize"], 100)
                self.assertEqual(observation["rawFields"]["noOfsharesBid"], 45)
                self.assertEqual(observation["denominatorStatus"], "unverified")
                self.assertEqual(observation["use"], "observation-only")
                self.assertEqual(observation["issuer"]["company"], before["company"])
                self.assertEqual(observation["issuer"]["symbol"], before["symbol"])
                self.assertEqual(observation["issuer"]["openDate"], "2026-09-16")
                self.assertEqual(observation["issuer"]["closeDate"], "2026-09-22")

    def test_new_issue_keeps_canonical_missing_and_zero_source_observations(self):
        row = next(row for row in self.result["proposed"]["ipos"] if row["id"] == "newfixture")
        self.assertIsNone(row.get("subscription"))
        self.assertFalse(any(key != "subscription" for key in subscription_family(row)))
        observation = row["observations"]["NSE"]["subscriptionSummary"]
        self.assertEqual(observation["values"], {"qib": 0, "nii": None, "retail": None, "total": 0})
        self.assertEqual(observation["rawFields"]["noOfsharesBid"], 0)

    def test_observation_endpoint_and_collection_clock_do_not_imply_source_time(self):
        endpoints = {"current": "https://www.nseindia.com/api/ipo-current-issue",
                     "upcoming": "https://www.nseindia.com/api/all-upcoming-issues?category=ipo",
                     "historical": "https://www.nseindia.com/api/public-past-issues"}
        for kind, endpoint in endpoints.items():
            with self.subTest(kind=kind):
                row = self.result["normalized"][kind]
                observation = row["observations"]["NSE"]["subscriptionSummary"]
                self.assertIsNone(row.get("subscription"))
                self.assertEqual(observation["sourceUrl"], endpoint)
                self.assertEqual(observation["feedKind"], kind)
                self.assertEqual(observation["collectedAt"], NOW.isoformat())
                self.assertIsNone(observation["observedAt"])
                self.assertEqual(observation["timeBasis"], "collection-only")
                self.assertEqual(observation["valueUnit"], "times")
        unsupported = self.result["unsupported"]["observations"]["NSE"]["subscriptionSummary"]
        self.assertIsNone(unsupported["values"])
        self.assertEqual(unsupported["rawFields"]["noOfTime"], "not disclosed")

    def test_defensive_core_merge_preserves_bundle_and_absence(self):
        result = self.result
        self.assertEqual(subscription_family(result["guarded"]),
                         subscription_family(result["before"]["ipos"][0]))
        self.assertEqual(subscription_family(result["blankGuarded"]), {})
        self.assertEqual(result["guarded"]["closeDate"], "2026-09-22")
        self.assertEqual(result["blankGuarded"]["closeDate"], "2026-09-22")

    def test_core_candidate_does_not_conflict_with_concurrent_detail_snapshot(self):
        result = self.result
        accepted = result["current"]["ipos"][0]
        published = next(row for row in result["published"]["ipos"] if row["id"] == accepted["id"])
        self.assertEqual(subscription_family(published), subscription_family(accepted))
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(published["closeDate"], "2026-09-22")
        self.assertIn("subscriptionSummary", published["observations"]["NSE"])

    def test_public_projection_does_not_relabel_previous_subscription(self):
        self.assertEqual(subscription_family(self.result["publicAfter"]),
                         subscription_family(self.result["publicBefore"]))


if __name__ == "__main__":
    if sys.argv[1:] == ["--replay"]:
        print(json.dumps(replay_core()))
    else:
        unittest.main()
