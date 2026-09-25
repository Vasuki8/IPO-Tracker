# Project status and handoff

Updated: **2026-09-25**, 05:49 UTC / 01:49 America/Toronto verification window.

## Current priority

Continue **P1 issuer identity and IPO-universe coverage** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The active application-term requirement remains **Lot Size only**. Preserve market lot, minimum bid quantity and minimum application amount as distinct fields. No UI or downstream commercial-feature work belongs to this continuation.

## VERIFIED: NSE official-universe review batch 1 — PR #230

PR #230 merged as `60e2ab2360d6782be5952e31cd0253a504b9baa1`. It reviewed the 15 pinned NSE 2026 candidates from the first official-universe audit batch rather than bulk-importing unmatched names.

Issuer-specific source capture run `36096308787`, artifact `10847442489`, ZIP SHA-256 `e00e9d7b3665c6f94e1994858e0fed05de6ac67b7bc6465ea7699fdf0e670e96`, exact source snapshot `cd03b3a9c7ac76518696bcc71877fd88881e96cf`.

### Review result

- **15 candidates reviewed**
- **14 independently verified initial public equity offerings**
- **1 held security: ADANIENPP1**
- **0 approved identity collisions**
- **83 explicit facts retained**
  - 14 listing dates
  - 28 offer/open-close dates
  - 14 scalar final issue prices
  - 13 price bands
  - 9 market lots
  - 5 minimum bid quantities

All 15 issuer-detail endpoints returned HTTP 200. All 15 quote-identity endpoints returned HTTP 403 and were **not** used or bypassed. For every approved issuer, NSE Issue Information explicitly described an initial public equity offer and aligned legal name, symbol, ISIN, board/segment, issue period and listing date with the past-issues observation. Final prices from the past feed were accepted only after that IPO/identity gate.

No issue-size amount, minimum application amount, or unsupported field was derived. Victory Electric Vehicles' fixed price of 41 remains a scalar issue price, not an invented price band. E2ERAIL correctly retains its December 2025 offer period with January 2026 listing.

Review receipt: `data/discovery/nse-universe-batch1-review-2026-09-25.json`. Reviewed evidence: `data/verified-nse-ipos/2026-09-25-batch1.json`.

### Held: ADANIENPP1

**Adani Enterprises Limited / ADANIENPP1 remains held.** Its detail response exposes company/symbol/ISIN/listing metadata but no issuer-specific Issue Size / Issue Period / explicit initial-public-equity-offer statement. The past feed contains three observations for the same security with different offer periods in 2024, 2025 and 2026. Symbol/series/listing metadata alone cannot establish IPO versus another offer/security type. No classification is inferred.

Fabino Life Sciences remains separately held for its 2021-versus-2022 official listing-year conflict.

### Import safety and rehearsal

The new reviewed-NSE importer validates evidence before writes and rejects cross-year legal-name, symbol, ISIN and source-identity collisions. It is invoked inside the existing semantic source-backed publication loop; no existing schedule or permission was expanded.

Exact rehearsal: **1,218 -> 1,232**, exactly **14 additions**, all **1,218 previous records unchanged**, zero identity conflicts, and a byte-idempotent rerun.

PR-head data-contract run `36098474997` and reviewed-evidence run `36098474991` passed.

## VERIFIED: production publication and actual Pages output

Production source-backed sync `36098558475` succeeded. Generated-data commit: `77c74d759d9833aaf3147d757ae9b7f8e30c1e1f`. Operator-state commit: `63370ecbd7e5e49a86f8c690f5da62cb65548ce6`; operator snapshot at `2026-09-25T05:33:22.126Z` is **healthy**.

The current recovery/public baseline is **1,232 records**:
2020 **65**, 2021 **120**, 2022 **136**, 2023 **216**, 2024 **301**, 2025 **293**, 2026 **101**.

Read-only publication workflow `36099067573` attempt 2 verified the actually served Pages dataset:

| Check | Result |
| --- | ---: |
| Actually served records | 1,232 |
| Reviewed issuers | 14 / 14 unique |
| Reviewed facts | 83 / 83 matching |
| Failed issuers | 0 |
| Snapshot bytes | 6,577,125 |
| Snapshot SHA-256 | `3fe550decca530638e0b354381827b5142c611fff89329c68562f1488e754f5c` |

Snapshot fetched `2026-09-25T05:44:14.484Z`; checked `05:44:14.568Z`; dataset generated `05:32:16.102Z`. Successful artifact `10848497149`, ZIP SHA-256 `6f6e06dfa46e537267c7001a2c4ac873a8da3ee4e386abc759be2d4f7074ba33`.

Compared with the prior verified 1,218-record Pages snapshot: **14 added, 0 removed, 7 existing records changed**. The 14 additions are exactly the reviewed batch. The seven existing changes came from independent scheduled/source enrichment in the same publication window (SEBI documents/collection clocks and verified historical offer dates), not from the reviewed-NSE importer. No existing record was removed.

## VERIFIED: Pages propagation reliability — PR #231

The first verifier attempt ended before GitHub Pages finished propagating and therefore still saw the old 1,218-record snapshot. It was a timing failure, not an import/evidence failure. The same verifier rerun after Pages settled passed immediately.

PR #231 merged as `c170c420774705c86c16f16cb7faf1980cbc86de` and only extends the bounded wait from five 15-second attempts to fourteen 30-second attempts, with a 10-minute job timeout. Verification logic, source-backed publication, schedules and permissions are unchanged.

PR-head validation runs `36100044374` and `36100044439` passed. Post-merge data-contract `36100106748`, reviewed-evidence `36100106765`, and Pages deployment `36100106805` passed.

Durable receipt: [verification/nse-universe-batch1-live-publication-2026-09-25.json](verification/nse-universe-batch1-live-publication-2026-09-25.json).

## Exact next backend task

Review the pinned second 15-candidate queue in [../data/discovery/ipo-universe-review-2026-09-25-batch2.json](../data/discovery/ipo-universe-review-2026-09-25-batch2.json), derived deterministically from canonical audit `36095239145` after excluding all batch1 symbols.

The batch starts at **GICL** and ends at **SPCON**. It deliberately contains review-risk signals such as **SILGOPP** and issuers with older listing histories. Reconcile every candidate against the latest 1,232-record universe and all recovery years. Independently determine IPO versus FPO, rights issue, partly-paid/repeat security or another offer type using issuer-specific official evidence. Resolve aliases and identifiers. Preserve unknowns/conflicts and only materialize unambiguous verified IPOs.

The source-audit snapshot still has broader coverage gaps: BSE issue-summary adapter, SEBI historical pagination and unclassified NSE series remain separate bounded tasks. Do not claim full IPO-universe completeness.

**Held conflicts remain:** ADANIENPP1 offering type unresolved; Fabino Life Sciences listing year unresolved. Do not infer either.

BSE parser v1.5 remains complete at **236/236 parsed**; do not replay that cursor.

## Preserved history

The preceding status/README are archived byte-for-byte in [archive/PROJECT_STATUS-before-nse-universe-batch1.md](archive/PROJECT_STATUS-before-nse-universe-batch1.md) and [archive/README-before-nse-universe-batch1.md](archive/README-before-nse-universe-batch1.md). Earlier archives and receipts remain intact. UI V2 remains separate under [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md).

No UI, minimum-investment expansion, billing, accounts, ads, spending or permission changes belong to this continuation.
