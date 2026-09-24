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

**Latest completed batch: first historical BSE discovery reconciliation — PR #174.**

Historical cursor run `35952980189` discovered **23 listing references** from the next 20 older BSE SME index notices. Exact reconciliation against the 67-record 2026 recovery universe found:

- **6 already present**
- **17 missing exact identities**
- **0 fuzzy/ambiguous overlaps accepted**

The 17 missing references were split into bounded verifier batches of 15 + 2 and checked against issuer-specific official BSE listing notices. Source verification run `35954077034` completed with:

- **13 verified**
- **4 rejected**
- **0 unavailable**
- artifact `10789631977`
- artifact ZIP SHA-256 `f493f894524bc666b8652b8726283122e85f87fb00e93d96fc258a7090cc9ad6`

Rejected and therefore **not publishable yet**:

- AUTOFURNISH LIMITED — `20260527-47`
- RECODE STUDIOS LIMITED — `20260511-16`
- MEHUL TELECOM LIMITED — `20260423-27`
- TIPCO ENGINEERING INDIA LIMITED — `20260330-44`

Their official listing PDFs did not independently confirm the expected scrip code/listing date; Autofurnish, Mehul Telecom and Tipco also failed the required equity-listing statement check. Do not infer or publish these four from index evidence.

Machine-readable reconciliation and candidate inputs:

- `data/discovery/bse-listing-reconciliation-2026-09-24.json`
- `data/discovery/bse-listing-candidates-2026-09-24-batch4.json`
- `data/discovery/bse-listing-candidates-2026-09-24-batch5.json`

**Next:** convert the 13 verified issuer-specific results into reviewed committed evidence manifests, revalidate their page excerpts/hashes, and publish only those 13 through the existing reviewed BSE importer. Keep the four rejected candidates on hold for issuer-identity/source repair. The independent historical cursor must continue advancing separately.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for exact run IDs, rejection reasons, production state and acceptance criteria.

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
