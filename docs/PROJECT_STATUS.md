# Project status and handoff

## Current handoff — October audit closed — 2026-10-05 UTC

**ALL FIFTEEN ORIGINAL OCTOBER 4 AUDIT FINDINGS ARE REPAIRED, MERGED AND
RELEASED.** The durable defect-to-release map is
[verification/october-audit-closeout-2026-10-05.md](verification/october-audit-closeout-2026-10-05.md).

The final defect, BUG-015 document-filter keyboard focus, merged in PR #366 as
`d3e44eb78a8b9f749ef3d21dde9b50daea308def`. Exact-head browser, data-contract,
reviewed-BSE and historical gates passed. Post-merge Pages **37352664322** verified
the served 1,388-record `data/ipos.json` on attempt 1, SHA-256
`1741ef733cb06bc6e8d2d466ebd861ab8336996a6e7a69a0751e58dfbe1d3360`.
Post-merge data contract **37352664476** and browser/interface **37352664386**
also passed. Pages health commit: `f2da5f4efc06f3114a6dcf351b6674985e7e3a69`.

Release sequence:
- PR #354: BUG-002/003/004.
- PR #356: BUG-001/005.
- PR #357: BUG-014 browser-fixture stabilization plus the separate duplicate-route
  skip-link focus race.
- PR #359: BUG-006/008.
- PR #360: BUG-007.
- PR #362: BUG-012.
- PR #361: BUG-009.
- PR #363: BUG-010.
- PR #364: BUG-011.
- PR #365: BUG-013.
- PR #366: BUG-015.

Important qualifications:
- SMCG04 remains excluded from the equity-IPO public directory on retained DEBT
  series evidence; recovery evidence is preserved.
- BUG-011 corrected six derived public `last_collected_at` values only. Raw
  recovery evidence was not redated.
- BUG-013 exposes lead-manager timestamp dates as proxies; it does not rewrite
  retained filing dates.
- The SEBI DRHP pagination surface can still fail upstream. BUG-012 keeps that
  failure isolated, retains the last good dataset, permits the independent Axis
  fallback attempt and records per-source health. Source availability itself is
  not claimed fixed.

## SSEK closeout — verified and retired — 2026-10-05 UTC

The four-record SSEK release remains closed without replay. Historical Pages
verification run **36662939353** / artifact **11075047555** was independently
rechecked during the closeout refresh. The temporary SSEK publisher and
temporary SSEK live-verifier workflow remain retired.

At SSEK closeout the immutable 2023 ledger was **16 reviewed/published + 14
awaiting review**.

## Mish Designs release — published and served-verified — 2026-10-05 UTC

Mish Designs Limited moved through separate bounded stages:
- PR #368 retained issuer/BSE source evidence without publication;
- PR #369 rejected a false BSE Prospectus candidate that was actually Arrowhead
  Seperation Engineering Limited;
- PR #370 retained the semantic field review without publication;
- PR #371 approved a BSE-only public projection without mutating production data;
- PR #372 merged the exact two-file publication as
  `58df8b081a0ff8b515e4ce650de32be452492642`.

Publication preparation run **37369397820**, attempt **2**, proved **1,388
existing public records unchanged** and exactly one added stable ID. Pages run
**37384618726** served the resulting **1,389-record** dataset on verification
attempt **1**, SHA-256
`333e7a7570965e47661386fada8ca20efed40523669d1be9d5167ad4ead13e4f`.
Verification artifact **11376300416** retains the served bytes/report. The served
Mish record exactly matches the approved projection and exposes only
`www.bseindia.com` evidence.

Published Mish facts are fixed issue price INR 122/share, total issue size
INR 97,600,000, offer dates 31-Oct-2023 through 02-Nov-2023, and actual listing
07-Nov-2023. Board, price band, market lot, minimum bid quantity and minimum
application amount remain null as reviewed. The issuer Prospectus's reversed
date-label observations remain preserved in correction history. See
[the live receipt](verification/bse-2023-mish-live-2026-10-05.json).

The immutable 2023 ledger is now **17 reviewed/published + 13 awaiting review**.

## Exact next bounded task

Review **AHASOLAR TECHNOLOGIES LIMITED (543941)**,
**ORGANIC RECYCLING SYSTEMS LIMITED (543997)**,
**Meson Valves India Limited (543982)** and
**TECHKNOWGREEN SOLUTIONS LIMITED (543991)** from the pinned 2023 queue. Start
with retained authoritative issuer-specific evidence and exact all-year identity
reconciliation. Treat discovery values as non-authoritative until reviewed,
preserve nulls/conflicts, and publish only via a separate reviewed manifest plus
exact served-data verification.

