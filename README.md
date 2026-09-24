# IPO Tracker

A source-first Indian IPO research website with automated official-source collection and GitHub Pages publication.

- Repository: `Vasuki8/IPO-Tracker`; default branch: `main`.
- Website: https://vasuki8.github.io/IPO-Tracker/
- Public dataset: `data/ipos.json`, generated from retained evidence under `data/recovery/`.
- Development contract: [docs/DEVELOPMENT_PROCESS.md](docs/DEVELOPMENT_PROCESS.md).
- Current handoff: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Product and data rules

Coverage spans 2020-2026 but is incomplete. Run `node scripts/audit-historical-coverage.mjs` for current counts; old milestones are not current totals.

The active application-term requirement is **Lot Size only**. Display verified market lot first, then verified minimum bid quantity when market lot is missing. Keep the raw fields distinct. Minimum investment/application amount remains out of scope.

Never invent missing values or use price-times-quantity arithmetic to fill them. Preserve official sources, document identity, dates, hashes when retained, nulls, conflicts and correction history. A final Prospectus is not required for inclusion. Repair retained recovery evidence rather than hand-editing `data/ipos.json`.

## Automation

The existing hourly `update-ipos.yml` collects NSE/SEBI data and imports reviewed BSE evidence. Historical PDF recovery and the bounded BSE notice cursor run independently. `deploy-pages.yml` publishes the site. Workflow files define actual schedules and execution.

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. It fetches the actual Pages dataset, retains its original bytes/hash and separate observation time, and checks issuer identity, values, source metadata and retained provenance. It runs manually or when its implementation changes; it does not alter the collection schedule or import IPOs.

Collection time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Latest completed unit: cursor6 reconciled and independently source-verified — PR #201.**

PR #201 merged as `9cc541d3b9e1bc317ed3e9bb3545ea51ce47f327`.

Do not repeat repaired cursor5 batch17. Concurrent automation already reviewed and published those four issuers through **batch22**, then PR #199 verified the actually served release:

- production sync `36036317281`: **4 added / 144 already present / 0 holds / 0 identity conflicts**;
- semantic publication: **4 added / 1 changed / 0 removed / 0 conflicts**;
- production total: **1,072 records**;
- live verifier `36037026089`: **4/4 unique issuers, 12/12 listing-date/lot/price fields, 0 failures**;
- live artifact `10824857948`, ZIP SHA-256 `52e5c015a0cc5eb7b71b20667fcce85215009abfe2e88e42c62dbfa1cc5e019f`.

A duplicate attempt in PR #202 was closed unmerged after the importer correctly reported `0 added / held_existing=4`. Do not resurrect batch23.

### Cursor6 completed work

The independent historical cursor advanced to:

- parser **1.3.0**;
- **140 tracked / 236 eligible**;
- **135 parsed / 5 unparseable**;
- **96 not yet tracked**.

The newest 20-notice segment first attempted at `2026-09-24T18:12:33.727Z` contains:

- **15 parsed notices**;
- **19 listing references**;
- **5 unparseable notices**.

PR #201 reconciled all 19 parsed references against the current **1,072-record public dataset** and current 2024 recovery (**273 records**):

- **19 exact-missing identities**;
- **0 already present**;
- **0 ambiguous / BSE-code collisions**.

Retained files:

- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor6.json`;
- `data/discovery/bse-listing-candidates-2026-09-24-batch18.json` — 15;
- `data/discovery/bse-listing-candidates-2026-09-24-batch19.json` — 4.

Independent issuer-specific verification run `36041395122` succeeded:

- batch18: **15/15 verified**;
- batch19: **4/4 verified**;
- rejected: **0**;
- unavailable: **0**;
- artifact: **10826304295**;
- artifact ZIP SHA-256: `1a54f73efd2784202fb64f1ddadb5cbd825b448aea4056a3d2d2ff2ebe35f441`.

The verifier needed one bounded source-family extension: **PIOTEX INDUSTRIES LIMITED** states its lot only in the official notice's `minimum market lot (i.e.1200 equity shares)` clause. The repair accepts that demonstrated clause without weakening issuer, notice number, BSE code, SME statement, listing date or issue-price checks. Regression coverage is merged.

All PR-head gates passed, including data contract, reviewed-evidence/importer tests, protected BSE identity regression and source verification.

### Five cursor6 parser failures

Keep these separate from the 19 verified candidates and do not infer issuers:

- `20240624-11`
- `20240612-20`
- `20240606-11`
- `20240205-12`
- `20240103-22`

**Next:** re-read current `main` and cursor first, but do not skip cursor6 batches18/19 if automation advances. Freeze the 19 already-verified source results from artifact `10826304295` into reviewed evidence manifests (maximum 15 entries each), retaining exact official BSE HTML evidence, source hashes, dates, listing date, market lot and final issue price. Rehearse the real importer against latest main, publish only if identities are still missing/unambiguous, verify the served site, then handle the five parser failures as a separate bounded source-family repair before moving to older unseen notices.

No UI redesign, minimum-investment work, billing, accounts, ads, spending or permission changes are part of this handoff.
## Local checks

```bash
node scripts/test-verify-bse-publication.mjs
node scripts/test-bse-public-projection.mjs
node scripts/test-bse-publication-rehearsal.mjs
node scripts/apply-verified-bse-listings.mjs --check
node scripts/build-published-data.mjs --check
node scripts/validate-data.mjs
node scripts/audit-historical-coverage.mjs
```

For a live receipt, run `scripts/verify-bse-publication.mjs` with `--manifests=<comma-separated reviewed paths>` and `--output-dir=<artifact directory>`. It reports failure on unavailable/malformed snapshots or mismatches and never imports IPO records.

## Historical handoffs

The complete previous README and status are preserved unchanged in [docs/archive/README-before-cursor4-live-verification.md](docs/archive/README-before-cursor4-live-verification.md) and [docs/archive/PROJECT_STATUS-before-cursor4-live-verification.md](docs/archive/PROJECT_STATUS-before-cursor4-live-verification.md). Older archives remain unchanged. Archived next-task instructions are not current instructions.
