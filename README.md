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

**Latest completed unit: cursor5 BSE parser failures repaired and reconciled — PR #193.**

PR #193 merged as `61453efd680289a57ecc889a0070aa894624df77`.

The prior cursor5 publication work is already complete in PR #191 / #192 and must not be repeated: discovery batches15/16 became reviewed batches20/21, production sync `36026575507` published **18 additions** into the **1,068-record** dataset, and live verification passed.

This batch repaired the three cursor5 notices that remained unparseable:

- `20241211-15`
- `20241202-11`
- `20240722-21`

A bounded read-only diagnostic re-fetched only those three official BSE Index Services payloads. Every fresh response SHA-256 exactly matched the text hash already retained in cursor state, so the failures were parser-shape issues rather than changed upstream content.

Demonstrated older BSE formats:

- whitespace inside the ticker parenthesis: `( Exchange ticker - 544296)`;
- a shared header containing multiple listing-notice IDs once — `Notice No:20240719-44 and 20240719-38` — followed by the same number of issuer/ticker pairs in order.

Parser **v1.3.0** now accepts only those demonstrated variants. Shared-ID clauses require a complete one-to-one ID/issuer/ticker mapping; malformed or partial clauses fail closed. Parsed v1.1/v1.2 cursor entries remain compatible, so the parser migration did not replay the 117 already-successful entries.

Final PR-head checks all passed:

- full data contract: `36028430818`;
- reviewed BSE evidence: `36028430692`;
- dedicated BSE cursor/parser suite: `36028431156`.

Merge-triggered production backfill `36028598993` succeeded:

- selected: **3**, all reason `parser_changed_failure`;
- parsed: **3/3**;
- fetch errors: **0**;
- unparseable: **0**;
- recovered listing references: **4**;
- report artifact: **10820393192**;
- artifact ZIP SHA-256: `01f9895ba1fcc97abda170c5f4a1690e227fc6401f3e2dde314ee4cd99b95f3c`;
- cursor-state commit: `fd06045ac437636bc5d0c8dba087397ad4897c28`.

Current cursor:

- parser **1.3.0**;
- **120 tracked / 236 eligible**;
- **120 parsed / 0 failed**;
- **116 not yet tracked**;
- next unseen notice: **`20240624-11`**.

The four repaired discovery references were reconciled against the current 2024 recovery set (**269 records**) and public dataset (**1,068 records**). All four are **exact-missing, unambiguous identities**; none is already present and no BSE-code/source collision exists:

| Issuer | BSE code | Listing notice | Listing date |
| --- | ---: | --- | --- |
| NISUS FINANCE SERVICES CO LIMITED | 544296 | `20241210-61` | 2024-12-11 |
| Rajesh Power Services Limited. | 544291 | `20241129-72` | 2024-12-02 |
| Aelea Commodities Limited | 544213 | `20240719-44` | 2024-07-22 |
| Three M Paper Boards Ltd | 544214 | `20240719-38` | 2024-07-22 |

Retained machine-readable handoff:

- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor5-repaired.json`
- `data/discovery/bse-listing-candidates-2026-09-24-batch17.json`

**Next:** re-read `main` and the cursor first, but do not skip this repaired candidate batch if automation advances. Independently verify batch17's four issuer-specific official BSE listing notices before materialization. Retain listing date, market lot and final issue price only from issuer-specific official evidence; keep unsupported fields null. If all four verify, publish through the existing reviewed-evidence importer, verify the live site, then continue historical discovery from `20240624-11`.

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
