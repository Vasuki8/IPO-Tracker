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

`verify-reviewed-nse-publication.yml` is the corresponding **read-only NSE post-publication check**, triggered after successful source sync. It now selects the batch7 manifest and retains actual Pages bytes, source revision, hashes and separate fetch/check/generation times.

`audit-ipo-universe.yml` is a **read-only bounded official-universe audit**, with no schedule. It runs manually or when relevant audit code/fixtures change. It collects eight NSE/BSE/SEBI source surfaces, verifies source hashes, reconciles exact issuer identities and records incomplete source coverage. Outputs include original responses, `sources.json`, `audit.json`, `audit-compact.json` and an exact source archive. Workflow artifacts expire after 14 days. No candidates are automatically imported.

Collection time, source business observation time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**NSE universe batch7 is VERIFIED LIVE.** PR #244 reviewed 15 candidates: **13 approved initial-equity IPOs**, **two debt exclusions (1150VIES30, 12AIL28)** and **no new holds**. The manifest retains **78 explicit facts**. The minimal importer repair reads FASCINATE's explicit extended closing date only when all date representations and independent source dates agree; minimum bid and market lot remain distinct.

Actual Pages fetched **2026-09-25T19:59:16.697Z** contains **1,309 records**. Batch7 passes **13/13 issuers and 78/78 facts**; all seven reviewed NSE batches pass **91 issuers / 544 facts**. Unknown/invalid statuses and missing status evidence are both **0**. SHA-256 `f1b0d662e1dc8a61cd4a821451143e85ea5a6e53425f158431a26953ca8b3df0`. [Durable live receipt](docs/verification/nse-universe-batch7-live-publication-2026-09-25.json).

Normal sync **36181601722** and actual Pages verifier **36182904949** succeeded. Data commit **23dc175bced8bc54a8063f43efa140b2eb979104**; operator health **healthy**. Exactly 13 reviewed identities added, none removed; **1,291 of 1,296 prior records unchanged**. The receipt separately records 5 routine-pipeline record changes and 3 optional field enrichments on the new batch, rather than treating them as reviewed manifest facts.

Final-head and merged-main CI passed. Regressions reject **20 source mutations and four cross-year identity collisions**, and cover pre/post-publication behavior, idempotency, nulls, exclusions and read-only inputs. The exact post-publication snapshot was retested; all **308 archived source files** remained unchanged. [Rehearsal receipt](docs/verification/nse-universe-batch7-rehearsal-2026-09-25.json).

### Exact next backend task

Review [batch8](data/discovery/ipo-universe-review-2026-09-25-batch8.json): **14 candidate issuer groups from SUMAX through SPECTRAA**, the remaining groups in the pinned canonical audit—not 14 confirmed IPOs. **DOLLEX** needs prior-offer/migration review; **13DCCL28** needs independent debt/repeat-security classification; **VINOD** needs fixed-price/null-band verification. Reconcile against latest main and actual Pages before any approval.

Preserve separate prior holds and resolved debt/migration exclusions. Completing this queue is not proof of full IPO-universe coverage: BSE/SEBI/NSE-series gaps remain. BSE parser v1.5 is 236/236 parsed. UI/research-depth work stays in [its own handoff](docs/UI_DETAIL_NAVIGATION_HANDOFF.md). No minimum-investment, billing/accounts/ads, spending or access-policy expansion.

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
node scripts/verify-reviewed-nse-publication.mjs --manifest=data/verified-nse-ipos/2026-09-25-batch7.json --output-dir=/tmp/nse-publication
```

## Historical handoffs

The immediately preceding README and status are archived byte-for-byte in [docs/archive/README-before-nse-batch7-live-verification.md](docs/archive/README-before-nse-batch7-live-verification.md) and [docs/archive/PROJECT_STATUS-before-nse-batch7-live-verification.md](docs/archive/PROJECT_STATUS-before-nse-batch7-live-verification.md). Earlier archives and verification receipts remain intact. Archived next-task instructions are not current instructions.
