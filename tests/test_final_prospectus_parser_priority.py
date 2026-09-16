import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_offer_documents as runner


class FinalProspectusParserPriorityTests(unittest.TestCase):
    def test_phase_status_keeps_default_parser_scope_at_p4_until_p5_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase = Path(tmp) / "phase.json"
            with patch.object(runner, "PHASE_FILE", phase):
                phase.write_text(json.dumps({"p5": {"status": "waiting_for_p4"}}))
                self.assertEqual(runner._effective_priority_max(None), 4)
                phase.write_text(json.dumps({"p5": {"status": "enabled"}}))
                self.assertEqual(runner._effective_priority_max(None), 5)

    def test_explicit_priority_override_is_bounded(self):
        self.assertEqual(runner._effective_priority_max(3), 3)
        self.assertEqual(runner._effective_priority_max(99), 5)
        self.assertEqual(runner._effective_priority_max(-5), 0)

    def test_p5_record_is_not_eligible_while_p4_gate_is_active(self):
        priorities = {"p4": 4, "p5": 5}
        self.assertTrue(runner._priority_allowed({"id": "p4"}, priorities, 4))
        self.assertFalse(runner._priority_allowed({"id": "p5"}, priorities, 4))
        self.assertFalse(runner._priority_allowed({"id": "not-in-queue"}, priorities, 4))
        self.assertTrue(runner._priority_allowed({"id": "p5"}, priorities, 5))

    def test_deferred_p5_record_is_not_mutated_or_parsed(self):
        p4 = {
            "id": "p4",
            "company": "Priority Four Limited",
            "leadManagers": ["Bad"],
            "documents": [
                {
                    "type": "PROSPECTUS",
                    "title": "Final Prospectus",
                    "url": "https://www.sebi.gov.in/files/p4.pdf",
                }
            ],
        }
        p5 = {
            "id": "p5",
            "company": "Priority Five Limited",
            "leadManagers": ["Bad"],
            "documents": [
                {
                    "type": "PROSPECTUS",
                    "title": "Final Prospectus",
                    "url": "https://www.sebi.gov.in/files/p5.pdf",
                }
            ],
        }
        payload = {"ipos": [p4, p5], "meta": {}}

        def fake_extract(record, doc):
            return {}, "abc", 1, 1

        with (
            patch.object(runner, "_load_queue_priorities", return_value={"p4": 4, "p5": 5}),
            patch.object(runner, "_effective_priority_max", return_value=4),
            patch.object(runner, "extract", side_effect=fake_extract) as extract_mock,
        ):
            health = runner.run(payload, limit=10, workers=1)

        self.assertEqual(health["priorityMax"], 4)
        self.assertEqual(health["attempted"], 1)
        self.assertEqual(health["deferredByPriority"], 1)
        self.assertEqual(extract_mock.call_count, 1)
        self.assertIs(extract_mock.call_args.args[0], p4)
        self.assertEqual(p4["leadManagers"], [])
        self.assertEqual(p5["leadManagers"], ["Bad"])
        self.assertNotIn("documentRepair", p5)


if __name__ == "__main__":
    unittest.main()
