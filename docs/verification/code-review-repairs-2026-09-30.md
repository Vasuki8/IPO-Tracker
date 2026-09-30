# Code review repairs — 2026-09-30

This batch addresses the nine findings from the repository review at baseline
`ad3c825bbb98216942f72dd71d3767b184256b6c`. Changes are prepared locally;
merge, GitHub Actions execution, Pages deployment and served-data verification
remain pending. It does not close or replay the historical SSEK release.

## Behavior repaired

- Successful, same-repository, main-branch source-writer completions can trigger
  Pages through `workflow_run`, including updates pushed with `GITHUB_TOKEN`.
  Deployment checks out `main` and records the actual uploaded commit. PR,
  foreign-repository and unsuccessful completions cannot run the deployment
  job or join its cancellation group.
- DRHP served-data verification runs after deployment, removing the dependency
  cycle in which collection had to verify deployment before triggering it.
  Deployment retains the fetched IPO/DRHP bytes and verification reports.
- Publication health requires successful deployment and served-data verification;
  a failed or missing verification preserves the previous successful publication.
- BSE enrichment compares retained fields and NSE `terms`, preserves the earlier
  official candidate and its evidence, and retains competing observations with
  conflict status. Corroborating disclosures and reruns preserve provenance.
- Concurrent creation of a year manifest merges noncolliding stable IDs rather
  than silently discarding the proposed records. Same-ID disagreements preserve
  current data and report a conflict.
- Closed IPOs advance to listed when a retained, verified NSE listing date has
  elapsed. Earlier status evidence is retained; live feeds cannot demote listed
  records. Promotion also runs when a listing date is first extracted. Evidence
  URLs must be HTTPS, on the approved NSE host and without user information.
- Published-data validation enforces the assertions in the local JSON schema
  before semantic checks. It rejects absent required fields, invalid board values,
  empty evidence objects, malformed dates, wrong types and unexpected properties
  without crashing on malformed record shapes. The schema explicitly recognizes
  the existing standard, retained-replacement and unresolved-conflict histories.
- Newest-first sorting reaches close-date, listing-date and name fallbacks when
  earlier dates are absent. Keyboard skip-to-content focuses the main content
  without leaving IPO details. Updated script URLs invalidate older asset caches.
- BSE PR validation uses a concurrency group separate from production backfills.

## Retained-data repair

The fixed lifecycle helper was applied offline as of **2026-09-30 14:37:04 UTC**
to the 2026 recovery manifest. Exactly five records advanced from closed to listed:

- Adroit Industries India Limited
- Armee Infotech Limited
- Elevate Campuses Limited
- Sonaselection India Limited
- Varmora Granito Limited

This is lifecycle advancement from existing verified dates, not a new observation
that trading began. No source was refetched. Existing source collection clocks,
listing dates, terms and earlier status evidence were preserved. The generated
dataset still has **1,387 records**; the other **1,382 public objects** are unchanged.
Only these five status/evidence projections and the generation timestamp changed.
Public-past-issues evidence does not claim the unrelated ipo-detail JSON locator.

## Validation

Each behavioral regression failed against the old behavior before its repair.
Coverage was added to the existing BSE extraction, semantic publication, NSE
listing, live-feed, ordering, browser and publication-health tests. New workflow
and schema tests are registered in `validate-data.yml`.

All **101 test scripts passed**, including the desktop/mobile browser suite and
**17 malformed-dataset rejection cases**. JavaScript syntax checks passed for
**207 files**; changed workflow YAML and **76 shell steps** passed syntax checks.
Published recovery consistency, operator state and independent JSON Schema
validation also passed. Browser checks use Playwright 1.56.1 with the cloud machine's
Chromium 151; CI installs the pinned Playwright browser build.

The GitHub trigger, trust and concurrency contracts are validated locally;
no production workflow, remote collection, push or deployment was executed.
After merging, verify the first collector-triggered deployment and inspect its
retained served-data reports before treating publication as live-verified.
