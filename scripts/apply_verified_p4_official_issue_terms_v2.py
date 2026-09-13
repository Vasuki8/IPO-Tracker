#!/usr/bin/env python3
"""Extend the official-only P4 issue-term registry with batch 2.

All entries remain exact-identity guarded and fill-only through the base runner.
Only SEBI filing pages or SEBI-hosted disclosures are used as provenance.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import apply_verified_p4_official_issue_terms as base  # noqa: E402


base.VERIFIED_P4_OFFICIAL_ISSUE_TERMS.update(
    {
        "damcapital": base._entry(
            "DAM Capital Advisors Limited",
            "DAMCAPITAL",
            "2024-12-19",
            "SEBI DAM Capital Advisors final Prospectus",
            "https://www.sebi.gov.in/filings/public-issues/dec-2024/dam-capital-advisors-limited-prospectus_90232.html",
            issue_size_cr=840.252,
            fresh_issue_cr=0.0,
            ofs_cr=840.252,
        ),
        "suraksha": base._entry(
            "Suraksha Diagnostic Limited",
            "SURAKSHA",
            "2024-11-29",
            "SEBI Suraksha Diagnostic final Prospectus",
            "https://www.sebi.gov.in/sebi_data/attachdocs/dec-2024/1733378164227.pdf",
            issue_size_cr=846.249,
            fresh_issue_cr=0.0,
            ofs_cr=846.249,
        ),
        "ventive": base._entry(
            "Ventive Hospitality Limited",
            "VENTIVE",
            "2024-12-20",
            "SEBI Ventive Hospitality final Prospectus",
            "https://www.sebi.gov.in/filings/public-issues/dec-2024/ventive-hospitality-limited-prospectus_90212.html",
            issue_size_cr=1600.0,
            fresh_issue_cr=1600.0,
            ofs_cr=0.0,
        ),
        "igil": base._entry(
            "International Gemmological Institute (India) Limited",
            "IGIL",
            "2024-12-13",
            "SEBI-hosted BRLM disclosure for International Gemmological Institute",
            "https://www.sebi.gov.in/sebi_data/attachdocs/jan-2025/1736249404881_639.pdf",
            issue_size_cr=4225.0,
        ),
        "iks": base._entry(
            "Inventurus Knowledge Solutions Limited",
            "IKS",
            "2024-12-12",
            "SEBI-hosted BRLM disclosure for Inventurus Knowledge Solutions",
            "https://www.sebi.gov.in/sebi_data/attachdocs/feb-2025/1739791805392_693.pdf",
            issue_size_cr=2497.923,
        ),
        "cewater": base._entry(
            "Concord Enviro Systems Limited",
            "CEWATER",
            "2024-12-19",
            "SEBI-hosted BRLM disclosure for Concord Enviro Systems",
            "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2025/1759368606185_979.pdf",
            issue_size_cr=500.326,
        ),
    }
)


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
