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
semantics. Strict validation has zero errors. All **36 Node tests** passed. The
final Linux suite passed **1,311 tests** in
[validation 35413034691](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35413034691).
The local UTF-8 suite retained the two known Windows filename/symlink limitations;
Linux passed them without weakening the tests.

[PR #154](https://github.com/Vasuki8/IPO-Tracker/pull/154) merged `089a9464` /
`7c9de7f8` as `9878e0f6`; 1,309 Linux tests and browser checks passed. Before its
data publisher ran, release inspection found that the legacy core cleanup would
discard seven already reviewed BSE-only issuer admissions. Run **35412526647** was
cancelled during collection; its publisher never ran. No accepted data was lost.

[PR #155](https://github.com/Vasuki8/IPO-Tracker/pull/155) merged `ac6a318f`,
`5927d9de`, `383d9a30` as **`432c9fa1853fb1cab23f5d7fbc834499edf6994b`**.
Identity source and observation retention is bound to the exact URL in the
accepted `universeAdmission.identitySource`. Unrelated comparison URLs still
follow legacy cleanup. The active core wrapper was tested with all seven actual
reviewed records, independent NSE success and BSE failure. Their retained official
HTML hashes, issuer names, equity security types, symbols and issue dates replayed
successfully; see [identity-source-replay.json](identity-source-replay.json).
Original collection dates are retained; this replay is not a new source retrieval.

The source-preview workflow now maps this narrow core route to existing
retained-data validation. Mixed parser changes retain full source preview.
Superseded preview **35412888497** was cancelled while correcting this scope;
[final preview 35413034734](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35413034734)
passed both jobs and explicitly skipped unrelated document and market-history
collection. [Browser 35413034726](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35413034726)
passed. Workflow permissions/protections are unchanged.

The comparison from assessment base through both engineering merges shows **zero
canonical record changes**, all 1,379 records and byte-identical 441 proposals.
Use [compare.py](compare.py) with `--base`, `--head` and an explicit report
`--output` to reproduce canonical/proposal/phase/receipt comparisons from Git.

Core data release **35413219212** succeeded, publishing
**`5ea15921c2a2e742b282acefad6df366dab0c58f`**. Pages **35413782301** and
deployed verification **35413803388** passed. [Published diff](published-diff.json)
retains every changed field path: all 1,379 IDs, all eight admission receipts and
all 441 byte-identical proposals survive. Check clocks are real source-attempt
times; NSE history's empty check remains success, and BSE's two failures remain
visible alongside eight beta-source rows. Source observation remains unknown.

[After report](after.json), bound to `5ea15921` inputs at `2026-09-19T01:53:00Z`,
records 5 failed / 1 partial / 27 successful sources, zero known overdue checks or
stages, 3 stages and 6 sources needing investigation, and 441 unresolved proposals.
Two subscription observations exceed age tolerance outside the monitoring window;
this is not a missed intraday SLA. Its publisher timing is the observed job window
(01:47:59–01:48:32Z), not an invented exact acceptance or deployment timestamp.
Replay at that immutable checkout with the retained run/jobs inputs; later hold
registry changes deliberately invalidate reproduction on another checkout.

[Public verifier](live-verification.json), [13 exact-byte data/profile checks](live-data-and-admissions.json)
and [browser source labels](live-browser.json) separately establish delivery.
SEBI's 13 unique filings are deduplicated from four requests, not 52 issuers or a
verified full-history crawl. BSE's primary page returned no parsed rows and its
SME endpoint timed out; absence of IPOs is not inferred.

The normal core maintenance stage also populated Vinod's financials, objects and
shareholding. [Official source review](../../../reviews/2026-09-19-vinod-publication-source-review.md)
confirms all nine financial and five allocation amounts. It rejects the derived
93.11% ownership and incorrect locator. An exact value-scoped hold is being
released through the existing review-only path; no collector or canonical writer
change is required. Preserve all source/correction history and publish the new
manual review. Final acceptance of that hold remains pending at this checkpoint.

P4 before the hold is unchanged at 387 actionable + 63 higher-priority, 1,552
blocking / 1,556 total reviews. Local held projection adds one review: 1,553 /
1,557, with zero semantic errors or unmapped reviews. No numerical repair or
blocker reduction is claimed for this operational milestone.
