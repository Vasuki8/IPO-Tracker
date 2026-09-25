# Project status and handoff

The separately requested IPO detail-page UI and future source-backed business/financial/risk-data requirements remain documented in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md). The P1 backend continuation below remains the active data workstream.

Updated: **2026-09-25**, after batch4 live verifier run `36167470675`.

## Current priority

Continue **P1 issuer identity and IPO-universe coverage** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The application-term requirement remains **Lot Size only**; keep market lot, minimum bid quantity and minimum application amount distinct. No UI or downstream commercial-feature work belongs to this continuation.

**NSE universe batch4 is VERIFIED LIVE.** Do not repeat its review/import. The exact next P1 task is the pinned batch5 queue, after reconciling against latest main and the verified **1,269-record** Pages snapshot.

## VERIFIED: NSE universe batch4 — PR #240

Reviewed 15 pinned RFBL-to-SHREEDHAR candidates. **13 initial public equity IPOs were independently verified and published; 1 migration and 1 debt security were excluded.**

Approved symbols: **RFBL, NFPSAMPOOR, TEAMTECH, BMLL, QLINE, CMRGREEN, GENXAI, UTKAL, CLAYCRAFT, AVIENCE, TURTLEMINT, CORDELIA, SHREEDHAR**.

Excluded:
- **QMSMEDI** — official NSE migration approval states that QMS Medical Allied Services moved from NSE Emerge SME to the Main Board effective **2026-06-18**. The canonical past-issues row retains the original 2022 offer period. This is a migration event, not a new IPO.
- **12VPT28A** — NSE ipo-detail reports `isDebtSec=true`, ISIN `INE0MEG07011`; NSE circular CML74788 independently identifies Viviana Power Tech security VPT28A as debt with a **12% coupon**. The aggregate row carries the issuer's 2022 equity-offer dates and must not be reinterpreted as a 2026 equity IPO.

The retained manifest contains **78 explicit source-backed facts**: 13 listing dates, 26 offer dates, 13 final issue prices, 13 price bands, 10 market lots and 3 minimum bid quantities. No minimum application amount or unsupported optional field was inferred.

Evidence:
- [../data/verified-nse-ipos/2026-09-25-batch4.json](../data/verified-nse-ipos/2026-09-25-batch4.json)
- [../data/discovery/nse-universe-batch4-review-2026-09-25.json](../data/discovery/nse-universe-batch4-review-2026-09-25.json)
- [verification/nse-universe-batch4-rehearsal-2026-09-25.json](verification/nse-universe-batch4-rehearsal-2026-09-25.json)
- [verification/nse-universe-batch4-live-publication-2026-09-25.json](verification/nse-universe-batch4-live-publication-2026-09-25.json)

### Source provenance and independent classification

Read-only source run `36165195790`; artifact `10877286718`; artifact SHA-256 `7aa33f4f7066e20a246a5da8328e8271759b4f2b2356b6ae4eed6cdec93185ad`; source snapshot `fd4e9da69a8e4a88967612b2b4ebee661f1532cd`.

All **20 original source files** revalidated against retained byte counts and hashes, including all 15 issuer-specific NSE responses, the canonical NSE past-issues response, the actual 1,256-record Pages baseline, the QMS migration approval and the Viviana debt circular.

### Narrow parser repairs

Three literal official-source forms required bounded support:
- **Initial Public Issue**
- observed NSE typo **Intial Public Offer**
- price range such as **Rs. 144 to 152 per Equity Shares**

The offer parser still requires equity shares and rejects FPO/further-public/rights/partly-paid/debenture/non-convertible forms. The price-band parser still requires INR evidence on the lower bound; a band with no leading currency marker fails closed.

### Rehearsal, tests and merge

Successful retained-source materialization run `36166287987`; artifact `10878100711`; artifact SHA-256 `80bdf98cbdd5aad9133294b8227ddba01784021eb2eed8cb1a6c6be31327d0a6`; reviewed commit `5679d346f4aaa1d84b075732c13bddd60c76c5ee`.

Isolated rehearsal: **1,256 -> 1,269**, exactly 13 additions, 0 removals, all 1,256 prior records preserved, and an idempotent rerun. All four reviewed NSE batches pass rehearsal checks: **51 issuers / 305 facts**.

Two temporary materialization attempts (`36166095008`, `36166189950`) failed only in the workflow's parser-patch guard before any reviewed data write. The third run used the same retained source artifact and passed. Both one-off collection/materialization workflows were removed before merge.

Final-head CI on the cleaned 9-file PR diff:
- full data contract `36166573363` — success
- reviewed-BSE compatibility `36166573350` — success

PR #240 merged as **`927782ac7dd9ed7752fc6def8e5fb0025fae8f0b`**.

## VERIFIED: normal source-backed publication and actual Pages output

Normal source sync **`36166656023`** completed successfully end-to-end. The earlier historical-NSE timeout did **not** recur.

