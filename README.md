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

The durable cursor3 window came from run `35962928144` / artifact `10793157274` (ZIP SHA-256 `caf6f8d747992eb25a447b8600b4f73eaf433d13d92ebde5e6a38aeeab649722`). It had **20 notices: 10 parsed, 10 unparseable**, with the parsed notices producing **14 listing references**.

Cross-check against the then-current 244-record 2025 recovery universe found all **14 as genuinely missing exact identities**, with 0 already-present matches and 0 ambiguous/fuzzy overlaps.

Retained discovery:

- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor3.json`
- `data/discovery/bse-listing-candidates-2026-09-24-batch11.json`

Initial issuer-specific verification returned **13 verified / 1 rejected**. The only rejection, **GLOBTIER INFOTECH LIMITED**, was a verifier-normalization defect: BSE wrapped one issuer mention in `&ldquo;...&rdquo;`, which produced a false second issuer identity after tag stripping. PR #181 now decodes BSE curly quote entities before the existing strict issuer comparison; no identity rule was relaxed. A regression fixture covers Globtier's exact source shape.

After that bounded repair, batch11 independently verified **14/14**, with **0 rejected / 0 unavailable**.

Reviewed publication:

- `data/verified-bse-listings/2026-09-24-batch16.json`
- manifest source run: `35964560752`
- manifest source artifact: `10792809549`
- manifest artifact ZIP SHA-256: `e6f102405d0c31657ea441b786cf2edb67f532885b759d586e53ca0044303fe7`
- final PR source verification: `35965176843` — 14/14
- final PR artifact: `10793174434` / SHA-256 `1724a3cc23f243edea2e2a2d6ccfae828b29d44d200f02667c144a7cd8aa813e`
- final main source verification: `35965260696` — 14/14
- final main artifact: `10793054943` / SHA-256 `cefbbed883f300a65f72c1445493b8edd30859de9506fb6f5145c005338c4377`

All 14 records use the strict reviewed official-BSE-HTML evidence contract because canonical listing-PDF archive paths are unavailable. Exact notice URL, response/document hash, normalized evidence text, collection/publication time, issuer identity, BSE code, listing date, market lot and issue price are retained. No index notice is used as listing-term authority.

Final publication rehearsal proved **1000 -> 1014**, exactly **14 additions**, all 1000 existing records unchanged, **0 holds/conflicts**, and an idempotent rerun. The reviewed BSE registry now contains **92 retained entries**.

Production sync `35965260674` succeeded:

- reviewed BSE import: **14 added / 78 already present / 0 holds**
- semantic publication: **14 added / 41 changed / 0 removed / 0 conflicts**
- source-backed data commit: `e607bb92434fbf41fcd84daddd71e0b665ac60ee`
- operator-state commit: `50792aceff402c683d341dc9bf9bb730739005ef`
- operator health: **healthy**
- production: **1014 total records**
- 2025: **258 records** — 83 Mainboard / 174 SME / 1 unknown
- 2026: **85 records** — 15 Mainboard / 60 SME / 10 unknown

Every one of the 14 new issuers occurs exactly once on current `main`, and code/listing date/lot/issue price/source URL/document hash/manifest provenance all match batch16. Unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null.

GitHub Pages build `35965869172` succeeded on operator commit `50792aceff402c683d341dc9bf9bb730739005ef`, so the deployed Pages revision contains the 1014-record release.

### Current historical cursor

The durable cursor remains:

- **80 tracked / 236 eligible**
- **70 parsed**
- **10 unparseable**
- **156 unseen**
- next unseen notice: **`20250403-16`**

The 14 parsed references from cursor3 are now fully reconciled and published. The remaining work from that cursor window is the **10 unparseable notices**, which must remain a separate parser/source-family repair track.

**Next:** always re-read the cursor first. If it has advanced beyond 80 tracked notices, reconcile only the newest completed cursor segment against the current 1014-record universe. If it is unchanged, inspect the 10 cursor3 unparseable notices as a bounded parser/source-family repair batch; group them by demonstrated source shape and do not infer issuers from index evidence.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for exact issuer facts, verification runs, parser repair details, production validation and the held unparseable notices.

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
