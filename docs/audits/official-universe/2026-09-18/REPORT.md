# Official IPO-universe name audit — 18 September 2026

**Coverage is incomplete.** This is an issuer/name and lifecycle inventory audit, not a financial backfill or proof that every observed filing became an IPO. Recovery used main `6992dd44c55dfa529cea29cb32a9462d9ca38a78`; no earlier three-source universe audit was found. The scheduled writer subsequently published `f19a561388cbccd3af93679c9e743838746cad4b`; all its existing records were preserved while the same eight reviewed admissions were reapplied. Previous financial and NSE subscription repairs were preserved.

## Scope and inclusion rules

| Dimension | Rule |
| --- | --- |
| Mainboard / SME | Keep the explicit exchange platform or EQ/SME security type. SEBI register membership supplies no board: null stays null. BE and absent platform values are not guessed. |
| Draft / UDRHP | Retain primary draft filings and addenda as filing observations; never label them upcoming solely because they are filed. |
| RHP | Preserve the RHP stage independently of draft/final filings; issue dates require separate exchange/document evidence. |
| Final Prospectus | Record membership in the final-offer register and the published title. This audit does not verify every document as final numerical authority. |
| Open / current / upcoming | Preserve source status and explicit exchange dates. An upcoming-feed row marked Closed remains closed. No dates inferred from a filing title. |
| Completed / listed | BSE historical means a closed issue observation, not proven listing. NSE listing dates are retained when explicitly supplied. |
| Withdrawn / cancelled | Preserve explicit notices/statuses; special withdrawal options are auxiliary events, not proof the whole issue was cancelled. No dedicated exhaustive cancellation register was verified. |
| Non-IPO instruments | Keep rights, debt, call-money, buyback and trust observations outside the equity-candidate denominator. BSE `FPO` here explicitly means Public Issue-Fixed Price, not automatically a follow-on offer. |
| Follow-on / auxiliary uncertainty | Public-issue registers can include follow-on offers, duplicate issues and auxiliary events. Candidate rows need admission review before becoming new canonical IPOs. |

Normalization is deterministic: Unicode normalization, case, spacing/punctuation, ampersand/and and terminal Ltd/Limited. Meaningful company words are retained. Bounded filing suffixes are separated from the exact published title. Multiple tracker matches, board disagreements, symbol disagreements and differing offer dates stay in review. Similarity produces suggestions only. Five aliases have replayable BSE issuer/symbol/date proofs; no fuzzy merge is accepted.

## Exact denominator and matching results

These rates use **distinct observed equity-public-issue candidate records**, not all Indian IPOs or unique companies. SEBI records are filings; exchange records are issue observations. The raw row counts, distinct keys, years, boards and lifecycle stages are all retained in `audit.json`. Every raw source row remains in `records.jsonl`, including duplicate observations and out-of-scope instruments.

| Source | Distinct candidate records | Safely matched before → after admissions | Final match rate | Missing-name records | Identity reviews / unverified |
| --- | ---: | ---: | ---: | ---: | ---: |
| BSE | 1,848 | 556 → 563 | 30.47% | 1,276 | 9 / 0 |
| NSE | 174 | 172 → 173 | 99.43% | 1 | 0 / 0 |
| SEBI | 5,813 | 2,601 → 2,602 | 44.76% | 3,061 | 47 / 103 |

The final report has **2,160 unmatched normalized candidate names** across sources and **227 tracker records not safely matched** in these captured cohorts. `genuinely_missing` means the published name has no deterministic tracker/approved-alias match; it does not prove a new legal entity, an initial offering, or absence under an unreviewed historical rename. The complete missing-name report was saved before admissions. No bulk import was performed.

| Source | Captured period and traversal | Remaining coverage limits |
| --- | --- | --- |
| NSE | Current/upcoming snapshots; 2025 Q1 and 2026-01-01–2026-09-18 historical responses. Observed dates extend through upcoming 2026-09-23. | Annual queries for every year 2000–2025 timed out; 2025 Q1 is only a subset. Q2/Q3 2026 attempts timed out, although the annual 2026 response succeeded. Before 2000 is not audited. API supplies no independent total. |
| BSE | Entire returned book-building result: 1,282 rows, 2002-01-28–2026-09-16. Fixed-price result: 558 rows, 2010-09-22–2026-09-15. Current filtered book-building: eight rows. | No global historical total/history-start guarantee. Main host returns an application shell; beta official form recovered the archive. Current fixed-price response has no usable rows and is not counted as verified zero. |
| SEBI | All 236 available page positions across four public-issue registers, with observations from 2003-12-01–2026-09-18. | Draft pagination changes between 2,208 and 2,210 rows and repeats 43 primary URLs; its traversal is not complete. Date-filter repair probe returned HTTP 530 and was retained. No pre-2003 or separate SME/cancellation completeness claim. |

