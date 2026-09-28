# Project status and handoff

Updated **2026-09-28 (UTC)** after publishing Ratnaveer, Valiant, ESAF and Plaza and repairing the completed 2020 release test/workflow. Active priority remains **P1 issuer identity and data correctness**.

## Exact next bounded task

Review **Indian Renewable Energy Development Agency Limited (544026)**, **Motisons Jewellers Limited (544053)**, **RBZ Jewellers Limited (544060)** and **SHELTER PHARMA LIMITED (543963)** as the next four-issuer 2023 evidence batch, where original official sources permit. Reconcile names, aliases and exchange identities across all current recovery years before importing. The [2023 progress ledger](../data/discovery/bse-2023-review-progress-2026-09-28.json) records **8 reviewed/published + 22 awaiting review** from the original 30 candidates. The [original discovery queue](../data/discovery/bse-2023-review-queue-2026-09-28.json) remains immutable; its source observation is not refreshed by this release. Discovery values never authorize publication.

The original 2022 queue remains **14 reviewed/published + 2 existing-recovery alias + 0 awaiting review**. The original 2021 queue is also complete. These bounded review counts do not establish complete Indian IPO coverage or update the dated 920-row audit.

## Latest backend release

PR **#332**, merge **43213e3bf7eb942348904a2654b21429e3fd4c3e**, published four new identities through data commit **862800b3265f053239e78d41b77a7c9cdc79078a**. **Do not replay or duplicate this batch.** The bounded importer rechecks all recovery years on latest main; actual publication writes only 2023 recovery and generated public data.

| Issuer | Price band | Issue price | Trading lot | Minimum bid | Public offer | Actual listing |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Ratnaveer Precision Engineering | INR 93–98 | INR 98 | 1 | 150 | 04–06 Sep-2023 | 11-Sep-2023 |
| Valiant Laboratories | INR 133–140 | INR 140 | 1 | Missing | 27-Sep–03-Oct-2023 | 06-Oct-2023 |
| ESAF Small Finance Bank | INR 57–60 | INR 60 | 1 | 250 | 03–07 Nov-2023 | 10-Nov-2023 |
| Plaza Wires | INR 51–54 | INR 54 | 1 | 277 | 29-Sep–05-Oct-2023 | 12-Oct-2023 |

The batch contains **27 verified core fields, 3 provisional offer amounts, 1 conflicting amount and 1 missing minimum bid**. Trading lot and minimum bid remain distinct. Public opening excludes anchor dates. Unsupported board, exchange identifiers and minimum application amounts remain null. Unknown PDF publication dates remain null; document, collection, generation and publication clocks remain separate.

### Evidence qualifications and held values

**Valiant offer amount remains a conflict**, not a verified final figure. Prefer the audited annual-report candidate **INR 152.46 crore** on physical PDF page 70 while retaining the narrative **INR 2152.46 crore** on page 22, both evidence locations and an unresolved correction. A separate paragraph also uses inconsistent offer-for-sale wording; do not infer issuer versus selling-shareholder proceeds from it.

**Valiant minimum bid remains missing.** Its SEBI RHP has an unfilled Bid Lot placeholder; its annual report says generic lot size 105 without establishing minimum-bid scope. The issuer-hosted final prospectus was retained and reviewed but is outside the existing publication-source allowlist. Do not disguise it as a SEBI mirror or relax source policy. Seek an approved official final-prospectus/basis-of-allotment mirror before filling the held field. Inclusion is not conditional on a complete final prospectus record.

Ratnaveer's **INR 1,650.32m** total offer is an up-to amount; ESAF's **INR 4,630m** and Plaza's **INR 712.81m** are subject to finalisation of Basis of Allotment. All three remain **provisional**, not independently verified realised proceeds. ESAF's total includes fresh issue, OFS and employee discount; never replace it with share count times the standard price.

Ratnaveer's original BSE listing notice **20230908-27** confirms 11-Sep-2023 independently of its annual report's inconsistent 2023/2024 dates. The annual report remains research-only. Plaza's repeated 2023 listing statement is retained, and a separate paragraph's 2013 typo is disclosed as a document inconsistency. Existing Hariom and FiveStar conflicts are unchanged.

## Source retention and live verification

Three source archives **10953446028 / 10953042025 / 10953436312**, from runs **36381885986 / 36382120949 / 36382669312**, contain **12 approved SEBI/BSE responses (7 PDFs, 4 landing pages, 1 BSE listing notice) / 52,112,571 bytes**. Four separate research-only responses bring total retained original response bytes to **74,968,732**. ZIP hashes, every original response hash/length, document identity, physical page evidence and source roles were checked. Web PDF screenshots failed; local original-byte renders were used, not OCR. The [source receipt](../data/evidence/bse-2023-rvpe-source-receipt-2026-09-28.json) and review remain content-bound to the approved manifest. Public source hosts are unchanged.

