# Vinod Texworld — bounded publication source review

Reviewed 19 September 2026 against publication `5ea15921c2a2e742b282acefad6df366dab0c58f`.
The core workflow's existing filing-maintenance stage populated financials,
objects and shareholding. These changes required source review in addition to
the operational release tests.

[SEBI filing](https://www.sebi.gov.in/filings/public-issues/sep-2026/vinod-texworld-limited-prospectus_104299.html)
classifies the 3 September 2026 Prospectus as a Final Offer Document filed with ROC.
The [official PDF](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1788775122933.pdf)
was retrieved at `2026-09-19T01:52:29Z`: 12,035,919 bytes, 469 pages,
SHA-256 `992cbd49f1a810bd5023b38fee33915069885229d5a49715cb787de4dd335766`.
Its cover identifies Vinod Texworld Limited, CIN `U17200GJ2012PLC071210`.
Canonical offer identity is symbol `VINOD`, opening 9 September 2026.
Extraction version 31 ran at `2026-09-19T07:12:32+05:30`; this visual review is
version 1. Downloaded PDF and rendered pages remain in the local source cache.

| Field | Physical / printed page and source row | Review |
| --- | --- | --- |
| Revenue | 348 / 342, KPI table, revenue from operations; FY2026/2025/2024 | 34,263.62 / 33,536.93 / 27,148.80 lakh matches 342.6362 / 335.3693 / 271.488 crore. |
| EBITDA | Same table and years | 2,282.89 / 2,095.81 / 1,230.04 lakh matches 22.8289 / 20.9581 / 12.3004 crore. |
| PAT | Same table and years | 1,040.74 / 923.36 / 548.64 lakh matches 10.4074 / 9.2336 / 5.4864 crore. |
| Financial definitions | 349 / 343, notes 1, 2 and 4 | Restated revenue, EBITDA and PAT definitions accompany the KPI table. No new consolidation scope is inferred. |
| Objects | 135 / 129, numbered utilization table | Plant 638.77, loan 715.00, working capital 2,035.00, general corporate purposes 597.27, expenses 296.98 lakh; all five stored crore amounts match division by 100. These are proposed allocations; issue expenses are estimates disclosed by the prospectus, not actual expenditure. |
| Combined promoter and promoter group | 119 / 113, category A in shareholding pattern | Direct disclosure is **93.10%**. |
| Separate groups | 121 / 115, pre-issue percentage column, Total(A) and Total(B) | Promoters **76.72%**, promoter group **16.39%**. Adding rounded subtotals gives stored **93.11%**, not the directly disclosed combined percentage. |
| Stored shareholding locator | 120 / 114 | Continuation and notes; the claimed percentage is absent. Three promoters are named in the document; an empty parsed list does not establish absence. |

Financial and objects amounts pass this bounded source comparison. Shareholding
does not: its field scope, derived percentage and page locator need repair.
`legacy_offer_parser._subtotal_pair_pct` adds rounded subtotals;
`final_prospectus_parser.extract_final_promoter_shareholding` describes that result
as explicit and attaches the marker page instead of the matched row page.

The existing value-scoped display hold binds the exact issuer, offer, PDF hash
and complete retained shareholding value. Public projections withhold the field
and create a manual source-review item. Canonical 93.11, empty names, source proof
and correction history remain available for audit. No 93.10 replacement is accepted,
no review is cleared and no P4 reduction is claimed. Collection-clock or parser
version changes cannot release this binding. A later changed value needs a new
source review; a nonmatching old hold is not itself proof of resolution.

Follow-up source-family work must distinguish promoters from promoter group,
prefer an explicit matched aggregate where that is the intended field, never add
rounded percentages to invent it, and cite the actual row page. Inspect multiple
real documents and measure affected canonical records before a shared parser repair.
