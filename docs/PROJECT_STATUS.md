# Project status and handoff

Updated **2026-09-28 (UTC)** after closing the four-issuer 2023 release and adding a tested, source-preserving review-progress ledger. Active priority remains **P1 issuer identity and data correctness**.

## Exact next bounded task

Review **Ratnaveer Precision Engineering Limited (543978)**, **Valiant Laboratories Limited (543998)**, **ESAF Small Finance Bank Ltd (544020)** and **Plaza Wires Limited (544003)** as the next four-issuer 2023 evidence batch, where official evidence permits. Reconcile names, aliases and exchange identities across all current recovery years before importing. Retain original official documents and field evidence; never auto-import discovery values. The [2023 progress ledger](../data/discovery/bse-2023-review-progress-2026-09-28.json) is the current work queue; the original [2023 candidate snapshot](../data/discovery/bse-2023-review-queue-2026-09-28.json) remains immutable.

The original 2022 queue remains **14 reviewed/published + 2 existing-recovery alias + 0 awaiting review**. Of the original **30** 2023 candidates, **4 are now reviewed/published and 26 await review**. These progress counts do not update or replace the dated 920-row retained-source audit, whose 215-candidate total is an earlier observation. No complete Indian IPO-universe claim is made.

## Latest release — four 2023 IPOs verified and closed

PR **#329** merged as **7c20ed7322aeaa834efe985273506411bccb4c1e**; publication commit **d5f56485e1f7ab213e1390fb219bc7681e0a50ce** added **Sah Polymers**, **Global Surfaces**, **Udayshivakumar Infra** and **Pyramid Technoplast**. They are already published; **do not replay the import or duplicate these issuers**. A fresh local rerun during closeout skipped all four and left all **1,371 public records unchanged**.

| Issuer | Price band | Issue price | Trading lot | Minimum bid | Public offer dates | Actual listing |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Sah Polymers | INR 61–65 | INR 65 | 1 | 230 | 30-Dec-2022–04-Jan-2023 | 12-Jan-2023 |
| Global Surfaces | INR 133–140 | INR 140 | 1 | 100 | 13–15 Mar-2023 | 23-Mar-2023 |
| Udayshivakumar Infra | INR 33–35 | INR 35 | 1 | 428 | 20–23 Mar-2023 | 03-Apr-2023 |
| Pyramid Technoplast | INR 151–166 | INR 166 | 1 | 90 | 18–22 Aug-2023 | 29-Aug-2023 |

**All four total offer amounts remain provisional:** Sah INR 663m, Global INR 1,549.8m, Uday INR 660m and Pyramid INR 1,530.52m. The first three prospectuses qualify amounts as subject to finalization of the Basis of Allotment; Pyramid reports an up-to offer. These are not independently verified final realized proceeds. Trading lots and minimum bids remain separate; public offer dates exclude anchor bidding. Board and unreviewed identifiers remain null. Pyramid's 2024 landing-page label is distinct from its 2023 prospectus date; unknown PDF publication dates remain null. Existing Hariom and FiveStar conflicts are unchanged.

The two source artifacts **10951145040 / 10949889655** (runs **36375320101 / 36375618559**) retain **12 official responses: 6 PDFs, 4 SEBI landing pages and 2 BSE listing notices / 37,415,464 bytes**. All original hashes and byte lengths were independently rechecked during closeout. Physical PDF pages were rendered and visually reviewed, and original listing-notice HTML was read. Web PDF screenshots failed, so original local-byte renders were used rather than OCR or substitute third-party data. Source receipt and review remain bound to their existing manifest.

Live workflow **36377209242**, workflow attempt **1**, succeeded on fetch attempt **3**. The retained response was checked **2026-09-28T04:20:53.915Z**, generated **2026-09-28T04:19:55.164Z**, and contains **1,371 records / 7,630,323 bytes**. Response SHA-256 **b6405fc41759f1df53f0cc16cabc20a7c7fa17fc519bfe5bfe9e064978e3f4f1**. Live artifact **10951711384** has ZIP SHA-256 **397396f752fcf2b4e4868abac51795ee268d7c509c3c6ac2cab4a8eae420ced8**. The [durable receipt](verification/bse-2023-four-live-2026-09-28.json) records that historical observation, not a new source check. Archive/response hashes, byte counts and all four served record projections were independently checked during closeout. The release regression suite passes **62 rejected-mutation cases** and real builder projection checks.

