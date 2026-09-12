import unittest

from scripts.normalize_source_health import normalize_source_health


class SourceHealthTests(unittest.TestCase):
    def test_zero_history_rows_is_successful_check(self):
        payload = {
            "meta": {
                "errors": [],
                "sourceHealth": {"NSE-history": {"ok": False, "records": 0}},
            }
        }
        result = normalize_source_health(payload)
        history = result["meta"]["sourceHealth"]["NSE-history"]
        self.assertTrue(history["ok"])
        self.assertEqual(history["status"], "checked")
        self.assertEqual(history["note"], "checked · 0 new rows")
        self.assertNotIn("error", history)

    def test_actual_history_error_remains_failed(self):
        payload = {
            "meta": {
                "errors": ["NSE history 2026-09-11..2026-09-12: HTTP 403"],
                "sourceHealth": {"NSE-history": {"ok": False, "records": 0}},
            }
        }
        result = normalize_source_health(payload)
        history = result["meta"]["sourceHealth"]["NSE-history"]
        self.assertFalse(history["ok"])
        self.assertEqual(history["status"], "failed")
        self.assertIn("HTTP 403", history["error"])
        self.assertNotIn("note", history)

    def test_nonzero_history_rows_is_refreshed(self):
        payload = {
            "meta": {
                "errors": [],
                "sourceHealth": {"NSE-history": {"ok": True, "records": 12}},
            }
        }
        result = normalize_source_health(payload)
        history = result["meta"]["sourceHealth"]["NSE-history"]
        self.assertTrue(history["ok"])
        self.assertEqual(history["status"], "refreshed")
        self.assertEqual(history["note"], "12 rows")


if __name__ == "__main__":
    unittest.main()
