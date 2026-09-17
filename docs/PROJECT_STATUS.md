# Project status and release evidence

## Standing commercial and data requirements

IPO Tracker is intended to become a public commercial product. The paying audience,
pricing and revenue model are not selected. Customer trust, repeat research,
accessibility, discoverability, dependable operations and sustainable costs apply
to every milestone. No new spending, contracts, external outreach, accounts,
payments, analytics tracking or materially changed access without required owner
approval. Sponsorship must be identifiable and separate from factual verification
and ranking. See `COMMERCIAL_READINESS.md` for evidence and unresolved decisions.

Keep the light/static architecture while it meets requirements. Final Prospectus
authority for completed static terms, explicitly provisional active disclosures,
source observation versus collection clocks, nulls, source evidence and correction
history remain mandatory. P4 is incomplete; P5/performance expansion remain gated.

## Current milestone — protect publication after source-policy changes

Rechecked on 17 September 2026 against main
`2e0e8541f92608ca71ab76a14232f6626ca43050`. Main, the five relevant open repair
PRs, canonical data and the deployed document-hold release are unchanged. Pages
[35283102313](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35283102313)
and automatic live acceptance
[35283136925](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35283136925)
succeeded for that checkpoint.

The next complete increment extracts the publication safeguard already developed
in #98 from draft integration #105, without releasing its unaccepted parser/data
changes. A collector could previously publish after the reviewed-correction
registry changed, or bypass verification with an empty supplied manifest. That
could reintroduce source values collected before a review decision, affecting all
public research views after publication.

Acceptance criteria: require an ancestor collector commit with identical scripts,
locked dependencies and correction registry; reject missing, empty, malformed or
stale supplied manifests before any data/proposal write; allow independent
accepted-data and documentation advances through the existing three-way merge;
preserve all canonical values, retained proposals and public projections.

Implementation is on `fix-current-publication-source-guard`, based on the main
checkpoint above. **983 Python regressions passed** with Python 3.12.14 and
`uv sync --frozen`, including real disposable Git histories and no-write CLI
failure checks. Strict validation has zero errors; seven Node tests and the public
release verifier pass. All 1,366 profiles and the compact directory rebuild
without changes, and the canonical dataset, 441 proposals and phase state remain
byte-identical. PR checks, merge and deployment evidence will be recorded before
this increment is marked released. See `PUBLICATION_SOURCE_GUARD.md` for the
recollection procedure; an old collector SHA must never be relabelled.

In parallel, local source integration `d8eed0555ff1480476a6d48347eec8e3e39b3f28`
incorporates main into #105's `54054c0e` head. The original seven-record transport
is still unavailable. New source reconstruction uses the exact current base and
retained PDF hashes, and is not accepted until its full source review and bounded
publication checks pass. No P4 completion or broader parser rollout is claimed.

## Previous milestone — document-scoped public review protection, released 17 September 2026

Reconciled at main `cf906df7ccc9bcf40881743b0af39480858a612e` on 17 September
2026. The earlier public trust/freshness milestone is already deployed and has
successful automatic live acceptance; it must not be rebuilt as new work.

Independent integration review reproduced a remaining boundary defect: a known
contradictory Final Prospectus could acquire `final_verified` use-of-proceeds
values before its canonical review snapshot existed if the source used a mirror
URL or a changed allocation fingerprint. Kaytex and SPEB retained CI examples
demonstrated this. The strict canonical correction guards deliberately preserve
concurrent values; the public projection needs its own document-level hold.

The bounded fix binds a public document review to the exact issuer, symbol,
opening date and field-proof PDF hash. Changing a URL or allocation does not
clear that review. A different document, issuer or offer cannot inherit the hold.
Existing value-scoped Emmvee, Teamtech and Unimech guards remain separate. Original
values, correction evidence and pending publication proposals stay intact.

Local acceptance: **966 Python regressions** in the frozen uv environment, **seven
Node quality tests**, source-bound/mirror/changed-value and null-state checks,
and the public release verifier all pass. All **1,366 profiles** and the compact
directory rebuild without output changes. Canonical data, all **441 retained
proposals**, phase state and the reviewed-corrections registry remain byte-for-byte
unchanged. The complete diff selects `presentation` publication.

