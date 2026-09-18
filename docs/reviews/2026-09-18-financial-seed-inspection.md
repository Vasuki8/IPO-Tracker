# Two-source financial layout inspection — diagnosis only

**Production text parity is not established.** This inspection used pypdf
6.18.1 `extraction_mode="layout"`; production uses `pdftotext`, which was not
available locally. The next task must reproduce the findings with production
extraction before implementing a repair. No financial value was accepted, no
review was resolved, and no canonical data, production parser or scheduling was
changed. This is not a completed source review for publication.

## Retained sources and inspection coverage

Exact complete PDFs remain in ignored `.cache/financial-next-batch/`. The
[machine-readable receipt](2026-09-18-financial-seed-inspection.json) retains
request/collection/review clocks, response URL/status, byte count, SHA-256,
complete page-tree verification, parser version/file digest, exact extracted
table lines, row/cell offsets and diagnostic results. PDF hashes match the
previously retained document identities. Both successful responses were HTTP
200 without a redirect. An earlier Onemi download was incomplete and was not
retained or used.

| Issuer | Official final source | Bytes / pages | Cover date | Retained `documentFiledDate` |
| --- | --- | ---: | --- | --- |
| `htel`, Hy-Tech Engineers Limited | [SEBI PDF](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787913136327.pdf) | 7,009,022 / 416 | 2026-08-27 | 2026-08-28 |
| `kissht`, Onemi Technology Solutions Limited | [SEBI PDF](https://www.sebi.gov.in/sebi_data/attachdocs/jun-2026/1781763357383.pdf) | 13,579,858 / 464 | 2026-05-05 | 2026-05-06 |

The cover dates were read from rendered source covers. They are separate from
the existing filing-date fields, whose semantics/authority were not adjudicated
here. HTTP Last-Modified is also separate: August 28 for Hy-Tech and June 18 for
Onemi. Do not substitute any of these dates for one another.

Hy-Tech was collected at `2026-09-18T20:08:10.932515+00:00`, SHA-256
`80e725bfa930875a995043c3dd1ede119446a03653e7baaccf9fe84f53670839`.
Onemi was collected at `2026-09-18T20:10:57.584968+00:00`, SHA-256
`2bde179647fe3c68c86079da1269657c0002e2c4515119b3527f5223bb5dbb19`.

Every page-tree entry was checked for both complete files. Rendered physical
pages inspected: Hy-Tech 1, 68, 282 and 329; Onemi 1, 69, 70 and 335. Targeted
extraction also covered the summary introductions and adjacent balance-sheet
pages. Hy-Tech's complete 416-page pypdf extraction was replayed through the
current strict parser. It emitted rotated-text warnings. Onemi's full-document
text extraction was interrupted after targeted pages were separately obtained;
there is no full-document Onemi parser replay or claim that every competing
financial row has been reviewed. Poppler rendered the selected pages; Hy-Tech
emitted font-substitution warnings, so retained text was crosschecked against
the visible table cells rather than treating extraction alone as evidence.

## Shared bounded source family

Both sources contain an **OTHER FINANCIAL INFORMATION** table: Hy-Tech physical
page 282 / printed 276 and Onemi physical page 335 / printed 329. The receipt
contains fixture-ready raw lines and offsets for these pages, including their
footnotes. The current strict parser (`PARSER_VERSION=22`, file digest in receipt)
produces `financials=null`, empty evidence and no conflicts for each extracted
page; Hy-Tech's complete pypdf document has the same empty outcome.

Three concrete gaps explain the page-level result:

1. `_HEADING` does not recognize `OTHER FINANCIAL INFORMATION`. The date line is
   separate from `Particulars`, so it does not activate a table independently.
2. `_period_columns` already finds the correct columns on these extracted
   pages: Hy-Tech annual 2026/2025/2024 at indexes 0/1/2; Onemi interim December
   31, 2025 followed by annual March 31, 2025/2024/2023 at indexes 1/2/3. Preserve
   that exclusion of the interim column. Increasing page limits is not a fix.
3. Hy-Tech's formula letters, arithmetic expressions and roman footnotes remain
   in the recognized row tails, causing `_numbers` to reject all nine metric
   candidates. Onemi's EPS label/unit wraps onto a second line; its numeric
   tails for EPS, diluted EPS, PAT and RoNW happen to pass `_numbers`, but its
   EBITDA tail fails on the currency/footnote suffix. A repair must bind exact
   columns and allowed label annotations, not strip arbitrary letters/numbers.

One of Hy-Tech's nine current metric candidates is `EBITDA to Total Income`:
it matches the current EBITDA prefix, but is a ratio. Keep it as a negative
fixture; a less strict tail parser must not publish 0.22/0.21/0.16 as EBITDA.
Share-count rows likewise must never supply EPS, nor RoNW supply net worth.
The receipt records current recognizer candidates, not accepted semantic maps.

## Source crosschecks and unresolved metric boundaries

The following are observations in source units for diagnosing the layout, not
approved canonical replacements. Hy-Tech's annual columns are March 31,
2026/2025/2024. Its table shows PAT 225.92/196.19/115.96 **million rupees**, basic
and diluted EPS 2.70/2.35/1.39 **rupees**, RoNW 20.24/21.39/15.11 **percent**, and
EBITDA 416.86/357.88/225.51 **million rupees**. The restated consolidated profit
and loss statement on physical page 68 corroborates PAT and EPS. Its summary
introduction on page 66 establishes consolidated scope; page 282 does not
repeat that scope in its heading. A future proof must bind that source context
explicitly rather than infer scope from the issuer.

Hy-Tech's notes define RoNW using **average total equity** and EBITDA by adding
tax, finance costs and depreciation/amortization to profit and subtracting other
income. Its weighted-average share counts are 83,531,840, a separate denominator
from EPS. Page 282 contains **total income**, 1,934.35/1,667.07/1,411.73 million,
whereas page 68 labels revenue from operations 1,894.04/1,613.82/1,377.08 million.
They must not be interchanged. Page 282 labels total equity, not net worth;
physical page 329 separately labels net worth 1,220.17/1,012.51/822.16 million
and supplies its definition and consolidated context. That corroboration does
not authorize a global total-equity-to-net-worth alias.

Onemi page 335 explicitly derives its ratios from restated **consolidated**
information. Its first column is the nine months ended December 31, 2025. In
annual March 31, 2025/2024/2023 order, the table shows PAT
1,606.21/1,972.90/276.67 million rupees, basic EPS 33.09/41.27/6.26 rupees,
diluted EPS 12.79/15.54/2.50 rupees, RoNW 15.97/24.52/4.89 percent, and EBITDA
4,033.68/3,589.58/977.11 million rupees. The separately retained interim cells
must stay outside annual output. Physical page 70 corroborates PAT/basic and
diluted EPS; its split-line date headers are an additional layout requiring
separate handling if that page is parsed.

Onemi's footnote says the July 8, 2025 share split from face value ₹10 to ₹1 was
applied retrospectively; basic and diluted EPS use different post-split
denominators under Ind AS 33. Preserve that basis. Its RoNW uses end-period net
worth, unlike Hy-Tech's average basis. Its EBITDA definition adds tax, finance
and depreciation/amortization without Hy-Tech's subtraction of other income.
The subsequent standalone-financial-statements link is separate prose, not a
change of scope for the preceding consolidated ratio table. Stop extraction
at the table/footnote boundary and preserve the definitions.

Neither OTHER table supplies revenue from operations or an explicit net-worth
row. This bounded table repair alone cannot resolve those metrics. It must not
clear all 42 seed reviews or the whole financial-provenance gate by implication.
The inspection removes **zero** P4 blockers. Existing nulls, competing rows and
unresolved review items remain unchanged.

## Exact next task

Re-extract these same verified complete PDFs using production `pdftotext` and
reproduce the isolated-page failures. Implement one bounded OTHER FINANCIAL
INFORMATION recognizer with explicit annual/interim column positions, source
scope, row units, permitted formula/footnote suffixes and wrapped EPS labels.
Use both exact source identities as positive fixtures. Require negative cases
for the EBITDA ratio, share counts, RoNW-as-net-worth, prose dates, lost/moved
units, shifted columns, conflicting rows and basic/diluted EPS conflation.
Retain source and extraction-engine identity for every proof.

Keep the first repair and rehearsal bounded to these two documents. A production
parser-version bump can schedule much broader re-extraction; review that routing
explicitly instead of treating a parser merge as acceptance of an entire backlog.

Before publication, inspect the remaining relevant same-issuer financial tables
for contradictions, review each proposed cell and its basis, and retain all
unresolved metrics. Use the existing bounded reviewed publication process only
after that review and measure actual blocker changes. Its current accepted group
kinds are composition and intermediaries; financial groups will require narrowly
scoped value/proof validation and preservation tests before they can use that
transport. Do not force them through another group's schema or ordinary registry
application. Do not extend this batch
to PNGS or the other seven signature matches until the two-source repair is
demonstrated. This task does not include #105, P5 or performance expansion.
