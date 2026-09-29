# Project status and handoff

Updated **2026-09-29 (UTC)** for **PR #342**, the bounded IREDA/Motisons/RBZ/Shelter actual-listing review and import. Active priority remains **P1 issuer identity and data correctness**. Original listing evidence and the reviewed importer are ready; **final CI, data publication and live verification are pending**. No queue row is closed by preparation alone.

## Exact next bounded task

Finish the reviewed publication of **Indian Renewable Energy Development Agency Limited (544026)**, **Motisons Jewellers Limited (544053)**, **RBZ Jewellers Limited (544060)** and **SHELTER PHARMA LIMITED (543963)** through the [approved manifest](../data/verified-bse-listings/2026-09-29-irms-2023.json). Original actual-listing evidence is now reviewed; do not redo prospectus or listing research. Recheck latest recovery across every year and preserve all unrelated records. Inspect the [release lifecycle](verification/bse-2023-irms-release-2026-09-29.json) before attempting anything: do not replay a completed import.

After publication, verify the four exact served projections, retain actual response bytes and receipt, retire the bounded `reviewed_irms` job from the existing active updater, and only then close these progress rows. The [2023 progress ledger](../data/discovery/bse-2023-review-progress-2026-09-28.json) remains **8 reviewed/published + 22 awaiting review** from the original 30 candidates. The original queue and its **2026-09-26T16:40:34.440Z** source observation remain unchanged. The original 2022 queue remains **14 reviewed/published + 2 existing-recovery alias + 0 awaiting review**; 2021 is also complete. These are bounded queue counts, not complete IPO-universe claims.

## Reviewed source findings

Four original exchange-hosted annual reports, **31,582,979 response bytes**, establish actual equity listings: IREDA **29-Nov-2023**, Motisons **26-Dec-2023**, RBZ **27-Dec-2023**, Shelter **23-Aug-2023**. Primary physical PDF pages are **93, 38, 20 and 42**, respectively. RBZ physical page 20 is a two-page spread; its listing statement is on printed page 37. Explicit BSE codes for all four and NSE symbols for the first three are retained with identity evidence. Board, unreviewed ISIN, Shelter NSE symbol and minimum application amounts remain null.

The [listing review](../data/discovery/bse-2023-irms-listing-review-2026-09-29.json) references the immutable PR #336 prospectus review; it does not rewrite its former listing holds, source clocks or provisional qualifications. Unknown PDF publication dates remain null. Dated covering letters/AGM notice are identified separately from actual publication and collection.

**IREDA offer total is an unresolved conflict.** Retain the final-prospectus candidate **INR 21,502.12 million**, originally provisional and subject to finalisation of Basis of Allotment. The annual report, physical page 38, states **INR 2,150.22 crore**, a normalized difference of **INR 80,000**. Preserve both observations, source evidence and correction history. Do not resolve this by rounding or call either candidate independently verified realised proceeds. The importer normalizes decimal money exactly instead of using binary-floating-point equality.

Motisons and RBZ offer totals remain **provisional**. Shelter retains its exact stated fixed-price gross issue amount, not an invented book-building band or a new realised-proceeds claim. Its band remains publicly null/missing. Historical trading lot and retail minimum bid remain distinct: **1/460, 1/250, 1/150, 3000/3000**. Public opening dates remain separate from anchor dates.

Motisons physical page 13 gives an inconsistent **02-Aug-2023 approval date** alongside its December IPO. That approval-date paragraph is not used as actual-listing authority; the **26-Dec-2023** listing is repeated elsewhere, including the explicit scrip-code statement on physical page 38. The discrepancy is retained, not silently corrected.

## Original bytes, failures and retention

