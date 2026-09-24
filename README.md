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

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. It fetches the actual Pages dataset, retains its original bytes/hash and separate observation time, and checks issuer identity, values, source metadata and retained provenance. It runs manually or when its implementation changes; it does not alter the collection schedule or import IPOs.

Collection time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Latest completed unit: cursor5 parsed references reconciled against current production; no duplicate verification/import required.**

The historical cursor segment first attempted at `2026-09-24T15:09:03.207Z` contains 20 notices:

- **17 parsed notices**
- **18 listing references**
- **3 unparseable notices**
- cursor state: **120 / 236 tracked**, **117 parsed**, **3 unparseable**

The earlier retained report `data/discovery/bse-listing-reconciliation-2026-09-24-cursor5.json` was correct at its 15:43 UTC observation: all 18 parsed identities were then missing. Subsequent official-source syncs populated them. That historical report is preserved unchanged.

Current-state reconciliation is retained as:

`data/discovery/bse-listing-reconciliation-2026-09-24-cursor5-final.json`

It compares the 18 parsed references against **all recovery years 2020-2026** and current public data, using normalized issuer identity, six-digit BSE code, and exact issuer-specific listing-source URL. Result:

- **18 / 18 already-present exact identities**
- **18 / 18 current public listing-date / market-lot / issue-price triples match retained recovery**
- **0 genuinely missing**
- **0 ambiguous / identity-review cases**
- **0 code conflicts**
- therefore **no new verifier batch and no re-import are justified**

Current reconciliation snapshot:

- public dataset: **1,068 records**
- 2020 recovery: **51**
- 2021: **100**
- 2022: **94**
- 2023: **174**
- 2024: **269**
- 2025: **293**
- 2026: **87**
- public dataset generation: `2026-09-24T16:21:47.053Z`

Do not replay these 18 references or treat the earlier “missing” classification as current state. The official index notices remain discovery-only; the already-present records retain issuer-specific BSE listing evidence.

### Next task

Keep the three failed cursor5 notices on their separate parser/source-family repair track:

- `20241211-15`
- `20241202-11`
- `20240722-21`

Re-fetch only those retained official BSE Index Services notice-detail payloads, confirm response hashes against cursor state, group failures by demonstrated source shape, and make only evidence-backed parser changes. Do **not** infer issuers from titles/index membership.

Before starting, re-read `main` and `ops/bse-sme-addition-notices.json`; if the independent cursor has advanced, do not skip these three held failures.

No UI redesign, minimum-investment work, billing, accounts, ads, spending or permission changes are included.
## Local checks

```bash
node scripts/test-verify-bse-publication.mjs
node scripts/test-bse-public-projection.mjs
node scripts/test-bse-publication-rehearsal.mjs
node scripts/apply-verified-bse-listings.mjs --check
node scripts/build-published-data.mjs --check
node scripts/validate-data.mjs
node scripts/audit-historical-coverage.mjs
```

For a live receipt, run `scripts/verify-bse-publication.mjs` with `--manifests=<comma-separated reviewed paths>` and `--output-dir=<artifact directory>`. It reports failure on unavailable/malformed snapshots or mismatches and never imports IPO records.

## Historical handoffs

The complete previous README and status are preserved unchanged in [docs/archive/README-before-cursor4-live-verification.md](docs/archive/README-before-cursor4-live-verification.md) and [docs/archive/PROJECT_STATUS-before-cursor4-live-verification.md](docs/archive/PROJECT_STATUS-before-cursor4-live-verification.md). Older archives remain unchanged. Archived next-task instructions are not current instructions.
