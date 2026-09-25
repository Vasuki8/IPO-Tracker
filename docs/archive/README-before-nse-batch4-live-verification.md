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

**NSE universe batch3 is VERIFIED LIVE.** Do not repeat its source review or import.

PR #235 merged the reviewed batch; the retained result is **13 published initial public equity IPOs / 78 explicit facts** from the 15-candidate APSISAERO-to-SIMCA queue. **AMIRCHAND remains held** for missing issuer identity metadata and **10MWL29 is excluded as debt**. Evidence: [data/discovery/nse-universe-batch3-review-2026-09-25.json](data/discovery/nse-universe-batch3-review-2026-09-25.json).

The actual served Pages snapshot fetched at **2026-09-25T16:55:27.249Z** contains **1,256 records**. Batch3 verification passed **13/13 issuers, 78/78 facts, 0 failures**. Compared with the preceding verified 1,243-record snapshot: **13 added, 0 removed, 0 existing records changed**. All 1,256 records have one of `open/upcoming/closed/listed` plus status evidence; Unknown/invalid status count is **0**. Live snapshot SHA-256: `74031fbbac15e9fff5b6e510a23df45c435e2eecf1c9257b064cc9c42ecf3932`. Durable receipt: [docs/verification/nse-universe-batch3-live-publication-2026-09-25.json](docs/verification/nse-universe-batch3-live-publication-2026-09-25.json).

Publication used data commit `d24291331f15e7f346977790e77b02c2c528c230`; retained repair verifier run `36163697372` and actual Pages deployment `36163746445` both succeeded. The temporary publication-repair workflow was removed after verification.

### Reliability note

The original normal source sync `36160239429` became abnormally long-running in optional NSE all-fields enrichment. PR #236, merged as `50fbd2ef2ed4176515607c35e787dfbd0d21f31f`, now limits that optional enrichment to an **8-minute best-effort budget**; unprocessed fields stay missing and are retried later.

Replacement sync `36163462983` failed independently in historical NSE materialization because an official request timed out. At the start of the next backend run, inspect the latest scheduled sync. If that same timeout repeats, add bounded retry/fail-closed handling to the historical collector rather than weakening data evidence rules.

### Exact next backend task

Review [data/discovery/ipo-universe-review-2026-09-25-batch4.json](data/discovery/ipo-universe-review-2026-09-25-batch4.json): **15 candidates from RFBL through SHREEDHAR**. Reconcile against latest main and the verified live universe; independently establish offering type and identity; no aggregate-feed-only imports. **QMSMEDI** and **12VPT28A** are explicit prior-offer/security-type review signals.

Separate holds remain **AMIRCHAND, ADANIENPP1, Fabino Life Sciences, GICL, SILGOPP, VITAL and KOTYARK**. The canonical queue has **74 remaining eligible source groups, not 74 confirmed IPOs**. Broader BSE/SEBI/NSE-series gaps remain; BSE parser v1.5 remains 236/236 parsed.

No UI, minimum-investment expansion, billing, accounts, ads, spending or permission changes belong to this backend continuation. Product UI work remains documented separately in [docs/UI_DETAIL_NAVIGATION_HANDOFF.md](docs/UI_DETAIL_NAVIGATION_HANDOFF.md).

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
