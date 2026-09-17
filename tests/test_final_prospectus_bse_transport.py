import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from pypdf import PdfWriter
from unittest.mock import MagicMock, patch

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_offer_documents as runner


def _valid_pdf():
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(stream)
    return stream.getvalue()


class _Response:
    def __init__(self, chunks=None, status_error=None):
        self._chunks = list(chunks or [])
        self._status_error = status_error
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def close(self):
        self.closed = True

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def iter_content(self, _size):
        yield from self._chunks


class BSEFinalProspectusTransportTests(unittest.TestCase):
    def bse_doc(self):
        return {
            "type": "PROSPECTUS",
            "title": "Sunshine Pictures Limited Final Prospectus",
            "url": "https://www.bseindia.com/downloads/ipo/361148/ipo_T3/Prospectus_20260821184134.pdf",
        }

    def test_bse_ipo_pdf_uses_session_bootstrap_and_referrer(self):
        session = MagicMock()
        session.__enter__.return_value = session
        session.__exit__.return_value = False
        home = _Response([b"home"])
        history = _Response([b"history"])
        expected = _valid_pdf()
        final = _Response([expected])
        session.get.side_effect = [home, history, final]

        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            runner, "CACHE", Path(temp_dir)
        ), patch.object(
            runner.requests, "Session", return_value=session
        ) as session_factory, patch.object(
            runner.requests, "get"
        ) as generic_get:
            data = runner.pdf_bytes(self.bse_doc())

        self.assertEqual(data, expected)
        session_factory.assert_called_once_with()
        generic_get.assert_not_called()
        self.assertTrue(home.closed)
        self.assertTrue(history.closed)
        self.assertEqual(session.get.call_count, 3)
        final_call = session.get.call_args_list[-1]
        self.assertEqual(final_call.args[0], self.bse_doc()["url"])
        self.assertEqual(final_call.kwargs["headers"]["Referer"], runner.BSE_IPO_HISTORY)
        self.assertTrue(final_call.kwargs["stream"])

    def test_bse_bootstrap_failure_does_not_hide_final_request(self):
        session = MagicMock()
        session.__enter__.return_value = session
        session.__exit__.return_value = False
        expected = _valid_pdf()
        final = _Response([expected])
        session.get.side_effect = [
            runner.requests.ConnectionError("home blocked"),
            runner.requests.Timeout("history blocked"),
            final,
        ]

        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            runner, "CACHE", Path(temp_dir)
        ), patch.object(runner.requests, "Session", return_value=session):
            data = runner.pdf_bytes(self.bse_doc())

        self.assertEqual(data, expected)
        self.assertEqual(session.get.call_count, 3)

    def test_non_bse_final_keeps_generic_transport(self):
        doc = {
            "type": "PROSPECTUS",
            "title": "Final Prospectus",
            "url": "https://nsearchives.nseindia.com/corporate/FP_EXAMPLE.pdf",
        }
        expected = _valid_pdf()
        response = _Response([expected])

        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            runner, "CACHE", Path(temp_dir)
        ), patch.object(
            runner.requests, "get", return_value=response
        ) as generic_get, patch.object(
            runner.requests, "Session"
        ) as session_factory:
            data = runner.pdf_bytes(doc)

        self.assertEqual(data, expected)
        generic_get.assert_called_once()
        session_factory.assert_not_called()

    def test_bse_transport_is_restricted_to_official_ipo_tree(self):
        self.assertTrue(runner._bse_ipo_pdf(self.bse_doc()["url"]))
        self.assertFalse(runner._bse_ipo_pdf("https://www.bseindia.com/downloads/UploadDocs/Notices/example.pdf"))
        self.assertFalse(runner._bse_ipo_pdf("https://example.com/downloads/ipo/361148/final.pdf"))


if __name__ == "__main__":
    unittest.main()
