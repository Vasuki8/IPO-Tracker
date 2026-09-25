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

`verify-reviewed-nse-publication.yml` is the corresponding **read-only NSE post-publication check**, triggered after successful source sync. It now selects the batch6 manifest and retains actual Pages bytes, source revision, hashes and separate fetch/check/generation times.

`audit-ipo-universe.yml` is a **read-only bounded official-universe audit**, with no schedule. It runs manually or when relevant audit code/fixtures change. It collects eight NSE/BSE/SEBI source surfaces, verifies source hashes, reconciles exact issuer identities and records incomplete source coverage. Outputs include original responses, `sources.json`, `audit.json`, `audit-compact.json` and an exact source archive. Workflow artifacts expire after 14 days. No candidates are automatically imported.

Collection time, source business observation time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**NSE universe batch6 is VERIFIED LIVE.** PR #243 reviewed 15 candidates: **12 independently verified initial-equity IPOs**, **two excluded migrations (ANNAPURNA, SWARAJ)** and **one identity hold (LEAP)**. The approved manifest contains **72 explicit facts**. The two parser repairs recognize literal repeated-per-share bands and Minimum-qualified bid quantities without converting minimum bids into market lots or estimating missing amounts.

Actual Pages fetched **2026-09-25T19:05:14.509Z** contains **1,296 records**, with batch6 **12/12 issuers and 72/72 facts** matching. All six reviewed NSE batches pass **78 issuers / 466 facts**; Unknown/invalid statuses and missing status evidence are both **0**. Normal source sync **36176259835** and actual Pages verifier **36177365928** succeeded. Data commit **b6c169c3481612cc2bf55ed10e72445d3687e89c**; operator health **healthy**. [Durable live receipt](docs/verification/nse-universe-batch6-live-publication-2026-09-25.json).

Exactly 12 approved records were added and none removed. **1,272 of the 1,284 older records were unchanged**. The receipt distinguishes 12 ordinary-pipeline changes: four evidence-backed open-to-closed status transitions, two previously missing Propshop fields, and document additions. Eight older-record changes predated the batch6 merge; four document-only updates came from the release sync. All earlier reviewed facts still match. One new record also received optional MV Electrosystems issue-size enrichment, separate from the 72 reviewed facts.

Live status totals: **listed 1,275 / open 12 / closed 7 / upcoming 2**. Snapshot SHA-256 `0fe577e052a06eef0e477eff7a0530a289b5715d25da42e372fc5071f4e9b1e0`. The exact post-publication snapshot passed local regression/build/schema tests; all 300 archived source files remained byte-identical.

Final-head CI passed, with preservation/idempotency rehearsed before and after publication. Batch6 regressions reject 18 source mutations and four cross-year identity collisions. The 24 original response hashes were checked; a failed standalone circular request is retained separately from the successful official migration disclosures. [Rehearsal receipt](docs/verification/nse-universe-batch6-rehearsal-2026-09-25.json).

### Exact next backend task

Review [batch7](data/discovery/ipo-universe-review-2026-09-25-batch7.json): **15 candidate issuer groups from SKYTECH through 12AIL28**. Reconcile against latest main and actual Pages before independently establishing offering type and identity. **1150VIES30 and 12AIL28** combine 2024 offer terms with 2026 listing dates and incompatible price observations; both require explicit debt/repeat-security investigation. **FASCINATE** needs its observed extended-length offer window checked against literal official dates.

The canonical audit has **29 remaining candidate issuer groups, not 29 confirmed IPOs**. New hold LEAP joins AMIRCHAND, ADANIENPP1, Fabino Life Sciences, GICL, SILGOPP, VITAL and KOTYARK. Keep resolved migrations/debt exclusions out of the new equity-IPO queue. Broader BSE/SEBI/NSE-series gaps remain; BSE parser v1.5 is 236/236 parsed. UI/research-depth work stays in [its own handoff](docs/UI_DETAIL_NAVIGATION_HANDOFF.md). No minimum-investment, billing/accounts/ads, spending or access-policy expansion.


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
node scripts/verify-reviewed-nse-publication.mjs --manifest=data/verified-nse-ipos/2026-09-25-batch6.json --output-dir=/tmp/nse-publication
```

## Historical handoffs

The immediately preceding README and status are archived byte-for-byte in [docs/archive/README-before-nse-batch6-live-verification.md](docs/archive/README-before-nse-batch6-live-verification.md) and [docs/archive/PROJECT_STATUS-before-nse-batch6-live-verification.md](docs/archive/PROJECT_STATUS-before-nse-batch6-live-verification.md). Earlier archives and verification receipts remain intact. Archived next-task instructions are not current instructions.
