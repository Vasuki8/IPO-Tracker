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

`verify-reviewed-nse-publication.yml` is the corresponding **read-only NSE post-publication check**, triggered after successful source sync. It now selects the batch3 manifest and retains actual Pages bytes, source revision, hashes and separate fetch/check/generation times.

`audit-ipo-universe.yml` is a **read-only bounded official-universe audit**, with no schedule. It runs manually or when relevant audit code/fixtures change. It collects eight NSE/BSE/SEBI source surfaces, verifies source hashes, reconciles exact issuer identities and records incomplete source coverage. Outputs include original responses, `sources.json`, `audit.json`, `audit-compact.json` and an exact source archive. Workflow artifacts expire after 14 days. No candidates are automatically imported.

Collection time, source business observation time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**NSE universe batch4 is VERIFIED LIVE.** Do not repeat its source review or import.

PR #240 reviewed 15 candidates: **13 independently verified initial public equity IPOs were published**, **QMSMEDI was excluded as an NSE Emerge-to-Main-Board migration**, and **12VPT28A was excluded as debt**. The batch retains **78 explicit facts**: 13 listing dates, 26 offer dates, 13 final prices, 13 price bands, 10 market lots and 3 minimum bid quantities.

Source review run `36165195790` retained 20 official source files; artifact `10877286718`, SHA-256 `7aa33f4f7066e20a246a5da8328e8271759b4f2b2356b6ae4eed6cdec93185ad`. Successful retained-source materialization run `36166287987` rehearsed **1,256 -> 1,269**, exactly 13 additions, no removals and an idempotent rerun. Durable rehearsal: [docs/verification/nse-universe-batch4-rehearsal-2026-09-25.json](docs/verification/nse-universe-batch4-rehearsal-2026-09-25.json).

The normal production sync `36166656023` then completed successfully end-to-end, including the historical NSE stage that had timed out in the preceding run. Data commit: `35166cf76ee03fb580d53e75898b030f7cc1f9c6`; operator state: **healthy**.

Actual Pages verifier `36167470675` passed **13/13 issuers, 78/78 facts, 0 failures**. The served snapshot fetched `2026-09-25T17:30:44.748Z` contains **1,269 records**, with **0 Unknown/invalid statuses** and status evidence on every record. Snapshot SHA-256: `228b3a1861836dbce8e344313a82035d9e7ed38bcd2a09c31f4dcd822047c6b5`. Durable live receipt: [docs/verification/nse-universe-batch4-live-publication-2026-09-25.json](docs/verification/nse-universe-batch4-live-publication-2026-09-25.json).

Against the preceding 1,256-record live baseline, batch4 added exactly 13 records and removed none. Two unrelated older records received normal SEBI document attachments (Euro Pratik Sales and Ivalue Infosolutions); no prior displayed IPO field/value/status changed.

### Exact next backend task

Review [data/discovery/ipo-universe-review-2026-09-25-batch5.json](data/discovery/ipo-universe-review-2026-09-25-batch5.json): **15 candidate source groups from TEJA through JNPR**.

Symbols: **TEJA, VMOBILE, KNACK, ICELCO, KUSUMGAR, HAPPY, LASERPOWER, SBIFUNDS, CMLL, METALIC, INDOMIM, LCL, PROPSHOP, MANIPALHOS, JNPR**.

Reconcile against latest main and the actual live universe, independently establish offering type and issuer identity, retain nulls/conflicts, and do not import from the aggregate NSE past-issues feed alone. The canonical audit has **59 remaining eligible source groups, not 59 confirmed IPOs**.

Separate unresolved holds remain **AMIRCHAND, ADANIENPP1, Fabino Life Sciences, GICL, SILGOPP, VITAL and KOTYARK**. **QMSMEDI** and **12VPT28A** are resolved exclusions, not holds. Broader BSE/SEBI/NSE-series gaps remain; BSE parser v1.5 remains 236/236 parsed.

No UI, minimum-investment expansion, billing, accounts, ads, spending or permission changes belong to this backend continuation. Product UI/research-depth work remains documented separately in [docs/UI_DETAIL_NAVIGATION_HANDOFF.md](docs/UI_DETAIL_NAVIGATION_HANDOFF.md).

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
node scripts/verify-reviewed-nse-publication.mjs --manifest=data/verified-nse-ipos/2026-09-25-batch3.json --output-dir=/tmp/nse-publication
```

## Historical handoffs

The immediately preceding README and status are archived byte-for-byte in [docs/archive/README-before-nse-batch3.md](docs/archive/README-before-nse-batch3.md) and [docs/archive/PROJECT_STATUS-before-nse-batch3.md](docs/archive/PROJECT_STATUS-before-nse-batch3.md). Earlier archives and verification receipts remain intact. Archived next-task instructions are not current instructions.
