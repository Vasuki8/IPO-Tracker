"""Optional PDF diagnostics cannot discard completed source validation."""
import hashlib
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import review_source_repairs as review


class SourceReviewReportTests(unittest.TestCase):
    def preview(self, directory, *, invalid=False, interrupt=False):
        root = Path(directory)
        (root / "data").mkdir()
        cache = root / "cache"
        cache.mkdir()
        data_file = root / "data/ipos.json"
        report_file = root / "data/source_review.json"
        data_file.write_text(json.dumps({"ipos": [
            {"id": "first", "company": "First Limited"},
            {"id": "second", "company": "Second Limited"},
        ]}))

        def document(record):
            return {"url": f"https://www.sebi.gov.in/files/{record['id']}.pdf"}

        for identifier in ("first", "second"):
            url = document({"id": identifier})["url"]
            (cache / (hashlib.sha256(url.encode()).hexdigest() + ".pdf")).write_bytes(b"cached PDF")

        def collect(payload, **kwargs):
            for record in payload["ipos"]:
                record["documentRepair"] = {"status": "updated"}
                record["dataReview"] = {"financials": "Annual financial table remains queued"}
                if invalid:
                    record["lotSize"] = -1

        def save(payload):
            data_file.write_text(json.dumps(payload))

        source_pages = [f"[PAGE {page}]\nneutral context" for page in range(1, 47)]
        for page in (1, 2, 45, 46):
            source_pages[page - 1] += f"\nFINANCIAL HEADER page {page}\nrow from page {page}"
        source_pages[2] += "\nFINANCIAL HEADER contents .... 45"
        text = "\f".join(source_pages)

        def diagnostic(data, *, page_limit):
            # A workflow cancellation during the first diagnostic must still
            # leave the report for every processed document on disk.
            saved = json.loads(report_file.read_text())
            self.assertEqual([row["id"] for row in saved["records"]], ["first", "second"])
            self.assertEqual(page_limit, 45)
            if interrupt:
                raise KeyboardInterrupt("diagnostics interrupted after completed collection")
            return text, 46, 46

        output = io.StringIO()
        with ExitStack() as stack:
            stack.enter_context(patch.object(review, "ROOT", root))
            stack.enter_context(patch.object(review.documents, "DATA_FILE", data_file))
            stack.enter_context(patch.object(review.documents, "CACHE", cache))
            stack.enter_context(patch.object(review.documents, "run", side_effect=collect))
            stack.enter_context(patch.object(review.documents, "atomic_save", side_effect=save))
            stack.enter_context(patch.object(review.documents, "document_for", side_effect=document))
            stack.enter_context(patch.object(review.documents, "pdf_bytes", return_value=b"cached PDF"))
            stack.enter_context(patch.object(review.parser, "extract_pdf_text", side_effect=diagnostic))
            stack.enter_context(patch.object(review.parser, "_HEADING", re.compile(r"^FINANCIAL HEADER")))
            stack.enter_context(patch.object(sys, "argv", ["review_source_repairs.py"]))
            stack.enter_context(redirect_stdout(output))
            if interrupt:
                with self.assertRaises(KeyboardInterrupt):
                    review.main()
                result = None
            else:
                result = review.main()
        return result, json.loads(report_file.read_text()), json.loads(data_file.read_text()), output.getvalue()

    def test_completed_report_survives_interrupted_optional_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            _, report, data, output = self.preview(directory, interrupt=True)
        self.assertEqual(report["before"]["errorCount"], 0)
        self.assertEqual(report["after"]["errorCount"], 0)
        self.assertEqual(report["after"]["reviewCount"], 2)
        self.assertEqual(len(report["records"]), 2)
        self.assertTrue(all(row["documentRepair"]["status"] == "updated" for row in data["ipos"]))
        self.assertIn("SOURCE_REVIEW_SUMMARY ", output)

    def test_bounded_diagnostics_preserve_excerpt_order_and_strict_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            result, report, _, output = self.preview(directory, invalid=True)
        self.assertEqual(result, 1)
        self.assertGreater(report["after"]["errorCount"], 0)
        layouts = [json.loads(line.removeprefix("SOURCE_LAYOUT "))
                   for line in output.splitlines() if line.startswith("SOURCE_LAYOUT ")]
        self.assertEqual(len(layouts), 2)
        for layout in layouts:
            self.assertEqual(len(layout["snippets"]), 3)
            for snippet, page in zip(layout["snippets"], (1, 2, 45)):
                self.assertIn(f"row from page {page}", snippet)
            self.assertNotIn("contents ....", "\n".join(layout["snippets"]))
            self.assertNotIn("row from page 46", "\n".join(layout["snippets"]))


if __name__ == "__main__":
    unittest.main()
