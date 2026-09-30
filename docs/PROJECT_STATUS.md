# Project status and handoff

Updated **2026-09-30 (UTC)** after the verified live closeout of the bounded **SSEK** 2023 release. Active priority remains **P1 issuer identity and data correctness**.

The SSEK release is **fully published and live-verified**. The immutable 2023 review ledger is now **16 reviewed/published + 14 awaiting review**. The bounded `reviewed_ssek` publisher and temporary SSEK live verifier are retired in this closeout branch and must not be replayed.

## Exact next bounded task

Review **Mish Designs Limited (544015)**, **AHASOLAR TECHNOLOGIES LIMITED (543941)**, **ORGANIC RECYCLING SYSTEMS LIMITED (543997)** and **Meson Valves India Limited (543982)** from the existing immutable 2023 queue. Start with retained authoritative issuer-specific source evidence and exact all-year identity reconciliation. Treat discovery dates/prices as non-authoritative until independently reviewed, preserve nulls/conflicts, and do not infer application amounts or board/identifier fields.

The next batch remains part of the bounded 30-row 2023 snapshot, not a fresh complete-universe audit. The original 2022 queue remains **14 reviewed/published + 2 existing-recovery alias + 0 awaiting review**.

## SSEK live closeout

The closed records are **SHANTI SPINTEX LIMITED (544059)**, **Shoora Designs Limited (543970)**, **Exhicon Events Media Solutions Limited (543895)** and **Khazanchi Jewellers Limited (543953)**. Reviewed actual BSE SME listing dates are **27-Dec-2023**, **29-Aug-2023**, **17-Apr-2023** and **07-Aug-2023** respectively.

PR **#350** merged the all-BSE provenance repair as **038593c36e7ad20309c0eb3374dfbd5b1bb39ab7**. Bounded publication workflow run **36662250755**, job **109719343973**, skipped normal live sync and pushed data commit **d4b196f6e9f37884d11cd48a3ef46cd930dcd47f**. Publication artifact **11074921852** recorded **1,383 existing public records unchanged + 4 additions = 1,387 records**. The generated public JSON was **7,798,075 bytes**, SHA-256 **77373449dcf00d800a82452072e92f45676d6611f2724e76a900d9f63adc7c6c**, generated at **2026-09-30T02:58:14.701Z**.

PR **#351** supplied a temporary read-only verification trigger because the Actions-authored data commit did not launch ordinary push workflows. Verification run **36662939353**, job **109721410740**, succeeded on fetch attempt **1**. The actual served Pages response was fetched at **2026-09-30T03:07:03.721Z**, checked at **2026-09-30T03:07:03.815Z**, contained **1,387** records, and matched the repository publication exactly: **7,798,075 bytes**, SHA-256 **77373449dcf00d800a82452072e92f45676d6611f2724e76a900d9f63adc7c6c**. Artifact **11075047555** is **250,608 bytes**, ZIP SHA-256 **3475799c28d017897cd25f502bcdcf8d3ad840328057dc01f134a5d2d991070d**, expiring **14-Oct-2026 03:07:04 UTC**. Durable verification is [bse-2023-ssek-live-2026-09-30.json](verification/bse-2023-ssek-live-2026-09-30.json).

The [release lifecycle](verification/bse-2023-ssek-release-2026-09-29.json) is now `verified_and_publisher_retired`. The 2023 progress ledger closes exactly four rows and advances to **16 published / 14 awaiting**.

## Listing-source repair and preserved evidence

Final source collection run **36661649197** retained all **4/4** listing reports on BSE-hosted filing URLs. Artifact **11075040486** is **53,439,026 bytes**, ZIP SHA-256 **4d15ea1dcc130e3be3e816dff55a99b8b2df6943aca35660b8221268ba01f81e**, expiring **14-Oct-2026 02:50:36 UTC**.

The first release attempt in PR **#349** failed safely before any push because the public-data builder rejected an issuer-hosted Exhicon source. No SSEK record was partially published and normal sync was skipped. The repair did **not** expand the builder trust allowlist: Exhicon was switched to a byte-identical BSE-hosted revised annual report; Khazanchi was switched to its BSE Regulation 34 filing and its physical evidence locators were re-reviewed because that filing adds a cover page.

The original Prospectus field review remains unchanged. Preserve Shanti's ₹80 Cut Off Price typo as an inconsistency, Exhicon's offer-date definition conflict, Shanti/Exhicon provisional issue amounts, and fixed-price semantics for Shoora/Khazanchi. Board, NSE identity, ISIN and monetary minimum application amount remain null/unapproved for all four. Market lot, minimum bid quantity and minimum application amount remain distinct.

## Release and verification guards

`scripts/apply-reviewed-bse-2023-ssek.mjs` remains as immutable/reproducible release logic but is no longer wired to an active publisher. `scripts/check-bse-2023-ssek-field-review.mjs` now distinguishes pre-publication clearance from the exact post-publication identity state and still rejects aliases/collisions. `scripts/check-bse-2023-progress.mjs` accepts both SHA-256-pinned legacy review manifests and Git-blob-pinned reviewed manifests.

Do not replay PR #350, its data commit, or the temporary live verification trigger. Preserve source hashes, collection clocks, page locators, nulls and correction history.

## Preserved project boundaries

The prior IRMS and earlier 2020–2022/NSE releases remain closed and should not be replayed. Administrative/legal items remain separate: **#339** main protection, **#347** code-vs-data licensing and **#348** exact merged-branch cleanup.

DRHP collection remains a separate fail-closed source-health workstream; do not mix it into this bounded 2023 review.

Continue P1. Do not expand P5/performance while upstream correctness remains materially blocked. No new spending, contracts, accounts, analytics, ads, billing, infrastructure or material access changes without approval. Follow [DEVELOPMENT_PROCESS](DEVELOPMENT_PROCESS.md).
