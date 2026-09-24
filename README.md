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

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. It fetches the actual Pages dataset, retains its original bytes/hash and separate observation time, and checks issuer identity, values, source metadata and retained provenance. It runs manually or when its implementation changes; it does not alter the collection schedule or import IPOs. Its current default remains cursor7 reviewed batches26/27.

Collection time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Latest completed backend unit: seven retained BSE parser failures repaired and VERIFIED operationally — PR #213.** No UI or IPO-data changes.

PR #213 merged as `224349d83acac08370ab30e9239ffaebab58dabc`. Parser **1.4.0** accepts the demonstrated BSE SME Platform suffix and terminal respectively in ordered shared-ID issuer lists, while rejecting incomplete/ambiguous mappings. Existing successful v1.1/v1.2/v1.3 cursor entries remain compatible. The temporary read-only diagnostic workflow was removed before merge; existing schedules and permissions are unchanged.

All seven freshly fetched source-text hashes matched retained cursor hashes. Seven literal source fixtures, **84 new fail-closed mutations**, asynchronous repair migration and idempotency checks passed. PR-head cursor/parser, reviewed-evidence and full data-contract CI all passed.

Production retry **`36065458265`** selected exactly seven old-parser failures and completed **7/7 parsed**, **13 recovered references**, **0 fetch errors**, **0 unparseable**. All **153 prior successful entries** and bootstrap were preserved exactly. Saved cursor commit: `ec995bfe578a0ae0fc5f9a47a236d335f9ef83e9`; whole-state Git blob: `0aba996b117374ea2ba4fbeb299144b63ca9cba2`.

Current historical cursor, attempted `2026-09-24T22:06:07.403Z`: **160/236 tracked**, **160 parsed**, **0 failed**, **76 untracked**; next unseen notice **`20230503-13`**.

The thirteen recovered references are **discovery only, not newly published IPOs**. Public and retained recovery data were unchanged at **1,109 records**. The previous live-publication receipt remains valid historical evidence; this unit verified the actual operational cursor instead of claiming a new website-data release.

Durable evidence: [docs/verification/bse-parser-v1.4-2026-09-24.json](docs/verification/bse-parser-v1.4-2026-09-24.json). Full source hashes, tests, commits, artifact IDs and production verification are in [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

### Next backend task

Re-read current main and cursor, then **reconcile the thirteen recovered references against the latest 2020-2026 recovery and public dataset** using issuer identity, BSE scrip code and listing-source identity. Do not assume thirteen missing IPOs. Independently verify issuer-specific BSE listing notices only for missing/unambiguous candidates, in batches of at most 15. Then retain reviewed evidence, rehearse safe/idempotent publication and verify the actually served dataset. Close this recovered segment before skipping to newer unseen work, even if independent automation advances.

The seven former parser failures are now closed. Do not replay cursor7 discovery batches20/21 or reviewed batches26/27, nor completed cursor6 batches18/19 or reviewed batches24/25. Index discovery is not listing-term authority. No UI, minimum-investment, billing, accounts, ads, spending or permissions changes belong to this continuation.

**Product UI workstream — V2 live and verified, PR #209:** its separate evidence and notes remain in [docs/UI_DESIGN_HANDOFF.md](docs/UI_DESIGN_HANDOFF.md). No UI files changed in the parser repair.

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

The complete preceding README and status are archived unchanged in [docs/archive/README-before-cursor7-parser-repair.md](docs/archive/README-before-cursor7-parser-repair.md) and [docs/archive/PROJECT_STATUS-before-cursor7-parser-repair.md](docs/archive/PROJECT_STATUS-before-cursor7-parser-repair.md). Older archives and verification receipts remain unchanged. Archived next-task instructions are not current instructions.
