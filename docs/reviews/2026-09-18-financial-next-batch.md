# Next bounded financial source batch - selection only

The selection snapshot below is preserved. Subsequent bounded inspection is
complete in [the source diagnosis](2026-09-18-financial-seed-inspection.md) and
its exact JSON receipt. No financial values were accepted. The current next action
is to reproduce the two layouts with production `pdftotext`, then implement and
source-review the shared bounded repair; do not repeat the initial selection or
treat the local pypdf replay as production extraction parity.

Read-only triage of canonical main `26894686`, before the pending intermediary
publication. Local `data/ipos.json` and `data/validation.json` exactly match that
commit's Git blobs `a147ee8880e7470e1a5269103ff66da3bce95b24` and
`bb3e30edb42ca99f95ed1297ee8b8e424476e0e7`. No financial source was downloaded or
accepted for this selection, and no canonical value or review was changed.

## Counts and recurring patterns

There are **1,299 financial review items on 135 issuers**: 1,026 P4 items, 258 P2
items and 15 P3 items. These are field-level reviews, not 1,299 missing records.

| Review reason | Items | Issuers |
| --- | ---: | ---: |
| Source tables disagree; conflicting metric excluded | 702 | 111 |
| Source table/period evidence has not been revalidated | 570 | 34 |
| Possible percentage-to-currency contamination | 27 | 9 |

Issuer sets overlap. The 702 conflicts concentrate in revenue (198), PAT (155)
and net worth (116). Repeated conflict signatures include revenue alone (20
issuers / 52 items), revenue plus PAT (12 / 58), and PAT alone (11 / 26).
`offerDocumentExtraction.conflicts` retains metric paths, not both competing
physical source rows; these signatures do not prove a common document defect.

A more concrete starting pattern is **net worth equal to one tenth of RoNW in
all three retained periods** for nine issuers: `aye`, `cleanmax`, `dhoottrans`,
`htel`, `jnpr`, `kissht`, `manipalhos`, `mvelectro`, `pngsreva`. They have 240
financial review items in total, including the 27 contamination flags.

The legacy recognizer's unanchored `Net Worth`/`Networth` patterns can match
inside `Return on Net Worth`, and `_series_near_label` takes the next numbers
within a 950-character window before converting currency metrics. This is a
plausible shared historical cause of the 0.1 ratio and stray dates/share counts
in EPS. It is **not proven source lineage for these exact records**. The current
strict parser already anchors metric rows and preserves annual-column/scope
evidence; its failure to recover these documents must be diagnosed separately.
Do not relax it or restore the legacy recognizer.

## Selected seed: Hy-Tech and Onemi; bounded third-document extension

| ID / issuer | Priority | Reviews | Retained Final Prospectus / filing-date field / complete pages |
| --- | --- | ---: | --- |
| `htel` / Hy-Tech Engineers Limited | P2 | 21: 18 unvalidated + 3 contamination | [SEBI PDF](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787913136327.pdf), 2026-08-28; 416/416 |
| `kissht` / Onemi Technology Solutions Limited | P4 | 21: 18 unvalidated + 3 contamination | [SEBI PDF](https://www.sebi.gov.in/sebi_data/attachdocs/jun-2026/1781763357383.pdf), 2026-05-06; 464/464 |
| `pngsreva` / PNGS Reva Diamond Jewellery Limited | P4 | 18: 15 unvalidated + 3 contamination | [SEBI PDF](https://www.sebi.gov.in/sebi_data/attachdocs/mar-2026/1772433551022.pdf), retained document date null; 477/477 |

All three retain no financial field evidence and no parser financial-conflict
paths. Existing extraction covered their complete page counts, so increasing
the 520-page limit is not a supported remedy. Their financials are populated;
each instead has `provenance.finalProspectus.financials` queued. Onemi has no
other missing-field queue entry in this baseline, making complete supported
financial revalidation particularly useful. That is not a promise that its
entire P4 record will clear after independent validation.

Examples of the diagnostic signature, **not accepted financial facts**: Hy-Tech
retains net worth 2.024 with RoNW 20.24 and EPS 83,531,840; Onemi retains net worth
2.118 with RoNW 21.18 and another period's EPS 2023; PNGS retains net worth 1.673
with RoNW 16.73 and another period's EPS 2024. Never repair those by reversing
the suspected arithmetic, substituting dates, or guessing a period order.

Source hashes to revalidate before using any downloaded bytes:

- `htel`: `80e725bfa930875a995043c3dd1ede119446a03653e7baaccf9fe84f53670839`
- `kissht`: `2bde179647fe3c68c86079da1269657c0002e2c4515119b3527f5223bb5dbb19`
- `pngsreva`: `99cedc3c1c9db3bb8b2eba984864705998aaceb562db5d0e38408d6f2019517b`

## Exact next action and acceptance boundary

Download only the two seed Final Prospectuses, verify hashes/complete page trees,
issuer/offer identity and cover dates, then locate and render their annual summary
and underlying restated tables. Retain every competing candidate's physical
page, exact row/header spans, reporting dates, monetary units, annual/interim
columns, standalone/consolidated scope, and basic/diluted EPS basis. Diagnose why
the strict parser returned no financial evidence. Add PNGS only if it proves the
same repair family; first recover its null document date from the actual cover.

Implement one shared bounded layout repair only after two real documents prove
the same cause. Existing `test_financial_source_layouts.py` and
`test_source_table_columns.py` cover annual/interim alignment, currency units,
scope and EPS distinctions. Their ESDS/Jindal/NSE excerpts are **abridged
prospectuses**, useful regression context but not Final Prospectus authority for
this batch. New fixtures need these exact final source identities and negative
cases for RoNW-as-net-worth, year/share-count-as-EPS and conflicting source rows.

The two-seed exposure is 42 reviews; all three expose 60. Neither figure is a
predicted removal: accept only recovered matching cells and retain unresolved
metrics/nulls/history. Use the existing bounded reviewed publication, verify
unchanged unrelated records/proposals and public projections, and measure the
actual post-publication gate. This work excludes #105's objects/composition
draft, P5 and performance expansion.
