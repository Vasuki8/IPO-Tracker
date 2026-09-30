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

The next four 2023 BSE candidates now have reviewed Prospectus terms **and** retained authoritative actual-listing evidence. The prepared SSEK release is still **not published**: the 2023 ledger remains **12 reviewed/published + 18 awaiting review** until the served Pages dataset is verified.

The original 2022 queue remains **14 reviewed/published + 2 existing-recovery alias + 0 awaiting review**.

The bounded scope is **SHANTI SPINTEX LIMITED (544059)**, **Shoora Designs Limited (543970)**, **Exhicon Events Media Solutions Limited (543895)** and **Khazanchi Jewellers Limited (543953)**. Reviewed actual listing dates are **27-Dec-2023**, **29-Aug-2023**, **17-Apr-2023** and **07-Aug-2023** respectively.

The guarded import is pinned by [data/verified-bse-listings/2026-09-29-ssek-2023.json](data/verified-bse-listings/2026-09-29-ssek-2023.json). The source receipt is [data/evidence/bse-2023-ssek-listing-source-receipt-2026-09-29.json](data/evidence/bse-2023-ssek-listing-source-receipt-2026-09-29.json). Artifact **11062426975** contains the four retained original annual reports and expires **13-Oct-2026**.

Board, NSE identity, ISIN and monetary minimum application amount remain null. Preserve Shanti's ₹80 Cut Off Price typo, Exhicon's Prospectus date-definition conflict, both provisional issue amounts, and the fixed-price semantics for Shoora and Khazanchi.

### Exact next backend task

Complete the pending release for **SHANTI SPINTEX LIMITED (544059)**, **Shoora Designs Limited (543970)**, **Exhicon Events Media Solutions Limited (543895)** and **Khazanchi Jewellers Limited (543953)**.

The original BSE 2022 queue has remaining **0** unmatched rows requiring import.

Finish the release lifecycle recorded in [docs/verification/bse-2023-ssek-release-2026-09-29.json](docs/verification/bse-2023-ssek-release-2026-09-29.json): merge only with a `release(ssek):` commit after final CI is green, let the temporary `reviewed_ssek` job publish against latest `main`, verify the actual served `data/ipos.json` with `scripts/verify-bse-2023-ssek.mjs`, then close the four queue rows and retire both temporary release surfaces.

Do not replay the completed IRMS, 2020–2022 or NSE releases. Continue to use `node scripts/check-bse-2023-progress.mjs`, `node scripts/build-published-data.mjs --check` and `node scripts/validate-data.mjs` as baseline guards.

## Historical release notes

The previous README is preserved byte-for-byte in [the release-note archive](docs/README_ARCHIVE_THROUGH_MARUTI_2026-09-28.md), original Git blob `83ceae2732ab2b095637782bab6b061d774c0a97`. Old next-task paragraphs and snapshot counts there are historical, not current instructions. Current source decisions and run receipts are in [PROJECT_STATUS](docs/PROJECT_STATUS.md) and its linked archives.
