# Reviewed allocation values

`previous-values.json` retains the six previously reviewed allocation lists in
`cc30f3701996232aa0eecd1b8c4adbf710c84735` and the Kaytex and SPEB lists from source
preview run `35264712051`, tested at `4707df1e82337e3a7b8bac0838bbaa30c3d200be`.
The regression tests prove that the review registry withdraws these values
only while issuer, offer, source URL, PDF hash and value fingerprint still
match. These values require source review before canonical use.

`new-document-ci-records.json` projects the exact Kaytex and SPEB CI records:
complete allocation values and field proofs, full document provenance,
primary extraction envelopes and full prior correction histories. The
projection retains any lot-size proof to test preservation of unrelated
evidence and omits other business fields and their separate field proofs.
Its input SHA-256 identifies the byte-verified `ipos.json` from that source
artifact. Both rows use `offerDocumentExtraction`; neither has an issuer
extraction envelope.

The corresponding `reviewedObjects` entries in `data/verified_corrections.json`
retain source hashes, physical PDF pages, source amounts and review findings:

- [Unimech Final Prospectus](https://nsearchives.nseindia.com/corporate/FP_INE0U3I01011_30DEC2024.pdf), PDF19: subsidiary ownership scope was attached to the preceding company row and omitted from its three children.
- [Teamtech Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/TeamtechFormworkSolutionsLimited_PROSP.pdf), PDF87–90: a project-cost breakdown was mistaken for the complete allocation of net issue proceeds.
- [Blackbuck Final Prospectus](https://www.sebi.gov.in/sebi_data/attachdocs/nov-2024/1732249559904.pdf), PDF124–125: the quoted allocation total of ₹550 crore conflicts with explicitly stated net proceeds of ₹519.719 crore.
- [M&B Engineering Final Prospectus](https://nsearchives.nseindia.com/corporate/FP_INE08N601015_04AUG2025.pdf), PDF24 and PDF119–120: the quoted allocation total of ₹275 crore conflicts with explicitly stated net proceeds of ₹259.32 crore.
- [Shri Ahimsa Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/ShriAhimsaNaturalsLimited_PROSP.pdf), PDF22 and PDF102–103: the repeated allocation total of ₹39.2956 crore conflicts with explicitly stated net proceeds of ₹42.6915 crore.
- [GenXAI Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/GenXAIAnalyticsLimited_PROSP.pdf), PDF100–101 and PDF117: the narrative calls ₹8.451 crore net proceeds after expenses, while the same-page table and later expense disclosure classify that amount as expenses and state ₹46.2138 crore net proceeds. The source does not explicitly supersede the conflicting narrative definition.
- [Kaytex Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/KaytexFabricsLimited_PROSP.pdf), PDF115 (printed110): the narrative states issuer Fresh Issue net proceeds of ₹47.6186 crore, while the immediately following table and retained allocations use ₹49.3465 crore. The page excludes OFS proceeds from the issuer's proceeds; its estimated-expenses footnote does not explicitly supersede the conflicting narrative. The ₹1.7279 crore difference requires source resolution.
- [SPEB Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/SpebAdhesivesLimited_PROSP.pdf), PDF119–120 (printed115–116): the facility allocation and detailed table give ₹20.4357 crore of net-proceeds funding, while a sentence citing the November 19, 2025 Board resolution gives ₹20.4189 crore for the same use. A later revision before the December 3 Final Prospectus could explain the ₹1.68 lakh difference, but the inspected passage does not explicitly supersede the Board figure. The retained allocation correctly selects IPO funding within the ₹26.0542 crore project cost. This hold requires authoritative source resolution.

Blackbuck, M&B Engineering, Shri Ahimsa and GenXAI require authoritative reconciliation; arithmetic
does not justify silently reducing the general corporate purposes allocation.

The new Kaytex and SPEB entries use document-scoped reviews. Initial activation
still requires the exact allocation fingerprint, source URL and PDF hash; an
initially null field has no review snapshot. A changed first allocation or
source URL is preserved under these guards. After a matching withdrawal, the
snapshot blocks re-extraction from the same PDF bytes, including changed
allocations and mirror URLs. A supported later authoritative document with
different bytes can resolve the review while preserving its original history.

Source preview applies the registry again after its primary and residual
collection passes, before the final policy, queue and report are saved.
Normal publication also applies the current registry after the three-way
merge and before policy enforcement, strict validation and page generation.
These final passes are necessary to withhold the exact reviewed allocations
when their fields were null during the initial pre-collection review. The
integration tests cover that publication sequence and preservation of a
concurrent subscription update and correction history.
