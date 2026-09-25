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

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. It fetches the actual Pages dataset, retains its original bytes/hash and separate observation time, and checks issuer identity, values, source metadata and retained provenance. It runs manually or when its implementation changes; it does not alter the collection schedule or import IPOs. Its current default is cursor10 reviewed batches33/34.

Collection time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Latest completed backend unit: cursor10 bounded historical segment published and VERIFIED live — PR #222 / #223.** No UI or parser changes.

The bounded BSE SME cursor backfill run `36087053657` advanced the retained state from **200/236 -> 220/236 tracked notices**. All 20 selected notices parsed successfully and produced **23 listing references**.

Authoritative source review `36087769933` reconciled those references against the then-current 1,171-record universe: **23 exact-missing, 0 present, 0 identity/code/source conflicts**. Strict issuer-specific official BSE verification passed **22/23 issuers**, yielding **66 explicit listing-date / market-lot / issue-price facts**. One issuer, **Fabino Life Sciences Limited**, remains deliberately held: the candidate/index date is `2022-01-13`, while BSE Listing Notice `20220112-10` contains an observed listing date of `2021-01-13`. No correction was inferred.

PR #222 merged as `6413c9e46542a578095c75a6ff5c8edcf5f99f49`. Rehearsal proved **1,171 -> 1,193**, exactly 22 additions, all 1,171 previous records unchanged, 247 already-present reviewed entries, 0 import holds/conflicts and a byte-idempotent rerun. Production sync `36087986289` succeeded; generated-data commit `384f235bdf19545f3960f2c9bcc7ed16e3f70d57`; operator-state commit `dcaf482c7b9860c1c50fb37ba565ce3fe1d8431b` is healthy.

PR #223 merged as `7e36858a7445aac975be4c32dba62ca0a718a94b` and selects reviewed batches33/34 in the existing read-only Pages verifier. Canonical post-merge run `36088367208` verified the actually served dataset: **1,193 records, 22/22 unique issuers, 66/66 matching fields, 0 failures, six unsupported fields null per issuer**. Snapshot SHA-256 `e7ea980d0b158a239e3d22f155d42b90385672dfe7303e49efd10d5732f9cff8`. Durable receipt: [docs/verification/cursor10-live-publication-2026-09-25.json](docs/verification/cursor10-live-publication-2026-09-25.json).

### Next backend task

Current retained cursor: parser **1.4.0**, **220/236 tracked**, **219 parsed**, **1 retained unparseable**, **16 untracked**, updated `2026-09-25T02:38:14.470Z`. The next unseen notice is **`20210322-22`**.

**Continue the remaining bounded historical discovery segment from `20210322-22`.** Use the existing state-driven backfill; do not reset/replay prior progress. Reconcile newly discovered references against current recovery/public identities, BSE codes and listing-source identities; independently verify only missing/unambiguous candidates in batches of at most 15. Preserve hashes, dates, excerpts, conflicts and nulls; rehearse safe/idempotent publication; publish through the normal source-backed sync; verify the actually served Pages result.

Keep the Fabino conflict held and separate unless authoritative official evidence resolves its listing date. Cursor10 batches33/34 and all earlier cursor/repaired batches are closed. Index discovery is not listing-term authority. No UI, minimum-investment, billing, accounts, ads, spending or permissions changes belong to this continuation.

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
