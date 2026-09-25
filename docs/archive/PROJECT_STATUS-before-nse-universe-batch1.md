# Project status and handoff

Updated: **2026-09-25**, 04:39 UTC / 00:39 America/Toronto verification window. The bounded official-universe audit is operationally verified. Full IPO-universe completeness remains unresolved.

## Current priority

Continue **P1 issuer identity and IPO-universe coverage** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The active application-term requirement remains **Lot Size only**. Preserve market lot, minimum bid quantity and minimum application amount as distinct fields. No UI or downstream commercial-feature work belongs to this continuation.

## VERIFIED: read-only official IPO-universe audit — PR #229

PR #229 merged as `2c9b5d0d97754747b6510a0bb0ad837e988e65b0`. The release adds a reusable, bounded official-source audit rather than importing unreviewed names. It does not change published IPO records or recovery evidence.

The six-file code change consists of `scripts/collect-ipo-universe-sources.mjs`, `scripts/audit-ipo-universe.mjs`, `scripts/test-audit-ipo-universe.mjs`, `scripts/fixtures/ipo-universe-source-contract.json`, the new `.github/workflows/audit-ipo-universe.yml`, and one added test step in the existing data-contract workflow. Existing issuer/date/status helpers are reused. The new workflow has **contents:read**, **no schedule**, and runs manually or on relevant PR/main changes. Existing collection schedules and permissions were not expanded.

### Canonical post-merge result

Audit run **`36095239145`** collected sources from `2026-09-25T04:38:21.481Z` through `2026-09-25T04:38:31.107Z`; report generated `2026-09-25T04:38:31.258Z`.

| Metric | Result |
| --- | ---: |
| Published/recovery baseline | 1,218 records |
| Official source surfaces collected | 8 |
| Usable source adapters | 7 |
| Accepted source observations | 1,283 |
| Normalized issuer-name groups | 1,232 |
| Already-present groups | 970 |
| Exact-name-unmatched candidate groups | 224 |
| Identity-review groups | 38 |
| Field-conflict groups in this observation | 0 |
| IPO records imported | 0 |

**The 224 unmatched groups are not 224 certified missing IPOs.** They require offering-type, legal-name/alias, exchange-identifier and issuer-specific source review. The 38 identity-review groups include truncated names, identifier disagreements and source-name ambiguity. No fuzzy merge or automatic import is allowed.

The audit did not observe matches for 245 baseline records in these bounded source windows. This does **not** mean those records should be removed, delisted, marked withdrawn or considered invalid. Fabino's separate retained hold remains present even though it was not observed in these source windows.

### Source coverage and unresolved gaps

| Source surface | Raw rows | Accepted observations | Limitation |
| --- | ---: | ---: | --- |
| NSE past public issues | 1,452 | 1,035 | No independently established full-history total; 206 other-series rows need scope review, 206 dated rows are outside 2020-2026, and 5 explicitly non-IPO offers were excluded. |
| NSE current issues | 15 | 15 | Current issues only. |
| NSE upcoming issues | 13 | 13 | Upcoming only; future dates do not mean listed. |
| BSE issue summary | 0 | 0 | HTTP 200 HTML shell without issuer rows; marked unusable, not successful empty coverage. |
| BSE SME IPO index | 160 | 160 | Index membership, not all historical IPOs; business as-of is August 31, 2026, separate from collection time. |
| SEBI draft documents | 25 | 15 | Only rows 1-25 of 2,211 site filing rows; supplemental/ambiguous rows separately recorded. |
| SEBI RHP documents | 25 | 20 | Only rows 1-25 of 1,282 site filing rows. |
| SEBI final documents | 25 | 25 | Only rows 1-25 of 1,567 site filing rows. |

SEBI totals count site filings, not distinct in-scope IPOs. Draft/RHP/final filing stages never imply a listed/completed/withdrawn outcome. Unclassified NSE series remain visible coverage gaps, not certified non-IPO exclusions. Index dates, transport response dates, filing publication dates and collection clocks remain separate.

### Evidence and tests

PR head `dc5c0e958b14af3f5bc1681a0b89ec7be23f9874` passed audit run `36094915220`, data-contract run `36094914761`, and reviewed-evidence run `36094914786`. Tested local and committed whole-tree SHA both equal `8faca78a0599febef3e72b9ace0b44ecdecbddf4`.

The audit tests cover exact and conflicting identity, duplicate/asymmetric records, generic-source URL rejection, malformed/unavailable responses, deceptive hosts, invalid/future dates, filing-stage separation, truncated index names, pagination gaps, hash mismatches, source failure and read-only deterministic operation. Six retained real-source fixtures cover NSE, BSE and SEBI response shapes. Existing historical-coverage, NSE/SEBI parser, live-verifier, synchronized-build and data validation checks also passed locally.

