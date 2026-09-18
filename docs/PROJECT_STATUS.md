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

## Recovery after the interrupted response — 18 September 2026

The interrupted work **did reach main and publication**. Code [#115](https://github.com/Vasuki8/IPO-Tracker/pull/115)
merged as `8a2ab9d266c7f7e9a4bcc606e9fccf2397b423d4`; the separate reviewed-only
request [#116](https://github.com/Vasuki8/IPO-Tracker/pull/116) merged as
`20d542fcde8b085a49b5443051a7647c624b5680`. Publisher
[35302828628](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35302828628) produced
`3834c7323fc7ae794526942f649d128c209a4997`. [Pages 35302925923](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35302925923)
and [live acceptance 35302956384](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35302956384)
succeeded. Do not repeat the Emmvee request or reimplement #115.

Recovered and hash-verified the actual Pages archive, retained reviewed bundle and
live receipt. The source-commit file is the #116 merge, both snapshot hashes match
the manifest, and replay of the existing transition/precondition checks succeeds.
Exactly **one canonical record, Emmvee**, changed; the other **1,365 records**,
record order, Teamtech and all **441 pending proposals** are preserved. Emmvee's
existing values and allocations were not changed again. The publication paired its
four composition fields with their exact reviewed proofs and appended **one** proof
audit event retaining all previous proofs/history. The proposed and published
record agree apart from the policy check clock. All four public fields are now
`final_verified`; Teamtech's objects remain withheld and `under_review`.

The [recovery receipt](releases/2026-09-18-reviewed-publication-recovery.json) retains
exact hashes, the original live receipt and replay results. The 1,366-profile
consistency check and 17 complete live responses establish served-byte consistency.
Evidence reuse retains the original 00:37 source-check time, PDF hash, document
date, source rows, units and parser lineage; this is **not a fresh PDF review**.

### This bounded increment: reviewed-release acceptance

Branch `fix-reviewed-release-acceptance` starts at `3834c732`. The existing
read-only release verifier now has `--check-reviewed-publication`. When the latest
publication is explicitly `reviewed`, it requires the selected accepted values,
complete retained proofs, issuer/offer identity, public amounts, source timestamps,
document hashes/pages and all four profile verification states to agree. Every
selected profile is added to the full-byte HTTPS checks, even outside the ordinary
sample. Consistently stale/withheld output no longer passes as a delivered repair.
Ordinary source releases explicitly report `not_requested`, not reviewed acceptance.
The master dataset/proof files are read locally, never fetched from the public site.

Acceptance: **16 verifier tests** (eight new), **15 reviewed-publication tests**,
**five request tests**, and **eight Node quality tests** pass locally using uv and
the available Python 3.13 environment. Frozen local sync failed DNS and local
Chromium navigation was administratively blocked; neither is claimed as passing.
The current published tree passes the new read-only check and the retained-bundle
replay. This change does not modify any canonical/proposal data, source code,
public renderer, dependency, permission, workflow writer or phase gate. Only the
existing read-only release workflow opts into the stronger check. Frozen CI,
browser CI and the post-merge live receipt remain to be recorded for this branch.

Current gate is unchanged: P4 **387 actionable + 51 higher-priority records**,
**1,596 total source reviews**, **1,592 blocking**, **four P5-only**, **zero unmapped**,
and zero strict semantic errors. P5 remains `waiting_for_p4`. No completion count
was improved by hiding work. #105 remains draft at `5a63a93dd9f782e3bc9ec853c937fb29661108f4`;
its broad parser/source proposal is still unaccepted. Preserve #94/#98/#99/#104.

No original Git checkout or uncommitted source files survived in this runtime.
The input ZIPs and screenshot remain untouched. This session recovered a separate
working copy from the checksum-matched Pages artifact; direct Git clone failed DNS.
Authenticated connector branch creation succeeded. Remote edits/releases are
reported only after their actual responses and checks.

**Next task after this acceptance release:** add a read-only retained-proposal
reconciliation report, starting with document-field proposals. Classify exact
already-applied versus still-conflicting groups with current accepted evidence;
preserve every original proposal and do not auto-resolve by timestamp. Do not start
that separate milestone in this recovery increment. Commercial rights, audience,
pricing and privacy decisions remain unresolved; no spending/outreach/access changes.

## Preserved source work and historical evidence

The prior pre-release notes, source receipt hashes, earlier handover correction and
implementation rationale remain in [the immutable pre-recovery status](https://github.com/Vasuki8/IPO-Tracker/blob/3834c7323fc7ae794526942f649d128c209a4997/docs/PROJECT_STATUS.md).
The broader source-repair histories are not merged: #94 (`4707df1e`), #98
(`d5e5d058`), #99 (`a503531d`) and #104 (`4d94951b`) remain preserved in draft #105
at `5a63a93dd9f782e3bc9ec853c937fb29661108f4`. Its source-code freeze is
`409c51c939bd839940594278d324016766cb84c6`. Their broad previews remain unaccepted;
this recovery does not adjudicate their values or repeat their collectors.

The retained Emmvee proof is Git blob `5ca3afdf6207c86fbea6f3e5ab236dde6c2fec45`,
SHA-256 `1f8b7ae600da76ea9f62a9771377925d17be3c5d98ebc8080e36b63a9a5795cf`,
from PDF `85eb9319dc01027821813c71d3702164911442a14547ad72cc04270ea6612eda`.
Its original source review is linked inside the recovery receipt and proof index.
Teamtech's unresolved page-89 crore/lakh conflict remains a hold, not an assumed typo.
