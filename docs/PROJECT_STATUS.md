# Project status and handoff

Updated: **2026-09-25**, after live verification run `36157133065`.

## Current priority

Continue **P1 issuer identity and IPO-universe coverage** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The active application-term requirement remains **Lot Size only**. Preserve market lot, minimum bid quantity and minimum application amount as distinct fields. No UI or downstream commercial-feature work belongs to this continuation.

## VERIFIED: Unknown IPO status repair — PR #232 / #234

A read-only audit found exactly **13 live records** rendered as `Status unavailable`. All 13 already had a **verified, past official NSE listing date**, empty status evidence, and a resolvable NSE identity. There were **0** unknown records with only offer dates and **0** with no dates.

Audit run `36101891389`, artifact `10849527986`, ZIP SHA-256 `57d3d6ae65a5eb00725432ca059a0a7095799a53701d6b9e8b9620c7a5dd96d4`.

PR #232 merged as `df5d2a6ae8cd14e640c29225acb578f2dee960a3`. The source-backed repair sets `status: listed` only when status is absent, status evidence is empty, the listing date is strict/verified/not future, its retained source is official NSE, and NSE identity resolves. The exact listing-date source is copied into `status_evidence`; no new source is invented and `last_collected_at` is not rewritten.

Production repair sync `36102715450`; generated-data commit `b6dab703052210070fd20248410c5e14ab8ff114`; operator-state commit `f980611435449220234cf0af82c15c6587d6ea83`.

PR #234 merged as `b62bd84a44cc3b901a4ca4735c315e878047d36d` and makes this a publication invariant: every public record must have one of `open/upcoming/closed/listed` plus retained status evidence.

**Current actual Pages status distribution:** listed **1,222**, open **16**, closed **3**, upcoming **2**, unknown **0**. Durable receipt: [verification/ipo-status-repair-2026-09-25.json](verification/ipo-status-repair-2026-09-25.json).

## VERIFIED: NSE official-universe review batch 2 — PR #233

Source run `36102861946`, artifact `10849678453`, ZIP SHA-256 `ca9c15994d67dea46c735b8a3cd555def34a3948463ab05b893615e94af2bdbd`, source snapshot `c5192aa36f15ebe37becd67c711fc890fc71aa75`.

### Review result

- **15 candidates reviewed**
- **11 independently verified 2026 initial public equity IPOs**
- **4 held legacy/migration/repeat-security cases**
- **66 explicit facts retained**: 11 listing dates, 22 offer dates, 11 final issue prices, 11 price bands, 7 market lots, 4 minimum bid quantities
- all 15 issuer-detail responses HTTP 200
- all 15 quote-identity responses HTTP 403 and unused
- all 31 retained source file hashes revalidated

**Published:** MARUSHIKA, MANILAM, CLEANMAX, MOBILISE, PNGSREVA, OMNI, YAAP, STRIDERS, ACETEC, SEDEMAC, SPCON.

**Held:** GICL, SILGOPP, VITAL, KOTYARK. GICL/SILGOPP have old 2016/2018 offer observations and no current issue-specific IPO terms; VITAL retains its 2022 IPO period with 2026 listing metadata and conflicting price evidence; KOTYARK retains its 2021 IPO at Rs.51 while the 2026 past row reports 281. None is inferred to be a new 2026 IPO.

The reviewed-period parser was narrowly extended to accept explicit full month names such as `26-February-2026 to 02-March-2026`; invalid month names still fail closed.

Exact isolated rehearsal: **1,232 -> 1,243**, exactly **11 additions**, all **1,232 existing records unchanged**, 0 removals/identity conflicts, idempotent rerun. Materialization run `36156144008` passed source-hash checks, evidence validation, rehearsal, build synchronization and data validation.

PR #233 merged as `1bac6fda9c05214383353741077cb517869b2ec5`.

## VERIFIED: batch-2 production and actual Pages output

Production source-backed sync `36156433535` succeeded. Generated-data commit `06253c537f7ff08dc4ef0fea325647a2ea0ec036`; operator-state commit `2850090ae29534b709be9fe47f9d577bad56abe6`; operator health is **healthy**.

Read-only Pages verifier `36157133065` passed:

| Check | Result |
| --- | ---: |
| Actually served records | 1,243 |
| Batch-2 issuers | 11 / 11 unique |
| Reviewed facts | 66 / 66 matching |
| Failed issuers | 0 |
| Unknown statuses | 0 |
| Snapshot bytes | 6,671,524 |
| Snapshot SHA-256 | `f349cc612501e4fb16b7616aadf902ae282b4541ae92e84df672299cf4703a54` |

Snapshot fetched `2026-09-25T15:53:38.128Z`; checked `15:53:38.204Z`; dataset generated `15:47:43.475Z`. Artifact `10873708367`, ZIP SHA-256 `10970bc95d0725f4d7cda64d29944bc66dc569b4044ec71e604f7764ef83b085`. Pages deployment `36157126001` succeeded.

Compared with the preceding verified 1,232-record snapshot: **11 added, 0 removed, 4 existing records changed through unrelated scheduled/source enrichment**. No existing record was removed.

Durable receipt: [verification/nse-universe-batch2-live-publication-2026-09-25.json](verification/nse-universe-batch2-live-publication-2026-09-25.json).

## Remaining holds

- **ADANIENPP1 / Adani Enterprises Limited:** offering type remains unverified; do not infer IPO status.
- **Fabino Life Sciences Limited:** official listing-year conflict remains unresolved.
- **GICL, SILGOPP, VITAL, KOTYARK:** retained as batch-2 legacy/migration/repeat-security holds, not new 2026 IPOs.

## Exact next backend task

Review the pinned 15-candidate queue in [../data/discovery/ipo-universe-review-2026-09-25-batch3.json](../data/discovery/ipo-universe-review-2026-09-25-batch3.json), derived deterministically from canonical audit `36095239145` after excluding all batch1/batch2 symbols.

Batch 3 starts at **APSISAERO** and ends at **SIMCA**. Reconcile against the latest 1,243-record universe before action. Independently establish IPO versus FPO/rights/partly-paid/repeat/migration security using issuer-specific official evidence; preserve aliases, nulls and conflicts; publish only independently verified unambiguous IPOs with rehearsal, source-backed sync and actual Pages verification.

The canonical audit still has broader gaps: BSE issue-summary adapter, SEBI historical pagination and unresolved NSE series. Do not claim full IPO-universe completeness.

BSE parser v1.5 remains **236/236 parsed**; do not replay that cursor.

## Preserved history

The preceding handoff is archived byte-for-byte in [archive/PROJECT_STATUS-before-status-and-nse-batch2.md](archive/PROJECT_STATUS-before-status-and-nse-batch2.md) and [archive/README-before-status-and-nse-batch2.md](archive/README-before-status-and-nse-batch2.md). Earlier archives and receipts remain intact. UI V2 remains separate under [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md).

No UI, minimum-investment expansion, billing, accounts, ads, spending or permission changes belong to this continuation.
