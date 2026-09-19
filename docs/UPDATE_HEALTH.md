# Recorded update health — operator report

This read-only report distinguishes **attempt age**, **recorded source outcome**,
**source observation age**, and **publication delivery evidence**. A recent build,
zero exit code or unchanged dataset does not prove fresh or correct source values.
It makes no changes to canonical records, proposals, review decisions or phase gates.
It does not fetch sources, poll GitHub, send alerts or activate another data writer.

## Generate and reproduce

Use the existing frozen environment (`uv sync --frozen`). Supply a timezone-aware
assessment instant; the tool intentionally has no hidden wall-clock default:

```sh
mkdir -p artifacts/update-health
uv run --frozen python tools/report_update_health.py \
  --as-of "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" > artifacts/update-health/report.json
uv run --frozen python tools/report_update_health.py \
  --check-report artifacts/update-health/report.json
```

The CLI prints to stdout only. Never redirect over accepted input files. `--data`
and `--phase` support isolated snapshots. Output binds the exact canonical, phase,
display-hold and code/policy bytes. Reproduction uses the original assessment
instant and returns `freshNow: not_asserted`; it is not a check that an old report
is fresh today. Generate a new report for a new instant. Missing/invalid inputs or
changed report/input/policy bytes fail explicitly.

The existing read-only **Validate IPO changes** job generates `update-health.json`
in its already-retained `proposal-reconciliation-<run>-<attempt>` artifact, before
any correction rehearsals. It records the real checkout SHA and checks that protected
data files remain unchanged. This adds two offline commands, not a scheduled monitor,
source request, dependency, permission or artifact-upload job. Existing fourteen-day
artifact retention applies. There is no addition to public page payloads or tracking.

Schema version 2 also reads the existing pending-proposal reconciliation, review
decisions and source-review queue. It retains every envelope and review, including
`not_assessed` proposals. `--pending` and `--queue` can select isolated snapshots;
the canonical/pending/hold byte bindings must agree with reconciliation. No second
state store is created. Use `--format markdown` for a human-readable view of the
same report. The default JSON contains every retained proposal and input hash.

The [18 September assessment](audits/operational-health/2026-09-18/REPORT.md)
contains real source/stage outcomes and proposal/publication timing evidence.
Its [JSON](audits/operational-health/2026-09-18/report.json) is a frozen snapshot,
not a declaration of current health. Reproduce at its original code/data checkout:

```sh
uv run --frozen python tools/report_update_health.py \
  --workflow-run docs/audits/operational-health/2026-09-18/accepted-run.json \
  --workflow-jobs docs/audits/operational-health/2026-09-18/accepted-jobs.json \
  --proposal-workflows docs/audits/operational-health/2026-09-18/proposal-workflows.json \
  --check-report docs/audits/operational-health/2026-09-18/report.json
```

## Read each independent signal

`stages` preserves the recorded status, exit code, counts and check clocks. Failed,
source-blocked and deferred work remains visible even when recently attempted.
`sourceHealth` entries appear as `sources`; a zero-row successful source check is
not treated as failure. A missing source check time remains unknown, even when its
parent stage or accepted snapshot has a recent timestamp. Conflicting check clocks
are not resolved by choosing whichever is newer. Historical/unmonitored entries
remain present as `recorded_only`, not silently assigned a current live schedule.

Each source row includes its explicit authority role, last source observation,
collection/check clock, latest retained successful parent-stage outcome, failure
or deferral reason, dataset publisher evidence and next action. Source roles are
not field verification. A successful wrapper does not prove each child source
succeeded. If the latest retained stage failed, its earlier success is unknown;
the tool does not invent historical outcomes. Explicit `source_unavailable` is
separate from a source/parser `source_blocked` diagnostic and from retryable failure.
The Python/JavaScript outcome and check-clock contract uses the same golden cases
in `tests/contracts/operational_health.json`. Clock contracts are kept outside the
document-fixture trigger; operational tests do not request a source-repair crawl.

Public source diagnostics use those same recorded outcome/check-clock rules.
Missing checks display `Not available`, never the dataset generation timestamp;
conflicting and invalid checks are labelled explicitly. A `Collection reported`
label describes the retained outcome and does not claim current source freshness.
Legacy global errors remain visible as retained diagnostics without overriding a
separately recorded source outcome. No new public dashboard or data fields are added.

`subscriptions` includes issues open according to stored offer dates and not marked
listed, withdrawn, cancelled or postponed. Every other record remains counted in
`lifecycleScopes`, including unknown/invalid dates. Dates are not guessed to force
an issue into a live cohort. Current subscription diagnostics reuse the existing
source-bound reconciliation rules and public numeric/review policy on copies. They
do not borrow attached source/history URLs, promote a secondary source to official,
replace a missing observation with collection time, or infer final subscription
from the closing date. These conservative snapshot diagnostics may expose gaps
that a public projection can link through separately matching history.

