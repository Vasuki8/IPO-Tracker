#!/usr/bin/env python3
"""Extend the verified recent-offer registry for narrow P4 partial residuals.

The base verified-field runner remains authoritative for exact identity guards,
fill-only semantics, source stamping, validation rebuilding and health metadata.
This layer adds only fields independently confirmed in official SEBI/NSE
documents for records that remained partial after parser-v13 extraction.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import apply_verified_recent_offer_fields as base  # noqa: E402


base.VERIFIED_RECENT_OFFER_FIELDS.update(
    {
        "rambhajo": base._entry(
            "Advit Jewels Limited",
            "RAMBHAJO",
            "2026-06-23",
            "SEBI Advit Jewels Abridged Prospectus objects",
            "https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Advit%20Jewels%20Limited%20-%20APR_p.pdf",
            objectsOfIssue=[
                "Funding incremental working capital requirements of the Company",
                "Repayment or prepayment, in full or in part, of certain outstanding borrowings availed by the Company from a scheduled commercial bank",
                "General corporate purposes",
            ],
        ),
        "aastha": base._entry(
            "Aastha Spintex Limited",
            "AASTHA",
            "2026-06-29",
            "SEBI Aastha Spintex issue announcement registrar",
            "https://www.sebi.gov.in/sebi_data/attachdocs/jun-2026/1781090594066.pdf",
            registrar="Bigshare Services Private Limited",
        ),
        "aye": base._entry(
            "Aye Finance Limited",
            "AYE",
            "2026-02-09",
            "NSE Aye Finance Basis of Allotment promoter status",
            "https://nsearchives.nseindia.com/corporate/ADV_INE501X01029_13FEB2026.pdf",
            shareholding={"promoterPreIssuePct": 0.0},
        ),
        "csm": base._entry(
            "CSM Technologies Limited",
            "CSM",
            "2026-06-24",
            "SEBI CSM Technologies final Prospectus intermediaries",
            "https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1782884582544.pdf",
            registrar="KFin Technologies Limited",
            leadManagers=["Keynote Financial Services Limited"],
        ),
        "innovision": base._entry(
            "Innovision Limited",
            "INNOVISION",
            "2026-03-10",
            "NSE Innovision statement of issue-proceeds objects",
            "https://nsearchives.nseindia.com/corporate/INNOVISION2007_13052026170308_Reg_32_1_-_Statement_of_Deviation_and_variation_signed.pdf",
            objectsOfIssue=[
                "Repayment or prepayment, in part or full of all or certain borrowings availed by the Company",
                "Funding working capital requirements of the Company",
                "General corporate purposes",
            ],
        ),
        "jnpr": base._entry(
            "Juniper Green Energy Limited",
            "JNPR",
            "2026-07-30",
            "NSE Juniper Green Energy DRHP registrar",
            "https://nsearchives.nseindia.com/corporate/Registration_28062025043935_JuniperGreenEnergyLimitedDRHP.pdf",
            registrar="KFin Technologies Limited",
        ),
    }
)


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
