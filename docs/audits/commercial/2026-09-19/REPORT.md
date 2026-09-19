# Commercial research receipt — 19 September 2026 UTC

Base: `11a62c47f64506fb3fbccdec8ba7f88e43d8c468`, fetched from current main before research. This sequential work follows the completed operational release (#149–151), universe audit and source repairs. No financial, inventory-admission or operational-writer work was repeated. Research conclusions and decision tables live in [COMMERCIAL_READINESS.md](../../../COMMERCIAL_READINESS.md).

## Scope and reproduction

[inventory.py](inventory.py) reads five exact files and installed locked package metadata, prints JSON and performs no network or canonical writes. It checks inputs against the base Git commit and fails if any changed. From the repository root on Windows with the locked environment:

```powershell
uv run --frozen python docs/audits/commercial/2026-09-19/inventory.py
```

Compare parsed JSON to [inventory.json](inventory.json); console newline encoding is not evidence of a content difference. Windows is necessary to reproduce the installed `tzdata` row. Use a new dated cohort after inputs/lockfile change, preserving this receipt. Its code is an offline research appendix, not another production inventory or data writer.

| Input | URL mentions | Scope |
| --- | ---: | --- |
| `data/ipos.json` | 19,149 | All string values, including historical proofs/notes; not accepted-value counts |
| `data/ipos-summary.json` | 470 | Public compact projection |
| `data/pending_updates.json` | 5,231 | Unresolved proposals and their evidence; never acceptance |
| `scripts/issuer_offer_registry.py` | 76 | String literals in Python syntax tree |
| `scripts/run_priority_subscriptions_v3.py` | 6 | String literals, including repeated configured links |

The union is **58 exact hostnames**. Hosts are not merged into corporate entities. Three sorted URL/pointer examples per host are included; all mention counts and file SHA-256/size evidence are retained. URL mentions are not unique documents, issuers, permissions or active feeds. This bounded inventory does not scan every repository file, remote artifact or commit in history, and therefore is not a complete rights audit of the repository.

Nine canonical secondary subscription labels at the base:

| Provider | Record IDs | Retained lifecycle |
| --- | --- | --- |
| IPO Premium | `vama-wovenfab-limited`, `shakti-polytarp-limited`, `injecto-polymers-limited`, `century-business-media-limited` | Closed |
| IPO Premium | `kheriaauto`, `axiomgas` | Open |
| IPO Dhamaka | `raksan-transformers-limited`, `om-galaxy-limited`, `maharaja-speedex-india-limited` | Closed |

Missing top-level source URLs remain null in the inventory; they are not invented from a label. Matching evidence URLs also exist in source/history arrays. Groww is configured and appears in Horizon research, but no current canonical subscription label names it. Inspect each field's evidence before inferring reproduction or authority from a host mention.

## Evidence carried and newly retrieved

The [previous register](previous-register.md) is an exact byte copy of the base commercial document. Its 17 September NSE, SEBI, GitHub Pages and direct-library evidence was still recent and was not redundantly refetched. All new checks in the current register are dated 19 September UTC; dates displayed by publishers are recorded separately. No acceptance button, account signup or gated residency confirmation was used, and no exchange/vendor was contacted.

New primary terms reviewed: IPO Premium terms/disclaimer dated 3 September; main-platform Groww terms dated 19 August; IPO Dhamaka terms dated 5 September; Orkla prospectus disclaimer; Sunshine website terms with raw displayed date `8-12-2025`; Integrated Registry disclaimer. Also inspected Om Galaxy, Shakti, Vama, Century, Raksan and Injecto issuer pages and Speedex merchandise terms. For pages without a located reuse grant, the outcome is **unverified**, not permission. All exact official URLs and relevant sections are in the current register.

Service research covered GitHub Actions additional terms/billing and privacy statement; Cloudflare self-serve, Developer Platform and Pages limits as an **unselected** candidate. No account, contract, purchase, migration or analytics was introduced. Python/uv/Playwright upstream licensing was reviewed; exact Poppler and browser/action bundle notices remain outstanding.

| Access attempt | Result / limit |
| --- | --- |
| `https://www.bseindia.com/static/about/disclaimer.aspx` | Research tool inaccessible; ordinary HTTP GET 403, access denied |
| `https://beta.bseindia.com/static/about/disclaimer.aspx` | Research tool inaccessible; ordinary HTTP GET 403, access denied |
| `https://marketdata.bseindia.com/` | HTTP 200; only application title `Self Data Feed`, no readable terms |
| `https://ipodhamaka.in/terms/` | Research tool failed; ordinary HTTP GET 200 recovered section 7; linked from subscription footer |
| `https://ipodhamaka.in/terms-and-conditions/` | Wrong candidate route returned 404; superseded by footer's `/terms/`, not treated as absent terms |
| `https://speedexind.com/` | Research tool failed; ordinary HTTP GET 200; footer led to `/terms-and-conditions/` |
| `https://gitlab.freedesktop.org/poppler/poppler/-/blob/master/COPYING` | Research-tool access failed; no exact Poppler artifact clearance inferred |

BSE denials were not bypassed. Search snippets and other companies' documents were not substituted for BSE's agreement. Unrelated Groww products' terms were not substituted for main-platform terms. Full third-party term text is not republished in this evidence packet; it retains links, locators and bounded paraphrases.

## Public distribution observation

Ordinary unauthenticated streaming GETs at approximately **2026-09-19T00:22Z** returned HTTP 200, `application/json; charset=utf-8`, and matching JSON-style prefixes for:

- [canonical JSON](https://vasuki8.github.io/IPO-Tracker/data/ipos.json)
- [pending proposals](https://vasuki8.github.io/IPO-Tracker/data/pending_updates.json)
- [compact public JSON](https://vasuki8.github.io/IPO-Tracker/data/ipos-summary.json)

These probes stopped after a small prefix and did not claim whole-file equality. They establish publicly reachable data routes, not authorization. Canonical JSON at the assessed commit is **27,618,770 bytes**; public-summary JSON is **1,303,236 bytes**; pending proposals are **12,256,367 bytes**. A hosting/publication review must include these routes, HTML-embedded profile data, generated CSVs, correction evidence, public Git history and workflow artifacts. This task changes none of those surfaces.

For the next rights-review packet, inspect `app.js` `exportCsv`, `scripts/build_company_pages.py` and the exact per-field proofs for the nine secondary subscription records, Orkla, Sunshine and Injecto's registrar-hosted evidence. Distinguish source links, factual values and copied excerpts. Propose an interim publication/retention policy for owner and qualified review; do not delete audit history or change access unilaterally.

## Software review boundaries

Eleven exact installed packages have notice file identities/hashes in the inventory. The prior Linux gap for Windows `tzdata 2026.4` is narrowed: LICENSE and LICENSE_APACHE exist; installed `zoneinfo/tzdata.zi` identifies 2026d and a public-domain input. Six transitive notice files were inspected, including certifi's Mozilla data notice and the PSF/historical notices in typing-extensions. This is not a complete operating-system/browser/action binary bill of materials or project-license decision.

No third-party fonts or code were added. No blanket project/data license was introduced. Project SVG provenance and exact redistributed-artifact notices remain open.

## Validation and handover

Validation evidence is recorded in PROJECT_STATUS and release metadata for the PR. Required local checks: reproduce inventory JSON; match previous-register bytes to base; strict validation to a temporary output; Markdown local-link checks; `git diff --check`; protected-data and public-output byte checks. Existing PR validation runs the full regression suite. No browser behavior changed, so a new browser-test implementation is unnecessary.

P4 is unchanged: **387 actionable + 63 higher-priority**, **1,552 blocking reviews** (1,556 total; four P5-only); **1,379 canonical records**, **441 retained proposals**; P5 waiting. This research removes no numerical/review blocker and establishes no new source permission.

Local results at 00:36 UTC: exact inventory reproduction, prior-register byte equality, hostname/provider counts, local document links and protected-file diff passed. Strict validation to `.cache/commercial-validation.json` found zero semantic errors and retained all 1,556 reviews. All 34 Node public-quality/source-health tests passed after an initial sandbox process-spawn denial; no assertion was weakened. `git diff --check` passed.

Owner decisions: operator/jurisdictions, interim rights policy, professional-review scope/budget, eventual authorized licensing/hosting outreach, initial customer cohort, code/asset license, support capacity, and later measurement. No spending, contract, outreach or material permission change was made.
