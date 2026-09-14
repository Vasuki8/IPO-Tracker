#!/usr/bin/env python3
"""Extend the verified NSE P4 issue-term registry with final close-out records."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from parser_loader import isolated_module
base = isolated_module("apply_verified_p4_nse_issue_terms")

EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS = {
    "credent": base._entry(
        "Credent Connect N Care Limited",
        "CREDENT",
        "2026-08-13",
        93.8952,
        93.8952,
        0.0,
        "NSE Emerge Credent Connect N Care final Prospectus",
        "https://nsearchives.nseindia.com/emerge/corporates/content/CredentConnectNCareLimited_PROSP.pdf",
        source_basis="NSE final Prospectus: Rs 9,389.52 lakh fresh issue; offer for sale nil",
    ),
    "pramodini": base._entry(
        "Pramodini Medicare Limited",
        "PRAMODINI",
        "2026-08-12",
        69.0442,
        63.1394,
        5.9047,
        "NSE Emerge Pramodini Medicare final Prospectus",
        "https://nsearchives.nseindia.com/emerge/corporates/content/PramodiniMedicareLimited_PROSP.pdf",
        source_basis="NSE final Prospectus: Rs 6,313.94 lakh fresh issue plus Rs 590.47 lakh OFS; total Rs 6,904.42 lakh",
    ),
    "identical": base._entry(
        "Identical Brains Studios Limited",
        "IDENTICAL",
        "2024-12-18",
        19.9476,
        19.9476,
        0.0,
        "NSE Emerge Identical Brains Studios final Prospectus",
        "https://nsearchives.nseindia.com/emerge/corporates/content/IdenticalBrainsStudiosLimited_PROSP.pdf",
        source_basis="NSE final Prospectus: 36,94,000 shares at Rs 54, aggregate Rs 1,994.76 lakh; issuance by the company",
    ),
    "capinvit": base._entry(
        "Capital Infra Trust",
        "CAPINVIT",
        "2025-01-07",
        1578.0,
        1077.0,
        501.0,
        "NSE Capital Infra Trust post-IPO outcome filing",
        "https://nsearchives.nseindia.com/corporate/CAPINVIT_14112025132746_Outcome.pdf",
        source_basis="NSE filing: 159,393,750 units at Rs 99; fresh 108,787,800 units (about Rs 1,077 cr) and OFS 50,605,950 units (about Rs 501 cr)",
        official_note="Stored crore values use the official rounded offer terms Rs 1,077 cr fresh + Rs 501 cr OFS = Rs 1,578 cr total.",
    ),
}

base.VERIFIED_P4_NSE_ISSUE_TERMS.update(EXTRA_VERIFIED_P4_NSE_ISSUE_TERMS)


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