Publication workflow **36384623274**, workflow attempt **1**, passed live verification on fetch attempt **3**. Actual served response checked **2026-09-28T06:05:20.242Z**: **1,375 records / 7,669,260 bytes**, generated **2026-09-28T06:04:20.542Z**. Response SHA-256 **a658ac8569b27175562d7a54d45b117eed416cf4126e6271c58db074fa694e47**. Artifact **10954400168**, ZIP SHA-256 **88d8ebb749d24cb23e304c35a2cf083f123d75a6f448cef0930a8c286ed83feb**. The [durable live receipt](verification/bse-2023-rvpe-live-2026-09-28.json) is an as-of observation, not a fresh source collection. ZIP/response bytes and all four exact public projections were independently rechecked. Raw Actions artifacts expire after 14 days; hashes/URLs/projections remain, not a claim of permanent raw-byte storage.

## Additional backend reliability repair

The legacy 2020 test incorrectly replayed its exact one-shot importer against legitimately enriched production recovery, causing `collision:likhitha-infrastructure-limited`. It now exercises an isolated before-import, after-import and rerun fixture, checks all unrelated records, and proves six price/timestamp/document enrichment mutations are rejected without touching production. **The production importer's collision guard is unchanged.**

Initial PR CI exposed a second replay path in `publish-reviewed-bse-2020-unmatched.yml`. This completed historical workflow now performs read-only review/lifecycle/build/validation checks. Its direct production import, commit and push steps were removed, and its job uses contents-read permission. `test-completed-bse-2020-workflow.mjs` prevents reintroducing replay. Do not reactivate that completed batch or weaken its importer to make enriched data fit an old snapshot. Historical manifests and evidence remain intact.

## Tests and verification commands

Final local backend run: **87 non-browser test entry points passed, zero failures**. The new batch covers **75 rejected mutations**, unit/page/source/clock binding, qualifications, conflict evidence, held nulls, cross-year collisions and the live-fetch contract. Real rehearsal added exactly four records, **1,371 to 1,375**, with all **1,371 existing public objects unchanged**; production inputs were then restored locally. Final uploaded code tree **5f0557124bfdc7b0e380464277da8337ada19dd7** matched the tested tree exactly. All seven final PR-head CI workflows passed before merge. Browser `test-ui.mjs` was not run because local Playwright is unavailable; this is not a UI/browser pass. Review was performed inline.

Before continuation run `node scripts/test-reviewed-bse-2023-rvpe.mjs`, `node scripts/test-reviewed-bse-2020-unmatched-import.mjs`, `node scripts/test-completed-bse-2020-workflow.mjs`, `node scripts/test-bse-2023-progress.mjs`, `node scripts/check-bse-2023-progress.mjs`, `node scripts/check-bse-2022-disposition.mjs`, `node scripts/check-retained-bse-snapshot.mjs`, `node scripts/build-published-data.mjs --check` and `node scripts/validate-data.mjs`. A pending matching identity warns; it never authorizes automatic import or closeout. Recompute publication against current main rather than overwrite concurrent collector work.

## Preserved product, history and boundaries

The prior canonical handoff is preserved **byte-for-byte** in [the four-issuer history archive](PROJECT_STATUS_ARCHIVE_THROUGH_FOUR_2023_2026-09-28.md), Git blob **b8fb9a3849c23cb21739bb3ad1a739a2ef488a01**. It contains the full 2020–2026 retained audit, old source-commit label discrepancy, TRAFIKSOL missing-code hold, and all earlier release/receipt references. Its next-task paragraphs and former legacy-test failure are historical, not current instructions.

The original 920-row audit and 30-row discovery snapshot are unchanged. Its earlier 215-candidate total is not this release's current work-queue count. Sah/Global/Uday/Pyramid, the final 2022 pair, all previous 2020–2022 imports, reviewed NSE batches and parser-v1.5's completed 236/236 cursor must not be replayed. Preserve Rainbow/FiveStar aliases and CAMS/Protean cross-year guards. FiveStar's differently scoped offer-size conflict requires official final Basis of Allotment evidence; do not label it final proceeds.

PR #330's light-theme UI and [UI design handoff](UI_DESIGN_HANDOFF.md) are preserved. That UI release recorded deployment success but not direct served-asset/browser verification; this backend JSON check does not remove that limitation. No UI, app logic, source allowlist or public schema changed here. The active application term remains **Lot Size only**, verified market lot first, then verified minimum bid when market lot is missing. Never derive minimum investment/application amounts. Preserve lifecycle-aware Pre-IPO history and partial coverage labels.

Overall universe and field coverage remain incomplete. Continue P1 and source repairs; **do not expand P5/performance while P4 is blocked**. Keep static hosting, commercial data-rights constraints, and no new spending/contracts/accounts/billing/analytics/ads/infrastructure or account-access changes without approval. Follow [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md), with tests, CI, deployment evidence and handoff updates.
