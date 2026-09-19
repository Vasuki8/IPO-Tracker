# Commercial publication scope — 19 September 2026

Assessment base: `1e86840856525db2ee2b436ed64f2b6e60374ee0` (release assessment after the scheduled filings publication).
Initial main was `4c5f1af5`; the scheduled update changed neither this cohort's evidence nor the P4 counts. Pointers/hashes were regenerated against the new main.
This completes the exact next commercial task from #152–153. Universe #162–163
and operational #164–165 were recognized as complete. No data repair was repeated.
The [previous register](previous-register.md) is preserved verbatim; current
decisions live in [COMMERCIAL_READINESS.md](../../../COMMERCIAL_READINESS.md).

## Problem, users and acceptance

The owner could identify restrictive sources but could not tell which retained
values, proofs and public surfaces they touched. That impedes a concrete review
of commercial publication policy and affects future customers who rely on stable,
lawfully supportable access. This work maps exposure; it makes no infringement,
permission or source-correctness determination.

Acceptance: bind a reproducible inventory and field/surface map to current main;
distinguish links, stored provenance, public values, held evidence and unresolved
proposals; keep missing URLs/clocks unknown; inspect accessible unresolved primary
terms and material runtime notices; preserve existing product/privacy/cost work;
test, merge, publish and verify the documentation with protected data unchanged.

## Inputs and reproducibility

[inventory.json](inventory.json) reuses the prior [inventory algorithm](../2026-09-19/inventory.py)
at this immutable base. It covers five named inputs, **61 hosts**, 19,382 canonical
URL mentions, 490 summary mentions, 5,231 pending-proposal mentions, 76 issuer-registry
and six subscription-collector mentions. These are string occurrences, including
history and embedded responses, not accepted facts or unique licensed sources.
The previous 58-host cohort is preserved. New hosts are `archives.nseindia.com`,
`bidcollection.nseindia.com` and `youtu.be`, inside retained NSE responses/history;
they do not establish a new YouTube collector. Eleven installed Python package
versions and notice hashes exactly match the previous inventory.

[exposure.json](exposure.json) binds canonical/summary/proposals, 13 generated
profiles, holds, phase, lockfile and projection/CSV code to base bytes. It records
JSON pointers, document hashes, evidence-text lengths/hashes and public field states
without copying excerpts or introducing source values. Seven exact host families
plus every canonical secondary subscription label select this bounded cohort.
All 1,404 canonical records are scanned for that selection; all 441 proposals are
scanned for cohort identity or host links. No fuzzy attribution is used.

From repository root, with the recorded base available in local Git history and
its named inputs unchanged:

```text
uv run --frozen python docs/audits/commercial/2026-09-19-publication-scope/inventory.py
uv run --frozen python docs/audits/commercial/2026-09-19-publication-scope/exposure.py
uv run --frozen python -m unittest discover -s tests -p test_commercial_publication_scope.py -v
```

Both scripts print JSON only. Changed input bytes fail closed; future cohorts
need a new dated appendix. Inventory package notices reflect the frozen Windows
environment; Linux may omit Windows-only tzdata. They are not a complete SBOM.

## Bounded issuer and publication map

Status is the stored issue status at the assessment base, not a newly observed
source lifecycle. History counts below are rows in generated profile payloads.
Proposals are unresolved, never counted as accepted provenance.

| Issuer ID | Relevant binding | Public profile history rows | Related proposals | Public/static distinction |
| --- | --- | ---: | ---: | --- |
| vama-wovenfab-limited | IPO Premium subscription; closed | 12 | 5 | Category values and summary total; top-level source URL missing |
| shakti-polytarp-limited | IPO Premium subscription; closed | 13 | 8 | Same scope; source URL missing |
| injecto-polymers-limited | IPO Premium; Integrated Registry links; closed | 9 | 2 | Subscription values; missing top-level URL. Registrar document/extraction links do not bind all static fields |
| century-business-media-limited | IPO Premium subscription; closed | 9 | 3 | Category values and summary total; source URL missing |
| raksan-transformers-limited | IPO Dhamaka subscription; closed | 1 | 1 | Category values and summary total; source URL missing |
| om-galaxy-limited | IPO Dhamaka subscription; closed | 1 | 3 | Same scope; source URL missing |
| maharaja-speedex-india-limited | IPO Dhamaka subscription; closed | 1 | 0 | Same scope; source URL missing |
| kheriaauto | IPO Premium subscription; open | 7 | 4 | Category values and summary total; stored subscription endpoint URL |
| axiomgas | IPO Premium subscription; open | 3 | 0 | Same scope; provisional official offer terms remain a separate source/rights question |
| orklaindia | Ten issuer-hosted static field proofs | — | 0 | All ten profile values present/final_verified; retained proof evidence and correction history also public in raw canonical data |
| sunshine | Eleven issuer-hosted static field proofs | — | 4 | Ten profile values present/final_verified; financials held under_review while raw financial proof remains retained |
| lumino | IPO Watch source reference | — | 0 | One canonical and one profile link; no direct static proof binding to this host |
| steamhouse | IPO Central source and VerifiedTerms observation | — | 4 | Two canonical references, one profile link; no direct static proof binding to this host |

Totals: **nine secondary value records, 56 public subscription-history rows,
21 issuer-hosted static proof bindings, 20 corresponding profile values and
34 related proposals**. All nine secondary totals exist in the compact summary;
seven top-level source URLs remain unknown. History links must not fill those gaps.

The shared ten Orkla/Sunshine proof fields are price band, lot size, lead managers,
registrar, promoters, listing issue price, issue composition, issue size, fresh
issue and OFS. Sunshine additionally has financials. Current Orkla extraction
metadata points to SEBI, but the retained static proofs still point to the issuer;
one link cannot substitute for another rights holder's permission. Injecto's four
registrar-host URL occurrences are references/document/extraction metadata. Its
current offer extraction uses the issuer host. No registrar-wide attribution or
license is inferred.

