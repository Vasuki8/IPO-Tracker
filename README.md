# IPO Tracker

A source-first Indian IPO research website with automated official-source collection and GitHub Pages publication.

- Repository: `Vasuki8/IPO-Tracker`; default branch: `main`.
- Website: https://vasuki8.github.io/IPO-Tracker/
- [Explore IPOs](index.html) · [Pre-IPO companies](drhp.html).
- Public IPO dataset: `data/ipos.json`, generated from retained evidence under `data/recovery/`.
- Separate DRHP observations: `data/drhp-filings.json`.
- Development contract: [docs/DEVELOPMENT_PROCESS.md](docs/DEVELOPMENT_PROCESS.md).
- Current handoff: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).
- UI design handoff: [docs/UI_DETAIL_NAVIGATION_HANDOFF.md](docs/UI_DETAIL_NAVIGATION_HANDOFF.md).

## Product and data rules

Coverage spans 2020–2026 but is incomplete. Stored record counts are not proof of official IPO-universe completeness.

Display verified market lot first, labelled **Trading lot**, then verified minimum bid quantity, labelled **Minimum IPO bid**, when market lot is missing. Show both quantities separately in detail evidence. Keep the raw fields distinct. Minimum investment/application amount remains out of scope.

The directory compares the first valid opening, closing, or listing date across all records for **Newest first**. Search currently covers company names; sector classification is unavailable. Board filters include **Board unavailable** without inferring a classification.

Actionable bidding status considers verified opening and closing dates using the Indian market day. Expired reported Open/Upcoming offers display **Bidding closed**, while a reported Open offer with a future opening date displays **Scheduled**. Retained reported status and evidence remain available; date-based display never confirms listing or trading. A final issue price outside its retained price band displays a **Price conflict** until the basis is reconciled, without overwriting source values.

Bidding displays refresh at Indian midnight and when a tab resumes, while preserving detail-page research state.

Never invent missing values or use price-times-quantity arithmetic to fill them. Preserve official sources, document identity, dates, hashes when retained, nulls, conflicts and correction history. A final Prospectus is not required for inclusion. Repair retained recovery evidence rather than hand-editing `data/ipos.json`.

The **Pre-IPO companies** view is a company-level IPO pipeline backed by retained DRHP/UDRHP evidence from the SEBI draft-offer index, configured official lead-manager offer-document sources, **and the current published IPO lifecycle dataset**. It shows one company per row and dynamically removes an exact canonical issuer match as soon as that issuer is `upcoming`, `open`, `closed`, or `listed`, or has a published IPO open/close/listing date. Draft-document versions remain retained evidence rather than the product itself. Matching uses the same conservative canonical legal-name normalization as the universe audit; no fuzzy matching is allowed. If lifecycle data cannot be validated, the page fails closed instead of showing a potentially stale pre-IPO list. Source coverage is intentionally labelled partial until all relevant official draft-document surfaces are configured.

Pre-IPO freshness separately shows the loaded draft-source collection time, IPO lifecycle dataset generation time, and latest reported refresh attempt/status. Refresh failure retains the loaded evidence; a newer health report cannot redate older displayed source data.

## Automation

The existing hourly `update-ipos.yml` collects NSE/SEBI data and imports reviewed BSE and NSE evidence. Historical PDF recovery and the bounded BSE notice cursor run independently. `deploy-pages.yml` publishes the site. Workflow files define actual schedules and execution.

`update-drhp.yml` now polls configured official draft sources **every two hours** (minute 17 UTC, subject to GitHub Actions scheduling). The primary SEBI draft-offer index remains bounded to 16 pages; an official Axis Capital offer-document adapter supplies a fallback for DRHPs not yet visible in that SEBI index. Previously observed filings remain retained when absent from a later scan; missing rows are not treated as withdrawals. Original SEBI and configured lead-manager source pages are retained in the workflow artifact. Collection failure retains the last good dataset and records a separate status in `ops/drhp-collection.json`. Successful refreshes verify the actual served dataset and page assets.

`verify-bse-publication.yml` is a read-only post-publication check for selected reviewed BSE manifests. Its default remains parser-v1.5 recovered reviewed batch36. `verify-reviewed-nse-publication.yml` is the corresponding NSE check after successful source sync and now selects **batch9**. Both retain actual Pages bytes and separate fetch/check/generation timestamps; neither imports records.

