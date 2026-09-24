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

**Latest completed batch: repaired BSE notice 20250912-85 and published its two issuers — PR #180.**

PR #180 merged as `1e19389f78ddafef7ae2a61596d7e8443dbfb4e9` and closes the single unparseable notice left by the prior cursor segment.

The official BSE SME index notice `20250912-85` contains two complete issuer references joined by an ampersand and a shared listing statement:

- **AUSTERE SYSTEMS LIMITED** — BSE code 544505 — issuer-specific listing notice `20250911-76`
- **SHARVAYA METALS LIMITED** — BSE code 544506 — issuer-specific listing notice `20250911-79`

The source says both were **listed on the SME platform of BSE effective September 12, 2025**. The later **September 15, 2025** date is the index-admission date and remains distinct.

The parser repair is intentionally narrow:

- accept only the demonstrated phrase `listed on SME platform of BSE`;
- allow `&` only between otherwise complete notice / issuer / six-digit ticker references;
- reject another exchange;
- reject a missing ticker rather than borrowing the next issuer's ticker;
- continue to exclude the later index-admission date from the listing-date field.

The retained cursor entry for `20250912-85` was reparsed from the same official source/hash into exactly two references. No issuer or value was inferred.

Discovery/reconciliation:

- `data/discovery/bse-listing-reconciliation-2026-09-24-notice-20250912-85.json`
- `data/discovery/bse-listing-candidates-2026-09-24-batch10.json`

Both issuer-specific BSE listing notices independently verified **2/2**, with **0 rejected / 0 unavailable**.

Reviewed evidence:

- `data/verified-bse-listings/2026-09-24-batch15.json`
- source run: `35962409176`
- source artifact: `10793305545`
- source artifact ZIP SHA-256: `a6e9c232aeb36430e83023607ddfee87ea9e72cb69fb2027d41f9558269d99bc`
- final main verification run: `35962927921`
- final artifact: `10793346309`
- final artifact ZIP SHA-256: `675edf2f8701535c0d6cd3b5756af3713fbabae41d884a70f7ca74c0448f9cb4`

Final publication rehearsal proved **998 -> 1000**, exactly **2 additions**, all 998 existing records unchanged, **0 holds/conflicts**, and an idempotent rerun. The reviewed BSE registry now contains **78 retained entries**.

Production sync `35962927876` succeeded:

- reviewed BSE import: **2 added / 76 already present / 0 holds**
- semantic publication: **2 added / 30 changed / 0 removed / 0 conflicts**
- source-backed data commit: `33d311903621c110e0db608c913fb071ccd99eb3`
- operator-state commit: `a275eaa5fcb6fdb665b702a8d47e5555500d0ea3`
- operator health: **healthy**
- production: **1000 total records**
- 2025: **244 records** — 83 Mainboard / 160 SME / 1 unknown
- 2026: **85 records** — 15 Mainboard / 60 SME / 10 unknown

Current `main` contains both repaired issuers exactly once:

- Austere Systems — listing date 2025-09-12, lot 2,000, issue price INR 55
- Sharvaya Metals — listing date 2025-09-12, lot 600, issue price INR 196

Each retains the exact official BSE listing-notice URL and document hash. Unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null.

GitHub Pages build `35963513850` succeeded on operator commit `a275eaa5fcb6fdb665b702a8d47e5555500d0ea3`, so the deployed Pages revision contains the 1000-record release.

### Cursor state after the repair

The merge also triggered the independent historical BSE cursor, which advanced another 20 notices in run `35962928144`:

- cursor artifact: `10793157274`
- artifact ZIP SHA-256: `caf6f8d747992eb25a447b8600b4f73eaf433d13d92ebde5e6a38aeeab649722`
- cursor state commit: `1704357838871f9e5dd677da4a7bfabba7b50760`
- **80 tracked / 236 eligible**
- **70 parsed**
- **10 unparseable**
- **156 unseen**
- next unseen notice: **`20250403-16`**
- newly parsed window produced **14 listing references**

The 14 new references have **not** been reconciled or published in this repair batch. The 10 new unparseable notices are also unresolved.

**Next:** re-read the cursor first. If it is still at the current 80-notice state, reconcile the 14 newly parsed references against the current 1000-record universe and retain the 10 unparseable notices as a separate parser/source-repair track. Do not repeat the completed repair for `20250912-85`.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for exact parser safety rules, evidence hashes, verification runs, production publication and the new cursor window.

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
