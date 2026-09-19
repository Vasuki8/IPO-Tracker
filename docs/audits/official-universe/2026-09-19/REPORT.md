# Official IPO-universe continuation — 19 September 2026

**Coverage remains incomplete.** This continuation starts from `be97b7966e647601141116447421af5c2d72634e` and preserves the completed audit/admissions #145–148 and active-term repairs #158–161. It reviews all 25 unmatched BSE July/August candidates and repairs the unresolved SEBI draft pagination through dated cohorts. It is an identity/lifecycle audit, not a financial backfill or P5 expansion.

## Inclusion and matching contract

| Universe dimension | Inclusion rule |
|---|---|
| Mainboard | Include explicit exchange Mainboard/EQ identity; do not infer board from a SEBI filing. |
| SME | Include explicit exchange SME identity; do not merge with a Mainboard observation without migration evidence. |
| Draft / UDRHP | Keep primary drafts and supplementary filings as filing observations. Filing alone never means upcoming. |
| RHP | Retain the RHP stage separately; do not infer issue dates from its register membership. |
| Final Prospectus | Retain final-register membership and exact title. Numerical authority still requires actual Final Prospectus field review. |
| Open/current | Use explicit official exchange status and dates; preserve observations and their collection clocks. |
| Upcoming | Require official lifecycle/issue-window evidence, not a draft title. |
| Completed/listed | Historical BSE means a closed issue observation; listing stays unknown unless separately evidenced. |
| Withdrawn/cancelled | Preserve explicit official notices; a withdrawal option is not cancellation of an entire issue. No exhaustive cancellation register is claimed. |
| Non-IPO / uncertain instruments | Retain rights, debt, call-money and trust observations outside the candidate denominator. BSE FPO here labels fixed-price public issues; it is not automatically a follow-on offer. |

Deterministic normalization retains meaningful company words while handling Ltd/Limited, punctuation, case, spacing and ampersands. Exact published names/titles, filing suffixes, stages, aliases, board differences and repeated observations remain in the machine report. Similarity only opens a review; no fuzzy merge or newest-value selection is accepted. Five previously source-reviewed aliases are replayed unchanged.

## Exact observed denominators

Denominators are distinct observed equity-public-issue candidate records, not unique companies or all Indian IPOs. SEBI rows are filings; exchange rows are issue observations. Duplicate raw rows and non-candidate instruments remain in `records.jsonl`. Missing means no deterministic name/approved-alias match, not automatic eligibility for admission.

| Source | Candidate records | Matched | Rate | Missing-name rows | Identity review | Unverified |
|---|---:|---:|---:|---:|---:|---:|
| BSE | 1,848 | 588 | 31.82% | 1,250 | 10 | 0 |
| NSE | 174 | 173 | 99.43% | 1 | 0 | 0 |
| SEBI | 5,858 | 2,618 | 44.69% | 3,090 | 47 | 103 |

There are **2,148 unmatched normalized candidate names** across these cohorts and **227 tracker-only records**. The latter are not proved invalid. `comparison.json` separates new source coverage from the 25 reviewed additions. BSE matches rise 563 → 588. Its missing rows decrease by 26 because one additional spelling collision moves to explicit review, not because a twenty-sixth issuer was added.

| Source | Period / retained evidence | Limitation |
|---|---|---|
| NSE | Retained current/upcoming observations, 2025 Q1 and 2026-01-01–2026-09-18 history; original collection dates retained. | New 2025 Q2, 2024 Q4, 2020 Q1 and 2015 Q1 attempts each timed out after 35 seconds. Earlier annual failures remain. No global total or full historical coverage. |
| BSE | Returned book-building archive: 1,282 rows from 2002; fixed-price archive: 558 rows from 2010; eight current rows, all retained from 18 September. Twenty-five detail identities freshly checked on 19 September. | Returned archive has no independent exchange-wide total/history-start guarantee; current fixed-price and main-host gaps remain. |
| SEBI | Retained RHP (1,270), final-offer (1,560), Other Documents (818) traversals; new draft windows cover 2004-01-01–2026-09-19. | Board remains unknown unless separately established. Pre-2004 draft history and dedicated SME/cancellation completeness are not claimed. Unfiltered draft inconsistencies remain visible. |

NSE’s unmatched Adani Enterprises event remains unadmitted: the retained EQ API row may relate to partly paid rights/call-money, and its exact event classification is unresolved. No exclusion was invented to improve the rate.

## SEBI draft traversal recovery

