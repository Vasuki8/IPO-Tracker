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

**Latest completed batch: legacy 2025 BSE SME addition-notice parser/source-family repair — PR #182.**

PR #182 merged as `1d892d573181d126bf2cee87ae63ae65057e6977`.

The third historical cursor window had left 10 official BSE Index Services notices unparseable. A bounded read-only diagnostic re-fetched exactly those 10 notice-detail payloads and confirmed that every response SHA-256 matched the text hash already retained in `ops/bse-sme-addition-notices.json`. The demonstrated older 2025 template uses:

- `Notice No .` with whitespace before the period;
- `listed on the SME Platform of BSE`;
- one notice identifier with whitespace around the dash (`20250407- 51`).

Parser v1.2.0 adds only those demonstrated grammar variants and canonicalizes recovered notice IDs. Successful v1.1 parsed entries remain compatible, while failed v1.1 entries are isolated for immediate parser-migration retry instead of replaying the entire cursor.

A semantic-state regression found during PR validation was also fixed: cursor publication now compares each incoming entry's parser version, so stale same-version failures cannot overwrite newer parsed evidence while a genuine parser-version repair can replace the old failed entry.

Final PR checks all passed:

- data-contract CI: `35967129380`
- reviewed-BSE evidence CI: `35967129462`
- dedicated BSE historical cursor tests: `35967129385`

Merge-triggered production backfill `35967210854` succeeded:

- selected parser-migration failures: **10**
- parsed: **10/10**
- fetch errors: **0**
- unparseable: **0**
- recovered listing references: **12**
- report artifact: **10794322473**
- cursor-state commit: `f8cdb085377d2beba8a51c5e697b8d618398aaa9`

Current durable cursor:

- **80 tracked / 236 eligible**
- **80 parsed**
- **0 failed/unparseable**
- **156 unseen**
- next unseen notice: **`20250403-16`**
- parser version: **1.2.0**

The 12 recovered references are discovery evidence only and have **not** created or edited IPO records:

| Issuer | BSE code | Listing notice | Listing date |
| --- | ---: | --- | --- |
| ASSTON PHARMACEUTICALS LIMITED | 544445 | `20250715-53` | 2025-07-16 |
| GLEN INDUSTRIES LIMITED | 544444 | `20250714-41` | 2025-07-15 |
| META INFOTECH LIMITED | 544441 | `20250710-60` | 2025-07-11 |
| CRYOGENIC OGS LIMITED | 544440 | `20250709-45` | 2025-07-10 |
| 3B Films Limited | 544412 | `20250605-49` | 2025-06-06 |
| UNIFIED DATA TECH SOLUTIONS LIMITED | 544406 | `20250528-43` | 2025-05-29 |
| SRIGEE DLM LIMITED | 544399 | `20250509-44` | 2025-05-12 |
| MANOJ JEWELLERS LIMITED | 544400 | `20250509-45` | 2025-05-12 |
| KENRIK INDUSTRIES LIMITED | 544398 | `20250508-51` | 2025-05-09 |
| SPINAROO COMMERCIAL LIMITED | 544392 | `20250407-51` | 2025-04-08 |
| INFONATIVE SOLUTIONS LIMITED | 544393 | `20250407-67` | 2025-04-08 |
| RETAGGIO INDUSTRIES LIMITED | 544391 | `20250404-53` | 2025-04-07 |

**Next:** re-read the durable cursor first. Reconcile these 12 recovered references against the current production universe. For genuinely missing, unambiguous identities, verify issuer-specific official BSE listing evidence in a bounded batch before publication. Index-addition notices remain discovery-only and must never be used as authority for market lot, issue price or other listing terms. After this recovered set is reconciled, continue with newer completed cursor segments if the independent cursor has advanced beyond `20250403-16`.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for the parser diagnosis, migration safeguards, production run and exact next-task acceptance criteria.

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
