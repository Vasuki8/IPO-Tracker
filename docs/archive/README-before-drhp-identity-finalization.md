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

`verify-reviewed-nse-publication.yml` is the corresponding **read-only NSE post-publication check**, triggered after successful source sync. It now selects the batch8 manifest and retains actual Pages bytes, source revision, hashes and separate fetch/check/generation times.

`audit-ipo-universe.yml` is a **read-only bounded official-universe audit**, with no schedule. It runs manually or when relevant audit code/fixtures change. It collects eight NSE/BSE/SEBI source surfaces, verifies source hashes, reconciles exact issuer identities and records incomplete source coverage. Outputs include original responses, `sources.json`, `audit.json`, `audit-compact.json` and an exact source archive. Workflow artifacts expire after 14 days. No candidates are automatically imported.

Collection time, source business observation time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Batch8 is VERIFIED LIVE. Do not replay the approved imports from batches 1–8.** PR #245 reviewed the final 14 pinned candidate groups: **12 approved equity IPOs, DOLLEX excluded as migration, 13DCCL28 excluded as debt, zero new holds**. The manifest retains **71 explicit facts**. Existing parsers handled the batch without changes. VINOD's explicit Rs.94 fixed price retains a null band and null minimum bid; its market lot is 1,200.

Actual Pages fetched **2026-09-25T21:14:56.192Z** contains **1,321 records**, with **12/12 batch8 issuers and 71/71 facts** matching. All eight reviewed batches pass **103 issuers / 615 facts**. Unknown/invalid statuses and missing status evidence are both **0**. Snapshot SHA-256 `704b89e1ff652353af29acf2790d1aee93a3b12fad083c6b4bca052622f37000`. [Durable live receipt](docs/verification/nse-universe-batch8-live-publication-2026-09-25.json).

Normal sync **36188314026** and actual Pages verifier **36189922895** succeeded; operator health **healthy**. Data commit **519c0fd8efb5db650f245aa17e5a368ca57b995b**. Exactly **12 additions / zero removals**. **1,305 of 1,309 prior records were unchanged**; the receipt separately records routine changes and optional enrichments rather than presenting them as manually reviewed batch facts.

Final-head and merged-main CI passed. Regressions reject **21 source mutations and four cross-year collisions**, and cover pre/post-publication execution, preservation, idempotency, fixed-price/null-band rules, positive exclusions and read-only behavior. The exact post-publication snapshot passed regression/build/schema checks with source files unchanged. [Rehearsal](docs/verification/nse-universe-batch8-rehearsal-2026-09-25.json).

### Exact next task

The [canonical review summary](data/discovery/nse-universe-canonical-review-2026-09-25.json) accounts for all **119 pinned groups: 103 approved IPOs, nine excluded debt/migration events, seven unresolved cases**. No unreviewed group remains in that queue; this is **not full-universe completeness**.

Begin the [held-candidate queue](data/discovery/ipo-universe-held-review-2026-09-25.json) with **AMIRCHAND and LEAP missing-identity review**, using independent official issuer/exchange evidence. Then resolve ADANIENPP1, GICL, SILGOPP, VITAL and KOTYARK offering/history conflicts. Preserve uncertainty rather than invent identity or terms.

A separate follow-up must assess the **original historical IPOs of the nine excluded-event issuers**: no exact normalized-name matches were found in checked recovery/Pages. Exclusion of a 2026 debt or migration event must not silently exclude an original historical equity IPO. Reconcile aliases and original offering year before any approval. Fabino's BSE listing-year hold and broader BSE/SEBI/NSE-series gaps remain; BSE parser v1.5 is 236/236 parsed. UI/research work remains in [its own handoff](docs/UI_DETAIL_NAVIGATION_HANDOFF.md).

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
node scripts/verify-reviewed-nse-publication.mjs --manifest=data/verified-nse-ipos/2026-09-25-batch8.json --output-dir=/tmp/nse-publication
```

## Historical handoffs

The immediately preceding README and status are archived byte-for-byte in [docs/archive/README-before-nse-batch8-live-verification.md](docs/archive/README-before-nse-batch8-live-verification.md) and [docs/archive/PROJECT_STATUS-before-nse-batch8-live-verification.md](docs/archive/PROJECT_STATUS-before-nse-batch8-live-verification.md). Earlier archives and verification receipts remain intact. Archived next-task instructions are not current instructions.