The current visible values were already withheld or absent; this closes a future
re-extraction/mirror bypass and does not publish new numerical corrections.
[#106](https://github.com/Vasuki8/IPO-Tracker/pull/106) is merged and deployed.

| Release evidence | Verified result |
| --- | --- |
| Reviewed code | `d9001a0ed4e5d0e3926976d7158a85b333f34cfd` |
| PR validation | [35282355631](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35282355631): 966 regressions and strict validation passed |
| Browser acceptance | [35282355685](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35282355685): all 24 journeys and freshness text boundaries at 1440, 375 and 320 pixels passed |
| Merge | `fe053a4c6e79ca1d6fcfdc2ed5b6704a14993b12` |
| Pages deployment | [35282621904](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35282621904) deployed the merge successfully |
| Publication scope | [35282622791](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35282622791): selected `presentation`, skipped source/residual collection, passed validation/Node checks, and reported no accepted data changes to publish |
| Actual live acceptance | [35282660194](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35282660194): 1,366 profiles consistent and 17 complete HTTPS responses matched the deployed checkout; an independent local HTTPS run produced the identical receipt |

[The retained receipt](releases/2026-09-17-document-holds.json) includes exact input
hashes, observed results and limitations. The live GenXAI profile was inspected:
its allocation remains withheld with its source link and `Under review` label.
The browser artifact's direct download returned HTTP 403; its reported digest is
recorded without claiming a local ZIP verification. Browser job logs confirmed
all 24 journeys; no new mobile screenshot inspection is claimed.

## Preserved source integration and commercial work — 17 September 2026

[#105](https://github.com/Vasuki8/IPO-Tracker/pull/105) now contains the combined
#94/#98/#99 source repairs at `54054c0e05d44c03260ddc84950c82d0bf6172bd` (tree
`162b4291e6877ba84898b426d9d6bd5f0b592d0f`). The three original heads are parents;
their branches and original work remain intact. The temporary recovery workflow
was removed. **1,023 tests passed locally with Python 3.12 and `uv sync --frozen`**;
[GitHub validation 35281606697](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35281606697)
also passed. Source preview is separate and is not accepted data.

That integration remains a draft. The previously cited immutable seven-record
proposal and its publication transport could not be recovered from accessible
repository refs, prior work files or file inventory. Its recorded hash remains
evidence of the earlier handoff, not proof that the payload is available now.
Older one-record Emmvee artifacts are not substitutes. Merging the parser would
start broad repair collection, which exceeds the seven-record acceptance scope.
Do not merge until a fresh bounded acceptance/publication path is reviewed; never
relabel an old collector manifest. See
[the exact recovery handoff](reviews/2026-09-17-integration-recovery.md).

The commercial register now has readable primary NSE terms, copyright and data
usage policies, plus exact locked dependency/license inventory. Project-specific
collection, redistribution and display rights remain unresolved, including for
existing public use. No permissions, contracts, spending, outreach or telemetry
were activated. See `COMMERCIAL_READINESS.md` for primary sources and open items.

## Previous milestone — completed 17 September 2026, 22:01 UTC

**Public-release acceptance is complete.** This finishes the interrupted public
field-trust release, not a new canonical source repair or P4 closeout.

Problem: a green build or interrupted handoff did not establish that directory,
profile, comparison and CSV users received the intended trust-aware snapshot.
The progress record still said pre-release after PR #100 was already deployed.

Delivered in [#101](https://github.com/Vasuki8/IPO-Tracker/pull/101): a read-only
verifier checking every generated profile against directory identity, inventory,
held-field decisions, source references and subscription clocks/authority. It
compares complete served bytes for a bounded sample with an immutable deployment
checkout and retains pass/failure receipts. Existing browser CI includes the check.

The first Pages deployment did not start the downstream verifier: its filter used
only the display title. [#102](https://github.com/Vasuki8/IPO-Tracker/pull/102) added
the built-in `pages-build-deployment` workflow identifier. The subsequent automatic
live run below proves that correction worked. No permission expansion was needed.

| Release evidence | Observed result |
| --- | --- |
| #101 merge | `ff5a6f8f12516c1c22120cf9a1bcce08295f7999`, 21:54:37 UTC |
| #101 PR checks | Frozen validation `35278977727`, browser `35278977715` and loopback release acceptance `35278977897` passed |
| #101 deployment | Pages `35279249890` succeeded; no downstream verifier was created by the original filter |
| #102 merge | `02d3b1462f6a805d3d24a806c14a20eec93128ca`, 22:00:35 UTC |
| #102 PR checks | Validation `35279709716` and release acceptance `35279709696` passed |
| Corrected deployment | Pages `35279781264` successfully deployed `02d3b1462f6a805d3d24a806c14a20eec93128ca` |
| Actual live acceptance | Automatic run `35279827685` passed on its first attempt against `https://vasuki8.github.io/IPO-Tracker/`: 1,366 local profiles consistent and 17 complete HTTPS responses matched the deployed checkout |
| Retained evidence | `releases/2026-09-17-public-release.json` preserves the actual receipt and binding to artifact `10522650398`; downloaded ZIP SHA-256 `2207a3954ca0b2ad59b3566eef6faf7083f7d116ad33012eb3c7fb1e03ab04e0` was verified before inspection |

Verification included **957 local Python regressions**, **seven Node quality tests**,
**24 real-browser journeys**, and freshness text-boundary checks at **1440, 375 and
320 pixels**. Browser artifact `10522080734` was downloaded and hash-verified:
`a7c91182d91c0fe6b999e73a30ed43c8ef5807d8518ac949553b8a489acec382`. All 24 cases
passed; the mobile screenshot was inspected. GitHub ran the frozen environment;
local uv tests used available Python 3.13 because locked local installation/network
was unavailable. The local suite is not represented as a local frozen pass.

The live sample is the full directory and route manifest, eight shared assets and
seven profiles: Emmvee, Teamtech, Shakti Polytarp, Kheria, Vama Wovenfab, Sona and
Manika. Exact paths/hashes are in the receipt. Real HTTPS acceptance ran on GitHub's
runner, separately from loopback/browser acceptance. It is not an all-profile live
browser audit, a feed-freshness guarantee or a fresh PDF source review.

PRs #101/#102 changed only tests, workflows and documentation. They did not change
collectors, parsers, canonical data, retained proposals, public renderers, P4/P5 or
commercial entitlements. Read-only permissions, bounded retries, an eight-minute
job cap and fourteen-day workflow artifact retention remain. No new paid service,
tracking, contract, sponsorship or outreach was activated. See
`PUBLIC_RELEASE_ACCEPTANCE.md` for commands, limitations and recovery.

## What survived the failed response

[#100](https://github.com/Vasuki8/IPO-Tracker/pull/100) had already merged as
`bb2227c727597b7c75ff55c6dc88268860026c41` at 21:30:10 UTC. Its presentation publication
`2ec1b07edd54ecb16efad9c1364bdbd0790703b4` deployed in successful Pages run
`35277098551`. Downloaded artifact `10521465600` matched archive SHA-256
`e90c5076826605b9856a39d89686f90e574cd6f038c25883c31de05ce5f369bf`. Its code, data and
1,366 generated profiles were recovered and inspected rather than rebuilt as a
new feature. Public field decisions/withholding, observation/check clocks,
secondary labels, methodology, commercial readiness and presentation-only
publication were already implemented.

No previous Git checkout or unfinished patch was found in the accessible workspace.
The roadmap, earlier source-preview ZIPs and three screenshots were preserved.
Recovery used a new artifact-derived workspace, not a reset of another checkout.
Direct Git/network access failed; GitHub connector reads/writes and CI artifacts
were usable. The independent scheduled publisher then advanced main to
`e3ee0fe1d43efee3785743388523e1d408ce6008`; #101 was based on that newer tree and
preserved its data instead of overwriting it with the recovered older artifact.

The detailed pre-release note remains in this file's history at `2ec1b07...` and
`ff5a6f8...`. `ROADMAP.md` remains the owner's dated audit. Current repository and
deployment evidence take precedence over its old completion counts.

## Preserved unfinished work and current gate

- [#94](https://github.com/Vasuki8/IPO-Tracker/pull/94), `fix-p4-mixed-ofs-sellers`,
  head `4707df1e82337e3a7b8bac0838bbaa30c3d200be`: open and integrated into draft
  #105. The broad preview did not contain the intended Emmvee/Teamtech
  repairs and is not an accepted seven-record publication.
- [#98](https://github.com/Vasuki8/IPO-Tracker/pull/98),
  `fix-reviewed-correction-publication-guard`, head
  `d5e5d0580360a87dffc35b69e674886848b55005`: open, stacked on #94; protects source
  policy and supplied collector manifests. Integrated into draft #105.
- [#99](https://github.com/Vasuki8/IPO-Tracker/pull/99),
  `fix-kaytex-speb-document-holds`, head `a503531ded368c4eb53ba09cf5c2aafef3391c38`:
  open, stacked on #94 and integrated into draft #105; Kaytex/SPEB source holds and final-preview correction
  ordering. Preserve its reviewed proposal and manifest handoff.

These original branches were not overwritten or retargeted; their changes are
integrated in #105 but are not merged to main. The latest canonical
phase report inspected at `e3ee0fe1d43efee3785743388523e1d408ce6008` (21:40:41 UTC)
has **385 P4 plus 51 higher-priority actionable records**, **zero semantic errors**,
**1,614 blocking source-review items**, including **17 unmapped items**. P5 is
`waiting_for_p4`, with 914 queued records. This milestone did not resolve those
source items or alter the gate. Earlier 385+53/1,615/14 counts belong to the older
presentation artifact, not the newer canonical snapshot.

## Exact next task

Incorporate the released #106 public document holds into #105 and freeze the
combined code for explicitly targeted seven-record acceptance.
The original proposal is unavailable; any replacement needs a new source-reviewed
acceptance lineage, exact current data base, code manifest and content hashes.
Reproduce
Emmvee composition and Teamtech allocations with matching Final Prospectus proofs;
preserve the five continuing holds, Kaytex/SPEB safeguards, unaffected records and
proposal history. Recollect under the combined source policy, never relabel an old
collector manifest. Only source acceptance, reviewed data publication and deployed
profile verification complete that repair. Do not enable P5/performance meanwhile.

Retained-proposal triage, semantic-review routing, overdue-update detection,
lifecycle work and the remaining P4 evidence batches are unfinished. Commercial
source/document/hosting rights, customer validation, dependency/asset notices,
professional jurisdiction review, telemetry decisions and a restore rehearsal also
remain unresolved. No monetization activation has been authorized by these checks.
