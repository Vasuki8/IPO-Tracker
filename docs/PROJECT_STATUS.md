# Project status and release evidence

## Standing requirements

IPO Tracker is intended to become a public commercial product. Audience, pricing
and revenue model remain undecided. Preserve trust, accessible mobile research,
privacy, stable URLs and sustainable costs. Keep the light static architecture.
No new spending, contracts, outreach, tracking, billing or material access changes
without owner approval. Sponsorship must be identifiable and cannot affect facts
or research rankings. See [COMMERCIAL_READINESS.md](COMMERCIAL_READINESS.md).

Completed static terms require matching Final Prospectus field evidence. Active
provisional disclosures and official market observations must remain labelled.
Preserve source URLs, document identity, dates, units, nulls, separate source and
collection clocks, quarantines and correction history. P5/performance expansion
remain gated by P4. See [ROADMAP.md](ROADMAP.md) and [OPERATIONS.md](OPERATIONS.md).

## Current verified implementation — 18 September 2026

[PR #126](https://github.com/Vasuki8/IPO-Tracker/pull/126) is merged and deployed at
`edb46e59dfeed64d7cc9f6c8e21b5430d76290aa`, tree
`f298697abb187f57b6449ae6409adef7edb5e84f`. Reviewed head is
`c758b08b71634fcd57de7819f0cc970099270619` on
`feat-read-only-update-health-20260918`. This documentation closeout on
`docs-update-health-checkpoint` records the release, not another implementation.

### Reconciled starting point and preserved ongoing work

Since the prior verified checkpoint `4552e771`, existing core run `35312842043`
published `d462f858fcdb18909180f8747c0e2bf0552dd6f8` at 06:01:12 UTC. Its Pages
and live acceptance succeeded as runs `35313116249` and `35313150717`. That
publication added one record (`swastika-infra-ltd`) and changed 37 existing records
beyond the policy-check clock. Those are pre-existing automated changes, not
changes from this report. Current inventory is **1,367**, not 1,366. Original
subscription-triage implementation #123 and documentation #124 are complete.

[PR #125](https://github.com/Vasuki8/IPO-Tracker/pull/125), branch
`fix-actionable-public-source-holds`, remains open and unmerged at
`be7c448544381cdc0723e09b01f3734713ec8f05`. Its prepared source-hold/queue repair
uses a different candidate inventory/hash and is not promoted by this increment.
Its reported source/browser checks have not been independently repeated here.
Preserve its work and reconcile it with current main before release. Broad draft
#105 remains unaccepted at `5a63a93dd9f782e3bc9ec853c937fb29661108f4`, source freeze
`409c51c9`, preserving #94/#98/#99/#104. No source parser or preview was merged.

### Completed: read-only source and publication health

Problem: operators could not distinguish missing/old source observations, failed
or deferred collection, and actual publication delay. Researchers can otherwise
mistake a recent build or accepted snapshot for fresh source data.

`tools/report_update_health.py` reports those signals separately using the existing
source-bound subscription and public-quality rules. It requires an explicit zoned
assessment instant, keeps every lifecycle cohort counted, preserves failed and
partial outcomes, and never fills an observation time from collection/generation
clocks. Old stages stay visible without an invented live cadence. Successful
zero-row checks are not labelled failures. Operational tolerances are labelled
operator policy, not an exchange-session calendar or service-level guarantee.

An old accepted snapshot alone cannot prove publication delay. Optional complete,
run/attempt/repository-bound GitHub run/jobs evidence distinguishes collection
failure, publication failure, recorded waiting/overdue work and a completed run
without matching acceptance (which can be a legitimate no-change). This is offline
assessment of supplied evidence, not live polling. No result authorizes a retry.

Reports bind input, hold, code and schedule bytes. Reproduction uses the original
assessment instant and explicitly does **not** assert freshness now. A changed
collection cron set requires tolerance review. The existing read-only validation
job retains `update-health.json` in its existing report artifact before correction
rehearsals. Only two offline workflow commands were added: no schedule, alert,
writer, dependency, source request, public payload or permission expansion.
See [UPDATE_HEALTH.md](UPDATE_HEALTH.md) for commands and limitations.

### Verified acceptance and measured result

All **1,098 local Python regressions**, including **20 new health tests**, passed
through uv. Eight Node quality tests passed. The exact omitted workflow files were
recovered and blob-verified, so no local workflow tests were excluded. Local
`uv sync --frozen --offline` lacked locked packages; local execution used the
available Python 3.13.5 environment and is **not a local frozen pass**.

[Frozen PR validation 35314569813](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35314569813)
passed the full suite, report generation/replay, protected-input checks, strict
validation and generated/support checks using Python 3.12 and `uv sync --frozen`.
Its test merge was `41ff686eadc523f2684dc9bb1e29d49dcbe04185`. Downloaded artifact
10534319364 verified ZIP SHA-256
`4ade7a2533fd6b692e84d3f5f27a53e6b9e913de7b2b66f7c2f42b9798312a63`.
The health report reproduced locally at its original **06:22:37 UTC** assessment;
report SHA-256 is `786512d841ccaac27a1dd2b5972e60f4b6d6db88f91f9ee96252e68390071119`.
[Post-merge validation 35314904775](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35314904775)
also succeeded. All four uploaded code/test/workflow/guide blobs match tested bytes.

At that assessment, eight issues were open by recorded dates: **seven unknown source
observation times**, **one overdue observation**, **six overdue collection times**
and **two missing collection times**. Twelve records with unknown lifecycle dates
remain counted. These are operational evidence gaps, not new source errors or
resolved reviews. Consumed-field excerpts from the actual completed core run and
its complete two-job inventory separately produced `accepted_run_matches`; this
neither refreshes its source observations nor proves a new source-value review.

All **1,367 profiles rebuilt without changes**. Strict validation remains zero
semantic errors and 1,596 reviews. All accepted baseline file bytes are unchanged
by #126, including canonical data, **441 pending proposals**, phase state, display
holds and public output. The 159 document and 22 subscription proposal comparisons
remain unresolved; 260 other-family proposals remain unassessed. Emmvee's existing
`do_not_apply_as_proposed` advice is still applicable, not a proposal resolution.

[Pages 35314904599](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35314904599)
deployed the exact merge. [Live acceptance 35314937796](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35314937796)
passed on its first attempt: all 1,367 local profiles consistent and **17 complete
HTTPS responses** matching the immutable release. Downloaded artifact 10533879198
verified SHA-256 `d9c0a7abb9ccf0bc97ce41531a1c3474a54b2d854ebc3738190d28954c43061d`;
its file hashes match local output. Ordinary core publication correctly reports
`reviewedPublication.status=not_requested`, not a new reviewed repair.

[The retained receipt](releases/2026-09-18-update-health-report.json) includes the
unaltered live receipt values, report/input hashes, run/job excerpts and exact
limitations. No new browser journey suite, source collection or PDF review ran
for this offline operator-only change. All implementation/release acceptance
criteria for #126 are complete; scheduled monitoring is not implemented.

The runtime working copy is a labelled artifact mirror, not remote Git history.
The checksum-verified baseline archive is Pages artifact 10533717197, SHA-256
`d0d7911a9b6f77b60d85d2eb2f48d7ab8ec55a2863dfb6c66d59f50f3759e6b5`.
Original archives remain untouched. Direct Git access failed DNS; authenticated
GitHub reads/writes and CI supplied the remote verification evidence.

### Remaining gate and exact next task

P4 remains **incomplete: 387 actionable + 52 higher-priority records**, **1,596**
total reviews, **1,592 blocking**, **four P5-only**, **zero unmapped** and zero strict
semantic errors. Teamtech remains held. P5/performance expansion stays gated.
Commercial source rights, audience, pricing and privacy decisions remain unresolved;
no spending, contracts, outreach, tracking, billing or access changes were introduced.

**Next concrete task:** reconcile existing #125 with the latest accepted baseline
and preserve the newer reporting/review tooling. Review its exact source-hold and
queue changes, verify all 1,367 records and 441 retained proposals are preserved,
then complete its source, regression, browser and deployment acceptance before
merging. Do not substitute its older prepared counts/hash for current main. After
that repair, use a newly generated health report plus the actual latest subscription
run/jobs to diagnose overdue collection; recover original source URL/issuer evidence
before any disposition of the 22 retained subscription proposals. Do not add alerts
or a new writer as a substitute for repairing the existing path.

[ROADMAP.md](ROADMAP.md) now separates current dependency order from its complete,
byte-preserved [dated audit](ROADMAP_DATED_AUDIT.md). Earlier checkpoint details and
source lineage remain in [the prior immutable status](https://github.com/Vasuki8/IPO-Tracker/blob/d462f858fcdb18909180f8747c0e2bf0552dd6f8/docs/PROJECT_STATUS.md)
and existing release/review receipts. No prior audit or retained work is discarded.
