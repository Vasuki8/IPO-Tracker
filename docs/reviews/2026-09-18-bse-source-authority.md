# BSE beta-host authority review — 18 September 2026

## Decision and scope

Add only the exact `beta.bseindia.com` HTTPS host to the existing official-exchange
source classification in Python and JavaScript. This is a source-host decision,
not verification of a particular issuer, bid multiple, final subscription, source
observation time or commercial redistribution permission. Do not change canonical
values, source/proof/collection clocks, review holds or retained proposals.

## Current primary evidence

The read-only inspection in run
[35369321624](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35369321624) passed at
`2026-09-18T16:35:11.473472+00:00`, from head
`674332cf741d2631faafbff3dccfc3462a9d38ce` and actual test checkout
`13780f13e95699b9373e8555a97ff0773020878f`. The downloaded artifact 10557865271 has
SHA-256 `85ff77abf657d652191e8df3b915d1c54cb62b1a9cc3a3868e8328ce57d9d750`;
its ZIP checksum was verified before interpreting the evidence.

1. BSE's [primary homepage](https://www.bseindia.com/) served HTTP 200 and directly
   referenced its own application bundle below. The complete response was 14,287
   bytes, SHA-256 `b534273e5f5247a718f3e46dbe848a7869809cb27ebb889cd1f1548d701e0dda`.
2. The referenced [BSE application bundle](https://www.bseindia.com/assets/includenew/js/main-X4YRFL25.js)
   served HTTP 200 without redirect: 882,820 bytes, SHA-256
   `648a7c72ca66a8d883cfe7fcf5c2aab7eca57600b11c09e450da753d74ee8f3b`.
   Its navigation contains explicit `href` destinations
   `https://beta.bseindia.com/register/AuditorRegisteration.aspx` and
   `https://beta.bseindia.com/register/SystemAuditorRegistration.aspx`.
   These registration links establish BSE's use of the exact beta host; they are
   not IPO evidence and the registration forms were not visited or submitted.
3. The [beta public-issue index](https://beta.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p)
   independently served HTTP 200, title `IPOs Listing|New Live Public Issues on BSE`,
   33,492 bytes, SHA-256
   `7842fe1ac102c322df80b06fd9a279a7dc81e321d44f08f16b59778ba9bcdb43`.
   It contained the public-issue links used by the existing BSE route. This check
   does not adjudicate every linked issue or its underlying figures.

The first inspection [35368979901](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35368979901)
correctly returned `needs_review`: the primary homepage is an application shell,
not a rendered navigation page. Retained artifact 10557334032 has verified ZIP
SHA-256 `0e9a0240564eebeae7e059fa2729d244a2c8299aa2ba14f4ba60d69b8339f07b`.
The follow-up inspected only directly referenced, exact-host BSE main bundles;
it did not assume a beta title alone proves the relationship. The web reader
returned 403; successful HTTPS inspection is from the recorded GitHub runner.
No full page, application bundle or PDF is republished by this change.

## Implementation and acceptance boundary

Both classifiers use literal, exact HTTPS authorities. Credentials, encoded or
Unicode host aliases, suffix/path lookalikes, backslashes, whitespace and nonstandard
ports cannot acquire an official badge through browser URL normalization. Existing
explicit secondary labels override an official hostname. Unknown source-observation
times stay unknown, and collection times never become observation times.

Ten new tests exercise shared Python/Node behavior, real retained beta snapshots,
zero/null/clock preservation, bounded source inspection and publication mode.
A dedicated real-browser check covers directory, CSV, comparison and profiles at
1440/375/320 pixels alongside the existing journeys. The only writer remains the
existing presentation-only publisher; the new evidence job is read-only and PR-only.
Mixed collector/data/lock changes do not use this presentation shortcut.

The local rebuild against automatic publication `eec88efb` changed only
`subscriptionAuthority` in seven projected records: heromotors, jsipl, ssretail,
nse, sona, manika and veegaland. Five have current direct snapshot URLs and two
use already-bound historical metadata under the unchanged fallback rules. All
seven source times remain unknown. Canonical data, all 441 proposals, holds and
phase/queue/validation files were byte-identical. The subsequent automatic filings
publication `248cbaf2` is preserved in this PR's integration, not counted as our work.

Local focused uv tests and eight Node tests pass. Local full-suite execution ran
1,154 tests but hit eight missing-workflow-file errors in the Pages mirror; frozen
offline sync lacked locked packages. Those attempts are not full/frozen passes.
Require complete-repository frozen CI, actual browser results, presentation-only
publication and live acceptance before declaring this repair deployed.

Commercial source rights, customer segment, pricing and privacy decisions remain
unresolved. No spending, contracts, outreach, tracking, billing or material access
changes. P4 and source-review dependencies are unchanged; Teamtech stays held,
Emmvee is not re-held, and broad draft #105 remains unaccepted.
