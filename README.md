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
| `verify-bse-listing-candidates.yml` | Bounded independent verification of pinned BSE listing candidates |
| `validate-reviewed-bse-listings.yml` | Offline identity, PDF safety, reviewed evidence and importer tests |
| `validate-data.yml` | Existing pull-request/push tests and data-contract checks |
| `deploy-pages.yml` | Website deployment and publication-health recording |

Collection time, dataset generation and Pages publication are separate signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values. Workflow files are authoritative for actual execution.

## Handoff for the next prompt

**Current batch: remaining 12 independently verified BSE SME listings; PR #167.**

PR #166's first 15 records are already live: a fresh deployed snapshot contains 937 records and all 45 previously reviewed facts. Do not repeat that batch.

The remaining 12 unambiguous candidates were pinned and independently checked against their actual BSE listing PDFs. Live verification `35946186883` passed all 12. All 24 header/fact pages were rendered and reviewed; all 36 listing-date/lot-size/final-price facts cite PDF page 2. A narrow missing-ff text-extraction fix handles Leapfrog's `e ective from` label while retaining the original source text and all identity/date guards.

Both reviewed batches are registered explicitly in `data/verified-bse-listings/approved-batches.json`. The existing offline importer validates every registered batch before writing, protects existing/concurrent values, preserves each batch's source version/times, and rejects cross-batch identity collisions. Unreviewed files are not automatically imported.

All 36 local tests passed. Publication rehearsal: **937 -> 949**, with all 937 existing records unchanged and a no-op second import. **Final CI, merge, production publication and deployed verification remain pending at this checkpoint.** Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for observed release results before claiming these 12 are live.

**Next:** resolve the two held code-544770 references (Merritronix and Yaashvi Jewellers) against their original official documents. The other 216 older eligible notices still require a durable cursor. Index admission dates remain distinct from listing dates; no complete-BSE-universe claim is made.

No UI redesign, research-depth expansion, minimum-investment work, billing, accounts, ads, paid services or permission changes are part of this batch.

## Local checks

```bash
node scripts/test-verify-bse-listing-candidates.mjs
node scripts/test-retry-bse-listing-pdf.mjs
node scripts/test-apply-verified-bse-listings.mjs
node scripts/test-apply-bse-approved-batches.mjs
node scripts/test-bse-publication-rehearsal.mjs
node scripts/apply-verified-bse-listings.mjs --check
node scripts/build-published-data.mjs --check
node scripts/validate-data.mjs
node scripts/audit-historical-coverage.mjs
```

To apply the already reviewed batches locally, run `node scripts/apply-verified-bse-listings.mjs` before rebuilding. This uses no network. The independent BSE PDF verification workflow requires `pdftotext`; its report never writes IPO records automatically.

## Earlier handoffs

PR #165's full verified discovery handoff is preserved in [docs/archive/PROJECT_STATUS-before-bse-listing-batch.md](docs/archive/PROJECT_STATUS-before-bse-listing-batch.md). Earlier accumulated milestones remain unchanged in `docs/archive/`; they are history, not current coverage or instructions.
