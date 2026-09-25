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

**Latest completed backend unit: first 15-candidate NSE universe review published and VERIFIED live — PR #230; propagation reliability fixed in PR #231.** No UI changes.

The batch reviewed 15 pinned NSE 2026 candidates using issuer-specific official evidence. **14 were verified as initial public equity offerings and published; ADANIENPP1 remains held** because its detail response lacks issue-specific IPO terms and the past feed contains three conflicting offer periods for the same security.

Source review run `36096308787`, artifact `10847442489`, SHA-256 `e00e9d7b3665c6f94e1994858e0fed05de6ac67b7bc6465ea7699fdf0e670e96`. The approved set retains **83 explicit facts**: 14 listing dates, 28 offer dates, 14 issue prices, 13 price bands, 9 market lots and 5 minimum bid quantities. Quote endpoints returned HTTP403 and were not used.

PR #230 merged as `60e2ab2360d6782be5952e31cd0253a504b9baa1`. Rehearsal proved **1,218 -> 1,232**, exactly 14 additions, all prior records unchanged, zero identity conflicts and an idempotent rerun. Production sync `36098558475` succeeded; generated data `77c74d759d9833aaf3147d757ae9b7f8e30c1e1f`; operator state `63370ecbd7e5e49a86f8c690f5da62cb65548ce6` is healthy.

Publication verifier `36099067573`, attempt 2, verified the actual Pages dataset: **1,232 records, 14/14 issuers, 83/83 reviewed facts, 0 failures**, snapshot SHA-256 `3fe550decca530638e0b354381827b5142c611fff89329c68562f1488e754f5c`. Live delta from the preceding verified snapshot is **+14 added / 0 removed / 7 existing records changed by unrelated scheduled/source enrichment**.

Attempt 1 had failed only because Pages still served the old snapshot before propagation completed. PR #231 (`c170c420774705c86c16f16cb7faf1980cbc86de`) extends the bounded verifier wait to cover the observed multi-minute Pages lag; verification logic, schedules and permissions are unchanged. Post-merge validation and Pages deployment passed.

Durable receipt: [docs/verification/nse-universe-batch1-live-publication-2026-09-25.json](docs/verification/nse-universe-batch1-live-publication-2026-09-25.json).

### Exact next backend task

Review [data/discovery/ipo-universe-review-2026-09-25-batch2.json](data/discovery/ipo-universe-review-2026-09-25-batch2.json): **15 pinned candidates from GICL through SPCON**. Reconcile every row against latest main and all recovery years, then establish IPO versus FPO/rights/partly-paid/repeat/other security using issuer-specific official evidence. Do not auto-import from the NSE past-issues feed. Preserve aliases, nulls and conflicts; publish only independently verified unambiguous IPOs with rehearsal, source-backed sync and actual Pages verification.

**ADANIENPP1 remains held** for unresolved offering type. **Fabino Life Sciences remains held** for its conflicting official listing year. The BSE parser cursor remains **236/236 parsed** and must not be replayed. BSE summary-source repair, SEBI historical pagination and broader P1 coverage remain unfinished.

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
