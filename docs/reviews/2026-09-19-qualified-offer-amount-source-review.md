# Qualified whole-offer amounts — source acceptance, 19 September 2026

Recovered main was `0a393cd40ec910958c9d685d586076d3b0e6f8f6`, including the
completed BSE batch and subsequent scheduled core/filings publications. Pages
35440189780 and public verification 35440209862 passed. Open work #94, #98, #99
and drafts #104/#105 is preserved. This is the exact next source family named in
PROJECT_STATUS.md, not a repeat of the completed NSE bidding-term or BSE repairs.

## Batch selection and acceptance

The current source-review queue has one remaining exchange gap for each of
Axiom Gas, Varmora and Pooja Logistics: `exchange.issueSizeCr`. The shared source
family is conditional whole-offer monetary disclosures at floor/cap prices in
issuer advertisements or explicit price-band corrigenda. The NSE labelled detail
tables do not themselves disclose those amounts. Independent review inspected
actual PDFs for all three issuers, including recovered Pooja documents.

Accept the following two complete, separately qualified pairs for active public
display only. These are amounts printed by the issuer, converted between explicit
INR units. No share count is multiplied by a price to supply a missing amount.

| Issuer | At floor price | At cap price | Qualification |
| --- | --- | --- | --- |
| Axiom Gas Engineering | INR 4,792.98 lakh = 47.9298 crore at INR 51/share | INR 5,074.92 lakh = 50.7492 crore at INR 54/share | Conditional on up to 9,398,000 shares and finalisation of the Basis of Allotment |
| Varmora Granito | Up to INR 6,870.47 million = 687.047 crore at INR 140/share | Up to INR 7,080.21 million = 708.021 crore at INR 148/share | Each monetary column explicitly says up to; final offer terms remain unknown |

The new pair must remain separate from canonical `issueSizeCr`, which stays null.
The existing active NSE values, qualifications, unknown observation times and all
historical evidence remain. Hold or conflict in the total/composition/bidding
band must withhold the dependent amount pair. It expires after the close date in
IST and cannot become a Final Prospectus fact through lifecycle changes.

## Original source inspection

The [independent evidence report](2026-09-19-qualified-offer-amount-source-review.json)
retains current URLs, byte counts, original PDF/archive SHA256 hashes, dates,
physical pages, table/paragraph locators, units, source identity, qualifications,
discovery authority and all recovery outcomes. Filesystem body-persistence clocks
are explicitly labelled; they are neither exchange observation nor publication
timestamps. The earlier receipts remain in Git history and are not rewritten.

**Axiom:** [issuer-hosted corrigendum and RHP bundle](https://axiomgas.com/uploads/investors/PB_AP_RHP_MERGED.pdf),
10,529,275 bytes, SHA256
`f171f2d945a297488025dd4041f84bd1dc886599dc0757e5fbe6bfc0fc91ee05`.
Physical page 1 is the scanned 16 September corrigendum. The revised paragraph
in section 8 prints both whole-issue amounts and its adjacent footnote qualifies
the share ceiling and allotment basis. Its introductory paragraph explicitly
supersedes the earlier 50–53 band with 51–54. The older advertisement and the
earlier monitoring-agency wording on the same page are retained, not selected.
The source's 8,328,000 demand denominator is a different tranche.

**Varmora:** [issuer advertisement linked by JM Financial](https://www.jmfl.com/Common/getFile/6031),
17,920,536 bytes, SHA256
`2287c54ae752a60cf2ed733940fa3e723bcd3a6e245641cb00f0619410417ea4`.
Physical page 1 is Financial Express printed page 16, dated 17 September.
The offer-details table has two price groups, each with share and monetary
columns. The selected row is Total Offer Size, not Fresh Issue, Offer for Sale
or post-offer market capitalization. Both explicit monetary legs reconcile to
their total at the disclosed precision. The floor and cap share totals differ.
The retained 726.31 crore observation derives from floor shares times cap price;
it is preserved as historical observation and cannot supply a displayed amount.

**Pooja:** recovered the [NSE RHP archive](https://nsearchives.nseindia.com/content/ipo/RHP_POOJALOGIS.zip)
and [ratios/advertisement archive](https://nsearchives.nseindia.com/content/ipo/RATIOS_POOJALOGIS.zip).
The RHP member SHA256 is
`e53f1eb90eb8850c6ef9f84a03d444052eba13d186fc62d02b2a82a1a866c847`;
the three-page Financial Express advertisement member SHA256 is
`00b4350743f3c1dc13320f28ea0f11b0aa95ac12dc228be70fe1f6b879bac54b`.
RHP cover/issue rows and the advertisement retain monetary placeholders. All
three advertisement pages were inspected; no explicit whole-offer amount pair
was found. The employee-reservation/discount references also prohibit assuming
one price for all shares. Pooja is **disclosure absent in the inspected current
documents**, with the earlier collection failures preserved and the successful
recovery recorded separately. Its amount gap stays open. No minimum-quantity or
composition expansion is included in this batch.

## Reproducible repair boundary

The two fixtures in `tests/fixtures/qualified-offer-amounts/` retain bounded
visual transcriptions of the scanned source paragraph/table, original source
tokens, their SHA256, physical locations and independent review metadata. They
are manually reviewed transcriptions, not claims that PDF text extraction read
the image. Replay validates complete paired columns, explicit units, whole-offer
scope, qualifications, supersession and compatible issuer/band/offer dates.
Changing a transcription, document identity or source metadata invalidates its
separately pinned review. Parser success alone never grants review acceptance.

Publication replaces each selected `activeOfferTerms` receipt atomically through
the existing explicit-reviewed registry and serialized publisher. The receipt
contains independent per-field document evidence for the pair. Original NSE
receipts survive in correction history. Ordinary correction runs are inert.
Support and source evidence precede a separate single-file reviewed request.

Baseline is **1,406 issuers; 408 P4 actionable + 69 higher priority; 1,553
blocking / 1,557 total source reviews; 441 pending proposals**. Expected accepted
effect is **three active amount gaps to one**, and **69 to 67 higher-priority
records**, solely through two evidenced provisional amount pairs. Blocking review
counts must remain unchanged, as must all unselected records, every hold and all
441 proposals. Final scalar amounts remain null. Expiry or invalidation restores
the missing-field work. This is active amount coverage, not final-price or final
issue-proceeds completion, and no availability exclusion is created.

Tests, actual publication hashes, canonical scope checks, deployed verification
and measured counts belong in the release receipt and PROJECT_STATUS.md. P4
remains incomplete; P5 and performance expansion remain disabled.
