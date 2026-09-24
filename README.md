# IPO Tracker

A source-first Indian IPO research website with automated official-source collection and GitHub Pages publication.

- Repository: `Vasuki8/IPO-Tracker`; default branch: `main`.
- Website: https://vasuki8.github.io/IPO-Tracker/
- Public dataset: `data/ipos.json`, generated from retained evidence under `data/recovery/`.
- Development contract: [docs/DEVELOPMENT_PROCESS.md](docs/DEVELOPMENT_PROCESS.md).
- Current handoff and verification: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Product and data rules

Coverage includes records across 2020-2026, but the historical universe and field coverage remain incomplete. Run `node scripts/audit-historical-coverage.mjs` for current per-year counts; do not reuse old milestone counts as current totals.

The active application-term requirement is **Lot Size only**. Display verified market lot first, then verified minimum bid quantity when market lot is missing. Keep the raw fields distinct. Minimum investment/application amount remains out of scope.

Never fill missing data with guesses or price x quantity arithmetic. Preserve source URLs, document identity, reporting dates, collection timestamps, nulls, conflicts and correction history. A final Prospectus is not required for inclusion; use the best available official evidence for each field. Do not edit `data/ipos.json` instead of repairing retained recovery evidence.

## Automation

| Workflow | Purpose |
| --- | --- |
| `update-ipos.yml` | Hourly NSE/SEBI collection, reviewed BSE evidence import and source-backed publication |
| `backfill-historical-offer-dates.yml` | Independent historical PDF offer-date recovery |
| `backfill-historical-pdf-fields.yml` | Independent historical PDF field recovery |
| `audit-bse-sme-universe.yml` | Read-only BSE SME constituent and addition-notice audits |
| `backfill-bse-sme-addition-notices.yml` | Durable parser-versioned historical BSE SME notice discovery cursor |
| `verify-bse-listing-candidates.yml` | Bounded independent verification of pinned BSE listing candidates |
| `validate-reviewed-bse-listings.yml` | Offline identity, PDF safety, reviewed evidence and importer tests |
| `validate-data.yml` | Existing pull-request/push tests and data-contract checks |
| `deploy-pages.yml` | Website deployment and publication-health recording |

Collection time, dataset generation and Pages publication are separate signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values. Workflow files are authoritative for actual execution.

## Handoff for the next prompt

**Latest completed batch: six historical BSE SME listings published — PR #175.**

PR #175 preserved the existing strict reviewed-evidence importer and added a safe PDF-upgrade probe for issuer-specific notices that initially verified through official BSE HTML.

From PR #174's 13 verified historical candidates:

- **6 have official BSE listing PDFs with page-backed evidence and are now reviewed/published**
- **7 remain verified from official BSE HTML, but their canonical archive PDF paths return HTTP 404**
- the prior **4 rejected candidates remain held** and were not published

Published batch manifest:

- `data/verified-bse-listings/2026-09-24-batch4.json`
- source verification run: `35954818300`
- artifact: `10789632860`
- artifact ZIP SHA-256: `3c312c2077a4e8ddfc170c50aa65ea54874ceb53fbfff813fdd882506f4db99f`

The isolated publication rehearsal on final PR validation run `35955058014` proved **951 -> 957**, exactly 6 additions, all 951 existing records unchanged, 0 holds and an idempotent rerun.

Merge-triggered production sync `35955112253` succeeded:

- reviewed BSE import: **6 added / 29 already present / 0 holds**
- semantic publication: **6 added / 37 changed / 0 removed**
- source-backed data commit: `fc5e0ec5e6bd9fb3c065544465066827a4005940`
- operator-state commit: `9c07573b1ca27d48d93724236fbbde30971f11c2`
- operator health: **healthy**
- production: **957 total records / 73 records for 2026**
- 2026 board coverage: **15 mainboard / 48 SME / 10 unknown**

GitHub Pages build `35955643913` succeeded on descendant commit `9c07573b1ca27d48d93724236fbbde30971f11c2`, so the deployed revision contains the six additions.

The seven verified-but-HTML-only notices that remain blocked by archive-PDF 404 are:

- ELFIN AGRO INDIA LIMITED — `20260311-44`
- PAN HR SOLUTION LIMITED — `20260212-30`
- KANISHK ALUMINIUM INDIA LIMITED — `20260203-43`
- ACCRETION NUTRAVEDA LIMITED — `20260203-44`
- MSAFE EQUIPMENTS LIMITED — `20260203-45`
- ARITAS VINYL LIMITED — `20260122-19`
- YAJUR FIBRES LIMITED — `20260113-25`

**Next:** repair the official evidence path for those seven. First look for issuer-notice attachments or alternate official BSE document URLs. If BSE truly exposes only HTML, add a separately reviewed official-HTML evidence contract with response hash and exact excerpts—never fake PDF/page evidence. Keep the four rejected candidates on a separate identity/source-repair track. The independent historical cursor remains at **40/236 parsed with 196 unseen** and must continue separately.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for exact facts, run IDs, source hashes, rejected candidates and deployment evidence.

No UI redesign, minimum-investment work, billing, accounts, ads, paid services or permission changes are part of this handoff.

## Local checks

```bash
node scripts/test-verify-bse-listing-candidates.mjs
node scripts/test-retry-bse-listing-pdf.mjs
node scripts/test-apply-verified-bse-listings.mjs
node scripts/test-bse-publication-rehearsal.mjs
node scripts/apply-verified-bse-listings.mjs --check
node scripts/build-published-data.mjs --check
node scripts/validate-data.mjs
node scripts/audit-historical-coverage.mjs
```

To apply the already reviewed batch locally, run `node scripts/apply-verified-bse-listings.mjs` before rebuilding. This uses no network. The independent BSE PDF verification workflow requires `pdftotext`; its report never writes IPO records automatically.

## Earlier handoffs

PR #165's full verified discovery handoff is preserved in [docs/archive/PROJECT_STATUS-before-bse-listing-batch.md](docs/archive/PROJECT_STATUS-before-bse-listing-batch.md). Earlier accumulated milestones remain unchanged in `docs/archive/`; they are history, not current coverage or instructions.
