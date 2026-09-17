# Kaytex and SPEB source reviews

The [PR #94 source preview](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35264712051)
completed successfully at code commit `4707df1e82337e3a7b8bac0838bbaa30c3d200be`.
Independent inspection found two unresolved disclosures outside the separately
accepted seven-record repair. The new allocation lists have valid retained spans,
units and arithmetic; omitted source context prevents accepting those lists.

| Issuer | Exact source context | Review |
|---|---|---|
| [Kaytex Fabrics](https://nsearchives.nseindia.com/emerge/corporates/content/KaytexFabricsLimited_PROSP.pdf) | Physical PDF 115, printed 110, states issuer Fresh Issue net proceeds of ₹47.6186 crore immediately above a table giving ₹49.3465 crore. The table subtracts ₹8.2391 crore expenses from ₹57.5856 crore fresh proceeds. | The same issuer funding scope differs by ₹1.7279 crore. The page excludes OFS proceeds and does not explicitly supersede the narrative. Withhold pending authoritative reconciliation. |
| [SPEB Adhesives](https://nsearchives.nseindia.com/emerge/corporates/content/SpebAdhesivesLimited_PROSP.pdf) | Physical PDF 119, printed 115, states facility funding from net proceeds of ₹20.4357 crore, then cites the November 19, 2025 Board resolution for ₹20.4189 crore. PDF 120 repeats ₹20.4357 crore. | Hold the unresolved ₹1.68 lakh difference. The Board figure predates the December 3 prospectus and could have been revised, but the inspected passage does not explicitly establish that revision. This is not an allocation-column or unit-conversion error. |

The PDF SHA-256 values are:

- Kaytex: `a0a9b14c498bdcb7a8b2f8e4c8ebd32406b145f6e87f85a1da1675fab056e934`
- SPEB: `048405928a44bebad40c08e16256534094b61b1a77890af9072b6cb778b818a2`

Both new `reviewedObjects` entries require the exact issuer/offer identity,
allocation fingerprint, proof URL and PDF hash before creating a review. A
matching review withdraws the canonical allocations and retains the complete
previous value, proof, document provenance and correction history. Once that
snapshot exists, document-scoped policy blocks later lists and mirror URLs with
the same PDF hash. A first extraction with different values or a different URL
does not satisfy the initial registry guard. This change preserves those
concurrent-value/source protections; it does not broaden initial activation.

`review_source_repairs.py` reapplies the registry after its primary and optional
residual collection passes, before final policy enforcement, saving, queue
generation and validation. A field that began empty can therefore receive the
review before the completed preview is reported. This matches the normal
publisher's existing post-merge registry pass. An interrupted collection
checkpoint may precede final review and is not an accepted publication.

The source ZIP SHA-256 is
`e0317f82f2de23d55a0e232decfdf89c25654c48f49a88c492f987771b394a66`
(artifact `10518025304`); its raw IPO member hashes to
`8647648fe07fcb03dbf074d62eb3f8304d220047365bc4df98ad12d63ad149e8`.
The compact CI fixture retains exact projections from that member, including
both complete allocation proofs and document-provenance envelopes. Independent
replay withdrew exactly these two lists, left the other 1,364 rows unchanged,
preserved all six prior review entries and 123 existing correction conflicts,
and passed strict validation with zero errors. Reapplication was idempotent.
The full regression suite passed all 979 tests, including actual CI-record
withdrawal, concurrent publication preservation and a final-preview review
that survives interruption of optional diagnostics.

The broader audit reviewed retained evidence for all 15 new lists and selected
pages from ten exact PDFs. Surrounding PDF context for Skyways, Vivid, Sai
Parenterals, Ashwini and MRIL remains unverified. Rappid's newly supported
allocations expose inherited composition errors; Apsis has an inherited ₹18,000
fresh-proceeds discrepancy. Those findings remain separate. This follow-up does
not accept the broad preview or establish P4 completion.

## Integration with the reviewed seven-record release

The immutable proposal remains
`5516b3ad6ba4345abc25d7a9b2771eb5c3b32f00e9163f30167da9d6b80cf6f6`:
Emmvee's composition repair, Teamtech's four allocations and five continuing
allocation holds. Kaytex and SPEB are null in that proposal, so the two new
reviews leave it unchanged.

Integrate this follow-up and [PR #98's publication policy guard](https://github.com/Vasuki8/IPO-Tracker/pull/98)
before freezing a new reviewed publication run. Regenerate the transport's
`acceptedCodeCommit` and complete `acceptedCodeFiles` manifest from the final
combined code. Preserve the original base, proposal hash, expected IDs and all
seven record replacements. The existing manifest pinned to `4707df1e` becomes
stale when this helper or registry changes. Do not relabel an old collector
artifact with a newer source SHA; let stale queued runs fail their guard and
create a new publication bundle through the workflow.
