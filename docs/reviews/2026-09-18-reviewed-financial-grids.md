# Reviewed annual financial grid repair — 18 September 2026

Baseline: `07527e52d2a3b590be2851fcb0d578ed3f580136`. This continues the exact
next task in PROJECT_STATUS after the completed intermediary/NSE releases.
The family is annotated annual consolidated tables with separate interim columns,
plus explicit issuer revenue and net-worth rows. It is an offline reviewed helper,
not a new global extraction fallback. Generic parser versions remain unchanged.

## Source review and normalization

| Issuer | Final Prospectus URL | SHA-256 | Cover date | Physical pages read |
|---|---|---|---|---|
| Hy-Tech / HTEL | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787913136327.pdf | `80e725bfa930875a995043c3dd1ede119446a03653e7baaccf9fe84f53670839` | 2026-08-27 | 416/416 |
| Onemi / KISSHT | https://www.sebi.gov.in/sebi_data/attachdocs/jun-2026/1781763357383.pdf | `2bde179647fe3c68c86079da1269657c0002e2c4515119b3527f5223bb5dbb19` | 2026-05-05 | 464/464 |

The cover dates differ from the retained filing dates (2026-08-28 and 2026-05-06).
Collection clocks are retained in the earlier seed receipt and new machine receipt;
review/extraction clocks are separate. HTTP modification dates are not document dates.

Production `extract_pdf_text` used Poppler 26.07.0 with
`-layout -fixed 3 -enc UTF-8 -f 1 -l <complete page count> - -`.
Both complete extracts reproduce the current parser's `(None, {}, [])` result.
The previous pypdf inspection was diagnostic only. The new grid fixtures retain
the exact native physical lines, header bounds, numeric spans, units, dates and
scope context, replayed by `reviewed-financial-grid-v1`.

Poppler matches the bundled 26.07.0 Windows package; only its missing pdftotext
binary was obtained into ignored local cache. Package SHA-256:
`3fdbb4caf50ecae4fa447cb7a7d6d5b521a39ae8d4de4f6565e0ce9cd6d7f903`;
binary SHA-256: `1d1007cd28967c616282a6b29c2daac7902d68ba4563f8c57fcc8e153bb0466f`.
No application dependency or production runtime change is included.

Amounts below are ₹ crore after exact million × 0.1 normalization; EPS is ₹ per
share and RoNW is percent. No amount is inferred from a ratio or rounded share count.

| Issuer / year | Revenue from operations | EBITDA | PAT | Net worth | RoNW | Basic EPS |
|---|---:|---:|---:|---:|---:|---:|
| HTEL FY2026 | 189.404 | 41.686 | 22.592 | 122.017 | 20.24 | 2.70 |
| HTEL FY2025 | 161.382 | 35.788 | 19.619 | 101.251 | 21.39 | 2.35 |
| HTEL FY2024 | 137.708 | 22.551 | 11.596 | 82.216 | 15.11 | 1.39 |
| KISSHT FY2025 | 1337.465 | 403.368 | 160.621 | 1005.994 | 15.97 | 33.09 |
| KISSHT FY2024 | 1674.446 | 358.958 | 197.290 | 804.569 | 24.52 | 41.27 |
| KISSHT FY2023 | 984.457 | 97.711 | 27.667 | 566.234 | 4.89 | 6.26 |

HTEL source pages: revenue 68/printed62; ratios 282/276; explicit Net Worth 329/323.
Consolidated scope is explicit on pages 66, 68 and 329. PAT/EPS corroborate the
underlying statement on page 68 and duplicate statement on 232. Its EBITDA
subtracts other income; RoNW uses average total equity. Total income, equity
share counts and EBITDA-to-total-income are different rows and were not aliased.

KISSHT source pages: revenue 70/64; ratios 335/329; explicit Net Worth 382/376,
also repeated on 132 and 366. Page 67 establishes consolidated summary scope;
page 335 states consolidated scope above its table. The standalone website prose
after the table does not change that scope. Nine-month December 2025 figures are
retained in the raw source but excluded from annual values. RoNW uses closing net
worth; ROE elsewhere uses average net worth. EBITDA adds tax, finance costs and
depreciation without HTEL's other-income subtraction. These definitions differ.

KISSHT page 334 explicitly reconciles FY2024 reported revenue 16,744.63 million
less 0.17 million to restated revenue 16,744.46 million, with the offset in other
income. This resolves the historical amount difference; it is not a newest-value
selection. EPS is retrospectively adjusted for the July 8, 2025 ten-to-one split.
The awkward split wording on page 312 is retained as a caveat; pages 70, 129 and
335 and the numeric denominators agree. Interim RoNW appears annualized although
the formula note omits that qualification; no interim correction is accepted.
Subsidiary Si Creva's separate statements are not issuer consolidated figures.

The six primary table pages were visually checked against the PDF, with scope,
cover and corroborating text reviewed separately. Independent read-only review
confirmed the 36 annual cells. This is a bounded source review, not a claim to
have audited every disclosure in either prospectus.

## Publication boundary and expected blocker effect

The whole financial field retains all six existing metrics for all three existing
annual years. Before-values, original document provenance, source-review holds,
correction history, other fields and all pending proposals must survive. Reviewed
proofs require exact issuer/offer identity, PDF hash, dates, per-cell replay and
the explicit-reviewed transaction. Existing unresolved conflicts still block
publication. The same-document generic extractor cannot replace an accepted proof.

Before: 1,598 total source reviews / 1,594 P4 blocking; P4 388 actionable / 55
higher-priority records. The two issuers each have 18 unvalidated metric reviews
and three net-worth percentage-contamination reviews. Offline preparation must
remove exactly 42 source reviews by validating/correcting all 36 cells, with no
queue deletion, exclusion or proposal disposal. Actual release counts and live
delivery evidence belong in PROJECT_STATUS and the release receipt after deployment.

## Additional family candidate inspected: PNGS Reva remains blocked

Official PDF https://www.sebi.gov.in/sebi_data/attachdocs/mar-2026/1772433551022.pdf
matches `99cedc3c1c9db3bb8b2eba984864705998aaceb562db5d0e38408d6f2019517b`;
477/477 pages were extracted with the same native engine. Physical page 331/327
has OTHER FINANCIAL INFORMATION but reports **Adjusted EBITDA**, not EBITDA.
It includes partnership-era FY2024/FY2023 and explicitly reports basic/diluted EPS
as NA because the company was formed by conversion on December 20, 2024. Its
six-month interim column and bonus-adjusted FY2025 EPS also need distinct treatment.
Consolidated scope is not established by this table. This is **parser unsupported**,
not unavailable source or absent disclosure for the entire field. All 18 PNGS
reviews remain open. Do not relabel adjusted EBITDA or manufacture historical EPS.

Next family: establish a reviewed representation for adjusted EBITDA and explicitly
unavailable partnership-era per-share values, then source-review PNGS's annual PAT,
net worth and definitions before any bounded publication. The current consolidated
grid batch is exhausted; unknown members of the nine-issuer contamination cluster
require their own source/layout classification.
