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

## Current integration checkpoint — 18 September 2026

Accepted data release/current main observed before documentation closeout:
**`de69f6ce92b94ce0acfbe6709c38a1b170c313a8`**. Recovery started from the supplied
`64697fe1d837e422a6678c51959e647fb7ad6e0b`; scheduled core publication
`268946862820bfead2b3b5e0c14c7a1f637d7dd5` arrived during review and was incorporated.
Earlier completed #108, #114–#117 and #135–#138 were recognized, not reapplied.
Documentation closeout branch: `docs-p4-integration-20260918`.

### Completed and verified

[PR #139](https://github.com/Vasuki8/IPO-Tracker/pull/139), merged as
`5039a33853a810b9beafea52a97e8e4e05f38ce1`, adds a reusable paired-column review
helper and evidence-bound intermediary publication. It requires exact issuer/offer
identity, role/name spans from one physical table, document hash/date, Final
Prospectus authority and separate collection/review clocks. Explicit-reviewed
correction groups remain inert in ordinary registry application. Generic
re-extraction of the same PDF cannot undo accepted reviewed role evidence;
different authoritative documents remain eligible. Existing holds/history survive.
The source-free support publisher produced `08b35e42` with unchanged canonical
and pending-proposal bytes.

[PR #141](https://github.com/Vasuki8/IPO-Tracker/pull/141), merged as
`3ef3e3e665eb10752eca7d35d7c273d4e0bd25df`, changes only the reviewed request.
[Publisher 35390088056](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35390088056)
selected `reviewed`, skipped source/residual collection, generated a fresh source
manifest and published `cf4dae81`. Only Snehaa and Sacheerome's intermediary groups
were accepted; 1,369 other issuer records and all 441 pending proposals survived.
Snehaa now has Fast Track Finsec / Skyline; Sacheerome has GYR Capital Advisors /
MUFG Intime India. Complete legal names and matching proofs are retained.

Exact official Final Prospectuses were downloaded and hash/page-tree checked:
Snehaa (467 pages, physical role table 1, corroborating 83) and Sacheerome
(293 pages, role table 3, corroborating 52). The source review distinguishes
Sacheerome's current MUFG legal name from its former Link Intime name. Source
bytes, role rows and rendered pages were reviewed; this is not a claim to have
audited every disclosure in both documents. See the immutable linked source
review and [release receipt](releases/2026-09-18-reviewed-intermediaries.json).

Final PR-head validation 35388997223 passed **1,217 frozen Python 3.12 regressions**;
source-free preview 35388996960 and release rehearsal 35388997191 passed.
[Browser 35388996780](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35388996780)
passed 25 existing journeys, nine Node tests, existing hold/BSE/Emmvee checks and
both new intermediary profile/quick-view journeys at 1440/375/320 pixels. The
downloaded artifact checksum matched; both 375-pixel profiles were visually
inspected. Request validation 35389898010 and five local request tests passed.
Local Windows full-suite limitations (control-character filenames and symlink
privilege) were not used to weaken Linux tests; Linux remains the release authority.

[Pages 35390194114](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35390194114)
and [live acceptance 35390243353](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35390243353)
passed on `cf4dae81`, including exact reviewed values/proofs and served profile
bytes. Direct live browser checks also confirmed Snehaa's page-1 role links and
Sacheerome's page-3 role links in its profile/quick view, with unrelated fields
still under review. Candidate artifacts were never substituted for deployment.

### Current blockers and next work

P4 is **incomplete: 388 actionable + 55 higher-priority records; 1,598 total
source reviews, 1,594 blocking, four P5-only, zero unmapped and zero semantic
errors**. This release removed **three actual blocking reviews** (1,597 → 1,594),
not three whole-record blockers. Final Prospectus revalidation remains 322 records /
1,175 fields (higher priority 28 / 105). Inventory remains 1,371. P5 remains
`waiting_for_p4` with 914 actionable records; performance expansion is gated.

SpectraA's exact NSE SME response now has a retained source/denominator review.
Its counts-only categories, zero-denominator EQ placeholder and graph total do
not establish a safe replacement snapshot. The hold remains active.
[PR #140](https://github.com/Vasuki8/IPO-Tracker/pull/140) merged as
`a0e7e0214bd161b227e822bbe0c41287f8e23429` after combined validation 35390771579
passed **1,239 frozen regressions**, including 22 real-response/guard tests.
The six-file change requires exact issue identity, correct API series and matching
reported multiples/bid denominators; contradictory duplicate counts fail even
when a row lacks a multiple. The response fixture stays outside the unrelated
Final Prospectus preview glob; no workflow or protection was changed. Earlier
broad previews on obsolete heads remain diagnostic and unaccepted.

[Publisher 35390899139](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35390899139)
used `subscriptions` mode and published `de69f6ce`. The source stage reports
`source_blocked`: five attempts, four updated records, zero added history snapshots,
one failure (SpectraA), zero NSE successes, two BSE and two explicitly labelled
secondary fallbacks. NSE returned HTTP 403 in the runner. This is a deployed guard,
not acceptance of a replacement SpectraA number or proof of fresh official NSE
data. All historical source bindings, 441 proposals and Teamtech's hold remain.
The four successful refreshes changed collection/check clocks, not subscription
values or history. Ordinary policy-check clocks were regenerated across the
inventory; they do not represent a new PDF source review. Snehaa, Sacheerome,
Teamtech and SpectraA's generated profile bytes match `cf4dae81` exactly.

[Pages 35391159527](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35391159527)
and [live acceptance 35391206824](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35391206824)
passed on `de69f6ce`. The [NSE guard release receipt](releases/2026-09-18-nse-detail-guard.json)
records the exact source outcomes, canonical/proof preservation and served-output
checks. No additional P4 blocker was removed by this guard release.

Legacy #94/#98/#99 and draft #104 remain preserved. Broad draft #105 stays
unaccepted at `5a63a93dd9f782e3bc9ec853c937fb29661108f4`; its preview passing does
not establish source acceptance, and it conflicts with current main. Do not merge
it wholesale or drop its review evidence. The 22 subscription proposals still
need original issuer/source evidence; stale operator advice needs revalidation.

**Exact next action:** reproduce the Hy-Tech and Onemi table failures with
production `pdftotext`, then implement and source-review the shared bounded
`OTHER FINANCIAL INFORMATION` repair in
[the source diagnosis](reviews/2026-09-18-financial-seed-inspection.md).
Both complete PDFs match retained hashes; targeted rendered tables were inspected
and 102 diagnostic receipt/replay assertions passed. Local pypdf layout is not
established as production extraction parity; comprehensive competing-table review
and financial-specific reviewed transport validation remain to do.
Their 42 financial reviews are exposure, not a promised reduction. Preserve annual
versus interim periods, units, scope, EPS basis, conflicts and nulls; accept only
matching Final Prospectus cells through a bounded publication. Add PNGS only if
its source proves the same layout family.

Commercial rights remain unresolved for collection, excerpts, storage, public
JSON/CSV and paid reuse. Paying audience, pricing/revenue model, suitable commercial
hosting, privacy/telemetry and regulatory review remain owner decisions in
[COMMERCIAL_READINESS.md](COMMERCIAL_READINESS.md). No spending, contracts,
outreach, billing, infrastructure or material permission changes were made.

## Historical recovery milestone — 18 September 2026

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
