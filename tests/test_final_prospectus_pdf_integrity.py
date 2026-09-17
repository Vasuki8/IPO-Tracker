import hashlib
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import requests
from pypdf import PdfWriter
from pypdf.generic import NameObject, NumberObject

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_offer_documents as runner


def valid_pdf(label="valid", *, encrypted=False, broken_pages=False, empty=False):
    stream = BytesIO()
    writer = PdfWriter()
    if not empty:
        writer.add_blank_page(width=612, height=792)
    writer.add_metadata({"/Title": label})
    if broken_pages:
        writer._root_object["/Pages"][NameObject("/Kids")] = NumberObject(7)
    if encrypted:
        writer.encrypt("")
    writer.write(stream)
    return stream.getvalue()


class Response:
    def __init__(self, data=b"", status_error=None):
        self.data = data
        self.status_error = status_error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def iter_content(self, size):
        for start in range(0, len(self.data), size):
            yield self.data[start:start + size]


class FinalProspectusPDFIntegrityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.cache = Path(directory.name)
        cache_patch = patch.object(runner, "CACHE", self.cache)
        cache_patch.start()
        self.addCleanup(cache_patch.stop)
        self.doc = {
            "type": "PROSPECTUS", "title": "Final Prospectus",
            "url": "https://www.sebi.gov.in/files/final-integrity.pdf",
        }
        self.path = self.cache / (hashlib.sha256(self.doc["url"].encode()).hexdigest() + ".pdf")
        self.good = valid_pdf()
        self.truncated = self.good.rsplit(b"%%EOF", 1)[0]

    def test_valid_cache_reuses_bytes_without_network_or_text_extraction(self):
        self.path.write_bytes(self.good)
        with patch.object(runner.requests, "get") as get, patch.object(
            runner.parser, "extract_pdf_text"
        ) as extract:
            self.assertEqual(runner.pdf_bytes(self.doc), self.good)
            self.assertEqual(runner.pdf_bytes(self.doc), self.good)
        get.assert_not_called()
        extract.assert_not_called()
        self.assertEqual(self.path.read_bytes(), self.good)

    def test_truncated_cache_is_discarded_then_replaced_by_valid_response(self):
        self.path.write_bytes(self.truncated)

        def response(*args, **kwargs):
            self.assertFalse(self.path.exists(), "Corrupt cached bytes must be discarded before refetch")
            return Response(self.good)

        with patch.object(runner.requests, "get", side_effect=response) as get:
            data = runner.pdf_bytes(self.doc)
        self.assertEqual(data, self.good)
        self.assertEqual(self.path.read_bytes(), self.good)
        get.assert_called_once()

    def test_oversized_cache_is_bounded_and_refetched(self):
        oversized = valid_pdf("large" * 1000)
        self.assertGreater(len(oversized), len(self.good))
        self.path.write_bytes(oversized)
        with patch.object(runner, "PDF_MAX_BYTES", len(self.good)), patch.object(
            runner.requests, "get", return_value=Response(self.good)
        ) as get:
            self.assertEqual(runner.pdf_bytes(self.doc), self.good)
        get.assert_called_once()
        self.assertEqual(self.path.read_bytes(), self.good)

    def test_non_pdf_cache_is_discarded_even_when_refetch_fails(self):
        self.path.write_bytes(b"<html>blocked response</html>")
        with patch.object(
            runner.requests, "get", return_value=Response(status_error=requests.HTTPError("404"))
        ) as get:
            with self.assertRaises(requests.HTTPError):
                runner.pdf_bytes(self.doc)
        get.assert_called_once()
        self.assertFalse(self.path.exists())
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_truncated_successful_response_retries_then_caches_recovery(self):
        with patch.object(
            runner.requests, "get",
            side_effect=[Response(self.truncated), Response(self.good)],
        ) as get, patch.object(runner.time, "sleep") as sleep:
            self.assertEqual(runner.pdf_bytes(self.doc), self.good)
        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once()
        self.assertEqual(self.path.read_bytes(), self.good)

    def test_persistently_malformed_responses_exhaust_bounded_retries_without_cache(self):
        with patch.object(
            runner.requests, "get", return_value=Response(self.truncated)
        ) as get, patch.object(runner.time, "sleep") as sleep:
            with self.assertRaises(runner.InvalidPDFError):
                runner.pdf_bytes(self.doc)
        self.assertEqual(get.call_count, runner.PDF_DOWNLOAD_ATTEMPTS)
        self.assertEqual(sleep.call_count, runner.PDF_DOWNLOAD_ATTEMPTS - 1)
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_unreadable_page_tree_and_empty_document_are_not_cached(self):
        for broken in (valid_pdf(broken_pages=True), valid_pdf(empty=True)):
            with self.subTest(size=len(broken)), patch.object(
                runner.requests, "get", return_value=Response(broken)
            ) as get, patch.object(runner.time, "sleep"):
                with self.assertRaises(runner.InvalidPDFError):
                    runner.pdf_bytes(self.doc)
                self.assertEqual(get.call_count, runner.PDF_DOWNLOAD_ATTEMPTS)
                self.assertEqual(list(self.cache.iterdir()), [])

    def test_non_strict_recoverable_pdf_and_empty_password_encryption_remain_usable(self):
        recoverable = self.good.rsplit(b"%%EOF", 1)[0] + b"%%EO"
        for usable in (self.good.rstrip(), recoverable, valid_pdf(encrypted=True)):
            self.path.unlink(missing_ok=True)
            with self.subTest(size=len(usable)), patch.object(
                runner.requests, "get", return_value=Response(usable)
            ) as get:
                self.assertEqual(runner.pdf_bytes(self.doc), usable)
                self.assertEqual(self.path.read_bytes(), usable)
                get.assert_called_once()

    def test_malformed_response_stops_when_total_deadline_is_exhausted(self):
        with patch.object(
            runner, "_download_pdf_once", return_value=self.truncated
        ) as download, patch.object(
            runner.time, "monotonic", side_effect=[0.0, runner.PDF_DOWNLOAD_TOTAL_SECONDS + 1.0]
        ), patch.object(runner.time, "sleep") as sleep:
            with self.assertRaises(runner.InvalidPDFError):
                runner.pdf_bytes(self.doc)
        download.assert_called_once()
        sleep.assert_not_called()
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_oversized_response_is_terminal_and_not_cached(self):
        with patch.object(runner, "PDF_MAX_BYTES", len(self.good) - 1), patch.object(
            runner.requests, "get", return_value=Response(self.good)
        ) as get, patch.object(runner.time, "sleep") as sleep:
            with self.assertRaisesRegex(ValueError, "40 MiB"):
                runner.pdf_bytes(self.doc)
        get.assert_called_once()
        sleep.assert_not_called()
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_atomic_replacement_exposes_old_bytes_until_complete_new_file_is_ready(self):
        previous = valid_pdf("previous")
        self.path.write_bytes(previous)
        replace = Path.replace

        def publish(temporary, target):
            self.assertEqual(target, self.path)
            self.assertEqual(temporary.parent, self.path.parent)
            self.assertNotEqual(temporary, self.path)
            self.assertEqual(self.path.read_bytes(), previous)
            self.assertEqual(temporary.read_bytes(), self.good)
            return replace(temporary, target)

        with patch.object(Path, "replace", autospec=True, side_effect=publish) as replacement:
            runner._write_pdf_cache(self.path, self.good)
        replacement.assert_called_once()
        self.assertEqual(self.path.read_bytes(), self.good)
        self.assertEqual(list(self.cache.iterdir()), [self.path])

    def test_interrupted_write_preserves_prior_cache_and_cleans_temporary_file(self):
        previous = valid_pdf("previous")
        self.path.write_bytes(previous)
        with patch.object(runner.os, "fsync", side_effect=OSError("interrupted write")):
            with self.assertRaisesRegex(OSError, "interrupted write"):
                runner._write_pdf_cache(self.path, self.good)
        self.assertEqual(self.path.read_bytes(), previous)
        self.assertEqual(list(self.cache.iterdir()), [self.path])

    def test_failed_initial_publication_leaves_no_cache_and_can_recover(self):
        with patch.object(
            runner.requests, "get", return_value=Response(self.good)
        ) as get:
            with patch.object(Path, "replace", side_effect=OSError("interrupted rename")):
                with self.assertRaisesRegex(OSError, "interrupted rename"):
                    runner.pdf_bytes(self.doc)
            self.assertEqual(list(self.cache.iterdir()), [])
            self.assertEqual(runner.pdf_bytes(self.doc), self.good)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(self.path.read_bytes(), self.good)

    def test_cached_bytes_cannot_bypass_final_document_or_https_requirements(self):
        self.path.write_bytes(self.good)
        invalid_documents = [
            {**self.doc, "type": "RHP", "title": "Red Herring Prospectus"},
            {**self.doc, "url": self.doc["url"].replace("https://", "http://")},
        ]
        with patch.object(runner.requests, "get") as get:
            for document in invalid_documents:
                with self.subTest(document=document), self.assertRaises(ValueError):
                    runner.pdf_bytes(document)
        get.assert_not_called()


    def test_cached_only_reuses_valid_cache_and_never_fetches_missing_or_invalid_cache(self):
        cases = ((self.good, None), (None, FileNotFoundError), (self.truncated, runner.InvalidPDFError))
        for data, error in cases:
            self.path.unlink(missing_ok=True)
            if data is not None:
                self.path.write_bytes(data)
            with self.subTest(error=error), patch.object(
                runner.requests, "get"
            ) as get, patch.object(runner.requests, "Session") as session:
                if error is None:
                    self.assertEqual(runner.pdf_bytes(self.doc, cached_only=True), self.good)
                else:
                    with self.assertRaises(error):
                        runner.pdf_bytes(self.doc, cached_only=True)
                    self.assertFalse(self.path.exists())
                get.assert_not_called()
                session.assert_not_called()

    def test_cached_only_run_reports_invalid_cache_without_network(self):
        self.path.write_bytes(self.truncated)
        record = {"id": "issuer", "company": "Issuer Limited", "documents": [self.doc]}
        payload = {"ipos": [record]}
        priorities = {runner._priority_key(record): 4}
        with patch.object(runner, "document_for", return_value=self.doc), patch.object(
            runner, "_load_queue_priorities", return_value=priorities
        ), patch.object(runner.requests, "get") as get, patch.object(
            runner.requests, "Session"
        ) as session, patch.object(runner.parser, "extract_pdf_text") as extract_text:
            health = runner.run(payload, limit=1, workers=1, cached_only=True, priority_max=4)
        self.assertEqual(health["attempted"], 1)
        self.assertEqual(health["failed"], 1)
        self.assertEqual(health["outcomes"][0]["status"], "parse_failed")
        self.assertFalse(self.path.exists())
        get.assert_not_called()
        session.assert_not_called()
        extract_text.assert_not_called()

    def test_cached_only_run_does_not_fetch_if_selected_cache_disappears(self):
        self.path.write_bytes(self.good)
        record = {"id": "issuer", "company": "Issuer Limited", "documents": [self.doc]}
        payload = {"ipos": [record]}
        priorities = {runner._priority_key(record): 4}
        extract = runner.extract

        def remove_selected_cache(record, document, **options):
            self.assertEqual(options, {"cached_only": True})
            self.path.unlink()
            return extract(record, document, **options)

        with patch.object(runner, "document_for", return_value=self.doc), patch.object(
            runner, "_load_queue_priorities", return_value=priorities
        ), patch.object(runner, "extract", side_effect=remove_selected_cache), patch.object(
            runner.requests, "get"
        ) as get, patch.object(runner.requests, "Session") as session:
            health = runner.run(payload, limit=1, workers=1, cached_only=True, priority_max=4)
        self.assertEqual(health["attempted"], 1)
        self.assertEqual(health["failed"], 1)
        self.assertIn("cached-only mode", health["outcomes"][0]["error"])
        self.assertFalse(self.path.exists())
        get.assert_not_called()
        session.assert_not_called()



if __name__ == "__main__":
    unittest.main()
