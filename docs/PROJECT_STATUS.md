# Project status and handoff

Updated **2026-09-28 (UTC)** after closing the published and live-verified Maruti Interior Products / Olatech Solutions release. Active priority remains **P1 issuer identity and universe correctness**.

## Exact next bounded task

Continue the **2022 BSE unmatched review** with **Droneacharya Aerial Innovations Limited (543713)** and **Five-Star Business Finance Ltd. (543663)**. Reconcile names, aliases and exchange identities against all current recovery years before treating either row as missing. Retain issuer-specific official BSE/SEBI evidence and original bytes before any import. BSE issue-summary values remain discovery evidence only.

The pinned [2022 disposition](../data/discovery/bse-2022-unmatched-disposition-2026-09-27.json) now accounts for the original 16 unmatched rows as **13 reviewed/published + 1 existing-recovery alias + 2 awaiting review**. The retained source surface remains **90 official rows / 74 original exact matches / 16 original unmatched**. Resolving this queue will not, by itself, establish complete Indian IPO-universe coverage.

## Latest release — Maruti and Olatech published and live-verified

PR **#325** merged as **8c226855046eb8e8b30a272cfccc632d59e5b98c**. Publication commit **4b0853a315ad1e74cf340ce53ac11c448afdb68e** added exactly two 2022 recovery records: **Maruti Interior Products Limited** and **Olatech Solutions Limited**. This closeout reconciles the handoff with that completed release; **do not replay or duplicate the import**.

| Issuer | Board | Issue price | Issue size | Market lot | Minimum bid | Offer dates | Listing |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| Maruti Interior Products Limited | SME | INR 55 | INR 110m | 2,000 | 2,000 | 03–08 Feb-2022 | 16-Feb-2022 |
| Olatech Solutions Limited | SME | INR 27 | INR 18.9m | 4,000 | 4,000 | 12–19 Aug-2022 | 29-Aug-2022 |

Both are fixed-price SME IPOs: `price_band` remains missing. Market lot and minimum bid are separate fields with separate source pages. Unsupported exchange identifiers and minimum application amounts remain null. Raw source values, INR-lakh normalization, reporting periods, physical PDF pages, document dates and source hashes are retained in recovery; first observation and last collection use the earliest and latest retained collection respectively. They are not source publication dates.

Source collection run **36365847939** retained **4 original SEBI/BSE PDFs / 22,346,671 source bytes** in artifact **10947656355**, ZIP SHA-256 **c14bab5a36044894c54b5e9f30ffbecdd591cfd6f6329083a09b20a15b0b0c20**. The release regression covers 22 rejected mutations, before/after publication, unchanged existing records, unit normalization, read-only checks and the live-fetch contract.

Publication workflow **36367972688** completed successfully on **workflow attempt 2**. Its retained successful live snapshot was fetched **2026-09-28T02:04:21.827Z**, contains **1,366 records / 7,580,477 response bytes**, and has dataset generation **2026-09-28T01:58:22.999Z** and SHA-256 **5b37be24bbb70b6ae6073f8cfd8887885d5a2cddd78a6523c60a5f9798a43b76**. Successful live artifact **10948117298** has ZIP SHA-256 **2f1061a5b83ec5c190fd9eeaa55011fcc65f71d47526e311683c95ac3cb2745f**. Both ZIP and response hashes were independently checked during closeout. The [durable live receipt](verification/bse-2022-maruti-olatech-live-2026-09-28.json) records these as-of observations; inner `attempt-1` is the fetch loop of workflow attempt 2, not the first workflow attempt.

Merged-main data-contract run **36367972691**, reviewed-BSE run **36367972669**, and Pages deployment **36367972668** passed. Production sync **36367972667** subsequently passed NSE/SEBI collection, rebuild, validation and repository publication; operator snapshot **2026-09-28T02:11:57.537Z** recorded healthy status. Its later dataset generation **2026-09-28T01:58:31.497Z** is distinct from the retained release snapshot above. Raw artifacts expire after 14 days; durable projections, receipt hashes and URLs remain in the repository. No new browser/UI test or complete-universe claim is made.

