# Operational receipt coverage — 19 September 2026

Baseline main: `5531a7cfbc668f0929a7264d599f1b41804c61e1`. The existing
operational report, source-check clock repair and public labels were already
released in #149–157. The newer #158–161 active-offer receipts were absent from
that report; #162–163 later admitted identities without refreshing those receipts
or changing the last collector publication metadata. None of that work is repeated.

Operators need to distinguish a reviewed provisional offer receipt from the
general NSE collector check. Schema 3 of `tools/report_update_health.py` now reuses
the exact receipt replay and shared public projection on copies. Every retained
receipt remains visible, including invalid, conflicting, held and expired evidence.
Source observation, collection, review and unknown acceptance clocks stay separate.
No source collector, canonical writer, scheduled deadline, alert, public dashboard
or public display policy is added or changed.

## Frozen assessment

[Machine-readable report](report.json) and [operator view](operator-view.md) are
assessed at **2026-09-19T04:30:00Z**. They are frozen evidence, not live monitoring.
[Before report](before.json) uses the original implementation at the baseline
commit, assessed at 04:23:20Z without workflow snapshots. Compare the identical
source/stage/proposal counts; no reduction is attributed to this reporting change.

- Three receipts: **Axiom Gas, Varmora Granito and Pooja Logistics**, all provisional
  at assessment; all three source observation clocks are unknown. Their original
  source URL/hash, parser version, collection/review clocks and unresolved total
  amounts remain. Axiom/Pooja minimum bid quantities also remain undisclosed.
- **5 failed / 1 partial / 27 successful source entries**. Three source checks
  (BSE, NSE-live, SEBI) and one core stage exceed the recorded operator tolerance.
  Four stages and eight sources need investigation. A recent build does not reset
  these old checks; this is not proof that a particular scheduled run was missed.
- Five open-by-recorded-date subscription snapshots: three unknown observations,
  two observations older than tolerance. Assessment is outside the weekday
  subscription monitoring window, so this is not a missed intraday deadline.
- **441 unresolved proposals** remain. All have separately labelled originating
  publisher execution windows from the retained immutable workflow evidence;
  exact proposal creation times remain unknown. No proposals were resolved.
- Last recorded collector publisher **35417782070**, execution **03:11:03–03:11:33Z**,
  binds to collector `9c404bea6e7edbeccee4680e7cce7d0984d6c57e`.
  Collection completion to publisher completion was 32 seconds. This window is
  neither the per-receipt acceptance instant nor the latest canonical identity
  edit or deployment time. [Run](accepted-run.json) and [complete jobs](accepted-jobs.json)
  were retrieved from GitHub during this assessment.

P4 remains **408 actionable + 67 higher-priority records**, **1,553 blocking /
1,557 total source reviews**, zero semantic errors/unmapped reviews. P5 remains
blocked. [Preservation receipt](preservation.json) binds unchanged canonical,
proposal, phase, queue, holds and reviewed correction registry bytes to baseline.
The existing commercial rights, audience, pricing, revenue model and hosting
decisions remain unresolved; this change activates none of them.

## Acceptance and verification

The report must list the three real source receipts without borrowing collection,
review, generation or general NSE clocks for observation. It must keep expired,
invalid, held and conflicting receipts; use the shared field display states; and
leave canonical, proposal, source-review and phase evidence unchanged.

Eight focused tests cover real source replay, independent clocks, India-midnight
expiry, partial withholding, exchange contradictions, malformed/null/hash-tampered
receipts, future clocks, inactive lifecycle and Markdown retention. The existing
operational suite covers failed/deferred/unavailable collection, delayed publication,
secondary versus official authority, unresolved proposals and timezone contracts.

Local results: **40 health tests**, **38 JavaScript tests**, strict validation
**1,404 records / zero errors / 1,557 reviews**. Full Python ran **1,347 tests**;
the only two errors are the existing Windows newline-filename and symlink-privilege
limitations. Linux CI and release evidence will be recorded in the closeout.
No browser behavior changes; no new numerical source review or repair is claimed.

Released through [PR #164](https://github.com/Vasuki8/IPO-Tracker/pull/164),
implementation `2b5f5d3c41fcec97f5a19d14663d3918a719fdbe`, merge
`aa4d5b4709a5b62bb4be8fa5ba95800984df8be9`. **All 1,347 Linux tests pass** in
PR validation **35421655528** and main validation **35421730603**. Pages
**35421729869** and live verification **35421750703** passed. The
[release receipt](release.json), [21-file live verifier](live-verification.json)
and [eight targeted live byte comparisons](live-report.json) confirm delivery of
the report and unchanged public profiles. No bounded acceptance criteria remain.

The retained [later refresh run](latest-run.json) and [complete jobs](latest-jobs.json)
for **35418300903** show success without a matching accepted run ID; its general
collection step was skipped. The existing delivery assessment is
`completed_without_matching_acceptance`, not publication failure. It does not
refresh the older core check clocks. Exact no-change/retry decisions still require
the original bundle and existing source-manifest safeguards.

Replay on the implementation checkout with its unchanged data/policy inputs:

```sh
uv run --frozen python tools/report_update_health.py \
  --check-report docs/audits/operational-health/2026-09-19-offer-receipts/report.json \
  --workflow-run docs/audits/operational-health/2026-09-19-offer-receipts/accepted-run.json \
  --workflow-jobs docs/audits/operational-health/2026-09-19-offer-receipts/accepted-jobs.json \
  --proposal-workflows docs/audits/operational-health/2026-09-18/proposal-workflows.json
```

Successful reproduction asserts the original assessment only. Later canonical or
policy changes intentionally invalidate it. Original response bytes remain in the
existing receipt/fixture locations; this audit does not duplicate or recollect them.

## Next operational task

Investigate the three overdue core check clocks using fresh refresh-workflow
run/job evidence. Separate scheduled-run delay, failed collection, no-change runs
and publication acceptance before choosing an existing bounded retry. BSE's
retained main-page parsing/SME access failures remain unresolved. Do not infer a
successful refresh from recent reviewed/presentation releases, remove reviews,
introduce another writer or start P5/performance.
