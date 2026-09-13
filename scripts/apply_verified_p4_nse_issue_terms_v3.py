#!/usr/bin/env python3
"""Extend verified NSE P4 issue terms with NSDL and Optimystix close-out facts."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import apply_verified_p4_nse_issue_terms_v2 as v2  # noqa: E402

base = v2.base

EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS_V3 = {
    "nsdl": base._entry(
        "National Securities Depository Limited",
        "NSDL",
        "2025-07-30",
        4010.954,
        0.0,
        4010.954,
        "NSE-hosted NSDL RHP and BRLM track record",
        [
            "https://nsearchives.nseindia.com/content/equities/NSDL_RHP.pdf",
            "https://nsearchives.nseindia.com/corporate/Registration_14082025225322_RSBDRHP.pdf",
        ],
        source_basis="NSDL RHP confirms the entire offer is OFS; NSE-hosted BRLM track record reports final issue size Rs 40,109.54 million at Rs 800, including the employee discount effect",
        official_note="Using the official aggregate issue size avoids overstating the offer by multiplying every reserved employee share by the undiscounted Rs 800 offer price.",
    ),
    "optimystix": base._entry(
        "Optimystix Entertainment India Limited",
        "OPTIMYSTIX",
        "2026-08-07",
        108.5,
        87.5,
        21.0,
        "NSE Emerge Optimystix Entertainment India final Prospectus",
        "https://nsearchives.nseindia.com/emerge/corporates/content/OptimystixEntertainmentIndiaLimited_PROSP.pdf",
        source_basis="NSE final Prospectus: 62,00,000 shares at Rs 175; fresh 50,00,000 shares Rs 87.50 cr plus OFS 12,00,000 shares Rs 21.00 cr",
    ),
}

base.VERIFIED_P4_NSE_ISSUE_TERMS.update(EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS_V3)


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
