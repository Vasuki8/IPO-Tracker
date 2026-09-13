#!/usr/bin/env python3
"""Run the validated issuer-document fallback with the current Phase 4.5 parser."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_issuer_offer_docs as base  # noqa: E402
import run_offer_docs_v9 as parser_v9  # noqa: E402

# Route issuer-hosted fallbacks through the current parser while retaining the
# base module's host + issuer-identity gates.
base.parser_v4 = parser_v9
base.PARSER_VERSION = parser_v9.PARSER_VERSION
base._extract_targeted_full_text = parser_v9.extract_targeted_pdf_text

# These links resolve to the issuers' own websites. The base module still
# validates host, PDF magic and company identity at runtime before accepting any
# fields, and merge logic remains fill-only so official exchange/SEBI values win.
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
        "shakti-polytarp-limited": {
            "company": "Shakti Polytarp Limited",
            "url": "https://shaktipolytarp.com/wp-content/uploads/2025/10/DRHP_Shakti_29092025.pdf",
            "host": "shaktipolytarp.com",
            "type": "DRHP",
            "title": "Draft Red Herring Prospectus",
            "sourcePage": "https://shaktipolytarp.com/ipo-drhp-and-industry-report/",
        },
    }
)


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