`acceptedPublication.snapshotAge` is age of the stored snapshot's generation clock,
**not** source freshness, accepted-commit time, last successful source check or
actual deployment time. Accepted publication metadata and phase evidence are copied
unchanged. Live deployment is deliberately `not_assessed_by_this_offline_report`;
use the existing public-release verifier for served-byte acceptance.

## Operational tolerances, not source guarantees

Initial operator tolerances are 120 minutes for the hourly core collector, 90
minutes for active subscription checks, 480 minutes for conditional filing work
with a six-hour fallback, and 30 minutes after collection completion for publication.
These are triage settings, not an exchange/service SLA or evidence that a scheduled
run actually fired. `within_tolerance` describes clock age only, never value accuracy
or source success. Failure/degraded evidence is an independent signal.

Subscription deadlines apply on configured UTC weekdays from 05:30 through 14:00:
04:00 first scheduled attempt plus 90-minute grace, through 12:30 last attempt plus
that grace. Outside that window, valid ages remain visible without asserting a
missed intraday deadline. This mirrors the configured schedule, not an exchange
holiday/calendar or trading-hours claim. Filing deadlines are conditional on
recorded higher-priority work. Other stages retain their outcomes without invented
cadences. A changed collection cron set fails the report until these assumptions
are reviewed. No P5/performance deadline or expansion is introduced.

## Diagnose an unpublished run separately

An old accepted snapshot alone cannot distinguish no new data, failed collection,
queue delay or failed publication. Without supplied workflow evidence, delivery
is `not_assessed`. For a specific run, save fresh GitHub REST responses for
`GET /repos/Vasuki8/IPO-Tracker/actions/runs/<RUN_ID>` and
`GET /repos/Vasuki8/IPO-Tracker/actions/runs/<RUN_ID>/jobs?filter=latest&per_page=100`.
Use all jobs if paginated; `total_count` must match. Supply both snapshots:

```sh
uv run --frozen python tools/report_update_health.py \
  --as-of "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
  --workflow-run artifacts/update-health/run.json \
  --workflow-jobs artifacts/update-health/jobs.json > artifacts/update-health/run-report.json
```

Run/repository/branch/workflow/attempt bindings are checked. Foreign, ambiguous or
partial job evidence fails instead of becoming a clean status. Collected work whose
recorded publisher is still waiting can exceed the 30-minute tolerance. Collection
failure, publication failure/cancellation, missing completion time and completed
work without matching acceptance are separate states. A successful no-change run
may correctly create no new accepted run ID, so it is not labelled a failed release.
All results describe the **supplied evidence at the assessment instant**, not a live
poll of the run. Keep the original inputs with the report and retrieve fresh evidence
before acting on old queued/running states. Reproduction never asserts current state.

When workflow identity matches the recorded dataset publisher, successful job
timestamps supply a **publisher execution window** and a separate interval from
collection completion to publisher completion. They do not supply an exact accepted
commit time, per-source acceptance time, or deployment time. Those remain unknown.
Later bounded canonical changes can also leave the last collector-publication
metadata unchanged. Do not describe its workflow window as the latest data edit.

### Reviewed provisional offer receipts

Schema 3 also inspects every retained `activeOfferTerms` entry, including null,
malformed, conflicting, held and expired receipts. The report reuses the existing
receipt validator, exact source-response replay and public projection on copies.
It does not accept a correction, remove a review or recollect a source. JSON and
Markdown show source URL/hash, parser/review version, observation, collection and
review clocks, unresolved disclosures, field display decisions and next action.

These are bounded source reviews, not a scheduled collector. No hourly or
subscription deadline is assigned to them. A newer general NSE check, collection,
review or build cannot supply their missing source observation. Future receipt
clocks require investigation. Replay validity is separate from provisional public
eligibility: existing holds and same-offer conflicts still win, and receipts remain
listed after expiry at the end of the recorded close date in Asia/Kolkata. Field
decisions explicitly identify whether they use this receipt or another source.

Receipt acceptance time and publication lag remain unknown. A source review clock
is not an accepted-publication clock; the last dataset publisher may predate a
later bounded canonical change. Inspect the immutable release and live delivery
evidence separately. Receipt summaries do not alter source/stage failure or
overdue counts, unresolved proposal counts, or P4 review counts.

Optional `--proposal-workflows` accepts an array of `{run, jobs}` GitHub snapshots
for retained proposal `runId` values, with the same repository/workflow/attempt and
complete-page checks. Exact proposal creation age stays unknown because current
envelopes have no creation timestamp. The age range of the originating publisher
execution is reported separately, with that limitation. Even a proposal matching
current canonical data remains unresolved until the existing review process acts.

No result authorizes a retry or publication. Keep the original collection bundle,
check the existing source-manifest guard and source evidence, and use the serialized
publisher. Do not delete proposals, relabel a collector manifest or resolve source
conflicts merely to remove an overdue signal. P4 and commercial data-rights gates
remain unchanged. Future always-on monitoring and alert delivery remain separate,
unimplemented work; this report adds no customer identifiers, paid infrastructure,
external communications or redistribution of new source material.
