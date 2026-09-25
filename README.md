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

**Latest completed backend unit: second retained cursor segment published and VERIFIED live — PR #220 / #221.** No UI or parser changes.

PR #220 merged as `3f8bc9086d8ca36f3b7d402c9f614b8e1f0a694d`. It retained discovery batches31/32, cursor9 reconciliation and reviewed evidence batches31/32 for **25 exact-missing BSE SME issuers**. Read-only source review `36080905638` found 25 missing / 0 present / 0 identity-code-source conflicts against the then-current 1,146-record universe. Independent official BSE issuer-listing verification passed **25/25**, with **75 explicit listing-date / market-lot / issue-price facts**. Unsupported fields remain null.

The exact source-snapshot rehearsal proved **1,146 -> 1,171**, exactly 25 additions, all 1,146 existing records unchanged, 222 already-present reviewed entries, 0 holds/conflicts and a byte-idempotent rerun. Relevant importer/evidence, publication-rehearsal, reviewed-evidence and data-contract checks passed.

Production source-backed syncs completed successfully. PR #221 (`bd549cc8b1951f6741fe6f6fd5ba11bdc5eacd48`) selected batches31/32 in the existing read-only Pages verifier. Post-merge live run `36086364954` verified the actual served snapshot: **1,171 records, 25/25 unique issuers, 75/75 matching fields, 0 failures, six unsupported fields null per issuer**. Snapshot SHA-256 `d8549169d7f15e297e6df535d3ce520abb32ab8c50c1b647a9c43839aa4a9f1c`. Durable receipt: [docs/verification/cursor9-live-publication-2026-09-25.json](docs/verification/cursor9-live-publication-2026-09-25.json).

### Next backend task

Current retained cursor: parser **1.4.0**, **200/236 tracked**, **199 parsed**, **1 retained unparseable**, **36 untracked**, updated `2026-09-24T23:18:20.858Z`.

**Continue one bounded historical discovery segment from the first unseen notice after the current retained state.** Use the existing state-driven backfill; do not reset or replay progress. Reconcile new references against current recovery/public identities, BSE codes and listing-source identities; independently verify only missing/unambiguous candidates in batches of at most 15. Preserve hashes, dates, excerpts and nulls; rehearse safe/idempotent publication; publish through the normal source-backed sync; verify the actually served Pages result.

Cursor9 batches31/32 are closed. Cursor8 batches23/24 + reviewed29/30 and all earlier repaired/cursor batches are closed. Index discovery is not listing-term authority. No UI, minimum-investment, billing, accounts, ads, spending or permissions changes belong to this continuation.

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