Successful source run **36578204890**, attempt **1**, artifact **11038004780**, retained the four linked exchange-hosted originals. ZIP SHA-256 **d2cd559feb46f05867c9b9700d26f4f3570e966ab8ad68e00a0f261b6f04fd07** and every PDF hash/length were independently checked. IREDA was fetched directly from the approved `nsearchives.nseindia.com` host; it is not mislabeled as a different mirror. No public source allowlist changed. Web PDF screenshots failed; original-byte local renders and extracted text were used without OCR.

Initial source run **36577257607**, artifact **11037723554**, tried four conventional BSE annual-report paths and received **four HTTP 404 responses**. Those rejected bodies and the failed collection remain retained in the [source receipt](../data/evidence/bse-2023-irms-listing-source-receipt-2026-09-29.json). Neither failures nor old PR #334 partial collections were relabeled successful. The temporary research workflow is removed from the final tree.

New raw source artifacts expire **13-Oct-2026** after 14 days. The earlier prospectus artifacts expire **12-Oct-2026**. Hashes and durable metadata are not permanent raw-PDF storage. Retrieve original archives before expiry, or record a genuinely new collection and compare hashes.

## Tests and controlled publication

The existing baseline has **92 non-browser test entry points**, passed in source-research CI. Local baseline execution hit an overall command timeout after earlier completed tests and was continued separately; no timeout is claimed as a suite pass. The new **63 targeted cases pass locally**, including source binding, decimal normalization, nulls, field qualifications, all-year identity collisions, rejection of replay over later enrichment, exact live-projection checks and writer-retirement guards. New guards were observed red before their implementations, then green.

The real local rehearsal added **exactly four records, 1,378 to 1,382**, with **all 1,378 existing public objects unchanged**, all six other recovery-year files byte-identical, and all four new projections matching the normal public builder. Production inputs were restored byte-for-byte afterwards. This is an offline rehearsal, not live publication. Its receipt is included in the release lifecycle.

The bounded offline publisher uses **only the existing `update-ipos.yml` writer**, gated by a push commit message beginning `release(irms):`. It is not scheduled; ordinary hourly sync keeps its existing schedule. It re-fetches current main, applies the fully pinned approval with all-year guards, rebuilds normally, checks every prior public object and only stages 2023 recovery plus `data/ipos.json`. It must be removed after verified closeout. The six-workflow production-writer allowlist and all 26 historical workflow retirements remain unchanged.

Final PR-head tests/merge/deployment evidence belongs in the release lifecycle; do not substitute earlier research CI for final verification. Review is inline, not independent-agent review. Browser/UI tests are not claimed.

## Preserved history and product boundaries

The prior canonical handoff is preserved byte-for-byte in [the IRMS-field archive](PROJECT_STATUS_ARCHIVE_THROUGH_IRMS_FIELDS_2026-09-29.md), Git blob **98719874e29169fa57c21f6077dc3f83d6069a50**. It retains PR #334/#336 source history, earlier release receipts, and the stale-PR retirement review. **PR #196 and PR #246 remain closed unmerged**. Preserve [completed-workflow retirement](verification/completed-release-workflow-retirement-2026-09-28.md), the read-only completed 2020 validator, and the newer scheduled-operation monitor.

Do not replay RVPE, Sah/Global/Uday/Pyramid, earlier 2020–2022 releases, reviewed NSE batches or parser-v1.5's completed cursor. Preserve Valiant/Hariom/FiveStar conflicts, Rainbow/FiveStar aliases, CAMS/Protean cross-year safeguards and the immutable original 920-row audit. The old 215-candidate audit count is not a current queue total.

No UI, public schema, source allowlist or commercial feature changes. Preserve light-theme UI, lifecycle-aware Pre-IPO filtering and incomplete-coverage labels. The active application term remains **Lot Size only**, verified market lot first and verified minimum bid only when market lot is missing. Never derive minimum investment amounts. Continue P1; **do not expand P5/performance while P4 is blocked**. No new spending, contracts, accounts, analytics, ads, billing, infrastructure or access changes without approval. Follow [DEVELOPMENT_PROCESS](DEVELOPMENT_PROCESS.md).
