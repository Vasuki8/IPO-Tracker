# Project status and handoff

Updated: **2026-09-25**, recorded `2026-09-25T16:35:52Z`.

## Current priority and release state

Continue **P1 issuer identity and IPO-universe coverage** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The application-term requirement remains **Lot Size only**; keep market lot, minimum bid quantity and minimum application amount distinct. No UI or downstream commercial-feature work belongs to this continuation.

**Batch3: MERGED AND TESTED; source-backed publication and actual Pages verification are not yet confirmed. The next action is to finish this release verification, not to repeat its review or start batch4.**

## Completed: NSE universe batch3 review and parser repair — PR #235

Reviewed 15 pinned APSISAERO-to-SIMCA candidates. **13 initial public equity IPOs approved; 1 identity hold; 1 debt security excluded.** Approved symbols: **APSISAERO, RSL, INNOVISION, GSPCROP, CMPDI, POWERICA, SAIPARENT, VIVIDEL, ADISOFT, AMBAAUTO, KISSHT, VALUE360, SIMCA**.

Retained **78 explicit source-backed facts**: 13 listing dates, 26 offer dates, 13 final issue prices, 13 price bands, 6 market lots and 7 minimum bid quantities. No inferred application amounts or optional facts. Evidence: [../data/verified-nse-ipos/2026-09-25-batch3.json](../data/verified-nse-ipos/2026-09-25-batch3.json); review: [../data/discovery/nse-universe-batch3-review-2026-09-25.json](../data/discovery/nse-universe-batch3-review-2026-09-25.json).

### Source provenance

Source run `36158694311`; artifact `10875066031`; ZIP SHA-256 `24faa41a1bee5e50eafdcebd8404ec97de79e23149777f1c08f9863d2168e78a`; exact source snapshot `1997f423d49050a576171b4867a7fa71c0015097`. All **18 original response file hashes** were revalidated, including all 15 issuer-detail responses. Literal selected JSON fields and source URL/date/hash identities remain in the manifest; the original Actions artifact has 14-day retention.

### Reusable parser fixes

The importer accepts **Revised/Extended Issue Period** only when both explicitly stated date representations and the independent past-source dates agree. It accepts **Revised Price Range**, retains the original source title/value in evidence and rejects competing ordinary/revised labels. Only an apostrophe inside a word is ignored for NSE issuer-name comparison; symbol, ISIN, board, offering type, listing identity and cross-year collision checks remain mandatory. This resolves Innovision's revised terms and Sai Parenterals' apostrophe variant without inferring other spelling changes.

**AMIRCHAND remains held:** IPO terms were observed, but the issuer-specific response lacked legal-name/ISIN/board/listing identity metadata. A future source-aware identity adapter must retain separate official evidence as its own source, not fabricate missing NSE metadata from the past feed.

**10MWL29 is excluded as debt:** NSE explicitly reports `isDebtSec=true`, ISIN `INE0JYY07026`. The issuer's 2026-05-16 disclosure independently labels it a debt symbol and distinguishes equity MWL/INE0JYY01011. Its misleading old-offer/new-debt-listing past row must not become an equity IPO.

### Tests, review and merge

Isolated publication rehearsal: **1,243 -> 1,256**, exactly 13 additions, zero removals, every prior record unchanged and an idempotent rerun. All three NSE batches pass rehearsal checks: **38 issuers / 227 facts** (83 + 66 + 78). The new suite rejects 17 malformed/held inputs and 3 cross-year apostrophe alias collisions; prior 34 negative-input and 4 cross-year collision tests still pass.

Final PR-head CI: data contract `36160049319` and reviewed BSE evidence `36160049332`, both successful at `a676a15f183f20409683ba8d0337a59b9a154865`. PR #235 merged as `2927fe2ed273db9c8a1fe72b3b21543a19003872`. The full data-contract suite passed again on merged main in `36160239490`.

Materialization run `36159865659` passed source validation, tests and rehearsal, but its bot push was rejected because it included a workflow-file edit without workflows permission. The tested commit/tree was read back and submitted through the already-authorized GitHub connector; no permissions changed. Both temporary workflows were removed before merge. Durable rehearsal receipt: [verification/nse-universe-batch3-rehearsal-2026-09-25.json](verification/nse-universe-batch3-rehearsal-2026-09-25.json). This historical bot-push failure is distinct from the pending production sync.