| Surface | Checked behavior / review boundary |
| --- | --- |
| Canonical JSON | Current selected records retain values, proofs, response/extraction metadata, subscription and correction history. Evidence strings are indexed by pointer/hash, including table headers/rows; they are not republished in this report |
| Pending JSON | 34 of 441 entries selected by exact cohort identity or provider links; paths/status/fingerprint/run retained. Public availability is separate from acceptance |
| Directory and comparison | Compact summary plus shared public-quality rules; secondary totals remain reported, held static values remain gated |
| Company profiles | Embedded `ipo-profile-data` values, provenance links and 56 history rows examined; UI rendering depends on existing shared quality rules |
| CSV | `app.js::exportCsv` uses filtered sanitized summary and `IPOQuality.snapshot`: selected price/lot/issue-size values, subscription total, clocks, source/authority and evidence-state columns. It has no full financial tables, proof excerpts or full subscription history |
| Repository/history/artifacts | Public repository contains retained evidence. Historical commits and all remote workflow artifacts were **not exhaustively enumerated**; UI holds cannot restrict those surfaces |

This is a static committed-artifact/code review, not an executed CSV capture or a
new browser behavior release. Prior unauthenticated live raw-data checks remain
dated evidence; deployment verification below checks the delivered release.

## Primary research delta and limits

The [primary receipt](primary-evidence.json) and [news-source terms](secondary-terms.json) retain URLs, check dates, locators,
available response hashes and a bounded CI-log receipt. Full terms are not copied.
The register contains the source-by-source interpretation and decision table.

- BSE's public interactive Legal route exposed no documents. Disclaimer access
  still failed. No registration, geographic assertion, paid plan or agreement was
  entered. Applicable IPO product rights, attribution and exports remain unknown.
- IPO Watch and IPO Central terms recovered; Economic Times, Moneycontrol,
  Business Standard and Mint terms reviewed against actual retained references.
  These references do not by themselves prove copied original content or accepted
  numerical provenance. Remaining smaller news/broker/issuer hosts stay unverified.
- NSE, SEBI, IPO Premium, IPO Dhamaka, Groww, issuer/registrar terms, Pages/Actions
  and the unselected Cloudflare alternative were already checked 17–19 September;
  those dates are carried, not refreshed. Current raw canonical size is 27,830,228
  bytes, still above the previously recorded candidate's 25 MiB asset limit.
- Actual collector logs identify Poppler/libpoppler134 24.02.0-1ubuntu9.9 and
  poppler-data 0.4.12-1; their matching Ubuntu copyright notices are now recorded.
  Playwright and five Actions top-level notices were checked. Chromium binaries,
  every bundled/transitive notice and SVG origins remain open. No blanket software
  or generated-data licensing conclusion follows.

## Ready-to-review owner packet

Known: exact bounded material/surfaces and source restrictions. Uncertain:
project entitlements, facts versus protected expression/compilation, territorial
scope, applicable exceptions and all historical-artifact exposure. Commercial
clearance remains blocked; no current publication policy is silently endorsed.

Owner identifies operator, jurisdictions and review owner. Professional review
should answer, per source: permitted collection route; factual extraction versus
excerpts; free/paid display; raw JSON/CSV/team exports; alerts; required attribution;
history/termination; and lawful evidence retention. Decide whether the interim
boundary requires permitted-link-only output, particular fields/surfaces to be
restricted, or documented licensed publication. These are choices for review,
not approved actions. A display hold alone would not implement an access policy.
Any restriction needs a separate bounded plan, acceptance checks and owner approval;
no historical evidence deletion is proposed.

The existing four customer hypotheses, recurring tasks, free/paid possibilities,
privacy-conscious event/retention proposal, cost categories and correction/incident
process remain in the register. They are hypotheses, not validated demand or pricing.
No analytics, accounts, billing, ads, contacts, contracts, spend or hosting changes.

## Validation, release and next task

Seven focused audit tests cover exact hosts, hostile lookalikes, pointer escaping,
source-link versus field-proof attribution, missing clocks/URLs, zero versus null,
held evidence, profile identity and duplicate payload rejection. Both JSON outputs
were reproduced from current base bytes. Strict validation passed with zero errors;
38 Node regressions passed. [PR #166](https://github.com/Vasuki8/IPO-Tracker/pull/166)
merged research commit `de09c162cae491ce2f0dae16f21349d9a14091aa` as
`3481d89a21e77ac1f302bdc9171dd8eb5b67ee4a`. PR validation **35423499597** passed
all **1,354 Python tests**; main validation **35423605159**, Pages **35423604707**
and public release verification **35423628525** succeeded. [27 direct checks](live-delivery.json)
matched live bytes to that merge, including raw files and all 13 mapped profiles.
The [release receipt](release.json) describes the research merge before this
documentation closeout. No product behavior or canonical values changed.
P4 remains **408 actionable + 67 higher priority; 1,553 blocking / 1,557 total
reviews; zero errors/unmapped**. No source correctness or blocker reduction claim.

Exact next commercial task: owner-directed professional review of the completed
packet and interim publication policy. Independent next research cohort is
broker/lead-manager and small-news material in the inventory, starting with
`www.ipoplatform.com`, `www.equentis.com`, `www.idbidirect.in`, `www.plindia.com`
and `ipobarta.ai`: map stored material first, then inspect applicable public terms.
BSE agreement recovery, runtime bundled notices and SVG provenance remain open.
Do not repeat this 13-issuer mapping unless its bound inputs change.