`audit-ipo-universe.yml` is a read-only bounded official-universe audit with no schedule. It collects eight NSE/BSE/SEBI source surfaces, verifies source hashes and reconciles identities while retaining incomplete-coverage labels. Candidates are not automatically imported. Raw Actions artifacts expire after 14 days; durable review projections and evidence references remain in the repository.

Completed historical one-shot publication/materialization workflows have been retired from current main; their evidence and Git history remain intact. The [retirement record](docs/verification/completed-release-workflow-retirement-2026-09-28.md) covers the retired writer and redundant-validator surfaces, with completed releases checked through one read-only validator. PR #342's temporary bounded publisher was removed after verified live closeout in PR #343.

Collection time, source observation, dataset generation and Pages publication are distinct. `node scripts/operator-report.mjs` reports IPO operational health without rewriting values. DRHP collection health is separate.

`collect-bse-2023-irms-evidence.yml` remains a read-only historical/manual collector for the now-closed IRMS source set; it does not authorize replay or publication. The [multi-attempt source receipt](data/evidence/bse-2023-irms-source-receipt-2026-09-28.json) retains both partial outcomes and the exact source selections used for the completed review.

## Handoff for the next prompt

The **October 4 correctness/accessibility audit remains closed**; see
[the complete audit receipt](docs/verification/october-audit-closeout-2026-10-05.md).
The bounded SSEK release also remains closed and retired.

**Mish Designs Limited is now published and served-verified.** PR #372 merged as
`58df8b08`. Pages run **37384618726** served **1,389 records** on verification
attempt **1**, with SHA-256
`333e7a7570965e47661386fada8ca20efed40523669d1be9d5167ad4ead13e4f`.
The retained Pages verification artifact is **11376300416**. Its served Mish
record exactly matched the approved projection: BSE-hosted evidence only, with
board, price band, market lot, minimum bid quantity and minimum application amount
left null as reviewed. The live receipt is
[docs/verification/bse-2023-mish-live-2026-10-05.json](docs/verification/bse-2023-mish-live-2026-10-05.json).

The immutable 2023 ledger is now **17 reviewed/published + 13 awaiting review**.
Continue with exactly **AHASOLAR TECHNOLOGIES LIMITED (543941)**,
**ORGANIC RECYCLING SYSTEMS LIMITED (543997)**,
**Meson Valves India Limited (543982)** and
**TECHKNOWGREEN SOLUTIONS LIMITED (543991)**. The original 2022 queue remains
**14 reviewed/published + 2 existing-recovery alias + 0 awaiting review**.

Current source-health qualification is unchanged: the SEBI DRHP pagination surface
can still fail upstream. The isolated source-health logic preserves the last good
dataset and the independent Axis fallback attempt.

### Exact next backend task

Review **AHASOLAR TECHNOLOGIES LIMITED (543941)**,
**ORGANIC RECYCLING SYSTEMS LIMITED (543997)**,
**Meson Valves India Limited (543982)** and
**TECHKNOWGREEN SOLUTIONS LIMITED (543991)** from the pinned immutable 2023 queue.
The original BSE 2022 queue has remaining **0** unmatched rows requiring import.
Start with retained issuer-specific authoritative evidence and exact all-year
identity reconciliation. Do not treat discovery dates or prices as publication
authority; preserve nulls and conflicts. Publish only through a separate reviewed
manifest followed by exact served-data verification.

Continue P1 correctness. Do not expand P5/performance while unresolved source or
release-governance work remains. No new spending, contracts, accounts, analytics,
ads, billing, infrastructure migration or material access changes without approval.

Browser regressions run with an isolated Playwright installation:

```sh
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node scripts/test-ui.mjs
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node scripts/test-product-logic-ui.mjs
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node scripts/test-drhp-freshness.mjs
```

Historical notes below are retained as evidence and are superseded by the active
handoff above.

## Historical release notes

The previous README is preserved byte-for-byte in [the release-note archive](docs/README_ARCHIVE_THROUGH_MARUTI_2026-09-28.md), original Git blob `83ceae2732ab2b095637782bab6b061d774c0a97`. Old next-task paragraphs and snapshot counts there are historical, not current instructions. Current source decisions and run receipts are in [PROJECT_STATUS](docs/PROJECT_STATUS.md) and its linked archives.
