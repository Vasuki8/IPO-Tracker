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

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. Its current default is cursor7 reviewed batches26/27. It fetches actual Pages JSON, retains exact bytes/hash and separate observation time, and checks issuer identity, values, public evidence and retained provenance. It runs manually or when its implementation changes; it does not alter the collection schedule or import IPOs.

Collection time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Latest completed backend unit: cursor7 reviewed publication VERIFIED live — PR #210 / #211.** No UI files changed.

PR #210 (`66532672a7f9c84d1fadf96cb0b17b55e87e73a8`) added reviewed batches26/27, preserving the exact issuer-specific official BSE evidence for 18 issuers. PR #211 (`34b39bc9617c013c6e4d7d3955b3de5b5207a5f0`) selected those manifests in the existing read-only live verifier.

The real importer/publication rehearsal proved **1,091 -> 1,109**, **18 additions**, all **1,091 existing records unchanged**, **0 holds/conflicts**, and an idempotent second run. Both PRs' data-contract and reviewed-evidence checks passed.

Production sync `36061861729` succeeded. The actual served-data comparison found **18 added / 1 changed / 0 removed**; the existing-record change was additional SEBI documents and collection time for Ameya, not an IPO term change. 2023 recovery increased **174 -> 192**.

Canonical post-merge verifier `36062649127` confirmed **1,109 served records**, **18/18 unique issuers**, **54/54 matching fields**, **0 failed issuers**, and **six unsupported fields null per issuer**. Snapshot fetched `2026-09-24T21:37:42.271Z`; dataset generated `2026-09-24T21:30:22.442Z`. Original hashes were checked in 54 retained recovery field sources; the public projection intentionally serializes zero document hashes.

Live artifact `10835146698`, ZIP SHA-256 `6d6a46359c858b93038da3970ed268d6ca918f6e6b27a323c86fd9beb19ba80a`. Durable release evidence: [docs/verification/cursor7-live-publication-2026-09-24.json](docs/verification/cursor7-live-publication-2026-09-24.json). Full tests, commits, clocks and deployment details are in [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

### Next backend task

Re-read current main and cursor first. Last checked: parser **1.3.0**, **160/236 tracked**, **153 parsed**, **7 unparseable**, **76 untracked**, updated `2026-09-24T20:00:39.470Z`.

Diagnose the seven retained failed BSE Index Services notices as a bounded source/parser-family repair: `20240624-11`, `20240612-20`, `20240606-11`, `20240205-12`, `20240103-22`, `20231206-8`, `20230719-15`. Re-fetch only the failures, compare source hashes, and add only demonstrated grammar with fail-closed regressions. Do not infer issuers or terms from failed index notices. If independent automation has advanced, reconcile its pending segments without replaying completed releases.

Cursor7 discovery batches20/21 and reviewed batches26/27 are closed. Do not repeat cursor6 batches18/19 or reviewed batches24/25. No UI, minimum-investment, billing, accounts, ads, spending or permissions changes belong to this backend continuation.

**Product UI workstream — V2 live and verified, PR #209:** the requested light directory/detail redesign is published. Its separate release evidence and follow-up notes remain in [docs/UI_DESIGN_HANDOFF.md](docs/UI_DESIGN_HANDOFF.md).

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

For a live receipt, run `scripts/verify-bse-publication.mjs` with `--manifests=<comma-separated reviewed paths>` and `--output-dir=<artifact directory>`. It fails on unavailable/malformed snapshots or mismatches and never imports IPO records.

## Historical handoffs

The preceding README and status are preserved byte-for-byte in [docs/archive/README-before-cursor7-publication.md](docs/archive/README-before-cursor7-publication.md) and [docs/archive/PROJECT_STATUS-before-cursor7-publication.md](docs/archive/PROJECT_STATUS-before-cursor7-publication.md). Older archives and verification receipts remain unchanged. Archived next-task instructions are not current instructions.