The original 2022 queue remains **14 reviewed/published + 2 existing-recovery alias + 0 awaiting review**; its next bounded queue is empty.

Continue P1 correctness. P5/performance remains out of scope while source/release
governance work is unresolved. No new spending, contracts, accounts, analytics,
ads, billing, infrastructure migration or material access changes without
approval.

## Browser gate and admission release — 2026-10-05 UTC

**MERGED, DEPLOYED AND SERVED-VERIFIED.** Separate browser PR #357 merged as
`ea0301aa`; refreshed admission/identity PR #356 merged as `0e0da6ce` on
2026-10-05 at 00:35 UTC (October 4, 20:35 EDT). All seven refreshed PR checks
passed. Four browser scripts passed all three repetitions before and after merge;
102 non-browser entrypoints passed locally. Post-merge browser 37248108152,
data contract 37248108188 and Pages 37248108151 succeeded.

Served IPO JSON: HTTP 200, first attempt, 1,388 records, SHA-256
`941e85283cf468a67ec4ad556755ed930afdd1dcef5c30fe0cf8ff86eba8307b`.
Only the explicitly DEBT SMCG04 public record was excluded; its full recovery
evidence, all seven recovery files and all other public objects were preserved.
See [release evidence and exact scope](verification/browser-gate-and-admission-release-2026-10-05.md).

BUG-014 fixture brittleness and the separate duplicate-route skip-link race are
fixed; BUG-015 document-filter focus is not. Together with PR #354, six original
audit fixes are deployed. BUG-006/007/008/009/010/011/012/013/015 remain open.
**Next bounded work:** amended-term/conflict retention (BUG-006) and endpoint
provenance (BUG-008), after checking current source health. SSEK #352 remains
separate. No historical replay, P5 expansion, spending or access changes.

The prior 37241174980/37242214201 cycle is verified complete. The receipt above
supersedes pending-release wording below, which is retained as historical evidence.

---

## Historical checkpoints — superseded by the release above

## Browser-gate stabilization — 2026-10-04

Separate test/focus batch unblocks PR #356; no public or recovery data is changed.
Fixed synthetic fixtures replace production-dependent count/status assumptions.
Duplicate same-URL route notifications no longer reset keyboard focus or research
state; genuine navigation and data reload still render. Local non-browser checks
passed; merge only after repeated pinned-runner browser checks are green.
See [scope and regression design](verification/browser-gate-stabilization-2026-10-04.md).

Next: validate/merge this separate batch, refresh and rerun PR #356, then verify
its served output. The prior sync 37241174980/downstream 37242214201 succeeded;
older pending paragraphs below are historical checkpoints. SSEK #352 stays open.

---

## Data-integrity safeguard release — 2026-10-04

**MERGED AND DEPLOYED; served snapshot verified. First post-merge live-sync
completion remains unverified.** PR #354 merged at **2026-10-04 22:44:42 UTC**
as `be8ec1e0c1683a6e9fa41ddd78fd34e4aa1dd804`. This closes the code review/merge
step for BUG-003 (atomic observations), BUG-004 (retained null/history) and
BUG-002 (typed domain validation); it does not close the other twelve audit bugs.
See [release receipt](verification/ipo-integrity-release-2026-10-04.md) and the
[original implementation record](verification/ipo-integrity-safeguards-2026-10-04.md).

Review reran all 103 local script entrypoints: **100 non-browser passes; three
browser entrypoints blocked by missing Playwright**, not counted as passing.
Additional 48 atomic-observation combinations, builder consistency, full corpus
validation and independent Python schema validation passed. All seven PR checks
passed. Post-merge Node 20 data-contract run **37241175018** also passed.

Pages deployment **37241175061** succeeded. Its retained served response at
**22:45:08 UTC** returned HTTP 200 and matched the public JSON on attempt 1:
**1,389 records**, SHA-256
`2343c0ae10a83fb56453f34afefcbe7d5568a1f295c62467fd532b1c1f60c53b`.
The six DRHP/page-asset responses also matched. Patched production files and all
seven unchanged recovery manifests matched the uploaded deployment archive.
No IPO facts or timestamps were changed by this release or this handoff update.

**Exact next task:** inspect live-sync run **37241174980** and its downstream
publication before claiming a fully verified production collection cycle. At the
last check NSE collection and SEBI document attachment had succeeded and it was
extracting issue fields; rebuild, semantic apply and repository publication were not yet
verified. If successful, proceed to BUG-001 / BUG-005 (instrument eligibility and
contradictory issuer identity). Do not rerun the historical one-shot imports.

