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

**Latest completed batch: all four held historical BSE listings resolved and published — PR #177.**

PR #177 merged as `e142d031eca66481c41428b65384b7cb0eb6b748` and closes the remaining source/identity holds from the first historical BSE discovery reconciliation.

Two distinct official-source repairs were required:

- **AUTOFURNISH LIMITED, MEHUL TELECOM LIMITED and TIPCO ENGINEERING INDIA LIMITED:** their official BSE listing PDFs are valid but page 2 is image-only, so `pdftotext` cannot recover the listing facts. A narrowly scoped `official_listing_pdf_visual_review` evidence contract now accepts only the exact official BSE listing-PDF URL, immutable document SHA-256, reviewed page 2, exact candidate identity, positive market-lot/price values and explicit visual source strings. No OCR-derived or index-inferred values are accepted.
- **RECODE STUDIOS LIMITED:** original BSE notice `20260511-16` explicitly says the listing date/security details will follow in a separate notice. The corrected issuer-specific listing notice is `20260511-46`, independently verified from the official BSE PDF. The original notice remains preserved as correction history.

Reviewed evidence:

- `data/verified-bse-listings/2026-09-24-batch7.json` — Autofurnish, Mehul Telecom, Tipco Engineering India
- `data/verified-bse-listings/2026-09-24-batch8.json` — Recode Studios
- corrected Recode discovery: `data/discovery/bse-listing-candidates-2026-09-24-batch7.json`
- image-only source artifact: `10789439895` / SHA-256 `d78e344277d79ccce4411e3a7f4552b3eeb87089e3d584d8a1fa8a5c746d1acb`
- corrected Recode source run: `35957926014`
- corrected Recode artifact: `10791635591` / SHA-256 `08edc97e797cfba08fcb33cd83ba476a15217eb669f12eee6746a560d8c760dc`

Final PR validation passed:

- reviewed-evidence/importer CI: `35958072837`
- full data-contract CI: `35958072891`
- BSE source verification: `35958072853`

The isolated publication rehearsal proved **964 -> 968**, exactly **4 additions**, all 964 existing records unchanged, **0 holds/conflicts**, and an idempotent rerun. The reviewed BSE registry now contains **46 retained entries**.

Production sync `35958207898` succeeded:

- reviewed BSE import: **4 added / 42 already present / 0 holds**
- semantic publication: **4 added / 35 changed / 0 removed / 0 conflicts**
- source-backed data commit: `93f4e0b02141c66d547e94b2f184dccaebe39d26`
- operator-state commit: `69aa8fb5e348a7de55b167fdd403c38c7ebb9ea1`
- operator health: **healthy**
- production: **968 total records / 84 records for 2026**
- 2026 board coverage: **15 mainboard / 59 SME / 10 unknown**

Current `main` contains each repaired issuer exactly once with verified listing date, market lot and issue price:

- Autofurnish — code 544767, 2026-05-29, lot 3,000, INR 41
- Recode Studios — code 544755, 2026-05-12, lot 800, INR 158
- Mehul Telecom — code 544751, 2026-04-24, lot 1,200, INR 98
- Tipco Engineering India — code 544740, 2026-04-01, lot 1,600, INR 89

Unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null.

GitHub Pages build `35958746456` succeeded on operator commit `69aa8fb5e348a7de55b167fdd403c38c7ebb9ea1`, which descends directly from the 968-record source-backed data commit.

**The first historical discovery batch is now fully resolved:** its 23 references consist of 6 issuers already present at reconciliation time plus 17 recovered and published through reviewed issuer-specific evidence. There are no remaining held candidates from that batch.

**Next:** re-read the durable historical BSE cursor before doing more recovery work. At this handoff it remains **40/236 parsed with 196 unseen**, next unseen notice `20260107-29`. The scheduled cursor is independent; once it advances, reconcile the newest completed discovery batch against the current 968-record universe, then verify/materialize only genuinely missing issuers. If it still has not advanced when the next run starts, inspect the cursor workflow schedule/operational state rather than repeating the now-closed first batch.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for the evidence contracts, exact source hashes, correction history, tests and production verification.

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
