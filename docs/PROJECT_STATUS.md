# Project status and handoff

Updated **2026-09-29 (UTC)** after completing the bounded **SSEK** source and Prospectus-term review for **SHANTI SPINTEX LIMITED (544059)**, **Shoora Designs Limited (543970)**, **Exhicon Events Media Solutions Limited (543895)** and **Khazanchi Jewellers Limited (543953)**. Active priority remains **P1 issuer identity and data correctness**.

The immutable 2023 review ledger remains **12 reviewed/published + 18 awaiting review**. This source/field review does **not** advance those four rows and does not authorize publication.

## Exact next bounded task

Retain approved original **actual-listing evidence** for the same four issuers: an exchange listing notice, annual report with explicit actual listing statement, or equivalent authoritative original source that establishes actual listing date and exchange identity. Keep BSE codes from the discovery queue non-authoritative until that evidence is reviewed. Re-run exact all-year identity reconciliation immediately before any later import.

After actual-listing review, prepare a separate pinned import manifest, preserve all source inconsistencies and provisional qualifications, publish only after current-recovery collision checks, then verify exact served projections before closing any queue row.

## SSEK source retention

Read-only source workflow run **36601106741**, attempt **1**, retained all **8/8** planned official SEBI responses: four landing pages and four linked Prospectus PDFs. Total retained original response bytes: **16,817,590**. Artifact **11048768865** is **16,843,453 bytes**, ZIP SHA-256 **938d65dbc230e0f0a3264a80dff8fa772d9d99695a7347db0b54a60fd914fcda**, expiring **13-Oct-2026 16:55 UTC**.

The durable [source receipt](../data/evidence/bse-2023-ssek-source-receipt-2026-09-29.json) retains every original response SHA-256/length and the exact identity preflight. At collection time, **1,383 recovery records and 1,383 public records** were checked with exact stable-id/canonical-name/BSE-code matching; all four candidates had **zero matches and zero identity holds**. This permits source review only and is not permanent alias clearance or import approval.

The temporary source-collection workflow is removed from the final review branch after the complete artifact was retained. Collector/plan/test code stays available for reproducibility but no recurring writer or collector is added.

## Reviewed Prospectus terms

The [field review](../data/discovery/bse-2023-ssek-field-review-2026-09-29.json) records **32 dispositions: 24 verified stated terms, 2 provisional issue amounts, 2 fixed-price band-not-applicable fields and 4 missing actual listing dates**. Original retained PDF pages were visually checked locally; Poppler text extraction was used without OCR.

**SHANTI SPINTEX LIMITED:** Prospectus dated **22-Dec-2023**; price band **₹66–₹70**, final Offer Price **₹70**, total offer **up to ₹3,124.80 lakh / ₹312.48m** retained as provisional, market lot **2,000**, retail minimum bid **2,000**, public open/close **19-Dec / 21-Dec-2023**, anchor **18-Dec-2023**. Preserve the definitions typo stating a **₹80 Cut Off Price**; it is not used because the same Prospectus states Cap Price and final Offer Price at ₹70.

**Shoora Designs Limited:** original Prospectus dated **09-Aug-2023** despite the SEBI landing page being displayed **04-Apr-2024**. Preserve those as separate clocks. Fixed price **₹48**, gross fresh issue **₹20.304m**, market lot/minimum retail application **3,000**, public open/close **17-Aug / 21-Aug-2023**. No price band or anchor date is invented.

**Exhicon Events Media Solutions Limited:** Prospectus dated **10-Apr-2023**; price band **₹61–₹64**, final issue price **₹64**, total fresh issue **up to ₹2,112 lakh / ₹211.2m** retained as provisional, market lot/minimum bid **2,000**, anchor **29-Mar-2023**, cover programme public open/close **31-Mar / 05-Apr-2023**. Preserve the conflicting definitions text that misstates/mislabels the offer dates; the review binds to the explicit cover programme rather than silently rewriting the source.

**Khazanchi Jewellers Limited:** Prospectus dated **15-Jul-2023**; fixed price **₹140**, gross fresh issue **₹9,674 lakh / ₹967.4m**, market lot/minimum retail application **1,000**, public open/close **24-Jul / 28-Jul-2023**. No price band or anchor date is invented.

For all four, actual listing date, verified exchange identifiers/board, ISIN and monetary minimum application amount remain unapproved/null at this stage. Exact stated gross amounts are not represented as independently verified realised proceeds.

## Preserved repository boundaries

The prior handoff covering the IRMS closeout and repository hardening is archived byte-for-byte in [PROJECT_STATUS_ARCHIVE_THROUGH_REPO_HARDENING_2026-09-29.md](PROJECT_STATUS_ARCHIVE_THROUGH_REPO_HARDENING_2026-09-29.md). Do not replay the completed IRMS, 2020–2022, NSE or historical release workflows.

Administrative/legal blockers remain tracked separately: **#339** main protection, **#347** code-vs-data licensing, **#348** deletion of exact merged-PR branch tips. DRHP remains fail-closed on unstable SEBI pagination; do not mix that separate source-health issue into this bounded 2023 review.

Continue P1. Preserve nulls, conflicts, original units, document hashes, page locators and reporting periods. Market lot, minimum bid quantity and monetary minimum application amount remain distinct. No new spending, contracts, accounts, analytics, ads, billing or material access changes without approval.
