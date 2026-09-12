#!/usr/bin/env python3
"""Run the validated issuer-document fallback with the current Phase 4.5 parser."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_issuer_offer_docs as base  # noqa: E402
import run_offer_docs_v5 as parser_v5  # noqa: E402

# The base issuer module predates parser v5. Route its runtime parser/deep scan
# through v5 while retaining the base module's host + issuer-identity gates.
base.parser_v4 = parser_v5
base.PARSER_VERSION = parser_v5.PARSER_VERSION
base._extract_targeted_full_text = parser_v5.extract_targeted_pdf_text

# Both links resolve to the issuer's own website. The base module still validates
# host, PDF magic and company identity at runtime before accepting any fields.
base.ISSUER_DOCUMENTS.update(
    {
        "om-galaxy-limited": {
            "company": "OM Galaxy Limited",
            "url": "https://omgalaxymould.com/wp-content/uploads/2026/09/Project-Om_-RHP_with_RFS.pdf",
            "host": "omgalaxymould.com",
            "type": "RHP",
            "title": "Red Herring Prospectus",
            "sourcePage": "https://omgalaxymould.com/",
        },
        "injecto-polymers-limited": {
            "company": "Injecto Polymers Limited",
            "url": "https://injectopolymers.in/wp-content/uploads/2026/09/1.-RHP_07.09.2026.pdf",
            "host": "injectopolymers.in",
            "type": "RHP",
            "title": "Red Herring Prospectus",
            "sourcePage": "https://injectopolymers.in/",
        },
    }
)


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
