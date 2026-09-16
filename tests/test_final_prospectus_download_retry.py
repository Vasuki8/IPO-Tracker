import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_offer_documents as runner


class _Response:
    def __init__(self, chunks=None, status_error=None):
        self._chunks = list(chunks or [])
        self._status_error = status_error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def iter_content(self, _size):
        yield from self._chunks


class FinalProspectusDownloadRetryTests(unittest.TestCase):
    def doc(self):
        return {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://www.sebi.gov.in/files/example.pdf",
        }

    def test_transient_connection_failure_retries_and_succeeds(self):
        success = _Response([b"%PDF-test"])
        with tempfile.TemporaryDirectory() as temp_dir, (
            patch.object(runner, "CACHE", Path(temp_dir)),
            patch.object(
                runner.requests,
                "get",
                side_effect=[requests.ConnectionError("broken stream"), success],
            ) as get_mock,
            patch.object(runner.time, "sleep") as sleep_mock,
        ):
            data = runner.pdf_bytes(self.doc())

        self.assertEqual(data, b"%PDF-test")
        self.assertEqual(get_mock.call_count, 2)
        sleep_mock.assert_called_once()

    def test_http_404_does_not_retry(self):
        response = _Response(
            status_error=requests.HTTPError("404 Client Error")
        )
        with tempfile.TemporaryDirectory() as temp_dir, (
            patch.object(runner, "CACHE", Path(temp_dir)),
            patch.object(runner.requests, "get", return_value=response) as get_mock,
            patch.object(runner.time, "sleep") as sleep_mock,
        ):
            with self.assertRaises(requests.HTTPError):
                runner.pdf_bytes(self.doc())

        self.assertEqual(get_mock.call_count, 1)
        sleep_mock.assert_not_called()

    def test_non_pdf_content_does_not_retry(self):
        response = _Response([b"<html>blocked</html>"])
        with tempfile.TemporaryDirectory() as temp_dir, (
            patch.object(runner, "CACHE", Path(temp_dir)),
            patch.object(runner.requests, "get", return_value=response) as get_mock,
            patch.object(runner.time, "sleep") as sleep_mock,
        ):
            with self.assertRaisesRegex(ValueError, "non-PDF"):
                runner.pdf_bytes(self.doc())

        self.assertEqual(get_mock.call_count, 1)
        sleep_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
