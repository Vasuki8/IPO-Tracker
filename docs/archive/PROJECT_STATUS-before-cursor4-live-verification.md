# Project status and handoff

Updated: 2026-09-24 UTC (September 24 in America/Toronto).

## Current priority

Continue P1/P2/P3 backend correctness, official-source coverage and dependable publication under `DEVELOPMENT_PROCESS.md`. The active application-term requirement is **Lot Size only**; minimum investment, UI redesign, research-depth expansion and commercial infrastructure remain out of scope.

Never infer missing IPO values. Keep listing date, index admission date, market lot, minimum bid quantity and application amount distinct.

## Latest completed batch: repaired cursor3 BSE references published — PR #184

PR #184 merged as:

`d08479a3c12cd5975902dfa5f689a22adc90b008`

This batch closed the 12 listing references recovered by the parser-v1.2.0 repair. It reconciled current identity coverage, independently verified the genuinely missing issuers from issuer-specific official BSE listing notices, retained reviewed evidence, published the missing records through the existing importer, verified production and left the next historical cursor segment cleanly isolated.

### Reconciliation

Source cursor state at reconciliation:

- parser: **1.2.0**
- cursor state blob: `4ab17cca3944d2d907c0961ccdc2648bcff38a00`
- tracked: **80 / 236 eligible**
- parsed: **80**
- failed: **0**
- next unseen: **`20250403-16`**

Reconciliation snapshots:

- 2025 recovery: **258 records**, blob `ee6464ea4388cf99ea278c04a495b917df112730`
- public dataset: **1,014 records**, blob `a524ef19c2f8a0c0c58375b6bc6cb21d4bded3dc`

Result:

- recovered references: **12**
- already present exact identity: **1**
- missing exact identities: **11**
- identity review required: **0**
- fuzzy matches accepted: **0**

The one already-present issuer was **3B Films Limited**. Its existing record already used BSE listing notice `20250605-49`, listing date 2025-06-06, market lot 3,000 and issue price INR 50, so it was excluded from the new verification/publication batch rather than overwritten.

Retained reconciliation:

- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor3-repaired.json`
- `data/discovery/bse-listing-candidates-2026-09-24-batch12.json`

Index-addition notices remained discovery-only.

### Issuer-specific verification

Initial pinned verification:

- run: **`35968091282`**
- attempted: **11**
- verified: **11**
- rejected: **0**
- unavailable: **0**
- artifact: **`10795017902`**
- artifact ZIP SHA-256: **`98e381697404285d1b521926bc6f81ba8cad4d5b42f43022b4952a1011521036`**

The PDF archive upgrade check completed without finding canonical listing-PDF archive paths for these 11 notices. Ancillary attachments were not accepted as listing authority. The already established strict official-BSE-HTML evidence contract was retained.

Reviewed manifest:

`data/verified-bse-listings/2026-09-24-batch17.json`

Final PR-head re-verification:

- run: **`35968733466`**
- attempted: **11**
- verified: **11**
- rejected: **0**
- unavailable: **0**
- artifact: **`10795735136`**
- artifact ZIP SHA-256: **`81d0ee8859e2dfee5998a98e30ec68067e95799f0a8db640ae375800b72c21ff`**

Final PR checks also passed:

- data-contract CI: **`35968733491`**
- reviewed-evidence/importer CI: **`35968733500`**

### Eleven published issuers

| Issuer | BSE code | Listing notice | Listing date | Market lot | Issue price |
| --- | ---: | --- | --- | ---: | ---: |
| ASSTON PHARMACEUTICALS LIMITED | 544445 | `20250715-53` | 2025-07-16 | 1,000 | INR 123 |
| GLEN INDUSTRIES LIMITED | 544444 | `20250714-41` | 2025-07-15 | 1,200 | INR 97 |
| META INFOTECH LIMITED | 544441 | `20250710-60` | 2025-07-11 | 800 | INR 161 |
| CRYOGENIC OGS LIMITED | 544440 | `20250709-45` | 2025-07-10 | 3,000 | INR 47 |
| UNIFIED DATA TECH SOLUTIONS LIMITED | 544406 | `20250528-43` | 2025-05-29 | 400 | INR 273 |
| SRIGEE DLM LIMITED | 544399 | `20250509-44` | 2025-05-12 | 1,200 | INR 99 |
| MANOJ JEWELLERS LIMITED | 544400 | `20250509-45` | 2025-05-12 | 2,000 | INR 54 |
| KENRIK INDUSTRIES LIMITED | 544398 | `20250508-51` | 2025-05-09 | 6,000 | INR 25 |
| SPINAROO COMMERCIAL LIMITED | 544392 | `20250407-51` | 2025-04-08 | 2,000 | INR 51 |
| INFONATIVE SOLUTIONS LIMITED | 544393 | `20250407-67` | 2025-04-08 | 1,600 | INR 79 |
| RETAGGIO INDUSTRIES LIMITED | 544391 | `20250404-53` | 2025-04-07 | 6,000 | INR 25 |

Only the explicitly verified listing date, market lot and final issue price were populated. Unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null.

### Publication rehearsal

The real importer/publication rehearsal measured:

- **1,014 -> 1,025 records**
- exactly **11 additions**
- **92 already-present** reviewed BSE records
- **0 held existing**
- **0 identity conflicts**
- all **1,014 existing records unchanged**
- second import/rebuild: **no-op / idempotent**

### Production publication

Merge-triggered live sync:

- run: **`35969070759`**
- conclusion: **success**
- reviewed BSE import: **11 added / 92 already present / 0 held / 0 identity conflicts**
- semantic publication: **11 added / 45 changed / 0 removed / 0 conflicts**
- source-backed data commit: **`53589374e3078540394866180b467bf7fb1442ad`**
- operator-state commit: **`8cd16c9a2ca45bc38ef239d81b455de7276d225d`**
- schema 1.2.0 validation: **1,025 records passed**
- operator health: **healthy**

Production after publication:

- **1,025 total IPO records**
- **2025: 269 records**
- **2026: 85 records**

The 45 changed records were normal concurrent NSE/SEBI source enrichment from the same source-first sync; the semantic publisher separately identified the 11 batch17 additions and zero removals/conflicts.

Current production blobs after publication:

- `data/ipos.json`: `253277e892c01be613aeb54284a7b56f8c6b8e3f`
- `data/recovery/2025/nse-issue-information.json`: `7a7aa351750df012bfe4eb3c85d0b9d2c457199c`

Independent post-publication record audit confirmed all 11 issuers:

- occur exactly once in recovery and public data;
- have the exact reviewed listing date, market lot and issue price;
- retain the exact issuer-specific BSE notice URL;
- retain the exact verified response/document SHA-256;
- carry `data/verified-bse-listings/2026-09-24-batch17.json` provenance.

All 11 audit checks passed.

### Deployment

Native GitHub Pages build **`35969750035`** completed successfully on final operator revision:

`8cd16c9a2ca45bc38ef239d81b455de7276d225d`

That revision descends from source-backed data commit `53589374e3078540394866180b467bf7fb1442ad`, so the deployed Pages revision contains the 1,025-record release.

### Current historical cursor and next task

The cursor did not advance during this publication batch:

- parser: **1.2.0**
- **80 tracked / 236 eligible**
- **80 parsed**
- **0 failed / unparseable**
- **156 unseen**
- next unseen notice: **`20250403-16`**

**Next task:** always re-read `ops/bse-sme-addition-notices.json` first. If it has advanced beyond 80 tracked notices, reconcile the newest completed cursor segment against the current **1,025-record** universe. If it is unchanged, the next bounded discovery segment starts at `20250403-16`; advance it through the existing independent BSE notice backfill, retain the resulting source hashes/references, then reconcile only the newly parsed references before issuer-specific verification. Do not repeat batch12/batch17, 3B Films handling, or the parser-v1.2.0 repair.

## Prior completed batch: legacy 2025 BSE SME notice parser repair — PR #182

PR #182 merged as:

`1d892d573181d126bf2cee87ae63ae65057e6977`

This batch repaired the **10 unparseable notices** left by the third durable BSE SME addition-notice cursor window. It did not materialize IPOs and did not infer listing terms from index evidence.

### Demonstrated source-family failure

A temporary, read-only diagnostic was run against exactly the 10 retained failures. For every notice, the current official BSE Index Services detail response SHA-256 matched the `extracted_text_sha256` already retained in cursor state, proving that the parser was failing on the same source text rather than on changed upstream content.

The 2025 source family demonstrated three grammar variants absent from parser v1.1.0:

- `Notice No .` with whitespace before the period;
- `listed on the SME Platform of BSE`;
- whitespace around a listing-notice dash, demonstrated by `20250407- 51`.

Representative official source clauses covered both single-issuer and shared-date plural notices.

### Parser and cursor migration repair

Parser version is now **1.2.0**.

The repair:

- accepts the demonstrated `Notice No .` punctuation;
- accepts optional `the` before `SME Platform of BSE`;
- accepts whitespace around the notice-number dash;
- canonicalizes recovered notice IDs to `YYYYMMDD-N`;
- retains all prior strict listing-statement, issuer, ticker and date-safety rules;
- treats successful v1.1 parsed entries as compatible with this additive grammar change;
- immediately isolates failed v1.1 entries as `parser_changed_failure` work, rather than replaying all previously parsed notices.

During PR validation, the semantic state-merge test exposed one migration edge case. The merge previously compared an existing entry with the proposal's root parser version, which could let a stale same-version failure replace newer parsed evidence. It now compares **incoming entry parser version** instead. Regression coverage proves both behaviors: stale same-version evidence cannot regress state, and a real v1.1 -> v1.2 repair can replace the failed entry.

Temporary diagnostic code and its temporary CI hook were removed before merge.

### Verification

Final PR-head checks:

- data-contract CI `35967129380`: **success**
- reviewed-BSE evidence CI `35967129462`: **success**
- dedicated BSE historical cursor workflow `35967129385`: **success**

Post-merge checks on `1d892d573181d126bf2cee87ae63ae65057e6977`:

- data-contract CI `35967210793`: **success**
- reviewed-BSE evidence CI `35967210815`: **success**
- BSE SME universe audit `35967210872`: **success**
- Pages workflow `35967210809`: **success**

### Production parser-migration run

Merge-triggered historical BSE cursor run:

- workflow: **`35967210854`**
- report artifact: **`10794322473`**
- parser version: **1.2.0**
- selected: **10**, all with reason `parser_changed_failure`
- parsed: **10/10**
- fetch errors: **0**
- unparseable: **0**
- recovered listing references: **12**
- semantic cursor-state commit: **`f8cdb085377d2beba8a51c5e697b8d618398aaa9`**

Cursor progress changed from:

- 70 compatible parsed
- 10 stale parser failures
- 156 untouched older notices

to:

- **80 parsed**
- **0 failed**
- **0 stale parser entries**
- **156 unseen**
- next unseen notice: **`20250403-16`**

The cursor still has **80 tracked / 236 eligible** notices because this batch repaired ten existing tracked entries rather than advancing into ten new older notices.

### Twelve recovered discovery references

| Issuer | BSE code | Listing notice | Listing date |
| --- | ---: | --- | --- |
| ASSTON PHARMACEUTICALS LIMITED | 544445 | `20250715-53` | 2025-07-16 |
| GLEN INDUSTRIES LIMITED | 544444 | `20250714-41` | 2025-07-15 |
| META INFOTECH LIMITED | 544441 | `20250710-60` | 2025-07-11 |
| CRYOGENIC OGS LIMITED | 544440 | `20250709-45` | 2025-07-10 |
| 3B Films Limited | 544412 | `20250605-49` | 2025-06-06 |
| UNIFIED DATA TECH SOLUTIONS LIMITED | 544406 | `20250528-43` | 2025-05-29 |
| SRIGEE DLM LIMITED | 544399 | `20250509-44` | 2025-05-12 |
| MANOJ JEWELLERS LIMITED | 544400 | `20250509-45` | 2025-05-12 |
| KENRIK INDUSTRIES LIMITED | 544398 | `20250508-51` | 2025-05-09 |
| SPINAROO COMMERCIAL LIMITED | 544392 | `20250407-51` | 2025-04-08 |
| INFONATIVE SOLUTIONS LIMITED | 544393 | `20250407-67` | 2025-04-08 |
| RETAGGIO INDUSTRIES LIMITED | 544391 | `20250404-53` | 2025-04-07 |

These are **discovery candidates only**. The BSE SME index notice supplies an exact issuer/listing-reference pointer, but it is not accepted as listing-term authority. No IPO record was created or updated by this parser-repair batch.

## Next task: reconcile the repaired cursor3 references

Start by re-reading `ops/bse-sme-addition-notices.json`, because the independent cursor may have advanced after this handoff was written.

For the 12 recovered references above:

- compare exact normalized issuer identities against the current production/recovery universe;
- classify each as already present, genuinely missing or ambiguous;
- preserve index notice number/date/source URL/source hash plus recovered listing notice, BSE code and listing date;
- use no fuzzy identity match as publication authority;
- for genuinely missing, unambiguous issuers, pin and verify issuer-specific official BSE listing notices in a bounded batch;
- retain market lot, final issue price and any other listing terms only from issuer-specific official evidence;
- keep unsupported fields null;
- do not materialize records from the BSE index notice itself.

After this repaired set is reconciled, process the newest completed cursor segment if the independent historical cursor has advanced past `20250403-16`.

## Prior completed batch: third historical BSE cursor parsed references published — PR #181

PR #181 merged as:

`cc44fd35a4bf6eff37aa9a59807393ac33277ee6`

This batch closed the **14 parseable references** from the third durable BSE SME cursor window while keeping the ten failed index notices isolated for a later parser/source-family repair.

### Cursor3 source window

The source cursor window was produced by:

- workflow: **`35962928144`**
- source commit: **`1e19389f78ddafef7ae2a61596d7e8443dbfb4e9`**
- artifact: **`10793157274`**
- artifact ZIP SHA-256: **`caf6f8d747992eb25a447b8600b4f73eaf433d13d92ebde5e6a38aeeab649722`**
- cursor-state commit: **`1704357838871f9e5dd677da4a7bfabba7b50760`**

The window selected 20 older BSE SME index notices:

- **10 parsed**
- **10 unparseable**
- **14 listing references**
- **0 fetch errors**

Machine-readable reconciliation:

`data/discovery/bse-listing-reconciliation-2026-09-24-cursor3.json`

Pinned issuer-specific verification batch:

`data/discovery/bse-listing-candidates-2026-09-24-batch11.json`

Reconciliation against the then-current 244-record 2025 recovery universe found:

- **14 missing exact identities**
- **0 already-present matches**
- **0 ambiguous / identity-review overlaps**
- no fuzzy matching accepted

Index-addition evidence remained discovery-only.

### Fourteen recovered issuers

The parsed references were:

| Issuer | BSE code | Listing notice | Listing date |
| --- | ---: | --- | --- |
| RACHIT PRINTS LIMITED | 544503 | `20250905-49` | 2025-09-08 |
| ABRIL PAPER TECH LIMITED | 544500 | `20250904-47` | 2025-09-05 |
| SUGS LLOYD LIMITED | 544501 | `20250904-61` | 2025-09-05 |
| OVAL PROJECTS ENGINEERING LIMITED | 544498 | `20250903-50` | 2025-09-04 |
| GLOBTIER INFOTECH LIMITED | 544494 | `20250901-44` | 2025-09-02 |
| NIS MANAGEMENT LIMITED | 544495 | `20250901-47` | 2025-09-02 |
| STAR IMAGING AND PATH LAB LIMITED | 544482 | `20250814-59` | 2025-08-18 |
| BLT LOGISTICS LIMITED | 544474 | `20250808-49` | 2025-08-11 |
| ESSEX MARINE LIMITED | 544475 | `20250808-47` | 2025-08-11 |
| REPONO LIMITED | 544463 | `20250801-73` | 2025-08-04 |
| UMIYA MOBILE LIMITED | 544464 | `20250801-62` | 2025-08-04 |
| MONARCH SURVEYORS AND ENGINEERING CONSULTANTS LIMITED | 544453 | `20250728-56` | 2025-07-29 |
| SWASTIKA CASTAL LIMITED | 544452 | `20250726-1` | 2025-07-28 |
| MONIKA ALCOBEV LIMITED | 544451 | `20250722-42` | 2025-07-23 |

### Globtier issuer-identity repair

Initial source verification run **`35964144439`** reached:

- attempted: **14**
- verified: **13**
- rejected: **1**
- unavailable: **0**

Globtier Infotech was the only rejection.

The official BSE notice was internally consistent and independently contained:

- issuer: Globtier Infotech Limited
- BSE code: **544494**
- listing date: **2025-09-02**
- market lot: **1,600**
- final issue price: **INR 72**

The false rejection came from BSE HTML wrapping one body-name occurrence in:

`&ldquo;Globtier Infotech limited&rdquo;`

The verifier normalized `&quot;` but not BSE curly-quote entities, producing a spurious second normalized issuer identity.

PR #181 added only the demonstrated decoding repair:

- `&ldquo;` and `&rdquo;` -> ordinary quote;
- `&lsquo;` and `&rsquo;` -> ordinary apostrophe.

All existing strict checks remain unchanged after decoding:

- normalized issuer identity;
- exact listing notice;
- exact six-digit BSE code;
- exact listing date;
- SME segment;
- explicit equity-listing statement;
- positive market lot / final issue price.

An exact Globtier regression fixture was added.

### Canonical source verification

After the bounded entity repair, run **`35964560752`** independently verified:

- attempted: **14**
- verified: **14**
- rejected: **0**
- unavailable: **0**

Artifact:

- id: **`10792809549`**
- ZIP SHA-256: **`e6f102405d0c31657ea441b786cf2edb67f532885b759d586e53ca0044303fe7`**

All 14 are retained as reviewed official-BSE-notice HTML evidence because the canonical archive listing-PDF paths were unavailable.

Reviewed manifest:

`data/verified-bse-listings/2026-09-24-batch16.json`

Exact retained lot / final issue-price values:

| Issuer | Market lot | Final issue price |
| --- | ---: | ---: |
| RACHIT PRINTS LIMITED | 1,000 | INR 149 |
| ABRIL PAPER TECH LIMITED | 2,000 | INR 61 |
| SUGS LLOYD LIMITED | 1,000 | INR 123 |
| OVAL PROJECTS ENGINEERING LIMITED | 1,600 | INR 85 |
| GLOBTIER INFOTECH LIMITED | 1,600 | INR 72 |
| NIS MANAGEMENT LIMITED | 1,200 | INR 111 |
| STAR IMAGING AND PATH LAB LIMITED | 1,000 | INR 142 |
| BLT LOGISTICS LIMITED | 1,600 | INR 75 |
| ESSEX MARINE LIMITED | 2,000 | INR 54 |
| REPONO LIMITED | 1,200 | INR 96 |
| UMIYA MOBILE LIMITED | 2,000 | INR 66 |
| MONARCH SURVEYORS AND ENGINEERING CONSULTANTS LIMITED | 600 | INR 250 |
| SWASTIKA CASTAL LIMITED | 2,000 | INR 65 |
| MONIKA ALCOBEV LIMITED | 400 | INR 286 |

Main-branch source re-verification:

- workflow: **`35965260696`**
- batch11: **14 / 14 verified**
- artifact: **`10793054943`**
- artifact ZIP SHA-256: **`cefbbed883f300a65f72c1445493b8edd30859de9506fb6f5145c005338c4377`**

### Pre-merge validation

Final PR-head checks:

- reviewed BSE evidence/importer: **`35965176868`** — success
- full data contract: **`35965176865`** — success
- protected BSE 544770 identity regression: **`35965176842`** — success
- canonical source verification: **`35964560752`** — 14 / 14

The real importer rehearsal measured:

- **1000 -> 1014 records**
- exactly **14 additions**
- **78 already-present** reviewed BSE records
- **0 held existing records**
- **0 identity conflicts**
- all **1000 existing records unchanged**
- second import/rebuild: **no-op / idempotent**
- total retained reviewed BSE entries: **92**

### Production publication

Merge-triggered live sync:

- run: **`35965260674`**
- conclusion: **success**
- reviewed BSE import: **14 added / 78 already present / 0 holds**
- semantic publication: **14 added / 41 changed / 0 removed / 0 conflicts**
- schema 1.2.0 validation: **1014 records passed**
- operator health: **healthy**

Source-backed data commit:

`e607bb92434fbf41fcd84daddd71e0b665ac60ee`

Operator-state commit:

`50792aceff402c683d341dc9bf9bb730739005ef`

Production after publication:

- **1014 total IPO records**
- **2025: 258 records** — 83 Mainboard / 174 SME / 1 unknown
- **2026: 85 records** — 15 Mainboard / 60 SME / 10 unknown
- all 14 batch16 issuers occur exactly once
- all 14 BSE codes, listing dates, market lots and issue prices agree with reviewed evidence
- all 14 exact BSE source URLs and document hashes are retained
- all 14 retain `batch16` provenance
- HTML-backed facts use `page: null`
- unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null
- deterministic recovery build and schema validation passed
- operator health: **healthy**

The 41 changed records are normal concurrent official NSE/SEBI enrichment from the same source-first run. The semantic publisher separately identified exactly 14 additions and zero removals/conflicts.

### Deployment

Native GitHub Pages build **`35965869172`** completed successfully on:

`50792aceff402c683d341dc9bf9bb730739005ef`

That operator-state revision directly descends from data commit `e607bb92434fbf41fcd84daddd71e0b665ac60ee`, so the deployed Pages revision contains the 1014-record release.

### Remaining cursor3 parser/source failures

PR #181 did not modify or trigger the durable cursor state.

Current cursor remains:

- **80 tracked / 236 eligible**
- **70 parsed**
- **10 unparseable**
- **156 unseen**
- next unseen notice: **`20250403-16`**

The 14 parsed cursor3 references are now fully closed.

The ten unfinished notices from this same window are:

- `20250716-16`
- `20250715-47`
- `20250711-10`
- `20250710-17`
- `20250606-10`
- `20250529-14`
- `20250512-14`
- `20250509-10`
- `20250408-20`
- `20250407-20`

These remain `no_parseable_listing_reference` and were **not** used to infer any issuer.

### Next task

Always re-read `ops/bse-sme-addition-notices.json` first because it advances independently.

If the cursor is still at the current 80-notice state, inspect the 10 unparseable notices and group them by demonstrated source/text shape. Repair the smallest reusable source family first, with regression tests and without inferring issuer identities from incomplete evidence.

If the cursor has advanced before the next continuation, reconcile the newly completed cursor segment first.

Do not repeat the completed 14-reference cursor3 publication batch.

## Latest completed batch: repaired BSE notice 20250912-85 and published two issuers — PR #180

PR #180 merged as:

`1e19389f78ddafef7ae2a61596d7e8443dbfb4e9`

This batch repaired the single unparseable BSE SME index notice left by the prior cursor segment, verified the recovered issuer identities independently, and published both missing IPOs.

### Root cause

Cursor entry `20250912-85` had been retained as:

- status: `unparseable`
- error: `no_parseable_listing_reference`
- source kind: `bse_index_notice_detail_api`
- source URL: `https://www.bseindices.com/AsiaIndexAPI/api/DisplayNoticecircular/w?NoticeId=20250912-85`
- extracted-text SHA-256: `c2504ec9ca86dcfc0aa36ff50afa5c70803d3802353d955aff602b5eae88a8d8`

