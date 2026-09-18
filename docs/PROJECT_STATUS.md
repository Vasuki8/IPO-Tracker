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

## Verified core subscription boundary — 18 September 2026

[PR #135](https://github.com/Vasuki8/IPO-Tracker/pull/135) merged as
**`2ae2f3e7fa1f0a8354744c7e69969f69cf534486`**, with reviewed head
`7b6d46118a68a869ea52a619438881996b4cac1e` on
`fix-core-subscription-boundary`. Reviewed and merged tree:
`327f84003f3835bd3c82a88fb6c4ffff9de8b31e`. Implementation is accepted and
Pages/live delivery is verified. This closeout on
`docs-core-subscription-checkpoint` records that release.

### Completed behavior and acceptance

Researchers could see a newly collected NSE summary total attached to older BSE
or secondary categories, source URLs and clocks. The publisher's atomic group
could not catch a mixed candidate already assembled by the core collector.

Generic issue-feed multiples now stay in an independent
`observations.NSE.subscriptionSummary` object. It retains the feed endpoint,
issuer and offer dates, raw source inputs including `noOfSharesOffered`,
category/series, parsed multiples and collection clock. Source time stays unknown;
the denominator remains explicitly unverified. Core merging preserves the entire
accepted `subscription*` family and history, including missingness. Normal
lifecycle updates continue, and concurrent accepted detail snapshots survive.
Competing summary observations retain the whole candidate as a pending review.

**This is a prevention release. The eight historical diagnostic snapshots remain
unresolved; neither total was accepted, restored or declared final.** The detail
collector's existing source-bound acceptance rules remain unchanged.

Starting checkpoint was `b3a108785c8f4436cd83a14c2ea408ed1f9e9683`; #125–#134
were already complete. Independent maintenance publication
`c5c42c7e26f42ac85cfdffbcc280775af40a687c` landed during this work and was
preserved through merge `ccb81c96cb1c53c237a051aadd6b589efd17835c`.
Its source-value changes are not attributed to #135. The complete data and profile
trees, `pyproject.toml` and `uv.lock` match that current-main baseline exactly.
All 441 retained proposals and existing holds/correction history remain intact.

### Tests, source checks and actual delivery

The test-only parent `5d39041f7ba50e283cedbbc64d67067b96b93156` reproduced all
eight mixed totals in [frozen CI 35375027327](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35375027327).
All reported failures were in the six new boundary tests. The ratios came from
the retained release diagnostic; reconstructed issuer shells/API rows are
synthetic fixtures, not original HTTP responses.

[Final-head validation 35375889352](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35375889352)
passed **1,161 regressions**, including seven new tests, on Python 3.12.14 with
`uv sync --frozen`. It also passed strict validation, compact artifact checks and
read-only proposal/update-health reports. Earlier implementation and reconciliation
runs 35375378425 and 35375633999 passed; post-merge validation 35376223457 passed.

[Final-head browser CI 35375889499](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35375889499)
passed eight Node tests, 25 research journeys, mobile layouts through 320px,
freshness, cross-surface holds, BSE authority and reviewed Emmvee/Teamtech checks.
Post-merge browser run 35376223442 also passed.
The browser workflow now watches both core files. Screenshot artifacts and their
GitHub-reported digest are retained; this disconnected session did not download
or visually inspect them.

A current [NSE issue-feed read](https://www.nseindia.com/api/ipo-current-issue)
confirmed the reported raw denominator alias and the eight diagnostic rows.
NSE detail and BSE demand URLs were inaccessible through the read tool.
No comparable detail denominator, source-observation timestamp, full HTTP body
digest or numerical replacement was verified. Exact interpretation is in
[the source/boundary review](reviews/2026-09-18-core-subscription-boundary.md).

[Pages 35376222084](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35376222084)
and [live acceptance 35376272766](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35376272766)
passed at the merged commit. The actual first-attempt log receipt binds **1,371
routes** and **22 complete HTTPS responses**, including the held profiles and
review reports. `reviewedPublication=not_requested` correctly identifies this as
ordinary delivery. [The release receipt](releases/2026-09-18-core-subscription-boundary.json)
preserves the live response/digest report, test and tree bindings, and limitations.

The local execution environment is disconnected (`409 environment_offline`).
Files were edited through GitHub repository tools; test execution is verified CI,
with no local pass claimed. No new paid service, writer, schedule, dependency,
tracking, billing or access change was introduced.

### Remaining gate and next concrete action

Current accepted inventory: **1,371 records**. P4 remains incomplete with **387
actionable + 56 higher-priority records**, **1,603 reviews / 1,599 blocking**,
four P5-only and zero unmapped. P5/performance expansion remains blocked. Teamtech
stays held and accepted Emmvee evidence is intact. #105 remains draft at
`5a63a93dd9f782e3bc9ec853c937fb29661108f4`; preserve #94/#98/#99/#104 and the
`409c51c9` freeze. Commercial rights, audience, pricing, privacy and applicable
professional-review questions remain unresolved.

**Next: review the eight historical mixed/unbound snapshots using exact
issuer/offer, source and bid-denominator evidence; use an explicit evidence-bound
public hold when reconciliation is unavailable.** Do not restore the prior total,
backfill observation clocks, infer finality or discard proposals. The existing
PDF/value hold registry requires static-field PDF proofs and does not currently
support these market snapshots; do not fabricate a PDF binding. Keep any market
hold narrowly bound to the actual snapshot and route its review into actionable
work across directory, profile, comparison and exports.

SpectraA's missing matching source and the 22 original subscription proposals
remain open. The existing ordinary repair workflow
[35376223422](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35376223422)
was still collecting as this checkpoint was prepared; no completed source repair
or publication is claimed from it. Check its actual outcome and any later main
commit before modifying current data. Older collector artifacts fail the updated
source-code guard and require recollection. No separate future task was configured.

The [prior checkpoint](https://github.com/Vasuki8/IPO-Tracker/blob/b3a108785c8f4436cd83a14c2ea408ed1f9e9683/docs/PROJECT_STATUS.md),
source reviews and original historical diagnostics remain preserved.
