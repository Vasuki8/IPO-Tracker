import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"
spec = importlib.util.spec_from_file_location("run_pipeline", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class PipelineIoTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.data = Path(self.tempdir.name) / "ipos.json"
        self.original_data = mod.DATA
        mod.DATA = self.data
        mod.PIPELINE_REPORTS.clear()
        mod.LAST_SUPPORT_REBUILD_HASH = None
        self.addCleanup(self._restore_module)

    def _restore_module(self):
        mod.DATA = self.original_data
        mod.PIPELINE_REPORTS.clear()
        mod.LAST_SUPPORT_REBUILD_HASH = None

    def write_payload(self, payload):
        self.data.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_unchanged_stage_does_not_rewrite_dataset_for_diagnostics(self):
        payload = {"meta": {}, "ipos": [{"id": "a", "company": "A"}]}
        self.write_payload(payload)
        before = self.data.read_bytes()

        with patch.object(mod.subprocess, "run", return_value=SimpleNamespace(stdout="ok\n", returncode=0)):
            report = mod.step("noop.py")

        self.assertEqual(report["status"], "no_change")
        self.assertEqual(self.data.read_bytes(), before)
        self.assertIn("noop.py", mod.PIPELINE_REPORTS)
        self.assertNotIn("pipelineStages", json.loads(self.data.read_text())["meta"])

    def test_changed_stage_keeps_collector_write_without_extra_diagnostic_write(self):
        original = {"meta": {}, "ipos": [{"id": "a", "company": "A", "issueSizeCr": 10}]}
        changed = {"meta": {}, "ipos": [{"id": "a", "company": "A", "issueSizeCr": 11}]}
        self.write_payload(original)
        changed_bytes = (json.dumps(changed, separators=(",", ":")) + "\n").encode()

        def collector(*_args, **_kwargs):
            self.data.write_bytes(changed_bytes)
            return SimpleNamespace(stdout="updated\n", returncode=0)

        with patch.object(mod.subprocess, "run", side_effect=collector):
            report = mod.step("collector.py")

        self.assertEqual(report["status"], "updated")
        self.assertEqual(self.data.read_bytes(), changed_bytes)
        self.assertNotIn("pipelineStages", json.loads(self.data.read_text())["meta"])

    def test_invalid_stage_output_restores_exact_previous_bytes(self):
        payload = {"meta": {}, "ipos": [{"id": "a", "company": "A"}]}
        self.write_payload(payload)
        before = self.data.read_bytes()

        def broken_collector(*_args, **_kwargs):
            self.data.write_text("{broken", encoding="utf-8")
            return SimpleNamespace(stdout="bad output\n", returncode=0)

        with patch.object(mod.subprocess, "run", side_effect=broken_collector):
            report = mod.step("broken.py")

        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["exitCode"], 1)
        self.assertEqual(self.data.read_bytes(), before)
        self.assertIn("Restored the previous valid dataset", report["diagnostics"])

    def test_failed_stage_retains_new_failure_metadata_and_accepted_rows(self):
        payload = {"meta": {}, "ipos": [{"id": "a", "company": "A", "issueSizeCr": None}]}
        self.write_payload(payload)
        failure = {"ok": False, "checkedAt": "2026-09-19T00:01:00+05:30", "error": "HTTP 403"}

        def collector(*_args, **_kwargs):
            payload['meta']['sourceHealth'] = {'NSE-live': failure}
            self.write_payload(payload)
            return SimpleNamespace(stdout='No source rows refreshed', returncode=2)

        with patch.object(mod.subprocess, 'run', side_effect=collector):
            report = mod.step('run_update_final_policy.py')
        self.assertEqual(report['status'], 'failed')
        mod.flush_pipeline_reports()
        result = json.loads(self.data.read_text())
        self.assertEqual(result['ipos'], payload['ipos'])
        self.assertEqual(result['meta']['sourceHealth']['NSE-live'], failure)

    def test_flush_persists_all_reports_once(self):
        self.write_payload({"meta": {"pipelineStages": {"old.py": {"status": "no_change"}}}, "ipos": []})
        mod.PIPELINE_REPORTS.update(
            {
                "a.py": {"stage": "a.py", "status": "updated"},
                "b.py": {"stage": "b.py", "status": "no_change"},
            }
        )

        self.assertTrue(mod.flush_pipeline_reports())
        payload = json.loads(self.data.read_text())
        stages = payload["meta"]["pipelineStages"]
        self.assertEqual(stages["old.py"]["status"], "no_change")
        self.assertEqual(stages["a.py"]["status"], "updated")
        self.assertEqual(stages["b.py"]["status"], "no_change")

    def test_duplicate_support_rebuild_is_skipped_until_records_change(self):
        self.write_payload({"meta": {"volatile": 1}, "ipos": [{"id": "a", "company": "A"}]})
        calls = []

        def fake_run(command, **_kwargs):
            calls.append(command[-1])
            return SimpleNamespace(returncode=0)

        with patch.object(mod.subprocess, "run", side_effect=fake_run):
            self.assertTrue(mod.rebuild())
            self.assertEqual(len(calls), 5)
            self.assertFalse(mod.rebuild())
            self.assertEqual(len(calls), 5)

            # Top-level metadata changes do not invalidate derived record artifacts.
            payload = json.loads(self.data.read_text())
            payload["meta"]["volatile"] = 2
            self.write_payload(payload)
            self.assertFalse(mod.rebuild())
            self.assertEqual(len(calls), 5)

            payload = json.loads(self.data.read_text())
            payload["ipos"][0]["company"] = "A Updated"
            self.write_payload(payload)
            self.assertTrue(mod.rebuild())
            self.assertEqual(len(calls), 10)

    def test_pipeline_enforces_final_prospectus_policy_before_mode_collectors(self):
        calls = []

        def fake_step(script, *args, **kwargs):
            calls.append((script, args, kwargs))
            return {"stage": script, "status": "no_change"}

        with patch.object(mod, "step", side_effect=fake_step), patch.object(
            mod, "rebuild", return_value=False
        ):
            mod.run("repair")

        scripts = [script for script, _args, _kwargs in calls]
        self.assertNotIn("apply_verified_recent_issue_terms.py", scripts)
        self.assertIn("enforce_final_prospectus_policy.py", scripts)
        self.assertLess(
            scripts.index("enforce_final_prospectus_policy.py"),
            scripts.index("run_priority_subscriptions_v3.py"),
        )
        self.assertIn("run_offer_documents.py", scripts)
        self.assertIn("run_issuer_offer_docs.py", scripts)

    def test_repair_mode_refreshes_live_subscriptions(self):
        calls = []

        def fake_step(script, *args, **kwargs):
            calls.append((script, args, kwargs))
            return {"stage": script, "status": "no_change"}

        with patch.object(mod, "step", side_effect=fake_step), patch.object(
            mod, "rebuild", return_value=False
        ):
            mod.run("repair")

        scripts = [script for script, _args, _kwargs in calls]
        self.assertIn("run_priority_subscriptions_v3.py", scripts)
        subscription_call = next(call for call in calls if call[0] == "run_priority_subscriptions_v3.py")
        self.assertEqual(subscription_call[1], ("--limit", "30"))

    def test_exhausted_budget_defers_stage_and_preserves_completed_data(self):
        self.write_payload({"meta": {}, "ipos": [{"id": "a", "lotSize": 1200}]})
        before = self.data.read_bytes()
        with patch.object(mod, "DEADLINE", 100), patch.object(mod.time, "monotonic", return_value=90), patch.object(mod.subprocess, "run") as run:
            report = mod.step("later.py")
        run.assert_not_called()
        self.assertEqual(report["status"], "deferred")
        self.assertEqual(self.data.read_bytes(), before)
        mod.flush_pipeline_reports()
        self.assertEqual(json.loads(self.data.read_text())["meta"]["pipelineStages"]["later.py"]["status"], "deferred")

    def test_stage_timeout_reserves_time_for_publication(self):
        self.write_payload({"ipos": []})
        with patch.object(mod, "DEADLINE", 100), patch.object(mod.time, "monotonic", return_value=60), patch.object(mod.subprocess, "run", return_value=SimpleNamespace(stdout="", returncode=0)) as run:
            mod.step("slow.py", timeout=600)
        self.assertEqual(run.call_args.kwargs["timeout"], 30)


if __name__ == "__main__":
    unittest.main()