All measured stages were successful:
- NSE collection
- 2020-2025 historical NSE materialization
- reviewed BSE and reviewed NSE imports
- SEBI document attachment
- bounded NSE all-fields enrichment
- dataset rebuild
- data validation
- semantic publication
- operator state publication

Data commit: **`35166cf76ee03fb580d53e75898b030f7cc1f9c6`**.  
Operator commit: **`4419dbd5e5c378a1f5cf555c949d8f868a508228`**.  
Operator health after the run: **healthy**, with no recovery reasons.

Batch4 post-publication verifier **`36167470675`** succeeded. Retained verifier artifact `10878475153`; SHA-256 `300af4538b2b65835c5644a6156193b596be95dea38d92b5eaa60a3ecd9030ad`.

The verifier fetched the real Pages dataset at **2026-09-25T17:30:44.748Z** and checked it at **17:30:44.828Z**.

| Check | Result |
| --- | ---: |
| Live records | **1,269** |
| Batch4 issuers | **13 / 13 unique** |
| Batch4 facts | **78 / 78 matching** |
| Failed issuers | **0** |
| Added records vs batch3 baseline | **13** |
| Removed records | **0** |
| Invalid / Unknown statuses | **0** |
| Records missing status evidence | **0** |
| Snapshot bytes | **6,841,294** |
| Snapshot SHA-256 | `228b3a1861836dbce8e344313a82035d9e7ed38bcd2a09c31f4dcd822047c6b5` |

Dataset `generated_at`: **2026-09-25T17:23:10.833Z**.

Live status distribution: **listed 1,248 / open 16 / closed 3 / upcoming 2 / Unknown 0**.

### Exact baseline delta

Compared with the independently verified 1,256-record batch3 snapshot:
- **13 approved batch4 records added**
- **0 records removed**
- **2 existing records changed only through normal SEBI document enrichment**
- **0 prior displayed IPO values/statuses changed**

The two ordinary-sync enrichments were:
- **Euro Pratik Sales Limited** — SEBI Prospectus + RHP filing/PDF documents attached; only `documents` and `last_collected_at` changed.
- **Ivalue Infosolutions Limited** — SEBI Prospectus + RHP filing/PDF documents attached; only `documents` and `last_collected_at` changed.

This ordinary sync enrichment is separate from the batch4 13-record reviewed import.

## Exact next P1 backend task — batch5

Review [../data/discovery/ipo-universe-review-2026-09-25-batch5.json](../data/discovery/ipo-universe-review-2026-09-25-batch5.json): **15 candidates from TEJA through JNPR**.

Pinned symbols:
**TEJA, VMOBILE, KNACK, ICELCO, KUSUMGAR, HAPPY, LASERPOWER, SBIFUNDS, CMLL, METALIC, INDOMIM, LCL, PROPSHOP, MANIPALHOS, JNPR**.

The queue is derived from canonical audit `36095239145`, excluding all 60 prior-batch source symbols and ordered by listing date then NSE symbol. **59 eligible source groups remain after batch4; this is not a count of confirmed IPOs.**

Before action:
1. Reconcile each candidate against latest main and the actual verified 1,269-record Pages universe.
2. Independently establish initial equity IPO versus FPO, rights, migration, repeat/partly-paid security, debt or another offer type using issuer-specific official evidence.
3. Resolve legal-name aliases, symbol/ISIN/board identity and prior-offer history.
4. Preserve nulls and conflicts; never infer prices, dates, quantities, issue size or application amount.
5. Do not import from aggregate past-issues evidence alone.
6. Rehearse preservation/idempotency, merge only reviewed unambiguous IPOs, use normal source-backed publication, and verify actual Pages output afterward.

## Remaining holds and broader gaps

Unresolved holds from prior batches:
- **AMIRCHAND** — missing issuer identity metadata
- **ADANIENPP1** — offering type not established
- **Fabino Life Sciences** — listing-year conflict
- **GICL, SILGOPP, VITAL, KOTYARK** — older-offer / migration / repeat-security conflicts

Batch4 exclusions **QMSMEDI** and **12VPT28A** are resolved non-IPO classifications, not holds, and must not be recycled into the equity IPO queue.

Broader coverage gaps remain: BSE issue-summary adapter, SEBI historical pagination and unresolved NSE series. Do not claim complete IPO-universe coverage.

BSE parser v1.5 remains **236/236 parsed**; do not replay that cursor.

## Preserved history and scope

The immediately preceding batch3-complete/batch4-pending handoff is archived byte-for-byte in:
- [archive/PROJECT_STATUS-before-nse-batch4-live-verification.md](archive/PROJECT_STATUS-before-nse-batch4-live-verification.md)
- [archive/README-before-nse-batch4-live-verification.md](archive/README-before-nse-batch4-live-verification.md)

Earlier archives and receipts remain intact. UI/research-depth work stays separate under [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md).

No UI, minimum-investment expansion, billing, accounts, ads, spending or permission changes belong to this continuation.