The official notice contains two explicit issuer references joined by an ampersand:

- BSE listing notice `20250911-76` — **AUSTERE SYSTEMS LIMITED** — ticker **544505**
- BSE listing notice `20250911-79` — **SHARVAYA METALS LIMITED** — ticker **544506**

The shared listing statement says the two issuers **are being listed on SME platform of BSE effective Friday, September 12, 2025**.

The same index notice later says the stocks will be added to the BSE SME IPO index effective **September 15, 2025**. That later date is an index-admission date and is not used as the listing date.

### Bounded parser repair

The prior parser recognized phrases such as `listed on BSE effective ...` but not the demonstrated wording `listed on SME platform of BSE effective ...`.

PR #180 makes only the source-proven extension:

- accept `listed on SME platform of BSE` as an equivalent BSE listing statement;
- allow `&` as a separator only when both sides still contain a complete Notice No / issuer / six-digit Exchange ticker reference;
- preserve the shared listing date for each complete reference;
- keep the later index-admission date excluded.

Regression guards prove that the repair does **not**:

- accept another exchange such as NSE;
- accept a missing issuer ticker;
- borrow a ticker from the next issuer;
- use the later index-admission date as listing date.

The retained cursor entry for `20250912-85` was deterministically reparsed from the same source/hash into exactly two references. No issuer identity, code or date was guessed.

### Repaired discovery

Retained reconciliation:

`data/discovery/bse-listing-reconciliation-2026-09-24-notice-20250912-85.json`

Pinned issuer-specific candidates:

`data/discovery/bse-listing-candidates-2026-09-24-batch10.json`

Both issuers were absent from the 2025 recovery universe before publication.

### Issuer-specific verification

Initial independent source run:

- workflow: **`35962409176`**
- repaired candidates attempted: **2**
- verified: **2**
- rejected: **0**
- unavailable: **0**
- artifact: **`10793305545`**
- artifact ZIP SHA-256: **`a6e9c232aeb36430e83023607ddfee87ea9e72cb69fb2027d41f9558269d99bc`**

Both records verified from exact issuer-specific official BSE notice HTML. The canonical listing-PDF archive path was unavailable, so the existing reviewed official-notice HTML evidence contract was used.

Reviewed manifest:

`data/verified-bse-listings/2026-09-24-batch15.json`

Exact reviewed facts:

| Issuer | BSE code | Listing notice | Listing date | Market lot | Issue price |
| --- | --- | --- | --- | ---: | ---: |
| AUSTERE SYSTEMS LIMITED | 544505 | `20250911-76` | 2025-09-12 | 2,000 | INR 55 |
| SHARVAYA METALS LIMITED | 544506 | `20250911-79` | 2025-09-12 | 600 | INR 196 |

Final `main` source verification repeated the repaired candidates successfully:

- workflow: **`35962927921`**
- repaired candidates: **2 / 2 verified**
- rejected: **0**
- unavailable: **0**
- artifact: **`10793346309`**
- artifact ZIP SHA-256: **`675edf2f8701535c0d6cd3b5756af3713fbabae41d884a70f7ca74c0448f9cb4`**

### Pre-merge validation

Final PR-head checks:

- reviewed BSE evidence/importer validation: **`35962725162`** — success
- durable BSE cursor/parser validation: **`35962725126`** — success
- full data-contract validation: **`35962725175`** — success
- earlier issuer-specific source verification proving the two candidates: **`35962409176`** — success

The isolated real-import publication rehearsal measured:

- **998 -> 1000 records**
- exactly **2 additions**
- **76 already-present** reviewed BSE records
- **0 held existing records**
- **0 identity conflicts**
- all **998 existing records unchanged**
- second import/rebuild: **no-op / idempotent**
- total retained reviewed BSE entries after this batch: **78**

### Production publication

Merge-triggered live sync:

- run: **`35962927876`**
- conclusion: **success**
- reviewed BSE import: **2 added / 76 already present / 0 holds**
- semantic publication: **2 added / 30 changed / 0 removed / 0 conflicts**
- schema 1.2.0 validation: **1000 records passed**
- operator health: **healthy**

Source-backed data commit:

`33d311903621c110e0db608c913fb071ccd99eb3`

Operator-state commit:

`a275eaa5fcb6fdb665b702a8d47e5555500d0ea3`

Production after publication:

- **1000 total IPO records**
- **2025: 244 records** — 83 Mainboard / 160 SME / 1 unknown
- **2026: 85 records** — 15 Mainboard / 60 SME / 10 unknown
- Austere Systems occurs exactly once
- Sharvaya Metals occurs exactly once
- listing date, BSE code, market lot and issue price agree with reviewed evidence
- exact BSE notice URL and document SHA-256 are retained
- HTML-backed facts use `page: null`
- unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null
- deterministic recovery build and schema validation passed
- operator health: **healthy**

### Deployment

Native GitHub Pages build **`35963513850`** completed successfully on:

`a275eaa5fcb6fdb665b702a8d47e5555500d0ea3`

That operator-state revision descends directly from the 1000-record source-backed data commit, so the deployed Pages revision contains both repaired issuers.

### Independent cursor advance after merge

PR #180 also triggered the independent historical BSE notice cursor.

Cursor run:

- workflow: **`35962928144`**
- artifact: **`10793157274`**
- artifact ZIP SHA-256: **`caf6f8d747992eb25a447b8600b4f73eaf433d13d92ebde5e6a38aeeab649722`**
- state commit: **`1704357838871f9e5dd677da4a7bfabba7b50760`**

It selected the next 20 older notices.

Result:

- **10 parsed**
- **10 unparseable**
- **14 discovered listing references**
- **0 fetch errors**

Durable cursor now:

- **80 tracked / 236 eligible**
- **70 parsed**
- **10 unparseable**
- **156 unseen**
- next unseen notice: **`20250403-16`**

The 14 newly parsed references begin with:

- RACHIT PRINTS LIMITED — 544503
- ABRIL PAPER TECH LIMITED — 544500
- SUGS LLOYD LIMITED — 544501
- OVAL PROJECTS ENGINEERING LIMITED — 544498
- GLOBTIER INFOTECH LIMITED — 544494
- NIS MANAGEMENT LIMITED — 544495
- STAR IMAGING AND PATH LAB LIMITED — 544482
- BLT LOGISTICS LIMITED — 544474
- ESSEX MARINE LIMITED — 544475
- REPONO LIMITED — 544463
- UMIYA MOBILE LIMITED — 544464
- MONARCH SURVEYORS AND ENGINEERING CONSULTANTS LIMITED — 544453
- SWASTIKA CASTAL LIMITED — 544452
- MONIKA ALCOBEV LIMITED — 544451

