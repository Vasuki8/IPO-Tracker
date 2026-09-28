# Retirement review: PR #196 and PR #246

Reviewed on 2026-09-28 against main **9a544996475e84788a7cc08fc6e49d9acd8b52bb**. Both PRs were closed **unmerged**, with their original descriptions preserved and the disposition appended. No production delta needed porting. Branches and historical evidence were retained; no stale branch was merged, rebased, force-pushed or executed.

| PR | Reviewed head | Divergence from reviewed main | Disposition |
| --- | --- | --- | --- |
| [#196](https://github.com/Vasuki8/IPO-Tracker/pull/196) | `5a3f7fdf7dfdb0bd0c2ebf29eca3f905abb3c02b` | 4 ahead / 684 behind | Superseded by merged #198 and #199; closed 2026-09-28T14:24:28Z |
| [#246](https://github.com/Vasuki8/IPO-Tracker/pull/246) | `e7933aaccbfe21a3d215e93609efb5c90064466d` | 3 ahead / 331 behind | Obsolete temporary workflows; closed 2026-09-28T14:24:35Z |

The user's earlier 678/325 behind counts had advanced by six commits. Merge bases remain `fd06045ac437636bc5d0c8dba087397ad4897c28` and `a1f15e89959bebeff4ad4ed3c020fa62938afe18`, respectively. Divergence alone does not prove a regression: the decision below compares all seven changed files and current behavior.

## PR #196: all four files compared semantically

All four Git blobs differ from main. File presence or hash equality was not used as a substitute for semantic review.

| Changed file | Comparison and decision |
| --- | --- |
| `.github/workflows/verify-bse-listing-candidates.yml` | Main already contains every batch17 addition: PR/push path triggers, issuer-specific verification, PDF retry, evidence-format report and summary. Main additionally retains batches18–21. Port nothing; preserve the later workflow. |
| `data/discovery/bse-listing-candidates-2026-09-24-batch17.json` | All four candidate objects are deeply equal, including exact identity, BSE code, notice/date/URL and source-text hash. Main replaces the redundant parser-version field with repair run `36028598993`, commit `61453efd680289a57ecc889a0070aa894624df77` and original cursor time; the selection text still identifies parser-v1.3 and requires issuer-specific verification before materialization. Port nothing. |
| `data/discovery/bse-listing-reconciliation-2026-09-24-cursor5-repaired.json` | Identical four entries after removing only the repeated `index_notice_subject`; identical classifications and counts. Main preserves the public/2024 snapshot identities and adds repair-run/commit/artifact/hash provenance and next cursor. PR-only snapshot metadata is historical, not a current import queue; retain it in the review receipt below without replacing the committed reconciliation. |
| `data/verified-bse-listings/2026-09-24-batch22.json` | Identical issuer identities, codes, board, evidence kind, URLs, document identities, publication dates, notice numbers and all 12 fact/value/source-value objects. Actual observation provenance differs: runs, artifact digests, raw-response hashes, normalized excerpts/hashes and collection clocks. Keep main's later approved evidence. Both manifests pass the current strict validator, but only main matches current retained record hashes. |

Main's batch22 came through [#198](https://github.com/Vasuki8/IPO-Tracker/pull/198), merge `4ef610e72568efc77027c87e33aefee7cecc8197`, with manifest commit `c625fde70b9b1420eb2b2954d447115215315064`. Read-only publication verification followed in [#199](https://github.com/Vasuki8/IPO-Tracker/pull/199), merge `7e173197e0864c415a59845200af3abb9ac78821`.

| Evidence observation | PR #196 | Retained main |
| --- | --- | --- |
| Run | `36028952078` | `36035011920` |
| Artifact | `10820049317` | `10824950566` |
| Artifact SHA-256 | `3a0b791cf52898289bbfc42dcd05c05e93ac7abe1b757f61b0527c26360734b2` | `10f39b08c821c4f08c37571f2d6435d3542875feede46a646a1bf4425f5089e4` |
| Collection interval, UTC | 2026-09-24 16:44:43.463–16:44:44.719 | 2026-09-24 17:35:29.007–17:35:30.543 |

These are separate observations of the same supported facts, not byte-identical evidence. Do not relabel or mix their hashes and clocks. No raw official notice was freshly fetched for this retirement review.

| Issuer | BSE code | Listing date | Market lot | Issue price, INR |
| --- | --- | --- | ---: | ---: |
| NISUS FINANCE SERVICES CO LIMITED | 544296 | 2024-12-11 | 800 | 180 |
| Rajesh Power Services Limited. | 544291 | 2024-12-02 | 400 | 335 |
| Aelea Commodities Limited | 544213 | 2024-07-22 | 1200 | 95 |
| Three M Paper Boards Ltd | 544214 | 2024-07-22 | 2000 | 69 |

Each issuer is present exactly once in all-year retained recovery and exactly once in the public projection, with main's later source-run binding and all three values intact. Price band, issue size, minimum bid, minimum application amount and offer open/close dates remain null for these four records.

An in-memory application to all seven current recovery years proves the replay distinction: main batch22 produces **0 added / 4 already present / 0 holds**; PR batch22 produces **0 added / 4 existing-record holds / 0 identity conflicts**. Both leave recovery deeply unchanged. This is the current no-overwrite safeguard doing its job; replacing hashes or weakening that guard to make the stale manifest apply would be a regression. See [the comparison receipt](stale-pr-review-2026-09-28.json).

## PR #246: three workflows, no unshipped feature delta

| Changed file | Behavior and disposition |
| --- | --- |
| `.github/workflows/collect-drhp-pages.yml` | Push-only on `feature/drhp-filings-20260925`; read-only bounded collector for ten SEBI pages and three AMIRCHAND/LEAP sources, with original-byte hashes and a 14-day artifact. Errors and HTTP failures are retained but do not make its collection process fail. Superseded by the current collector/integrity/status pipeline; do not revive. |
| `.github/workflows/materialize-drhp-feature.yml` | Push-only on the old branch, explicitly checks out and pushes that branch with contents-write permission. Fetches five packed Git blobs plus fixed source artifact `10888804325`, SHA-256 `58becb285cd29c5ff7fa5fd93c8820ffbf0dd3160f3ba51cb3b6e6b4f0ac103e`; verifies transport/payload hashes, 19 exact allowed file paths, before/after hashes and seed hashes. It also contains a narrowly hash-guarded transfer-encoding repair. These guards must not be relaxed. Its commit/push occurs before browser testing, and it is an old-baseline bootstrap rather than a current-main migration. Retire without execution. |
| `.github/workflows/review-drhp-sources.yml` | Read-only PR-triggered exploratory probe of SEBI/NSE and the old deployed baseline; records failures but does not fail collection. It was explicitly temporary in the original PR description. Do not reintroduce obsolete collection into ordinary CI. |

The first two workflows would be inert on a main push as written. This review does **not** claim that merging their YAML automatically overwrites main. The replay hazard is reviving the old branch/materializer, retargeting it, or bypassing its baseline guards to restore already-superseded code, evidence and UI. All three files are absent from current main and should remain absent.

The opaque five-part code payload is not an ordinary PR code diff and was not executed or independently decoded in this review. A read-only blob fetch returned a binary UTF-8 decoding error; no validation bypass or materialization run was attempted. Retirement rests on the complete visible workflow review, current production equivalents, merged release history and current regression checks; it does not certify the packed payload as safe to replay.

The requested outcomes already exist:

- [#248](https://github.com/Vasuki8/IPO-Tracker/pull/248), merge `a6577265048c5d7e4855feac34a3b6c06800e969`, shipped DRHP functionality and resolved AMIRCHAND/LEAP with retained official evidence. LEAP's listed symbol is **LEAPIND**; do not restore the earlier held-identity work.
- [#249](https://github.com/Vasuki8/IPO-Tracker/pull/249), merge `253b2d1b11341e240c4e1ea11742a76c1ffd8cef`, preserves filing history, rejects stale/conflicting data, counts unique URLs, retains original responses and verifies served publication.
- #251 and #252 changed the surface to company-level Pre-IPO coverage and added exact canonical lifecycle filtering with fail-closed validation. Source filing history remains retained when a company progresses.
- #253–#256 added the official lead-manager fallback and corrected mirror/date/identity mistakes with correction history.
- `update-drhp.yml`, `sync-sebi-drhp.mjs`, `drhp-integrity.mjs`, `verify-drhp-publication.mjs` and `assets/pre-ipo-filter.js` are the current paths. They retain last-good data on collection failure, surface the failure, preserve separate clocks and maintain partial-coverage labels. The current cadence remains every two hours with bounded SEBI pagination; this review changes none of it.

DRHP discovery can support P1 coverage, but recreating this completed feature is not the next P1 task. Current source/field review remains **IREDA (544026), Motisons (544053), RBZ (544060), Shelter (543963)** using PR #334's retained receipt. The original 2023 queue remains **8 published / 22 awaiting**; discovery and successful downloads do not authorize publication. Preserve all conflict, null, alias, cross-year and completed-batch safeguards.

## Verification and limits

Fresh local checks at the reviewed main completed successfully:

```text
node scripts/test-apply-verified-bse-listings.mjs
node scripts/test-verify-bse-listing-candidates.mjs
node scripts/test-bse-publication-rehearsal.mjs
node scripts/test-sync-sebi-drhp.mjs
node scripts/test-drhp-integrity.mjs
node scripts/test-drhp-ui.mjs
node scripts/check-bse-2023-progress.mjs
node scripts/check-bse-2022-disposition.mjs
node scripts/check-retained-bse-snapshot.mjs
node scripts/build-published-data.mjs --check
node scripts/validate-data.mjs
git diff --exit-code
git diff --check
```

The real BSE importer/publisher rehearsal ran in an isolated temporary copy: **1,375 before = 1,375 after, 0 added, 1,375 unchanged, 296 reviewed entries already present, 0 holds/conflicts, idempotent rerun**. Current DRHP tests verified **96 retained companies / 98 filing URLs / 85 active Pre-IPO companies / 11 progressed companies hidden**, including failure/stale/conflict/URL and lifecycle safeguards. The 2023 and 2022 ledgers passed; the original retained 920-row snapshot check was read-only and did not refetch its raw report.

Two exploratory check errors were corrected before the successful final command batch: the ad-hoc record matcher initially used a nonexistent `company_name` field, and `test-pre-ipo-filter.mjs` does not exist (the lifecycle assertions are in `test-drhp-ui.mjs`). Neither required a repository code change.

This task changes documentation and PR state only. It does not claim fresh raw-source, browser or live-site field verification, a new public-data release, complete IPO coverage, or validation of the opaque materializer payload. Existing publication health at reviewed main records successful Pages run `36434045747`, completion `2026-09-28T14:11:20Z`, for `9e8e9341f159dddbca2b668a5848a2561654c14e`; that is a retained observation, not a fresh fetch. Review was performed inline. P5/performance expansion remains blocked by the existing upstream gates.
