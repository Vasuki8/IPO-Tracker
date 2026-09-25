# IPO Tracker

A source-first Indian IPO research website with automated official-source collection and GitHub Pages publication.

- Repository: `Vasuki8/IPO-Tracker`; default branch: `main`.
- Website: https://vasuki8.github.io/IPO-Tracker/
- Public dataset: `data/ipos.json`, generated from retained evidence under `data/recovery/`.
- Development contract: [docs/DEVELOPMENT_PROCESS.md](docs/DEVELOPMENT_PROCESS.md).
- Current handoff: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).
- Current UI design handoff: [docs/UI_DETAIL_NAVIGATION_HANDOFF.md](docs/UI_DETAIL_NAVIGATION_HANDOFF.md).

## Product and data rules

Coverage spans 2020-2026 but is incomplete. Stored record counts are not proof of official IPO-universe completeness.

The active application-term requirement is **Lot Size only**. Display verified market lot first, then verified minimum bid quantity when market lot is missing. Keep the raw fields distinct. Minimum investment/application amount remains out of scope.

Never invent missing values or use price-times-quantity arithmetic to fill them. Preserve official sources, document identity, dates, hashes when retained, nulls, conflicts and correction history. A final Prospectus is not required for inclusion. Repair retained recovery evidence rather than hand-editing `data/ipos.json`.

## Automation

The existing hourly `update-ipos.yml` collects NSE/SEBI data and imports reviewed BSE and NSE evidence. Historical PDF recovery and the bounded BSE notice cursor run independently. `deploy-pages.yml` publishes the site. Workflow files define actual schedules and execution.

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. It fetches the actual Pages dataset, retains original bytes/hash and separate observation time, and checks issuer identity, values, source metadata and retained provenance. Its current default remains parser-v1.5 recovered reviewed batch36.

`verify-reviewed-nse-publication.yml` is the corresponding **read-only NSE post-publication check**, triggered after successful source sync. It now selects the batch5 manifest and retains actual Pages bytes, source revision, hashes and separate fetch/check/generation times.

`audit-ipo-universe.yml` is a **read-only bounded official-universe audit**, with no schedule. It runs manually or when relevant audit code/fixtures change. It collects eight NSE/BSE/SEBI source surfaces, verifies source hashes, reconciles exact issuer identities and records incomplete source coverage. Outputs include original responses, `sources.json`, `audit.json`, `audit-compact.json` and an exact source archive. Workflow artifacts expire after 14 days. No candidates are automatically imported.

Collection time, source business observation time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**NSE universe batch5 is VERIFIED LIVE.** PR #242 added **15 independently verified initial public equity IPOs** and **89 explicit facts**, with no new holds/exclusions or production parser changes. TEJA is fixed price; its price band remains null. Market lot, minimum bid quantity and minimum application amount remain distinct.

Actual Pages fetched **2026-09-25T18:16:59.688Z** contains **1,284 records**: batch5 **15/15 issuers and 89/89 facts** match, and all five reviewed NSE batches pass **66 issuers / 394 facts**. Unknown/invalid statuses and missing status evidence are both **0**. SHA-256 `a542ba9d96d621dff867f7310c99d5c74f2864898501c46b214d94db112f1e91`. [Durable live receipt](docs/verification/nse-universe-batch5-live-publication-2026-09-25.json).

Normal source sync **36171237358** succeeded; data commit **`359ea237cda83fed91d7724ddd4ee658efb96ae8`**; actual Pages verifier **36172343065** succeeded. The 15 approved identities were added with no removals. **1,266 of 1,269 existing baseline records were unchanged**; the receipt separately records 3 normal-sync record changes and any optional source enrichment, rather than attributing everything to the reviewed import.

Final-head CI and merged-main data-contract tests passed. New regressions cover pre/post-publication execution, idempotency, fixed-price/null semantics, source mutations and cross-year collisions; the post-publication source snapshot was retested. [Rehearsal receipt](docs/verification/nse-universe-batch5-rehearsal-2026-09-25.json).

### Exact next backend task

Review [batch6](data/discovery/ipo-universe-review-2026-09-25-batch6.json): **15 candidate issuer groups from MVELECTRO through CREDENT**. Reconcile against latest main and actual Pages, then independently establish offering type and identity. **ANNAPURNA and SWARAJ** combine 2022 offer dates with 2026 listing dates and need explicit prior-offer/migration/repeat-security review; they are not approved new IPOs.

The canonical audit has **44 remaining candidate issuer groups, not 44 confirmed IPOs**. Keep prior holds and resolved exclusions separate. Broader BSE/SEBI/NSE-series gaps remain; BSE parser v1.5 is 236/236 parsed. No UI, minimum-investment, billing/accounts/ads, spending or permission work belongs to this backend continuation; UI/research-depth requirements stay in [their own handoff](docs/UI_DETAIL_NAVIGATION_HANDOFF.md).

## Local checks

```bash
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

A successful audit execution can still have **partial source coverage**; always inspect the report's source gaps and `full_universe_complete` flag. For live IPO-publication receipts, use `scripts/verify-bse-publication.mjs` with `--manifests=<reviewed paths>` and `--output-dir=<artifact directory>`. Neither verifier imports IPO records.

For the selected NSE release, verify actual Pages output without importing:

```bash
node scripts/verify-reviewed-nse-publication.mjs --manifest=data/verified-nse-ipos/2026-09-25-batch5.json --output-dir=/tmp/nse-publication
```

## Historical handoffs

The immediately preceding README and status are archived byte-for-byte in [docs/archive/README-before-nse-batch5-live-verification.md](docs/archive/README-before-nse-batch5-live-verification.md) and [docs/archive/PROJECT_STATUS-before-nse-batch5-live-verification.md](docs/archive/PROJECT_STATUS-before-nse-batch5-live-verification.md). Earlier archives and verification receipts remain intact. Archived next-task instructions are not current instructions.