The ten new unparseable notices are:

- `20250716-16`
- `20250715-47`
- `20250711-10`
- `20250710-17`
- `20250606-10`
- `20250529-14`
- `20250512-14`
- `20250509-10`
- `20250408-20`
- `20250407-20`

None of these 14 new references or 10 unparseable notices were reconciled/materialized as part of PR #180.

### Next task

Always re-read `ops/bse-sme-addition-notices.json` first because the cursor advances independently.

If the cursor is still at the 80-notice state, the next coherent batch is:

1. reconcile the **14 newly parsed listing references** against the current **1000-record** recovery universe;
2. split genuinely missing identities into bounded verification batches of at most 15;
3. verify issuer-specific official BSE listing evidence before publication;
4. keep the **10 unparseable notices** as a separate parser/source-family repair track.

Do not repeat the completed `20250912-85` repair.

## Latest completed batch: second historical BSE cursor batch published — PR #178

PR #178, **Reconcile second historical BSE cursor batch**, merged as:

`17e0c7322d975587de0f640e83215ef68022c33f`

This batch consumed the next durable BSE SME index-notice cursor segment and recovered the full set of parseable missing issuers across the 2025/2026 boundary.

### Cursor advance

The bounded cursor run was:

- workflow: **`35959162509`**
- cursor artifact: **`10791926413`**
- artifact ZIP SHA-256: **`ac543656d4fdfa7f6644ef50e0274d93d8c01a75d5aa28fdd70255881a109209`**
- retained state commit: **`5d63a07f9f1910b5b6eccb913dfc31ecdfed327d`**

The selected window contained **20 older BSE SME index notices**.

Current operational status for that cursor position is:

- **60 tracked notices total**
- **59 parsed**
- **1 unparseable**
- **176 unseen**
- next unseen notice: **`20250908-25`**

The unparseable notice is intentionally retained rather than guessed:

- notice: **`20250912-85`**
- date: **2025-09-12**
- source: `https://www.bseindices.com/AsiaIndexAPI/api/DisplayNoticecircular/w?NoticeId=20250912-85`
- extracted-text SHA-256: **`c2504ec9ca86dcfc0aa36ff50afa5c70803d3802353d955aff602b5eae88a8d8`**
- error: **`no_parseable_listing_reference`**

The cursor is designed so this failed notice does not block older unseen notices.

### Cross-year reconciliation

The 19 successfully parsed notices produced **30 listing references**.

They were reconciled against both retained recovery universes:

- 2025 recovery before this batch: **213 records**
- 2026 recovery before this batch: **84 records**

Result:

- **30 missing exact identities**
- **0 already-present exact matches**
- **0 identity-review / ambiguous overlaps**
- **0 fuzzy-name equivalence accepted**

Index-addition evidence remains discovery-only.

Retained machine-readable reconciliation:

`data/discovery/bse-listing-reconciliation-2026-09-24-cursor2.json`

The 30 missing references were divided into two bounded 15-candidate verification files:

- `data/discovery/bse-listing-candidates-2026-09-24-batch8.json`
- `data/discovery/bse-listing-candidates-2026-09-24-batch9.json`

### Issuer-specific BSE verification

The reviewed manifests were created from source run:

- workflow: **`35959840134`**
- artifact: **`10792036701`**
- artifact ZIP SHA-256: **`3d883788e3aa99fd09553869f0850150b0a987174861b292804a021e206e6c94`**

Each bounded half verified **15 / 15** against issuer-specific official BSE listing notices.

The canonical archive listing-PDF paths were not available for these records, so publication uses the existing reviewed **official BSE notice HTML** contract. Each retained entry has the exact BSE notice URL, response/document hash, compact normalized identity/fact evidence, collection/publication timestamps, and offline replay through the listing verifier. No index notice is used as market-term authority and no page number is invented.

Canonical reviewed manifests:

- `data/verified-bse-listings/2026-09-24-batch9.json` — 4 entries
- `data/verified-bse-listings/2026-09-24-batch10.json` — 7 entries
- `data/verified-bse-listings/2026-09-24-batch11.json` — 4 entries
- `data/verified-bse-listings/2026-09-24-batch12.json` — 5 entries
- `data/verified-bse-listings/2026-09-24-batch13.json` — 5 entries
- `data/verified-bse-listings/2026-09-24-batch14.json` — 5 entries

Total reviewed records in this cursor batch: **30**.

Final PR source verification repeated both halves successfully:

- workflow: **`35960785399`**
- batch 8: **15 / 15 verified**
- batch 9: **15 / 15 verified**
- rejected: **0**
- unavailable: **0**
- artifact: **`10792048220`**
- artifact ZIP SHA-256: **`2df53976159ccbaa39558020ddf3c5300f76a286d5bdaea907560105afc7e015`**

### Bounded parser repair

Apollo Techno Industries' official notice uses this BSE date formatting:

`December 31 , 2025`

The previous listing-date grammar accepted `December 31, 2025` but not whitespace immediately before the comma.

PR #178 made only the bounded formatting repair:

- `strictDate` permits optional whitespace before the comma;
- the issuer-specific listing-date regex permits the same harmless spacing;
- a regression test verifies Apollo's exact formatting.

This is not a relaxed date parser: invalid dates, wrong listing dates and non-listing date statements remain rejected.

### Pre-merge validation

Final PR-head checks:

- reviewed BSE evidence/importer validation: **`35960785377`** — success
- full data-contract validation: **`35960785360`** — success
- issuer-specific BSE source verification: **`35960785399`** — success
- protected BSE 544770 regression/source verification: **`35960785366`** — success

The isolated real-import publication rehearsal measured:

- **968 -> 998 records**
- exactly **30 additions**
- **46 already-present** reviewed BSE records
- **0 held existing records**
- **0 identity conflicts**
- all **968 existing records unchanged**
- second import/rebuild: **no-op / idempotent**
- total retained reviewed BSE evidence entries after this batch: **76**

### Production publication

Merge-triggered production sync:

- run: **`35960919082`**
- conclusion: **success**
- reviewed BSE import: **30 added / 46 already present / 0 holds**
- semantic publication: **30 added / 36 changed / 0 removed / 0 conflicts**
- schema 1.2.0 validation: **998 records passed**
- operator health: **healthy**

A separate historical PDF-field commit `45e34cff370a8f49501b1d3b935bd322aef58412` landed while the production sync was running. The semantic publisher reset against latest `main` and produced the final data commit one commit later, with zero conflicts, so the BSE additions and concurrent official-source enrichment were both retained.

Source-backed data commit:

`a8b6cc81f7c805598ab67552131833afea4bfa17`

Operator-state commit:

`32cadd15b4fc91a92ef89f5af6415c893b545146`

Production after publication:

- **998 total IPO records**
- **2025: 242 records** — 83 Mainboard / 158 SME / 1 unknown
- **2026: 85 records** — 15 Mainboard / 60 SME / 10 unknown
- 29 of the new cursor2 issuers belong to 2025
- 1 new issuer belongs to 2026
- every one of the 30 reviewed issuers occurs exactly once
- every BSE code, listing date, market lot, final issue price, source URL, document hash and manifest provenance matches committed reviewed evidence
- unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null
- deterministic recovery build and schema validation passed
- operator health: **healthy**

### Deployment

Native GitHub Pages build **`35961435740`** completed successfully on:

`32cadd15b4fc91a92ef89f5af6415c893b545146`

That operator-state revision directly descends from the 998-record data commit `a8b6cc81f7c805598ab67552131833afea4bfa17`, so the deployed Pages revision contains the full 30-record release.

### Concurrent duplicate work reconciliation

A second PR, **#179**, was opened while PR #178 was concurrently completing the same cursor batch.

Repository evidence showed that PR #178 had already:

- reconciled both 15-candidate halves;
- committed reviewed evidence for all 30 parsed references;
- included the same bounded Apollo spaced-comma parser repair;
- passed the complete source/import/data-contract test set.

PR #179 was therefore closed **without merge**. No duplicate evidence or IPO records were published from it.

### Next task

Always re-read `ops/bse-sme-addition-notices.json` first because the cursor advances independently.

At this handoff the state is:

- **60 tracked / 236 eligible**
- **59 parsed**
- **1 unparseable**
- **176 unseen**
- next unseen notice: **`20250908-25`**

If the cursor has advanced in the next continuation, reconcile only the newly completed cursor segment against the current **998-record** universe.

If the cursor is unchanged, the next bounded source-repair task is notice **`20250912-85`**. Inspect why the official index notice is currently `no_parseable_listing_reference`, repair only the demonstrated parser/source-family gap, and do not infer an issuer or listing notice when the source cannot prove one.

Do not repeat the completed 30-reference cursor2 batch.

## Latest completed batch: four held historical BSE listings resolved — PR #177

PR #177 merged as:

`e142d031eca66481c41428b65384b7cb0eb6b748`

This closes all four remaining source/identity holds from the first historical BSE SME discovery batch.

### Root causes

The four records did not share one failure mode.

**Autofurnish, Mehul Telecom and Tipco Engineering India**

Their issuer-specific official BSE listing PDFs were correctly located and downloaded, but page 2 is image-only. The PDF text layer contains the notice header on page 1 while `pdftotext` cannot recover the page-2 listing statement or terms. The earlier rejection was therefore a text-extraction limitation, not contradictory issuer evidence.

The official immutable PDFs were visually reviewed on page 2 without OCR. The reviewed facts are bound to exact BSE PDF hashes:

