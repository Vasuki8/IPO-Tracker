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

**Verified batch: remaining 12 unambiguous BSE SME listings — PR #168.**

PR #168 merged at `39ead2287b9352953d43b24ec9a006ab21f0d72a`. The 12 remaining unambiguous issuer references from the original BSE notice report were independently checked against issuer-specific official BSE listing PDFs.

Successful source verification run `35946970931` finished **12/12 verified**, with artifact `10787446306` and artifact SHA-256 `4d93a865acc52cebd8b57e6d00668b722b6182c79aa8d2b874b9864dc57e1863`.

The reviewed evidence is retained in `data/verified-bse-listings/2026-09-24-batch2.json`. Only explicit listing date, market lot and final issue price are published. The verifier also now distinguishes rejected PDFs from unavailable sources and handles BSE PDF text where the `ff` ligature in `effective` is extracted as a space without accepting index-admission wording.

The reviewed importer now supports multiple committed BSE evidence batches with the same no-overwrite/idempotency rules.

Production live sync `35947297162` succeeded and semantic publication added exactly **12 records**. Source-backed data commit: `1d7ffff145b99cf045b6954028d595105a1522fb`.

Current production counts from that run:

- **949 total records**
- **65 records for 2026**
- deterministic recovery check passed
- data-contract validation passed
- operator state healthy

GitHub Pages build `35947797703` succeeded on descendant commit `1d92710098fcf9b492a572eb6424e2c434153e93`, so the deployed website includes the new data.

Pages publication-health persistence was also made race-safe in PR #169. Production deployment `35948287263` completed green and durable status commit `45b2f22a4f5d3a7b8416133a0b7eeab6fc580b5a` records the successful deployment.

Across PR #166 + PR #168, **27 independently reviewed BSE SME records from the original discovery report are now published**.

**Next:** resolve the remaining code-`544770` identity conflict between MERRITRONIX LIMITED and YAASHVI JEWELLERS LIMITED using their original index PDFs plus issuer-specific official BSE listing notices. Do not pick one by recency or fuzzy identity. After that, add a durable versioned cursor for the **216 older eligible BSE SME addition notices** not covered by the latest-20 audit.

Read [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for exact production evidence, reviewed facts and remaining blockers.

No UI redesign, research-depth expansion, minimum-investment work, billing, accounts, ads, paid services or permission changes are part of this handoff.

## Local checks

```bash
node scripts/test-verify-bse-listing-candidates.mjs
node scripts/test-retry-bse-listing-pdf.mjs
node scripts/test-apply-verified-bse-listings.mjs
node scripts/apply-verified-bse-listings.mjs --check
node scripts/build-published-data.mjs --check
node scripts/validate-data.mjs
node scripts/audit-historical-coverage.mjs
```

To apply the already reviewed batch locally, run `node scripts/apply-verified-bse-listings.mjs` before rebuilding. This uses no network. The independent BSE PDF verification workflow requires `pdftotext`; its report never writes IPO records automatically.

## Earlier handoffs

PR #165's full verified discovery handoff is preserved in [docs/archive/PROJECT_STATUS-before-bse-listing-batch.md](docs/archive/PROJECT_STATUS-before-bse-listing-batch.md). Earlier accumulated milestones remain unchanged in `docs/archive/`; they are history, not current coverage or instructions.
