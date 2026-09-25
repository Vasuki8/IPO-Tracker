# IPO Tracker

A source-first Indian IPO research website with automated official-source collection and GitHub Pages publication.

- Repository: `Vasuki8/IPO-Tracker`; default branch: `main`.
- Website: https://vasuki8.github.io/IPO-Tracker/
- Public dataset: `data/ipos.json`, generated from retained evidence under `data/recovery/`.
- Development contract: [docs/DEVELOPMENT_PROCESS.md](docs/DEVELOPMENT_PROCESS.md).
- Current handoff: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Product and data rules

Coverage spans 2020-2026 but is incomplete. Run `node scripts/audit-historical-coverage.mjs` for current counts; old milestones are not current totals.

The active application-term requirement is **Lot Size only**. Display verified market lot first, then verified minimum bid quantity when market lot is missing. Keep the raw fields distinct. Minimum investment/application amount remains out of scope.

Never invent missing values or use price-times-quantity arithmetic to fill them. Preserve official sources, document identity, dates, hashes when retained, nulls, conflicts and correction history. A final Prospectus is not required for inclusion. Repair retained recovery evidence rather than hand-editing `data/ipos.json`.

## Automation

The existing hourly `update-ipos.yml` collects NSE/SEBI data and imports reviewed BSE evidence. Historical PDF recovery and the bounded BSE notice cursor run independently. `deploy-pages.yml` publishes the site. Workflow files define actual schedules and execution.

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. It fetches the actual Pages dataset, retains its original bytes/hash and separate observation time, and checks issuer identity, values, source metadata and retained provenance. It runs manually or when its implementation changes; it does not alter the collection schedule or import IPOs. Its current default is parser-v1.5 recovered reviewed batch36.

Collection time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Latest completed backend unit: all BSE cursor parser failures repaired and the 10 recovered issuers VERIFIED live — PR #226 / #227 / #228.** No UI changes.

Parser **v1.5.0** repairs the three former failures `20221010-15`, `20200813-12`, and `20200713-20` using exact official-source fixtures and fail-closed rules. Production migration run `36092149729` selected exactly those three failures, parsed all three, recovered **10 references**, and preserved successful v1.4 history. The retained cursor is now **236/236 tracked, 236 parsed, 0 failed, 0 unseen, complete:true**.

Independent source review `36092275068` found the 10 recovered references were all exact-missing against the then-current 1,208-record universe. **10/10 issuer-specific official BSE notices and 30/30 listing-date / market-lot / issue-price facts verified**, with zero rejected/unavailable sources.

PR #227 merged as `e581d1e7a47f59fc62a3488849e815f5ae689b15`. Rehearsal proved **1,208 -> 1,218**, exactly 10 additions, every prior record unchanged, zero holds/conflicts and an idempotent rerun. Production sync `36092732738` succeeded; generated data `61b173feb789fba15eb207c0bacaaa476704cbbb`; operator state `602fd2cdb2d2da6c47e85048bf61c3aa1839566d` is healthy.

PR #228 merged as `9abfd1f72e9277dc22158be9249fe419fd667fd7`. Canonical live run `36093076719` verified the actually served dataset: **1,218 records, 10/10 unique issuers, 30/30 matching fields, 0 failures**, cursor v1.5.0 with 236/236 parsed. Snapshot SHA-256 `9a5ced8e0831bf07961c4fb3593f24d99008688f6874b2b86649c1d449841945`. Compared with the previous verified snapshot, the live delta is **+10 added / 0 removed / 0 existing records changed**. Durable receipt: [docs/verification/bse-parser-v1.5-repair-and-live-publication-2026-09-25.json](docs/verification/bse-parser-v1.5-repair-and-live-publication-2026-09-25.json).

**Fabino Life Sciences Limited remains separately held.** Do not infer a corrected listing year; candidate/index `2022-01-13` conflicts with issuer-specific notice `2021-01-13`.

### Next backend task

The bounded BSE SME cursor is closed and fully parsed. Return to the earliest unfinished P1 priority: **IPO-universe coverage**.

Run a fresh machine-readable official-universe audit across current NSE, BSE and SEBI sources against the **1,218-record** tracker. Define/retain inclusion and status rules for Mainboard/SME and relevant draft/RHP/final/open/upcoming/completed/withdrawn states, reconcile issuer/market/source identities, report exact missing/ambiguous/already-present counts, and only add unambiguous exact-missing issuers with official evidence. Do **not** treat 236 BSE index notices as the complete IPO universe.

Observed tracker counts are 2020:65, 2021:120, 2022:136, 2023:216, 2024:301, 2025:293, 2026:87; these are baselines, not completeness claims. After identity coverage, continue P1 field completeness; Lot Size remains the active application-term requirement.

No UI, minimum-investment expansion, billing, accounts, ads, spending or permission changes belong to this continuation.

**Product UI workstream — V2 live and verified, PR #209:** separate notes remain in [docs/UI_DESIGN_HANDOFF.md](docs/UI_DESIGN_HANDOFF.md).

## Local checks

```bash
node scripts/test-audit-bse-sme-addition-notices.mjs
node scripts/test-backfill-bse-sme-addition-notices.mjs
node scripts/test-apply-bse-sme-addition-notice-state.mjs
node scripts/apply-bse-sme-addition-notice-state.mjs --check
node scripts/test-verify-bse-publication.mjs
node scripts/test-bse-public-projection.mjs
node scripts/test-bse-publication-rehearsal.mjs
node scripts/apply-verified-bse-listings.mjs --check
node scripts/build-published-data.mjs --check
node scripts/validate-data.mjs
node scripts/audit-historical-coverage.mjs
```

For a live IPO-publication receipt, run `scripts/verify-bse-publication.mjs` with `--manifests=<comma-separated reviewed paths>` and `--output-dir=<artifact directory>`. It reports failure on unavailable/malformed snapshots or mismatches and never imports IPO records.

## Historical handoffs

The previous README and status are preserved byte-for-byte in [docs/archive/README-before-cursor11-publication.md](docs/archive/README-before-cursor11-publication.md) and [docs/archive/PROJECT_STATUS-before-cursor11-publication.md](docs/archive/PROJECT_STATUS-before-cursor11-publication.md). Earlier archives and verification receipts remain unchanged. Archived next-task instructions are not current instructions.