| Issuer | Notice | PDF SHA-256 | Listing date | Market lot | Issue price |
| --- | --- | --- | --- | ---: | ---: |
| AUTOFURNISH LIMITED | `20260527-47` | `9d19ae886d5aba5c8835ccbb656488d69b3ba8dd91a47b2411b3e7a21e97b8c3` | 2026-05-29 | 3,000 | INR 41 |
| MEHUL TELECOM LIMITED | `20260423-27` | `b620aec3111262a67e52332ba2d379dbaef32533129a8ef1c2a3215d2ac2300f` | 2026-04-24 | 1,200 | INR 98 |
| TIPCO ENGINEERING INDIA LIMITED | `20260330-44` | `ce287772d38f0efc53c4994a235331a422697f3bac2116a628fe78068a3d2bbc` | 2026-04-01 | 1,600 | INR 89 |

These three use the new reviewed evidence kind `official_listing_pdf_visual_review`.

That contract is intentionally narrow:

- exact official BSE listing-PDF URL only;
- immutable source document SHA-256;
- reviewed visual page limited to pages 1–3;
- candidate issuer, scrip code and listing date must still agree with discovery identity;
- market lot must be a positive integer and issue price a positive scalar;
- retained source strings must explicitly contain the reviewed values;
- the listing statement must contain the issuer, “Equity Shares”, “shall be listed”, and exact listing-date phrase;
- no OCR result, BSE index notice or inferred value is accepted as authority.

The visual review is preserved in:

`data/verified-bse-listings/2026-09-24-batch7.json`

Source artifact for the three PDFs:

- run: **`35956034085`**
- artifact: **`10789439895`**
- artifact ZIP SHA-256: **`d78e344277d79ccce4411e3a7f4552b3eeb87089e3d584d8a1fa8a5c746d1acb`**

**Recode Studios**

The original index-derived candidate referenced BSE notice `20260511-16`. That official notice is not the final listing-details notice: it explicitly states that the listing date and security details will be informed through a separate notice.

The original claim is preserved as correction history rather than silently replaced.

Corrected discovery:

`data/discovery/bse-listing-candidates-2026-09-24-batch7.json`

Corrected issuer-specific listing notice:

- BSE notice: **`20260511-46`**
- BSE scrip code: **544755**
- listing date: **2026-05-12**
- market lot: **800**
- final issue price: **INR 158/share**
- official PDF SHA-256: **`b04afcddd0177f067b27727405256b5bfc60d8783d825a7497367ff01f46e29a`**
- collection time: **2026-09-24T04:59:43.736Z**
- listing/lot/price evidence: **page 2**

Independent corrected-source verification:

- workflow run: **`35957926014`**
- attempted: **1**
- verified: **1**
- rejected/unavailable: **0**
- artifact: **`10791635591`**
- artifact ZIP SHA-256: **`08edc97e797cfba08fcb33cd83ba476a15217eb669f12eee6746a560d8c760dc`**

Reviewed Recode manifest:

`data/verified-bse-listings/2026-09-24-batch8.json`

### Validation

Final PR-head checks:

- reviewed BSE evidence/importer validation: **`35958072837`** — success
- full data-contract validation: **`35958072891`** — success
- BSE source verification including corrected Recode: **`35958072853`** — success

The isolated real-import publication rehearsal measured:

- **964 -> 968 records**
- exactly **4 additions**
- **42 already-present** reviewed BSE records
- **0 held existing records**
- **0 identity conflicts**
- all **964 existing records unchanged**
- second import/rebuild: **no-op / idempotent**
- total retained reviewed BSE entries: **46**

An initial PR test run failed because the synthetic visual-review fixture omitted the same “Equity Shares … shall be listed” structure required by the tightened contract. The fixture was corrected to realistic source wording; the production evidence contract was not weakened.

### Production publication

A scheduled live sync had already started immediately before the merge. The `live-ipo-sync` concurrency guard correctly cancelled that stale scheduled run when the merge-triggered run queued.

Merge-triggered production sync:

- run: **`35958207898`**
- conclusion: **success**
- reviewed BSE import: **4 added / 42 already present / 0 holds**
- semantic publication: **4 added / 35 changed / 0 removed / 0 conflicts**
- schema 1.2.0 validation: **968 records passed**
- operator health: **healthy**

The 35 changed records are concurrent official NSE/SEBI enrichment from the same source-first run; the semantic publisher separately identified exactly four additions and zero removals/conflicts.

Source-backed data commit:

`93f4e0b02141c66d547e94b2f184dccaebe39d26`

Operator-state commit:

`69aa8fb5e348a7de55b167fdd403c38c7ebb9ea1`

Production after publication:

- **968 total IPO records**
- **84 records for 2026**
- 2026 board coverage: **15 mainboard / 59 SME / 10 unknown**
- each of the four repaired issuers occurs exactly once
- each listing date, market lot and issue price agrees with reviewed evidence
- all four source document hashes are retained
- unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null
- deterministic build and schema validation passed
- operator health: **healthy**

### Deployment

Native GitHub Pages build **`35958746456`** completed successfully on:

`69aa8fb5e348a7de55b167fdd403c38c7ebb9ea1`

That operator-state revision directly descends from the 968-record data commit `93f4e0b02141c66d547e94b2f184dccaebe39d26`, so the deployed Pages revision contains the four-record release.

### First historical discovery batch is closed

The first durable-cursor discovery batch contained **23 listing references**.

Its final accounting is now:

- **6** were already present when reconciled;
- **17** were genuinely missing;
- all **17** missing issuers have now been resolved and published with reviewed issuer-specific official evidence;
- no candidates from that batch remain held.

Do not revisit the completed 23-reference batch unless later authoritative evidence creates an explicit correction.

### Next task

Re-read `ops/bse-sme-addition-notices.json` before starting the next run because the cursor advances independently.

At this handoff it remains:

- **40 / 236 parsed**
- **196 unseen**
- next unseen notice: **`20260107-29`**

The next scheduled cursor run has not yet advanced this state. Once it does, reconcile only the newly completed cursor batch against the current **968-record** universe, retain exact index-notice/listing-reference evidence, and verify/materialize only genuinely missing issuers.

If the cursor is still unchanged at the next continuation after its expected schedule window, inspect the cursor workflow execution/operational state as the next P3 reliability task. Do not manually reset the cursor or repeat the now-closed first historical batch.

## Latest completed batch: remaining seven historical BSE SME listings published — PR #176

PR #176 merged as:

`9edcbb30d0a62575e12c0116a2533564ffffc4f2`

This completed the publishable subset from the first historical BSE discovery reconciliation. Combined with PR #175's six PDF-backed records, all **13 issuer-specific candidates that independently verified in PR #174 are now published**. The four candidates that failed issuer-specific verification remain held.

### Evidence-path repair

The remaining seven records had verified official BSE listing-notice HTML but no usable canonical archive listing-PDF path. PR #176 tested the notice-bound `DownloadAttach.aspx` links exposed by those pages.

Those attachment URLs were constrained to:

- `https://www.bseindia.com/markets/MarketInfo/DownloadAttach.aspx`;
- exact matching listing-notice ID;
- UUID-shaped attachment ID;
- a maximum of four notice-bound attachment probes.

The attachments were real BSE PDFs, but they were ancillary Annexure documents rather than the listing notice itself and correctly failed the listing verifier with missing listing-notice identity/content. They are **not** used as listing authority.

Instead of weakening the PDF contract, PR #176 added a separate reviewed **official-notice HTML** contract. An HTML-backed reviewed entry must retain and revalidate:

- the exact issuer-specific BSE notice URL;
- BSE notice number and publication date;
- raw HTTP-response SHA-256;
- normalized evidence-text SHA-256;
- collection timestamp;
- issuer name, SME segment, scrip code and equity-listing statement;
- listing date, market lot and final issue price;
- an offline replay through the existing `verifyListingHtml` identity/fact verifier.

HTML evidence does not invent pagination. Published fields and board/status evidence use `page: null`.

The PDF contract remains strict and separate: PDF-backed entries still require the bounded official PDF URL, document hash, page excerpts, page identity and `verifyListingPdfText` replay.

### Source verification retained

The reviewed HTML evidence came from:

- workflow run: **`35956034085`**
- artifact: **`10789439895`**
- artifact ZIP SHA-256: **`d78e344277d79ccce4411e3a7f4552b3eeb87089e3d584d8a1fa8a5c746d1acb`**

Reviewed manifests:

- `data/verified-bse-listings/2026-09-24-batch5.json` — 2 entries
- `data/verified-bse-listings/2026-09-24-batch6.json` — 5 entries

Exact published facts:

| Issuer | BSE code | Listing notice | Listing date | Market lot | Issue price |
| --- | --- | --- | --- | ---: | ---: |
| ELFIN AGRO INDIA LIMITED | 544724 | `20260311-44` | 2026-03-12 | 3,000 | INR 47 |
| PAN HR SOLUTION LIMITED | 544698 | `20260212-30` | 2026-02-13 | 1,600 | INR 78 |
| KANISHK ALUMINIUM INDIA LIMITED | 544693 | `20260203-43` | 2026-02-04 | 1,600 | INR 73 |
| ACCRETION NUTRAVEDA LIMITED | 544694 | `20260203-44` | 2026-02-04 | 1,000 | INR 129 |
| MSAFE EQUIPMENTS LIMITED | 544695 | `20260203-45` | 2026-02-04 | 1,000 | INR 123 |
| ARITAS VINYL LIMITED | 544683 | `20260122-19` | 2026-01-23 | 3,000 | INR 47 |
| YAJUR FIBRES LIMITED | 544676 | `20260113-25` | 2026-01-14 | 800 | INR 174 |

Unsupported price band, offer dates, monetary issue size, minimum bid quantity and minimum application amount remain null for all seven unless supported separately by another official source.

### Pre-merge validation

Final PR-head validation:

- reviewed BSE evidence/importer validation: **`35956420754`** — success
- full data-contract validation: **`35956420683`** — success
- issuer-specific BSE source diagnostics: **`35956420702`** — success
- protected code-544770 regression/source verification: **`35956420680`** — success

The isolated publication rehearsal used the real importer, publisher and validators:

- **957 -> 964 records**
- exactly **7 additions**
- **35 already-present** reviewed BSE records
- **0 held existing records**
- **0 identity conflicts**
- all **957 existing records unchanged**
- second import/rebuild: **no-op / idempotent**
- total retained reviewed BSE entries after this batch: **42**

