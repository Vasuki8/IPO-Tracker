# Core source-attempt clocks — 19 September 2026

Assessment base: `ac51bebeb75a1afd41150a061288d4078e0e89c9`.
The [before report](before.json), assessed at `2026-09-19T01:20:00Z`, binds the
accepted inputs and report policy. Reproduce with `tools/report_update_health.py
--check-report` at this input checkpoint. No sources were collected to create it.

NSE live, NSE history, SEBI and BSE all lack check clocks. Across the 33 retained
source entries, five recorded failures remain; eight need investigation. There
are zero *known* overdue source checks, one overdue stage, two subscription
observations older than tolerance, and 441 unresolved proposals. Unknown checks
are not counted as current. P4 is incomplete: 387 actionable, 63 higher-priority,
1,552 blocking reviews / 1,556 total, zero semantic errors or unmapped reviews.

The repair records future real request/parser attempts with exact source URLs,
page/date-range scope, count, outcome, check time and retained failure reason.
Skipped ranges/sources receive no new check clock. Source observation remains
unknown unless independently disclosed; collection does not backfill that clock.
NSE current/upcoming and SEBI/BSE pages keep successful siblings and failed
receipts. All-empty/all-failed runs preserve accepted records while saving health.
Attachment failures discard incomplete mutations. Whole source/stage entries
remain atomic through concurrent publication, preserving the accepted entry on
conflict rather than mixing its clock with another outcome.

Focused tests cover these paths, malformed NSE payloads, unchanged accepted
records/reviews/corrections, publication, date boundaries and shared Python/JS
semantics. Strict validation has zero errors. All 36 Node tests passed. The full
local UTF-8 suite passed 1,305 of 1,307 tests before the final two merge regressions;
the other two require Linux filename/symlink capabilities. Linux CI must pass the
complete final suite before merging. The first local run without UTF-8 was
invalid for this repository's Unicode data and was repeated correctly.

Release acceptance remains pending: merge, existing core workflow (including
conditional bounded filing maintenance), canonical/proposal diff inspection,
public generation, deployment, live browser/JSON verification and after report.
No P4 numerical reduction or source correctness is claimed from this code change.
