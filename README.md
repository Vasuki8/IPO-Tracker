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

The active application-term requirement is **Lot Size only**. Display verified market lot first, then verified minimum bid quantity when market lot is missing. Keep the raw fields distinct. Minimum investment/application amount remains out of scope.

Never invent missing values or use price-times-quantity arithmetic to fill them. Preserve official sources, document identity, dates, hashes when retained, nulls, conflicts and correction history. A final Prospectus is not required for inclusion. Repair retained recovery evidence rather than hand-editing `data/ipos.json`.

The **Pre-IPO companies** view is a company-level IPO pipeline backed by retained DRHP/UDRHP evidence from the SEBI draft-offer index, configured official lead-manager offer-document sources, **and the current published IPO lifecycle dataset**. It shows one company per row and dynamically removes an exact canonical issuer match as soon as that issuer is `upcoming`, `open`, `closed`, or `listed`, or has a published IPO open/close/listing date. Draft-document versions remain retained evidence rather than the product itself. Matching uses the same conservative canonical legal-name normalization as the universe audit; no fuzzy matching is allowed. If lifecycle data cannot be validated, the page fails closed instead of showing a potentially stale pre-IPO list. Source coverage is intentionally labelled partial until all relevant official draft-document surfaces are configured.

## Automation

The existing hourly `update-ipos.yml` collects NSE/SEBI data and imports reviewed BSE and NSE evidence. Historical PDF recovery and the bounded BSE notice cursor run independently. `deploy-pages.yml` publishes the site. Workflow files define actual schedules and execution.

`update-drhp.yml` now polls configured official draft sources **every two hours** (minute 17 UTC, subject to GitHub Actions scheduling). The primary SEBI draft-offer index remains bounded to 16 pages; an official Axis Capital offer-document adapter supplies a fallback for DRHPs not yet visible in that SEBI index. Previously observed filings remain retained when absent from a later scan; missing rows are not treated as withdrawals. Original SEBI and configured lead-manager source pages are retained in the workflow artifact. Collection failure retains the last good dataset and records a separate status in `ops/drhp-collection.json`. Successful refreshes verify the actual served dataset and page assets.

`verify-bse-publication.yml` is a read-only post-publication check for selected reviewed BSE manifests. Its default remains parser-v1.5 recovered reviewed batch36. `verify-reviewed-nse-publication.yml` is the corresponding NSE check after successful source sync and now selects **batch9**. Both retain actual Pages bytes and separate fetch/check/generation timestamps; neither imports records.

`audit-ipo-universe.yml` is a read-only bounded official-universe audit with no schedule. It collects eight NSE/BSE/SEBI source surfaces, verifies source hashes and reconciles identities while retaining incomplete-coverage labels. Candidates are not automatically imported. Raw Actions artifacts expire after 14 days; durable review projections and evidence references remain in the repository.

Historical corrections use dedicated one-shot reviewed workflows. The nine-IPO repair uses `materialize-historical-ipo-evidence.yml`, `publish-reviewed-historical-ipos.yml` and `verify-reviewed-historical-ipo-publication.yml`. Fabino uses `materialize-fabino-listing-evidence.yml`, `publish-reviewed-fabino.yml` and `verify-reviewed-fabino-publication.yml`. BSE historical coverage uses the read-only `audit-bse-issue-summary.yml`; the five reviewed reconciliation actions use `materialize-bse-audit-conflict-evidence.yml`, `publish-reviewed-bse-reconciliation.yml` and `verify-reviewed-bse-reconciliation-publication.yml`. These are evidence-bound release paths, not general auto-import mechanisms.

Collection time, source observation, dataset generation and Pages publication are distinct. `node scripts/operator-report.mjs` reports IPO operational health without rewriting values. DRHP collection health is separate.

## Handoff for the next prompt

**The original 2022 queue is complete: 14 reviewed/published + 2 existing-recovery alias + 0 awaiting review.** PR #327 added Droneacharya and repaired the existing FiveStar record without duplicating it. FiveStar's differently scoped offer-size disclosures remain an unresolved source conflict. The original 2021 queue is also complete; do not replay closed batches.

Next P1 batch: **Ratnaveer Precision Engineering Limited (543978)**, **Valiant Laboratories Limited (543998)**, **ESAF Small Finance Bank Ltd (544020)** and **Plaza Wires Limited (544003)** from the [2023 progress ledger](data/discovery/bse-2023-review-progress-2026-09-28.json). The original 30 candidates now have **4 reviewed/published + 26 awaiting review**. Sah, Global Surfaces, Udayshivakumar and Pyramid are published through PR #329 and live-verified; do not re-import them. Their four offer-size candidates remain provisional. Reconcile all recovery years before the next import. The [original candidate snapshot](data/discovery/bse-2023-review-queue-2026-09-28.json) and [dated 920-row audit](data/discovery/bse-retained-reconciliation-2026-09-28.json) remain unchanged; the earlier 215-candidate audit total is not a current progress count or a complete-universe claim.

Use [PROJECT_STATUS](docs/PROJECT_STATUS.md) and the pinned queues. Run `node scripts/check-bse-2023-progress.mjs`, `node scripts/check-bse-2022-disposition.mjs` and `node scripts/check-retained-bse-snapshot.mjs` before handoff. The read-only audit checks archived source hashes and rejects forged parsed projections; CI retains the reproducible full report while raw artifacts remain available.

### Exact next backend task

The remaining **0** original BSE 2022 unmatched rows need no further import. Next review **Ratnaveer Precision Engineering Limited (543978)**, **Valiant Laboratories Limited (543998)**, **ESAF Small Finance Bank Ltd (544020)** and **Plaza Wires Limited (544003)** from the separate 2023 progress ledger. The immutable source queue is evidence, not a mutable todo list. Target one four-issuer evidence family in a run when feasible, but publish only independently verified records. Discovery prices/dates never authorize publication. Resolve FiveStar's offer-size conflict only against an official final basis-of-allotment disclosure, preserving both earlier observations.

Droneacharya is published through PR #327; Five-Star is the existing `fivestar-business-finance-limited` / FIVESTAR alias, not a new issuer. The release fills its band, one-share trading lot and public offer dates while retaining the 31-share minimum bid and original identity/evidence. Maruti/Olatech and all preceding 2020–2022 releases remain complete. Keep Hariom and FiveStar source conflicts, Rainbow's existing alias, and all historical correction evidence intact. Overall Indian IPO-universe and field coverage remain incomplete.

## Historical release notes

The previous README is preserved byte-for-byte in [the release-note archive](docs/README_ARCHIVE_THROUGH_MARUTI_2026-09-28.md), original Git blob `83ceae2732ab2b095637782bab6b061d774c0a97`. Old next-task paragraphs and snapshot counts there are historical, not current instructions. Current source decisions and run receipts are in [PROJECT_STATUS](docs/PROJECT_STATUS.md) and its linked archives.
