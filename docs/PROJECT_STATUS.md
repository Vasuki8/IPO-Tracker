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

## Verified recovery milestone — 18 September 2026

[PR #137](https://github.com/Vasuki8/IPO-Tracker/pull/137) is merged as
`8dd2a51305a21b5ddb9aebf6c7861128a985ebd0`, tree
`97db9fa055262310c546c867841109892022bae2`. Reviewed head was
`eebd4ff8ba897b91526ac0eaf3986bdffc1795e8` on
`fix-historical-subscription-review-holds`. The existing review-only publisher
produced **`f6db111ac3275a180562e2251c95818b23f4a95f`**, tree
`fa05493d9e58ef4dd35df0a451a6ffbb9ce52eb0`. This output is live-verified.
Documentation closeout branch: `docs-subscription-hold-recovery-checkpoint`.
No second implementation milestone is included in this recovery.

### What survived the interruption

The older portable core-collector patch was recovered and checksum-checked, not
reapplied: #135 and #136 had already completed. Current main was the independent
repair publication `4688128d226c86fd1194f519a09688fed91297cd`, with successful
Pages/live runs 35378534547/35378579959. Its 1,371 records and 441 proposals were
preserved. Original repair/source branches and the handoff archives remain intact.

Open #137 already contained the next historical-snapshot hold implementation at
`482eae8a69f452b8e418acbd4303c36edbff248c`, with source-note parent
`0b27f66c244074e971a0c7e08591f0b842b3cacf`. Its tests/browser checks passed but
release run 35380352028 correctly rejected `spectraa: held subscription leaked`:
it inspected old generated outputs before the review publisher had rebuilt them.
The failed receipt was downloaded and checksum-verified, not disregarded as a pass.

### Completed problem and acceptance criteria

Unreconciled historical subscription figures must not appear as ordinary reported
multiples or escape through chart/history fallback. The existing hold registry now
retains eight exact issuer/offer/snapshot bindings, separate from static PDF holds.
Only SpectraA still matches the current held snapshot: the independent repair had
already replaced the other seven through the existing collector. Those newer
snapshots were neither overwritten nor declared audited resolutions by this work.

A collection-clock refresh or a later history row cannot release mixed facts.
Actual source identity, observation time, category values, missing keys and nulls
remain part of the evidence boundary. Active holds withhold subscription multiples
and history in shared public projections and expose an accurate Field evidence
explanation. Every active hold reaches an actionable manual source-review task,
without inventing a Final Prospectus repair gap or accepting a replacement number.
The [retained review](reviews/2026-09-18-subscription-snapshot-holds.md) preserves
the original dataset/source limitations and eight bindings. The original before/
after hashes and all eight diagnostic changes were independently replayed here.

Recovery follow-up `fddf7cf9` adds a PR-only isolated Git-export rehearsal using
only the four existing derived-output builders. It rejects dirty/mismatched
checkouts, unsafe destinations, missing inputs, symlinks, failed builders and any
protected-file mutation after each stage. Candidate receipts are explicitly not
deployments. Actual deployed verification remains read-only and never rebuilds.
Follow-up `eebd4ff8` narrowly includes the known read-only release workflow in
review-mode routing; any mixed collector, dependency or canonical change still
requires repair. No new publisher, schedule, permission or dependency was added.

### Tests and actual publication

Final-head frozen validation **35383110930**, candidate release **35383110680**,
source-hold evidence **35383110671** and BSE-host evidence **35383110585** passed.
[Browser 35383110570](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35383110570)
passed 25 existing journeys plus active subscription-hold profile/quick-view,
directory, comparison and CSV checks at 1440/375/320 pixels. Static holds, BSE
labels, freshness layout and the reviewed Emmvee rehearsal also passed. Downloaded
browser results matched their artifact checksum; the 375-pixel SpectraA screenshot
was inspected. No page errors or master-dataset requests were reported.

[Publisher 35383599928](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35383599928)
explicitly selected **review** mode and skipped source collection and P4 residual
extraction. Its Python 3.12.14 / `uv sync --frozen` run passed **1,182 regressions**
(21 added across the recovered hold and recovery changes). Post-merge validation
35383599887 and browser 35383599949 passed. Local uv tests passed 12 hold tests,
eight isolated-rehearsal tests and one routing test; nine Node tests passed.
Local Python 3.13 with available packages is not the frozen CI environment.
The Pages mirror lacks some workflow files and direct Git failed DNS; no full
local frozen suite or local browser run is claimed. Remote writes used the actual
connector and original ancestry, not reconstructed local Git history.

[Pages 35383703226](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35383703226)
and [live acceptance 35383754007](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35383754007)
succeeded. The checksum-verified first-attempt receipt checks all **1,371** local
profiles and **23 complete live HTTPS responses**, including SpectraA and its
validation/queue. The deployed workflow skipped the PR builder. Its ordinary
`reviewedPublication=not_requested` is not a new reviewed numerical repair.

Downloaded baseline/published trees and local read-only verifier replay confirm
all canonical/proposal bytes, values, clocks, proofs and correction histories are
unchanged. Teamtech and Emmvee public bytes are identical. SpectraA's displayed
subscription is withheld; heromotors, jsipl and ssretail additionally lose expired
provisional price bands under existing India-date rules. Four profiles changed,
1,367 did not; this is not four source-data corrections. No new numerical source
or full-PDF audit is claimed. The [release receipt](releases/2026-09-18-subscription-hold-recovery.json)
retains exact hashes, lineage, checks, publication scope and the unaltered live
receipt. All acceptance criteria for this hold-delivery milestone are complete.

### Remaining blockers and exact next task

Current P4: **388 actionable + 55 higher-priority records**, **1,601 total source
reviews**, **1,597 blocking**, four P5-only and zero unmapped. The extra blocking
review is SpectraA; it is unresolved work becoming visible, not completion.
Priority changes also reflect the India-date rollover. All **441 proposals** remain
pending. Teamtech stays held; #105 remains draft/unaccepted at
`5a63a93dd9f782e3bc9ec853c937fb29661108f4` with code freeze `409c51c9`.
Preserve #94/#98/#99/#104. P5 and performance expansion remain gated.

**Next:** obtain exact SpectraA issuer/offer/source-detail and bid-denominator
evidence before a bounded subscription correction. Do not replace its number from
headline feeds/history or clear the hold by changing collection clocks. The other
seven historical bindings are retained, not marked resolved; the 22 retained
subscription proposals still need original source/issuer evidence. Revalidate the
stale Emmvee operator advice rather than renewing it automatically. Source rights,
customer segment, pricing and privacy remain unresolved; no spending, outreach,
tracking, billing, infrastructure or access changes were introduced.

Earlier detailed status remains [immutable at the recovered baseline](https://github.com/Vasuki8/IPO-Tracker/blob/4688128d226c86fd1194f519a09688fed91297cd/docs/PROJECT_STATUS.md).
Existing source reviews, correction histories and the dated roadmap audit are preserved.
