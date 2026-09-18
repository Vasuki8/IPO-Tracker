# Project status and release evidence

## Standing requirements

IPO Tracker is intended to become a public commercial product. Audience, pricing
and revenue model remain undecided. Preserve trust, accessible mobile research,
privacy, stable URLs and sustainable costs. Keep the light static architecture.
No new spending, contracts, outreach, tracking, billing or material access changes
without owner approval. Sponsorship must be identifiable and cannot affect facts
or research rankings. See [COMMERCIAL_READINESS.md](COMMERCIAL_READINESS.md).

Completed static terms require matching Final Prospectus field evidence. Active
provisional disclosures and market observations keep their separate authorities.
Preserve source URLs, document identity, reporting dates, units, nulls, independent
source/collection clocks, quarantines and correction history. P5/performance
expansion remains gated by P4. See [ROADMAP.md](ROADMAP.md) and [OPERATIONS.md](OPERATIONS.md).

## Verified implementation and publication — 18 September 2026

[PR #131](https://github.com/Vasuki8/IPO-Tracker/pull/131) merged as
`30e994f7265719cf91e1004df978d403c45093a1` (tree
`e5650c527e746d85c4d81456a1e2e629efecfbf9`). Reviewed head was
`40a310075a7bed39403afff10f52a32febe502ac` on
`fix-subscription-snapshot-source-binding`. Its existing subscription publisher
produced **`70a5133f11bce99f9e432c1ae56b52c29b012593`**, tree
`471130c973180688fbeaf82a314f162667a1c072`; this publication is live-verified.
This documentation closeout on `docs-subscription-snapshot-binding-checkpoint`
records that completed increment, not another source correction.

### Recovered work was already complete

The handover and earlier status were behind current main. Recovery started at
`9210afeac2867d2ebbdfadd290706ec6a528bf4c`: #125 had already merged as
`cc41fad70e01866d0116f6dfca1a07082da10cc4`, followed by review-only publication
`fe0bd1f4e807d0be52c6be16722ac2ba0b42a3b7`. #130 added live verification of the
held intermediary profiles and validation/queue/phase files. Baseline Pages
35353803775 and live acceptance 35353865005 succeeded. The downloaded baseline
and receipt were checksum-verified. Do not repeat #125 or import its old reports.

### Completed milestone: source-bound, unmixed subscription snapshots

Affected users are daily IPO researchers and repair operators. The retained
collection bundle from run 35350847357 showed that seven successful observations
omitted their direct source URL from the atomic subscription group even though
history contained it. The writer also borrowed absent categories from an older
observation and re-stamped them with a new source/time; numeric-only history
deduplication lost equal-value source and observation changes.

Acceptance: keep each new snapshot's numbers, URL and independent clocks together;
preserve source changes in history; and reject invalid or incomplete responses
before modifying the previous snapshot. A response omitting a previously populated
category (including zero) now leaves all prior values, source metadata, clocks and
history untouched. First partial observations retain nulls. No source-observation
time, final-subscription status or historical URL is invented. The old borrowed-total
test is strengthened to require complete preservation rather than removed.

A narrowly allowlisted leaf-collector change selects the existing `subscriptions`
mode. Mixed collector/policy/data/workflow/dependency changes still require guarded
repair; mixed reviewed requests fail. No workflow, writer, schedule, source ordering,
dependency, account or permission was added. See the [diagnosis and acceptance note](reviews/2026-09-18-subscription-snapshot-binding.md).

### Tests and actual release evidence

Fifteen new tests, ten existing subscription tests and eight Node quality tests
passed locally through uv. The complete local attempt ran 1,144 tests with eight
errors caused by missing workflow files in the Pages mirror; frozen offline sync
also lacked locked packages. These are not full/frozen local passes. Local tests
used available Python 3.13.5 dependencies. No new browser journey suite or full-PDF
source audit is claimed for this collector/provenance increment.

[Frozen PR validation 35365121296](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35365121296)
and [post-merge validation 35365585590](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35365585590)
passed. The actual collector job independently passed **all 1,144 regressions** on
Python 3.12.14 using `uv sync --frozen`. The five-file diff and remote blobs matched
the local candidate, main had not advanced and no review request was outstanding.
Merge used the exact expected head without force or changed protections.

[Collection/publication 35365585525](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35365585525)
selected `subscriptions`, skipped Final Prospectus residual collection and ran no
P5/performance collector. Existing policy checks and derived support builds still
ran. Eight attempts produced seven updates: five through the BSE fallback and two
explicitly secondary IPO Premium observations; SpectraA still failed. Both jobs
succeeded, but source health correctly remains degraded with one failure.

The checksum-verified collected bundle and published Pages tree were compared.
All seven successful records now contain their supplied URL in the atomic group.
Two secondary observations changed values and appended history; five BSE-route
observations retained numbers and unknown observation times. Their collection
clocks advanced without claiming a source observation. All previous history entries
survived. Published records match the collected proposal except two explicitly
verified derived check clocks: `staticSourcePolicy.checkedAt` and, for seven
source-array changes, `validation.checkedAt`. All other static values, complete
field proofs, correction history and review occurrences are unchanged.

The other 1,363 records are unchanged except routine policy-check timestamps.
All **441 pending proposals** and the display-hold registry are byte-identical to
the baseline. SpectraA's subscription values/clocks are unchanged. All eleven
active source holds remain; Teamtech stays held and Emmvee is not re-held. The P4
counts did not improve through this provenance repair.

[Pages 35365791253](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35365791253)
and [live acceptance 35365847478](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35365847478)
succeeded. The downloaded receipt passes **1,370 local profiles and 22 complete
public HTTPS responses**, including held profiles and review reports, and all
hashes match the downloaded published tree. This ordinary subscription publication
correctly reports reviewedPublication `not_requested`, not a new reviewed static
repair. The [release receipt](releases/2026-09-18-subscription-snapshot-binding.json)
retains source/run/artifact bindings, exact publication comparisons and limitations.
Implementation, publication and delivery acceptance for #131 are complete.

### Remaining work and exact next task

P4 remains incomplete: **387 actionable + 55 higher-priority records**, **1,607**
total source reviews, **1,603** blocking, four P5-only and zero unmapped. P5 remains
`waiting_for_p4`. All 441 proposals remain pending: 159 document and 22 subscription
groups still conflict; 260 other-family entries are not assessed. The retained
Emmvee decision reports `stale_evidence` both before and after this release; do not
reuse its old advice without revalidating its changed evidence/hold-registry binding.
Its accepted public composition is not affected by that operator-advice state.

**Next concrete task:** verify the exact `beta.bseindia.com` authority from current
BSE primary evidence, then align the shared Python/JavaScript source allowlists
and real-host regressions if justified. Five current BSE-route snapshots are labelled
`unknown` authority by the existing public boundary, before and after #131. Do not
silently promote them merely to pass an assertion. Keep missing source-observation
times unknown and secondary sources labelled. Then investigate SpectraA's absent
matching source with exact issuer/offer evidence; do not loosen fuzzy matching or
invent data. Historical subscription proposals still need original URL/issuer
proof before any audited disposition.

Broad source draft #105 remains unaccepted at
`5a63a93dd9f782e3bc9ec853c937fb29661108f4`, with #94/#98/#99/#104 and its code freeze
preserved. Commercial rights, customer segment, pricing and privacy questions
remain unresolved; source URL presence is not a redistribution license. No spending,
contracts, outreach, tracking, billing or material access changes occurred.

The runtime used a separate checksum-verified Pages mirror, not a remote Git clone;
original artifacts and source branches remain untouched. Earlier release details
and the superseded status remain in [the immutable recovery baseline](https://github.com/Vasuki8/IPO-Tracker/blob/9210afeac2867d2ebbdfadd290706ec6a528bf4c/docs/PROJECT_STATUS.md).
The dated roadmap audit and immutable source reviews are preserved.