| SEBI register | Captured raw rows | Pages | Displayed total(s) | Traversal reconciled |
| --- | ---: | ---: | --- | --- |
| draft | 2,208 | 89 | 2208, 2210 | No |
| rhp | 1,270 | 51 | 1270 | Yes |
| final_prospectus | 1,560 | 63 | 1560 | Yes |
| other | 818 | 33 | 818 | Yes |

NSE’s remaining unmatched candidate is Adani Enterprises (`ADANIENPP1`). It is not admitted: the API says EQ, while a related [official filing](https://nsearchives.nseindia.com/corporate/ADANIENT_04022026203545_Intimationconversionpptopp1stcall.pdf) concerns partly paid rights/call-money securities; that filing alone does not identify the exact API event, which still needs classification. This ambiguity remains in the report rather than being removed to improve coverage. The captured `N0`/`DEBT` debt and `IV`/`RR` trust rows remain in raw observations outside the candidate IPO denominator.

## Period, board and lifecycle denominators

`eligibleDistinctBySourcePeriodBoardStage` supplies the full four-way breakdown; `bySourcePeriodBoardStage` additionally retains duplicate/out-of-scope raw rows. Below is the period roll-up. A dash means no captured denominator, not zero official issues.

| Record year | NSE candidate rows | BSE candidate rows | SEBI filing rows |
| --- | ---: | ---: | ---: |
| 2002 | — | 2 | — |
| 2003 | — | 4 | 5 |
| 2004 | — | 19 | 104 |
| 2005 | — | 50 | 216 |
| 2006 | — | 73 | 326 |
| 2007 | — | 96 | 345 |
| 2008 | — | 36 | 134 |
| 2009 | — | 21 | 104 |
| 2010 | — | 74 | 266 |
| 2011 | — | 42 | 175 |
| 2012 | — | 26 | 83 |
| 2013 | — | 39 | 97 |
| 2014 | — | 46 | 83 |
| 2015 | — | 58 | 148 |
| 2016 | — | 70 | 184 |
| 2017 | — | 92 | 322 |
| 2018 | — | 88 | 305 |
| 2019 | — | 55 | 128 |
| 2020 | — | 38 | 82 |
| 2021 | — | 99 | 340 |
| 2022 | — | 96 | 322 |
| 2023 | — | 121 | 371 |
| 2024 | — | 161 | 639 |
| 2025 | 33 | 259 | 651 |
| 2026 | 141 | 183 | 383 |

## Accepted identity admissions and aliases

Seven recent BSE SME issues were independently checked against the detail-page issuer header, Equity security type, symbol and exact issue period. Vinod was checked against NSE’s explicit SME symbol and 17 September listing date. The seven BSE records remain **closed, listing date null**. No listing was inferred from “Listing @ BSE”. All price, issue-size, lot, intermediary, subscription and financial fields remain null.

| New record | Source | Open → close | Accepted lifecycle |
| --- | --- | --- | --- |
| AMTECH ESTERS LIMITED (`amtech-esters`) | BSE | 2026-09-09 → 2026-09-11 | closed; listing unknown |
| QUANTO AGROWORLD LIMITED (`quanto-agroworld`) | BSE | 2026-09-15 → 2026-09-17 | closed; listing unknown |
| PANCHATV BHARAT LIMITED (`panchatv-bharat`) | BSE | 2026-09-10 → 2026-09-15 | closed; listing unknown |
| INFRAX RENEWABLE LIMITED (`infrax-renewable`) | BSE | 2026-09-09 → 2026-09-11 | closed; listing unknown |
| APANA LOGISTICS LIMITED (`apana-logistics`) | BSE | 2026-09-07 → 2026-09-09 | closed; listing unknown |
| FARM PEACE LIMITED (`farm-peace`) | BSE | 2026-09-01 → 2026-09-03 | closed; listing unknown |
| FLY HI MARITIME TRAVELS LIMITED (`fly-hi-maritime-travels`) | BSE | 2026-09-01 → 2026-09-03 | closed; listing unknown |
| Vinod Texworld Limited (`vinod`) | NSE | 2026-09-09 → 2026-09-11 | listed 2026-09-17 |

Accepted aliases: Rays of Belief → `momsbelief`; Happy Forgings → `happyforge`; DCX Systems → `dcx`; Prince Pipe & Fittings → `princepipe`; Astron Paper and Board Mill → `astron`. They change audit matching only. Hariom remains in review because BSE’s HARIOM symbol differs from the retained HARIOMPIPE symbol; no automatic exchange-symbol equivalence was assumed. Other spelling, offer-date and identity conflicts remain in `identity-review.jsonl`.

All 1,371 previous records, all 441 proposals, correction registry entries, existing field proofs and holds survive unchanged. All 1,556 source reviews are identical. Only canonical build time/record count changed alongside eight additions. Inventory is now 1,379. P4 remains incomplete: **387 actionable + 63 higher priority**, 1,552 blocking reviews, zero semantic errors; P5 remains waiting. The eight additional incomplete records are visible work, not a P4 reduction.

PR #146 deployed the first audited release as `b23fc366`. Live browser review found that the new source links displayed retrieval time as “Source record timestamp”. Admission review v2 corrects that boundary: source `asOf` remains null and retrieval time remains in `collectedAt`, separately from unknown `observedAt`. `clock-correction.json` retains every previous displayed clock and the correction reason. No source was fetched anew or made fresher by this correction.

## Reproduction and continuation

Use Python 3.12 and the committed uv lock. Collection is explicit and resumable; it never changes canonical data. Verified cohorts are reused; failed cohorts are retried only with `--retry-failed`. A different as-of date requires a new snapshot directory. Raw responses are content-addressed gzip files; receipts retain URL, POST fields, response hash, HTTP result and collection clock. Unknown reporting/observation clocks remain null. Original failed attempts remain available.

```powershell
uv run --frozen python tools/audit_ipo_universe.py reconcile --snapshot docs/audits/official-universe/2026-09-18 --aliases docs/audits/official-universe/2026-09-18/aliases.json --report-dir .cache/universe-replay
uv run --frozen python tools/audit_ipo_universe.py collect --snapshot docs/audits/official-universe/2026-09-18 --as-of 2026-09-18 --sources NSE --start-year 2000 --max-new-cohorts 4 --retry-failed
```

To replay the initial pre-admission report/proposal, retrieve `data/ipos.json` from commit `6992dd44` into a temporary file and pass `--tracker`. `prepare-admissions` also requires `--admissions .../admissions.json` and a separate `--output`; it rejects writing directly to canonical data. The publication replay uses `f19a5613` and `admissions-publication.json`, with its corresponding `audit-before-publication.json`; the original recovery plan/report remain retained. Baseline hashes, exact source identities and existing names/symbols are checked. Five aliases replay their retained BSE identity rows.

Validation: 30 focused tests cover normalization, aliases, collisions, stage separation, board differences, repeated pages, source hashing and eight real BSE layouts plus NSE listing evidence. Nine Node public-quality tests pass. Strict validation reports zero errors. The full Windows suite exposed the record-count metadata mismatch, which was corrected; all 20 affected operational regressions then passed. The two existing Windows path/symlink limitations remain platform-specific; all 1,283 tests passed in Linux CI for PR #146. Direct browser checks passed for directory search, all eight source-linked profiles and the longest new name at 375 pixels; unknown terms stay unavailable. The clock correction also asserts distinct source/collection timestamps and requires its own release verification. Final PR, CI and deployment evidence are recorded in PROJECT_STATUS and the closeout receipt.

**Exact next cohort:** reconcile BSE’s August 2026 unmatched SME name cohort using the retained archive and issuer/symbol/date detail proofs. First resolve candidates already linked to a differently named tracker entry. Separately recover stable SEBI draft pagination and retry the smallest failed NSE historical cohort from an environment where the official endpoint responds. Reuse the verified RHP, final-offer, Other Documents and BSE historical responses; do not recrawl them. No P5/numerical or performance expansion is authorized by this audit. Source redistribution/commercial rights remain unresolved.
