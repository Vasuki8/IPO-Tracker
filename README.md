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

**Latest completed batch: third historical BSE cursor parsed references published — PR #181.**

PR #181 merged as `cc44fd35a4bf6eff37aa9a59807393ac33277ee6`.

This batch reconciled the 14 parsed references from the third durable BSE cursor window against the then-current 244-record 2025 recovery universe.

Cursor3 source window:

- cursor run: `35962928144`
- cursor artifact: `10793157274`
- artifact ZIP SHA-256: `caf6f8d747992eb25a447b8600b4f73eaf433d13d92ebde5e6a38aeeab649722`
- cursor state commit: `1704357838871f9e5dd677da4a7bfabba7b50760`
- 20 notices selected
- 10 parsed
- 10 unparseable
- 14 listing references

Cross-checking those 14 references against retained 2025 recovery found **14 genuinely missing exact identities**, with **0 already-present matches** and **0 ambiguous/fuzzy overlaps**.

Retained reconciliation and candidates:

- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor3.json`
- `data/discovery/bse-listing-candidates-2026-09-24-batch11.json`

Initial issuer-specific source verification found **13/14 verified**. Globtier Infotech was the only rejection, and the official BSE notice itself was not contradictory: it independently confirmed code 544494, listing date 2025-09-02, lot 1,600 and issue price INR 72. The rejection came from the notice body wrapping the issuer name in BSE HTML entities `&ldquo;...&rdquo;`, which the verifier had not normalized.

PR #181 therefore added a bounded identity-normalization repair:

- decode `&ldquo;` / `&rdquo;` as ordinary quotes;
- decode `&lsquo;` / `&rsquo;` as ordinary apostrophes;
- keep the same strict normalized issuer-name, notice-number, BSE-code, listing-date and SME-segment checks after decoding;
- add an exact Globtier regression fixture.

With that repair, canonical source run `35964560752` verified **14/14**, with **0 rejected / 0 unavailable**.

Reviewed evidence:

- `data/verified-bse-listings/2026-09-24-batch16.json`
- source run: `35964560752`
- source artifact: `10792809549`
- source artifact ZIP SHA-256: `e6f102405d0c31657ea441b786cf2edb67f532885b759d586e53ca0044303fe7`

All 14 use the strict reviewed official-BSE-notice HTML evidence contract. Canonical archive listing-PDF paths were unavailable; index notices are not used as market-term authority.

Final PR validation:

- reviewed evidence/importer: `35965176868` — success
- data contract: `35965176865` — success
- protected BSE 544770 regression: `35965176842` — success
- canonical source verification: `35964560752` — 14/14
- final `main` source re-verification: `35965260696` — 14/14
- final main artifact: `10793054943`
- final main artifact SHA-256: `cefbbed883f300a65f72c1445493b8edd30859de9506fb6f5145c005338c4377`

Publication rehearsal proved **1000 -> 1014**, exactly **14 additions**, all 1000 existing records unchanged, **0 holds/conflicts**, and an idempotent rerun. The reviewed BSE registry now contains **92 retained entries**.

Production sync `35965260674` succeeded:

- reviewed BSE import: **14 added / 78 already present / 0 holds**
- semantic publication: **14 added / 41 changed / 0 removed / 0 conflicts**
- source-backed data commit: `e607bb92434fbf41fcd84daddd71e0b665ac60ee`
- operator-state commit: `50792aceff402c683d341dc9bf9bb730739005ef`
- operator health: **healthy**
- production: **1014 total records**
- 2025: **258 records** — 83 Mainboard / 174 SME / 1 unknown
- 2026: **85 records** — 15 Mainboard / 60 SME / 10 unknown

All 14 new issuers occur exactly once on current `main`, and each listing date, BSE code, market lot, issue price, source URL/hash and batch16 provenance matches the reviewed manifest. Unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null.

GitHub Pages build `35965869172` succeeded on operator commit `50792aceff402c683d341dc9bf9bb730739005ef`, so the deployed Pages revision contains the 1014-record release.

### Cursor state

PR #181 did not touch or trigger the durable cursor workflow. Current cursor remains:

- **80 tracked / 236 eligible**
- **70 parsed**
- **10 unparseable**
- **156 unseen**
- next unseen notice: **`20250403-16`**

The 14 parsed references from cursor3 are now fully reconciled, verified and published. The remaining unfinished work from that cursor window is the **10 unparseable notices**:

- `20250716-16`
- `20250715-47`
- `20250711-10`
- `20250710-17`
- `20250606-10`
- `20250529-14`
- `20250512-14`
- `20250509-10`
- `20250408-20`
- `20250407-20`

**Next:** re-read the cursor first. If it is still at this 80-notice state, inspect the 10 unparseable notices, group them by demonstrated source/text shape, and repair the smallest reusable parser/source family without guessing issuer identities. If the cursor has advanced independently, reconcile the newly completed cursor window first.

Do not repeat the now-completed 14-reference cursor3 publication batch.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for exact evidence, parser normalization, validation, production and deployment details.

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
