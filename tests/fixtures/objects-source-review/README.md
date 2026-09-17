# Reviewed legacy allocation values

`previous-values.json` retains the exact incorrect allocation lists in
`cc30f3701996232aa0eecd1b8c4adbf710c84735`. The regression tests prove that the
review registry withdraws these values only while issuer, offer, source URL,
PDF hash and value fingerprint still match. These are rejected values, not
examples of correct canonical data.

The corresponding `reviewedObjects` entries in `data/verified_corrections.json`
retain source hashes, physical PDF pages, source amounts and review findings:

- [Unimech Final Prospectus](https://nsearchives.nseindia.com/corporate/FP_INE0U3I01011_30DEC2024.pdf), PDF19: subsidiary ownership scope was attached to the preceding company row and omitted from its three children.
- [Teamtech Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/TeamtechFormworkSolutionsLimited_PROSP.pdf), PDF87–90: a project-cost breakdown was mistaken for the complete allocation of net issue proceeds.
- [Blackbuck Final Prospectus](https://www.sebi.gov.in/sebi_data/attachdocs/nov-2024/1732249559904.pdf), PDF124–125: the quoted allocation total of ₹550 crore conflicts with explicitly stated net proceeds of ₹519.719 crore.
- [M&B Engineering Final Prospectus](https://nsearchives.nseindia.com/corporate/FP_INE08N601015_04AUG2025.pdf), PDF24 and PDF119–120: the quoted allocation total of ₹275 crore conflicts with explicitly stated net proceeds of ₹259.32 crore.
- [Shri Ahimsa Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/ShriAhimsaNaturalsLimited_PROSP.pdf), PDF22 and PDF102–103: the repeated allocation total of ₹39.2956 crore conflicts with explicitly stated net proceeds of ₹42.6915 crore.
- [GenXAI Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/GenXAIAnalyticsLimited_PROSP.pdf), PDF100–101 and PDF117: the narrative calls ₹8.451 crore net proceeds after expenses, while the same-page table and later expense disclosure classify that amount as expenses and state ₹46.2138 crore net proceeds. The source does not explicitly supersede the conflicting narrative definition.

Blackbuck, M&B Engineering, Shri Ahimsa and GenXAI require authoritative reconciliation; arithmetic
does not justify silently reducing the general corporate purposes allocation.
