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

## Current milestone — completed 17 September 2026, 22:01 UTC

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
  head `4707df1e82337e3a7b8bac0838bbaa30c3d200be`: open and currently not mergeable
  against main. The broad preview did not contain the intended Emmvee/Teamtech
  repairs and is not an accepted seven-record publication.
- [#98](https://github.com/Vasuki8/IPO-Tracker/pull/98),
  `fix-reviewed-correction-publication-guard`, head
  `d5e5d0580360a87dffc35b69e674886848b55005`: open, stacked on #94; protects source
  policy and supplied collector manifests. Not integrated by this milestone.
- [#99](https://github.com/Vasuki8/IPO-Tracker/pull/99),
  `fix-kaytex-speb-document-holds`, head `a503531ded368c4eb53ba09cf5c2aafef3391c38`:
  open, stacked on #94; Kaytex/SPEB source holds and final-preview correction
  ordering. Preserve its reviewed proposal and manifest handoff.

These branches were not overwritten, retargeted or merged. The latest canonical
phase report inspected at `e3ee0fe1d43efee3785743388523e1d408ce6008` (21:40:41 UTC)
has **385 P4 plus 51 higher-priority actionable records**, **zero semantic errors**,
**1,614 blocking source-review items**, including **17 unmapped items**. P5 is
`waiting_for_p4`, with 914 queued records. This milestone did not resolve those
source items or alter the gate. Earlier 385+53/1,615/14 counts belong to the older
presentation artifact, not the newer canonical snapshot.

## Exact next task

Reconcile #94 with current main while preserving #100's public trust boundary and
#101/#102's release checks. Integrate #98 and #99 on the repair branch, then freeze
the combined code for explicitly targeted seven-record acceptance. Reproduce
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
