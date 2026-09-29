# Project status and handoff

Updated **2026-09-29 (UTC)** after the verified live closeout of PR #342 in **PR #343** and the repository loose-end hardening sequence. Active product priority remains **P1 issuer identity and data correctness**.

The IREDA/Motisons/RBZ/Shelter release is **fully published and live-verified**. The bounded `reviewed_irms` publisher has been retired. The immutable 2023 review ledger is now **12 reviewed/published + 18 awaiting review**. Do not replay the IRMS import or its temporary verifier.

## Exact next bounded task

Review **SHANTI SPINTEX LIMITED (544059)**, **Shoora Designs Limited (543970)**, **Exhicon Events Media Solutions Limited (543895)** and **Khazanchi Jewellers Limited (543953)** from the existing immutable 2023 queue. Start with official source retention and all-year identity reconciliation; preserve discovery-only values as non-authoritative until issuer-specific evidence is reviewed. Do not infer missing application terms or overwrite later recovery evidence.

The next batch remains part of the bounded 30-row 2023 snapshot, not a fresh complete-universe audit. The original 2022 queue remains **14 reviewed/published + 2 existing-recovery alias + 0 awaiting review**; 2021 is also complete.

## IRMS live closeout

PR #342 published exactly four reviewed records through data commit **ed5599db1a625f7d8513c8990b29e1bc40ab6375**. The publication artifact recorded **1,378 existing records unchanged + 4 additions = 1,382 published records**.

PR #343's read-only verifier fetched the actual served `data/ipos.json` on the first attempt at **2026-09-29T14:41:23.875Z**. The served response was **7,738,917 bytes**, SHA-256 **f61a41fc9b0db23f256dfc9b4a55a6183bbbbf32aa62cd21949e633a78a273b9**, generated at **2026-09-29T14:37:16.380Z**, and matched all four exact reviewed public projections. The durable [live receipt](verification/bse-2023-irms-live-2026-09-29.json) is backed by workflow run **36584512199**, artifact **11040473771**, ZIP SHA-256 **90b963dec8cd97b4845bc21805909e1e077b95b14fb4da4b1b53fb3fd20316ec**. Raw artifact retention expires **13-Oct-2026**.

The four closed records are Indian Renewable Energy Development Agency Limited, Motisons Jewellers Limited, RBZ Jewellers Limited and SHELTER PHARMA LIMITED. The approved manifest and original listing/prospectus evidence remain unchanged. IREDA's offer-total discrepancy remains an unresolved conflict; Motisons/RBZ amounts remain provisional; Shelter remains fixed-price with no invented band. Market lot, minimum bid quantity and minimum application amount remain distinct.

The [release lifecycle](verification/bse-2023-irms-release-2026-09-29.json) is now `verified_and_publisher_retired`. The temporary closeout workflow is not retained in the final tree, and the one-shot `reviewed_irms` job has been removed from `update-ipos.yml`.

## Repository loose-end hardening completed

The repository-wide audit and repair sequence completed the following safe work:

- stale PRs **#152, #196, #246, #247, #317 and #335** are closed unmerged after semantic supersession review;
- completed one-shot release/materialization writers were retired, followed by consolidation of redundant completed-release validators; the active workflow surface fell from **50 to 23** before the temporary IRMS closeout workflow was removed;
- production-write workflow capability is guarded by an explicit allowlist for the sanctioned operational writers;
- missed scheduled starts are now monitored separately from execution failures;
- DRHP pagination drift now fails closed after bounded retry; two fresh attempts on **29-Sep-2026** still alternated between SEBI totals **2215/2213**, so the last good 96-company / 98-filing snapshot remains retained rather than replaced by an inconsistent scan;
- historical SEBI PDF downloads now resume partial transfers. The first post-merge production runs reduced offer-date transport errors **33 → 23** and historical PDF-field errors **5 → 2**;
- `SECURITY.md`, `CONTRIBUTING.md`, CODEOWNERS, PR checks and focused issue templates are now present.

Three repository-administration/legal items remain intentionally open because the current connector cannot or should not decide them automatically: **#339** protect `main` without breaking sanctioned Actions writers; **#347** decide source-code license vs data redistribution terms; **#348** delete the **310** exact merged-PR branch tips identified by the branch audit. Do not bulk-delete the remaining closed-unmerged/no-PR/advanced-after-merge branches without semantic review.

## Preserved release evidence and boundaries

The pre-closeout handoff is preserved byte-for-byte in [PROJECT_STATUS_ARCHIVE_THROUGH_IRMS_RELEASE_2026-09-29.md](PROJECT_STATUS_ARCHIVE_THROUGH_IRMS_RELEASE_2026-09-29.md). Earlier IRMS field/source archives remain authoritative for original evidence and qualifications.

Do not replay PR #342 or earlier completed BSE/NSE releases. Preserve all retained conflicts, aliases, nulls, source hashes, clocks and correction history. The active application term remains **Lot Size only**, using verified market lot first and verified minimum bid only when market lot is missing. Never derive minimum investment/application amounts.

DRHP collection is currently **source-unstable, fail-closed** rather than healthy: the last successful collection remains **2026-09-28T13:49:35.161Z** with **96 companies / 98 filings**. The schedule-health monitor correctly treats the latest critical DRHP run as failed. Do not relabel that run successful or drop retained filings.

Continue P1. Do not expand P5/performance while upstream correctness remains materially blocked. No new spending, contracts, accounts, analytics, ads, billing, infrastructure or material access changes without approval. Follow [DEVELOPMENT_PROCESS](DEVELOPMENT_PROCESS.md).
