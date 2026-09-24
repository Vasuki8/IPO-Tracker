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

**Latest completed backend unit: thirteen repaired cursor7 references published and VERIFIED live — PR #215 / #216.** No UI or parser changes.

PR #215 (`45eab356842ecd49895642133fc2e3eab1d0c427`) retained discovery batch22, the multi-year reconciliation report and reviewed evidence batch28. All thirteen references were absent from the current 1,109-record recovery/public universe and independently verified against issuer-specific official BSE listing notices. Source review run `36068697382`: **13/13 verified, 0 rejected/unavailable**. Original response hashes, collection/publication dates and literal evidence excerpts were preserved; unsupported terms remain null. The temporary read-only review workflow was removed before merge.

The real publication rehearsal proved **1,109 -> 1,122**, **13 additions**, all **1,109 existing records unchanged**, **185 already-present reviewed entries**, **0 holds/conflicts**, and a byte-idempotent rerun. All relevant local tests and PR-head data-contract/reviewed-evidence checks passed.

Production sync `36069541844` succeeded and operator health was healthy. The actual served comparison found **13 added / 3 changed / 0 removed**. Three existing records gained SEBI document references and collection timestamps; no existing IPO term value changed. Recovery increased **2023: 192 -> 196** and **2024: 292 -> 301**.

PR #216 (`f41557347c204fda3f8f297e4ed23f1267b39d49`) selected batch28 in the existing read-only live verifier. Post-merge run `36070243437` confirmed **1,122 served records**, **13/13 unique issuers**, **39/39 matching fields**, **0 failures**, and **six unsupported fields null per issuer**. Snapshot fetched `2026-09-24T22:57:35.734Z`; dataset generated `2026-09-24T22:49:44.462Z`. Original document hashes were checked in 39 retained recovery field sources; the public projection serializes zero document hashes. Downloaded archive/served bytes and an independent pure audit matched the workflow receipt.

Live artifact `10838520133`, ZIP SHA-256 `9177f167c564f4c9269c15d4d9bd7ec377dc2320246999284369e0ba080ae8d0`. Durable receipt: [docs/verification/repaired-cursor7-live-publication-2026-09-24.json](docs/verification/repaired-cursor7-live-publication-2026-09-24.json). Full source hashes, tests, clocks and commits are in [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

### Next backend task

Re-read current main and cursor. Latest checked: parser **1.4.0**, **160/236 tracked**, **160 parsed**, **0 failed**, **76 untracked**, updated `2026-09-24T22:06:07.403Z`.

**Continue one bounded historical cursor segment from the first unseen notice, currently `20230503-13`.** If independent automation has advanced, reconcile its earliest pending segment instead of fetching it again. Check all current recovery/public identities, BSE codes and listing sources; independently verify only missing/unambiguous candidates before reviewed publication. Preserve source hashes, dates and nulls; rehearse safe/idempotent publication and verify the actual served dataset.

The thirteen repaired references are closed as discovery batch22 / reviewed batch28. Do not repeat the seven parser repairs, cursor7 discovery20/21 and reviewed26/27, or cursor6 discovery18/19 and reviewed24/25. Index discovery is not listing-term authority. No UI, minimum-investment, billing, accounts, ads, spending or permissions changes belong to this continuation.

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
