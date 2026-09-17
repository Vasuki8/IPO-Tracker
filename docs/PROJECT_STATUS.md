# Project status and release evidence

## Standing commercial and data requirements

IPO Tracker is intended to become a public commercial product. The paying audience,
pricing and revenue model are not selected. Customer trust, repeat research,
accessibility, discoverability, dependable operations and sustainable costs apply
to every milestone. No new spending, contracts, external outreach, accounts,
payments, analytics tracking or materially changed access without owner approval.
Sponsorship must be identifiable and separate from factual verification/ranking.
See `COMMERCIAL_READINESS.md` for evidence and unresolved decisions.

Keep the light/static architecture. Final Prospectus authority for completed
static terms, explicitly provisional active disclosures, distinct source/check
clocks, missing values and correction history remain mandatory. P4 is incomplete;
P5/performance expansion remain gated. Tests do not establish every source fact.

## Recovered state — 17 September 2026

The failed responses did not discard the previous releases. #100 implemented public
field trust; #101 added release verification; #102 fixed its Pages trigger; #103
recorded the observed live acceptance. All are merged. Current main was rechecked
as `cf906df7ccc9bcf40881743b0af39480858a612e`, deployed successfully by Pages run
`35280338567`. Do not implement those milestones again.

The prior automatic live acceptance `35279827685` verified 1,366 local profiles and
17 complete HTTPS responses against deployed commit `02d3b146...`. The complete
receipt is retained in `releases/2026-09-17-public-release.json`; the full earlier
release history remains in this file at `cf906df7`. It is a delivery/consistency
check, not a fresh source or all-profile browser audit. The dated owner roadmap
remains `ROADMAP.md`; current evidence takes precedence over its old counts.

No earlier checkout or unfinished patch survived in the accessible workspace.
Existing source-preview ZIPs, roadmap and screenshots were preserved. The current
Pages artifact `10522721136` was hash-checked. Direct Git/DNS access failed, so a
read-only GitHub runner exported the four pinned public histories in artifact
`10522831961` from run `35280986033`. Its ZIP SHA-256 is
`c9fafb0a0e8bfb36f03608f7a4ffd6ca687f168b471d98da41c210284503f2ef`.
`git bundle verify` confirmed complete history and exact main/#94/#98/#99 refs.
The recovered checkout and source artifacts were not substituted for newer data.

## Active milestone: integrate the pending P4 repairs

**Problem / affected users:** the reviewed repairs must coexist with the deployed
trust boundary before their data can reach directory/profile/comparison/export
users. Independent subscription updates and review history must survive.

**Acceptance:** integrate the exact preserved heads on current main; retain all
public trust, release and P4 gates; exercise repair-to-public-projection behavior;
run frozen and browser checks; require targeted source acceptance before a merge
that would activate source collection. This is not a P4 closeout.

Active branch: `integrate-p4-reviewed-repairs`, [PR #104](https://github.com/Vasuki8/IPO-Tracker/pull/104).
Integrated histories:

- #94: `4707df1e82337e3a7b8bac0838bbaa30c3d200be` — Emmvee composition and reviewed allocation policy.
- #98: `d5e5d0580360a87dffc35b69e674886848b55005` — source-policy and manifest publication safeguards.
- #99: `a503531ded368c4eb53ba09cf5c2aafef3391c38` — Kaytex/SPEB holds and final-preview review ordering.

All three actual Git merges were clean despite GitHub's earlier non-mergeable
flag for #94. Original remote branches are untouched. The temporary recovery
workflow is absent from the final proposed tree; its commit/artifact survive.

Four new integration regressions cover: repaired Emmvee reaching summary/profile
with matching proof; Teamtech's corrected allocations clearing its value-scoped
hold while keeping the review; the five continuing canonical holds working without
temporary display holds; and Kaytex/SPEB post-publication holds preserving an
independent subscription update and distinct clocks. Existing repair fixtures and
physical source excerpts are reused; these are not new complete-PDF acceptance.
Browser CI now also triggers for shared source-policy/validator dependencies that
can change public field decisions.

Local results: **1,027 Python regressions**, **seven Node quality checks** and
frontend syntax checks passed. Execution used uv with available Python 3.13 and
pypdf 5.9. `uv sync --frozen --offline` could not install locked packages; no local
frozen pass is claimed. Actual GitHub frozen/browser outcomes belong in the PR
and a subsequent observed-results entry, never inferred from local success.

Canonical IPO data, pending proposals, phase status, committed public outputs,
public trust implementation, light frontend and the serialized publisher workflow
remain byte-identical to the inspected main. The corrections registry is
intentionally integrated as policy, not a published data repair. The broad preview
remains unaccepted; no source-code merge or new deployment is claimed here.

## Release blocker and exact next action

Finish PR #104's frozen/browser verification, then run explicitly targeted
seven-record source acceptance from the combined code and the then-current accepted
dataset. Verify full Emmvee and Teamtech Final Prospectuses; produce complete
value/proof groups; preserve the five continuing holds, Kaytex/SPEB safeguards,
unaffected records and retained proposal history. Generate a new bundle under the
combined policy rather than relabelling an old collector manifest. Source review,
current-base acceptance and required checks precede merge/publication; verify the
actual generated and deployed profiles afterward. Do not merge only because the
deterministic tests pass: main's source-code push activates automatic collection.

The last inspected canonical gate (21:40:41 UTC at `e3ee0fe1...`) remains **385 P4
plus 51 higher-priority actionable records**, **zero semantic errors**, **1,614
blocking reviews**, including **17 unmapped**. P5 is `waiting_for_p4`, with 914
queued records. Integration does not resolve those items or alter the gate.

Proposal triage, semantic-review routing, overdue-source monitoring, lifecycle
work and remaining P4 evidence batches remain unfinished. Commercial reuse/hosting
permissions, customer validation, dependency/asset notices, professional review,
telemetry decisions and a restore rehearsal remain unresolved. No spending,
contract, outreach, tracking, access change or monetization was activated.
