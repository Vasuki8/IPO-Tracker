#!/usr/bin/env python3
"""Extend the verified recent-offer registry for narrow P4 partial residuals.

The base verified-field runner remains authoritative for exact identity guards,
fill-only semantics, source stamping, validation rebuilding and health metadata.
This layer adds only fields independently confirmed in official SEBI/NSE or
issuer-hosted offer documents for records that remained partial after parsing.
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
            "Aastha Spintex issuer-hosted RHP offer terms",
            "https://aasthaspintex.com/pdf/RHP/RHP_Aastha.pdf",
            registrar="Bigshare Services Private Limited",
            shareholding={"promoterPreIssuePct": 74.23},
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
            "Innovision issuer-hosted offer documents",
            "https://www.innovision.co.in/public/uploads/631573851.pdf",
            objectsOfIssue=[
                "Repayment or prepayment, in part or full of all or certain borrowings availed by the Company",
                "Funding working capital requirements of the Company",
                "General corporate purposes",
            ],
            shareholding={"promoterPreIssuePct": 100.0},
        ),
        "jnpr": base._entry(
            "Juniper Green Energy Limited",
            "JNPR",
            "2026-07-30",
            "Juniper Green Energy issuer-hosted DRHP offer terms",
            "https://www.junipergreenenergy.com/wp-content/uploads/2025/06/JuniperGreenEnergyLimitedDRHP.pdf",
            registrar="KFin Technologies Limited",
            shareholding={"promoterPreIssuePct": 100.0},
        ),
        "rsl": base._entry(
            "Rajputana Stainless Limited",
            "RSL",
            "2026-03-09",
            "Rajputana Stainless issuer-hosted final Prospectus shareholding",
            "https://www.rajputanastainless.com/public/frontend/assets/pdf/RSL_Prospectus_Project-Steel_Final.pdf",
            shareholding={"promoterPreIssuePct": 78.22},
        ),
        "shiprocket": base._entry(
            "Shiprocket Limited",
            "SHIPROCKET",
            "2026-08-12",
            "Shiprocket issuer financial statements promoter status",
            "https://sr-website-01.shiprocket.in/sr-website/1.%20Shiprocket%20Standalone%20financials%20FY%2024-25-ulD9o9.pdf",
            shareholding={"promoterPreIssuePct": 0.0},
        ),
    }
)


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