### Production publication

Merge-triggered live sync:

- run: **`35956583736`**
- conclusion: **success**
- reviewed BSE import: **7 added / 35 already present / 0 holds**
- semantic publication: **7 added / 36 changed / 0 removed / 0 conflicts**
- schema 1.2.0 validation: **964 records passed**
- operator health: **healthy**

The 36 changed records are normal concurrent official NSE/SEBI enrichment from the same source-first run. The semantic publisher separately identified the seven additions and zero removals/conflicts.

Source-backed data commit:

`40c8326db90e1c8d29d98cc2c998aa88d159742c`

Operator-state commit:

`ad52c686ebfad609aab8e33db686c34e082ce256`

Production after publication:

- **964 total IPO records**
- **80 records for 2026**
- 2026 board coverage: **15 mainboard / 55 SME / 10 unknown**
- all seven new issuers occur exactly once on current `main`
- each retains its reviewed BSE notice URL and document hash
- each verified listing date, market lot and issue price agrees with the reviewed manifest
- HTML-backed field/page metadata remains `page: null`
- unsupported fields remain null
- the four rejected candidates remain absent
- deterministic build and schema validation passed
- operator health: **healthy**

### Deployment

GitHub Pages dynamic build **`35957085010`** completed successfully on:

`ad52c686ebfad609aab8e33db686c34e082ce256`

That commit is one commit ahead of and directly descends from source-backed data commit `40c8326db90e1c8d29d98cc2c998aa88d159742c`, so the deployed Pages revision contains the 964-record release.

The custom `ops/pages-publication.json` snapshot still refers to the merge-triggered deploy attempt because bot-authored data/operator commits do not necessarily re-trigger that custom persistence workflow. The native Pages build above is the authoritative descendant deployment evidence for this data commit.

### Remaining holds

The four rejected candidates from the same historical discovery batch remain excluded:

- AUTOFURNISH LIMITED — `20260527-47`
- RECODE STUDIOS LIMITED — `20260511-16`
- MEHUL TELECOM LIMITED — `20260423-27`
- TIPCO ENGINEERING INDIA LIMITED — `20260330-44`

Current recovery data confirms all four are absent. Do not infer them from SME-index discovery evidence. They require a separate issuer-identity/source repair.

### Next task

Re-read `ops/bse-sme-addition-notices.json` before starting the next run because its scheduled workflow advances independently.

At this handoff the durable cursor is still:

- **40 / 236 parsed**
- **196 unseen**
- next unseen notice: **`20260107-29`**

If the cursor has advanced by the next prompt, reconcile the newest completed cursor discovery batch against the current production universe and verify only genuinely missing/unambiguous issuers with issuer-specific official BSE evidence.

If it has not advanced, keep the cursor independent and use the next bounded P1/P2 batch to investigate the four held issuer/source mismatches. Do not reset the cursor, duplicate the 13 now-published historical records, or infer values from BSE index-addition notices.

## Latest completed batch: six historical BSE SME listings published — PR #175

PR #175 merged as:

`6059dab836760e8d9c658101a3e1e536683bd039`

It completed the safe publishable subset from the first historical discovery reconciliation without weakening the reviewed-evidence importer.

### Why only 6 of the 13 verified candidates were published

The existing reviewed importer intentionally requires an issuer-specific official BSE listing **PDF**, document hash, and page-backed excerpts.

The prior source run had 13 issuer identities that verified through official BSE listing notices, but only 6 had PDF evidence. PR #175 added an opt-in PDF-upgrade probe for already verified HTML notices and tested that behavior without changing the default retry semantics.

Source run:

- workflow: **`35954818300`**
- artifact: **`10789632860`**
- artifact ZIP SHA-256: **`3c312c2077a4e8ddfc170c50aa65ea54874ceb53fbfff813fdd882506f4db99f`**

The PDF upgrade confirmed:

- **6 PDF-backed verified candidates**
- **7 official-HTML verified candidates whose canonical archive PDF path returns HTTP 404**
- the previously identified **4 rejected candidates remain rejected**

The importer was not relaxed. HTML verification was not converted into fake page evidence.

### Reviewed batch 4

Committed manifest:

`data/verified-bse-listings/2026-09-24-batch4.json`

| Issuer | BSE code | Listing notice | Listing date | Market lot | Issue price |
| --- | --- | --- | --- | ---: | ---: |
| M.R. MANIVENI FOODS LIMITED | 544768 | `20260529-40` | 2026-06-01 | 2,000 | INR 52 |
| VEGORAMA PUNJABI ANGITHI LIMITED | 544765 | `20260526-31` | 2026-05-27 | 1,600 | INR 77 |
| GOLDLINE PHARMACEUTICAL LIMITED | 544759 | `20260518-28` | 2026-05-19 | 3,000 | INR 43 |
| SAFETY CONTROLS & DEVICES LIMITED | 544746 | `20260410-44` | 2026-04-13 | 1,600 | INR 80 |
| EMIAC TECHNOLOGIES LIMITED | 544747 | `20260410-43` | 2026-04-13 | 1,200 | INR 98 |
| NOVUS LOYALTY LIMITED | 544735 | `20260324-28` | 2026-03-25 | 1,000 | INR 146 |

Only explicit listing date, market lot and final issue price are retained from the listing PDFs. Unsupported price-band, offer-date, issue-size and application fields remain null unless supported by another official source.

### Pre-merge validation

Final PR workflows:

- reviewed BSE evidence/importer validation: **`35955058014`** — success
- full data-contract validation: **`35955057967`** — success
- BSE candidate/source diagnostics: **`35955057960`** — success
- 544770 regression/source verification: **`35955057944`** — success

The isolated real-import rehearsal measured:

- **951 -> 957 records**
- exactly **6 additions**
- **29 already-present** reviewed BSE records
- **0 held existing records**
- **0 identity conflicts**
- all **951 existing records unchanged**
- second import/rebuild: **no-op / idempotent**
- total reviewed BSE evidence entries after this batch: **35**

### Production publication

Merge-triggered live sync:

- run: **`35955112253`**
- conclusion: **success**
- reviewed BSE import: **6 added / 29 already present / 0 holds**
- semantic publication: **6 added / 37 changed / 0 removed**
- operator health: **healthy**

The 37 changed records are normal concurrent official NSE/SEBI enrichment from the same source-first run; the semantic publisher separately reported exactly 6 additions and 0 removals.

Source-backed data commit:

`fc5e0ec5e6bd9fb3c065544465066827a4005940`

Operator-state commit:

`9c07573b1ca27d48d93724236fbbde30971f11c2`

Production after publication:

- **957 total IPO records**
- **73 records for 2026**
- 2026 board coverage: **15 mainboard / 48 SME / 10 unknown**
- deterministic publication/recovery checks: passed
- schema validation: passed
- operator health: **healthy**

The exact six records are present on current `main` with their BSE scrip codes, verified listing date, market lot, issue price, document hash and batch-4 provenance.

### Deployment verification

GitHub Pages dynamic build **`35955643913`** completed successfully on:

`9c07573b1ca27d48d93724236fbbde30971f11c2`

That revision is a descendant of source-backed data commit `fc5e0ec5e6bd9fb3c065544465066827a4005940`, so the deployed Pages revision contains the six-record release.

A direct HTTP fetch of the deployed JSON could not be performed from this execution environment because external DNS resolution was unavailable. Deployment verification therefore uses the successful descendant Pages build plus exact current-main recovery records and the successful production publication log.

### Remaining seven HTML-verified candidates

These issuer-specific BSE notice pages independently verified identity and listing facts, but the official archive PDF probe returned **HTTP 404** for each:

| Issuer | Listing notice |
| --- | --- |
| ELFIN AGRO INDIA LIMITED | `20260311-44` |
| PAN HR SOLUTION LIMITED | `20260212-30` |
| KANISHK ALUMINIUM INDIA LIMITED | `20260203-43` |
| ACCRETION NUTRAVEDA LIMITED | `20260203-44` |
| MSAFE EQUIPMENTS LIMITED | `20260203-45` |
| ARITAS VINYL LIMITED | `20260122-19` |
| YAJUR FIBRES LIMITED | `20260113-25` |

They are **not published yet**. Their official HTML evidence is retained in the verification artifacts, but the current reviewed importer correctly rejects evidence without the required PDF/page contract.

### Four rejected candidates remain held

Do not publish or infer from the SME-index references:

- AUTOFURNISH LIMITED — `20260527-47`
- RECODE STUDIOS LIMITED — `20260511-16`
- MEHUL TELECOM LIMITED — `20260423-27`
- TIPCO ENGINEERING INDIA LIMITED — `20260330-44`

These remain a separate issuer-identity/source-repair problem.

### Next task

Repair the official evidence path for the **seven HTML-verified / PDF-404** notices.

Acceptance requirements:

- first inspect the exact BSE notice pages for attachment/download URLs or another official BSE document endpoint;
- preserve the already verified HTML response hashes and identities;
- if an official document exists, verify it independently and retain its hash/page evidence before publication;
- if BSE genuinely exposes only HTML, design a **separate reviewed official-HTML evidence contract** that retains URL, notice identity, publication date, response hash, collection timestamp and exact excerpts;
- do not invent page numbers or silently weaken the PDF evidence contract;
- keep the four rejected candidates out of this batch;
- after resolving this source family, return to the independent historical cursor, currently **40/236 parsed with 196 unseen** (next unseen notice remains `20260107-29`).

The historical cursor itself remains independent and must not be reset or coupled to live sync.

## Latest completed batch: first historical BSE discovery reconciliation

PR #174 reconciled the first historical cursor batch from BSE SME addition-notice run **`35952980189`**.

### Reconciliation result

The cursor's next 20 parsed notices produced **23 listing references**. Exact comparison with the current 2026 recovery universe found:

- **6 already present**
- **17 missing exact identities**
- **0 identity-review/fuzzy-match cases**

No index-only candidate was promoted. The reconciliation is retained in:

