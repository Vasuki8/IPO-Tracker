import io
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pypdf import PdfWriter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import offer_parser as parser


def pdf_bytes(page_count):
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


class OfferPDFPageLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.long_pdf = pdf_bytes(535)
        cls.short_pdf = pdf_bytes(3)
        cls.pages = [f"Source page {number}\n" for number in range(1, 536)]
        cls.poppler_output = ("\f".join(cls.pages) + "\f").encode("utf-8")

    def extract(self, data, output, **kwargs):
        with patch.object(parser.shutil, "which", return_value="/usr/bin/pdftotext"), patch.object(
            parser.subprocess, "run", return_value=SimpleNamespace(stdout=output)
        ) as run:
            result = parser.extract_pdf_text(data, **kwargs)
        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertEqual(command[:9], ["pdftotext", "-layout", "-fixed", "3", "-enc", "UTF-8", "-f", "1", "-l"])
        self.assertEqual(command[10:], ["-", "-"])
        self.assertEqual(run.call_args.kwargs["input"], data)
        return result, command[9]

    def expected_text(self, count):
        return "\f".join(f"[PAGE {number}]\n{text}" for number, text in enumerate(self.pages[:count], 1))

    def test_default_preserves_canonical_520_page_cap_and_total_count(self):
        result, last_page = self.extract(self.long_pdf, self.poppler_output)
        self.assertEqual(last_page, "520")
        self.assertEqual(result, (self.expected_text(520), 520, 535))

    def test_diagnostic_limit_bounds_conversion_and_returned_pages(self):
        result, last_page = self.extract(self.long_pdf, self.poppler_output, page_limit=45)
        self.assertEqual(last_page, "45")
        self.assertEqual(result, (self.expected_text(45), 45, 535))

    def test_short_document_keeps_actual_page_accounting(self):
        output = ("\f".join(self.pages[:3]) + "\f").encode("utf-8")
        for kwargs in ({}, {"page_limit": 45}, {"page_limit": 1}):
            with self.subTest(kwargs=kwargs):
                result, last_page = self.extract(self.short_pdf, output, **kwargs)
                expected_count = min(3, kwargs.get("page_limit", 520))
                self.assertEqual(last_page, str(expected_count))
                self.assertEqual(result, (self.expected_text(expected_count), expected_count, 3))

    def test_invalid_limits_fail_before_reading_pdf_or_running_poppler(self):
        for limit in (True, False, None, "45", 45.0, 1.5, [], {}, 0, -1, 521):
            with self.subTest(limit=limit), patch.object(parser, "PdfReader") as reader, patch.object(
                parser.subprocess, "run"
            ) as run:
                with self.assertRaisesRegex(ValueError, "integer from 1 to 520"):
                    parser.extract_pdf_text(b"not parsed", page_limit=limit)
                reader.assert_not_called()
                run.assert_not_called()

    def test_page_limit_is_keyword_only(self):
        with self.assertRaises(TypeError):
            parser.extract_pdf_text(self.long_pdf, 45)


if __name__ == "__main__":
    unittest.main()
