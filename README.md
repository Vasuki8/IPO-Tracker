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

**Latest completed batch: BSE code 544770 conflict resolved and published — PR #171.**

Issuer-specific official BSE listing notices resolve the old discovery collision:

- **Yaashvi Jewellers Limited = 544770** — listing 2026-06-02, market lot 1,600, issue price INR 83.
- **Merritronix Limited = 544773** — listing 2026-06-08, market lot 1,000, issue price INR 149.

Merritronix's later SME-index addition notice had claimed 544770. That conflicting index value remains retained as superseded discovery evidence; it was not silently overwritten or used as listing authority.

Corrected source verification run `35950849004` passed **2/2** and retained both official PDFs in artifact `10787659263` (SHA-256 `f969117ce1895c8d9d17f5b3ba2a2dfe91640f5f71367898c65f330520c04e21`). Reviewed evidence is committed as `data/verified-bse-listings/2026-09-24-batch3.json`.

PR validation passed, including a **949 -> 951** isolated publication rehearsal with exactly 2 additions, all 949 existing records unchanged by the BSE importer, no held conflicts, and a no-op second import/rebuild.

Production live sync `35951056853` succeeded. Semantic publication added exactly **2 records** and produced source-backed data commit `6221738a93158e5831c524d4bc8883103492cce5`.

Current production state from that run:

- **951 total records**
- **67 records for 2026**
- **42 SME records for 2026**
- **29 reviewed BSE records across the three retained batches**
- deterministic build and schema validation passed
- operator state healthy

GitHub Pages build `35951543912` succeeded on descendant commit `cf04c69179cd5935e8b04d212d56cc20360f7d40`, so the deployed site includes the two resolved records.

**Cursor completed:** PR #173 added a durable notice-ID/parser-version backfill. Production run `35952980189` parsed the first **20 older notices**, discovered **23 listing references**, had **0 failures**, and advanced progress from **20/236 to 40/236**. State commit: `6a8a21ce8c0befea1a3c67911472c3aff731c7f1`; 196 notices remain and will continue on the independent two-hour schedule.

**Next:** reconcile those 23 discovery references against the current 951-record universe, then verify only genuinely missing/unambiguous issuers from their issuer-specific official BSE listing notices. The cursor itself must continue independently; index evidence remains discovery-only.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for exact source hashes, correction history, run IDs, production counts and acceptance criteria.

No UI redesign, research-depth expansion, minimum-investment work, billing, accounts, ads, paid services or permission changes are part of this handoff.

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