## Additional work — durable 2023 progress and consistency checks

The separate [progress ledger](../data/discovery/bse-2023-review-progress-2026-09-28.json) closes four source rows without changing the immutable candidate snapshot or its hash. Run `node scripts/test-bse-2023-progress.mjs` and `node scripts/check-bse-2023-progress.mjs` before handoff. The checker binds progress to original source bytes, validates counts, approved review/manifest identity, retained live evidence, all-year recovery/public identity presence and all current README/status next-task sections. Matches on an awaiting row create a review warning, not authority to auto-import or auto-close. Discovery price/date values never rewrite published facts.

The new read-only CI workflow uses contents-read permission, leaves production data unchanged and tests **50 rejected cases**, including wrong-year duplicates, bad evidence hashes/paths, false completeness/freshness, stale handoff sections and an empty completed queue. The completed 2022 checker now scopes next-task codes to its own closed queue, allowing the 2023 handoff while still rejecting replay of completed 2022 rows. Its regression suite passes **37 rejected cases**, including all three current handoff sections. The frozen retained-universe snapshot remains intact. Original Actions artifacts expire after their retention period; durable source links, projections and hashes do not claim raw bytes are stored forever.

## Closeout verification and known test exceptions

Local broad regression executed all **86** `scripts/test-*.mjs` entry points on the release snapshot: **84 passed**, one pre-existing legacy import assertion failed, and one browser test was environment-blocked. `test-reviewed-bse-2020-unmatched-import.mjs` fails with `collision:likhitha-infrastructure-limited` on both untouched main snapshot `d5f56485e1f7ab213e1390fb219bc7681e0a50ce` and this closeout. Do not weaken the old importer's changed-evidence guard or replay its completed release; repair the legacy test in a separate bounded task. `test-ui.mjs` could not start because Playwright is not installed in the local runtime; this is not a browser pass or a discovered UI assertion failure. The aggregate NSE import test initially exceeded a 12-second local harness limit, then passed with a full allowance. These exceptions do not replace PR-head or post-merge CI verification.

The new 2023 progress check, completed-2022 transition tests, four-issuer release regression, frozen snapshot checks, public-data builder and data validator passed. No production IPO object, immutable discovery queue, historical audit receipt or source manifest was changed by this closeout. Review was performed inline; no independent reviewer or new interactive browser verification is claimed.

## Previous release — final 2022 pair and FiveStar repair

PR **#327** merged as **f569f249f6fb90d2f77b584b5c419afecc103e0e**. Publication **74ef09c365fad379366b9eba56a857345e7ff0a2** added one issuer, **Droneacharya Aerial Innovations Limited**, and repaired the existing **FiveStar Business Finance Limited / FIVESTAR** record. Do not create a second Five-Star issuer or replay the import.

Droneacharya: BSE SME, book-built band INR 52–54, issue price INR 54, total issue INR 339.66m, trading lot 2,000 and separately evidenced minimum bid 2,000; public offer 13–15 December 2022, actual listing 23 December 2022. Anchor bidding was 12 December and is not the public opening. SEBI's later order is used only for its explicit historical listing statement, not a current regulatory-status inference.

FiveStar: filled four missing fields—band INR 450–474, trading lot **1 share**, public dates 9–11 November 2022. Existing minimum bid **31 shares**, listing 21 November, issue price 474, stable ID, issuer spelling, NSE identity and first-observed timestamp remain unchanged. Anchor date 7 November is not the public opening.

**FiveStar offer size remains an unresolved scope/stage conflict.** The retained NSE initial offer describes up to INR 19,600.05m including anchor allocation; the later Final Prospectus reports INR 15,934.49m **subject to finalization of Basis of Allotment**, excluding multiple bids and bids not banked. The public field prefers the prospectus candidate with `status: conflict`, both source observations and an explicit correction note. Do not call it verified or finalized proceeds. Reconcile an official final basis-of-allotment disclosure before resolving it. Hariom's earlier conflict is unchanged.

