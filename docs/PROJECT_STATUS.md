# Project status and handoff

The separately requested IPO detail-page UI batch is documented in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md). The P1 backend continuation below remains the data workstream handoff.

Updated: **2026-09-25**, after live batch3 verification run `36163697372`.

## Current priority

Continue **P1 issuer identity and IPO-universe coverage** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The application-term requirement remains **Lot Size only**; keep market lot, minimum bid quantity and minimum application amount distinct. No UI or downstream commercial-feature work belongs to this continuation.

**NSE universe batch3 is now VERIFIED LIVE.** Do not repeat its review/import. The next P1 queue is batch4, after reconciling against latest main and the verified 1,256-record live snapshot.

## VERIFIED: NSE universe batch3 — PR #235

Reviewed 15 pinned APSISAERO-to-SIMCA candidates. **13 initial public equity IPOs were independently verified and published; 1 remains held for identity; 1 was excluded as debt.**

Published: **APSISAERO, RSL, INNOVISION, GSPCROP, CMPDI, POWERICA, SAIPARENT, VIVIDEL, ADISOFT, AMBAAUTO, KISSHT, VALUE360, SIMCA**.

Held: **AMIRCHAND**. Its issuer-specific response contains IPO terms, but legal-name / ISIN / board / listing identity metadata is absent. Do not fabricate those identity fields from the aggregate past-issues feed.

Excluded: **10MWL29**. NSE reports `isDebtSec=true`, ISIN `INE0JYY07026`; the issuer disclosure independently identifies it as a debt symbol and distinguishes equity symbol MWL / ISIN `INE0JYY01011`. It must not re-enter the equity-IPO queue.

The retained batch contains **78 explicit source-backed facts**: 13 listing dates, 26 offer dates, 13 final issue prices, 13 price bands, 6 market lots and 7 minimum bid quantities. No minimum application amount or unsupported optional field was inferred.

Evidence:
- [../data/verified-nse-ipos/2026-09-25-batch3.json](../data/verified-nse-ipos/2026-09-25-batch3.json)
- [../data/discovery/nse-universe-batch3-review-2026-09-25.json](../data/discovery/nse-universe-batch3-review-2026-09-25.json)
- [verification/nse-universe-batch3-live-publication-2026-09-25.json](verification/nse-universe-batch3-live-publication-2026-09-25.json)

### Source provenance and review

Source run `36158694311`; artifact `10875066031`; ZIP SHA-256 `24faa41a1bee5e50eafdcebd8404ec97de79e23149777f1c08f9863d2168e78a`; exact source snapshot `1997f423d49050a576171b4867a7fa71c0015097`. All **18 original source-file hashes** were revalidated.

PR #235 merged as `2927fe2ed273db9c8a1fe72b3b21543a19003872`. Its importer repair accepts explicit **Revised/Extended Issue Period** only when both date representations and the independent past-source dates agree, accepts **Revised Price Range** while retaining the literal evidence title/value, and ignores only an apostrophe inside a word for issuer-name comparison. Symbol, ISIN, board, offering type, listing identity and cross-year collision gates remain mandatory.

Isolated rehearsal: **1,243 -> 1,256**, exactly 13 additions, 0 removals, all 1,243 existing records unchanged, idempotent rerun. All three reviewed NSE batches pass rehearsal checks: **38 issuers / 227 facts**.

## VERIFIED: actual Pages publication

The original production sync `36160239429` applied reviewed evidence but became abnormally long-running in optional NSE all-fields enrichment. It was eventually cancelled by workflow concurrency.

PR #236 fixed that operational failure mode by bounding optional `--all-fields` enrichment to an **8-minute best-effort budget**. Deferred enrichment stays null/missing and is retried by later scheduled syncs; no field is guessed. PR #236 merged as `50fbd2ef2ed4176515607c35e787dfbd0d21f31f`. CI passed in data-contract run `36163365949` and reviewed-BSE run `36163365958`.

Replacement normal sync `36163462983` then failed earlier, in **Materialize 2020-2025 NSE historical IPO universes**, because an official NSE historical request hit a `DOMException [TimeoutError]`. That run never reached reviewed-NSE import/publication; its operator snapshot correctly recorded health as unknown.

To avoid coupling the already-reviewed batch3 release to unrelated network enrichment, a one-time bounded repair workflow used the existing reviewed importer, public-data builder, validator and read-only Pages verifier only. It performed no unrelated network enrichment and preserved missing values as null.