SSEK closeout PR #352 is separate and is not closed by the Pages byte check.
DRHP had independently recovered at **2026-10-04 21:21:28 UTC** (102 companies,
104 filings, consistent pagination); this preceded PR #354 and is not credited
to this batch. Recheck current source health rather than repeat the old failure
status. Schedule gaps, licensing and main protection remain separate workstreams.
Do not expand P5/performance or introduce new spending, access changes or monetization.

**Historical clarification:** PR #353 merged on 2026-09-30 at 16:35 UTC. The
September 30 paragraphs below retain their original pre-merge context, not the
current state. All source qualifications, evidence and release history remain.

---

## Retained preceding handoff

## Website logic repair batch prepared for review — 2026-09-30

All seven subsequent website-review findings have local repairs: date-aware
bidding status, explicit price conflicts, distinct trading-lot/minimum-bid labels,
chronological fallback sorting, company-only search, separate draft freshness,
and unavailable-board browsing. An independent review's open-tab midnight issue
was also fixed. All 103 regression scripts and the syntax, builder and contract
checks passed. Every retained source record and dataset timestamp is preserved;
the public array is reordered through the shared comparator. See the
[behavior and verification record](verification/product-logic-repairs-2026-09-30.md).
Changes are prepared on the repair branch; merge, deployment, source pricing reconciliation and the
historical served-data closeout below remain separate work.

## Code review repair batch prepared for review — 2026-09-30

Nine reviewed correctness, publication, validation and navigation findings have
local repairs and regression coverage. Five 2026 lifecycle statuses were advanced
using their existing verified elapsed NSE listing dates, preserving prior evidence
and the other 1,382 public records. No source was refetched. See the
[repair and validation record](verification/code-review-repairs-2026-09-30.md).
Merge and deployment remain pending; the historical SSEK release below is still
awaiting its separate served-data closeout.

Updated **2026-09-30 (UTC)** after PR #350 repaired the listing-source provenance and the guarded SSEK publisher successfully added four reviewed records to repository data. Active priority remains **P1 issuer identity and data correctness**.

The SSEK release lifecycle is now **`published_verification_pending`**. Repository data commit **d4b196f6e9f37884d11cd48a3ef46cd930dcd47f** added exactly four reviewed records while preserving **1,383** existing public objects unchanged, producing **1,387** public records. The immutable 2023 review ledger intentionally remains **12 reviewed/published + 18 awaiting review** until the actual served Pages dataset is verified.

## Historical SSEK next-task checkpoint — superseded

Complete the pending release for **SHANTI SPINTEX LIMITED (544059)**, **Shoora Designs Limited (543970)**, **Exhicon Events Media Solutions Limited (543895)** and **Khazanchi Jewellers Limited (543953)**.

Run the temporary **read-only served-data verifier** against the deployed Pages dataset and retain the fetched response. Only after all four exact reviewed projections match may the four queue rows be closed and both temporary release surfaces (`reviewed_ssek` and the SSEK live verifier) be retired.

Do not replay earlier IRMS or historical releases. Do not let the normal sync run on the explicit SSEK release commit.

The original 2022 queue remains **14 reviewed/published + 2 existing-recovery alias + 0 awaiting review**; its next bounded queue is empty.

## SSEK reviewed scope

The four approved identities are:

- **SHANTI SPINTEX LIMITED (544059)** — actual BSE SME listing **27-Dec-2023**.
- **Shoora Designs Limited (543970)** — actual BSE SME listing **29-Aug-2023**.
- **Exhicon Events Media Solutions Limited (543895)** — actual BSE SME listing/trading commencement **17-Apr-2023**.
- **Khazanchi Jewellers Limited (543953)** — actual BSE SME listing **07-Aug-2023**.

The listing review is [data/discovery/bse-2023-ssek-listing-review-2026-09-29.json](../data/discovery/bse-2023-ssek-listing-review-2026-09-29.json), pinned by [data/verified-bse-listings/2026-09-29-ssek-2023.json](../data/verified-bse-listings/2026-09-29-ssek-2023.json). Publication remains bounded to these four exact stable IDs and BSE codes.

Board mapping, NSE identity, ISIN and monetary minimum application amount remain **null/unapproved** for all four. The annual reports explicitly say BSE SME, but that observation is retained separately and is not silently mapped into the tracker board field.

## Listing-source retention

Final read-only repair workflow run **36661649197**, attempt **1**, retained all **4/4** selected annual-report PDFs from **BSE-hosted filing URLs**. Artifact **11075040486** is **53,439,026 bytes**, ZIP SHA-256 **4d15ea1dcc130e3be3e816dff55a99b8b2df6943aca35660b8221268ba01f81e**, expiring **14-Oct-2026 02:50:36 UTC**. Original PDFs total **54,941,101 bytes**.