Source run **36371487755**, artifact **10948564535**, retained **3 PDFs + 3 landing responses / 14,006,299 response bytes**; ZIP SHA-256 **be4bfc110ccb1aba363e0f99f82f805de8dccb88305d2c70b33eea166cfbf23a**. Original hashes/lengths and physical PDF pages were checked. Unknown PDF publication dates remain null; FiveStar's November-2022-labelled landing page currently links a May-2023-path PDF whose cover is dated 15 November 2022. Those clocks are not interchangeable.

Release tests passed **46 rejected-mutation cases**, the real builder/validator, rerun safety, all 1,365 unrelated records unchanged, alias collision rejection, source hash/unit/page binding, public/anchor dates, market-lot/minimum-bid distinction and live-fetch projection. All PR-head and merged-main data-contract/reviewed-BSE checks passed. Workflow **36373086633**, workflow attempt 1, succeeded on live fetch attempt 3. The retained successful snapshot was fetched **2026-09-28T03:18:01.629Z**, generated **2026-09-28T03:17:00.726Z**, and contains **1,367 records / 7,596,148 response bytes**. Response SHA-256 **ecea0544bc585e5a7e6d1b3e1c445113908ef66c65fb2be06d33f35c4d55d418**. Live artifact **10950101413** ZIP SHA-256 **71f693bd6cae4992353554e292f633a2f7f11bf7d194419d4508b2a5fc4e48c1**. See the [durable receipt](verification/bse-2022-final-pair-live-2026-09-28.json).

## Retained BSE universe reconciliation — additional work this run

The [dated audit receipt](../data/discovery/bse-retained-reconciliation-2026-09-28.json) rechecks all **16 original responses / 296,942 bytes** against pinned SHA-256 hashes and reconstructs the parsed year rows from raw bytes before comparing them. It rejects a forged saved projection even when the archived raw files are unchanged. It is read-only and does not collect or publish IPOs. Source observation remains **2026-09-26T16:40:34.440Z**; reconciliation is **2026-09-28T03:21:52.783Z** against publication commit **74ef09c365fad379366b9eba56a857345e7ff0a2**, plus the separately hash-pinned closeout alias dispositions.

| Retained year | Source rows | Exact matches | Reviewed aliases | Awaiting review |
| --- | ---: | ---: | ---: | ---: |
| 2020 | 31 | 31 | 0 | 0 |
| 2021 | 91 | 90 | 1 | 0 |
| 2022 | 90 | 88 | 2 | 0 |
| 2023 | 120 | 90 | 0 | 30 |
| 2024 | 158 | 120 | 0 | 38 |
| 2025 | 255 | 164 | 0 | 91 |
| 2026 | 175 | 119 | 0 | 56 |
| **Total** | **920** | **702** | **3** | **215** |

These are identity-reconciliation counts, not 705 independently re-reviewed prospectuses or a field-completeness audit. Explicit reviewed aliases are linked; approximate names and code-only hints remain review candidates, never automatic matches/imports. The immutable 30-row 2023 discovery snapshot preserves original row numbers and hashes. It proposed the first four names as of that audit; use the separate progress ledger above for the current batch. The audit itself imported no 2023 IPOs.

Two provenance exceptions are preserved: the compact original pin labels source commit **460df3b91a509b82b30c7e5630cfcf83de784842**, while the retained collection archive labels **fb81541413afd32a2fc1eddf10d29fff4ad20cd1**. All raw response hashes and parsed projections match; the commit-label discrepancy is disclosed, not silently repaired. The 2024 TRAFIKSOL source row has no usable BSE scrip code and remains held rather than receiving an invented code.

The full row-level report is reproducible from source artifact **10910707544**, ZIP SHA-256 **5105397fdae479e05e46528ecb2cf7665f3f329c6cbae74169ac9dc64b35cac5**, the pinned recovery commit and alias files. It is attached to the closeout CI archive while original raw artifacts remain available and is also provided with the conversation. Raw Actions artifacts expire; the committed compact receipt, 2023 queue and input/output hashes remain. A missing/expired replay archive is explicitly reported, not presented as a successful source check.

## Handoff and audit tests

