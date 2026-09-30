# Project status and handoff

Updated **2026-09-30 (UTC)** after PR #349 merged but its guarded SSEK publisher failed safely before any data push, followed by an all-BSE listing-source repair. Active priority remains **P1 issuer identity and data correctness**.

The SSEK release lifecycle remains **`prepared_import_pending`**. PR #349 did **not** publish any SSEK recovery/public record: `build-published-data.mjs` rejected the issuer-hosted Exhicon URL before commit/push, and the normal sync job was skipped. The immutable 2023 review ledger therefore remains **12 reviewed/published + 18 awaiting review** until the actual served Pages dataset is verified.

## Exact next bounded task

Complete the pending release for **SHANTI SPINTEX LIMITED (544059)**, **Shoora Designs Limited (543970)**, **Exhicon Events Media Solutions Limited (543895)** and **Khazanchi Jewellers Limited (543953)**.

Merge the **all-BSE source-repair release** only after final PR/synthetic-merge checks are green. The merge commit must start with **`release(ssek):`** so the temporary `reviewed_ssek` job retries exactly the four reviewed records against latest `main`. Then verify the actual served `data/ipos.json` with the temporary read-only SSEK verifier. Only after exact served projections match may the four queue rows be closed and both temporary release surfaces retired.

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

The durable [listing-source receipt](../data/evidence/bse-2023-ssek-listing-source-receipt-2026-09-29.json) binds exact source URLs, response hashes/lengths, page counts, collection clocks and artifact. Exhicon's BSE-hosted revised annual report is byte-for-byte identical to the previously reviewed issuer copy. Khazanchi's BSE Regulation 34 filing adds one cover page, so its physical listing locator is re-reviewed at PDF page **26** and its BSE code is bound on PDF page **1**.

The first guarded publication run **36658314491** stopped before push because the public-data builder correctly rejected Exhicon's issuer-hosted source. Artifact **11073505374** retains that failed publication attempt. No SSEK record reached recovery or public data, and the normal sync job remained skipped.

The temporary repair collector has been retired from the release branch. Reproducibility scripts remain, but collection itself cannot authorize publication.

## Prospectus terms preserved

The original [Prospectus field review](../data/discovery/bse-2023-ssek-field-review-2026-09-29.json) remains unchanged:

- **Shanti:** ₹66–₹70 band, final ₹70 offer price, ₹312.48m total offer provisional, market lot/minimum bid 2,000, public 19–21 Dec 2023. Preserve the source's ₹80 Cut Off Price typo as an inconsistency; do not use it.
- **Shoora:** fixed price ₹48, ₹20.304m gross fresh issue, market lot/minimum bid 3,000, public 17–21 Aug 2023. No price band invented.
- **Exhicon:** ₹61–₹64 band, final ₹64 issue price, ₹211.2m total fresh issue provisional, market lot/minimum bid 2,000, public 31 Mar–05 Apr 2023. Preserve the definitions-date conflict.
- **Khazanchi:** fixed price ₹140, ₹967.4m gross fresh issue, market lot/minimum bid 1,000, public 24–28 Jul 2023. No price band invented.

Market lot, minimum bid quantity and minimum application amount remain distinct. No amount is inferred from price × quantity.

## Import and publication guards

`scripts/apply-reviewed-bse-2023-ssek.mjs` is idempotent and fails closed on stable-ID, canonical-name or BSE-code collisions across every recovery year. It pins the approved manifest/review/receipt/source-plan blobs, preserves pre-existing records, and can mutate only the 2023 recovery file when explicitly run with `--apply`.

`scripts/verify-bse-2023-ssek.mjs` compares the actual served Pages snapshot against all four exact reviewed public projections. The temporary lifecycle file is [docs/verification/bse-2023-ssek-release-2026-09-29.json](verification/bse-2023-ssek-release-2026-09-29.json).

Full data-contract run **36657540634** passed after the reviewed importer was added, including the SSEK source, field, import and live-verifier test cases. The later release-lifecycle CI is the final gate before merge.

## Preserved project boundaries

The prior IRMS release remains fully published and live-verified; its bounded publisher is retired. Administrative/legal items remain separate: **#339** main protection, **#347** code-vs-data licensing and **#348** exact merged-branch cleanup.

DRHP remains fail-closed on unstable SEBI pagination; do not mix that separate source-health issue into this bounded 2023 release.

Continue P1. Do not expand P5/performance while upstream correctness remains materially blocked. No new spending, contracts, accounts, analytics, ads, billing, infrastructure or material access changes without approval. Follow [DEVELOPMENT_PROCESS](DEVELOPMENT_PROCESS.md).
