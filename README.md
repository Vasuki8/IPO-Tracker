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

**Latest completed batch: remaining seven historical BSE SME listings published — PR #176.**

PR #176 merged as `9edcbb30d0a62575e12c0116a2533564ffffc4f2` and completed the first historical discovery batch's publishable records.

The seven issuer-specific BSE listing notices did not have usable canonical archive listing-PDF paths. Their notice pages did expose Annexure PDFs, but those annexures are ancillary shareholding/IPO documents and correctly failed the listing-notice verifier. The importer was therefore extended with a separate **official BSE notice HTML** evidence contract rather than treating annexures as listing authority or inventing page evidence.

For reviewed HTML evidence the importer now requires the exact BSE notice URL, raw-response SHA-256, normalized-evidence SHA-256, collection/publication timestamps, exact notice/issuer/scrip/listing identity, and an offline replay through the existing listing verifier. HTML-backed fields retain `page: null`; no fake page numbers are created.

Reviewed manifests:

- `data/verified-bse-listings/2026-09-24-batch5.json` — Aritas Vinyl, Yajur Fibres
- `data/verified-bse-listings/2026-09-24-batch6.json` — Elfin Agro, PAN HR Solution, Kanishk Aluminium India, Accretion Nutraveda, Msafe Equipments
- source verification run: `35956034085`
- source artifact: `10789439895`
- artifact ZIP SHA-256: `d78e344277d79ccce4411e3a7f4552b3eeb87089e3d584d8a1fa8a5c746d1acb`

Final PR validation proved an isolated **957 -> 964** publication rehearsal with exactly **7 additions**, all 957 existing records unchanged, 0 holds/conflicts and an idempotent rerun. Reviewed-evidence CI `35956420754`, data-contract CI `35956420683`, source diagnostics `35956420702` and the 544770 regression workflow `35956420680` all succeeded.

Production sync `35956583736` succeeded:

- reviewed BSE import: **7 added / 35 already present / 0 holds**
- semantic publication: **7 added / 36 changed / 0 removed / 0 conflicts**
- source-backed data commit: `40c8326db90e1c8d29d98cc2c998aa88d159742c`
- operator-state commit: `ad52c686ebfad609aab8e33db686c34e082ce256`
- operator health: **healthy**
- production: **964 total records / 80 records for 2026**
- 2026 board coverage: **15 mainboard / 55 SME / 10 unknown**

Current `main` contains each of the seven new issuers exactly once with the reviewed BSE notice URL/hash and verified listing date, market lot and issue price. Unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null. The four rejected candidates from the same discovery batch remain absent and held: Autofurnish, Recode Studios, Mehul Telecom and Tipco Engineering.

GitHub Pages build `35957085010` succeeded on operator commit `ad52c686ebfad609aab8e33db686c34e082ce256`, which is a descendant of the 964-record data commit, so the deployed Pages revision includes this release.

**The original 13 verified missing candidates from PR #174 are now fully published: 6 PDF-backed + 7 reviewed official-HTML-backed.** The four rejected candidates are still a separate identity/source-repair track.

**Next:** re-read the durable historical BSE cursor before starting. At this handoff it remains **40/236 parsed with 196 unseen** and next unseen notice `20260107-29`. If the scheduled cursor has advanced, reconcile its newest completed discovery batch against the current 964-record universe and verify only genuinely missing issuers. If it has not advanced yet, keep the cursor independent and work on the four held identity/source repairs without inferring from index evidence.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for the seven exact facts, evidence-contract details, run IDs, hashes, production verification and remaining holds.

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