The durable [listing-source receipt](../data/evidence/bse-2023-ssek-listing-source-receipt-2026-09-29.json) binds exact source URLs, response hashes/lengths, page counts, collection clocks and artifact. Exhicon's BSE-hosted revised annual report is byte-for-byte identical to the reviewed issuer copy. Khazanchi's BSE Regulation 34 filing adds one cover page, so its physical listing locator is re-reviewed at PDF page **26** and its BSE code is bound on PDF page **1**.

The first guarded publication run **36658314491** stopped before push because the public-data builder correctly rejected Exhicon's issuer-hosted source. Artifact **11073505374** retains that failed publication attempt. No SSEK record reached recovery or public data, and the normal sync job remained skipped.

The temporary repair collector has been retired from the release branch. Reproducibility scripts remain, but collection itself cannot authorize publication.

## Prospectus terms preserved

The original [Prospectus field review](../data/discovery/bse-2023-ssek-field-review-2026-09-29.json) remains unchanged:

- **Shanti:** ₹66–₹70 band, final ₹70 offer price, ₹312.48m total offer provisional, market lot/minimum bid 2,000, public 19–21 Dec 2023. Preserve the source's ₹80 Cut Off Price typo as an inconsistency; do not use it.
- **Shoora:** fixed price ₹48, ₹20.304m gross fresh issue, market lot/minimum bid 3,000, public 17–21 Aug 2023. No price band invented.
- **Exhicon:** ₹61–₹64 band, final ₹64 issue price, ₹211.2m total fresh issue provisional, market lot/minimum bid 2,000, public 31 Mar–05 Apr 2023. Preserve the definitions-date conflict.
- **Khazanchi:** fixed price ₹140, ₹967.4m gross fresh issue, market lot/minimum bid 1,000, public 24–28 Jul 2023. No price band invented.

Market lot, minimum bid quantity and minimum application amount remain distinct. No amount is inferred from price × quantity.

## Repository publication complete; served verification pending

PR **#350** merged as **038593c36e7ad20309c0eb3374dfbd5b1bb39ab7**. Bounded publication workflow run **36662250755**, job **109719343973**, passed its reviewed-import and preservation checks, skipped normal live sync, and pushed data commit **d4b196f6e9f37884d11cd48a3ef46cd930dcd47f**.

Publication artifact **11074921852** is **499,208 bytes**, ZIP SHA-256 **f7e80a5ecda702ef94105d4642563c1416080662394dabbf141e45fe33480a12**, and records **1,383 existing records unchanged + 4 additions = 1,387**. The generated public JSON is **7,798,075 bytes**, SHA-256 **77373449dcf00d800a82452072e92f45676d6611f2724e76a900d9f63adc7c6c**, generated at **2026-09-30T02:58:14.701Z**.

A later Pages build for main commit **268ceb75d9eeff427e2165c18bb88092d4bd6cf5** completed successfully. The data commit was authored by the repository automation token, so the push-only SSEK live verifier did not auto-start. A temporary explicit `verify(ssek):` trigger is being used to obtain and retain the actual served response without changing published data.

## Import and publication guards

`scripts/apply-reviewed-bse-2023-ssek.mjs` is idempotent and fails closed on stable-ID, canonical-name or BSE-code collisions across every recovery year. It pins the approved manifest/review/receipt/source-plan blobs, preserves pre-existing records, and can mutate only the 2023 recovery file when explicitly run with `--apply`.

`scripts/verify-bse-2023-ssek.mjs` compares the actual served Pages snapshot against all four exact reviewed public projections. The temporary lifecycle file is [docs/verification/bse-2023-ssek-release-2026-09-29.json](verification/bse-2023-ssek-release-2026-09-29.json).

Full data-contract run **36657540634** passed after the reviewed importer was added, including the SSEK source, field, import and live-verifier test cases. The later release-lifecycle CI is the final gate before merge.

## Preserved project boundaries

The prior IRMS release remains fully published and live-verified; its bounded publisher is retired. Administrative/legal items remain separate: **#339** main protection, **#347** code-vs-data licensing and **#348** exact merged-branch cleanup.

DRHP remains fail-closed on unstable SEBI pagination; do not mix that separate source-health issue into this bounded 2023 release.

Continue P1. Do not expand P5/performance while upstream correctness remains materially blocked. No new spending, contracts, accounts, analytics, ads, billing, infrastructure or material access changes without approval. Follow [DEVELOPMENT_PROCESS](DEVELOPMENT_PROCESS.md).
