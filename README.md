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

**Latest completed batch: second historical BSE cursor batch reconciled and published — PR #178.**

PR #178 merged as `17e0c7322d975587de0f640e83215ef68022c33f` and processed the next durable BSE SME index-notice cursor segment.

Cursor source run `35959162509` selected 20 older notices. Current operational state is:

- **60 tracked notices total**
- **59 parsed**
- **1 unparseable** — BSE index notice `20250912-85`, error `no_parseable_listing_reference`
- **176 unseen**
- next unseen notice: **`20250908-25`**

The 19 successfully parsed notices produced **30 listing references**. Cross-year reconciliation against retained 2025 + 2026 recovery found **30 genuinely missing exact identities**, with 0 already-present matches and 0 ambiguous/fuzzy matches accepted.

Retained reconciliation:

- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor2.json`
- cursor artifact: `10791926413`
- cursor artifact SHA-256: `ac543656d4fdfa7f6644ef50e0274d93d8c01a75d5aa28fdd70255881a109209`

The 30 missing issuers were split into two bounded 15-candidate discovery batches:

- `data/discovery/bse-listing-candidates-2026-09-24-batch8.json`
- `data/discovery/bse-listing-candidates-2026-09-24-batch9.json`

Both halves independently verified **15/15** against issuer-specific official BSE listing notices. The canonical archive PDFs were unavailable for these records, so reviewed publication uses the existing strict official-BSE-HTML evidence contract with exact notice URL, response/document hash, normalized evidence text and offline identity/fact replay.

Canonical reviewed manifests are `data/verified-bse-listings/2026-09-24-batch9.json` through `batch14.json`, totaling **30 entries**.

Evidence runs:

- manifest source run: `35959840134`
- manifest source artifact: `10792036701`
- artifact SHA-256: `3d883788e3aa99fd09553869f0850150b0a987174861b292804a021e206e6c94`
- final PR source verification: `35960785399`
- final artifact: `10792048220`
- final artifact SHA-256: `2df53976159ccbaa39558020ddf3c5300f76a286d5bdaea907560105afc7e015`

A bounded parser repair was required for Apollo Techno Industries: BSE writes `December 31 , 2025` with whitespace before the comma. The listing-date grammar now accepts only that harmless spacing variant in addition to the existing date form, with a regression test.

Final PR validation passed:

- reviewed-evidence/importer CI: `35960785377`
- full data-contract CI: `35960785360`
- BSE source verification: `35960785399`
- protected 544770 regression: `35960785366`

The isolated publication rehearsal proved **968 -> 998**, exactly **30 additions**, all 968 existing records unchanged, **0 holds/conflicts**, and an idempotent rerun. The reviewed BSE registry now contains **76 retained entries**.

Production sync `35960919082` succeeded:

- reviewed BSE import: **30 added / 46 already present / 0 holds**
- semantic publication: **30 added / 36 changed / 0 removed / 0 conflicts**
- source-backed data commit: `a8b6cc81f7c805598ab67552131833afea4bfa17`
- operator-state commit: `32cadd15b4fc91a92ef89f5af6415c893b545146`
- operator health: **healthy**
- production: **998 total records**
- 2025: **242 records** — 83 Mainboard / 158 SME / 1 unknown
- 2026: **85 records** — 15 Mainboard / 60 SME / 10 unknown

All 30 new issuers occur exactly once on current `main`, and every listing date, BSE code, market lot, issue price, source URL/hash and reviewed-manifest provenance matches the committed evidence. Unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null.

GitHub Pages build `35961435740` succeeded on operator commit `32cadd15b4fc91a92ef89f5af6415c893b545146`, a direct descendant of the 998-record data commit.

A duplicate PR #179 opened during the same work was closed **without merge** after PR #178 advanced `main`; no duplicate data was published.

**Next:** re-read the cursor first. If it has advanced beyond the current 60 tracked notices, reconcile only the newest completed cursor segment against the current 998-record universe. If it is unchanged, repair the single held unparseable index notice `20250912-85` as a bounded parser/source task without guessing an issuer. Do not reset the cursor or repeat the now-completed 30-reference cursor2 batch.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for exact source/evidence details, validation results and production verification.

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
