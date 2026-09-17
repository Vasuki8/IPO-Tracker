# P4 repair integration and source-acceptance recovery

Evidence checked on 17 September 2026. This note records code integration and
the remaining release gate; it does not accept a source-preview dataset or
invalidate an earlier review because its working files are unavailable.

## Preserved work and verified checks

The accepted public release was on main
`cf906df7ccc9bcf40881743b0af39480858a612e`. Its Pages deployment
[35280338567](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35280338567)
and live acceptance
[35280386203](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35280386203)
succeeded. The trust/freshness presentation and release verification from
#100–#103 must survive subsequent repairs.

| Work | Exact head | Evidence |
|---|---|---|
| [#94](https://github.com/Vasuki8/IPO-Tracker/pull/94): composition/parser and six reviewed allocations | `4707df1e82337e3a7b8bac0838bbaa30c3d200be` | [35264712036](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35264712036): 976 regression tests passed |
| [#98](https://github.com/Vasuki8/IPO-Tracker/pull/98): correction-policy/source-commit guard | `d5e5d0580360a87dffc35b69e674886848b55005` | [35268841225](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35268841225): 993 passed; 987 belonged to its earlier commit |
| [#99](https://github.com/Vasuki8/IPO-Tracker/pull/99): Kaytex/SPEB holds and preview correction ordering | `a503531ded368c4eb53ba09cf5c2aafef3391c38` | [35271722104](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35271722104): 979 passed |
| [#105](https://github.com/Vasuki8/IPO-Tracker/pull/105): combined integration, still draft | `54054c0e05d44c03260ddc84950c82d0bf6172bd` | Tree `162b4291e6877ba84898b426d9d6bd5f0b592d0f`; 1,023 local frozen Python 3.12 regressions and [35281606697](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35281606697) passed |

The CI counts above were checked in job logs. Each validation run also passed
JavaScript syntax, generated public payloads, reviewed corrections and compact
support-artifact checks, with zero strict errors. The integration CI used Python
3.12.14 and `uv sync --frozen`. These checks do not prove every source value.

#105 preserves the three repair heads as commit parents and removes its temporary
recovery workflow. Its integration leaves canonical `data/ipos.json`, retained
`data/pending_updates.json`, public display holds and existing public renderers
unchanged. #104 remains a separate recovery-only draft at
`5700a6614326ff259a8ffe07cc49be15494785a8`; do not duplicate its integration effort.
The original #94/#98/#99 branches remain intact.

The #99 source preview
[35271722183](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35271722183)
completed successfully; its older PR text saying it was running is stale. #105's
new preview [35281606917](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35281606917)
was still running when checked. Neither preview is a targeted accepted release.

## Missing acceptance transport

The surviving [#99 source-review handoff](2026-09-17-additional-source-holds.md)
identifies an immutable seven-record proposal by SHA-256:

```text
5516b3ad6ba4345abc25d7a9b2771eb5c3b32f00e9163f30167da9d6b80cf6f6
```

Its payload, original data-base binding and transport containing
`acceptedCodeCommit` / complete `acceptedCodeFiles` were not recovered from the
accessible repository refs, prior working files or saved-file inventory. The
surviving Emmvee-only rehearsal used 1,365 records and base `cebbba4945cb7e5698cb36ce371da839e8dd2ab9`;
it cannot substitute for this 1,366-record proposal. Missing recovery material is
not evidence that the original review was incorrect.

The [#94 release condition](https://github.com/Vasuki8/IPO-Tracker/pull/94#issuecomment-5720530310)
remains unmet: a current-base targeted bundle must show these seven records only,
matching source proofs, preserved other records/history, regenerated public pages
and deployed verification:

- `emmvee`: fresh issue ₹2,143.862 crore, OFS ₹756.138 crore, total ₹2,900 crore;
  preserve the existing allocations and their evidence.
- `teamtech`: four actual net-proceeds allocations totaling ₹45.4859 crore.
- `unimech`, `blackbuck`, `mbel`, `shriahimsa`, `genxai`: preserve the continuing
  allocation holds, previous values, source evidence and correction history.
- Preserve Kaytex/SPEB safeguards. Both fields are null in the recorded proposal.

The old broad source-preview artifact `10518025304` from run `35264712051` has ZIP
SHA-256 `e0317f82f2de23d55a0e232decfdf89c25654c48f49a88c492f987771b394a66`.
Its raw IPO member hashes to
`8647648fe07fcb03dbf074d62eb3f8304d220047365bc4df98ad12d63ad149e8`.
It still contains the old Emmvee composition and no Teamtech allocation repair;
the green run must not be promoted wholesale.

## Source identities for renewed acceptance

Complete retained PDFs were recovered and SHA-256 verified for the first five
rows below. Their local recovery paths are deliberately not treated as durable
dependencies. The last two rows retain source identities and committed excerpts,
but complete PDF bytes were not recovered by this investigation.

| Issuer | Official source | PDF SHA-256 |
|---|---|---|
| Emmvee | [Final Prospectus](https://nsearchives.nseindia.com/corporate/FP_INE1C6T01020_14NOV2025.pdf) | `85eb9319dc01027821813c71d3702164911442a14547ad72cc04270ea6612eda` |
| Teamtech | [Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/TeamtechFormworkSolutionsLimited_PROSP.pdf) | `985909fbad119ffa02604f6fbb2895387a98d817a1fa8b486a7806ac18b537e8` |
| Unimech | [Final Prospectus](https://nsearchives.nseindia.com/corporate/FP_INE0U3I01011_30DEC2024.pdf) | `b10afca3e64e8731dd4c4660a99ec720c8f0ec4fa4eb0b524ab441717977cfd3` |
| M&B Engineering | [Final Prospectus](https://nsearchives.nseindia.com/corporate/FP_INE08N601015_04AUG2025.pdf) | `e20a311a4d4473a5ee93a683023f831e009a6910524a9044f48d367acf513219` |
| Blackbuck | [Final Prospectus](https://www.sebi.gov.in/sebi_data/attachdocs/nov-2024/1732249559904.pdf) | `0a6837d67b0d5b91c5ca9d9f6527c155fc28f9cad4e8654bba803b60c438007b` |
| Shri Ahimsa | [Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/ShriAhimsaNaturalsLimited_PROSP.pdf) | `eb9fd3588990048a03f5c8602406a45020bebe158f6aa566fd4c028d746177b0` |
| GenXAI | [Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/GenXAIAnalyticsLimited_PROSP.pdf) | `c810471e52810eaf6ffb7f023b359b82702c486694af19f086dac8b89c0163b0` |

Physical-page context is recorded in
`tests/fixtures/objects-source-acceptance/README.md` on #105. Reacquired bytes must
match their recorded hashes or be reviewed as a new document. Fixture regressions
alone cannot establish full-document consistency.

## Next bounded milestone and release gate

Merging #105 changes parser/registry paths. `publication_mode.py` selects `repair`
for such a push, and `refresh.yml` then runs broad collection plus residual repairs
before automatic publication. A seven-record local rehearsal does not establish
acceptance of all those additional changes. Keep #105 draft until both targeted
source acceptance and the resulting publication scope are reviewed. A separate
presentation-only document-hold fix can proceed without changing canonical data;
integrate its accepted public protection before the final repair freeze.

1. Reconcile #105 with then-current main and freeze the combined code SHA/tree.
   Capture the canonical base SHA/hash, pending proposals and seven exact record
   identities before source work in an isolated checkout. Preserve current main
   changes; do not reset accepted data to an old preview.
2. If the original proposal is recovered, verify its hash and original base before
   using it, then regenerate the documented code manifest after fresh acceptance.
   Otherwise create a **new acceptance lineage** from current code, current base
   and exact source bytes. Record the unrecovered prior hash as history; do not
   claim the new bytes preserve it or rewrite an old collector's source SHA.
3. Use existing extraction, canonical-policy and reviewed-correction functions on
   copies of the selected records. Validate issuer/offer identity, full document
   context, units, physical spans and complete evidence. Review every changed
   field; bound the accepted replacement set to the seven named IDs and intended
   fields. Preserve unrelated records, metadata, evidence and audit history.
4. Rehearse existing three-way publication against the current accepted data and
   retained pending proposals, supplying a freshly generated source-commit file.
   Source-policy changes must invalidate stale bundles. Review conflicts instead
   of choosing a newest writer, and document any scope beyond the seven repairs.
5. Rebuild and verify all public projections, then complete the existing PR,
   source-review and publication checks. Verify deployed canonical target values
   and proofs as well as public pages. Keep P4 incomplete and P5/performance gated.

The following commands support verification in that isolated acceptance checkout;
the source reconstruction and scope review above remain separate required work:

```sh
uv python install 3.12
uv sync --frozen
uv run --frozen python -m unittest discover -s tests -q
node --test tests/public_quality.test.cjs
uv run --frozen python scripts/validate_data.py --strict
uv run --frozen python scripts/build_company_pages.py
uv run --frozen python tests/verify_public_release.py --expected-commit "$(git rev-parse HEAD)"
```

For deployed acceptance, run the same verifier from the immutable deployed
checkout with `--base-url https://vasuki8.github.io/IPO-Tracker/`. This verifies
artifact consistency, not source correctness; retain the separate seven-record
source receipt and field-proof/history comparisons. No new general writer,
approval bypass, paid infrastructure or unattended task is introduced by this note.
