# Completed release workflow retirement — 2026-09-28

This repository-hygiene change removes production write/replay capability from completed one-shot historical release workflows while preserving their evidence, importer code, tests, manifests, and Git history.

## Retired workflow surfaces

- `materialize-bse-2020-unmatched-evidence.yml`
- `materialize-bse-2021-mainboard-batch1-evidence.yml`
- `materialize-bse-audit-conflict-evidence.yml`
- `materialize-fabino-listing-evidence.yml`
- `materialize-historical-ipo-evidence.yml`
- `publish-bse-2021-sme-pair.yml`
- `publish-reviewed-bse-2021-batch2-nureca.yml`
- `publish-reviewed-bse-2021-batch3-paras.yml`
- `publish-reviewed-bse-2021-final-pair.yml`
- `publish-reviewed-bse-2021-getalong-svrl.yml`
- `publish-reviewed-bse-2021-hp-nuvoco.yml`
- `publish-reviewed-bse-2021-jetmall-brandbucket.yml`
- `publish-reviewed-bse-2021-mainboard-batch1.yml`
- `publish-reviewed-bse-2022-eighty-virtuoso.yml`
- `publish-reviewed-bse-2022-final-pair.yml`
- `publish-reviewed-bse-2022-hariom-rainbow.yml`
- `publish-reviewed-bse-2022-maagh-technopack.yml`
- `publish-reviewed-bse-2022-maruti-olatech.yml`
- `publish-reviewed-bse-2022-pace-gargi.yml`
- `publish-reviewed-bse-2022-tmb-dcx.yml`
- `publish-reviewed-bse-2022-veranda-uma.yml`
- `publish-reviewed-bse-2023-four.yml`
- `publish-reviewed-bse-2023-rvpe.yml`
- `publish-reviewed-bse-reconciliation.yml`
- `publish-reviewed-fabino.yml`
- `publish-reviewed-historical-ipos.yml`
- `publish-reviewed-bse-2020-unmatched.yml`
- `verify-reviewed-bse-reconciliation-publication.yml`
- `verify-reviewed-fabino-publication.yml`
- `verify-reviewed-historical-ipo-publication.yml`

These workflow files are removed from current `main`; their historical definitions remain available in Git history. No historical evidence JSON, importer script, correction history, public IPO record, or recovery record is deleted.

## Replacement validation

`.github/workflows/validate-completed-releases.yml` is read-only and re-runs the retained historical evidence/release contract tests plus `build-published-data.mjs --check` and `validate-data.mjs`.

`scripts/test-completed-release-workflow-retirement.mjs` prevents the retired workflow filenames from being reintroduced and restricts production-write workflow capability to the explicit active operational allowlist:

- `backfill-bse-sme-addition-notices.yml`
- `backfill-historical-offer-dates.yml`
- `backfill-historical-pdf-fields.yml`
- `deploy-pages.yml`
- `update-drhp.yml`
- `update-ipos.yml`

The completed 2020 validator and three orphaned publication verifiers were later consolidated into the same read-only validation surface. Their verifier scripts and tests remain in the repository; only redundant workflow entry points were removed.

## Boundaries

This change does not alter IPO data, evidence semantics, source precedence, collection cadence, publication data, Pages content, or the active P1 2023 review. It does not delete branches. It only removes stale production-write entry points for releases that are already complete.