`data/discovery/bse-listing-reconciliation-2026-09-24.json`

The 17 missing candidates were split to respect the verifier's 15-record safety bound:

- `data/discovery/bse-listing-candidates-2026-09-24-batch4.json` — 15
- `data/discovery/bse-listing-candidates-2026-09-24-batch5.json` — 2

### Issuer-specific source verification

PR source run **`35954077034`** completed both candidate batches.

Final issuer-specific official BSE listing-notice result:

- attempted: **17**
- verified: **13**
- rejected: **4**
- unavailable: **0**

Artifact:

- id: **`10789631977`**
- ZIP SHA-256: **`f493f894524bc666b8652b8726283122e85f87fb00e93d96fc258a7090cc9ad6`**

Batch 5 verified **2/2**. Batch 4 verified **11/15** after the official PDF archive retry.

The four rejected candidates are intentionally held:

| Issuer | Listing notice | Rejection |
| --- | --- | --- |
| AUTOFURNISH LIMITED | `20260527-47` | scrip code missing/mismatch; listing date missing/mismatch; equity-listing statement missing |
| RECODE STUDIOS LIMITED | `20260511-16` | scrip code missing/mismatch; listing date missing/mismatch |
| MEHUL TELECOM LIMITED | `20260423-27` | scrip code missing/mismatch; listing date missing/mismatch; equity-listing statement missing |
| TIPCO ENGINEERING INDIA LIMITED | `20260330-44` | scrip code missing/mismatch; listing date missing/mismatch; equity-listing statement missing |

These are source-verification failures, not permission to infer values from the SME-index notices. Preserve them as unresolved discovery evidence until issuer identity/source repair proves the correct listing notice or bounded parser fix.

### Validation

On the final PR head:

- Validate reviewed BSE listing evidence: **success** — run `35954077035`
- Validate IPO data contract: **success** — run `35954077036`
- Verify BSE listing candidates: **success as a diagnostic collection run** — run `35954077034`; it intentionally retained the four rejected candidates instead of treating them as publishable.

No IPO records are materialized by this PR. Production remains **951 records / 67 records for 2026** until reviewed evidence for the 13 verified issuers is committed and imported.

### Next task

Convert only the **13 verified** results from artifact `10789631977` into reviewed BSE evidence manifests with document hashes/page excerpts, revalidate them offline through the existing importer, then publish those 13. Keep the four rejected candidates held for a separate source/identity repair batch. The independent historical BSE cursor must continue advancing and must not be reset.

## Latest completed batch: BSE 544770 conflict resolved and published

PR #171, **Resolve BSE 544770 identity conflict**, merged at:

`71f0f0c3824269621734e65cdd0e4abfe0c097bc`

The retained discovery conflict is now resolved by issuer-specific official BSE listing notices:

- **YAASHVI JEWELLERS LIMITED** — BSE Listing Notice `20260601-25` independently confirms **scrip code 544770**, listing date **2026-06-02**, market lot **1,600**, and final issue price **INR 83/share**.
- **MERRITRONIX LIMITED** — BSE Listing Notice `20260605-37` independently confirms **scrip code 544773**, listing date **2026-06-08**, market lot **1,000**, and final issue price **INR 149/share**.

The older BSE SME index-addition notice `20260608-14` had associated Merritronix with `544770`. That claim is preserved as **superseded discovery evidence** rather than silently deleted or selected by recency. Yaashvi's earlier index notice `20260602-17` and its listing notice both support `544770`.

### Conflict/source verification

The first conflict probe intentionally used the original index-derived identities separately:

- Merritronix candidate `544770` was **rejected only for scrip-code mismatch**, with the issuer-specific PDF observing `544773`;
- Yaashvi candidate `544770` was **verified**.

The corrected two-record batch then verified **2/2**, with 0 rejected and 0 unavailable.

Successful corrected source run:

- workflow: `35950849004`
- artifact: `10787659263`
- artifact SHA-256: `f969117ce1895c8d9d17f5b3ba2a2dfe91640f5f71367898c65f330520c04e21`
- Merritronix PDF SHA-256: `920101f48760a903cf0f41424f0df00077cd2f85987feed8fe3f91244b9bf0be`
- Yaashvi PDF SHA-256: `22e26ebf183205834b468993d4441d5eea66a14e2c775464e70c05eed2f37dfd`

Retained inputs/evidence:

- `data/discovery/bse-listing-conflict-544770-merritronix.json`
- `data/discovery/bse-listing-conflict-544770-yaashvi.json`
- `data/discovery/bse-listing-candidates-2026-09-24-batch3.json`
- `data/verified-bse-listings/2026-09-24-batch3.json`
- `.github/workflows/verify-bse-544770-conflict.yml`

Batch 3 retains Merritronix's original index claim and the issuer-specific correction in machine-readable form. Only explicit issuer-specific listing-date, market-lot and final-issue-price facts are publishable.

### Pre-merge validation

All three PR workflows passed on the reviewed batch:

- conflict/source verification: `35950980614`;
- reviewed BSE evidence/importer validation: `35950980623`;
- full data-contract validation: `35950980645`.

The isolated publication rehearsal measured:

- **949 -> 951 records**;
- exactly **2 records added**;
- **27 already-present** reviewed BSE records;
- **0 existing records changed by the BSE importer**;
- **0 held conflicts**;
- second import/rebuild: **no-op / idempotent**.

### Production publication

Merge-triggered live sync:

- run: **`35951056853`**
- conclusion: **success**
- reviewed BSE import: **2 added, 27 already present, 0 holds**
- semantic publication: **2 added, 31 changed, 0 removed**

The additional changed records are normal concurrent NSE/SEBI enrichment from the same source-first run; semantic merge reported zero conflicts.

Source-backed data commit:

`6221738a93158e5831c524d4bc8883103492cce5`

Production after publication:

- **951 total IPO records**
- **67 records for 2026**
- 2026 board coverage: **15 mainboard / 42 SME / 10 unknown**
- 2026 verified issue price: **49**
- 2026 verified market lot: **55**
- 2026 verified listing date: **49**
- deterministic recovery build: passed
- schema 1.2.0 validation: passed
- operator health: **healthy**

The production diff shows both new records retaining page-2 BSE evidence, document hashes, collection times and batch-3 provenance. Unsupported raw terms remain null: price band, offer dates, INR issue size and minimum bid quantity are not inferred.

### Deployment

The source-backed data commit was followed by operator-state commit `cf04c69179cd5935e8b04d212d56cc20360f7d40`. GitHub Pages build **`35951543912`** completed successfully on that descendant revision, so the deployed Pages artifact includes the 951-record dataset and both resolved records.

This conflict is **closed**. Do not re-open it from index evidence or change Merritronix back to `544770`.

## Latest completed batch: remaining 12 verified BSE SME listings

PR #168, **Verify and recover remaining 12 BSE SME listings**, merged at:

`39ead2287b9352953d43b24ec9a006ab21f0d72a`

This batch completed the remaining unambiguous issuer references from the original 29-reference BSE SME addition-notice report. Together with PR #166's first 15 records, **27 independently reviewed BSE listing records from that report are now retained and published**.

The two disputed code-`544770` references remain excluded:

- MERRITRONIX LIMITED — referenced listing notice `20260605-37`
- YAASHVI JEWELLERS LIMITED — referenced listing notice `20260601-25`

Do not choose one by recency, name similarity or last-wins logic.

### Batch-2 source verification

Pinned input:

`data/discovery/bse-listing-candidates-2026-09-24-batch2.json`

Successful issuer-specific source verification:

- workflow run: `35946970931`
- attempted: **12**
- verified: **12**
- rejected: **0**
- unavailable: **0**
- artifact: `10787446306`
- artifact SHA-256: `4d93a865acc52cebd8b57e6d00668b722b6182c79aa8d2b874b9864dc57e1863`

The artifact contains all 12 official BSE listing PDFs plus the verification report. Exact reviewed evidence is retained in:

`data/verified-bse-listings/2026-09-24-batch2.json`

Only explicit issuer-specific PDF facts are retained:

- listing date;
- market lot;
- final issue price.

No price band, offer dates, monetary issue size, minimum bid quantity or application amount is inferred.

### Reliability repairs in PR #168

The batch also repaired two reusable verifier issues:

1. **PDF rejection classification**
   - a successfully downloaded official PDF that fails identity verification is now classified as `rejected`, not left as `unavailable`;
   - HTML-attempt metadata is preserved separately.

2. **BSE PDF ligature text**
   - Leapfrog Engineering Services' official PDF extracts `effective` as `e ective`;
   - the listing-date grammar now accepts only that bounded PDF-text form in addition to normal `effective from`;
   - `Effective at the open ...` remains rejected so index-admission dates cannot become listing dates.

The first post-fix run demonstrated the distinction: an earlier run produced 11 verified + 1 rejected; after the bounded ligature repair the same source family produced 12/12 verified.

### Multi-batch reviewed importer

`scripts/apply-verified-bse-listings.mjs` now loads multiple approved manifests under `data/verified-bse-listings/`.

For every batch it still:

- revalidates committed page excerpts and PDF facts;
- requires the matching approved discovery batch;
- uses no network in the live import step;
- creates missing records only;
- never overwrites an existing or conflicting identity;
- preserves field/source hashes, page evidence and collection timestamps;
- remains idempotent on rerun.

PR validation passed for both the reviewed-evidence importer and the full data contract.

## Production publication verification

Merge-triggered live sync:

- workflow run: **`35947297162`**
- conclusion: **success**
- reviewed BSE import step: **success**
- semantic publication: **success**

The live workflow measured:

- `added_records: 12`
- `changed_records: 27`
- `removed_records: 0`

The additional changed records came from the normal concurrent NSE/SEBI historical/live enrichment in the same source-first run; the semantic merge preserved those concurrent changes.

Source-backed data commit:

`1d7ffff145b99cf045b6954028d595105a1522fb`

Production build after semantic merge:

- **949 total published IPO records**
- **65 records for 2026**
- schema/core validation: passed
- deterministic recovery build check: passed
- operator health at completion: healthy

