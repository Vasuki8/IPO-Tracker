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

**Latest completed backend unit: cursor10 bounded segment published and VERIFIED live — PR #222 / #223.** No UI or parser changes.

The state-driven BSE SME cursor advanced one bounded segment: backfill run `36087053657` selected **20 notices**, parsed **20/20**, found **23 listing references**, and moved the retained cursor to **220/236 tracked**. Independent source review found all 23 references exact-missing against the then-current 1,171-record universe.

Strict issuer-specific official BSE verification accepted **22/23 issuers** with **66 explicit listing-date / market-lot / issue-price facts**. **Fabino Life Sciences Limited** remains deliberately held because official BSE listing notice `20220112-10` contains contradictory listing-year information; no date was inferred or guessed.

The publication rehearsal proved **1,171 -> 1,193**, exactly 22 additions, all 1,171 existing records unchanged, 247 already-present reviewed entries, 0 publishable-batch holds/conflicts and a byte-idempotent rerun. PR #222 merged as `6413c9e46542a578095c75a6ff5c8edcf5f99f49`. Production sync `36087986289` succeeded; generated-data commit `384f235bdf19545f3960f2c9bcc7ed16e3f70d57`; operator state `dcaf482c7b9860c1c50fb37ba565ce3fe1d8431b` is healthy.

PR #223 merged as `7e36858a7445aac975be4c32dba62ca0a718a94b` and selected reviewed batches33/34 in the existing read-only Pages verifier. Post-merge run `36088367208` verified the actual served snapshot: **1,193 records, 22/22 unique issuers, 66/66 matching fields, 0 failures**, with six unsupported fields null per issuer. Snapshot SHA-256 `e7ea980d0b158a239e3d22f155d42b90385672dfe7303e49efd10d5732f9cff8`. Durable receipt: [docs/verification/cursor10-live-publication-2026-09-25.json](docs/verification/cursor10-live-publication-2026-09-25.json).

### Next backend task

Current retained cursor: parser **1.4.0**, **220/236 tracked**, **219 parsed**, **1 retained unparseable**, **16 untracked**, updated `2026-09-25T02:38:14.470Z`. The next unseen notice is **`20210322-22`**.

**Process the final bounded historical cursor segment from `20210322-22` using the existing state-driven backfill.** Do not reset or replay prior progress. Reconcile new references against current recovery/public identities, BSE codes and listing-source identities; independently verify only missing/unambiguous candidates in batches of at most 15. Preserve hashes, dates, excerpts and nulls; rehearse safe/idempotent publication; publish through the normal source-backed sync; verify the actually served Pages result.

Keep the Fabino conflict separate from cursor continuation and do not silently correct it without an authoritative official source. Cursor10 batches33/34, cursor9 batches31/32, cursor8 batches23/24 + reviewed29/30 and all earlier repaired/cursor batches are closed. No UI, minimum-investment, billing, accounts, ads, spending or permission changes belong to this continuation.

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
