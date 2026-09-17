# Project status and release evidence

## Standing product direction

IPO Tracker is intended to become a public commercial product. The paying audience, pricing and revenue model are not selected. Customer trust, repeat research, accessibility, discoverability, dependable operations and sustainable costs apply to every milestone. Do not add spending, contracts, outreach, accounts, payments, analytics tracking or materially changed access without the required owner approval. Sponsorship must be identifiable and separate from factual verification/ranking. See `COMMERCIAL_READINESS.md` for evidence and unresolved decisions.

Keep the existing light/static architecture while it meets requirements. Final Prospectus authority for completed static terms and the existing P4 correctness gate are unchanged. P5/performance expansion remain gated; presentation work does not close canonical gaps.

## Reconciled baseline — 17 September 2026

Current upstream main was verified as `cc30f3701996232aa0eecd1b8c4adbf710c84735`; tree `3f0396594e446d6abc9d9c63867b1557f4828a0c`. GitHub reports the Pages deployment successful in [run 35258451293](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35258451293), completed at 18:23 UTC. The downloaded Pages artifact was `10513224480`, archive digest `sha256:225c4c3510f8fdf277b92981c071927ab074d28d92e34dd11aa6a452ee210770`; its source files and generated outputs were inspected. Current code and deployment evidence take precedence over earlier chat claims.

The published report snapshot still contains 1,366 records, 385 P4 actionable records plus 53 higher-priority records, 1,619 semantic review items (1,615 blocking and 14 unmapped), and 441 retained proposals. P5 remains `waiting_for_p4`, with 913 queued records. These are the last published report numbers, not a newly collected market snapshot or a claim that each stored record is verified. Rolling date-based counts must be recalculated on the exact next canonical publication.

Already delivered and retained: light dashboard, stable company URLs, quick view, comparison, local watchlist, calendar, CSV, compact public payloads, full queue retention, semantic validation, source evidence, isolated browser CI and serialized publication. Do not rebuild these as new features.

Unmerged repair work preserved:

- [#94](https://github.com/Vasuki8/IPO-Tracker/pull/94), `fix-p4-mixed-ofs-sellers`, head `4707df1e82337e3a7b8bac0838bbaa30c3d200be`: parser/source-review work, not a published seven-record acceptance. The green source preview did not contain the intended Emmvee and Teamtech repairs. Do not promote that broad preview wholesale. Five other allocations remain held pending evidence.
- [#98](https://github.com/Vasuki8/IPO-Tracker/pull/98), `fix-reviewed-correction-publication-guard`, head `d5e5d0580360a87dffc35b69e674886848b55005`: green publication-policy and manifest safeguards stacked on #94; not merged into main. This milestone does not retarget, overwrite or bypass it.

## Earliest unmet milestone: public field trust

Problem: source reviews/quarantines and distinct subscription clocks did not consistently survive public projection. An exchange agreement badge could coexist with contradictory public figures. Affected users: directory researchers, profile readers, comparison users and CSV consumers, including narrow mobile screens.

Acceptance: the same field-level decisions and withholding across all four public surfaces; explicit source/check clocks and secondary authority; no canonical/proposal/gate mutation; no unsanitized master-data fallback; retained existing navigation, watchlist, comparison and mobile behavior; frozen CI plus browser checks before merge; generated-page and deployed-artifact verification before claiming publication.

Implemented on `feat-public-field-trust` (PR/release evidence to be recorded after actual creation):

- Pure `scripts/public_quality.py` projects field decisions without mutating canonical records. Source/value-bound temporary holds contain the seven reviewed #94 defects without pretending to correct them or blocking a later changed source/value automatically.
- Final verified static fields require matching value, Final Prospectus classification, issue date, document hash and physical source evidence. A selected active bidding term can be provisional only when it matches an issue-bound official exchange observation. Attached documents alone do not prove a field. Provisional permissions expire after close in IST; the browser rechecks cached decisions on rendering.
- Contradictory composition groups and quarantined/reviewed fields are withheld. Derived amounts/returns cannot reuse held inputs. Bid lot, market lot, minimum bid quantity and one-lot-at-cap remain distinct; minimum application is not inferred.
- Shared browser quality labels, field/source explanations and an explicit `methodology.html` page. No whole-record verification claim. Legacy payloads fail closed; the normal browser does not fall back to `data/ipos.json`.
- Source observation and collection clocks remain separate. Current accepted subscriptions cannot borrow a newer history value or a different source URL. Secondary providers remain visible on mobile; unknown time remains unknown.
- The existing single serialized publisher gains a presentation-only rebuild path. Pure presentation pushes can rebuild from current accepted main without source collection, correction application, proposal reconciliation or phase-state writes. Mixed/unknown source changes remain normal repair mode. No second data writer is introduced.

Local verification completed: 949 Python regressions (930 baseline plus 19 new), seven Node contract/renderer tests, JavaScript syntax checks, generation of all 1,366 routes and an idempotent second build with all routes unchanged. Canonical `data/ipos.json`, `data/pending_updates.json` and `data/phase_status.json` remain byte-for-byte unchanged. The selected production fixture preserves exact affected values/hash bindings; it is not a fresh PDF source acceptance.

Local environment limitation: `uv run --no-project --python /opt/pyvenv/bin/python` used the available Python 3.13 / pypdf 5.9 runtime, not the locked Python 3.12 environment. Full frozen GitHub CI is therefore required. Local Chromium navigation failed with `net::ERR_BLOCKED_BY_ADMINISTRATOR` before reaching localhost; no local browser pass is claimed. The existing browser workflow rebuilds the new projections and runs 24 checks in its supported runner. CI outcome is pending until observed.

Public payload tradeoff measured locally: directory JSON grows from 570,254 to 1,293,859 bytes to carry per-field decisions and deduplicated source references, while remaining about 4.8% of the 26,758,638-byte canonical master. This is a correctness cost, not a speed improvement claim. No real-user measurements were collected.

## Release status

This status entry accompanies the implementation before release. Do not infer merge or deployment from code generation, test definitions or a green source preview. Record the actual PR head, frozen/browser outcomes, merge commit, presentation publication commit and Pages artifact verification here when available.

## Next concrete action and remaining blockers

After public-display acceptance, complete #94's current-base, explicitly targeted seven-record source acceptance: corrected Emmvee composition and Teamtech allocations with matching proofs, the five continuing holds, exact unaffected-record preservation, then reviewed publication and live generated-page verification. Integrate #98 without bypassing its dependency. Next, triage retained proposals and route every semantic review into actionable work. P4 closure still requires the existing runtime gate; performance/P5 expansion remain disabled while it is blocked.

Commercial permissions, actual customer validation, hosting suitability, exact dependency/asset notices, professional jurisdiction review, telemetry decisions, overdue-source monitoring and a restore rehearsal remain unresolved. No paid feature, contract, external outreach or measurement collection was activated.
