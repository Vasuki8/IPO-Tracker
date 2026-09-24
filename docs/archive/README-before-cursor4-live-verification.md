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

**Latest completed batch: repaired cursor3 BSE references reconciled, verified and published — PR #184.**

PR #184 merged as `d08479a3c12cd5975902dfa5f689a22adc90b008`.

The 12 listing references recovered by parser v1.2.0 were reconciled against the then-current **258-record 2025 recovery universe** and **1,014-record public dataset**:

- **1 already present exact identity:** 3B Films Limited, already backed by BSE listing notice `20250605-49`, listing date 2025-06-06, market lot 3,000 and issue price INR 50.
- **11 genuinely missing exact identities.**
- **0 ambiguous / identity-review collisions.**
- no fuzzy-name equivalence accepted.

Machine-readable reconciliation:

- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor3-repaired.json`
- pinned verifier batch: `data/discovery/bse-listing-candidates-2026-09-24-batch12.json`

Issuer-specific BSE verification completed **11/11 verified, 0 rejected, 0 unavailable**. Canonical listing-PDF archive paths were unavailable for this batch, so reviewed evidence uses the strict official-BSE-notice HTML contract already used by the prior cursor3 release.

Reviewed publication:

- `data/verified-bse-listings/2026-09-24-batch17.json`
- source verification run: `35968091282`
- source artifact: `10795017902`
- artifact ZIP SHA-256: `98e381697404285d1b521926bc6f81ba8cad4d5b42f43022b4952a1011521036`
- final PR source re-verification: `35968733466` — 11/11
- final PR artifact: `10795735136` / SHA-256 `81d0ee8859e2dfee5998a98e30ec68067e95799f0a8db640ae375800b72c21ff`

Published facts:

| Issuer | Listing date | Market lot | Issue price |
| --- | --- | ---: | ---: |
| ASSTON PHARMACEUTICALS LIMITED | 2025-07-16 | 1,000 | INR 123 |
| GLEN INDUSTRIES LIMITED | 2025-07-15 | 1,200 | INR 97 |
| META INFOTECH LIMITED | 2025-07-11 | 800 | INR 161 |
| CRYOGENIC OGS LIMITED | 2025-07-10 | 3,000 | INR 47 |
| UNIFIED DATA TECH SOLUTIONS LIMITED | 2025-05-29 | 400 | INR 273 |
| SRIGEE DLM LIMITED | 2025-05-12 | 1,200 | INR 99 |
| MANOJ JEWELLERS LIMITED | 2025-05-12 | 2,000 | INR 54 |
| KENRIK INDUSTRIES LIMITED | 2025-05-09 | 6,000 | INR 25 |
| SPINAROO COMMERCIAL LIMITED | 2025-04-08 | 2,000 | INR 51 |
| INFONATIVE SOLUTIONS LIMITED | 2025-04-08 | 1,600 | INR 79 |
| RETAGGIO INDUSTRIES LIMITED | 2025-04-07 | 6,000 | INR 25 |

Real importer rehearsal proved **1,014 -> 1,025**, exactly **11 additions**, all 1,014 existing records unchanged, **0 holds/conflicts**, and an idempotent rerun.

Production sync `35969070759` succeeded:

- reviewed BSE import: **11 added / 92 already present / 0 holds / 0 identity conflicts**
- semantic publication: **11 added / 45 changed / 0 removed / 0 conflicts**
- source-backed data commit: `53589374e3078540394866180b467bf7fb1442ad`
- operator-state commit: `8cd16c9a2ca45bc38ef239d81b455de7276d225d`
- schema 1.2.0 validation: **1,025 records passed**
- operator health: **healthy**
- production: **1,025 total records**
- 2025: **269 records**
- 2026: **85 records**

The 45 changed records were normal concurrent official NSE/SEBI enrichment; the semantic publisher separately identified exactly 11 additions and zero removals/conflicts.

Post-publication audit confirmed every batch17 issuer occurs exactly once in recovery and public data, and every listing date, market lot, issue price, exact source URL, source-document SHA-256 and batch17 provenance matches reviewed evidence. Unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null.

GitHub Pages build `35969750035` succeeded on final operator revision `8cd16c9a2ca45bc38ef239d81b455de7276d225d`.

### Current historical cursor

The durable BSE SME addition-notice cursor has **not advanced** since the repaired segment:

- parser: **1.2.0**
- **80 tracked / 236 eligible**
- **80 parsed**
- **0 failed/unparseable**
- **156 unseen**
- next unseen notice: **`20250403-16`**

**Next:** always re-read `ops/bse-sme-addition-notices.json` first. If the cursor has advanced beyond 80 tracked notices, reconcile only the newest completed segment against the current 1,025-record universe. If it is unchanged, the next bounded historical discovery work begins with the unseen segment starting at `20250403-16`; use the existing independent backfill workflow, then reconcile its newly parsed references before issuer-specific verification/publication. Do not repeat batch12/batch17 or the parser-repair work.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for exact evidence, release verification and the next-task acceptance criteria.

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