Run `node scripts/test-bse-2022-disposition.mjs`, `node scripts/check-bse-2022-disposition.mjs`, `node scripts/test-retained-bse-universe.mjs`, `node scripts/test-retained-bse-snapshot.mjs` and `node scripts/check-retained-bse-snapshot.mjs`. The new universe test covers **19 rejected cases**, raw/projection tampering, alias identity binding, cross-year/date holds, missing codes, source-clock separation and non-mutation. Snapshot tests additionally validate the committed report/queue counts and boundaries. CI does not rewrite production data. All previous archives, data conflicts and reviewed manifests remain intact.

## Previous release — Maruti and Olatech

PR #325 and closeout #326 remain complete. Maruti (INR 55, INR 110m, lot/minimum 2,000, public 3–8 February 2022, listed 16 February) and Olatech (INR 27, INR 18.9m, lot/minimum 4,000, public 12–19 August 2022, listed 29 August) are already published. Original source artifact 10947656355 and [live receipt](verification/bse-2022-maruti-olatech-live-2026-09-28.json) remain intact. No prior imports or historical correction records were changed by the audit closeout.

## Completed work — do not restart

The original BSE 2021 unmatched queue is complete. Previously released 2022 batches include Veranda/Uma, Hariom (with its unresolved issue-size source conflict), TMB/DCX, MAAGH/Technopack, Eighty/Virtuoso and PACE/Gargi. Rainbow remains an existing-recovery alias, not a new imported issuer. Their retained manifests, source receipts and historical verification records are unchanged.

Also complete: the four BSE 2020 repairs; five high-priority BSE historical reconciliations; Fabino's evidence-backed 2022 listing correction; nine excluded-event issuers' historical equity IPOs; the pinned NSE review (**105 approved IPOs + 14 non-IPO exclusions = 119 groups, no unresolved holds**). Keep excluded debt, migration and rights-security events out of the new-IPO queue. BSE parser v1.5's completed **236/236** cursor must not be replayed.

PR #319's cross-year historical identity guard remains in force: stale NSE rows for CAMS and Protean must be held against their retained recovery identities, not recreated in later years. Do not revert to year-local-only matching. Routine source refreshes and backfills may advance main; recompute publication against the latest main rather than overwriting concurrent source-backed work.

## Remaining boundaries and parallel workstreams

Overall Indian IPO-universe coverage and field/source coverage remain incomplete. The original 2022 queue is complete; continue with the pinned 2023 candidates and later retained years. SEBI historical pagination, NSE-series coverage and wider Pre-IPO lead-manager discovery remain separate gaps. Maintain observation, collection, generation and publication distinctions; preserve nulls, source conflicts and correction history. Do not enable or expand P5/performance while P4 remains blocked.

The active application-term requirement is **Lot Size only**: display verified market lot first, then verified minimum bid quantity when market lot is missing, while keeping the raw fields distinct. Minimum investment/application amount remains out of scope; do not derive it from price times quantity. Final Prospectus terms are authoritative where available; inclusion is not contingent on having a final Prospectus. Every displayed figure must remain source-backed.

The Pre-IPO view and collector remain lifecycle-aware and history-preserving; this closeout does not refresh or re-audit their coverage. UI/company-research requirements remain in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md). Keep static hosting, the light theme and standing commercial-readiness/data-rights constraints. No new spending, licensing commitments, billing, accounts, analytics, ads, infrastructure migration or access-policy changes are authorized by this closeout. Continue the sequential review, tests, CI, merge, deployment verification and handoff process in [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md).

## Preserved historical handoff

The prior canonical status is preserved **byte-for-byte** in [PROJECT_STATUS_ARCHIVE_THROUGH_PACE_GARGI_2026-09-28.md](PROJECT_STATUS_ARCHIVE_THROUGH_PACE_GARGI_2026-09-28.md), original Git blob **3fc77988cacc1950ee466aaf42a1c241b2775b47**. It retains release facts, source decisions, failed approaches and earlier run/receipt IDs. Its old next-task paragraphs are historical, not current instructions. All earlier archives, including [PROJECT_STATUS_ARCHIVE_THROUGH_PARAS_2026-09-27.md](PROJECT_STATUS_ARCHIVE_THROUGH_PARAS_2026-09-27.md), remain intact. Use this current file and the pinned disposition for the next continuation.