## Remaining release gate: production sync and actual Pages verification

Production sync **`36160239429`**, job **`108154724424`**, was still **in_progress** at handoff. The reviewed-NSE import step succeeded. The active step was **Extract NSE Issue Information fields in one pass**, started `2026-09-25T16:23:42Z`; source-backed publication had not yet completed. No failure conclusion was observed.

Do not claim 1,256 live records or batch3 deployment from the rehearsal or code merge. The latest main observed before this handoff was `b7c5defabb5f420d242ed898d58f48b340d165b4`, an earlier code-Pages health update, not a batch3 generated-data commit.

**Exact next actions:** inspect sync `36160239429` to completion, its generated-data/operator commits, the resulting Pages deployment, and the automatically triggered **Verify reviewed NSE IPO publication** workflow. Download its artifact with actual `deployed-data.json`, `report.json` and source snapshot. Verify 13 unique batch3 issuers / 78 facts; check global valid statuses with evidence and Unknown count; compare actual served records against the retained 1,243 baseline; record any ordinary-sync enrichment separately from the isolated import. Recheck all reviewed batches against the actual snapshot when practical. Retain the live publication receipt and update README/status before batch4. Do not recollect or reimport the completed batch solely because verification is pending.

Recorded release state: [verification/nse-universe-batch3-release-status-2026-09-25.json](verification/nse-universe-batch3-release-status-2026-09-25.json).

## Last independently verified live baseline — historical, not a new live claim

Batch2 verifier `36157133065` fetched `2026-09-25T15:53:38.128Z`: **1,243 records**, status distribution **listed 1,222 / open 16 / closed 3 / upcoming 2 / Unknown 0**. Snapshot SHA-256 `f349cc612501e4fb16b7616aadf902ae282b4541ae92e84df672299cf4703a54`; dataset generated `2026-09-25T15:47:43.475Z`.

The prior PR #232 status repair and PR #234 valid-status-plus-evidence publication invariant remain intact. Historical receipts: [status repair](verification/ipo-status-repair-2026-09-25.json) and [batch2](verification/nse-universe-batch2-live-publication-2026-09-25.json).

## Queue after batch3 is live-verified

[../data/discovery/ipo-universe-review-2026-09-25-batch4.json](../data/discovery/ipo-universe-review-2026-09-25-batch4.json) pins **15 candidates RFBL through SHREEDHAR**. It is explicitly gated on finishing batch3 verification first. Reconcile against latest main and published data before action; independently establish IPO versus FPO/rights/partly-paid/repeat/migration/debt offering; preserve aliases, nulls and conflicts. No aggregate-feed-only imports.

The queue comes from canonical audit `36095239145`, excluding all 45 prior-batch candidates, including holds/exclusions. **74 eligible source groups remain, not 74 confirmed IPOs.** QMSMEDI and 12VPT28A are prior-offer/security-type review signals only.

Remaining holds: **AMIRCHAND** (identity metadata), **ADANIENPP1** (offering type), **Fabino Life Sciences** (listing-year conflict), **GICL, SILGOPP, VITAL, KOTYARK** (older-offer/migration/repeat-security conflicts). The debt exclusion must not be recycled into the equity-IPO queue.

Broader gaps remain: BSE issue-summary adapter, SEBI historical pagination and unresolved NSE series. Do not claim complete IPO-universe coverage. BSE parser v1.5 remains **236/236 parsed**; do not replay that cursor.

## Preserved history and scope

The preceding handoff is archived byte-for-byte in [archive/PROJECT_STATUS-before-nse-batch3.md](archive/PROJECT_STATUS-before-nse-batch3.md) and [archive/README-before-nse-batch3.md](archive/README-before-nse-batch3.md). Earlier archives and receipts remain intact. UI V2 stays separate under [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md).

No UI, minimum-investment expansion, billing, accounts, ads, spending or permission changes belong to this continuation.
