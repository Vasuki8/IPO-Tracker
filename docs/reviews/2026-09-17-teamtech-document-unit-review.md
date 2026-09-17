# Teamtech use-of-proceeds source-unit review

Reviewed 17 September 2026 at 23:37:16 UTC. **Keep Teamtech's allocations under
document-level review.** Reconstructing the complete four-purpose table does not
resolve an explicit monetary-unit conflict elsewhere in the same prospectus.

The source is Teamtech Formwork Solutions Limited's
[22 May 2026 Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/TeamtechFormworkSolutionsLimited_PROSP.pdf),
for the offer opening 19 May 2026, symbol `TEAMTECH`. The inspected PDF has 372
pages, 8,669,697 bytes and SHA-256
`985909fbad119ffa02604f6fbb2895387a98d817a1fa8b486a7806ac18b537e8`.

## Conflicting evidence

Physical and printed page numbers agree for the pages cited below.

| Pages | Observed disclosure | Implication |
| --- | --- | --- |
| 22-23 and 87 | Gross proceeds 5,014.80 lakh less issue expenses 466.21 lakh equals net proceeds 4,548.59 lakh. The four allocations total that same net amount. | These tables express the net budget as 45.4859 crore. |
| 88 | The deployment schedule repeats the net-proceeds funding scope and lakh units. | It corroborates the earlier lakh budget. |
| 89 | In the means-of-finance table, the numeric column is explicitly headed **Amount in Crores**. Both **Net Proceeds** and the total are 4,548.59. | The same net-proceeds budget has a stated scale 100 times the earlier tables. The header is visibly attached to this column. |

The share count, issue price and repeated lakh tables strongly suggest a mistaken
header on page 89. That remains an inference. The inspected material does not
explicitly correct or supersede the contradictory unit; publication must not
silently choose one source statement.

The broader review also recorded a secondary quotation discrepancy: page 90 gives
1,192.36 lakh for machinery quotations, while the seven items and printed subtotal
on pages 91-92 total 1,192.35 lakh. This is supporting project-cost context,
not a separate IPO allocation. The earlier project-cost-table rejection remains
valid. Neither finding authorizes a replacement estimate or adjusted allocation.

## Reconstruction and review coverage

All 372 pages were extracted and searched in two Poppler layouts, including the
canonical parser layout; no page-limit truncation occurred. Detailed text review
covered the cover, summary, objects section and relevant cross-references. Visual
inspection focused on physical pages 87-92, following the PDF review workflow;
it was not a visual inspection of every page.

The strict objects extractor ran directly on the complete canonical-layout text.
It returned four rows of 11.9235, 15.5, 13.7688 and 4.2936 crore, totaling 45.4859
crore, with retained physical source evidence and no structural problems. It
selected the page 23 allocation table and page 22 reconciliation. Its table
checks did not detect the page 89 contradiction. The whole Final Prospectus
adapter was not run in that independent review environment.

The rejected candidate's actual rows and complete proof are retained in
`tests/teamtech_unaccepted_objects.json`. The file records the source PDF identity,
full-text digest, extractor/checker digests and original result digest. Those
extractor/checker bytes match immutable code commit
`54054c0e05d44c03260ddc84950c82d0bf6172bd` on the unmerged #105 repair branch.
The canonical-layout text SHA-256 is
`7d89661142c20549eb85ac9361cb60d1acd21423cd7d41a5ccaf93488906229e`;
the original parser-result JSON SHA-256 is
`4bc76a8382011fb77d39cda96904ef79629e82c601256c2a5b33f25c52d724b5`.
The regression constructs only a test record envelope around this unaccepted
extraction; it does not create an accepted canonical correction.

## Public protection and remaining work

Teamtech's public display hold now binds its exact issuer/offer identity, matching
field-proof issue date, and the reviewed PDF hash. It covers the original rejected
project-cost list and later allocation extractions from the same document,
including mirrored URLs. A different document hash still passes through ordinary
source-evidence rules. Emmvee and Unimech retain their value-scoped layout holds;
the six other existing document-scoped holds remain intact.

This change affects public projection only. Canonical values, correction history,
retained proposals, parser versions and the P4 gate remain unchanged. The earlier
seven-record acceptance plan must be revised before publication: Teamtech's
45.4859-crore candidate is unaccepted. Reconcile its source units through a
corrected authoritative disclosure or explicit source supersession, and update
the isolated canonical review registry before reconsidering that repair.