The earlier unfiltered traversal mixed totals of 2,208/2,210 and repeated 43 primary URLs. A fresh unfiltered probe reproduced that inconsistency. Dated annual windows recover the historical years; the 2026 annual response still repeats three URLs, so it is explicitly incomplete. Nine monthly windows resolve 2026 instead. The selected **22 annual + nine monthly windows contain 2,210 rows and 2,210 unique primary URLs**, recovering **45 previously uncaptured filing URLs**. All old rows, failures and inconsistent windows are preserved; only reporting deduplicates source identities. The 2024 annual timeout was retried once and recovered.

The complete selected window denominators and recovered documents are in `draft-recovery.json`; every window’s dates, reported total, page coverage and duplicates are in `audit.json`. A successful window does not establish global IPO coverage.

| Selected draft period | Reported / captured rows | Pages | Traversal reconciled |
|---|---:|---:|---|
| 2004-01-01–2004-12-31 | 33 / 33 | 2 | Yes |
| 2005-01-01–2005-12-31 | 116 / 116 | 5 | Yes |
| 2006-01-01–2006-12-31 | 187 / 187 | 8 | Yes |
| 2007-01-01–2007-12-31 | 138 / 138 | 6 | Yes |
| 2008-01-01–2008-12-31 | 66 / 66 | 3 | Yes |
| 2009-01-01–2009-12-31 | 64 / 64 | 3 | Yes |
| 2010-01-01–2010-12-31 | 128 / 128 | 6 | Yes |
| 2011-01-01–2011-12-31 | 90 / 90 | 4 | Yes |
| 2012-01-01–2012-12-31 | 27 / 27 | 2 | Yes |
| 2013-01-01–2013-12-31 | 20 / 20 | 1 | Yes |
| 2014-01-01–2014-12-31 | 20 / 20 | 1 | Yes |
| 2015-01-01–2015-12-31 | 46 / 46 | 2 | Yes |
| 2016-01-01–2016-12-31 | 34 / 34 | 2 | Yes |
| 2017-01-01–2017-12-31 | 60 / 60 | 3 | Yes |
| 2018-01-01–2018-12-31 | 90 / 90 | 4 | Yes |
| 2019-01-01–2019-12-31 | 46 / 46 | 2 | Yes |
| 2020-01-01–2020-12-31 | 32 / 32 | 2 | Yes |
| 2021-01-01–2021-12-31 | 147 / 147 | 6 | Yes |
| 2022-01-01–2022-12-31 | 117 / 117 | 5 | Yes |
| 2023-01-01–2023-12-31 | 129 / 129 | 6 | Yes |
| 2024-01-01–2024-12-31 | 192 / 192 | 8 | Yes |
| 2025-01-01–2025-12-31 | 277 / 277 | 12 | Yes |
| 2026-01-01–2026-01-31 | 23 / 23 | 1 | Yes |
| 2026-02-01–2026-02-28 | 9 / 9 | 1 | Yes |
| 2026-03-01–2026-03-31 | 11 / 11 | 1 | Yes |
| 2026-04-01–2026-04-30 | 20 / 20 | 1 | Yes |
| 2026-05-01–2026-05-31 | 6 / 6 | 1 | Yes |
| 2026-06-01–2026-06-30 | 16 / 16 | 1 | Yes |
| 2026-07-01–2026-07-31 | 20 / 20 | 1 | Yes |
| 2026-08-01–2026-08-31 | 28 / 28 | 2 | Yes |
| 2026-09-01–2026-09-19 | 18 / 18 | 1 | Yes |

## Period, board and lifecycle denominators

`eligibleDistinctBySourcePeriodBoardStage` in `audit.json` contains the complete four-way denominator and matching breakdown. `bySourcePeriodBoardStage` includes repeated/out-of-scope raw observations. These compact roll-ups do not replace it.

| Year | NSE candidates | BSE candidates | SEBI filings |
|---|---:|---:|---:|
| 2002 | — | 2 | — |
| 2003 | — | 4 | 5 |
| 2004 | — | 19 | 104 |
| 2005 | — | 50 | 220 |
| 2006 | — | 73 | 330 |
| 2007 | — | 96 | 347 |
| 2008 | — | 36 | 136 |
| 2009 | — | 21 | 106 |
| 2010 | — | 74 | 270 |
| 2011 | — | 42 | 177 |
| 2012 | — | 26 | 83 |
| 2013 | — | 39 | 97 |
| 2014 | — | 46 | 83 |
| 2015 | — | 58 | 150 |
| 2016 | — | 70 | 184 |
| 2017 | — | 92 | 324 |
| 2018 | — | 88 | 307 |
| 2019 | — | 55 | 130 |
| 2020 | — | 38 | 82 |
| 2021 | — | 99 | 342 |
| 2022 | — | 96 | 326 |
| 2023 | — | 121 | 371 |
| 2024 | — | 161 | 641 |
| 2025 | 33 | 259 | 657 |
| 2026 | 141 | 183 | 386 |

