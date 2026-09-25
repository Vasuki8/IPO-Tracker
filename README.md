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

**Latest completed backend unit: bounded official IPO-universe audit VERIFIED — PR #229.** Merge commit `2c9b5d0d97754747b6510a0bb0ad837e988e65b0`. No IPO data or UI changes.

Canonical main audit `36095239145`, generated **2026-09-25 04:38:31 UTC / 00:38:31 Toronto**, reconciled **1,283 observations / 1,232 normalized issuer-name groups** against the 1,218-record tracker:

| Classification | Groups |
| --- | ---: |
| Already present | 970 |
| Exact-name-unmatched review candidates | 224 |
| Identity-review cases | 38 |
| New IPOs imported | 0 |

**224 unmatched names are not 224 confirmed missing IPOs.** Offering type, aliases, identifiers and issuer-specific official evidence require review. Seven of eight source adapters were usable. BSE summary returned an HTML shell with no issuer rows; SEBI covers only the first 25 rows of each filing category; NSE other-series rows and historical completeness remain gaps. A filing stage is not a listing/outcome, and index membership is not the full IPO universe. The audit correctly reports `full_universe_complete:false`.

Source hashes, baseline hashes, and both full and compact reports were independently replayed exactly for the PR and main runs. Current-head and post-merge audit/data-contract/reviewed-evidence checks passed. The main workflow's clean-worktree check passed.

A fresh existing Pages verifier run `36093076719`, **attempt 2**, fetched the live dataset at `2026-09-25T04:39:09.873Z`. It remains **1,218 records and byte-identical to the baseline**, SHA-256 `9a5ced8e0831bf07961c4fb3593f24d99008688f6874b2b86649c1d449841945`: **0 added / 0 removed / 0 changed**. No new issuer was published in this unit.

Durable receipt: [docs/verification/ipo-universe-audit-2026-09-25.json](docs/verification/ipo-universe-audit-2026-09-25.json). Full raw evidence and all-candidate reports are in artifact **10846749143**, SHA-256 `14521267a7d9d11f197248c3a7d4fca7fcf2e7257f63544a45677f1e1edf0c8c`, expiring **2026-10-09 04:38:37 UTC**.

### Exact next backend task

**Review the first 15 NSE 2026 candidates pinned in [data/discovery/ipo-universe-review-2026-09-25-batch1.json](data/discovery/ipo-universe-review-2026-09-25-batch1.json).** The audit observed 119 exact-name-unmatched groups with a 2026 NSE listing-date observation. This batch selects the earliest 15 by date then symbol, beginning `E2ERAIL` and ending `FRACTAL`.

Re-read current main and reconcile all years again. Establish IPO versus FPO, rights, partly-paid/repeat security or another offer type using issuer-specific official evidence; **no row, including `ADANIENPP1`, has approved IPO status from the queue alone**. Resolve legal-name and identifier ambiguity. Only publish independently verified unambiguous IPOs, with a preservation/idempotency rehearsal, normal source-backed sync and actual Pages verification. Do not bulk-import the unmatched names or blindly extend the historical materializer.

BSE summary-source repair and SEBI historical pagination remain separate bounded coverage tasks. **Fabino Life Sciences remains held** for its 2021-versus-2022 listing-year conflict; no correction may be inferred. The BSE parser v1.5 cursor remains **236/236 parsed**, with no replay needed. Broader P1 coverage/field completeness remains unfinished.

No UI, minimum-investment expansion, billing, accounts, ads, spending or permission changes belong to this continuation. UI V2 remains a separate completed workstream under [docs/UI_DESIGN_HANDOFF.md](docs/UI_DESIGN_HANDOFF.md).

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
