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

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. It fetches the actual Pages dataset, retains its original bytes/hash and separate observation time, and checks issuer identity, values, source metadata and retained provenance. It runs manually or when its implementation changes; it does not alter the collection schedule or import IPOs. Its current default is repaired-cursor7 reviewed batch28.

Collection time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Latest completed backend unit: earliest pending cursor8 segment published and VERIFIED — PR #219.** No UI or parser changes.

PR #219 merged as `7fbd972531154a19624711a10cf77f52dd12bb58`. It retained discovery batches23/24, cursor8 reconciliation and reviewed evidence batches29/30 for **24 exact-missing BSE SME issuers**. Source review `36072368549` found 24 missing / 0 present / 0 identity-code-source conflicts against the then-current 1,122-record universe. Independent issuer-specific official BSE verification passed **24/24**, with **72 explicit listing-date / market-lot / issue-price facts** revalidated. Unsupported fields remain null; retained unparseable index notice `20221010-15` was not promoted to IPO terms.

The real rehearsal proved **1,122 -> 1,146**, exactly 24 additions, all 1,122 existing records unchanged, 198 already-present reviewed entries, 0 holds/conflicts and byte-idempotent rerun. PR-head and post-merge reviewed-evidence/data-contract CI passed.

Production source-backed sync `36079891576` succeeded, generated-data commit `9cd4824aa7d1cd3c26c6dbce84c8fca1ad58a641`, operator-state commit `7d5e43eada6b7767048871f89ac3a8cb745ab7f4`. Latest Pages deployment `36080148485` succeeded. Operator snapshot at `2026-09-25T01:01:00.530Z` is **healthy** with collection, rebuild, validation and repository publication successful. Full evidence, clocks and hashes are in [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

### Next backend task

Current retained cursor: parser **1.4.0**, **200/236 tracked**, **199 parsed**, **1 retained unparseable**, **36 untracked**, updated `2026-09-24T23:18:20.858Z`.

**Reconcile and review the next pending cursor segment, which already contains 25 discovered references from the following 20 notices.** Compare against current recovery/public identities, BSE codes and listing-source identities; independently verify only missing/unambiguous candidates in batches of at most 15. Preserve hashes, dates, excerpts and nulls; rehearse safe/idempotent publication; publish through the normal source-backed sync; verify served output. Do not reset/replay cursor progress.

Cursor8 batches23/24 + reviewed29/30 are closed. Do not repeat earlier repaired/cursor batches. Index discovery is not listing-term authority. No UI, minimum-investment, billing, accounts, ads, spending or permissions changes belong to this continuation.

**Product UI workstream — V2 live and verified, PR #209:** its separate evidence and notes remain in [docs/UI_DESIGN_HANDOFF.md](docs/UI_DESIGN_HANDOFF.md). No UI files changed in this backend release.

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

The complete preceding README and status are archived unchanged in [docs/archive/README-before-repaired-cursor7-publication.md](docs/archive/README-before-repaired-cursor7-publication.md) and [docs/archive/PROJECT_STATUS-before-repaired-cursor7-publication.md](docs/archive/PROJECT_STATUS-before-repaired-cursor7-publication.md). Older archives and verification receipts remain unchanged. Archived next-task instructions are not current instructions.