| Source / board | Lifecycle denominator |
|---|---|
| BSE / Mainboard | completed_issue_listing_unverified: 1037; open: 2; upcoming: 1 |
| BSE / SME | completed_issue_listing_unverified: 794; upcoming: 5 |
| BSE / unknown | completed_issue_listing_unverified: 9 |
| NSE / Mainboard | closed: 3; completed_issue_listing_unverified: 3; listed: 69; open: 2; upcoming: 1 |
| NSE / SME | completed_issue_listing_unverified: 3; listed: 74; open: 3; upcoming: 1 |
| NSE / unknown | listed: 15 |
| SEBI / unknown | draft: 2214; final_prospectus: 1771; other: 575; rhp: 1298 |

## Reviewed additions and unresolved identities

`missing-before-admissions.json` was saved before changing canonical data. All 25 July/August BSE details independently agree with the archive’s issuer, SME board, Equity security type, symbol and issue dates. `admission-review.json` records each decision and both archive/detail retrieval clocks. Only identity and closed-issue lifecycle are admitted; listing, prices, lot quantities, amounts, financials and subscriptions remain null. The detail source uses its actual retrieval time; unknown observation time remains null. All 1,379 earlier records, all 441 byte-identical proposals and all 1,557 validation/expanded queue reviews survive. Public generation wrote 25 new profiles and left 1,379 existing profiles unchanged.

The official June 23 **Dhanwel Hybird Seeds** detail also says DHANWEL, but its dates differ from the accepted August 19–21 **Dhanwel Hybrid Seeds** offer. It is retained as a possible duplicate/lifecycle review with its own bytes and dates (`collision-review.json`); no cancellation status, alias, second issuer or offer merge is inferred. Other identity reviews and all five original aliases remain.

## Reproduction, tests and continuation

The continuation references the original content-addressed responses and binds the original capture manifest hash. It never relabels old collection times. Completed cohorts are reused without network calls. Source failures and raw responses survive retries. No competing canonical writer was added.

```powershell
uv run --frozen python tools/audit_ipo_universe.py reconcile --snapshot docs/audits/official-universe/2026-09-19 --aliases docs/audits/official-universe/2026-09-19/aliases.json --report-dir .cache/universe-replay-20260919
uv run --frozen python tools/audit_ipo_universe.py continue-snapshot --base-snapshot docs/audits/official-universe/2026-09-19 --snapshot <new-directory> --as-of <YYYY-MM-DD>
```

For before-admission reproduction, materialize `data/ipos.json` from `be97b796` and pass `--tracker`. `prepare-admissions` requires the exact retained baseline hash and writes a separate proposal. To resume failed collection use the matching snapshot date, explicit source/register/period, a bounded `--max-new-cohorts` and `--retry-failed`; successful windows are reused.

Validation: 30 existing normalization/alias/duplicate/stage/board tests plus seven continuation/real-cohort tests pass; 38 Node public-quality/source-health tests pass. Local full Python ran 1,337 tests before two additional focused tests were added, with only the two known Windows filename/symlink limitations; All **1,339 tests passed in Linux CI 35420466941**, including those filesystem cases and the two additional focused tests. Strict validation has zero errors and 1,557 reviews. The dated `browser-check.cjs` passed all 25 profiles/searches and 75 viewport checks (1440/375/320px), with no page errors, horizontal overflow or master-data browser fetch. It replays this release’s null-field contract. PR [#162](https://github.com/Vasuki8/IPO-Tracker/pull/162) merged `cf21055c` as `46e4bbaf`. Pages **35420562278**, main validation **35420562959** and deployed verification **35420613423** passed. All 25 admitted profiles pass exact-byte HTTPS delivery checks and the identity/null/clock contract; live Browser checks confirm Complete Sports and the accepted Dhanwel August offer. See `release.json`, `live-delivery.json` and `live-browser.json`.

P4 remains blocked: **408 actionable + 67 higher-priority records**, **1,553 blocking / 1,557 total reviews**, zero errors/unmapped reviews; P5 remains waiting. The increase exposes the newly admitted incomplete records; this is not a P4 blocker reduction. Source commercial/redistribution rights and product/pricing decisions remain unresolved.

**Exact next cohort:** source-review the **18 BSE June 2026 unmatched candidates** in `next-cohort.json`, keeping the separate Dhanwel June/August lifecycle conflict under review. Recover NSE history only when the official endpoint responds, beginning with the four retained failed quarters. Reuse all reconciled SEBI year/month cohorts; do not recrawl the completed registers.