## Handoff consistency checks

Run `node scripts/test-bse-2022-disposition.mjs` and `node scripts/check-bse-2022-disposition.mjs` before closing a 2022 batch. The read-only check reconciles declared counts, unique source rows, approved manifest references, recovery/public identities, and all current README/status next-task sections. It accepts the legacy manifest format and preserved aliases. A possible existing identity on an awaiting row is a warning requiring review, not authority to import or auto-close it. Discovery price/date disagreements are not used to rewrite published facts.

The dedicated `check-bse-2022-handoff.yml` workflow runs these checks without importing, publishing or rewriting data. IPO values, source allowlists and the public schema are unchanged by this closeout.

## Completed work — do not restart

The original BSE 2021 unmatched queue is complete. Previously released 2022 batches include Veranda/Uma, Hariom (with its unresolved issue-size source conflict), TMB/DCX, MAAGH/Technopack, Eighty/Virtuoso and PACE/Gargi. Rainbow remains an existing-recovery alias, not a new imported issuer. Their retained manifests, source receipts and historical verification records are unchanged.

Also complete: the four BSE 2020 repairs; five high-priority BSE historical reconciliations; Fabino's evidence-backed 2022 listing correction; nine excluded-event issuers' historical equity IPOs; the pinned NSE review (**105 approved IPOs + 14 non-IPO exclusions = 119 groups, no unresolved holds**). Keep excluded debt, migration and rights-security events out of the new-IPO queue. BSE parser v1.5's completed **236/236** cursor must not be replayed.

PR #319's cross-year historical identity guard remains in force: stale NSE rows for CAMS and Protean must be held against their retained recovery identities, not recreated in later years. Do not revert to year-local-only matching. Routine source refreshes and backfills may advance main; recompute publication against the latest main rather than overwriting concurrent source-backed work.

## Remaining boundaries and parallel workstreams

Overall Indian IPO-universe coverage and field/source coverage remain incomplete. After the final two original 2022 unmatched rows, continue bounded year/source-family reconciliation. SEBI historical pagination, NSE-series coverage and wider Pre-IPO lead-manager discovery remain separate gaps. Maintain observation, collection, generation and publication distinctions; preserve nulls, source conflicts and correction history. Do not enable or expand P5/performance while P4 remains blocked.

The active application-term requirement is **Lot Size only**: display verified market lot first, then verified minimum bid quantity when market lot is missing, while keeping the raw fields distinct. Minimum investment/application amount remains out of scope; do not derive it from price times quantity. Final Prospectus terms are authoritative where available; inclusion is not contingent on having a final Prospectus. Every displayed figure must remain source-backed.

The Pre-IPO view and collector remain lifecycle-aware and history-preserving; this closeout does not refresh or re-audit their coverage. UI/company-research requirements remain in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md). Keep static hosting, the light theme and standing commercial-readiness/data-rights constraints. No new spending, licensing commitments, billing, accounts, analytics, ads, infrastructure migration or access-policy changes are authorized by this closeout. Continue the sequential review, tests, CI, merge, deployment verification and handoff process in [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md).

## Preserved historical handoff

The prior canonical status is preserved **byte-for-byte** in [PROJECT_STATUS_ARCHIVE_THROUGH_PACE_GARGI_2026-09-28.md](PROJECT_STATUS_ARCHIVE_THROUGH_PACE_GARGI_2026-09-28.md), original Git blob **3fc77988cacc1950ee466aaf42a1c241b2775b47**. It retains release facts, source decisions, failed approaches and earlier run/receipt IDs. Its old next-task paragraphs are historical, not current instructions. All earlier archives, including [PROJECT_STATUS_ARCHIVE_THROUGH_PARAS_2026-09-27.md](PROJECT_STATUS_ARCHIVE_THROUGH_PARAS_2026-09-27.md), remain intact. Use this current file and the pinned disposition for the next continuation.