The prior production state had 53 records for 2026, so this batch accounts for exactly the expected **+12**.

The 2026 recovery diff retains batch-2 provenance through:

`data/verified-bse-listings/2026-09-24-batch2.json`

and shows unsupported raw terms such as price band, open/close dates and minimum bid quantity remaining null for these new BSE-only records.

### Deployment

GitHub Pages build `35947797703` completed successfully on commit:

`1d92710098fcf9b492a572eb6424e2c434153e93`

That commit is a descendant of the source-backed data revision `1d7ffff145b99cf045b6954028d595105a1522fb`, so the deployed Pages build includes the 12 newly published BSE records.

### Independent live-data check and release safeguards — PR #167

The live dataset itself was fetched after publication at **2026-09-24T02:36:18.996Z**, separately from dataset generation time **2026-09-24T02:31:21.345Z**. This was not merely a check that a Pages job was green.

The retained live snapshot contains **949 records**. Each of the **27 issuers and 81 listing-date/market-lot/issue-price fields** across both reviewed batches was compared with the committed evidence: every issuer appears once, every value agrees, every field is verified and retains the corresponding official PDF URL and page 2. Both held issuers remain absent. All six unsupported fields in the 12 new records remain null/missing: price band, open date, close date, INR issue size, minimum bid quantity and minimum application amount. The actual live snapshot also passes the schema 1.2.0 core validator.

PR #167 merged at `3a89120f498f18e54fcd1b26340cf090446e22fe`. During its independent verification, PR #168 reached main with the same 12 issuers. GitHub correctly blocked the stale merge. The final reconciliation preserves #168's canonical `batch2` manifests, importer, PDF rejection classification and ligature repair unchanged. The alternative unmerged `batch-02` manifests and approval-registry implementation were dropped from the PR diff, never added to production. Do not reintroduce that superseded alternative or duplicate the 12 records.

The final #167 change is restricted to:

- `scripts/test-bse-publication-rehearsal.mjs`: an isolated run of the real importer, publisher and validators, proving existing public records are unchanged, unrelated yearly manifests are byte-identical and a second import/rebuild causes no timestamp churn;
- `.github/workflows/validate-reviewed-bse-listings.yml`: runs this end-to-end rehearsal before merge;
- `.github/workflows/verify-bse-listing-candidates.yml`: retains a tracked-source ZIP for reproducible tests and a separately timestamped deployed-data snapshot in the existing read-only artifact. No permission expansion or new PDF work inside hourly sync.

All **34 reconciled local test scripts** passed using the actual repository modules, without matcher substitutes. The publication rehearsal measured **937 -> 949**, exactly 12 added and 15 already present, with all 937 pre-existing public records unchanged and a no-op second import. Production's normal NSE/SEBI enrichments in the same sync are distinct from this isolated no-overwrite test.

All three final PR workflows passed: data-contract CI `35947529604`, reviewed-evidence CI `35947529606`, and independent source verification `35947529605`. Post-merge data-contract `35947640996` and reviewed-evidence `35947640921` also passed.

Independent source verification `35946186883` had already checked the same 12 original PDFs; all 12 document hashes and all 36 values/pages agree with the preserved canonical batch. All 24 header/fact pages were rendered and reviewed. Reconciled source run `35947529605` and its post-publication attempt 2 both verify 12/12, with 0 rejected/unavailable.

#### Reproducible evidence retention

The post-publication artifact is `bse-listing-verification-35947529605-2`, ID **10787263725**, from attempt 2. It retains the original listing PDFs, HTML attempts, verification report, tracked-source ZIP and actual deployed-data snapshot.

- ZIP SHA-256: `22dd81e6868e8907184e5efe8089aba00ce674ff7b2cd160d2ddd98ac20aabb6`
- Deployed snapshot-file SHA-256: `5c7f4df154afe0ed14db78ae2157575e93c9308f3ee00c1cfa23d44e71cd444f`
- Artifact expiry: `2026-10-08T02:36:37Z`
- A copy of this artifact and the machine-readable 27-record/81-field live-check report were retained in the conversation.

The independent pre-reconciliation source artifact remains available as ID `10787195768`, run `35946186883`, ZIP SHA-256 `8a0a777a7c29dfef19da9e6549aa1f626b070dccfae6d395333e8d6e294b9612`. Its source ZIP is an earlier revision, not the final reconciled implementation.

This release is **verified live**. Do not repeat the first 15 or remaining 12 listing imports or their completed ligature/source-delivery diagnoses.

## Reviewed batch-2 facts

| Issuer | BSE listing notice | Listing date | Market lot | Issue price (INR/share) |
| --- | --- | --- | ---: | ---: |
| Crazy Snacks | 20260702-44 | 2026-07-03 | 3,000 | 42 |
| Liotech Industries | 20260623-33 | 2026-06-24 | 400 | 321 |
| Leapfrog Engineering Services | 20260623-30 | 2026-06-24 | 6,000 | 23 |
| Diksha Polymers | 20260623-31 | 2026-06-24 | 1,200 | 112 |
| Horizon Reclaim (India) | 20260618-28 | 2026-06-19 | 1,200 | 103 |
| Susan Electricals India | 20260617-35 | 2026-06-18 | 1,000 | 127 |
| Vahh Chemicals | 20260610-34 | 2026-06-11 | 2,000 | 60 |
| UHM Vacation | 20260610-44 | 2026-06-11 | 800 | 166 |
| SMR Jewels | 20260605-45 | 2026-06-08 | 1,000 | 128 |
| Aureate Tradde | 20260604-33 | 2026-06-05 | 2,000 | 70 |
| Rajnandini Fashion India | 20260602-37 | 2026-06-03 | 2,000 | 63 |
| Harikanta Overseas | 20260601-23 | 2026-06-02 | 1,200 | 91 |

## Release reliability follow-up: Pages publication-state race

During final handoff publication, GitHub Pages deployment for README commit `ad62e44ad85c60a0910a6df1e9212349f559c0bc` itself succeeded, but workflow run `35948066974` ended red because its final `ops/pages-publication.json` commit conflicted while rebasing over another Pages-health update.

PR #169 repaired only that operational-state race:

- merge commit: `180087143d3fb986d0413c62c2fdb5a2da69909f`;
- the workflow now resets to the latest `origin/main`, recomputes Pages state against the newest committed state, validates the operational schema, and retries the push up to three times;
- CI forbids returning to the old "modify JSON then rebase" pattern.

Production deployment run `35948287263` completed **successfully**, including the formerly failing status-persistence step. Durable Pages state was committed as `45b2f22a4f5d3a7b8416133a0b7eeab6fc580b5a` and records:

- deployment status: success;
- deployed commit: `180087143d3fb986d0413c62c2fdb5a2da69909f`;
- completion: `2026-09-24T02:41:40Z`;
- page URL: `https://vasuki8.github.io/IPO-Tracker/`.

This was an operational metadata repair only; no IPO value or recovery evidence was changed.

## Completed: durable historical BSE notice cursor — PR #173

PR #173 merged at `2dcd60597c0fb8995a446efa00199138034b1603`.

The BSE SME addition-notice backfill is now independent, bounded and durable:

- operational state: `ops/bse-sme-addition-notices.json`;
- parser version: `1.1.0`;
- maximum batch: **20 notices**;
- schedule: every two hours, independent of the live IPO critical path;
- state is keyed by BSE notice ID, not positional offsets, so new notices do not shift historical progress;
- parser-version changes requeue earlier notices deterministically;
- unseen notices advance before retries so a failed notice cannot block the older backlog;
- failed/fetch-error/unparseable notices remain in state with attempt timestamps and are retried after cooldown;
- semantic state publication resets to latest main, merges notice-by-notice and retries pushes without rewriting IPO values.

The newest 20 successful notices were bootstrapped from retained audit run `35939161246`, artifact `10783988662`, rather than being fetched again. That bootstrap represents 29 previously reviewed discovery references and remains operational state only.

### First production historical batch

Merge-triggered workflow run:

- run: **`35952980189`**
- conclusion: **success**
- report artifact: **`10788684195`**
- artifact SHA-256: `1dde2b06eb2ce178800e6fc382895b1ad57b7458be3077e3f46098c0a248b544`
- state commit: **`6a8a21ce8c0befea1a3c67911472c3aff731c7f1`**

Observed progress:

- eligible notices: **236**
- before: **20 parsed / 216 unseen**
- selected: **20 older notices**
- parsed: **20/20**
- fetch errors: **0**
- unparseable: **0**
- new discovery references: **23**
- after: **40 parsed / 196 unseen**
- next unseen notice: **`20260107-29`**

The batch moved from the June 1, 2026 notice backward through January 13, 2026. Some older notices lacked a direct catalog PDF URL and were parsed through the existing official BSE Index Services detail endpoint; that fallback remains source-labelled in cursor state.

**Important:** these 23 references are discovery candidates only. This workflow never creates or edits IPO records. Every candidate still requires issuer-specific official BSE listing evidence before materialization.

## Next task: reconcile the first historical discovery batch

The next bounded P1/P2 task is to compare the **23 newly discovered references** from run `35952980189` against the current **951-record** production universe and retained BSE evidence.

Acceptance requirements:

- separate already-present issuers from genuinely missing candidates;
- retain exact index notice identity, listing-reference notice number, scrip code, listing date and source hash;
- never infer equivalence from fuzzy names when identity is ambiguous;
- for missing/unambiguous issuers, verify issuer-specific official BSE listing notices in a bounded batch before publication;
- preserve null unsupported fields;
- do not stop or reset the new historical cursor—the independent scheduled backfill should continue advancing the remaining **196** notices.

## Prior handoffs

- First reviewed 15-record BSE listing batch: `archive/PROJECT_STATUS-before-bse-listing-batch2.md`
- PR #165 discovery/notice-repair state: `archive/PROJECT_STATUS-before-bse-listing-batch.md`
- Older accumulated milestones remain under `docs/archive/`.

Current repository, workflow and deployment evidence supersede stale next-task instructions in archived handoffs.
