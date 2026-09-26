# IPO Tracker

A source-first Indian IPO research website with automated official-source collection and GitHub Pages publication.

- Repository: `Vasuki8/IPO-Tracker`; default branch: `main`.
- Website: https://vasuki8.github.io/IPO-Tracker/
- [Explore IPOs](index.html) · [DRHP filings](drhp.html).
- Public IPO dataset: `data/ipos.json`, generated from retained evidence under `data/recovery/`.
- Separate DRHP observations: `data/drhp-filings.json`.
- Development contract: [docs/DEVELOPMENT_PROCESS.md](docs/DEVELOPMENT_PROCESS.md).
- Current handoff: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).
- UI design handoff: [docs/UI_DETAIL_NAVIGATION_HANDOFF.md](docs/UI_DETAIL_NAVIGATION_HANDOFF.md).

## Product and data rules

Coverage spans 2020–2026 but is incomplete. Stored record counts are not proof of official IPO-universe completeness.

The active application-term requirement is **Lot Size only**. Display verified market lot first, then verified minimum bid quantity when market lot is missing. Keep the raw fields distinct. Minimum investment/application amount remains out of scope.

Never invent missing values or use price-times-quantity arithmetic to fill them. Preserve official sources, document identity, dates, hashes when retained, nulls, conflicts and correction history. A final Prospectus is not required for inclusion. Repair retained recovery evidence rather than hand-editing `data/ipos.json`.

The DRHP directory is a separate filing-discovery list. A draft filing does not automatically create an IPO record or establish approval, opening, completion or listing. Current coverage is explicit 2026 DRHP/UDRHP markers from SEBI's draft-offer section, not a complete register.

## Automation

The existing hourly `update-ipos.yml` collects NSE/SEBI data and imports reviewed BSE and NSE evidence. Historical PDF recovery and the bounded BSE notice cursor run independently. `deploy-pages.yml` publishes the site. Workflow files define actual schedules and execution.

`update-drhp.yml` refreshes the separate DRHP list daily at **06:43 UTC**, subject to GitHub Actions scheduling. Collection is bounded to 16 pages and continues to the prior-year boundary. Previously observed filings remain retained when absent from a later scan; missing rows are not treated as withdrawals. Original source pages are kept in the workflow artifact. Collection failure retains the last good dataset and records a separate status in `ops/drhp-collection.json`. Successful refreshes verify the actual served DRHP dataset and directory assets.

`verify-bse-publication.yml` is a read-only post-publication check for selected reviewed BSE manifests. Its default remains parser-v1.5 recovered reviewed batch36. `verify-reviewed-nse-publication.yml` is the corresponding NSE check after successful source sync and now selects **batch9**. Both retain actual Pages bytes and separate fetch/check/generation timestamps; neither imports records.

`audit-ipo-universe.yml` is a read-only bounded official-universe audit with no schedule. It collects eight NSE/BSE/SEBI source surfaces, verifies source hashes and reconciles identities while retaining incomplete-coverage labels. Candidates are not automatically imported. Raw Actions artifacts expire after 14 days; durable review projections and evidence references remain in the repository.

Collection time, source observation, dataset generation and Pages publication are distinct. `node scripts/operator-report.mjs` reports IPO operational health without rewriting values. DRHP collection health is separate.

## Handoff for the next prompt

**The interrupted identity/DRHP release is complete: PR #248 and PR #249 are merged and verified. Do not replay batches 1–9.**

The [DRHP directory](drhp.html) contains **89 companies / 90 unique 2026 DRHP or UDRHP filings**. Actual served data and all four page assets matched published bytes at **2026-09-26T02:57:48.027Z**. Source refresh **36213264969** succeeded; publication commit **43fbd1f519701fe8b149cf7038f76e3709a1a5dd**. Dataset SHA-256: `a74943eca9e7bc66d0e791b25f9c59b2347ae37609d4448bfd0f3e373bf51b38`.

