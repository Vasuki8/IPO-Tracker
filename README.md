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

The existing hourly `update-ipos.yml` collects NSE/SEBI data and imports reviewed BSE and NSE evidence. Historical PDF recovery and the bounded BSE notice cursor run independently. `deploy-pages.yml` publishes the site. Workflow files define actual schedules and execution.

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. It fetches the actual Pages dataset, retains original bytes/hash and separate observation time, and checks issuer identity, values, source metadata and retained provenance. Its current default remains parser-v1.5 recovered reviewed batch36.

`verify-reviewed-nse-publication.yml` is the corresponding **read-only NSE post-publication check**, triggered after successful source sync. It now selects the batch3 manifest and retains actual Pages bytes, source revision, hashes and separate fetch/check/generation times.

`audit-ipo-universe.yml` is a **read-only bounded official-universe audit**, with no schedule. It runs manually or when relevant audit code/fixtures change. It collects eight NSE/BSE/SEBI source surfaces, verifies source hashes, reconciles exact issuer identities and records incomplete source coverage. Outputs include original responses, `sources.json`, `audit.json`, `audit-compact.json` and an exact source archive. Workflow artifacts expire after 14 days. No candidates are automatically imported.

Collection time, source business observation time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**NSE universe batch3 is MERGED AND TESTED; live publication verification remains pending.** Handoff recorded `2026-09-25T16:35:52Z`. The release must not be called fully verified yet.

PR #235 merged as `2927fe2ed273db9c8a1fe72b3b21543a19003872`. Final-head CI passed (`36160049319`, `36160049332`), and the full data-contract suite also passed on merged main (`36160239490`).

### Completed review and implementation

Reviewed 15 candidates: **13 independently verified initial public equity IPOs approved**, **AMIRCHAND held for missing issuer-identity metadata**, and **10MWL29 excluded as a debt security**. Approved symbols: APSISAERO, RSL, INNOVISION, GSPCROP, CMPDI, POWERICA, SAIPARENT, VIVIDEL, ADISOFT, AMBAAUTO, KISSHT, VALUE360, SIMCA.

The retained manifest contains **78 explicit facts**: 13 listing dates, 26 offer dates, 13 final prices, 13 price bands, 6 market lots and 7 minimum bid quantities. The importer now handles explicit revised offer-period/price-band labels and apostrophe-only issuer-name variants without relaxing other identity or conflict checks. Source review: [data/discovery/nse-universe-batch3-review-2026-09-25.json](data/discovery/nse-universe-batch3-review-2026-09-25.json).

The isolated rehearsal passed **1,243 -> 1,256**, exactly 13 additions, no removals, all prior records unchanged and an idempotent rerun. **1,256 is a rehearsal result, not a verified live count.** All three reviewed NSE batches pass the rehearsal: 38 issuers / 227 facts.

### Remaining release gate — do this first

Production sync **`36160239429`** applied the reviewed NSE batch successfully but was still in **Extract NSE Issue Information fields in one pass** at handoff. Its source-backed publication step was not yet complete. Do not confuse the code merge or an earlier Pages deployment with publication of these 13 records.

First inspect that sync, the resulting Pages deployment and the automatically triggered **Verify reviewed NSE IPO publication** run. Fetch the verifier's retained actual Pages snapshot and confirm all 13 issuers / 78 facts, global status evidence, record count and exact baseline delta. Then retain the live receipt and update this handoff. Do not repeat the completed source review/import.

The **last independently verified live baseline** remains 1,243 records with 0 Unknown statuses, fetched `2026-09-25T15:53:38.128Z`; this is historical baseline evidence, not a new live claim. Release state: [docs/verification/nse-universe-batch3-release-status-2026-09-25.json](docs/verification/nse-universe-batch3-release-status-2026-09-25.json).

### After batch3 is verified

The next queue is [data/discovery/ipo-universe-review-2026-09-25-batch4.json](data/discovery/ipo-universe-review-2026-09-25-batch4.json): **15 candidates from RFBL through SHREEDHAR**, explicitly gated on batch3 live verification. Reconcile against latest main and independently establish offering type and issuer identity; no aggregate-feed-only imports. QMSMEDI and 12VPT28A need specific prior-offer/security-type review, not classification from a symbol alone.

Separate holds remain AMIRCHAND, ADANIENPP1, Fabino Life Sciences, GICL, SILGOPP, VITAL and KOTYARK. The canonical queue has 74 remaining eligible source groups, **not 74 confirmed IPOs**. Broader BSE/SEBI/NSE-series coverage gaps remain. BSE parser v1.5 remains 236/236 parsed; do not replay that cursor.

No UI, minimum-investment expansion, billing, accounts, ads, spending or permission changes belong to this continuation. Product UI V2 remains separate: [docs/UI_DESIGN_HANDOFF.md](docs/UI_DESIGN_HANDOFF.md).

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
