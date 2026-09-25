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

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. It fetches the actual Pages dataset, retains its original bytes/hash and separate observation time, and checks issuer identity, values, source metadata and retained provenance. It runs manually or when its implementation changes; it does not alter the collection schedule or import IPOs. Its current default is cursor11 reviewed batch35.

Collection time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Latest completed backend unit: cursor11 publishable records VERIFIED live — PR #224 / #225.** No UI or parser changes. All catalogued historical notices have now been attempted, but this is not complete IPO-universe coverage.

Backfill run `36089320357` selected the final 16 unseen notices: **14 parsed, 2 new unparseable, 0 fetch errors, 15 issuer references**. All 220 earlier notice objects stayed unchanged. The retained cursor is now **236/236 tracked, 233 parsed, 3 unresolved, 0 unseen**, with `complete: false`.

Independent source review `36089473609` found **15 exact-missing identities**, with zero already-present or ambiguous/colliding identities. All **15 issuer-specific official BSE notices / 45 facts** passed verification. Original response hashes, dates, literal excerpts and unsupported nulls are retained in discovery/reviewed batch35 and cursor11 reconciliation.

PR #224 merged as `9b83b943e9d5ef89c1136769825d2053b84bd54c`. Real rehearsal: **1,193 -> 1,208**, 15 additions, all 1,193 existing records unchanged, 269 already-present reviewed entries, zero holds/conflicts and a byte-idempotent rerun. Current-head reviewed-evidence/data-contract checks passed. Production sync `36090144644` succeeded; generated-data commit `85841109957bf71f7c35e7e7d922bc5f73fbef96`; operator snapshot at `2026-09-25T03:26:46.463Z` is healthy.

PR #225 merged as `79d6adcf144a6855d3bb8ca10d75d6cc87d65bce`. Canonical post-merge live run `36090479336` verified **1,208 actually served records, 15/15 unique issuers, 45/45 matching fields, zero failures and six unsupported null fields per issuer**. Snapshot fetched `2026-09-25T03:28:25.758Z`, SHA-256 `8139aab00bef2066d00377eca641f1e09f6dec6a6fe1a61d1c7e1ead788c9329`. Downloaded bytes and all issuer results were independently audited; PR/post-merge snapshots match exactly. Public evidence omits document hashes; original hashes were checked in retained recovery.

The actual served comparison found **15 added / 2 changed / 0 removed**. The two changes only added SEBI document references and collection times to existing records; no old documents were removed and no existing IPO term value changed. Durable receipt: [docs/verification/cursor11-live-publication-2026-09-25.json](docs/verification/cursor11-live-publication-2026-09-25.json).

### Next backend task

**Inspect and repair the three retained parser failures: `20221010-15`, `20200813-12` and `20200713-20`.** Re-read current main and cursor. Work from original official source text, retain fixtures, and add fail-closed regression tests before any reusable parser repair. Do not reset or replay successfully parsed history. Reconcile any recovered references against current multi-year identities and independently verify issuer-specific listing evidence before reviewed import and live verification.

**Fabino Life Sciences Limited remains separately held and absent from the served snapshot.** Its candidate/index listing date `2022-01-13` conflicts with `2021-01-13` in official notice `20220112-10`; no correction may be inferred without authoritative official evidence.

Cursor11 batch35 and all earlier cursor/repaired publication batches are closed. Broader coverage and field completeness remain incomplete. No UI, minimum-investment, billing, accounts, ads, spending or permission changes belong to this continuation.

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
