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

Completed historical one-shot publication/materialization workflows have been retired from current main; their evidence and Git history remain intact. The [retirement record](docs/verification/completed-release-workflow-retirement-2026-09-28.md) covers the retired writer and redundant-validator surfaces, with completed releases checked through one read-only validator. PR #342's temporary bounded publisher was removed after verified live closeout in PR #343.

Collection time, source observation, dataset generation and Pages publication are distinct. `node scripts/operator-report.mjs` reports IPO operational health without rewriting values. DRHP collection health is separate.

`collect-bse-2023-irms-evidence.yml` remains a read-only historical/manual collector for the now-closed IRMS source set; it does not authorize replay or publication. The [multi-attempt source receipt](data/evidence/bse-2023-irms-source-receipt-2026-09-28.json) retains both partial outcomes and the exact source selections used for the completed review.

## Handoff for the next prompt

The IREDA/Motisons/RBZ/Shelter release is complete and live-verified. The 2023 immutable review ledger is now **12 reviewed/published + 18 awaiting review**. The bounded IRMS publisher is retired; do not replay the completed import.

Continue with **SHANTI SPINTEX LIMITED (544059)**, **Shoora Designs Limited (543970)**, **Exhicon Events Media Solutions Limited (543895)** and **Khazanchi Jewellers Limited (543953)**. Start with official source retention and all-year identity reconciliation, then prepare a separately reviewed bounded import only for unambiguous evidence-backed identities.

**The original 2022 queue is complete: 14 reviewed/published + 2 existing-recovery alias + 0 awaiting review.** The original 2021 queue is also complete. Preserve historical conflicts, aliases, evidence hashes and nulls; never replay completed releases.

Repository hardening is recorded in [PROJECT_STATUS](docs/PROJECT_STATUS.md). Administration/legal follow-ups remain tracked in issues #339, #347 and #348.

### Exact next backend task

The original BSE 2022 queue has remaining **0** unmatched rows requiring import.

Review **SHANTI SPINTEX LIMITED (544059)**, **Shoora Designs Limited (543970)**, **Exhicon Events Media Solutions Limited (543895)** and **Khazanchi Jewellers Limited (543953)** from the pinned 2023 queue. Do not treat discovery values as publication authority. Retain original official evidence, reconcile identity across every recovery year, preserve conflicts/nulls, and only publish after a separate reviewed manifest and exact served verification.

Use `node scripts/check-bse-2023-progress.mjs`, `node scripts/check-bse-2022-disposition.mjs`, `node scripts/check-retained-bse-snapshot.mjs`, `node scripts/build-published-data.mjs --check` and `node scripts/validate-data.mjs` as baseline guards. The completed IRMS live receipt is [docs/verification/bse-2023-irms-live-2026-09-29.json](docs/verification/bse-2023-irms-live-2026-09-29.json).

## Historical release notes

The previous README is preserved byte-for-byte in [the release-note archive](docs/README_ARCHIVE_THROUGH_MARUTI_2026-09-28.md), original Git blob `83ceae2732ab2b095637782bab6b061d774c0a97`. Old next-task paragraphs and snapshot counts there are historical, not current instructions. Current source decisions and run receipts are in [PROJECT_STATUS](docs/PROJECT_STATUS.md) and its linked archives.
