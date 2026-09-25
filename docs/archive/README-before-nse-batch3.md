# IPO Tracker

A source-first Indian IPO research website with automated official-source collection and GitHub Pages publication.

- Repository: `Vasuki8/IPO-Tracker`; default branch: `main`.
- Website: https://vasuki8.github.io/IPO-Tracker/
- Public dataset: `data/ipos.json`, generated from retained evidence under `data/recovery/`.
- Development contract: [docs/DEVELOPMENT_PROCESS.md](docs/DEVELOPMENT_PROCESS.md).
- Current handoff: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Product and data rules

Coverage spans 2020-2026 but is incomplete. Stored record counts are not proof of official IPO-universe completeness.

The active application-term requirement is **Lot Size only**. Display verified market lot first, then verified minimum bid quantity when market lot is missing. Keep the raw fields distinct. Minimum investment/application amount remains out of scope.

Never invent missing values or use price-times-quantity arithmetic to fill them. Preserve official sources, document identity, dates, hashes when retained, nulls, conflicts and correction history. A final Prospectus is not required for inclusion. Repair retained recovery evidence rather than hand-editing `data/ipos.json`.

## Automation

The existing hourly `update-ipos.yml` collects NSE/SEBI data and imports reviewed BSE evidence. Historical PDF recovery and the bounded BSE notice cursor run independently. `deploy-pages.yml` publishes the site. Workflow files define actual schedules and execution.

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. It fetches the actual Pages dataset, retains original bytes/hash and separate observation time, and checks issuer identity, values, source metadata and retained provenance. Its current default remains parser-v1.5 recovered reviewed batch36.

`audit-ipo-universe.yml` is a **read-only bounded official-universe audit**, with no schedule. It runs manually or when relevant audit code/fixtures change. It collects eight NSE/BSE/SEBI source surfaces, verifies source hashes, reconciles exact issuer identities and records incomplete source coverage. Outputs include original responses, `sources.json`, `audit.json`, `audit-compact.json` and an exact source archive. Workflow artifacts expire after 14 days. No candidates are automatically imported.

Collection time, source business observation time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Latest completed backend unit: Unknown-status repair + NSE universe batch2 published and VERIFIED live.** No UI changes.

### Status correctness

Audit run `36101891389` found exactly **13** public records with null status; every one already had verified past NSE listing evidence. PR #232 (`df5d2a6ae8cd14e640c29225acb578f2dee960a3`) repairs those records at the recovery layer by deriving `listed` only from strict verified official-NSE listing evidence. PR #234 (`b62bd84a44cc3b901a4ca4735c315e878047d36d`) prevents regression by requiring every published record to have `open/upcoming/closed/listed` plus status evidence.

The current served snapshot has **0 Unknown statuses**: listed 1,222; open 16; closed 3; upcoming 2. Receipt: [docs/verification/ipo-status-repair-2026-09-25.json](docs/verification/ipo-status-repair-2026-09-25.json).

### NSE universe batch2

Source review run `36102861946`, artifact `10849678453`, SHA-256 `ca9c15994d67dea46c735b8a3cd555def34a3948463ab05b893615e94af2bdbd`.

**11 verified IPOs published:** MARUSHIKA, MANILAM, CLEANMAX, MOBILISE, PNGSREVA, OMNI, YAAP, STRIDERS, ACETEC, SEDEMAC, SPCON. **4 held:** GICL, SILGOPP, VITAL, KOTYARK because their evidence points to older offer periods/migration or repeat-security situations rather than a demonstrated new 2026 IPO.

The reviewed set retains **66 explicit facts**. Rehearsal proved **1,232 -> 1,243**, 11 additions, all prior records unchanged, zero removals/conflicts, idempotent rerun. PR #233 merged as `1bac6fda9c05214383353741077cb517869b2ec5`. Production sync `36156433535` succeeded; generated data `06253c537f7ff08dc4ef0fea325647a2ea0ec036`; operator state `2850090ae29534b709be9fe47f9d577bad56abe6` is healthy.

Live verifier `36157133065` passed on the actual Pages dataset: **1,243 records, 11/11 issuers, 66/66 facts, 0 failures, 0 Unknown statuses**, snapshot SHA-256 `f349cc612501e4fb16b7616aadf902ae282b4541ae92e84df672299cf4703a54`. Receipt: [docs/verification/nse-universe-batch2-live-publication-2026-09-25.json](docs/verification/nse-universe-batch2-live-publication-2026-09-25.json).

### Exact next backend task

Review [data/discovery/ipo-universe-review-2026-09-25-batch3.json](data/discovery/ipo-universe-review-2026-09-25-batch3.json): **15 pinned candidates from APSISAERO through SIMCA**. Reconcile against latest main, independently establish offering type and issuer identity, and do not auto-import from the NSE past-issues feed. The symbol **10MWL29** and any previously listed issuer are explicit repeat/migration review signals.

Existing holds remain: ADANIENPP1, Fabino Life Sciences, GICL, SILGOPP, VITAL and KOTYARK. BSE parser remains 236/236 parsed. Broader BSE/SEBI universe-source gaps remain unfinished.

No UI, minimum-investment expansion, billing, accounts, ads, spending or permission changes belong to this continuation.

**Product UI workstream — V2 live and verified, PR #209:** separate notes remain in [docs/UI_DESIGN_HANDOFF.md](docs/UI_DESIGN_HANDOFF.md).

## Local checks

```bash
node scripts/test-audit-ipo-universe.mjs
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

Read-only official-universe collection and reconciliation, writing outside the checkout:

```bash
node scripts/collect-ipo-universe-sources.mjs --output-dir=/tmp/ipo-universe
node scripts/audit-ipo-universe.mjs --input=/tmp/ipo-universe --output=/tmp/ipo-universe/audit.json
```

A successful audit execution can still have **partial source coverage**; always inspect the report's source gaps and `full_universe_complete` flag. For live IPO-publication receipts, use `scripts/verify-bse-publication.mjs` with `--manifests=<reviewed paths>` and `--output-dir=<artifact directory>`. Neither verifier imports IPO records.

## Historical handoffs

The preceding README and status are archived unchanged in [docs/archive/README-before-official-universe-audit.md](docs/archive/README-before-official-universe-audit.md) and [docs/archive/PROJECT_STATUS-before-official-universe-audit.md](docs/archive/PROJECT_STATUS-before-official-universe-audit.md). Earlier archives and verification receipts remain intact. Archived next-task instructions are not current instructions.