- Repair workflow run: **`36163697372` — success**
- Repair job: `108166179765`
- Data publication commit: **`d24291331f15e7f346977790e77b02c2c528c230`**
- Repair artifact: `10876409156`, SHA-256 `5df767d48bf49a4c06c7e22ff5cb132451e9907f06840be556c3454a2419d2fe`
- Actual Pages deployment for the data commit: `36163746445` — success
- Temporary repair workflow retired in commit `3491f0c4385f7bab2e6e9f718887bc5fb699cf71`

### Actual live snapshot

The retained verifier fetched the real Pages dataset at **2026-09-25T16:55:27.249Z** and checked it at **16:55:27.334Z**.

| Check | Result |
| --- | ---: |
| Live records | **1,256** |
| Batch3 issuers | **13 / 13 unique** |
| Batch3 facts | **78 / 78 matching** |
| Failed issuers | **0** |
| Existing baseline records changed | **0 / 1,243** |
| Removed records | **0** |
| Added records | **13** |
| Invalid / Unknown statuses | **0** |
| Records missing status evidence | **0** |
| Snapshot bytes | **6,753,982** |
| Snapshot SHA-256 | `74031fbbac15e9fff5b6e510a23df45c435e2eecf1c9257b064cc9c42ecf3932` |

Dataset `generated_at`: **2026-09-25T16:08:35.285Z**.

Live status distribution: **listed 1,235 / open 16 / closed 3 / upcoming 2 / Unknown 0**.

Compared byte-for-record against the previously retained 1,243-record Pages snapshot: **13 added, 0 removed, 0 existing records changed**.

Durable receipt: [verification/nse-universe-batch3-live-publication-2026-09-25.json](verification/nse-universe-batch3-live-publication-2026-09-25.json).

## Operational follow-up

The batch3 release is complete even though normal sync run `36163462983` hit a separate historical NSE timeout. At the start of the next backend run, inspect the latest scheduled `Sync live IPO data` result. If the same historical-materialization timeout repeats, repair that source fetch with bounded retry/fail-closed behavior before relying on the hourly pipeline for new publication. Do not weaken evidence requirements to make the workflow pass.

PR #236's all-fields budget remains a permanent reliability guard: optional enrichment can no longer hold a normal release indefinitely.

## Exact next P1 backend task

Review [../data/discovery/ipo-universe-review-2026-09-25-batch4.json](../data/discovery/ipo-universe-review-2026-09-25-batch4.json): **15 candidates from RFBL through SHREEDHAR**.

Before action:
1. Reconcile the queue against latest main and the actual verified Pages universe.
2. Independently establish IPO versus FPO, rights, partly-paid/repeat security, migration/listing transfer, debt or another offering type using issuer-specific official evidence.
3. Preserve legal-name aliases, source identities, nulls and conflicts.
4. Do not import from the aggregate NSE past-issues row alone.
5. Rehearse preservation/idempotency before publication and verify actual Pages output afterward.

Specific review signals:
- **QMSMEDI** — resolve any older offer/migration history before treating 2026 as a new IPO.
- **12VPT28A** — unusual security symbol; independently establish equity versus debt/repeat security.

The canonical audit has **74 remaining eligible source groups**, not 74 confirmed IPOs.

## Remaining holds and broader gaps

Unresolved holds:
- **AMIRCHAND** — missing issuer identity metadata
- **ADANIENPP1** — offering type not established
- **Fabino Life Sciences** — listing-year conflict
- **GICL, SILGOPP, VITAL, KOTYARK** — older-offer / migration / repeat-security conflicts

Broader coverage gaps remain: BSE issue-summary adapter, SEBI historical pagination and unresolved NSE series. Do not claim full IPO-universe completeness.

BSE parser v1.5 remains **236/236 parsed**; do not replay that cursor.

## Preserved history and scope

The immediately preceding pending-release handoff is archived byte-for-byte in:
- [archive/PROJECT_STATUS-before-nse-batch3-live-verification.md](archive/PROJECT_STATUS-before-nse-batch3-live-verification.md)
- [archive/README-before-nse-batch3-live-verification.md](archive/README-before-nse-batch3-live-verification.md)

Earlier archives and receipts remain intact. The concurrent IPO detail-page UI work remains separate under [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md) and was not modified by this backend release.

No UI, minimum-investment expansion, billing, accounts, ads, spending or permission changes belong to this continuation.