**Paras Healthcare** is preserved from the earlier source-backed list. The latest eight-page scan contained 93 observations but only 89 unique filings; one earlier retained filing brings the union to 90. SEBI page totals varied between 2,214 and 2,212, so the site explicitly labels incomplete coverage. Older years, unlabelled draft rows, exchange-only filings, addenda and corrigenda are outside this release's scope. Do not repeat the superseded 92/91 observation counts as distinct filings.

**AMIRCHAND and LEAP are resolved.** Official identity evidence establishes AMIRCHAND / INE05TO01019 and LEAPIND / INE00GO01025; LEAP remains the IPO lookup symbol, distinct from trading symbol LEAPIND. The retained actual IPO snapshot fetched **2026-09-26T02:21:48.511Z** contains **1,323 records** and passes all **105 reviewed issuers / 627 facts**, including **2/2 batch9 issuers and 12/12 facts**. It has no invalid statuses or missing status evidence. This is the earlier IPO snapshot, not a new 02:57 UTC IPO fetch; subsequent routine historical fills on main remain separate from this DRHP-only repair.

Final-head CI, merged-main data-contract tests and local retained-source regressions passed. Exact fetched DRHP assets were rendered offline at 320/375/1440 pixels, with search, empty/error/retry, failed-refresh preservation and mobile navigation passing without page overflow. Actual remote byte verification was performed by Actions; the browser checks used retained JSON test doubles.

[Combined live receipt](docs/verification/drhp-identity-release-live-2026-09-26.json) · [Current review/hold state](data/discovery/nse-universe-current-review-2026-09-26.json).

### Exact next backend task

Review **ADANIENPP1 and SILGOPP** offering/security histories with independent official issuer/exchange evidence, then GICL, VITAL and KOTYARK. Reconcile latest main/Pages, preserve prior IPOs and conflicts, and do not infer a security type from its symbol.

Current accounting is **105 approved IPOs, nine excluded debt/migration events and five unresolved cases out of 119 pinned groups**. Original September 25 canonical/hold files are historical snapshots; use the September 26 current-state file for new work. This is not full-universe completeness.

Separately review original historical IPO coverage for the nine excluded-event issuers. Fabino's BSE listing-year hold, BSE issue-summary, SEBI historical pagination and NSE-series gaps remain. BSE parser v1.5 is **236/236 parsed**; do not replay its cursor. UI/research-depth work remains in its own handoff. No minimum-investment, billing/accounts/ads, spending or access-policy expansion.

## Local checks

```bash
node scripts/test-sync-sebi-drhp.mjs
node scripts/test-drhp-integrity.mjs
node scripts/test-drhp-ui.mjs
node scripts/test-reviewed-nse-ipos.mjs
node scripts/test-reviewed-nse-publication.mjs
node scripts/apply-reviewed-nse-ipos.mjs --check
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

A successful audit can still have partial source coverage; inspect source gaps and `full_universe_complete`. For BSE receipts, use `scripts/verify-bse-publication.mjs` with `--manifests=<reviewed paths>` and `--output-dir=<artifact directory>`.

For the selected NSE release and DRHP directory, verify actual Pages without importing:

```bash
node scripts/verify-reviewed-nse-publication.mjs --manifest=data/verified-nse-ipos/2026-09-25-batch9.json --output-dir=/tmp/nse-publication
node scripts/verify-drhp-publication.mjs --output-dir=/tmp/drhp-publication
```

## Historical handoffs

The immediately preceding README and status are archived byte-for-byte in [docs/archive/README-before-drhp-identity-finalization.md](docs/archive/README-before-drhp-identity-finalization.md) and [docs/archive/PROJECT_STATUS-before-drhp-identity-finalization.md](docs/archive/PROJECT_STATUS-before-drhp-identity-finalization.md). Earlier archives and receipts remain intact. Archived next-task instructions are not current instructions.
