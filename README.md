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

**Latest completed unit: cursor4 publication verified live; canonical verifier and handoff completed in PR #189.**

PR #187 had already merged 23 reviewed cursor4 issuers through discovery batches 13/14 and evidence batches 18/19. PR #188 repaired the large-recovery-baseline buffer failure in semantic publication. Neither import nor repair should be repeated.

Live verification run **36020477749** checked the actual site at **2026-09-24T15:28:55.890Z**:

- **1,050 live records**; retained recovery counts: **2025 = 292**, **2026 = 87**.
- **23/23 issuers** occur exactly once and **69/69 listing-date, market-lot and issue-price fields** match reviewed evidence.
- All six unsupported fields remain null for each of these 23 issuers.
- Original document hashes and batch provenance are verified in retained recovery. The current public projection does **not** serialize document hashes; do not describe them as live hash verification.
- Data-contract, reviewed-evidence and fresh live-publication workflows passed on code head `3f2e29e1aa3be1e101c0bbe65f1339eb19302c25`.

Receipt: [docs/verification/cursor4-live-publication-2026-09-24.json](docs/verification/cursor4-live-publication-2026-09-24.json). Artifact **10817060050** retains the full receipt, actual served JSON and source snapshot. Duplicate alternative PR #190 was closed unmerged; do not resurrect its parallel auditor.

### Next task

Re-read `main`, this handoff, the development process and `ops/bse-sme-addition-notices.json` first.

The independent cursor has advanced to **120/236 tracked: 117 parsed, 3 unparseable, 116 not yet tracked**. The newly completed 20-notice segment first attempted at **2026-09-24T15:09:03.207Z** contains **18 parsed listing references** across 17 notices, from `20250103-24` through `20240627-14`.

**Reconcile those 18 references against the current multi-year recovery/public universe**, then independently verify only genuinely missing, unambiguous issuers in batches of at most 15. These references have not yet been established as missing IPOs. Keep the three failed index notices (`20241211-15`, `20241202-11`, `20240722-21`) on a separate parser/source-family repair track. Do not infer their issuers. Do not skip this unprocessed segment if a newer cursor segment appears.

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
