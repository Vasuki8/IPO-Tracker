import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"
spec = importlib.util.spec_from_file_location("run_pipeline_queue_refresh", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class P4PipelineQueueRefreshTests(unittest.TestCase):
    def test_new_final_prospectus_is_requeued_before_canonical_parse(self):
        events = []

        def fake_step(script, *args, **kwargs):
            events.append(script)
            return {"stage": script, "status": "no_change"}

        def fake_rebuild(*args, **kwargs):
            events.append("<rebuild>")
            return True

        with patch.object(mod, "step", side_effect=fake_step), patch.object(
            mod, "rebuild", side_effect=fake_rebuild
        ):
            mod.discover_and_parse_final_prospectuses(4, document_limit=20, parse_limit=100)

        discovery = events.index("collect_nse_offer_filings_final_policy.py")
        first_policy = events.index("enforce_final_prospectus_policy.py", discovery + 1)
        queue_refresh = events.index("<rebuild>", first_policy + 1)
        canonical_parse = events.index("run_offer_documents.py")

        self.assertLess(discovery, first_policy)
        self.assertLess(first_policy, queue_refresh)
        self.assertLess(queue_refresh, canonical_parse)
        self.assertEqual(events.count("<rebuild>"), 1)
        self.assertEqual(events.count("enforce_final_prospectus_policy.py"), 2)


if __name__ == "__main__":
    unittest.main()
