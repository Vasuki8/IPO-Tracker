#!/usr/bin/env python3
"""Apply narrow official-source promoter-shareholding residuals for P4.

This runs after the broader verified offer-residual layer.  It deliberately uses
its own entries because several issuers already have other verified fields whose
provenance comes from different official documents.  Keeping this as a separate
pass ensures the shareholding field is stamped with the document that actually
supports that percentage.

All writes still use the established exact id/company/symbol/open-date identity
guards and fill-only semantics from apply_verified_recent_offer_fields.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import apply_verified_offer_residuals_v2 as residuals_v2  # noqa: E402

base = residuals_v2.base

SHAREHOLDING_RESIDUALS = {
    "aastha": base._entry(
        "Aastha Spintex Limited",
        "AASTHA",
        "2026-06-29",
        "Aastha Spintex RHP promoter shareholding",
        "https://aasthaspintex.com/pdf/RHP/RHP_Aastha.pdf",
        shareholding={"promoterPreIssuePct": 74.23},
    ),
    "innovision": base._entry(
        "Innovision Limited",
        "INNOVISION",
        "2026-03-10",
        "NSE Innovision final Prospectus promoter shareholding",
        "https://nsearchives.nseindia.com/corporate/FP_INE0ADB01012_18MAR2026.pdf",
        shareholding={"promoterPreIssuePct": 100.0},
    ),
    "jnpr": base._entry(
        "Juniper Green Energy Limited",
        "JNPR",
        "2026-07-30",
        "Juniper Green Energy pre-IPO shareholder register",
        "https://www.junipergreenenergy.com/wp-content/uploads/2025/07/List-of-Shareholders-as-on-June-27-2025.pdf",
        shareholding={"promoterPreIssuePct": 100.0},
    ),
    "shiprocket": base._entry(
        "Shiprocket Limited",
        "SHIPROCKET",
        "2026-08-12",
        "NSE Shiprocket UDRHP promoter status",
        "https://nsearchives.nseindia.com/corporate/Shiprocket_Limited_UDRHP_1.pdf",
        shareholding={"promoterPreIssuePct": 0.0},
    ),
}

# Register only for this process.  The preceding residual pass has already
# persisted its own fields, so replacing duplicate registry entries here keeps
# field-level provenance accurate without overwriting any stored values.
base.VERIFIED_RECENT_OFFER_FIELDS.update(SHAREHOLDING_RESIDUALS)


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
