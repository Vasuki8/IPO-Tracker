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

**Latest completed unit: cursor7 reconciliation and source verification — PR #207.**

PR #207 merged as `17fe924e81fdf735ffd7addd1ed9982dfe49a3d8`. The independent BSE historical cursor had advanced to a new 20-notice segment, so the continuation reconciled that segment before touching older parser failures.

Cursor7 produced **18 parsed listing references + 2 new unparseable notices**. All 18 parsed references were exact-missing across the current **1,091 retained recovery records** with no BSE-code or listing-source collisions. They are retained in discovery batches20/21 and remain publication-blocked until reviewed evidence is materialized.

The first verification pass found two evidence-specific identity issues. They are now resolved without fuzzy matching:

- Arrowhead uses the issuer-specific BSE listing-notice spelling `Arrowhead Seperation Engineering Limited`, while retaining the index discovery spelling for traceability.
- City Crops demonstrated a `Registered & Corporate Office` heading that the verifier previously appended to the issuer name; the boundary is fixed with a regression fixture.

Final source-verification run `36058133127` completed **15/15 + 3/3 verified**, **0 rejected/unavailable**. Artifact `10833780727`, digest `sha256:553d9350d77756c3f61bac19f563aae15d3c0c7d97b6eebe47da48e7c4e2137c`, expires `2026-10-08T21:00:14Z`. Reviewed-evidence CI `36058133257`, identity-conflict guard `36058133386`, and full data-contract CI `36058133413` also passed.

### Current historical cursor

Re-read after PR #207 merge:

- parser **1.3.0**;
- **160 tracked / 236 eligible**;
- **153 parsed**;
- **7 unparseable**;
- **76 not yet tracked**;
- state blob `6ada9ade533cd1dc535799814b7a61bece067d35`;
- updated `2026-09-24T20:00:39.470Z`.

The seven failures remain separate: `20240624-11`, `20240612-20`, `20240606-11`, `20240205-12`, `20240103-22`, `20231206-8`, `20230719-15`. Do not infer issuers from them.

### Next task

Freeze the **18 already source-verified cursor7 issuers** from artifact `10833780727` into bounded reviewed manifests (currently next available: batch26/batch27), preserving exact issuer-specific BSE evidence and only explicit listing date, market lot and final issue price. Re-read latest recovery/public data before materialization; rehearse the real importer/publication, require existing records unchanged and an idempotent second run, then publish through the existing workflow and verify the served Pages dataset. Only after the cursor7 parsed segment is fully published should the seven failed index notices move to a separate bounded parser/source-family repair.

Do not replay cursor7 discovery batches20/21 or completed cursor6 reviewed batches24/25. No UI redesign, minimum-investment work, billing, accounts, ads, spending or permission changes are part of this handoff.

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