Both PR and post-merge artifact ZIPs were downloaded and hash-checked. All **8 original response hashes** and **9 baseline input hashes** were independently checked per run. Full and compact reports were reproduced exactly using captured clocks. The main audit's clean-worktree guard passed; post-merge validation runs `36095239164` and `36095239260` passed. Pages deployment `36095239216` succeeded.

Canonical artifact: **`10846749143`**, ZIP SHA-256 `14521267a7d9d11f197248c3a7d4fca7fcf2e7257f63544a45677f1e1edf0c8c`, expires **2026-10-09 04:38:37 UTC**. It contains `sources.json`, original response bytes, `audit.json`, `audit-compact.json`, and an exact source archive. Full report SHA-256: `ce56c4763f72b1cd452f90a60b0dbb1e42c8ede1052dd7526bbc967b84114bc7`.

Durable summary, source hashes, clocks and run receipt: [verification/ipo-universe-audit-2026-09-25.json](verification/ipo-universe-audit-2026-09-25.json). The full source and all-candidate reports are in the expiring artifact; the next 15-row review batch is committed separately. Re-run the audit for later observations rather than presenting this snapshot as current indefinitely.

### Actual served data stayed unchanged

The existing read-only batch36 Pages verifier was rerun as **`36093076719`, attempt 2**, using its existing code revision. It fetched the actual public dataset at `2026-09-25T04:39:09.873Z`, checked at `04:39:09.909Z`, and passed its 10-issuer / 30-field checks with no failures.

The full fetched dataset was independently compared with the audit baseline: **1,218 records, byte-identical, 0 additions, 0 removals, 0 changed records**. SHA-256 remains `9a5ced8e0831bf07961c4fb3593f24d99008688f6874b2b86649c1d449841945`; 6,480,099 bytes. This is not a claim that every field of every baseline IPO has been individually reverified.

Live-check artifact `10847411232`, ZIP SHA-256 `dfdc5a06aafa08b286c2226ee7875f1dd5c609fe87c6baf99c496a99b14b29ef`.

## Exact next backend task

**Review the pinned first 15 NSE 2026 candidates in [../data/discovery/ipo-universe-review-2026-09-25-batch1.json](../data/discovery/ipo-universe-review-2026-09-25-batch1.json).** The audit found 119 exact-name-unmatched groups with a 2026 explicit NSE listing-date observation; the queue selects the earliest 15 by listing date, then symbol. It starts at `E2ERAIL` and ends at `FRACTAL`.

Re-read current main and reconcile each candidate against all seven recovery years and public data. Independently establish whether the observed security belongs to an IPO, FPO, rights issue, partly-paid/repeat security or another offer type. A public-issues feed is not necessarily IPO-only; **no candidate, including `ADANIENPP1`, has approved IPO status solely from this queue**. Resolve issuer aliases and identifiers using issuer-specific official evidence. Preserve unknowns and conflicts. Only then materialize unambiguous verified IPOs, rehearse preservation/idempotency, publish through the normal source-backed workflow and verify actual Pages output. Do not bulk-import the 224 unmatched groups or blindly extend the historical materializer.

Continue the BSE summary-source adapter and SEBI historical pagination coverage as separate bounded work after this initial review batch. The new audit is a repeatable baseline, not completion of P1 universe coverage.

**Fabino Life Sciences Limited remains held:** BSE `543444`, notice `20220112-10`, index/candidate listing date `2022-01-13` versus issuer-notice text `2021-01-13`. No inferred correction or publication. BSE parser v1.5 and its **236/236 parsed** cursor remain complete and unchanged; do not replay those notices.

## Earlier work and unsuccessful approaches

Initial collection-only audit `36093963252` had a slightly different SEBI page window and 223 unmatched groups; the final tested PR and canonical main run both have 224. Retain clocks and hashes rather than silently treating page drift as a parser change. The BSE summary source returned a shell, so broad page-title/token matching was deliberately not promoted to issuer evidence. Other-series rows and ambiguous filing titles were not silently declared out of scope. No unsupported issuer or term values were imported.

Prior status and README are archived unchanged in [archive/PROJECT_STATUS-before-official-universe-audit.md](archive/PROJECT_STATUS-before-official-universe-audit.md) and [archive/README-before-official-universe-audit.md](archive/README-before-official-universe-audit.md). Earlier archives/receipts remain intact. UI V2 remains separate under [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md). No UI, minimum-investment expansion, spending, accounts, ads, billing or permission changes belong to this continuation.
